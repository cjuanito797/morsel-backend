from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.text import slugify
import json
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Product, Category, Ingredient, Extras
from .serializers import ProductSerializer, CategorySerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from .utils.openai_helpers import generate_product_description
from rest_framework.parsers import JSONParser
from django.core.files.base import ContentFile
import base64
import uuid
from decimal import Decimal, InvalidOperation
from .utils.openai_image import generate_ingredient_image
import logging

logger = logging.getLogger(__name__)

# Create your views here.
class ProductListView(APIView):
    """API Endpoint to retrieve all the products"""

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True,
                                       context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TopSoldProductsView(APIView):
    """API endpoint to retrieve the top 4 sold products to display on home page"""

    def get(self, request):
        products = Product.objects.all().order_by('-purchase_count')[:4]
        serializer = ProductSerializer(products, many=True,
                                       context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CateringProductsView(APIView):
    """API endpoint to retrieve 4 items, deemed popular with catering to be displayed on
    catering page."""

    def get(self, request):
        products = Product.objects.all().filter(popular_with_catering=True)
        serializer = ProductSerializer(products, many=True,
                                       context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductDetailView(APIView):
    """API endpoint to retrieve a single product by slug"""

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        serializer = ProductSerializer(product, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryListView(APIView):
    """API Endpoint to retrieve the categories from the backend"""

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True,
                                        context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def ai_generate_description(request):
    product_name = request.data.get('product_name')
    ingredients = request.data.get('ingredients')
    if not product_name:
        return Response({"error": "Product name is required."}, status=400)

    description = generate_product_description(product_name, ingredients)
    print(description)

    if description:
        return Response({'description': description})
    return Response({'error': 'failed to generate description.'}, status=500)


class NewCategoryView(APIView):
    """API Endpoint to create a new category"""
    def post(self, request):
        try:
            logger.info("Received a POST request to add a new category.")
            category_name = request.data.get('category_name')
            category = Category.objects.create(name=category_name)
            category.save()

            return Response({'message': 'New Category Added.'},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeleteCategoryView(APIView):
    """API Endpoint to delete a category"""
    def post(self, request):
        try:
            logger.info("Received a POST request to delete a category.")
            category_name = request.data.get('category_name')
            category = Category.objects.get(name=category_name)
            category.delete()

            return Response({'message': 'Category Deleted.'},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeleteProductView(APIView):
    def post(self, request):
        try:
            logger.info("Receieved a POST request to delete an existing "
                        "product.")
            product = request.data.get('product')

            # query the product with the id.
            id = product.get('id')

            product = Product.objects.get(id=id)
            product.delete()

            return Response({'message': 'Product deleted.'}, status=status.HTTP_200_OK)

        except Product.DoesNotExist:
            return Response({'message': 'Product does not exist.'}, status=404)


class EditProductView(APIView):
    def post(self, request):
        try:
            logger.info("Received a POST request to edit an existing product.")

            data = request.data.get('product')

            # collect all the data and save it to the product, even if we
            # have redundancy.

            id = data.get('id')

            # query the product with this id.
            product = Product.objects.get(id=id)

            description = data.get('description')
            available = data.get('available')
            price = data.get('price')
            name = data.get('name')

            product.description = description
            product.available = available
            product.price = price
            product.name = name

            product.save()

            logger.info("Succesfully updated the product.")

            return Response({"success": True})

        except Exception as e:
            logger.exception("An error occurred while editing the product.")
            return Response({"error": str(e)}, status=500)

class CreateProductAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            logger.info("Received product creation request.")

            name = request.data.get('name')
            description = request.data.get('description')
            # is the category passed in a string
            # is it an id?

            # if (string), this means admin is wanting to create a new category.
            # if it is an ID, this means that the admin will be wanting to
            # utilize an exisiting category.

            category = request.data.get('category')
            logger.info("Here is the category that was passed in: ", category)

            image = request.FILES.get('image')

            logger.debug(f"Raw data: name={name}, category={category}, image={bool(image)}")

            try:
                price = Decimal(request.data.get('price'))
                logger.debug(f"Parsed price: {price}")
            except (TypeError, InvalidOperation):
                logger.error("Invalid price format", exc_info=True)
                return Response({'error': 'Invalid price format.'}, status=400)

            ingredients = json.loads(request.data.get('ingredients', '[]'))
            extras = json.loads(request.data.get('extras', '[]'))

            logger.debug(f"Parsed ingredients: {ingredients}")
            logger.debug(f"Parsed extras: {extras}")

            if not all([name, description, price, category]):
                logger.warning("Missing required fields.")
                return Response({'error': 'Missing required fields.'}, status=400)

            category, _ = Category.objects.get_or_create(name=category)
            logger.debug(f"Found category: {category.name}")

            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                image=image,
                slug=slugify(name)
            )
            logger.info(f"Created product: {product.name}")

            # Handle Ingredients
            for ing in ingredients:
                ing_name = ing.get('name', '').strip()
                ing_price = ing.get('price', 0.0)

                if not ing_name:
                    continue

                ingredient, _ = Ingredient.objects.get_or_create(
                    name=ing_name,
                    defaults={'extra_price': ing_price}
                )
                product.ingredients.add(ingredient)
                logger.debug(f"Linked ingredient: {ing_name}")

            # Handle Extras
            for ex in extras:
                ex_name = ex.get('name', '').strip()
                ex_price = ex.get('price', 0.0)

                if not ex_name:
                    continue

                extra, _ = Extras.objects.get_or_create(
                    name=ex_name,
                    defaults={'price': ex_price}
                )
                product.extras.add(extra)
                logger.debug(f"Linked extra: {ex_name}")

            logger.info(f"Product creation complete: {product.name}")
            return Response({'success': True, 'product_id': product.id}, status=201)

        except Category.DoesNotExist:
            logger.error("Invalid category ID", exc_info=True)
            return Response({'error': 'Invalid category.'}, status=400)
        except Exception as e:
            logger.critical("Unhandled error during product creation", exc_info=True)
            return Response({'error': str(e)}, status=500)
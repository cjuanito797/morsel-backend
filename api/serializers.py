from rest_framework import serializers
from .models import Product, Category, Tag, Extras, Ingredient

class FloatDecimalField(serializers.DecimalField):
    """A custom DecimalField that serializes decimals as floats instead of strings."""
    def to_representation(self, value):
        value = super().to_representation(value)
        return float(value) if value is not None else 0.0

class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags related to products."""
    class Meta:
        model = Tag
        fields = ['id', 'name']

class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients related to products."""
    extra_price = FloatDecimalField(max_digits=10, decimal_places=2)
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'extra_price', 'image']

class ExtrasSerializer(serializers.ModelSerializer):
    """Serializer for ingredients related to products."""
    price = FloatDecimalField(max_digits=10, decimal_places=2)
    class Meta:
        model = Extras
        fields = ['id', 'name', 'price', 'image']

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products, ensuring full image URLs"""
    tags = TagSerializer(many=True, read_only=True)  # Include tags as nested data
    extras = ExtrasSerializer(many=True, read_only=True)  # include ingredients as
    ingredients = IngredientSerializer(many=True, read_only=True)
    price = FloatDecimalField(max_digits=10, decimal_places=2)
    # nested data.
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'tags', 'available',
                  'image', 'slug', 'purchase_count', 'extras', 'ingredients']

    def get_image(self, obj):
        """Ensure absolute URL for images in API response"""
        request = self.context.get('request')
        if obj.image:
            image_url = obj.image.url
            if request:
                return request.build_absolute_uri(image_url)
            return f"http://127.0.0.1:8000{image_url}"  # Fixed missing "http://"
        return None

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories, ensuring full image URLs"""
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'products']

    def get_image(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return f"{obj.image.url}"
        return None
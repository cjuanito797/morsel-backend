from django.urls import path
from .views import (ProductListView, ProductDetailView, CategoryListView,
                    TopSoldProductsView, CateringProductsView,
                    ai_generate_description, CreateProductAPIView,
                    EditProductView, DeleteProductView, NewCategoryView, DeleteCategoryView)

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('top_sold_products/', TopSoldProductsView.as_view(), name='top-products'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('edit_product/', EditProductView.as_view(), name='edit-product'),
    path('topCateringProducts/', CateringProductsView.as_view(), name='popular-with-catering'),
    path('generate-description/', ai_generate_description, name='ai-generate-description'),
    path('create-product/', CreateProductAPIView.as_view(), name='create-product'),
    path('delete-product/', DeleteProductView.as_view(), name='delete-product'),
    path('new-category/', NewCategoryView.as_view(), name='new-category'),
    path('delete-category/', DeleteCategoryView.as_view(), name='delete-category'),
]
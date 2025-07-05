from rest_framework import serializers
from .models import Order, OrderItem, UberQuote, Delivery
from api.serializers import ProductSerializer

class UberQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UberQuote
        fields = [
            'dropoff_address',
            'dropoff_lat',
            'dropoff_lng',
            'dropoff_phone_number',
            'fee',
        ]

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            'delivery_id',
            'delivery_status',
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'quantity',
            'price',
            'special_instructions',
            'owner',
            'extras',
            'ingredients_instructions',
        ]

class DeliveryOrderSerializer(serializers.ModelSerializer):
    uberquote = UberQuoteSerializer(read_only=True)
    delivery_info = DeliverySerializer(read_only=True)
    items = OrderItemSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = [
            'order_number',
            'fullDateAndTime',
            'logistics',
            'total',
            'order_completed',
            'payment_status',
            'first_name',
            'last_name',
            'email',
            'phone',
            'uberquote',
            'delivery_info',
            'items'
        ]

class OrderWithItemsSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_number',
            'pickup_date',
            'pickup_time',
            'fullDateAndTime',
            'total',
            'order_completed',
            'payment_status',
            'first_name',
            'last_name',
            'email',
            'phone',
            'items', # nested items
        ]
import random
import string
import os
from faulthandler import cancel_dump_traceback_later

from django.utils.timezone import now
from django.utils import timezone
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from api.models import Product

# Create your models here.

def generate_order_number():
    from .models import Order  # avoid circular import on initial migration

    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Order.objects.filter(order_number=code).exists():
            return code

class Order(models.Model):
    # User (Optional For Now, but ready for future user inclusion)
    user = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    # capture the order details here.
    order_number = models.CharField(
        max_length=8,
        unique=True,
        default=generate_order_number,
        editable=False
    )

    logistics = models.CharField(
        max_length=20,
        default='pickup',
        choices=[
            ('pickup', 'pickup'),
            ('delivery', 'delivery'),
        ]
    )

    # Pickup logistics if order_type is of type pickup.
    pickup_date = models.CharField(max_length=50, blank=True, null=True)
    pickup_time = models.CharField(max_length=50, blank=True, null=True)
    fullDateAndTime = models.DateTimeField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2) # amount of the order total.

    order_completed = models.BooleanField(default=False)
    # capture the payment details
    payment_status = models.CharField(
        max_length=20,
        default="Pending",
        choices =[
            ("Pending", "Pending"),
            ("Completed", "Completed"),
            ("Cancelled", "Cancelled"),
            ("Refunded", "Refunded")
        ]
    )

    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(null=True,
                                blank=True)
    cart_metadata = models.JSONField(null=True, blank=True)

    # guest information (collected for guest orders)
    first_name = models.CharField(max_length=100, default="John")
    last_name = models.CharField(max_length=100, default="Doe")
    email = models.EmailField(default="guest@example.com")
    phone = models.CharField(max_length=20, null=True, blank=True) # optional phone number

    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(models.Model):
    # link to the order and the product
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('api.Product', on_delete=models.CASCADE)

    # item specific details
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2) # price of the product at
    # the time of the order.

    # very important! capture the special instructions for the product, as typed in by user.
    special_instructions = models.TextField(null=True, blank=True)

    #capture the owner of the order item.
    owner = models.CharField(null=True, blank=True, max_length=100)

    # track the selected extras.
    extras = models.JSONField(null=True, blank=True)

    # track in a json field the state of the ingredients.
    ingredients_instructions = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

class UberQuote(models.Model):
    order = models.OneToOneField("Order", on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 related_name='uberquote')
    pickup_address = models.CharField(max_length=255)
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()

    dropoff_address = models.CharField(max_length=255)
    dropoff_lat = models.FloatField()
    dropoff_lng = models.FloatField()

    pickup_ready_dt = models.DateTimeField(null=True, blank=True)
    pickup_deadline_dt = models.DateTimeField(null=True, blank=True)
    dropoff_ready_dt = models.DateTimeField(null=True, blank=True)
    dropoff_deadline_dt = models.DateTimeField(null=True, blank=True)

    pickup_phone_number = models.CharField(max_length=255, null=True, blank=True)
    dropoff_phone_number = models.CharField(max_length=255, null=True, blank=True)

    manifest_total_value = models.IntegerField(null=True, blank=True)
    external_store_id = models.CharField(max_length=255, null=True, blank=True)
    quote_id = models.CharField(max_length=255, null=True, blank=True)

    fee = models.DecimalField(max_digits=6, decimal_places=2, null=True,
                              blank=True)
    currency = models.CharField(max_length=10, null=True, blank=True)

    quote_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Uber Quote ({self.quote_id}) - {self.pickup_address} → {self.dropoff_address}"

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('dispatched', 'Dispatched'),
        ('en_route', 'En Route'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    order = models.OneToOneField("Order", on_delete=models.CASCADE,
                                 related_name='delivery_info')
    quote = models.OneToOneField("UberQuote", on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='delivery')

    delivery_id = models.CharField(max_length=255, unique=True) # Uber delivery ID
    tracking_url = models.URLField(null=True, blank=True)

    delivery_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending'
    )

    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional driver metadata (not always available)
    driver_name = models.CharField(max_length=255, null=True, blank=True)
    driver_phone = models.CharField(max_length=50, null=True, blank=True)

    def mark_dispatched(self, delivery_id: str, tracking_url: str):
        self.delivery_id = delivery_id
        self.tracking_url = tracking_url
        self.delivery_status = 'dispatched'
        self.dispatched_at = timezone.now()
        self.save()

    def mark_delivered(self):
        self.delivery_status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Delivery for Order #{self.order.order_number}"


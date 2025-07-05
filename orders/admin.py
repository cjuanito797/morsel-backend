from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Order, OrderItem, UberQuote, Delivery
# Register your models here.

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', )

@admin.register(UberQuote)
class UberQuoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'fee')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user' )


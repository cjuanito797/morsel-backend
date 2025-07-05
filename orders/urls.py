from django.urls import path
from .views import (get_uber_quote, create_payment_intent_registered,
                    stripe_webhook, create_payment_intent_guest,
                    pickup_logistics, OutstandingPickupOrders,
                    OutstandingDeliveryOrders, dispatch_to_uber, mark_delivery_complete)
from . import views

urlpatterns = [
    path('uber/quote/', get_uber_quote, name='get_uber_quote'),
    path('create-payment-intent/registered/', create_payment_intent_registered,
         name='create_payment_intent_registered'),
    path('create-payment-intent/guest/', create_payment_intent_guest, name='create_payment_intent_guest'),
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
    path('pickup-logistics/', pickup_logistics, name='pickup_logistics'),
    path('outstanding-pickup/', OutstandingPickupOrders.as_view(), name='outstanding_pickup'),
    path('mark-ready/<str:order_number>/', views.mark_ready, name='mark_ready'),
    path('outstanding-delivery/', OutstandingDeliveryOrders.as_view(), name='outstanding_delivery'),
    path('dispatch-to-uber/', dispatch_to_uber, name='dispatch_to_uber'),
    path('mark-delivery-complete/', mark_delivery_complete, name='mark_delivery_complete'),
]

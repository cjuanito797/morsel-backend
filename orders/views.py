import json
import pprint
import traceback
from django.db import transaction
from rest_framework import status
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.http import JsonResponse
from decimal import Decimal
import stripe
import logging
from .models import Order, OrderItem, UberQuote, Delivery
from accounts.utils import sanitize_phone_number
from twilio.rest import Client
from communication.emails import (send_order_confirmation_email,
                                  send_order_ready_email,
                                  send_delivery_order_pickedup)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from api.models import Product, Extras
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import OrderWithItemsSerializer, DeliveryOrderSerializer
from communication.tasks import send_order_ready_email_async
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

logger = logging.getLogger("django")

stripe.api_key = settings.STRIPE_SECRET_KEY


class OutstandingDeliveryOrders(APIView):
    def get(self, request):
        orders = Order.objects.filter(logistics='delivery',
                                      order_completed=False)
        orders = orders.order_by('fullDateAndTime')
        serializer = DeliveryOrderSerializer(orders, many=True)
        return Response(serializer.data)


class OutstandingPickupOrders(APIView):
    def get(self, request):
        orders = Order.objects.filter(logistics='pickup',
                                      order_completed=False)
        orders = orders.order_by('fullDateAndTime')
        serializer = OrderWithItemsSerializer(orders, many=True)
        return Response(serializer.data)


class SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


@csrf_exempt
@api_view(['POST'])
def mark_delivery_complete(request):
    if request.method == "POST":
        try:
            order_number = request.data.get('order_number')
            driver_name = request.data.get('driver_name')
            driver_phone_number = request.data.get('driver_phone')
            logger.info("Here is the information for the driver %s %s",
                        driver_name, driver_phone_number)
            order = Order.objects.get(order_number=order_number)
            delivery = order.delivery_info
            # sanitize the phone number.

            phone = sanitize_phone_number(driver_phone_number)
            delivery.driver_name = driver_name
            delivery.driver_phone = phone
            delivery.save()
            logger.info("Here is the current status of the delivery %s",
                        delivery.delivery_status)

            order.order_completed = True
            order.save()

            # build the context for our MJML template.
            context_data = {
                'name': order.first_name,
                'order_number': order.order_number,
                'driver_name': driver_name,
                'tracking_url': order.delivery_info.tracking_url,
            }

            send_delivery_order_pickedup(order.email, context_data)

            return JsonResponse({"status": "success"},
                                status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return JsonResponse({'status': 'failed'},
                                status=status.HTTP_404_NOT_FOUND)
    return JsonResponse({'status': 'failed'},
                        status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def mark_ready(request, order_number):
    if request.method == 'POST':
        try:
            order = Order.objects.get(order_number=order_number)
            order.order_completed = True
            order.save()

            # build the context for our MJML template.
            context = {
                "name": order.first_name,
                "order_number": order.order_number,
                "pickup_time": f"{order.pickup_date} @ {order.pickup_time}",
                "email": order.email,
            }

            # render MJML -> HTML
            send_order_ready_email_async.delay(order.email, context)

            return JsonResponse({'status': 'success'},
                                status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return JsonResponse({'status': 'failed'},
                                status=status.HTTP_404_NOT_FOUND)
    return JsonResponse({'status': 'failed'},
                        status=status.HTTP_400_BAD_REQUEST)


def send_sms(to_number, message_body):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        to=to_number,
        from_=settings.TWILIO_PHONE_NUMBER,
        body=message_body)

    return message.sid


def enrich_extras_with_price(extras_list):
    enriched = []
    for extra in extras_list:
        try:
            db_extra = Extras.objects.get(id=extra["id"])
            enriched.append({
                "id": db_extra.id,
                "name": db_extra.name,
                "price": float(db_extra.price),
                "image": db_extra.image.url if db_extra.image else None,
                "selectionType": extra.get("selectionType", "add"),
                "showOptions": extra.get("showOptions", False),
            })
        except Extras.DoesNotExist:
            continue
    return enriched


def notify_customer(phone_number):
    try:
        phone = sanitize_phone_number(phone_number)
        message = f"Hi your order has been confirmed and is being prepared."
        sid = send_sms(phone, message)
        logger.info(f"SMS sent with SID: {sid}")

    except Exception as e:
        logger.info(f"Failed to send SMS with error: {e}")


@csrf_exempt
def pickup_logistics(request):
    try:
        data = json.loads(request.body)
        order_number = data.get('order_number')
        order = Order.objects.get(order_number=order_number)
        order_time = data.get('pickup_time')
        order_date = data.get('pickup_date')

        if order_time is not None and order_date is not None:
            order_date_and_time = data.get('pickup_date_and_time')
            order.pickup_time = order_time
            order.pickup_date = order_date
            order.fullDateAndTime = order_date_and_time

        # set the logistics for the order.
        order.logistics = 'Pickup'
        order.save()
        order.refresh_from_db()  # force a fresh DB read

        logger.info("Queried Order:", order)
        logger.info("Order ID:", order.id)
        logger.info("Order Items:", order.items.all())
        logger.info("Order Item Count:", order.items.count())

        order_items = OrderItem.objects.filter(order=order)
        logger.info(order_items)

        for idx, order_item in enumerate(order_items, start=1):
            logger.info(f"Item {idx}: {order_item}")

        context_data = {
            "name": order.first_name,
            "order_number": order_number,
            "pickup_time": (order.pickup_time + ' ' + order.pickup_date) if
            order.pickup_time
            else 'ASAP',
            "total": f"{order.total:.2f}"
            # formats as string with 2 decimal places
        }

        send_order_confirmation_email(order.email, context_data,
                                      "email_confirmation_pickup.mjml")

        return JsonResponse({"order_number": order_number})
    except Exception as e:
        logger.info("Exception occurred while handling the logistics for a "
                    "pickup "
                    "order.", {e})
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@api_view(['POST'])
def create_payment_intent_guest(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        total = Decimal(data.get('total_amount', '0'))
        currency = data.get('currency', 'usd')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone_number = data.get('phone')
        email = data.get('email')
        cart = data.get('cart_items')
        logistics = data.get('logistics')

        try:
            formatted_number = sanitize_phone_number(phone_number)
        except Exception as e:
            formatted_number = phone_number  # fallback

        if total <= 0:
            return JsonResponse(
                {"error": "Total amount must be greater than 0"}, status=400)

        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=formatted_number,
            cart_metadata=json.dumps(cart, cls=SafeEncoder),
            payment_status="Pending",
            total=total,
        )

        if logistics['order_type'] == 'pickup':
            logger.info("Setting the logistics for a pickup order.")
            order.logistics = 'pickup'
            order.pickup_time = logistics.get('pickup_time') or ''
            order.pickup_date = logistics.get('pickup_date') or ''
            order.fullDateAndTime = (logistics.get('pickup_date_and_time') or
                                     None)
            order.save()
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),
                # convert the total into an integer for
                # cents.
                currency=currency,
                metadata={
                    "order_number": str(order.order_number),
                    "email": str(email),
                    "first_name": str(first_name),
                    "last_name": str(last_name),
                    "phone_number": str(formatted_number),
                },
            )

            order.stripe_payment_intent_id = intent['id']

        elif logistics['order_type'] == 'delivery':
            logger.info("Setting the logistics for a delivery order.")
            order.logistics = "delivery"
            order.fullDateAndTime = datetime.now(ZoneInfo("America/Chicago"))
            quote_id = (
                data.get("logistics", {})
                .get("delivery_info", {})
                .get("quote_id")
            )
            # query the quote_id
            uber_quote = UberQuote.objects.filter(quote_id=quote_id).get()
            uber_quote.order = order
            uber_quote.save()
            order.save()
            logger.info("✅ Completed setting the logistics for a delivery "
                        "order.")
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),
                # convert the total into an integer for
                # cents.
                currency=currency,
                metadata={
                    "order_number": str(order.order_number),
                    "email": str(email),
                    "first_name": str(first_name),
                    "last_name": str(last_name),
                    "phone_number": str(formatted_number),
                    "quote_id": str(quote_id),
                },
            )

            order.stripe_payment_intent_id = intent['id']

        return JsonResponse({"client_secret": intent.client_secret,
                             "order_number": str(order.order_number),
                             })
    except Exception as e:
        traceback.print_exc()  # logger.info the fullstack trace to console.
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent_registered(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        total = Decimal(data.get("total_amount", "0"))
        currency = data.get("currency", "usd")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone_number = data.get("phone")
        email = data.get("email")
        cart = data.get("cart_items")
        logistics = data.get("logistics")
        auth_token = data.get("authToken")

        user = request.user
        logger.info("Here is the authorization token that was passed in to the "
                    "backend.")
        logger.info(auth_token)
        logger.info(user.username)

        try:
            formatted_number = sanitize_phone_number(phone_number)
        except Exception as e:
            formatted_number = phone_number  # Fallback

        if total <= 0:
            return JsonResponse({"error": "Invalid request data"}, status=400)

        order = Order.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=formatted_number,
            cart_metadata=json.dumps(cart, cls=SafeEncoder),
            payment_status="Pending",
            total=total,
        )

        intent = stripe.PaymentIntent.create(
            amount=int(total * 100),  # cents
            currency=currency,
            metadata={
                "order_number": str(order.order_number),
                "email": str(email),
                "first_name": str(first_name),
                "last_name": str(last_name),
                "phone_number": str(formatted_number),
            },
        )

        order.stripe_payment_intent_id = intent["id"]

        if logistics['order_type'] == 'pickup':
            logger.info("Setting the logistics for a pickup order.")
            order.logistics = "pickup"
            order.pickup_time = logistics.get("pickup_time") or ""
            order.pickup_date = logistics.get("pickup_date") or ""
            order.fullDateAndTime = (logistics.get("pickup_date_and_time") or
                                     None)
            order.save()
            logger.info("Completed setting the logistics for a pickup order.")

        elif logistics['order_type'] == 'delivery':
            logger.info("Setting the logistics for a delivery order.")
            order.logistics = "delivery"
            order.fullDateAndTime = datetime.now(ZoneInfo("America/Chicago"))
            quote_id = (
                data.get("logistics", {})
                .get("delivery_info", {})
                .get("quote_id")
            )
            # query the quote_id
            uber_quote = UberQuote.objects.filter(quote_id=quote_id).get()
            uber_quote.order = order
            uber_quote.save()
            order.save()
            logger.info("✅ Completed setting the logistics for a delivery "
                        "order.")

        return JsonResponse({
            "client_secret": intent.client_secret,
            "order_number": str(order.order_number),
        })

    except Exception as e:
        traceback.print_exc()  # logger.info the full-stack truce to console.
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@api_view(['POST'])
def stripe_webhook(request):
    logger.info("Webhook received")

    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error(f"Stripe webhook validation failed: {e}")
        return HttpResponse(status=400)

    logger.info(f"Webhook event type: {event['type']}")

    if event['type'] != 'payment_intent.succeeded':
        logger.info("Ignoring non-payment_intent.succeeded event.")
        return HttpResponse(status=200)

    try:
        payment_intent = event['data']['object']
        metadata = payment_intent.get('metadata', {})

        order_number = metadata.get('order_number')
        if not order_number:
            logger.warning("Missing order_number in metadata")
            return HttpResponse("Missing order_number", status=400)

        order = Order.objects.get(order_number=order_number)
        logger.info(f"Processing Order #{order_number} ({order.logistics})")
        order.payment_status = "Completed"

        cart_data = order.cart_metadata
        if not cart_data:
            logger.warning("Missing cart data in order")
            return HttpResponse("Missing cart data", status=400)

        # Save Uber quote + create delivery object if needed
        if order.logistics == "delivery":
            logger.info("Order is for delivery.")
            quote_id = metadata.get('quote_id')
            if not quote_id:
                return HttpResponse("Missing quote_id", status=400)

            uber_quote = UberQuote.objects.get(quote_id=quote_id)
            uber_quote.quote_status = 'completed'
            uber_quote.save()

            Delivery.objects.create(
                order=order,
                quote=uber_quote,
                delivery_id=uber_quote.quote_id,
                delivery_status='pending',
            )

        order.save()

        # Create order items
        cart_items = json.loads(cart_data)
        for item in cart_items:
            enriched_extras = enrich_extras_with_price(item.get("extras", []))
            OrderItem.objects.create(
                order=order,
                product=Product.objects.get(pk=item["product_id"]),
                quantity=int(item["quantity"]),
                price=float(item["quantity"]) * float(item["unit_price"]),
                special_instructions=item["special_instructions"],
                extras=enriched_extras,
                ingredients_instructions=item["ingredients"]
            )

        # Send confirmation and dispatch delivery if needed
        if order.logistics == "delivery":
            dispatch_to_uber(order_number)

            # refresh the delivery relationship from the DB
            order.refresh_from_db()

            logger.info("Here is the url for tracking your order %s",
                        order.delivery_info.tracking_url)

            context_data = {
                "name": order.first_name,
                "order_number": str(order.order_number),
                "delivery_address": order.uberquote.dropoff_address,
                "tracking_url": order.delivery_info.tracking_url,
                "total": f"{order.total:.2f}",
                "order_items": order.items.all(),
            }
            send_order_confirmation_email(order.email, context_data,
                                          "email_confirmation_delivery.mjml")

        elif order.logistics == "pickup":
            if not order.pickup_date or not order.pickup_time:
                logger.warning("Missing pickup date/time.")
                return HttpResponse("Incomplete pickup info", status=400)

            pickup_info = f"{order.pickup_date.strftime('%Y-%m-%d')} @ {order.pickup_time.strftime('%I:%M %p')}"
            context_data = {
                "name": order.first_name,
                "order_number": order.order_number,
                "pickup_time": pickup_info,
                "total": f"{order.total:.2f}",
                "order_items": order.items.all(),
            }
            send_order_confirmation_email(order.email, context_data,
                                          "email_confirmation_pickup.mjml")

        else:
            logger.warning(f"Unknown logistics type: {order.logistics}")

        return HttpResponse(status=200)

    except Order.DoesNotExist:
        logger.error(f"Order not found for number: {order_number}")
        return HttpResponse("Order not found", status=404)

    except Exception as e:
        logger.exception("Unexpected error during payment processing")
        return HttpResponse("Error processing webhook", status=500)


def get_uber_access_token():
    payload = {
        'client_id': settings.UBER_CLIENT_ID,
        'client_secret': settings.UBER_CLIENT_SECRET,
        'grant_type': 'client_credentials',
        'scope': settings.UBER_SCOPE,
    }

    response = requests.post(settings.UBER_TOKEN_URL, data=payload)
    response.raise_for_status()
    return response.json()['access_token']


def format_uber_time(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')


@csrf_exempt
def get_uber_quote(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)

        pickup_address = data.get('pickup_address')
        pickup_lat = data.get('pickup_latitude')
        pickup_lng = data.get('pickup_longitude')
        dropoff_address = data.get('dropoff_address')
        dropoff_lat = data.get('dropoff_latitude')
        dropoff_lng = data.get('dropoff_longitude')
        order_subtotal = data.get('order_subtotal')

        if not all([pickup_address, pickup_lat, pickup_lng,
                    dropoff_address, dropoff_lat, dropoff_lng, order_subtotal]):
            return JsonResponse(
                {'error': 'Missing one or more required fields'}, status=400)

        central_now = datetime.now(ZoneInfo('America/Chicago'))
        pickup_ready_dt = central_now + timedelta(minutes=90)
        pickup_deadline_dt = pickup_ready_dt + timedelta(minutes=30)
        dropoff_ready_dt = pickup_deadline_dt
        dropoff_deadline_dt = dropoff_ready_dt + timedelta(minutes=60)

        pickup_ready_utc = pickup_ready_dt.astimezone(ZoneInfo("UTC"))
        pickup_deadline_utc = pickup_deadline_dt.astimezone(ZoneInfo("UTC"))
        dropoff_ready_utc = dropoff_ready_dt.astimezone(ZoneInfo("UTC"))
        dropoff_deadline_utc = dropoff_deadline_dt.astimezone(ZoneInfo("UTC"))

        access_token = get_uber_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        manifest_cents = int(float(order_subtotal) * 100)

        payload = {
            "pickup_address": pickup_address,
            "pickup_latitude": pickup_lat,
            "pickup_longitude": pickup_lng,
            "dropoff_address": dropoff_address,
            "dropoff_latitude": dropoff_lat,
            "dropoff_longitude": dropoff_lng,
            "pickup_ready_dt": format_uber_time(pickup_ready_utc),
            "pickup_deadline_dt": format_uber_time(pickup_deadline_utc),
            "dropoff_ready_dt": format_uber_time(dropoff_ready_utc),
            "dropoff_deadline_dt": format_uber_time(dropoff_deadline_utc),
            "pickup_phone_number": "+17123221607",
            "dropoff_phone_number": "+15555555555",
            "manifest_total_value": manifest_cents,
            "external_store_id": "morsel_store_demo",
        }

        logger.info(f"Sending to Uber:\n{json.dumps(payload, indent=2)}")

        response = requests.post(settings.UBER_QUOTE_URL, headers=headers,
                                 json=payload)
        logger.info(f"Uber response: {response.status_code} - {response.text}")

        response.raise_for_status()
        quote = response.json()

        UberQuote.objects.create(
            pickup_address=pickup_address,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            dropoff_address=dropoff_address,
            dropoff_lat=dropoff_lat,
            dropoff_lng=dropoff_lng,
            pickup_ready_dt=pickup_ready_dt,
            pickup_deadline_dt=pickup_deadline_dt,
            dropoff_ready_dt=dropoff_ready_dt,
            dropoff_deadline_dt=dropoff_deadline_dt,
            pickup_phone_number="+17123221607",
            dropoff_phone_number="+15555555555",
            manifest_total_value=manifest_cents,
            external_store_id="morsel_store_demo",
            quote_id=quote.get("id"),
            fee=quote.get("fee") / 100 if quote.get("fee") else None,
            currency=quote.get("currency"),
        )

        return JsonResponse({
            'fee': quote.get('fee'),
            'currency': quote.get('currency'),
            'duration': quote.get('duration'),
            'dropoff_eta': quote.get('dropoff_eta'),
            'quote_id': quote.get('id'),
        })

    except requests.exceptions.HTTPError as err:
        logger.error(f"Uber API error: {err.response.text}")
        return JsonResponse({'error': f'Uber API error: {err.response.text}'},
                            status=500)

    except Exception as e:
        logger.exception("Unexpected error during Uber quote creation")
        return JsonResponse({'error': 'Unexpected server error'}, status=500)


@csrf_exempt
def dispatch_to_uber(order_number):
    try:
        if not order_number:
            return {'Error': 'Missing order_number'}

        # find the paid order and the delivery.
        order = Order.objects.get(order_number=order_number)
        delivery = order.delivery_info  # one to one field, related_name
        quote = order.uberquote

        if not quote or not quote.quote_id:
            return {'Error': 'Missing Uber quote or quote_id'}

        access_token = get_uber_access_token()

        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json',
        }

        # build manifest from order items
        manifest = []
        for item in order.items.all():
            name = item.product.name
            qty = item.quantity
            manifest.append(f"{qty}x {name}")

        payload = {
            "pickup_address": quote.pickup_address,
            "pickup_latitude": quote.pickup_lat,
            "pickup_longitude": quote.pickup_lng,
            "pickup_name": "Morsel Kitchen",
            "pickup_phone_number": quote.pickup_phone_number,
            "dropoff_address": quote.dropoff_address,
            "dropoff_latitude": quote.dropoff_lat,
            "dropoff_longitude": quote.dropoff_lng,
            "dropoff_name": f"{order.first_name} {order.last_name}",
            "dropoff_phone_number": quote.dropoff_phone_number,
            "manifest": ", ".join(manifest),
            "quote_id": quote.quote_id,
            "external_store_id": quote.external_store_id,
            "external_delivery_id": f"{order.order_number}",
        }

        # log everything
        logger.info("Dispatching to Uber with payload:")
        logger.info(json.dumps(payload, indent=2))
        logger.info("Using headers:")
        logger.info(json.dumps(headers, indent=2))

        dispatch_url = settings.UBER_DISPATCH_URL  # SANDBOX endpoint
        response = requests.post(dispatch_url, headers=headers, json=payload)
        logger.info(
            f"Uber dispatch response: {response.status_code} - {response.text}")
        response.raise_for_status()

        dispatch_data = response.json()
        delivery.delivery_id = dispatch_data.get('id')
        delivery.tracking_url = dispatch_data.get('tracking_url')
        delivery.delivery_status = 'dispatched'
        delivery.save()

        return {
            'message': 'Order dispatched to uber succesfully',
            'delivery_id': delivery.delivery_id,
            'tracking_url': delivery.tracking_url,
            'status': delivery.delivery_status,
        }

    except Order.DoesNotExist:
        return {'error': 'Order not found'}
    except AttributeError:
        return {'error': 'no delivery associated with this order'}
    except requests.exceptions.RequestException as e:
        logger.error("Dispatch failed:", exc_info=True)
        return {'error': 'uber dispatch failed'}
    except Exception as e:
        logger.error('Unexpected error during dispatch:', exc_info=True)
        return {'error': str(e)}

from celery import shared_task
from .emails import send_order_ready_email

@shared_task
def send_order_ready_email_async(email, context):
    send_order_ready_email(email, context)
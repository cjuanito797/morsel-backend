from django.core.mail import EmailMultiAlternatives
from .mjml_renderer import render_mjml_template

def send_order_confirmation_email(to_email, context, template_name):
    # Dynamically adjust subject based on template used
    if "pickup" in template_name:
        subject = "Your Pickup Order Confirmation"
    elif "delivery" in template_name:
        subject = "Your Delivery Order Confirmation"
    else:
        subject = "Your Order Confirmation"

    from_email = "orders@yourdomain.com"
    html_content = render_mjml_template(template_name, context)

    text_content = f"""Hi {context['name']}, your order is confirmed.
Total: ${context['total']}
"""

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def send_delivery_order_pickedup(to_email: str, context: dict):
    subject = (f"Your delivery order has been picked up by "
               f"{context['driver_name']}")
    from_email = 'orders@morselpro.com' # change as needed

    html_content = render_mjml_template("delivery_order_picked_up.mjml",
                                        context)

    # optional plain-text fallback.
    text_content = (
        f"Hello {context['name']},\n\n"
        f"Your order #{context['order_number']} hass been picked up by {context['driver_name']}."
        f"You can track your order at: {context['tracking_url']}"
        f"Thank you for choosing us!"
    )

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send()

def send_order_ready_email(to_email: str, context: dict):
    subject = f"🎉 Your order #{context['order_number']} is ready!"
    from_email = 'orders@morselpro.com'  # Change as needed

    # Render HTML content using MJML
    html_content = render_mjml_template("order_ready.mjml", context)

    # Optional: Plain-text fallback
    text_content = (
        f"Hello {context['name']},\n\n"
        f"Your order #{context['order_number']} is ready for pickup!\n"
        f"Pickup Time: {context['pickup_time']}\n\n"
        "Thank you for choosing us!"
    )

    # Create the email
    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send()
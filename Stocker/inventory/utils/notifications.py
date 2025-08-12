from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_low_stock_digest(products, to_email=None):
    to_email = to_email or settings.MANAGER_EMAIL
    if not products:
        return 0
    ctx = {"products": products}
    subject = "Stocker • Low stock alert"
    text = render_to_string("email/low_stock.txt", ctx)
    html = render_to_string("email/low_stock.html", ctx)
    msg = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [to_email])
    msg.attach_alternative(html, "text/html")
    msg.send()
    return len(products)

def send_expiry_digest(products, days, to_email=None):
    to_email = to_email or settings.MANAGER_EMAIL
    if not products:
        return 0
    ctx = {"products": products, "days": days}
    subject = f"Stocker • Items expiring in ≤ {days} days"
    text = render_to_string("email/expiry.txt", ctx)
    html = render_to_string("email/expiry.html", ctx)
    msg = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [to_email])
    msg.attach_alternative(html, "text/html")
    msg.send()
    return len(products)

def send_low_stock_single(product, to_email=None):
    return send_low_stock_digest([product], to_email)

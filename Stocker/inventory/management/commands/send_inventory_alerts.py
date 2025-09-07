from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import F, Q

from inventory.models import Product
from inventory.utils.notifications import send_low_stock_digest, send_expiry_digest

class Command(BaseCommand):
    help = "Send daily low-stock and expiry alerts"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=getattr(settings, "INVENTORY_EXPIRY_ALERT_DAYS", 7),
                            help="Days ahead for expiry alerts")
        parser.add_argument("--to", type=str, default=getattr(settings, "MANAGER_EMAIL", None),
                            help="Recipient email (defaults to settings.MANAGER_EMAIL)")
        parser.add_argument("--only", choices=["low", "expiry", "all"], default="all",
                            help="Send only low, only expiry, or all")

    def handle(self, *args, **opts):
        days = opts["days"]
        to_email = opts["to"]
        only = opts["only"]

        # Low stock (global across users). If you want per-user emails, scope by owner.
        low_qs = Product.objects.filter(quantity_on_hand__lte=F("reorder_level")).order_by("name")

        # Expiry (within N days, not null, and not already expired beyond window)
        today = date.today()
        end = today + timedelta(days=days)
        # Expiry (global across users). If you want per-user emails, scope by owner.
        exp_qs = Product.objects.filter(expiry_date__isnull=False, expiry_date__lte=end).order_by("expiry_date", "name")

        sent_low = sent_exp = 0
        if only in ("all", "low"):
            sent_low = send_low_stock_digest(list(low_qs), to_email)
        if only in ("all", "expiry"):
            sent_exp = send_expiry_digest(list(exp_qs), days, to_email)

        self.stdout.write(self.style.SUCCESS(
            f"Alerts sent • low: {sent_low} items, expiry: {sent_exp} items → {to_email}"
        ))

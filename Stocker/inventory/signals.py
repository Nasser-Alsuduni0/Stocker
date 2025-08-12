from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings
from django.db.models import F

from .models import StockMovement
from .utils.notifications import send_low_stock_single


ALERT_COOLDOWN_HOURS = int(getattr(settings, "LOW_STOCK_ALERT_COOLDOWN_HOURS", 12))

@receiver(post_save, sender=StockMovement)
def low_stock_alert_on_movement(sender, instance: StockMovement, created, **kwargs):
    if not created:
        return
    p = instance.product
    if p.quantity_on_hand is None or p.reorder_level is None:
        return
    if p.quantity_on_hand > p.reorder_level:
        return

    key = f"low_alert_{p.pk}"
    if cache.get(key):
        return  

 
    try:
        send_low_stock_single(p)
        cache.set(key, True, timeout=ALERT_COOLDOWN_HOURS * 3600)
    except Exception:
        
        pass


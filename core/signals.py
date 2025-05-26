from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import OrderItem, Discount

def invalidate_order_cache(order_id):
    cache.delete(f"order_{order_id}_total_price")
    cache.delete(f"order_{order_id}_final_price")
    cache.delete(f"order_{order_id}_total_quantity")

@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def order_item_changed(sender, instance, **kwargs):
    invalidate_order_cache(instance.order.id)

@receiver(post_save, sender=Discount)
@receiver(post_delete, sender=Discount)
def discount_changed(sender, instance, **kwargs):
    if instance.order_id:
        invalidate_order_cache(instance.order_id)
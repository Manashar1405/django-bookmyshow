from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from movies.models import Booking, Payment
from .analytics.cache import AnalyticsCacheKeys

def clear_analytics_cache():
    # In a real Redis setup, you might use wildcards (e.g., cache.delete_pattern("analytics:*"))
    # For LocMemCache, we explicitly clear known keys (assuming 30d default for simplicity)
    keys_to_clear = [
        AnalyticsCacheKeys.with_days(AnalyticsCacheKeys.REVENUE, 30),
        AnalyticsCacheKeys.with_days(AnalyticsCacheKeys.MOVIES, 30),
        AnalyticsCacheKeys.with_days(AnalyticsCacheKeys.USERS, 30),
        AnalyticsCacheKeys.THEATERS,
    ]
    cache.delete_many(keys_to_clear)

@receiver(post_save, sender=Booking)
@receiver(post_delete, sender=Booking)
def invalidate_booking_cache(sender, instance, **kwargs):
    clear_analytics_cache()

@receiver(post_save, sender=Payment)
def invalidate_payment_cache(sender, instance, **kwargs):
    if instance.status == "SUCCESS":
        clear_analytics_cache()

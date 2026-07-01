from django.core.cache import cache
from django.conf import settings

class AnalyticsCacheKeys:
    REVENUE = "analytics:revenue"
    BOOKINGS = "analytics:bookings"
    USERS = "analytics:users"
    MOVIES = "analytics:movies"
    THEATERS = "analytics:theaters"
    DASHBOARD_CARDS = "analytics:dashboard_cards"
    
    @classmethod
    def with_days(cls, key: str, days: int) -> str:
        return f"{key}_{days}d"

def get_cached_or_compute(key: str, compute_func, timeout: int = None):
    if timeout is None:
        timeout = getattr(settings, 'ANALYTICS_CACHE_TIMEOUT', 300)
        
    result = cache.get(key)
    if result is None:
        result = compute_func()
        cache.set(key, result, timeout)
    return result

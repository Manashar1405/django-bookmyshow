from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from movies.models import Booking

class UserAnalyticsService:
    @staticmethod
    def get_user_stats(days: int = 30) -> dict:
        start_date = timezone.now() - timedelta(days=days)
        
        total_users = User.objects.filter(is_staff=False).count()
        new_users = User.objects.filter(is_staff=False, date_joined__gte=start_date).count()
        
        return {
            'total_users': total_users,
            'new_users': new_users
        }

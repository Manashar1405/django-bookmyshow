from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from movies.models import Movie, Booking

class MovieAnalyticsService:
    @staticmethod
    def get_top_movies(days: int = 30) -> list[dict]:
        start_date = timezone.now() - timedelta(days=days)
        
        movies = Movie.objects.filter(
            booking__booked_at__gte=start_date
        ).annotate(
            booking_count=Count('booking')
        ).order_by('-booking_count')[:10]
        
        return [
            {
                'id': m.id,
                'name': m.name,
                'bookings': m.booking_count
            }
            for m in movies
        ]

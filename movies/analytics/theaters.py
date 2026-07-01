from django.db.models import Count, F, FloatField, ExpressionWrapper, Q
from movies.models import Theater

class TheaterAnalyticsService:
    @staticmethod
    def get_occupancy() -> list[dict]:
        theaters = Theater.objects.annotate(
            total=Count('seats'),
            booked=Count('seats', filter=Q(seats__is_booked=True))
        ).annotate(
            rate=ExpressionWrapper(F('booked') * 100.0 / F('total'), output_field=FloatField())
        ).order_by('-rate')[:5]
        
        return [
            {
                'id': t.id,
                'name': t.name,
                'occupancy_rate': round(t.rate, 2) if t.rate else 0
            }
            for t in theaters
        ]

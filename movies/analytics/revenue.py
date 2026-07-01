from django.db.models import Sum
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
from movies.models import Payment

class RevenueAnalyticsService:
    @staticmethod
    def get_revenue(days: int = 30) -> dict:
        start_date = timezone.now() - timedelta(days=days)
        revenue_qs = Payment.objects.filter(
            status="SUCCESS", 
            created_at__gte=start_date
        )
        
        daily = list(revenue_qs.annotate(date=TruncDay('created_at'))
                    .values('date')
                    .annotate(total=Sum('amount'))
                    .order_by('date'))
                    
        total = revenue_qs.aggregate(total_rev=Sum('amount'))['total_rev'] or 0
        
        return {
            'total_revenue_inr': total / 100,
            'daily_breakdown': [
                {'date': d['date'].strftime('%Y-%m-%d'), 'amount': d['total'] / 100} 
                for d in daily
            ]
        }

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from movies.analytics import (
    RevenueAnalyticsService, 
    MovieAnalyticsService, 
    UserAnalyticsService, 
    TheaterAnalyticsService,
    AnalyticsCacheKeys,
    get_cached_or_compute
)

@method_decorator(staff_member_required, name='dispatch')
class AnalyticsAPIView(View):
    def get(self, request, *args, **kwargs):
        try:
            days = int(request.GET.get('days', 30))
            if days <= 0 or days > 365:
                return JsonResponse({"status": "error", "message": "Invalid date range"}, status=400)
                
            data = {
                "revenue": get_cached_or_compute(
                    AnalyticsCacheKeys.with_days(AnalyticsCacheKeys.REVENUE, days),
                    lambda: RevenueAnalyticsService.get_revenue(days)
                ),
                "movies": get_cached_or_compute(
                    AnalyticsCacheKeys.with_days(AnalyticsCacheKeys.MOVIES, days),
                    lambda: MovieAnalyticsService.get_top_movies(days)
                ),
                "users": get_cached_or_compute(
                    AnalyticsCacheKeys.with_days(AnalyticsCacheKeys.USERS, days),
                    lambda: UserAnalyticsService.get_user_stats(days)
                ),
                "theaters": get_cached_or_compute(
                    AnalyticsCacheKeys.THEATERS,
                    lambda: TheaterAnalyticsService.get_occupancy()
                )
            }
            return JsonResponse({"status": "success", "data": data})
            
        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid days parameter"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

import csv
from django.http import HttpResponse

@method_decorator(staff_member_required, name='dispatch')
class AnalyticsExportView(View):
    def get(self, request, *args, **kwargs):
        days = int(request.GET.get('days', 30))
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_export_{days}d.csv"'
        
        writer = csv.writer(response)
        
        # Write Revenue
        writer.writerow(['--- REVENUE ---'])
        writer.writerow(['Date', 'Revenue (INR)'])
        revenue_data = get_cached_or_compute(
            AnalyticsCacheKeys.with_days(AnalyticsCacheKeys.REVENUE, days),
            lambda: RevenueAnalyticsService.get_revenue(days)
        )
        for row in revenue_data['daily_breakdown']:
            writer.writerow([row['date'], row['amount']])
            
        writer.writerow([])
        
        # Write Movies
        writer.writerow(['--- TOP MOVIES ---'])
        writer.writerow(['Movie Name', 'Total Bookings'])
        movie_data = get_cached_or_compute(
            AnalyticsCacheKeys.with_days(AnalyticsCacheKeys.MOVIES, days),
            lambda: MovieAnalyticsService.get_top_movies(days)
        )
        for row in movie_data:
            # Handle unicode and commas gracefully
            writer.writerow([row['name'], row['bookings']])
            
        return response

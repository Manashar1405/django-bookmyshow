from django.urls import path
from .views import movie_detail, book_seats, razorpay_webhook, theater_list, verify_payment
from .views.dashboard import AdminDashboardView
from .views.api import AnalyticsAPIView, AnalyticsExportView
from .views.movie_list import MovieListView

app_name = 'movies'

urlpatterns = [
    path('', MovieListView.as_view(), name='movie_list'),
    path('<int:movie_id>/theaters', theater_list, name='theater_list'),
    path('movie/<int:movie_id>/', movie_detail, name='movie_detail'),
    path('theater/<int:theater_id>/seats/book/', book_seats, name='book_seats'),
    path('verify-payment/', verify_payment, name='verify_payment'),
    path('razorpay-webhook/', razorpay_webhook, name='razorpay_webhook'),
    path('admin/analytics/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('api/v1/analytics/', AnalyticsAPIView.as_view(), name='analytics_api'),
    path('api/v1/export/', AnalyticsExportView.as_view(), name='analytics_export'),
]
from django.contrib import admin
from .models import Movie, Theater, Seat, Booking, Payment, Genre, Language


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'cast', 'description', 'trailer_url')


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ('name', 'movie', 'time')


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('theater', 'seat_number', 'is_booked')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'seat', 'movie', 'theater', 'booked_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'razorpay_order_id', 'amount', 'status', 'is_verified', 'created_at')
    list_filter = ('status', 'is_verified')
    search_fields = ('razorpay_order_id', 'user__username')
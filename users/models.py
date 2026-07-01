from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Movie(models.Model):
    name = models.CharField(max_length=255)
    rating = models.FloatField()
    cast = models.TextField()
    description = models.TextField()
    image = models.ImageField(upload_to='movies/')
    trailer_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class Theater(models.Model):
    name = models.CharField(max_length=255)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    time = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.movie.name}"


class Seat(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)

    # OLD FEATURE
    is_booked = models.BooleanField(default=False)

    # ✅ NEW FEATURES (TASK 2)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def is_lock_expired(self):
        if self.locked_at:
            return (timezone.now() - self.locked_at).seconds > 120
        return False

    def __str__(self):
        return self.seat_number


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.seat.seat_number}"
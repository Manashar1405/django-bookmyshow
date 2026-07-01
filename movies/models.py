from django.db import models
from django.contrib.auth.models import User


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)

    def __str__(self):
        return self.name

class MovieSort(models.TextChoices):
    LATEST = "latest", "Latest"
    RATING = "rating", "Rating"
    TITLE = "title", "Title"
    POPULARITY = "popularity", "Popularity"

class Movie(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='movies/')
    rating = models.DecimalField(max_digits=3, decimal_places=1, db_index=True)
    cast = models.TextField()
    description = models.TextField(blank=True, null=True)
    
    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)
    languages = models.ManyToManyField(Language, related_name='movies', blank=True)
    release_date = models.DateField(null=True, blank=True, db_index=True)

    # Task 1 field
    trailer_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class Theater(models.Model):
    name = models.CharField(max_length=255)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='theaters')
    time = models.DateTimeField()

    def __str__(self):
        return f"{self.name} - {self.movie.name} at {self.time}"


from django.utils import timezone

class Seat(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)

    is_booked = models.BooleanField(default=False)

    # NEW FIELDS 👇
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    def is_lock_expired(self):
        if self.locked_at:
            return timezone.now() > self.locked_at + timezone.timedelta(minutes=2)
        return True

    def __str__(self):
        return f"{self.seat_number} in {self.theater.name}"


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movie_bookings')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    confirmation_email_sent_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.user.username} booked {self.seat.seat_number}"
    
from django.contrib.auth.models import User

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    
    # Store the intended seat IDs securely for the webhook
    seat_ids = models.CharField(max_length=255, blank=True, null=True)

    razorpay_order_id = models.CharField(max_length=255)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)

    amount = models.IntegerField()  # in paise

    status = models.CharField(max_length=50, default="CREATED", db_index=True)

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"
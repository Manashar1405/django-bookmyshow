from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
import razorpay
import re
from movies.models import Movie, Theater, Seat, Booking, Payment
from movies.services.filtering import MovieFilterService as FilterService
from movies.services.pagination import PaginationService
from movies.services.facets import FacetService
from movies.services.notifications import NotificationService


# ===============================
# TASK 1: YouTube Trailer Logic
# ===============================
def extract_youtube_id(url):
    pattern = r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    youtube_id = extract_youtube_id(movie.trailer_url) if movie.trailer_url else None

    return render(request, "movies/movie_detail.html", {
        "movie": movie,
        "youtube_id": youtube_id
    })


# Removed old movie_list view. Replaced with MovieListView CBV in movie_list.py


# ===============================
# Theater Listing
# ===============================
def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theaters = Theater.objects.filter(movie=movie)

    return render(request, 'movies/theater_list.html', {
        'movie': movie,
        'theaters': theaters
    })


# ===============================
# TASK 2: Concurrency Safe Booking
# ===============================
@login_required(login_url='/users/login/')
def book_seats(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)

    seats = Seat.objects.filter(theater=theater)

    if request.method == 'POST':
        selected_seats = request.POST.getlist('seats')

        if not selected_seats:
            return render(request, 'movies/seat_selection.html', {
                'theater': theater,
                'seats': seats,
                'error': 'Please select at least one seat.'
            })

        try:
            with transaction.atomic():

                # 🔒 Lock rows (SQLite safe logic)
                locked_seats = Seat.objects.select_for_update().filter(
                    id__in=selected_seats,
                    theater=theater
                )

                # 🚨 STEP 1: STRICT VALIDATION (before any change)
                unavailable_seats = []

                for seat in locked_seats:
                    if seat.is_booked:
                        unavailable_seats.append(seat.seat_number)

                    elif seat.is_locked and seat.locked_at:
                        if timezone.now() < seat.locked_at + timezone.timedelta(minutes=2):
                            unavailable_seats.append(seat.seat_number)

                # ❌ STOP if any seat unavailable
                if unavailable_seats:
                    return render(request, 'movies/seat_selection.html', {
                        'theater': theater,
                        'seats': Seat.objects.filter(theater=theater),
                        'error': f"Seats {', '.join(unavailable_seats)} are already booked or locked."
                    })

                # 🔒 STEP 2: Lock seats
                for seat in locked_seats:
                    seat.is_locked = True
                    seat.locked_at = timezone.now()
                    seat.save()

                # ✅ STEP 3: Init Payment
                amount = len(selected_seats) * 100 * 100 # Assuming Rs 100 per ticket
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                payment_order = client.order.create({
                    "amount": amount,
                    "currency": "INR",
                    "payment_capture": 1
                })

                Payment.objects.create(
                    user=request.user,
                    razorpay_order_id=payment_order['id'],
                    amount=amount,
                    seat_ids=",".join(selected_seats)
                )

                return render(request, "movies/payment.html", {
                    "payment": payment_order,
                    "razorpay_key": settings.RAZORPAY_KEY_ID,
                    "amount": amount
                })

        except Exception as e:
            return render(request, 'movies/seat_selection.html', {
                'theater': theater,
                'seats': Seat.objects.filter(theater=theater),
                'error': "Something went wrong. Try again."
            })

    return render(request, 'movies/seat_selection.html', {
        'theater': theater,
        'seats': seats
    })


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import razorpay
import json

@login_required
def verify_payment(request):
    payment_id = request.GET.get("payment_id")
    order_id = request.GET.get("order_id")
    signature = request.GET.get("signature")

    # 🔥 STEP 1: HANDLE SIMULATION
    if payment_id and payment_id.startswith("test_"):
        payment = Payment.objects.filter(razorpay_order_id=order_id).first()
        if payment and payment.status != "SUCCESS":
            _fulfill_booking(payment, "test_payment_123")
        return redirect("profile")

    # ❌ STEP 2: REAL PAYMENT
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
    except razorpay.errors.SignatureVerificationError:
        return HttpResponse("Invalid payment signature", status=400)
    
    payment = get_object_or_404(Payment, razorpay_order_id=order_id)
    if payment.status == "SUCCESS":
        return redirect("profile") # Already fulfilled
    
    _fulfill_booking(payment, payment_id)
    return redirect("profile")


def _fulfill_booking(payment, payment_id):
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(id=payment.id)
            if payment.status in ["SUCCESS", "FAILED_SEAT_UNAVAILABLE"]:
                return
            
            seat_ids = payment.seat_ids.split(",")
            # Ensure seats are locked for update to check exact current state
            seats = Seat.objects.select_for_update().filter(id__in=seat_ids)
            
            # Check for late payment timeouts where seat is already taken
            if any(seat.is_booked for seat in seats):
                payment.status = "FAILED_SEAT_UNAVAILABLE"
                payment.razorpay_payment_id = payment_id
                payment.save()
                return # Abort booking (trigger refund asynchronously in production)
            
            first_booking_id = None
            for seat in seats:
                seat.is_booked = True
                seat.is_locked = False
                seat.locked_at = None
                seat.save()

                booking = Booking.objects.create(
                    user=payment.user,
                    seat=seat,
                    movie=seat.theater.movie,
                    theater=seat.theater,
                    payment=payment
                )
                if not first_booking_id:
                    first_booking_id = booking.id
            
            payment.status = "SUCCESS"
            payment.razorpay_payment_id = payment_id
            payment.is_verified = True
            payment.save()

            if first_booking_id:
                transaction.on_commit(
                    lambda b_id=first_booking_id: NotificationService.send_booking_confirmation(b_id)
                )

    except Exception as e:
        print("Error fulfilling booking", e)


@csrf_exempt
def razorpay_webhook(request):
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', 'test_secret') # Use fallback for test
    signature = request.headers.get('X-Razorpay-Signature')
    payload = request.body.decode('utf-8')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_webhook_signature(payload, signature, webhook_secret)
    except razorpay.errors.SignatureVerificationError:
        return HttpResponse("Invalid signature", status=400)

    try:
        event = json.loads(payload)
        event_type = event.get('event')

        if event_type == 'payment.captured':
            payment_entity = event['payload']['payment']['entity']
            order_id = payment_entity['order_id']
            payment_id = payment_entity['id']
            
            payment = Payment.objects.filter(razorpay_order_id=order_id).first()
            if payment and payment.status != "SUCCESS":
                _fulfill_booking(payment, payment_id)

        elif event_type == 'payment.failed':
            payment_entity = event['payload']['payment']['entity']
            order_id = payment_entity['order_id']
            
            payment = Payment.objects.filter(razorpay_order_id=order_id).first()
            if payment and payment.status != "SUCCESS":
                payment.status = "FAILED"
                payment.save()
                if payment.seat_ids:
                    seat_ids = payment.seat_ids.split(",")
                    Seat.objects.filter(id__in=seat_ids, is_booked=False).update(is_locked=False, locked_at=None)

    except json.JSONDecodeError:
        return HttpResponse("Invalid payload", status=400)
    
    return HttpResponse(status=200)
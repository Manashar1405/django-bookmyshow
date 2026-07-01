import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from movies.models import Booking

logger = logging.getLogger(__name__)

def send_booking_email_task(booking_id):
    """
    Background task to send booking confirmation email.
    Args:
        booking_id: The ID of the booking to confirm.
    """
    logger.info(f"Executing send_booking_email_task for booking_id: {booking_id}")
    
    try:
        # Fetch booking with related objects to avoid N+1 and ensure fresh data
        booking = Booking.objects.select_related(
            'user', 'movie', 'theater', 'seat', 'payment'
        ).get(id=booking_id)
        
        # Idempotency check: Don't resend if already sent successfully
        if booking.confirmation_email_sent_at:
            logger.info(f"Email already sent for booking_id: {booking_id} at {booking.confirmation_email_sent_at}")
            return
        
        # Prepare context
        # Gather all bookings associated with this payment to show all seats
        if booking.payment:
            related_bookings = booking.payment.bookings.select_related('seat').all()
            seat_numbers = ", ".join([str(b.seat.seat_number) for b in related_bookings])
        else:
            seat_numbers = booking.seat.seat_number
            
        context = {
            'user': booking.user,
            'movie': booking.movie,
            'theater': booking.theater,
            'booking': booking,
            'seat_numbers': seat_numbers,
            'amount_paid': (booking.payment.amount / 100) if booking.payment else 0, # Assuming amount is in paise
            'payment_id': booking.payment.razorpay_payment_id if booking.payment else None
        }
        
        subject = f"Booking Confirmed: {booking.movie.name} at {booking.theater.name}"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bookmyseat.local')
        to_email = [booking.user.email]
        
        if not booking.user.email:
            logger.warning(f"User {booking.user.username} has no email address. Skipping email for booking {booking_id}.")
            return
            
        # Render templates
        text_content = render_to_string('emails/booking_confirmation.txt', context)
        html_content = render_to_string('emails/booking_confirmation.html', context)
        
        # Send Email
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        
        # Mark as sent
        booking.confirmation_email_sent_at = timezone.now()
        booking.save(update_fields=["confirmation_email_sent_at"])
        
        logger.info(f"Successfully sent confirmation email for booking {booking_id}")
        
    except Booking.DoesNotExist:
        logger.error(f"Booking with id {booking_id} does not exist.")
        # We don't raise here, as retrying a non-existent booking will always fail.
        # This could happen if the transaction rolled back but the task somehow still queued,
        # which we prevent using transaction.on_commit, but good to be defensive.
    except Exception as e:
        logger.error(f"Failed to send email for booking {booking_id}: {str(e)}")
        raise # Reraise to trigger django-q retry logic

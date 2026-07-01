from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from movies.models import Movie, Theater, Seat, Booking, Payment
from movies.tasks.email import send_booking_email_task
from movies.services.notifications import NotificationService
from unittest.mock import patch

class EmailQueueTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.movie = Movie.objects.create(name='Test Movie', rating='8.0', cast='Actor A', trailer_url='http://test.com', image='test.jpg')
        self.theater = Theater.objects.create(name='Test Theater', movie=self.movie, time=timezone.now())
        self.seat = Seat.objects.create(theater=self.theater, seat_number='A1')
        
        self.payment = Payment.objects.create(
            user=self.user,
            seat_ids=str(self.seat.id),
            razorpay_order_id='order_test',
            amount=10000,
            status='SUCCESS',
            is_verified=True
        )
        
        self.booking = Booking.objects.create(
            user=self.user,
            seat=self.seat,
            movie=self.movie,
            theater=self.theater,
            payment=self.payment
        )

    @patch('movies.services.notifications.async_task')
    def test_notification_service_enqueues_task(self, mock_async_task):
        """Test that the notification service triggers the django-q async task"""
        NotificationService.send_booking_confirmation(self.booking.id)
        mock_async_task.assert_called_once_with('movies.tasks.email.send_booking_email_task', self.booking.id)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_task_execution_and_templates(self):
        """Test that the worker actually sends the email and renders both HTML/TXT formats"""
        send_booking_email_task(self.booking.id)
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        # Verify recipients and subject
        self.assertEqual(email.to, [self.user.email])
        self.assertIn('Test Movie', email.subject)
        
        # Verify content
        self.assertIn('A1', email.body)
        self.assertIn('Rs. 100', email.body) # 10000 paise = 100 Rs
        
        # Verify HTML alternative
        self.assertEqual(len(email.alternatives), 1)
        html_content, mimetype = email.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        self.assertIn('<span class="value">Test Movie</span>', html_content) # Depending on html template structure
        self.assertIn('A1', html_content)
        
        # Verify idempotency flag is set
        self.booking.refresh_from_db()
        self.assertIsNotNone(self.booking.confirmation_email_sent_at)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_idempotency(self):
        """Test that executing the task twice only sends one email"""
        # First run
        send_booking_email_task(self.booking.id)
        self.assertEqual(len(mail.outbox), 1)
        
        # Second run (simulating worker crash after success but before ack)
        send_booking_email_task(self.booking.id)
        # Still 1, didn't send again
        self.assertEqual(len(mail.outbox), 1)

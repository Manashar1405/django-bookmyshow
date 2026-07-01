import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Temporary notification service without background queue.
    Email sending is disabled on this machine.
    """

    @staticmethod
    def send_booking_confirmation(booking_id: int):
        """
        Temporarily disable async email sending.
        """

        logger.info(
            f"NotificationService: Email notification skipped for booking {booking_id}"
        )

        # Email queue disabled temporarily
        return True
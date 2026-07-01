from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone

def release_all_expired_seats():
    from .models import Seat # Lazy import to avoid AppRegistryNotReady
    expired_time = timezone.now() - timezone.timedelta(minutes=2)
    
    # Release expired seats globally for all theaters
    Seat.objects.filter(
        is_locked=True,
        locked_at__lt=expired_time
    ).update(is_locked=False, locked_at=None)

def start():
    scheduler = BackgroundScheduler()
    # Run the job every 1 minute
    scheduler.add_job(release_all_expired_seats, 'interval', minutes=1, id='release_seats_job', replace_existing=True)
    scheduler.start()

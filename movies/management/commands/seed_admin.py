import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Seeds a superuser from environment variables'

    def handle(self, *args, **options):
        # Fallback values for local testing, overridden by env vars in production
        username = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
        password = os.environ.get('DJANGO_ADMIN_PASSWORD', 'AdminSecret123!')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email='admin@example.com', password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}"'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists.'))

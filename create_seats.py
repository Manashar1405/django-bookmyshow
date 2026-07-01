import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from movies.models import Theater, Seat

theater = Theater.objects.first()

if not theater:
    print("❌ No theater found. Create one from admin first.")
else:
    for row in ['A', 'B', 'C', 'D']:
        for num in range(1, 9):
            seat_number = f"{row}{num}"

            if not Seat.objects.filter(theater=theater, seat_number=seat_number).exists():
                Seat.objects.create(
                    theater=theater,
                    seat_number=seat_number
                )

    print("✅ Seats created successfully!")

    
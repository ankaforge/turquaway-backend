from django.db import migrations, models
from django.db.models import Q


def deduplicate_tour_reservations(apps, schema_editor):
    TourReservation = apps.get_model('api', 'TourReservation')
    TourSession = apps.get_model('api', 'TourSession')

    duplicates = {}
    for reservation in TourReservation.objects.exclude(session__isnull=True).order_by('session_id', 'user_id', 'id'):
        key = (reservation.user_id, reservation.session_id)
        duplicates.setdefault(key, []).append(reservation)

    for reservations in duplicates.values():
        for duplicate in reservations[1:]:
            duplicate.delete()

    for session in TourSession.objects.all():
        total_guests = 0
        for reservation in TourReservation.objects.filter(session_id=session.id):
            total_guests += reservation.adults + reservation.children
        TourSession.objects.filter(id=session.id).update(booked_count=total_guests)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_tour_includes_free_food_drinks_and_more'),
    ]

    operations = [
        migrations.RunPython(deduplicate_tour_reservations, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='tourreservation',
            constraint=models.UniqueConstraint(
                fields=('user', 'session'),
                condition=Q(session__isnull=False),
                name='unique_user_tour_session_reservation',
            ),
        ),
    ]
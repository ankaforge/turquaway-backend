import re

from django.db import migrations


def normalize_icon_name(value):
    raw_value = str(value or '').strip()
    if not raw_value:
        return 'Activity'

    if re.fullmatch(r'[A-Z][A-Za-z0-9]*', raw_value):
        return raw_value

    parts = re.findall(r'[A-Za-z0-9]+', raw_value)
    if not parts:
        return 'Activity'

    return ''.join(part[:1].upper() + part[1:] for part in parts)


def forwards(apps, schema_editor):
    ActivityCategory = apps.get_model('api', 'ActivityCategory')

    for activity in ActivityCategory.objects.all().only('id', 'icon'):
        normalized_icon = normalize_icon_name(activity.icon)
        if activity.icon != normalized_icon:
            ActivityCategory.objects.filter(id=activity.id).update(icon=normalized_icon)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_tourreservation_unique_user_session'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
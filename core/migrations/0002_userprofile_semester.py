from django.conf import settings
from django.db import migrations, models
from django.utils import timezone

import core.models


def backfill_semester(apps, schema_editor):
    UserProfile = apps.get_model("core", "UserProfile")
    for profile in UserProfile.objects.select_related("user").iterator():
        account_date = timezone.localtime(profile.user.date_joined).date()
        if account_date.month >= 9 or (account_date.month == 1 and account_date.day <= 15):
            profile.semester = "semester_1"
        else:
            profile.semester = "semester_2"
        profile.save(update_fields=["semester"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="semester",
            field=models.CharField(
                choices=[("semester_1", "Semester 1"), ("semester_2", "Semester 2")],
                default=core.models.current_semester,
                max_length=12,
            ),
        ),
        migrations.RunPython(backfill_semester, migrations.RunPython.noop),
    ]

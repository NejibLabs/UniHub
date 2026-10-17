from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_specialty_cycle_userprofile_current_year"),
    ]

    operations = [
        migrations.AddField(
            model_name="resource",
            name="category",
            field=models.CharField(
                choices=[("exam", "Exam"), ("notes", "Notes"), ("other", "Other")],
                default="other",
                max_length=12,
            ),
        ),
    ]

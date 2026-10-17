from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_subject_semester_subject_year"),
    ]

    operations = [
        migrations.AddField(
            model_name="specialty",
            name="cycle",
            field=models.CharField(
                choices=[
                    ("preparatory", "Preparatory cycle"),
                    ("bachelor", "Bachelor"),
                    ("master", "Master"),
                    ("engineering", "Engineering cycle"),
                ],
                default="bachelor",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="current_year",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Year 1"), (2, "Year 2"), (3, "Year 3")],
                default=1,
            ),
        ),
    ]

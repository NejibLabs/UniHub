from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_resource_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="university",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]

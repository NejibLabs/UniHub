from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_userprofile_university"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="university",
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_job_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='accepting_applications',
            field=models.BooleanField(default=True),
        ),
    ]

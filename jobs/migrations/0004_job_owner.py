from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_job_category_job_contact_email_job_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='jobs', to=settings.AUTH_USER_MODEL),
        ),
    ]

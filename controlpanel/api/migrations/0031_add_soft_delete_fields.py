# Generated by Django 4.2.1 on 2023-10-09 15:33

# Third-party
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0030_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='s3bucket',
            name='deleted_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='s3bucket',
            name='deleted_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_s3buckets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='s3bucket',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]

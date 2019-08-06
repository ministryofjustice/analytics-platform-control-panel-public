# Generated by Django 2.2.3 on 2019-07-10 06:39

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_user_last_name_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('key', models.CharField(max_length=50, validators=[django.core.validators.RegexValidator('[a-zA-Z0-9_]{1,50}')])),
                ('description', models.CharField(max_length=600)),
                ('app_type', models.CharField(choices=[('airflow', 'Airflow'), ('webapp', 'Web app')], max_length=8)),
                ('role_name', models.CharField(max_length=63, validators=[django.core.validators.RegexValidator('[a-zA-Z0-9_]{1,63}')])),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'control_panel_api_parameter',
                'ordering': ('-modified', '-created'),
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]
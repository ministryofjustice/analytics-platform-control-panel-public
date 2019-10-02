# Generated by Django 2.2.5 on 2019-09-25 16:46

from django.conf import settings
import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_DATA_add_tools'),
    ]

    operations = [
        migrations.CreateModel(
            name='IAMManagedPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=63, unique=True, validators=[django.core.validators.RegexValidator('[a-z0-9_+@,.:=-]{2,63}')])),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_iam_managed_policy', to=settings.AUTH_USER_MODEL)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'control_panel_api_iam_managed_policy',
                'ordering': ('-modified', '-created'),
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='apps3bucket',
            name='paths',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255, validators=[django.core.validators.RegexValidator('[a-zA-Z0-9_/\\*-]')]), default=list, size=None),
        ),
        migrations.AddField(
            model_name='users3bucket',
            name='paths',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255, validators=[django.core.validators.RegexValidator('[a-zA-Z0-9_/\\*-]')]), default=list, size=None),
        ),
        migrations.CreateModel(
            name='PolicyS3Bucket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('access_level', models.CharField(choices=[('readonly', 'Read-only'), ('readwrite', 'Read-write')], default='readonly', max_length=9)),
                ('paths', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255, validators=[django.core.validators.RegexValidator('[a-zA-Z0-9_/\\*-]')]), default=list, size=None)),
                ('policy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='policys3buckets', to='api.IAMManagedPolicy')),
                ('s3bucket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='policys3buckets', to='api.S3Bucket')),
            ],
            options={
                'db_table': 'control_panel_api_policys3bucket',
                'ordering': ('id',),
                'unique_together': {('policy', 's3bucket')},
            },
        ),
    ]
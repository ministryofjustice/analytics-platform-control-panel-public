# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-30 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_app_description'),
    ]

    replaces = [('control_panel_api', '0003_user_email_verified')]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
    ]
# Generated by Django 3.1.6 on 2021-08-31 13:27

# Third-party
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0014_tool_target_infrastructure"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tool",
            name="values",
            field=models.JSONField(default=dict),
        ),
    ]

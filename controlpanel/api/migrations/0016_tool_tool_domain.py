# Generated by Django 3.1.6 on 2021-10-04 12:21

# Third-party
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0015_auto_20210831_1327"),
    ]

    operations = [
        migrations.AddField(
            model_name="tool",
            name="tool_domain",
            field=models.SlugField(
                blank=True,
                default=None,
                help_text='Name to use in the tool\'s domain instead of chart name. E.g. use the standard "jupyter-lab" instead of a custom chart name.',  # noqa: E501
                max_length=100,
                null=True,
            ),
        ),
    ]

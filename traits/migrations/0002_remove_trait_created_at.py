# Generated by Django 4.2 on 2023-04-12 23:40

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("traits", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="trait",
            name="created_at",
        ),
    ]

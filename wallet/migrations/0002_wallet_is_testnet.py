# Generated by Django 5.0.2 on 2025-02-02 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallet',
            name='is_testnet',
            field=models.BooleanField(default=True),
        ),
    ]

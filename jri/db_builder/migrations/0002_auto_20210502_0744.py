# Generated by Django 3.2 on 2021-05-01 22:44

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('db_builder', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='infixation',
            name='date_added',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='infixation',
            name='video_title',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]

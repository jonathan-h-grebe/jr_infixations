# Generated by Django 3.1.7 on 2021-06-14 00:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db_builder', '0006_auto_20210602_1757'),
    ]

    operations = [
        migrations.CreateModel(
            name='Part_Checked_Vids',
            fields=[
                ('vid_id', models.CharField(max_length=11, primary_key=True, serialize=False)),
                ('next_page_token', models.CharField(max_length=120)),
                ('vid_title', models.CharField(blank=True, max_length=50)),
            ],
        ),
    ]

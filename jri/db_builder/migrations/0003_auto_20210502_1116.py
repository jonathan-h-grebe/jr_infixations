# Generated by Django 3.2 on 2021-05-02 02:16

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('db_builder', '0002_auto_20210502_0744'),
    ]

    operations = [
        migrations.CreateModel(
            name='Checked_CommentThreads',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment_thread_id', models.CharField(max_length=11)),
                ('vid_title', models.CharField(blank=True, max_length=50)),
                ('checked_date', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Checked_Vids',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vid_id', models.CharField(max_length=11)),
                ('vid_title', models.CharField(blank=True, max_length=50)),
                ('checked_date', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.RenameField(
            model_name='infixation',
            old_name='video_title',
            new_name='vid_title',
        ),
    ]

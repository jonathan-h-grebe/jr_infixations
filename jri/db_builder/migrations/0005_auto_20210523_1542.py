# Generated by Django 3.1.7 on 2021-05-23 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db_builder', '0004_alter_infixation_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='infixation',
            name='likes',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='checked_commentthreads',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='Checked_Vids',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='infixation',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]

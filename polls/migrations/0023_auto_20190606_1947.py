# Generated by Django 2.2.1 on 2019-06-06 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0022_auto_20190606_1941'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventgroup',
            name='events',
        ),
        migrations.AddField(
            model_name='event',
            name='groups',
            field=models.ManyToManyField(to='polls.EventGroup', verbose_name='événement'),
        ),
    ]
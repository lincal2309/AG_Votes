# Generated by Django 2.2.1 on 2019-06-06 22:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0024_auto_20190607_0021'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserPoll',
        ),
    ]

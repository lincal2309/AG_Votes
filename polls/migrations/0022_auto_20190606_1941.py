# Generated by Django 2.2.1 on 2019-06-06 17:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("polls", "0021_auto_20190606_1941")]

    operations = [
        migrations.RenameField(
            model_name="eventgroup", old_name="event", new_name="events"
        ),
        migrations.RenameField(
            model_name="eventgroup", old_name="user", new_name="users"
        ),
    ]

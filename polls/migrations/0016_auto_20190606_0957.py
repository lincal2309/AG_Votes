# Generated by Django 2.2.1 on 2019-06-06 07:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("polls", "0015_eventgroup_evt_group")]

    operations = [
        migrations.AlterField(
            model_name="eventgroup",
            name="evt_group",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="auth.Group"
            ),
        )
    ]

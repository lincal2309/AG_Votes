# Generated by Django 2.2.2 on 2019-06-24 09:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("polls", "0041_auto_20190624_0930")]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="polls.Company",
                verbose_name="société",
            ),
        )
    ]

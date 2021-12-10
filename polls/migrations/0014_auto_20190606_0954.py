# Generated by Django 2.2.1 on 2019-06-06 07:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("polls", "0013_uservote_proxy_confirmed"),
    ]

    operations = [
        migrations.RemoveField(model_name="eventgroup", name="evt_group"),
        migrations.RemoveField(model_name="uservote", name="proxy_confirmed"),
        migrations.RemoveField(model_name="uservote", name="proxy_user"),
        migrations.AddField(
            model_name="eventgroup",
            name="group_name",
            field=models.CharField(default="Groupe", max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="question", name="question_text", field=models.TextField()
        ),
        migrations.CreateModel(
            name="UserGroup",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("vote_weight", models.IntegerField(default=0)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="polls.Event"
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="polls.EventGroup",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"verbose_name": "Groupe"},
        ),
        migrations.CreateModel(
            name="Procuration",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("proxy_date", models.DateField()),
                ("proxy_confirmed", models.BooleanField(default=False)),
                ("confirm_date", models.DateField()),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="polls.Event"
                    ),
                ),
                (
                    "proxy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proxy",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"verbose_name": "Procuration"},
        ),
    ]

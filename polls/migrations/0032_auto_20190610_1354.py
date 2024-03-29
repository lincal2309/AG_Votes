# Generated by Django 2.2.1 on 2019-06-10 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("polls", "0031_uservote_nb_user_votes")]

    operations = [
        migrations.AddField(
            model_name="company",
            name="host",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="company",
            name="host_password",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="company",
            name="host_user",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="company", name="port", field=models.IntegerField(null=True)
        ),
        migrations.AddField(
            model_name="company",
            name="use_tls",
            field=models.BooleanField(default=True),
        ),
    ]

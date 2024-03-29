# Generated by Django 2.2.2 on 2019-06-18 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("polls", "0036_auto_20190612_0837")]

    operations = [
        migrations.AlterField(
            model_name="company",
            name="address2",
            field=models.CharField(
                blank=True,
                max_length=300,
                null=True,
                verbose_name="complément d'adresse",
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="fax",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="mot de passe"
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="hname",
            field=models.EmailField(
                blank=True, max_length=100, null=True, verbose_name="utilisateur"
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="host",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="serveur mail"
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="img/"),
        ),
        migrations.AlterField(
            model_name="company",
            name="port",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="port du serveur"
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="street_cplt",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="complément"
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="street_num",
            field=models.IntegerField(blank=True, null=True, verbose_name="N° de rue"),
        ),
        migrations.AlterField(
            model_name="company",
            name="use_tls",
            field=models.BooleanField(
                blank=True, default=True, verbose_name="authentification requise"
            ),
        ),
        migrations.AlterField(
            model_name="procuration",
            name="confirm_date",
            field=models.DateField(
                blank=True, null=True, verbose_name="date de confirmation"
            ),
        ),
        migrations.AddConstraint(
            model_name="choice",
            constraint=models.UniqueConstraint(
                fields=("event", "choice_no"), name="unique_choice_no_per_event"
            ),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.UniqueConstraint(
                fields=("company_id", "slug"), name="unique_slug"
            ),
        ),
        migrations.AddConstraint(
            model_name="question",
            constraint=models.UniqueConstraint(
                fields=("event", "question_no"), name="unique_question_no_per_event"
            ),
        ),
    ]

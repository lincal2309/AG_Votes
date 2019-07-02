# Generated by Django 2.2.2 on 2019-06-12 06:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("polls", "0035_auto_20190612_0818")]

    operations = [
        migrations.AddField(
            model_name="company",
            name="siret",
            field=models.CharField(
                default="82148229600018", max_length=50, verbose_name="SIRET"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="company",
            name="statut",
            field=models.CharField(
                default="SCIC – SAS à capital variable",
                max_length=50,
                verbose_name="forme juridique",
            ),
            preserve_default=False,
        ),
    ]

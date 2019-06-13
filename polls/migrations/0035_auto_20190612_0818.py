# Generated by Django 2.2.2 on 2019-06-12 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0034_auto_20190610_1405'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='host_password',
        ),
        migrations.RemoveField(
            model_name='company',
            name='host_user',
        ),
        migrations.AddField(
            model_name='company',
            name='address1',
            field=models.CharField(default='rue de Lasserre', max_length=300, verbose_name='adresse'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='company',
            name='address2',
            field=models.CharField(max_length=300, null=True, verbose_name="complément d'adresse"),
        ),
        migrations.AddField(
            model_name='company',
            name='city',
            field=models.CharField(default='Le Fousseret', max_length=200, verbose_name='ville'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='company',
            name='fax',
            field=models.CharField(max_length=50, null=True, verbose_name='mot de passe'),
        ),
        migrations.AddField(
            model_name='company',
            name='hname',
            field=models.EmailField(max_length=100, null=True, verbose_name='utilisateur'),
        ),
        migrations.AddField(
            model_name='company',
            name='street_cplt',
            field=models.CharField(max_length=50, null=True, verbose_name='complément'),
        ),
        migrations.AddField(
            model_name='company',
            name='street_num',
            field=models.IntegerField(null=True, verbose_name='N° de rue'),
        ),
        migrations.AddField(
            model_name='company',
            name='zip_code',
            field=models.IntegerField(default=31430, verbose_name='code postal'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='company',
            name='host',
            field=models.CharField(max_length=50, null=True, verbose_name='serveur mail'),
        ),
        migrations.AlterField(
            model_name='company',
            name='port',
            field=models.IntegerField(null=True, verbose_name='port du serveur'),
        ),
        migrations.AlterField(
            model_name='company',
            name='use_tls',
            field=models.BooleanField(default=True, verbose_name='authentification requise'),
        ),
    ]

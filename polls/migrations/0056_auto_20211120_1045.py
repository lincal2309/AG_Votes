# Generated by Django 2.2.12 on 2021-11-20 09:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0055_usergroup_hidden'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='usercomp',
            options={'verbose_name': 'Profil utilisateurs', 'verbose_name_plural': 'Profils utilisateurs'},
        ),
    ]

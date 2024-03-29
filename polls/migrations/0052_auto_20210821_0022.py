# Generated by Django 2.2.12 on 2021-08-20 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0051_compsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='compsettings',
            name='rule',
            field=models.CharField(choices=[('MAJ', 'Majorité'), ('PROP', 'Proportionnelle')], default='MAJ', max_length=5, verbose_name='mode de scrutin'),
        ),
        migrations.AlterField(
            model_name='compsettings',
            name='upd_rule',
            field=models.BooleanField(default=False, verbose_name='choisir la règle de répartition pour chaque événement'),
        ),
        migrations.AlterField(
            model_name='compsettings',
            name='use_groups',
            field=models.BooleanField(default=False, verbose_name='utilise les groupes'),
        ),
    ]

# Generated by Django 2.2.1 on 2019-06-08 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0030_auto_20190608_1023'),
    ]

    operations = [
        migrations.AddField(
            model_name='uservote',
            name='nb_user_votes',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
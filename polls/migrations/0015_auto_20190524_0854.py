# Generated by Django 2.2.1 on 2019-05-24 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0014_question_question_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_no',
            field=models.IntegerField(),
        ),
    ]

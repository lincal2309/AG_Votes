# Generated by Django 2.2.1 on 2019-06-06 07:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        ('polls', '0014_auto_20190606_0954'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventgroup',
            name='evt_group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='auth.Group'),
            preserve_default=False,
        ),
    ]
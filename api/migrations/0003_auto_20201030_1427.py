# Generated by Django 3.1.2 on 2020-10-30 14:27

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20201030_1403'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskreminder',
            name='recipients',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(default='Unnamed', max_length=256), size=None),
        ),
    ]
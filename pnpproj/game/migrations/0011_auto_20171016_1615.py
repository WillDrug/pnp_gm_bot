# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-16 13:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0010_auto_20171016_1408'),
    ]

    operations = [
        migrations.AlterField(
            model_name='players',
            name='last_seen',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

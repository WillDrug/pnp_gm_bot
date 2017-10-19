# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-19 08:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='action',
            old_name='char',
            new_name='character',
        ),
        migrations.RenameField(
            model_name='roll',
            old_name='char',
            new_name='character',
        ),
        migrations.AddField(
            model_name='charparm',
            name='base_dice',
            field=models.IntegerField(default=100),
        ),
    ]

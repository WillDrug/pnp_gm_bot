# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-01 21:15
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import game.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('display_name', models.CharField(max_length=50)),
                ('known', models.BooleanField(default=False)),
                ('flavour', models.CharField(max_length=250)),
                ('experience', models.IntegerField()),
                ('levelup', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Combat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            bases=(models.Model, game.models.Parm),
        ),
        migrations.CreateModel(
            name='Feats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('char', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Character')),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('flavour', models.CharField(max_length=250)),
            ],
        ),
        migrations.CreateModel(
            name='Hidden',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            bases=(models.Model, game.models.Parm),
        ),
        migrations.CreateModel(
            name='Influence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apply_to', models.CharField(max_length=50)),
                ('apply_num', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='InfluenceItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('char', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Character')),
                ('influence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.InfluenceItem')),
            ],
        ),
        migrations.CreateModel(
            name='Players',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_seen', models.DateTimeField()),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Game')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Secondary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            bases=(models.Model, game.models.Parm),
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('flavour', models.CharField(max_length=250)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Stats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            bases=(models.Model, game.models.Parm),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('turns', models.IntegerField(default=-1)),
                ('char', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Character')),
                ('influence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.InfluenceItem')),
            ],
        ),
        migrations.CreateModel(
            name='Tertiary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            bases=(models.Model, game.models.Parm),
        ),
        migrations.AddField(
            model_name='influence',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.InfluenceItem'),
        ),
        migrations.AddField(
            model_name='game',
            name='setting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Setting'),
        ),
        migrations.AddField(
            model_name='feats',
            name='influence',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.InfluenceItem'),
        ),
        migrations.AddField(
            model_name='character',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Game'),
        ),
        migrations.AddField(
            model_name='character',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
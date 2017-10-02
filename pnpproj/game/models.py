import json
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError



def parm_validator(cls, value):
    if value not in cls.__restrictions__.keys():
        raise ValidationError(_('%(value)s не является подходящим значением'),
                              params={'value': value}, )


# Create your models here.
class Setting(models.Model):
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=20)
    flavour = models.CharField(max_length=250)


class Game(models.Model):
    setting = models.ForeignKey(Setting)
    name = models.CharField(max_length=20)
    flavour = models.CharField(max_length=250)


class Players(models.Model):
    game = models.ForeignKey(Game)
    user = models.ForeignKey(User)
    last_seen = models.DateTimeField()


class Character(models.Model):
    owner = models.ForeignKey(User)
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=30)
    display_name = models.CharField(max_length=50)
    known = models.BooleanField(default=False)
    flavour = models.CharField(max_length=250)
    experience = models.IntegerField()
    levelup = models.BooleanField(default=True)

class Parm:
    __cost__ = 1
    __restrictions__ = 'dynamic'
    char = models.ForeignKey(Character)
    value = models.IntegerField()

    def bonus(self):
        return self.value * 10

    def validate(self, value):
        if isinstance(__restrictions__, dict()):
            parm_validator(self.__class__, value)

    name = models.CharField(max_length=15, validators=[validate])

class Stats(models.Model, Parm):
    __cost__ = 25
    __restrictions__ = {
        'Сила': {
            'affected_by': '',
        },
        'Выносливость': {
            'affected_by': '',
        },
        'Ловкость': {
            'affected_by': ''
        },
        'Скорость': {
            'affected_by': ''
        },
        'Интеллект': {
            'affected_by': ''
        },
        'Внимание': {
            'affected_by': ''
        },
        'Воля': {
            'affected_by': ''
        },
        'Харизма': {
            'affected_by': ''
        }

    }

    def bonus(self, influence):
        stat = self.value + influence
        if stat == 0:
            return -200
        elif stat == 1:
            return -100
        elif stat == 2:
            return -50
        elif stat == 3:
            return -25
        elif stat == 4:
            return -10
        elif stat == 5:
            return 0
        elif stat == 6 or stat == 7:
            return 5
        elif stat == 8 or stat == 9:
            return 10
        elif stat >= 10:
            return 15 + 5 * (stat - 10)


class Secondary(models.Model, Parm):
    __cost__ = 5
    __restrictions__ = {
        'Акробатика': {
            'affected_by': '+Stats/Ловкость',
        },
        'Атлетика': {
            'affected_by': '+Stats/Сила',
        },
        'Оккультизм': {
            'affected_by': '+Stats/Внимание,+Stats/Интеллект'
        },
        'Наблюдательность': {
            'affected_by': '+Stats/Внимание'
        },
        'Социализация': {
            'affected_by': '+Stats/Харизма'
        },
        'Стиль': {
            'affected_by': '+Stats/Харизма'
        }
    }


class Tertiary(models.Model, Parm):
    __cost__ = 1
    __restrictions__ = 'dynamic'


class Combat(models.Model, Parm):
    __cost__ = 10
    __restrictions__ = {
        'Атака': {
            'affected_by': '+Stats/Ловкость'
        },
        'Блок': {
            'affected_by': '+Stats/Ловкость'
        },
        'Уклонение': {
            'affected_by': '+Stats/Ловкость'
        }
    }


class Hidden(models.Model, Parm):
    __cost__ = 0
    __restrictions__ = {
        'Инициатива': {
            'affected_by': '+Stats/Ловкость,+Stats/Скорость'
        },
        'Здоровье': {
            'affected_by': '+Stats/Выносливость'
        }
    }

class InfluenceItem(models.Model):
    type = models.CharField(max_length=15)

class Inventory(models.Model):
    char = models.ForeignKey(Character)
    name = models.CharField(max_length=25)
    influence = models.ForeignKey(InfluenceItem)


class Feats(models.Model):
    char = models.ForeignKey(Character)
    name = models.CharField(max_length=25)
    influence = models.ForeignKey(InfluenceItem)


class Status(models.Model):
    char = models.ForeignKey(Character)
    name = models.CharField(max_length=25)
    turns = models.IntegerField(default=-1)
    influence = models.ForeignKey(InfluenceItem)

class Influence(models.Model):
    item = models.ForeignKey(InfluenceItem)  # stack
    apply_to = models.CharField(max_length=50)
    apply_num = models.IntegerField()

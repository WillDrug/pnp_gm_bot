import json
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save

# Create your models here.
class Setting(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    flavour = models.CharField(max_length=250)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Game(models.Model):
    setting = models.ForeignKey(Setting, blank=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    flavour = models.CharField(max_length=250)
    invite = models.CharField(max_length=16, unique=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

class Scene(models.Model):
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=50)
    flavour = models.CharField(max_length=2000)

class Languages(models.Model):
    setting = models.ForeignKey(Setting, blank=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)

class Players(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)

class Character(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    display_name = models.CharField(max_length=50)
    known = models.BooleanField(default=False)
    flavour = models.CharField(max_length=250)
    experience = models.IntegerField()
    levelup = models.BooleanField(default=True)
    scene = models.ForeignKey(Scene, blank=True, on_delete=models.PROTECT)
    languages = models.
    def __str__(self):
        return self.name if self.known else self.display_name

    def __unicode__(self):
        return self.name if self.known else self.display_name

class ParmGroup(models.Model):
    setting = models.ForeignKey(Setting, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    flavour = models.CharField(max_length=2000, blank=True)
    cost_to_add = models.IntegerField(default=40)

class CharParm(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    group = models.ForeignKey(ParmGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    flavour = models.CharField(max_length=2000)
    value = models.IntegerField()
    cost = models.IntegerField()
    affeced_by = models.ManyToManyField('self', symmetrical=False)

    def true_value(self):
        return 0  # to fix. how we display the value after items and shit.

    def roll(self):
        return 0  # to fix. rolls shit.

class InfSet(models.Model):
    reference = models.CharField(max_length=25)

class Status(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    item = models.ForeignKey(InfSet, on_delete=models.CASCADE)
    turns = models.IntegerField(blank=True)

class Item(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    item = models.ForeignKey(InfSet, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)
    count = models.IntegerField(default=1)

class Influence(models.Model):
    affects = models.ForeignKey(CharParm, on_delete=models.CASCADE)
    value = models.IntegerField()
    infset = models.ForeignKey(InfSet, on_delete=models.CASCADE)



@receiver(post_save, sender=Setting)
def populate_groups(sender, instance, created, *args, **kwargs):
    if created:
        parm = ParmGroup(setting=sender, name='Основное', cost_to_add=-1,
                         flavour='Основные параметры персонажа')
        parm = ParmGroup(setting=sender, name='Статы', cost_to_add=-1,
                         flavour='Базовые возможности персонажа')
        parm = ParmGroup(setting=sender, name='Вторичное', cost_to_add=-1,
                         flavour='Вторичные навыки')
        parm = ParmGroup(setting=sender, name='Третичное', cost_to_add=0,
                         flavour='Третичные наывки (как, например, вязание корзинок)')
        parm = ParmGroup(setting=sender, name='Бой', cost_to_add=-1,
                         flavour='Боевые способности персонажа')
        parm = ParmGroup(setting=sender, name='Магия', cost_to_add=-1,
                         flavour='Магические способности персонажа')
        parm = ParmGroup(setting=sender, name='Таланты', cost_to_add=50,
                         flavour='Особенности персонажа '
                                 '(Например возможность проецировать магию физической атакой или '
                                 'невосприимчивость к ядам, но НЕ умение обезоружить или заклинания '
                                 '(это в маневры) ')
        parm = ParmGroup(setting=sender, name='Умения', cost_to_add=25,
                         flavour='Боевые маневры, заклинания и другие приемы, которые выучил персонаж.'
                                 'Если действия персонажа, выбивающегося из обычного, нет в этом списке - '
                                 'Он хуже будет выполнять его.')

@receiver(post_save, sender=Character)
def populate_parms(sender, instance, created, *args, **kwargs):
    if created:
        # stats
        grp = ParmGroup.filter(setting=sender.game.setting).filter(name='Статы').first()
        strength = CharParm(character=sender, group=grp, name='Сила', value=5, cost=25, affeced_by=None,
                            flavour='Физическая сила персонажа -- я могу поднять помидор.').save()
        constitution = CharParm(character=sender, group=grp, name='Выносливость', value=5, cost=0, affeced_by=None,
                                flavour='Выносливость персонажа -- я могу съесть тухлый помидор').save()
        dexterity = CharParm(character=sender, group=grp, name='Ловкость', value=5, cost=25, affeced_by=None,
                             flavour='Ловкость персонажа -- я могу кинуть помидор').save()
        agility = CharParm(character=sender, group=grp, name='Скорость', value=5, cost=25, affeced_by=None,
                           flavour='Скорость персонажа -- я могу догнать помидор').save()
        intelligence = CharParm(character=sender, group=grp, name='Интеллект', value=5, cost=25, affeced_by=None,
                                flavour='Интеллект персонажа -- я знаю что помидор фрукт').save()
        perception = CharParm(character=sender, group=grp, name='Внимание', value=5, cost=25, affeced_by=None,
                              flavour='Внимание персонажа -- я могу следить за тремя помидорами').save()
        power = CharParm(character=sender, group=grp, name='Харизма', value=5, cost=25, affeced_by=None,
                         flavour='Сила Духа персонажа -- я могу заколдовать или продать '
                                 'фруктовый салат с помидором').save()
        willpower = CharParm(character=sender, group=grp, name='Воля', value=5, cost=25, affeced_by=None,
                             flavour='Сила Воли персонажа -- я могу устоять от того чтобы делать '
                                     'фруктовый салат с помидором').save()

        # core
        grp = ParmGroup.filter(setting=sender.game.setting).filter(name='Основное').first()
        initiative = CharParm(character=sender, group=grp, name='Инициатива', value=0, cost=10, affeced_by=None,
                              flavour='Определяет кто ходит первым')
        initiative.affeced_by.add(dexterity)
        initiative.affeced_by.add(agility)
        initiative.save()
        health = CharParm(character=sender, group=grp, name='Здоровье', value=5, cost=10, affeced_by=None,
                          flavour='Здоровье персонажа. Персонаж не имеет проблем пока успешно прокидывает '
                                  'сложность здоровья. Прокачивать здоровье проще, чем выносливость')
        health.affeced_by.add(constitution)
        health.save()

        # combat
        grp = ParmGroup.filter(setting=sender.game.setting).filter(name='Бой').first()
        attack = CharParm(character=sender, group=grp, name='Атака', value=0, cost=10, affeced_by=None,
                          flavour='Умение обращаться с оружием и наносить им урон (или обращаться с кулаками)')
        attack.affeced_by.add(dexterity)
        attack.save()
        block = CharParm(character=sender, group=grp, name='Блок', value=0, cost=10, affeced_by=None,
                         flavour='Умение останавливать удары (не делает кожу лезвие-непробиваемым)')
        block.affeced_by.add(dexterity)
        block.save()
        dodge = CharParm(character=sender, group=grp, name='', value=0, cost=10, affeced_by=None,
                         flavour='Умение уклоняться от ударов')
        dodge.affeced_by.add(dexterity)
        dodge.save()

        # magic
        grp = ParmGroup.filter(setting=sender.game.setting).filter(name='Магия').first()
        magic_level = CharParm(character=sender, group=grp, name='Уровень Магии', value=-1, cost=100, affeced_by=None,
                               flavour='Определяет максимальную сложность заклинаний вашего персонажа')
        magic_level.affeced_by.add(intelligence)
        magic_level.save()
        projection = CharParm(character=sender, group=grp, name='Проекция', value=0, cost=100, affeced_by=None,
                               flavour='Определяет насколько хорошо вы целитесь или защищаетесь заклинаниями')
        projection.affeced_by.add(power)
        projection.save()
        mana = CharParm(character=sender, group=grp, name='', value=0, cost=100, affeced_by=None,
                               flavour='Духовная усталость. Работает как здоровье.')
        mana.affeced_by.add(power)
        mana.save()

        # secondary
        grp = ParmGroup.filter(setting=sender.game.setting).filter(name='Вторичное').first()
        acrobatics = CharParm(character=sender, group=grp, name='Акробатика', value=0, cost=5, affeced_by=None,
                               flavour='Умение персонажа прыгать, гнуться и оказываться за спиной оппонента')
        acrobatics.affeced_by.add(dexterity)
        acrobatics.save()
        athletics = CharParm(character=sender, group=grp, name='Атлетика', value=0, cost=5, affeced_by=None,
                               flavour='Умение персонажа поднимать тяжести и управляться с доспехами')
        athletics.affeced_by.add(strength)
        athletics.save()
        occult = CharParm(character=sender, group=grp, name='Оккульт', value=0, cost=5, affeced_by=None,
                               flavour='Умение персонажа чувствовать колдунство перед собой и проводить ритуалы'
                                       '(По умолчанию магия не видна)')
        occult.affeced_by.add(perception)
        occult.affeced_by.add(magic_level)
        occult.save()
        notice = CharParm(character=sender, group=grp, name='Наблюдательность', value=0, cost=5, affeced_by=None,
                               flavour='Умение персонажа успешно найти вещь или выделить в толпе кого-то')
        notice.affeced_by.add(perception)
        social = CharParm(character=sender, group=grp, name='Социальное', value=0, cost=5, affeced_by=None,
                               flavour='Умение персонажа звучать убедительно')
        social.affeced_by.add(power)
        social.save()
        style = CharParm(character=sender, group=grp, name='Стиль', value=0, cost=5, affeced_by=None,
                               flavour='Умение персонажа круто выглядеть в любой ситуации. '
                                       'Это не третичный навык потому что быть крутым чего-то да стоит.')
        style.affeced_by.add(power)
        style.save()
        empathy = CharParm(character=sender, group=grp, name='Эмпатия', value=0, cost=5, affeced_by=None,
                           flavour='Умение "читать" других людей. Бросок идет против Стойкости.')
        empathy.affeced_by.add(perception)
        empathy.add()
        composure = CharParm(character=sender, group=grp, name='Стойкость', value=0, cost=5, affeced_by=None,
                               flavour='Умение персонажа не терять лицо и переносить боль. '
                                       'Влияет на контроль эмоций и перенос урона.')
        composure.affeced_by.add(willpower)
        composure.save()



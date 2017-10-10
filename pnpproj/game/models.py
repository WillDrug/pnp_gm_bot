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
    experience = models.IntegerField(default=0)
    levelup = models.BooleanField(default=False)
    scene = models.ForeignKey(Scene, blank=True, null=True, on_delete=models.PROTECT)
    pause = models.BooleanField(default=False)
    languages = models.ManyToManyField(Languages)

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
        instance.save()
        lang = Languages(setting=instance, name='common').save()
        parm = ParmGroup(setting=instance, name='Основное', cost_to_add=-1,
                         flavour='Основные параметры персонажа').save()
        parm = ParmGroup(setting=instance, name='Статы', cost_to_add=-1,
                         flavour='Базовые возможности персонажа').save()
        parm = ParmGroup(setting=instance, name='Вторичное', cost_to_add=-1,
                         flavour='Вторичные навыки').save()
        parm = ParmGroup(setting=instance, name='Третичное', cost_to_add=0,
                         flavour='Третичные наывки (как, например, вязание корзинок)').save()
        parm = ParmGroup(setting=instance, name='Бой', cost_to_add=-1,
                         flavour='Боевые способности персонажа').save()
        parm = ParmGroup(setting=instance, name='Магия', cost_to_add=-1,
                         flavour='Магические способности персонажа').save()
        parm = ParmGroup(setting=instance, name='Таланты', cost_to_add=50,
                         flavour='Особенности персонажа '
                                 '(Например возможность проецировать магию физической атакой или '
                                 'невосприимчивость к ядам, но НЕ умение обезоружить или заклинания '
                                 '(это в маневры) ').save()
        parm = ParmGroup(setting=instance, name='Умения', cost_to_add=25,
                         flavour='Боевые маневры, заклинания и другие приемы, которые выучил персонаж.'
                                 'Если действия персонажа, выбивающегося из обычного, нет в этом списке - '
                                 'Он хуже будет выполнять его.').save()


@receiver(post_save, sender=Character)
def populate_parms(sender, instance, created, *args, **kwargs):
    if created:
        instance.save()
        # stats
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Статы').first()
        strength = CharParm(character=instance, group=grp, name='Сила', value=1, cost=25,
                            flavour='Физическая сила персонажа -- я могу поднять помидор.')
        strength.save()
        constitution = CharParm(character=instance, group=grp, name='Выносливость', value=1, cost=0,
                                flavour='Выносливость персонажа -- я могу съесть тухлый помидор')
        constitution.save()
        dexterity = CharParm(character=instance, group=grp, name='Ловкость', value=1, cost=25,
                             flavour='Ловкость персонажа -- я могу кинуть помидор')
        dexterity.save()
        agility = CharParm(character=instance, group=grp, name='Скорость', value=1, cost=25,
                           flavour='Скорость персонажа -- я могу догнать помидор')
        agility.save()
        intelligence = CharParm(character=instance, group=grp, name='Интеллект', value=1, cost=25,
                                flavour='Интеллект персонажа -- я знаю что помидор фрукт')
        intelligence.save()
        perception = CharParm(character=instance, group=grp, name='Внимание', value=1, cost=25,
                              flavour='Внимание персонажа -- я могу следить за тремя помидорами')
        perception.save()
        power = CharParm(character=instance, group=grp, name='Харизма', value=1, cost=25,
                         flavour='Сила Духа персонажа -- я могу заколдовать или продать '
                                 'фруктовый салат с помидором')
        power.save()
        willpower = CharParm(character=instance, group=grp, name='Воля', value=1, cost=25,
                             flavour='Сила Воли персонажа -- я могу устоять от того чтобы делать '
                                     'фруктовый салат с помидором')
        willpower.save()

        # core
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Основное').first()
        initiative = CharParm(character=instance, group=grp, name='Инициатива', value=0, cost=10,
                              flavour='Определяет кто ходит первым')
        initiative.save()
        initiative.affeced_by.add(dexterity)
        initiative.affeced_by.add(agility)
        initiative.save()
        health = CharParm(character=instance, group=grp, name='Здоровье', value=1, cost=10,
                          flavour='Здоровье персонажа. Персонаж не имеет проблем пока успешно прокидывает '
                                  'сложность здоровья. Прокачивать здоровье проще, чем выносливость')
        health.save()
        health.affeced_by.add(constitution)
        health.save()

        # combat
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Бой').first()
        attack = CharParm(character=instance, group=grp, name='Атака', value=0, cost=10,
                          flavour='Умение обращаться с оружием и наносить им урон (или обращаться с кулаками)')
        attack.save()
        attack.affeced_by.add(dexterity)
        attack.save()
        block = CharParm(character=instance, group=grp, name='Блок', value=0, cost=10,
                         flavour='Умение останавливать удары (не делает кожу лезвие-непробиваемым)')
        block.save()
        block.affeced_by.add(dexterity)
        block.save()
        dodge = CharParm(character=instance, group=grp, name='Уклонение', value=0, cost=10,
                         flavour='Умение уклоняться от ударов')
        dodge.save()
        dodge.affeced_by.add(dexterity)
        dodge.save()

        # magic
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Магия').first()
        magic_level = CharParm(character=instance, group=grp, name='Уровень Магии', value=-1, cost=100,
                               flavour='Определяет максимальную сложность заклинаний вашего персонажа')
        magic_level.save()
        magic_level.affeced_by.add(intelligence)
        magic_level.save()
        projection = CharParm(character=instance, group=grp, name='Проекция', value=0, cost=100,
                              flavour='Определяет насколько хорошо вы целитесь или защищаетесь заклинаниями')
        projection.save()
        projection.affeced_by.add(power)
        projection.save()
        mana = CharParm(character=instance, group=grp, name='Мана', value=0, cost=100,
                        flavour='Духовная усталость. Работает как здоровье.')
        mana.save()
        mana.affeced_by.add(power)
        mana.save()

        # secondary
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Вторичное').first()
        acrobatics = CharParm(character=instance, group=grp, name='Акробатика', value=0, cost=5,
                              flavour='Умение персонажа прыгать, гнуться и оказываться за спиной оппонента')
        acrobatics.save()
        acrobatics.affeced_by.add(dexterity)
        acrobatics.save()
        athletics = CharParm(character=instance, group=grp, name='Атлетика', value=0, cost=5,
                             flavour='Умение персонажа поднимать тяжести и управляться с доспехами')
        athletics.save()
        athletics.affeced_by.add(strength)
        athletics.save()
        occult = CharParm(character=instance, group=grp, name='Оккульт', value=0, cost=5,
                          flavour='Умение персонажа чувствовать колдунство перед собой и проводить ритуалы'
                                  '(По умолчанию магия не видна)')
        occult.save()
        occult.affeced_by.add(perception)
        occult.affeced_by.add(magic_level)
        occult.save()
        notice = CharParm(character=instance, group=grp, name='Наблюдательность', value=0, cost=5,
                          flavour='Умение персонажа успешно найти вещь или выделить в толпе кого-то')
        notice.save()
        notice.affeced_by.add(perception)
        social = CharParm(character=instance, group=grp, name='Социальное', value=0, cost=5,
                          flavour='Умение персонажа звучать убедительно')
        social.save()
        social.affeced_by.add(power)
        social.save()
        style = CharParm(character=instance, group=grp, name='Стиль', value=0, cost=5,
                         flavour='Умение персонажа круто выглядеть в любой ситуации. '
                                 'Это не третичный навык потому что быть крутым чего-то да стоит.')
        style.save()
        style.affeced_by.add(power)
        style.save()
        empathy = CharParm(character=instance, group=grp, name='Эмпатия', value=0, cost=5,
                           flavour='Умение "читать" других людей. Бросок идет против Стойкости.')
        empathy.save()
        empathy.affeced_by.add(perception)
        empathy.save()
        composure = CharParm(character=instance, group=grp, name='Стойкость', value=0, cost=5,
                             flavour='Умение персонажа не терять лицо и переносить боль. '
                                     'Влияет на контроль эмоций и перенос урона.')
        composure.save()
        composure.affeced_by.add(willpower)
        composure.save()

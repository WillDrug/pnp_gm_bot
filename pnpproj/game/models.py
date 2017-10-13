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

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Players(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)


class Character(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, default='')
    display_name = models.CharField(max_length=50, default='')
    known = models.BooleanField(default=False)
    flavour = models.CharField(max_length=250, blank=True, default='')
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
    cost = models.IntegerField(default=1)


class CharParm(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    group = models.ForeignKey(ParmGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    flavour = models.CharField(max_length=2000)
    value = models.IntegerField()
    override_cost = models.IntegerField(default=-1)
    affected_by = models.ManyToManyField('self', symmetrical=False)

    def true_value(self):
        return 0  # to fix. how we display the value after items and shit.

    def roll(self):
        return 0  # to fix. rolls shit.

    @classmethod
    def from_db(cls, db, field_names, values):
        # Default implementation of from_db() (subject to change and could
        # be replaced with super()).
        if len(values) != len(cls._meta.concrete_fields):
            values = list(values)
            values.reverse()
            values = [
                values.pop() if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
                ]
        instance = cls(*values)
        instance._state.adding = False
        instance._state.db = db
        # customization to store the original field values on the instance
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def save(self, *args, **kwargs):
        if not self._state.adding:
            cost = self.override_cost if self.override_cost>-1 else self.group.cost
            self.character.experience -= (self.value-self._loaded_values['value'])*cost
            self.character.save()
        else:
            cost = self.group.cost_to_add
            self.character.experience -= cost
            self.character.save()
        super(CharParm, self).save(*args, **kwargs)


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
        lang = Languages(setting=instance, name='common')
        lang.save()
        parm = ParmGroup(setting=instance, name='Статы', cost_to_add=-1, cost=25,
                         flavour='Базовые возможности персонажа')
        parm.save()
        parm = ParmGroup(setting=instance, name='Основное', cost_to_add=-1, cost=10,
                         flavour='Основные параметры персонажа')
        parm.save()
        parm = ParmGroup(setting=instance, name='Бой', cost_to_add=-1, cost=10,
                         flavour='Боевые способности персонажа')
        parm.save()
        parm = ParmGroup(setting=instance, name='Магия', cost_to_add=-1, cost=100,
                         flavour='Магические способности персонажа. '
                                 'Если в таланты персонажа не добавлена магия стоимость умений будет зашкаливать')
        parm.save()
        parm = ParmGroup(setting=instance, name='Вторичное', cost_to_add=-1, cost=5,
                         flavour='Вторичные навыки')
        parm.save()
        parm = ParmGroup(setting=instance, name='Третичное', cost_to_add=0, cost=1,
                         flavour='Третичные наывки (как, например, вязание корзинок)')
        parm.save()
        parm = ParmGroup(setting=instance, name='Таланты', cost_to_add=50, cost=-1,
                         flavour='Особенности персонажа '
                                 '(Например возможность проецировать магию физической атакой или '
                                 'невосприимчивость к ядам, но НЕ умение обезоружить или заклинания '
                                 '(это в маневры) ')
        parm.save()
        parm = ParmGroup(setting=instance, name='Умения', cost_to_add=25, cost=-1,
                         flavour='Боевые маневры, заклинания и другие приемы, которые выучил персонаж.'
                                 'Если действия персонажа, выбивающегося из обычного, нет в этом списке - '
                                 'Он хуже будет выполнять его.')
        parm.save()


@receiver(post_save, sender=Character)
def populate_parms(sender, instance, created, *args, **kwargs):
    if created:
        instance.save()
        # stats
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Статы').first()
        strength = CharParm(character=instance, group=grp, name='Сила', value=1,
                            flavour='Физическая сила персонажа -- я могу поднять помидор.')
        strength.save()
        constitution = CharParm(character=instance, group=grp, name='Выносливость', value=1,
                                flavour='Выносливость персонажа -- я могу съесть тухлый помидор')
        constitution.save()
        dexterity = CharParm(character=instance, group=grp, name='Ловкость', value=1,
                             flavour='Ловкость персонажа -- я могу кинуть помидор')
        dexterity.save()
        agility = CharParm(character=instance, group=grp, name='Скорость', value=1,
                           flavour='Скорость персонажа -- я могу догнать помидор')
        agility.save()
        intelligence = CharParm(character=instance, group=grp, name='Интеллект', value=1,
                                flavour='Интеллект персонажа -- я знаю что помидор фрукт')
        intelligence.save()
        perception = CharParm(character=instance, group=grp, name='Внимание', value=1,
                              flavour='Внимание персонажа -- я могу следить за тремя помидорами')
        perception.save()
        power = CharParm(character=instance, group=grp, name='Харизма', value=1,
                         flavour='Сила Духа персонажа -- я могу заколдовать или продать '
                                 'фруктовый салат с помидором')
        power.save()
        willpower = CharParm(character=instance, group=grp, name='Воля', value=1,
                             flavour='Сила Воли персонажа -- я могу устоять от того чтобы делать '
                                     'фруктовый салат с помидором')
        willpower.save()

        # core
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Основное').first()
        initiative = CharParm(character=instance, group=grp, name='Инициатива', value=0,
                              flavour='Определяет кто ходит первым')
        initiative.save()
        initiative.affected_by.add(dexterity)
        initiative.affected_by.add(agility)
        initiative.save()
        health = CharParm(character=instance, group=grp, name='Здоровье', value=1,
                          flavour='Здоровье персонажа. Персонаж не имеет проблем пока успешно прокидывает '
                                  'сложность здоровья. Прокачивать здоровье проще, чем выносливость')
        health.save()
        health.affected_by.add(constitution)
        health.save()

        # combat
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Бой').first()
        attack = CharParm(character=instance, group=grp, name='Атака', value=0,
                          flavour='Умение обращаться с оружием и наносить им урон (или обращаться с кулаками)')
        attack.save()
        attack.affected_by.add(dexterity)
        attack.save()
        block = CharParm(character=instance, group=grp, name='Блок', value=0,
                         flavour='Умение останавливать удары (не делает кожу лезвие-непробиваемым)')
        block.save()
        block.affected_by.add(dexterity)
        block.save()
        dodge = CharParm(character=instance, group=grp, name='Уклонение', value=0,
                         flavour='Умение уклоняться от ударов')
        dodge.save()
        dodge.affected_by.add(dexterity)
        dodge.save()

        # magic
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Магия').first()
        magic_level = CharParm(character=instance, group=grp, name='Уровень Магии', value=-1,
                               flavour='Определяет максимальную сложность заклинаний вашего персонажа')
        magic_level.save()
        magic_level.affected_by.add(intelligence)
        magic_level.save()
        projection = CharParm(character=instance, group=grp, name='Проекция', value=0,
                              flavour='Определяет насколько хорошо вы целитесь или защищаетесь заклинаниями')
        projection.save()
        projection.affected_by.add(power)
        projection.save()
        mana = CharParm(character=instance, group=grp, name='Мана', value=0,
                        flavour='Духовная усталость. Работает как здоровье.')
        mana.save()
        mana.affected_by.add(power)
        mana.save()

        # secondary
        grp = ParmGroup.objects.filter(setting=instance.game.setting).filter(name='Вторичное').first()
        acrobatics = CharParm(character=instance, group=grp, name='Акробатика', value=0,
                              flavour='Умение персонажа прыгать, гнуться и оказываться за спиной оппонента')
        acrobatics.save()
        acrobatics.affected_by.add(dexterity)
        acrobatics.save()
        athletics = CharParm(character=instance, group=grp, name='Атлетика', value=0,
                             flavour='Умение персонажа поднимать тяжести и управляться с доспехами')
        athletics.save()
        athletics.affected_by.add(strength)
        athletics.save()
        occult = CharParm(character=instance, group=grp, name='Оккульт', value=0,
                          flavour='Умение персонажа чувствовать колдунство перед собой и проводить ритуалы'
                                  '(По умолчанию магия не видна)')
        occult.save()
        occult.affected_by.add(perception)
        occult.affected_by.add(magic_level)
        occult.save()
        notice = CharParm(character=instance, group=grp, name='Наблюдательность', value=0,
                          flavour='Умение персонажа успешно найти вещь или выделить в толпе кого-то')
        notice.save()
        notice.affected_by.add(perception)
        social = CharParm(character=instance, group=grp, name='Социальное', value=0,
                          flavour='Умение персонажа звучать убедительно')
        social.save()
        social.affected_by.add(power)
        social.save()
        style = CharParm(character=instance, group=grp, name='Стиль', value=0,
                         flavour='Умение персонажа круто выглядеть в любой ситуации. '
                                 'Это не третичный навык потому что быть крутым чего-то да стоит.')
        style.save()
        style.affected_by.add(power)
        style.save()
        empathy = CharParm(character=instance, group=grp, name='Эмпатия', value=0,
                           flavour='Умение "читать" других людей. Бросок идет против Стойкости.')
        empathy.save()
        empathy.affected_by.add(perception)
        empathy.save()
        composure = CharParm(character=instance, group=grp, name='Стойкость', value=0,
                             flavour='Умение персонажа не терять лицо и переносить боль. '
                                     'Влияет на контроль эмоций и перенос урона.')
        composure.save()
        composure.affected_by.add(willpower)
        composure.save()

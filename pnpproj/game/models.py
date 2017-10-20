import json
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save
import re
from barnum import gen_data

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

    def __str__(self):
        return self.name

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
    last_seen = models.DateTimeField(auto_now_add=True)

    @property
    def get_char(self): #would return just one char for GM but who gives a shit
        return Character.objects.filter(game=self.game).filter(owner=self.user).first()

class Character(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, default='')
    display_name = models.CharField(max_length=50, default='')
    known = models.BooleanField(default=False)
    flavour = models.CharField(max_length=250, blank=True, default='')
    experience = models.IntegerField(default=0)
    levelup = models.BooleanField(default=False)
    scene = models.ForeignKey(Scene, blank=True, null=True, on_delete=models.SET_NULL)
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
    base_dice = models.IntegerField(default=100)
    name = models.CharField(max_length=50)
    flavour = models.CharField(max_length=2000)
    value = models.IntegerField()
    override_cost = models.IntegerField(default=-1)
    affected_by = models.ManyToManyField('self', symmetrical=False)

    def __str__(self):
        return self.group.name+'/'+self.name

    def roll_bonus(self, root=list()):
        val = self.value
        if self.name in root:
            return self.value
        root.append(self.name)
        for aff in self.affected_by.all():
            val += int(aff.roll_bonus(root))
        influences = Influence.objects.filter(infset__character=self.character).filter(affects=self).all()
        for inf in influences:
            val += int(inf.value)
        return val


    def true_value(self, root=list()):
        val = self.value
        if self.name in root:
            return self.value
        root.append(self.name)
        for aff in self.affected_by.all():
            val += int(aff.true_value(root))
        influences = Influence.objects.filter(infset__character=self.character).filter(affects=self).\
            filter(visible=True).all()
        for inf in influences:
            val += int(inf.value)
        return val  # to fix. how we display the value after items and shit.


    def affected_string(self):
        textlist = dict()
        for aff in self.affected_by.all():
            textlist[aff.name] = aff.true_value()
        influences = Influence.objects.filter(infset__character=self.character).filter(affects=self).\
            filter(visible=True).all()
        for inf in influences:
            item = Item.objects.filter(item=inf.infset).first()
            status = Status.objects.filter(item=inf.infset).first()
            if item is not None:
                textlist[item.name] = inf.value
            elif status is not None:
                if status.visible:
                    textlist[status.name] = inf.value
        return textlist

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
        if not self._state.adding and hasattr(self, '_loaded_values'):
            cost = self.override_cost if self.override_cost > -1 else self.group.cost
            self.character.experience -= (self.value-self._loaded_values['value'])*cost
            self.character.save()
        else:
            cost = self.group.cost_to_add if self.group.cost_to_add > -1 else 0
            self.character.experience -= cost
            self.character.save()
        super(CharParm, self).save(*args, **kwargs)


class InfSet(models.Model):
    character = models.ForeignKey(Character)
    reference = models.CharField(max_length=250)

    def affected_string(self):
        affects = Influence.objects.filter(infset=self).all()
        aff_list = dict()
        for aff in affects:
            if aff.visible:
                aff_list[aff.affects.name] = aff.value
            else:
                aff_list['???'] = '???'
        return aff_list

    def __str__(self):
        return self.reference

class Status(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    item = models.ForeignKey(InfSet, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    turns = models.IntegerField(blank=True, null=True)

    def affected_string(self):
        aff_list = self.item.affected_string()
        return aff_list



class Item(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    item = models.ForeignKey(InfSet, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=50)
    flavour = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=False)
    count = models.IntegerField(default=1)

    def affected_string(self):
        aff_list = self.item.affected_string()
        return aff_list

class Influence(models.Model):
    affects = models.ForeignKey(CharParm, on_delete=models.CASCADE)
    value = models.IntegerField()
    visible = models.BooleanField()
    infset = models.ForeignKey(InfSet, on_delete=models.CASCADE)


class Action(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    game = models.ForeignKey(Game)
    character = models.ForeignKey(Character, null=True)
    scene = models.ForeignKey(Scene, null=True, on_delete=models.SET_NULL)
    scene_name = models.CharField(max_length=250)
    action = models.CharField(max_length=5000)
    phrase = models.CharField(max_length=5000, blank=True)
    language = models.ForeignKey(Languages, null=True)
    response = models.CharField(max_length=5000, blank=True)
    finished = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    def get_text(self, char):
        if self.phrase == '' or self.language is None:
            return ''
        if char is None:
            return self.phrase
        if self.language in self.character.languages.all():
            return self.phrase
        else:
            sentences = list()
            temp = ''
            for a in self.phrase+' ':
                if a in ['.', '!', '?']:
                    temp += a
                elif temp != '':
                    sentences.append(temp)
                    temp = ''

            new_phrase = ''
            if sentences.__len__() == 0:
                new_phrase = gen_data.create_sentence()
            for sentence in sentences:
                to_append = gen_data.create_sentence()
                to_append = to_append[:-1]
                to_append += sentence + ' '
                new_phrase += to_append
            return new_phrase

class Roll(models.Model):

    added = models.DateTimeField(auto_now_add=True)
    action = models.ForeignKey(Action)
    character = models.ForeignKey(Character, on_delete=models.CASCADE, null=True)
    parm = models.ForeignKey(CharParm, on_delete=models.SET_NULL, null=True)
    parm_name = models.CharField(max_length=250)
    base_dice = models.IntegerField(default=100)
    dice_roll = models.IntegerField(default=0)
    parm_bonus = models.IntegerField(default=0)
    free_bonus = models.IntegerField(default=0)
    difficulty = models.IntegerField(default=0)
    # pass\surpass = diff - sum.

    def make_roll(self, action, char=None):
        if self.parm_name == '':
            self.parm_name = self.parm.name
        if char is not None:
            self.character = char
        self.dice_roll = 100  #do random
        self.parm_bonus = 0 if self.parm is None else self.parm.roll_bonus()
        self.action = action

    def show_roll(self, player):
        roll = dict()
        visibility = RollVisibility.objects.filter(roll=self.pk).filter(player=player).first()
        if visibility is None:
            full_visibility = dict(
                base_dice=self.base_dice,
                dice_roll=self.dice_roll,
                parm_bonus=self.parm_bonus,
                free_bonus=self.free_bonus,
                difficulty=self.difficulty,
                result=self.dice_roll+self.parm_bonus+self.free_bonus-self.difficulty,
            )
            if full_visibility['result'] > 0:
                full_visibility['passed'] = 'true'
            elif full_visibility['result'] < 0:
                full_visibility['passed'] = 'false'
            else:
                full_visibility['passed'] = 'tie'
            return full_visibility

        roll['base_dice'] = self.base_dice
        roll['dice_roll'] = self.dice_roll if visibility.visible_dice_roll else '???'
        roll['parm_bonus'] = self.parm_bonus if visibility.visible_parm_bonus else '???'
        roll['free_bonus'] = self.free_bonus if visibility.visible_free_bonus else '???'
        roll['difficulty'] = self.difficulty if visibility.visible_difficulty else '???'
        roll['result'] = self.dice_roll+self.parm_bonus+self.free_bonus-self.difficulty if visibility.visible_result else '???'
        if not visibility.visible_passed:
            roll['passed'] = '???'
        elif roll['result'] > 0:
            roll['passed'] = 'true'
        elif roll['result'] < 0:
            roll['passed'] = 'false'
        else:
            roll['passed'] = 'tie'
        return roll

class RollVisibility(models.Model):
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE)
    player = models.ForeignKey(Players, on_delete=models.CASCADE)
    visible_dice_roll = models.BooleanField(default=True)
    visible_parm_bonus = models.BooleanField(default=True)
    visible_free_bonus = models.BooleanField(default=True)
    visible_difficulty = models.BooleanField(default=True)
    visible_result = models.BooleanField(default=True)
    visible_passed = models.BooleanField(default=True)




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
        if grp is not None:
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
        if grp is not None:
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
        if grp is not None:
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
        if grp is not None:
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
        if grp is not None:
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


import base64
import hashlib
import time

from django import forms
from game.models import Game, Setting, Character, Languages, ParmGroup, Scene, CharParm, Item, InfSet, Status, Action, \
    Roll, RollVisibility


class NewSettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ('name', 'flavour')

    name = forms.CharField(widget=forms.TextInput(), label='Название Сеттинга')
    flavour = forms.CharField(widget=forms.Textarea(), label='Описание Сеттинга')


class NewGameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ('setting', 'name', 'flavour', 'invite')

    setting = forms.ModelChoiceField(queryset=Setting.objects.all(), empty_label=None)
    name = forms.CharField(widget=forms.TextInput(), label='Название Игры')
    flavour = forms.CharField(widget=forms.Textarea(), label='Описание Игры')
    invite = forms.CharField(widget=forms.HiddenInput(), label='invite_link')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(NewGameForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['setting'].queryset = Setting.objects.filter(owner=user)
        hasher = hashlib.sha1(user.__str__().encode('utf-8') + str(time.time()).encode('utf-8'))
        self.fields['invite'] = forms.CharField(
            initial=base64.urlsafe_b64encode(hasher.digest()[0:10]).decode('utf-8'),
            widget=forms.HiddenInput()
        )


class BaseCharForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ('name', 'display_name', 'flavour', 'languages')

    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), label='Имя персонажа')
    display_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}),
                                   label='Обозначение персонажа (пока неизвестно имя)')
    flavour = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}),
                              label='Описание персонажа')
    languages = forms.ModelMultipleChoiceField(queryset=Languages.objects.none(), label='Языки', required=False)

    def __init__(self, *ar, **kw):
        super(BaseCharForm, self).__init__(*ar, **kw)
        self.fields['languages'].queryset = Languages.objects.filter(setting=self.instance.game.setting).all()


class GMCharForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ('known', 'experience', 'levelup', 'scene', 'pause')

    levelup = forms.BooleanField(required=False)
    known = forms.BooleanField(required=False)
    experience = forms.IntegerField(required=False)
    pause = forms.BooleanField(required=False)
    scene = forms.ModelChoiceField(queryset=Scene.objects.none(), required=False)

    def __init__(self, *ar, **kw):
        super(GMCharForm, self).__init__(*ar, **kw)
        self.fields['scene'].queryset = Scene.objects.filter(game=self.instance.game).all()


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ('name', 'flavour', 'item', 'is_active', 'count')

    name = forms.CharField(widget=forms.TextInput(), label='')
    flavour = forms.CharField(widget=forms.Textarea(), label='')
    item = forms.ModelChoiceField(queryset=InfSet.objects.none(), label='', required=False)
    is_active = forms.BooleanField(required=False, label='')
    count = forms.IntegerField(label='')

    def __init__(self, *ar, **kw):
        char = kw.pop('character', None)
        super(ItemForm, self).__init__(*ar, **kw)
        self.fields['item'].queryset = InfSet.objects.filter(character=char).all()


class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ('name', 'item', 'turns')

    name = forms.CharField(widget=forms.TextInput(), label='')
    item = forms.ModelChoiceField(queryset=InfSet.objects.none(), label='')
    turns = forms.IntegerField(required=False)

    def __init__(self, *ar, **kw):
        char = kw.pop('character', None)
        super(StatusForm, self).__init__(*ar, **kw)
        self.fields['item'].queryset = InfSet.objects.filter(character=char).all()


class InfSetForm(forms.ModelForm):
    class Meta:
        model = InfSet
        fields = ('reference',)

    reference = forms.CharField(widget=forms.TextInput(), label='Название Сета')

    def is_valid(self, *ar, **kw):
        char = kw.pop('character')
        self.instance.character = char
        return super(InfSetForm, self).is_valid(*ar, **kw)


class ParmGroupForm(forms.ModelForm):
    class Meta:
        model = ParmGroup
        fields = ('name', 'flavour', 'cost_to_add', 'cost')

    name = forms.CharField(widget=forms.TextInput, label='Название группы')
    flavour = forms.CharField(widget=forms.Textarea, label='Описание группы')
    cost_to_add = forms.IntegerField(label='Стоимость добавления нового')
    cost = forms.IntegerField(label='Стоимость поднятия навыка')

    def is_valid(self, *ar, **kw):
        setting = kw.pop('setting')
        self.instance.setting = setting
        return super(ParmGroupForm, self).is_valid(*ar, **kw)


class GroupInlineForm(forms.ModelForm):
    class Meta:
        model = CharParm
        fields = ('name', 'flavour', 'value', 'override_cost', 'affected_by')

    name = forms.CharField(widget=forms.TextInput, label='Название')
    flavour = forms.CharField(widget=forms.Textarea, label='Описание')
    value = forms.IntegerField(label='Значение')
    override_cost = forms.IntegerField(label='Стоимость (-1 = стоимость группы)')
    affected_by = forms.ModelMultipleChoiceField(queryset=CharParm.objects.none(), required=False)

    def __init__(self, *ar, **kw):
        character = kw.pop('character')
        super(GroupInlineForm, self).__init__(*ar, **kw)
        self.fields['affected_by'].queryset = CharParm.objects.filter(character=character).all()


class SceneForm(forms.ModelForm):
    class Meta:
        model = Scene
        fields = ('name', 'flavour')

    name = forms.CharField(widget=forms.TextInput(), label='Название')
    flavour = forms.CharField(widget=forms.Textarea(), label='Описание')


class GMActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ('response',)

    response = forms.CharField(widget=forms.Textarea())

    def save(self, *ar, **kw):
        self.instance.finished = True
        super(GMActionForm, self).save(*ar, **kw)


class PlayerActionSubmitForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ('action', 'phrase', 'language')

    action = forms.CharField(widget=forms.Textarea, label='Действие', required=False)
    phrase = forms.CharField(widget=forms.Textarea, label='Речь', required=False)
    language = forms.ModelChoiceField(queryset=Languages.objects.none(), label='Язык', required=False)

    # char+scene = on_save
    # on init - language query
    def __init__(self, *ar, **kw):
        char = kw.pop('character')
        super(PlayerActionSubmitForm, self).__init__(*ar, **kw)
        self.fields['language'].queryset = char.languages

    def is_valid(self, **kw):
        error = False
        valid = super(PlayerActionSubmitForm, self).is_valid()
        if not valid:
            error = True

        if self.cleaned_data['phrase'] != '' and self.cleaned_data['language'] is None:
            self._errors['Ошибка'] = ': Выберите язык'
            error = True

        char = kw.pop('char')
        if char is None:
            self._errors['Чо?'] = 'По ходу у вас нет персонажа'
            error = True
        if char.scene is None:
            self._errors['Нет сцены'] = 'Ваш персонаж не находится в сцене. Подождите пока ГМ поместит вас в сцену'
            error = True
        if char.pause:
            self._errors[
                'Пауза'] = 'Вы не имеете права действовать. Дождитесь своего хода или пока ГМ снимет вас с паузы'
            error = True

        if error:
            return False
        else:
            return True


class GMCharActionSubmitForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ('scene', 'action', 'response', 'finished')

    scene = forms.ModelChoiceField(queryset=Scene.objects.none(), label='Сцена')
    action = forms.CharField(widget=forms.Textarea, label='Действие')
    response = forms.CharField(widget=forms.Textarea, label='Результат', required=False)
    finished = forms.BooleanField(required=False)

    def __init__(self, *ar, **kw):
        game = kw.pop('game')
        super(GMCharActionSubmitForm, self).__init__(*ar, **kw)
        self.fields['scene'].queryset = Scene.objects.filter(game=game).all()

    def is_valid(self, **kw):
        error = False
        valid = super(GMCharActionSubmitForm, self).is_valid()
        if not valid:
            error = True

        if error:
            return False
        else:
            return True
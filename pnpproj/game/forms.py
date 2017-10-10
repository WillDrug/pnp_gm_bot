import base64
import hashlib
import time

from django import forms
from game.models import Game, Setting, Character, Languages, ParmGroup, Scene


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
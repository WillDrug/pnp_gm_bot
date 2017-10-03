from django import forms
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from game.models import Game, Setting, Character
import hashlib, base64, time


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
        hasher = hashlib.sha1(user.__str__().encode('utf-8')+str(time.time()).encode('utf-8'))
        self.fields['invite'] = forms.CharField(
            initial=base64.urlsafe_b64encode(hasher.digest()[0:10]).decode('utf-8'),
            widget=forms.HiddenInput()
        )

class NewCharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ('name', 'display_name', 'flavour')
    name = forms.CharField(widget=forms.TextInput(), label='Имя Персонажа')
    display_name = forms.CharField(widget=forms.TextInput(),
                                   label='Обозначение персонажа пока имя неизвестно '
                                         '(например, "человек в красной шляпе")')
    flavour = forms.CharField(widget=forms.Textarea(), label='Описание Персонажа')

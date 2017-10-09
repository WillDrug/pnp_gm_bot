import base64
import hashlib
import time

from django import forms
from game.models import Game, Setting, Character, Languages, ParmGroup


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

class BaseCharacterFormPlayer(forms.ModelForm):
    class Meta:
        model = Character
        fields = ('name', 'display_name', 'flavour')

class GroupConfigForm(forms.ModelForm):
    class Meta:
        model = ParmGroup
        fields = ('name', 'flavour', 'cost_to_add')

    name = forms.CharField(widget=forms.TextInput(), label='Название группы')
    flavour = forms.CharField(widget=forms.Textarea(), label='Описание группы')
    class ParmGroup(models.Model):
        setting = models.ForeignKey(Setting, on_delete=models.CASCADE)
        name = models.CharField(max_length=25)
        flavour = models.CharField(max_length=2000, blank=True)
        cost_to_add = models.IntegerField(default=40)

from django import forms
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from game.models import Game, Setting

class NewSettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ('name', 'flavour')

    name = forms.CharField(widget=forms.TextInput(), label='Название Сеттинга')
    flavour = forms.CharField(widget=forms.Textarea(), label='Описание Сеттинга')

class NewGameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ('setting', 'name', 'flavour')

    setting = forms.ModelChoiceField(queryset=Setting.objects.all())
    name = forms.CharField(widget=forms.TextInput(), label='Название Игры')
    flavour = forms.CharField(widget=forms.Textarea(), label='Описание Игры')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(NewGameForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['setting'].queryset = Setting.objects.filter(owner=user).all()
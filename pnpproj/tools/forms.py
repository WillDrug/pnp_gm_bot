from django import forms
from django.contrib.auth.models import User
from django.forms.utils import ErrorList

class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'password',)
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин',
                                'required': 'true', 'autofocus': 'true'}), label='')
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль',
                                'required': 'true', 'autofocus': 'true'}), label='')

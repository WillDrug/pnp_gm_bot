from django.views.decorators.csrf import csrf_exempt
import base64
import hashlib
import time
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from game.views import game_main
from tools.views import login_view
from game.models import Character, CharParm, Influence, InfSet, Item, Status, ParmGroup, Players, Setting, Game, Languages
from game.forms import NewSettingForm, NewGameForm
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory, modelformset_factory
from django import forms
from annoying.decorators import ajax_request
from main.models import Chat
from game.views import get_game
from datetime import datetime, timedelta, timezone

def generate_menu(request):
    playing = Players.objects.filter(user=request.user).all()
    playing_full = dict()
    for i in playing:
        if i.game.setting.owner == request.user:
            continue
        if i.game.setting.name not in playing_full.keys():
            playing_full[i.game.setting.name] = list()
        playing_full[i.game.setting.name].append({'name': i.game.name,
                                                  'key': i.game.invite})
    owning = Setting.objects.filter(owner=request.user).all()
    owning_full = dict()
    for i in owning:
        if i.name not in owning_full.keys():
            owning_full[i.name] = {'games': list(),
                                   'pk': i.pk}
        games_in_setting = Game.objects.filter(setting=i).all()
        for q in games_in_setting:
            owning_full[i.name]['games'].append({'name': q.name,
                                        'key': q.invite})
    return dict(playing=playing_full, owning=owning_full)

# Create your views here.
def index(request):
    if isinstance(request.user, AnonymousUser):
        return login_view(request)
    else:
        return gameindex(request)


# Create your views here.

@login_required(redirect_field_name='index')
def gameindex(request, **kwargs):
    # gather user games
    assert isinstance(request.user, User)
    if 'menu' in request.GET.keys() or request.user.first_name == '':
        request.user.first_name = 'menu'
        request.user.save()
    if request.user.first_name == 'menu':
        return render(request, 'main/gamemenu.html', dict(menu=generate_menu(request)))
    else:
        return game_main(request)

@login_required(redirect_field_name='index')
def new_game(request):
    if request.method == 'POST':
        if request.POST['act'] == 'setting':
            form = NewSettingForm(request.POST)
            if form.is_valid():
                setting = form.save(commit=False)
                setting.owner = request.user
                setting.save()
                return redirect(reverse('new_game'))
        elif request.POST['act'] == 'game':
            form = NewGameForm(request.POST)
            if form.is_valid():
                form.save()
                request.user.first_name = form.fields['invite']
                request.user.save()
                return redirect(reverse('edit_setting')+'?setting='+str(form.cleaned_data.get('setting').pk))

    settings = Setting.objects.filter(owner=request.user).all()

    if settings.__len__() == 0 or 'setting' in request.GET.keys():
        form = NewSettingForm(None)
        title = 'Создайте Сеттинг'
        action = 'setting'
    else:
        form = NewGameForm(user=request.user)  # , user=request.user)
        title = 'Создайте Игру'
        action = 'game'


    return render(request, 'main/newgame.html', {'form': form, 'title': title, 'action': action, 'menu': generate_menu(request)})

@login_required(redirect_field_name='index')
def switch_game(request, **kwargs):
    try:
        gamehash = kwargs.pop('gamehash')
    except KeyError:
        return redirect(reverse('index'))
    game = Game.objects.filter(invite=gamehash).first()
    player = Players.objects.filter(game=game).filter(user=request.user).first()
    if player is None:
        player = Players(user=request.user, game=game)
        player.save()
    request.user.first_name = gamehash
    request.user.save()
    return redirect(reverse('game_index'))


def add_languages(request): #also edit groups

    LanguageFormSet = inlineformset_factory(Setting, Languages, fields=('name',), extra=1)
    ParmGroupFormSetBase = inlineformset_factory(Setting, ParmGroup, fields=('name', 'flavour', 'cost_to_add', 'cost'),
                                             extra=0)

    class ParmGroupFormSet(ParmGroupFormSetBase):
        def add_fields(self, form, index):
            super(ParmGroupFormSet, self).add_fields(form, index)
            form.fields["flavour"] = forms.CharField(widget=forms.Textarea(attrs={'class': 'pg_area', 'placeholder': 'Описание', }))
            form.fields["name"] = forms.CharField(widget=forms.TextInput(attrs={'class': 'pg_text', 'placeholder': 'Название', }))

    setting_to_edit = Setting.objects.filter(pk=request.GET['setting']).first()
    if setting_to_edit is None:
        return redirect(reverse('game_index'))
    if setting_to_edit.owner != request.user:
        return HttpResponse('fuck you')
    if request.method == 'POST' and request.POST.get('add_lang') == 'true':
        formset = LanguageFormSet(request.POST, request.FILES, instance=setting_to_edit, prefix='langs')
        grpformset = ParmGroupFormSet(request.POST, instance=setting_to_edit, prefix='groups')
        if formset.is_valid():
            formset.save()
            formset = LanguageFormSet(instance=setting_to_edit, prefix='langs') #reload
        if grpformset.is_valid():
            grpformset.save()
            grpformset = ParmGroupFormSet(instance=setting_to_edit, prefix='groups')
    else:
        formset = LanguageFormSet(instance=setting_to_edit, prefix='langs')
        grpformset = ParmGroupFormSet(instance=setting_to_edit, prefix='groups')
    return render(request, 'main/add_languages.html', {'formset': formset,
                                                       'groupformset': grpformset,
                                                       'menu': generate_menu(request)})

@ajax_request
def rehash(request, **kw):
    hash = kw.pop('gamehash')
    if request.user.first_name != hash:
        return HttpResponse('BOGUS BULL BULL WOW')

    game = Game.objects.filter(invite=hash).first()
    if game.setting.owner != request.user:
        return HttpResponse('WOW NO')

    hash_avail = False
    while not hash_avail:
        hasher = hashlib.sha1(request.user.__str__().encode('utf-8') + str(time.time()).encode('utf-8'))
        new_hash = base64.urlsafe_b64encode(hasher.digest()[0:10]).decode('utf-8')
        try_game = Game.objects.filter(invite=new_hash).first()
        if try_game is None:
            hash_avail = True
    game.invite = new_hash
    users = User.objects.filter(first_name=hash).all()
    for user in users:
        user.first_name = new_hash
        user.save()
    game.save()

    return dict(newhash=reverse('join_game', kwargs=dict(gamehash=new_hash)))

@ajax_request
@csrf_exempt
def chat(request):
    initial = request.GET.get('initial')
    if initial is not None:
        # get list of new ones
        game = get_game(request.user)
        messages = Chat.objects.filter(game=game).order_by('-added').all()[:10][::-1]
        return_list = list()
        for msg in messages:
            return_list.append(msg.as_dict)
        return return_list

    if request.method == 'POST':
        msg = request.POST.get('msg')
        game = get_game(request.user)
        new_msg = Chat(user=request.user, game=game, msg=msg[:255])
        new_msg.save()
        return dict(ok=True)
        # submit to chat

    update = request.GET.get('update')
    if update is not None:
        game = get_game(request.user)
        datetime_object = datetime.strptime(update, '%Y-%m-%dT%H:%M:%S.%fZ')
        datetime_object += timedelta(milliseconds=2)
        messages = Chat.objects.filter(game=game).filter(added__gt=datetime_object.astimezone(timezone.utc)).order_by('added').all()
        return_list = list()
        for msg in messages:
            return_list.append(msg.as_dict)
        return return_list


    return HttpResponse('nope')

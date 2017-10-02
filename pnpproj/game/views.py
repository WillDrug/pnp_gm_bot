from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from game.models import Game, Players, Setting
from game.forms import NewSettingForm, NewGameForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse

# Create your views here.

@login_required(redirect_field_name='index')
def gameindex(request, **kwargs):
    print(kwargs['gamehash'])
    # gather user games
    assert isinstance(request.user, User)
    if 'menu' in request.GET.keys() or request.user.first_name == '':
        request.user.first_name = 'menu'
        request.user.save()
    if request.user.first_name == 'menu':
        playing = Players.objects.filter(user=request.user).all()
        playing_full = dict()
        for i in playing:
            if i.game.setting.name not in playing_full.keys():
                playing_full[i.game.setting.name] = list()
            playing_full[i.game.setting.name].append({'name': i.game.name,
                                                    'key': i.game.invite})
        owning = Setting.objects.filter(owner=request.user).all()
        owning_full = dict()
        for i in owning:
            if i.name not in owning_full.keys():
                owning_full[i.name] = list()
            games_in_setting = Game.objects.filter(setting=i).all()
            for q in games_in_setting:
                owning_full[i.name].append({'name': q.name,
                                            'key': q.invite})
        return render(request, 'game/gameindex.html', {'menu': True, 'playing': playing_full, 'owning': owning_full})
    else:
        game = Game.objects.filter(invite=request.user.first_name).first()
        if game is None:
            request.user.first_name = 'menu'
            request.user.save()
            return redirect(reverse('game_index'))
        if game.game_master == request.user:
            role = 'gm'
        else:
            role = 'player'
        characters = Character.objects.filter(owner=request.user).filter(game=game).all()
        return render(request, 'game/gameindex.html', {'game': game, 'characters': characters})

@login_required(redirect_field_name='index')
def new_game(request):
    if request.method == 'POST':
        if request.POST['act'] == 'setting':
            form = NewSettingForm(request.POST)
            if form.is_valid():
                setting = form.save(commit=False)
                setting.owner = request.user
                setting.save()
        elif request.POST['act'] == 'game':
            form = NewGameForm(request.POST)
            if form.is_valid():
                form.save()
                request.user.first_name = form.fields['invite']
                request.user.save()
                return redirect(reverse('game_index'))
    settings = Setting.objects.filter(owner=request.user).all()
    if settings.__len__() == 0 or 'setting' in request.GET.keys():
        form = NewSettingForm(None)
        title = 'Создайте Сеттинг'
        action = 'setting'
    else:
        form = NewGameForm(None)#, user=request.user)
        title = 'Создайте Игру'
        action = 'game'

    return render(request, 'game/newgame.html', {'form': form, 'title': title, 'action': action})
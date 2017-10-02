from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from game.models import Game, Players, Setting
from game.forms import NewSettingForm, NewGameForm
from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required(redirect_field_name='index')
def gameindex(request):
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
                playing_full[i.game.setting.name] = dict()
            playing_full[i.game.setting.name]['name'] = i.game.name
            playing_full[i.game.setting.name]['key'] = i.game.pk
        owning = Setting.objects.filter(owner=request.user).all()
        owning_full = dict()
        for i in owning:
            print(i)
            if i.name not in owning_full.keys():
                owning_full[i.name] = dict()
            games_in_setting = Game.objects.filter(setting=i).all()
            for q in games_in_setting:
                owning_full[i.name]['name'] = q.name
                owning_full[i.name]['key'] = q.pk
        return render(request, 'game/gameindex.html', {'menu': True, 'playing': playing_full, 'owning': owning_full})
    else:
        game = Game.objects.filter(name=request.user.first_name).first()
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
            if form.is_valid():
                form.save()
                return redirect('index')
    settings = Setting.objects.filter(owner=request.user).all()
    if settings.__len__() == 0 or 'setting' in request.GET.keys():
        form = NewSettingForm(request)
        title = 'Создайте Сеттинг'
        action = 'setting'
    else:
        form = NewGameForm(request, user=request.user)
        title = 'Создайте Игру'
        action = 'game'

    return render(request, 'game/newgame.html', {'form': form, 'title': title, 'action': action})
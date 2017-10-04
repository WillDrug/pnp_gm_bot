from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from game.models import Game, Players, Setting, Character, Stats, Combat, Magic, Secondary, Tertiary, Inventory
from game.forms import NewSettingForm, NewGameForm, NewCharacterForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse

#functions
def generate_menu(request):
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
    return dict(playing=playing_full, owning=owning_full)


# Create your views here.

@login_required(redirect_field_name='index')
def gameindex(request, **kwargs):
    # gather user games
    assert isinstance(request.user, User)
    if 'menu' in request.GET.keys() or request.user.first_name == '':
        request.user.first_name = 'menu'
        request.user.save()
    if request.user.first_name == 'menu':
        return render(request, 'game/gamemenu.html', dict(menu=generate_menu(request)))
    else:
        return game(request)


@login_required(redirect_field_name='index')
def new_game(request):
    settings = Setting.objects.filter(owner=request.user).all()
    if settings.__len__() == 0 or 'setting' in request.GET.keys():
        form = NewSettingForm(None)
        title = 'Создайте Сеттинг'
        action = 'setting'
    else:
        form = NewGameForm(None)  # , user=request.user)
        title = 'Создайте Игру'
        action = 'game'

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

    return render(request, 'game/newgame.html', {'form': form, 'title': title, 'action': action, 'menu': generate_menu(request)})

@login_required(redirect_field_name='index')
def switch_game(request, **kwargs):
    try:
        gamehash = kwargs.pop('gamehash')
    except KeyError:
        return redirect(reverse('index'))
    request.user.first_name = gamehash
    request.user.save()
    return redirect(reverse('game_index'))

@login_required(redirect_field_name='index')
def new_character(request):
    # check active game
    game = Game.objects.filter(invite=request.user.first_name)
    if game is None:
        return redirect(reverse('game_index'))

    # check character list with levelup=True
    char = Character.objects.filter(owner=request.user).filter(game=game).filter(levelup=True).first()
    stats = Stats.objects.filter(char=char).first()
    combat = Combat.objects.filter(char=char).first()
    magic = Magic.objects.filter(char=char).first()
    secondary = Secondary.objects.filter(char=char).first()
    tertiary = Tertiary.objects.filter(char=char).first()
    feats = Feats.objects.filter(char=char).first()
    inventory = Inventory.objects.filter(char=char).first()

    if char is None:
        redirect(reverse('game_index')) #that's a possible infinite loop, LOOOOOL

    parms = {
        'Основное': char,  # core
        'Статы': {},     # parm
        'Бой': {},       # parm
        'Магия': {},     # parm
        'Вторичные': {}, # parm
        'Третичные': {}, # parm
        'Таланты': {},   # influence item
        'Инвентарь': {}, # influence item
    }
    if 'action' not in request.GET.keys():
        action = 'core'
        exp = ''
    else:
        action = request.GET['action']

    if action == 'core':
        char = Character.objects.filter(owner=request.user).filter(game=request.first_name).all()
        if request.method == 'POST':
            form = NewCharacterForm(request.POST)
            if form.is_valid:
                char = form.save()
                char.owner = request.user
                char.experience = 600
                action = 'stats'
        else:
            form = NewCharacterForm()

    return render(request, 'game/newchar.html', {'form': form, 'parms': parms, 'action': action, 'exp': exp})

@login_required(redirect_field_name='index')
def game(request):
    game = Game.objects.filter(invite=request.user.first_name).first()
    if game is None:
        request.user.first_name = 'menu'
        request.user.save()
        return redirect(reverse('game_index'))
    if game.setting.owner == request.user:
        role = 'gm'
    else:
        role = 'player'
        player = Players.objects.filter(game=game).filter(user=request.user).first()
        if player is None:
            player = Players(user=request.user, game=game)
            player.save()
    characters = Character.objects.filter(owner=request.user).filter(game=game).all()
    if characters.__len__() == 0 and role == 'player':
        newchar = Character(owner=request.user, game=Game.objects.filter(invite=request.user.first_name).first().first())
        newchar.save()
        return redirect(reverse('new_char'))
    else:
        return render(request, 'game/game.html',
                  dict(game=game, role=role, characters=characters))
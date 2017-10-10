from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from game.models import Character, CharParm, Influence, InfSet, Item, Status, ParmGroup, Players, Setting, Game, \
    Languages
from game.forms import NewSettingForm, NewGameForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.forms import inlineformset_factory, modelformset_factory


# functions


def new_character(user, game):
    newchar = Character(owner=request.user, game=Game.objects.filter(invite=request.user.first_name).first(),
                        experience=0)
    # add forced form?
    newchar.save()
    return newchar

@login_required(redirect_field_name='index')
def game_main(request):
    game = Game.objects.filter(invite=request.user.first_name).first()
    if game is None:
        request.user.first_name = 'menu'
        request.user.save()
        return redirect(reverse('game_index'))
    if game.setting.owner == request.user:
        return gm(request, game)
    else:
        return player(request, game)

def player(request, game, **kw):
    character = Character.objects.filter(owner=request.user).filter(game=game).first()
    if character.__len__() == 0:
        character = new_character(request.user, game)

    return render(request, 'game/game.html',
                  dict(game=game, left_menu=left_menu_dict, gm=False))

def gm(request, game, **kw):
    characters = Character.objects.filter(game=game).all()

    return render(request, 'game/game.html',
                  dict(game=game, left_menu=left_menu_dict, gm=True))

@login_required(redirect_field_name='index')
def base_char_edit(request, **kw):
    try:
        setting = kw.pop('setting')
        character = kw.pop('character')
    except KeyError:
        return redirect(reversed('game_index'))
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


@login_required(redirect_field_name='index')
def new_character(request):
    # check active game
    game = Game.objects.filter(invite=request.user.first_name)
    if game is None:
        return redirect(reverse('game_index'))
    if char is None:
        redirect(reverse('game_index'))  # that's a possible infinite loop, LOOOOOL
    char = Character.objects.filter(owner=request.user).filter(game=request.first_name).all()
    if request.method == 'POST':
        form = NewCharacterForm(request.POST)
        if form.is_valid:
            char = form.save()
            char.owner = request.user
            char.experience = 600
            # add shit to char.
            parm = CharParm()
            # return game window with levelup waiting to happen
            return redirect(reverse('game_index'))
    else:
        form = NewCharacterForm()

    return render(request, 'game/newchar.html', {'form': form, 'parms': parms,
                                                 'action': action,
                                                 'exp': exp})


@login_required(redirect_field_name='index')
def game_main(request):
    game = Game.objects.filter(invite=request.user.first_name).first()
    if game is None:
        request.user.first_name = 'menu'
        request.user.save()
        return redirect(reverse('game_index'))
    if game.setting.owner == request.user:
        role = 'gm'
        return gm(request, game)
    else:
        role = 'player'
        return player(request, game)


def player(request, game, **kw):
    character = Character.objects.filter(owner=request.user).filter(game=game).first()
    if character.__len__() == 0:
        newchar = Character(owner=request.user, game=Game.objects.filter(invite=request.user.first_name).first(),
                            experience=0)
        newchar.save()
    left_menu_dict = char_edit(request, character)
    return render(request, 'game/game.html',
                  dict(game=game, left_menu=left_menu_dict, gm=False))


def gm(request, game, **kw):
    characters = Character.objects.filter(game=game).all()
    left_menu_dict = char_list(request, characters=characters)
    return render(request, 'game/game.html',
                  dict(game=game, left_menu=left_menu_dict, gm=True))



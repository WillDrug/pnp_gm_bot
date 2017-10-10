from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from game.models import Character, CharParm, Influence, InfSet, Item, Status, ParmGroup, Players, Setting, Game, \
    Languages, Scene
from game.forms import BaseCharForm, GMCharForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.forms import inlineformset_factory, modelformset_factory


# functions


def new_character(user):
    game = Game.objects.filter(invite=user.first_name).first()
    owner = user
    newchar = Character(owner=owner, game=game,
                        experience=0)
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
    if character is None:
        character = new_character(request.user)

    return render(request, 'game/game.html',
                  dict(game=game, gm=False))

def gm(request, game, **kw):
    char_list_parms = char_list(request, initial=True)
    return render(request, 'game/game.html',
                  dict(game=game, gm=True, char_list_parms=char_list_parms))

@login_required(redirect_field_name='index')
def char_list(request, **kw):
    try:
        initial = kw.pop('initial')
    except KeyError:
        initial = False
    game = Game.objects.filter(invite=request.user.first_name).first()
    CharListFormSet = modelformset_factory(Character, form=GMCharForm, extra=0)
    if request.method == 'POST':
        charlist = CharListFormSet(request.POST, queryset=Character.objects.filter(game=game))
        if charlist.is_valid():
            charlist.save()
    else:
        charlist = CharListFormSet(queryset=Character.objects.filter(game=game))
    parms = dict()
    parms['parms'] = dict()
    parms['parms']['formset'] = charlist
    parms['parms']['action_url'] = reverse('char_list')
    if initial:
        return parms
    else:
        return render(request, 'game/char_list.html', parms)

@login_required(redirect_field_name='index')
def base_char_edit(request, **kw):
    char = Character.objects.filter(pk=kw.pop('character')).first()
    if request.user != char.owner and request.user != char.game.setting.owner:
        return HttpResponse('BULLSHIT')
    parms = dict(action_url=reverse('base_char_edit', kwargs=dict(character=char.pk)))
    if request.method == 'POST':
        parms['form'] = BaseCharForm(request.POST, instance=char)
        if parms['form'].is_valid():
            parms['form'].save()
    else:
        parms['form'] = BaseCharForm(instance=char)
    parms['title'] = 'Редактировать Персонажа'
    parms['deletable'] = False
    return render(request, 'tools/modal.html', parms)

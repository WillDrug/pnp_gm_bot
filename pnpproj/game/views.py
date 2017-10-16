from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from game.models import Character, CharParm, Influence, InfSet, Item, Status, ParmGroup, Players, Setting, Game, \
    Languages, Scene
from game.forms import BaseCharForm, GMCharForm, ItemForm, StatusForm, InfSetForm, ParmGroupForm, GroupInlineForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.forms import inlineformset_factory, modelformset_factory
from annoying.decorators import ajax_request


# functions

def authenticate_by_char(user, char):
    if char.owner == user or char.game.setting.owner == user:
        return True
    else:
        return False


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
    char_parms = char_edit(request, initial=True, character=character.pk)

    return render(request, 'game/game.html',
                  dict(game=game, gm=False, char_parms=char_parms))


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


def char_edit(request, **kw):
    try:
        initial = kw.pop('initial')
    except KeyError:
        initial = False
    char = Character.objects.filter(pk=kw.pop('character')).first()
    if not authenticate_by_char(request.user, char):
        return HttpResponse('BULLSHIT')
    parms = dict(parms=dict(action_url=reverse('char_edit', kwargs=dict(character=char.pk))))
    parms['parms']['character'] = char
    parms['parms']['groups'] = list()
    if char.game.setting.owner == request.user:
        parms['parms']['gm'] = True
    else:
        parms['parms']['gm'] = False
    # populate formsets for each group (with link to add if need be)
    groups = ParmGroup.objects.filter(setting=char.game.setting).all()
    ParmFormSet = inlineformset_factory(Character, CharParm, fields=('name', 'flavour', 'value'), extra=0)

    for group in groups:
        group_dict = dict(group=group)
        group_dict['group_edit_action'] = reverse('group_edit', kwargs=dict(character=char.pk, group=group.pk))
        if request.method == 'POST':
            formset_to_save = ParmFormSet(request.POST, request.FILES, instance=char, prefix=group.name)
            if formset_to_save.is_valid():
                instances = formset_to_save.save(commit=False)
                for i in instances:
                    i.group = group
                    i.save()
                for i in formset_to_save.deleted_objects:
                    i.delete()

        group_dict['charparm_formset'] = ParmFormSet(queryset=CharParm.objects.filter(group=group).all(),
                                                     instance=char, prefix=group.name)

        parms['parms']['groups'].append(group_dict)
    if parms['parms']['gm']:
        ItemFormSet = inlineformset_factory(Character, Item, form=ItemForm, extra=0)
        StatusFormSet = inlineformset_factory(Character, Status, form=StatusForm, extra=0)
        if request.method == 'POST':
            itemsformset = ItemFormSet(request.POST, instance=char, prefix='items', form_kwargs=dict(character=char))
            statusformset = StatusFormSet(request.POST, instance=char, prefix='status', form_kwargs=dict(character=char))
            if itemsformset.is_valid():
                itemsformset.save()
            if statusformset.is_valid():
                statusformset.save()
        parms['parms']['itemformset'] = ItemFormSet(instance=char, prefix='items', form_kwargs=dict(character=char))
        parms['parms']['statusformset'] = StatusFormSet(instance=char, prefix='status', form_kwargs=dict(character=char))
        parms['parms']['infsets'] = InfSet.objects.filter(character=char).all()
    else:
        parms['parms']['items'] = Item.objects.filter(character=char).all()
        parms['parms']['status'] = Status.objects.filter(character=char).all()
    # populate formsets for inventory and such


    # populate formsets
    if initial:
        return parms
    else:
        return render(request, 'game/char.html', parms)


@login_required(redirect_field_name='index')
def base_char_edit(request, **kw):
    char = Character.objects.filter(pk=kw.pop('character')).first()
    if not authenticate_by_char(request.user, char):
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

def inf_set_edit(request, **kw):
    character = kw.pop('character')
    character = Character.objects.filter(pk=character).first()
    if not authenticate_by_char(request.user, character):
        return HttpResponse('bullshit')
    set = kw.pop('set')
    if set == '-1':
        set = InfSet(reference='Новый', character=character)
        set.save()
    else:
        set = InfSet.objects.filter(pk=set).first()
    InfluenceFormSet = inlineformset_factory(InfSet, Influence, extra=0, fields=('affects', 'value'))
    errors = list()
    if request.method == 'POST':
        if request.POST.get('DELETE'):
            set.delete()
            return redirect(reverse('char_edit', kwargs=dict(character=character.pk)))
        setform = InfSetForm(request.POST, instance=set, prefix='infset')
        formset = InfluenceFormSet(request.POST, instance=set, prefix='influences')
        if setform.is_valid(character=character):
            setform.save()
        else:
            errors.append(setform.errors)
        if formset.is_valid():
            influences = formset.save(commit=False)
            for inf in influences:
                inf.character = character
                inf.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
        else:
            errors.append(formset.errors)
        if errors.__len__() == 0:
            return redirect(reverse('char_edit', kwargs=dict(character=character.pk)))
    setform = InfSetForm(instance=set, prefix='infset')
    formset = InfluenceFormSet(instance=set, prefix='influences')
    return render(request, 'game/infsets.html', dict(setform=setform,
                                                     formset=formset,
                                                     character=character,
                                                     errors=errors,
                                                     action=reverse('inf_set_edit',
                                                                    kwargs=dict(character=character.pk, set=set.pk))
                                                     ))


def group_edit(request, **kw):
    character = kw.pop('character')
    character = Character.objects.filter(pk=character).first()
    if not authenticate_by_char(request.user, character):
        return HttpResponse('BULLSHIT')
    grp = kw.pop('group')
    if grp == '-1':
        grp = ParmGroup(setting=character.game.setting, name='Группа1', flavour='Описание',
                        cost_to_add=0, cost=1)
        grp.save()
    else:
        grp = ParmGroup.objects.filter(pk=grp).first()

    GroupFormSet = inlineformset_factory(ParmGroup, CharParm, form=GroupInlineForm, extra=0)
    errors = list()
    if request.method == 'POST':
        grpform = ParmGroupForm(request.POST, instance=grp, prefix='grpform')
        formset = GroupFormSet(request.POST, instance=grp, queryset=CharParm.objects.filter(character=character), form_kwargs=dict(character=character), prefix='grpset')
        if grpform.is_valid(setting=character.game.setting):
            grpform.save()
        else:
            errors.append(grpform.errors)
        if formset.is_valid():
            parms = formset.save(commit=False)
            for parm in parms:
                parm.character = character
                parm.group = grp
                parm.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
        else:
            errors.append(formset.errors)
        if errors.__len__() == 0:
            return redirect(reverse('char_edit', kwargs=dict(character=character.pk)))
    grpform = ParmGroupForm(instance=grp, prefix='grpform')
    formset = GroupFormSet(instance=grp, queryset=CharParm.objects.filter(character=character), form_kwargs=dict(character=character), prefix='grpset')
    return render(request, 'game/parmgroups.html', dict(grpform=grpform,
                                                     formset=formset,
                                                     character=character,
                                                     errors=errors,
                                                     action=reverse('group_edit',
                                                                    kwargs=dict(character=character.pk, group=grp.pk))
                                                     ))

@ajax_request
def action_log(request, initial=False):

    return None
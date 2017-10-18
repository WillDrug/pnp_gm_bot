from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from game.models import Character, CharParm, Influence, InfSet, Item, Status, ParmGroup, Players, Setting, Game, \
    Languages, Scene, Action, Roll, RollVisibility
from game.forms import BaseCharForm, GMCharForm, ItemForm, StatusForm, InfSetForm, ParmGroupForm, GroupInlineForm, \
    SceneForm, GMActionForm, GMCharActionSubmitForm, PlayerActionSubmitForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.forms import inlineformset_factory, modelformset_factory
from annoying.decorators import ajax_request
from datetime import timezone, datetime, timedelta
from barnum import gen_data


# functions

def authenticate_by_char(user, char):
    if char.owner == user or char.game.setting.owner == user:
        return True
    else:
        return False


def new_character(user):
    game = get_game(user)
    owner = user
    name = gen_data.create_name()
    name = name[0] + ' ' + name[1]
    newchar = Character(owner=owner, name=name, display_name=name,
                        game=game, experience=0)
    newchar.save()
    return newchar


def get_game(user):
    return Game.objects.filter(invite=user.first_name).first()

def get_char(user):
    return Character.objects.filter(game=get_game(user)).filter(owner=user).first()

def get_player(user):
    return Players.objects.filter(user=user).filter(game=get_game(user)).first()

@login_required(redirect_field_name='index')
def game_main(request):
    game = Game.objects.filter(invite=request.user.first_name).first()
    if game is None:
        request.user.first_name = 'menu'
        request.user.save()
        return redirect(reverse('game_index'))
    if game.setting.owner == request.user:
        return gm_view(request, game)
    else:
        return player_view(request, game)


def player_view(request, game, **kw):
    character = Character.objects.filter(owner=request.user).filter(game=game).first()
    if character is None:
        character = new_character(request.user)
    char_parms = char_edit(request, initial=True, character=character.pk)
    scene_parms = scenes(request, initial=True, scene=-1 if character.scene is None else character.scene.pk)
    action_parms = action_log(request, gm=False)
    action_submit_parms = action_submit(request, char=character.pk, initial=True)
    return render(request, 'game/game.html',
                  dict(game=game, gm=False,
                       char_parms=char_parms,
                       scene_parms=scene_parms,
                       action_parms=action_parms,
                       action_submit=action_submit_parms))


def gm_view(request, game, **kw):
    char_list_parms = char_list(request, initial=True)
    scene_parms = scenes(request, initial=True, scene='-1')
    action_parms = action_log(request, gm=True)
    action_submit_parms = action_submit(request, char='-1', initial=True)
    return render(request, 'game/game.html',
                  dict(game=game, gm=True,
                       char_list_parms=char_list_parms,
                       scene_parms=scene_parms,
                       action_parms=action_parms,
                       action_submit=action_submit_parms))


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
            statusformset = StatusFormSet(request.POST, instance=char, prefix='status',
                                          form_kwargs=dict(character=char))
            if itemsformset.is_valid():
                itemsformset.save()
            if statusformset.is_valid():
                statusformset.save()
        parms['parms']['itemformset'] = ItemFormSet(instance=char, prefix='items', form_kwargs=dict(character=char))
        parms['parms']['statusformset'] = StatusFormSet(instance=char, prefix='status',
                                                        form_kwargs=dict(character=char))
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


@ajax_request
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
            return dict(reload=True, id="char_container", url=reverse('char_edit', kwargs=dict(character=char.pk)))
    else:
        parms['form'] = BaseCharForm(instance=char)
    parms['title'] = 'Редактировать Персонажа'
    parms['deletable'] = False
    return render(request, 'tools/modal.html', parms)


@ajax_request
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
    InfluenceFormSet = inlineformset_factory(InfSet, Influence, extra=0, fields=('affects', 'value', 'visible'))
    errors = list()
    if request.method == 'POST':
        if request.POST.get('DELETE') == 'true':
            set.delete()
            return dict(reload=True, id="char_container", url=reverse('char_edit', kwargs=dict(character=character.pk)))
        else:
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
                return dict(reload=True, id="char_container", url=reverse('char_edit', kwargs=dict(character=char.pk)))
    setform = InfSetForm(instance=set, prefix='infset')
    formset = InfluenceFormSet(instance=set, prefix='influences')
    return render(request, 'game/infsets.html', dict(deletable=True,
                                                     setform=setform,
                                                     formset=formset,
                                                     character=character,
                                                     errors=errors,
                                                     action=reverse('inf_set_edit',
                                                                    kwargs=dict(character=character.pk, set=set.pk))
                                                     ))


def group_edit(request, **kw):
    character = kw.pop('character')
    character = Character.objects.filter(pk=character).first()
    if not character.game.setting.owner == request.user:
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
        formset = GroupFormSet(request.POST, instance=grp, queryset=CharParm.objects.filter(character=character),
                               form_kwargs=dict(character=character), prefix='grpset')
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
    formset = GroupFormSet(instance=grp, queryset=CharParm.objects.filter(character=character),
                           form_kwargs=dict(character=character), prefix='grpset')
    return render(request, 'game/parmgroups.html', dict(grpform=grpform,
                                                        formset=formset,
                                                        character=character,
                                                        errors=errors,
                                                        action=reverse('group_edit',
                                                                       kwargs=dict(character=character.pk,
                                                                                   group=grp.pk))
                                                        ))



def scenes(request, **kw):
    try:
        initial = kw.pop('initial')
    except KeyError:
        initial = False
    scene = kw.pop('scene')
    if scene == '-1':
        scene = None
    else:
        scene = Scene.objects.filter(pk=scene).first()

    parms = dict(parms=dict())
    game = get_game(request.user)
    if game.setting.owner == request.user:
        parms['parms']['gm'] = True
        parms['parms']['scenes'] = Scene.objects.filter(game=game).all()
    else:
        parms['parms']['gm'] = False
    if scene is not None:
        if scene.game.invite != request.user.first_name:
            return HttpResponse('BULLSHIT!!!')
        else:
            parms['parms']['scene'] = scene
        characters = Character.objects.filter(game=game).filter(scene=scene).all()
        parms['parms']['chars'] = list()
        for char in characters:
            player = Players.objects.filter(game=game).filter(user=char.owner).first()
            parms['parms']['chars'].append(dict(
                char=char,
                online=True if datetime.now(timezone.utc) - player.last_seen > timedelta(minutes=5) else False
            ))

    if initial:
        return parms
    else:
        return render(request, 'game/scenes.html', parms)


@ajax_request
def scene_edit(request, **kw):
    game = get_game(request.user)
    if game.setting.owner != request.user:
        return HttpResponse('BULLSHITTT!')
    scene = kw.pop('scene')
    if scene == '-1':
        scene = Scene(game=game, name='Новая сцена', flavour='Описание')
        scene.save()
    else:
        scene = Scene.objects.filter(pk=int(scene)).first()
    if request.method == 'POST':
        if request.POST.get('DELETE') == 'true':
            scene.delete()
            return dict(reload=True, id="scenes", url=reverse('scenes', kwargs=dict(scene='-1')))
        form = SceneForm(request.POST, instance=scene)
        if form.is_valid():
            form.save()
            return dict(reload=True, id="scenes", url=reverse('scenes', kwargs=dict(scene=scene.pk)))
    parms = dict()
    parms['form'] = SceneForm(instance=scene)
    parms['title'] = 'Редактировать Персонажа'
    parms['deletable'] = True
    parms['action_url'] = reverse('scene_edit', kwargs=dict(scene=scene.pk))
    return render(request, 'tools/modal.html', parms)


def action_log(request, gm):
    parms = dict(parms=dict())
    if gm:
        actions = Action.objects.filter(game=get_game(request.user)).order_by('-added')[:10][::-1]
        char = None
    else:
        game = get_game(request.user)
        char = get_char(request.user)
        actions = Action.objects.filter(game=game).filter(scene=char.scene).order_by('-added')[:10][::-1]
        parms['parms']['char'] = char
    parms['parms']['gm'] = gm
    parms['parms']['actions'] = list()
    player = get_player(request.user)
    player.last_seen = datetime.utcnow()
    player.save()
    for action in actions:
        if action.private and action.char != char:
            continue
        temp = dict()
        temp['action'] = action
        temp['action_phrase'] = action.get_text(char)
        temp['char'] = action.char.__str__() if action.char is not None else 'Мир'
        temp['char_flavour'] = action.char.flavour if action.char is not None else 'Действие не совершается конкретным персонажем'
        temp['rolls'] = list()
        rolls = Roll.objects.filter(action=action).order_by('added').all()
        for roll in rolls:
            temp_roll = dict()
            temp_roll['char'] = roll.char.__str__()
            temp_roll['parm'] = roll.parm_name
            temp_roll['parms'] = roll.show_roll(player)
            temp['rolls'].append(temp_roll)
        if gm and not action.finished:
            parms['parms']['form'] = GMActionForm(instance=action)
        parms['parms']['actions'].append(temp)
    return parms

def action_submit(request, initial=False, **kw):
    char = kw.pop('char')
    parms = dict(parms=dict())
    game = get_game(request.user)
    if char == '-1':
        parms['parms']['action_url'] = reverse('action_submit', kwargs=dict(char='-1'))
        if request.method == 'POST':
            parms['parms']['form'] = GMCharActionSubmitForm(request.POST, game=game)
            if parms['parms']['form'].is_valid():
                private = request.POST.get('invisible')
                action = parms['parms']['form'].save(commit=False)
                action.scene_name = action.scene.name
                action.game = game
                if private is not None:
                    action.private = True
                action.save()
        else:
            parms['parms']['form'] = GMCharActionSubmitForm(game=game)
    else:
        char = Character.objects.filter(pk=char).first()
        if not authenticate_by_char(request.user, char):
            return HttpResponse('BUUUUUUULLSHIT')

        parms['parms']['action_url'] = reverse('action_submit', kwargs=dict(char=char.pk))
        if request.method == 'POST':
            parms['parms']['form'] = PlayerActionSubmitForm(request.POST, character=char)
            if char.scene is not None and not char.pause:
                if parms['parms']['form'].is_valid(char=char):
                    private = request.POST.get('invisible')
                    action = parms['parms']['form'].save(commit=False)
                    action.game = game
                    action.char = char
                    action.scene = char.scene
                    action.scene_name = char.scene.name
                    if private is not None:
                        action.private = True
                    action.save()
                    parms['parms']['form'] = PlayerActionSubmitForm(character=char)
        else:
            parms['parms']['form'] = PlayerActionSubmitForm(character=char)

    if initial:
        return parms
    else:
        return render(request, 'game/action_submit.html', parms)

@ajax_request
def get_actions(request):
    player = get_player(request.user)
    game = get_game(request.user)
    if game.owner == request.user:
        gm = True
    else:
        gm = False
    resp = dict()
    if gm:
        new_actions = Action.objects.filter(added__gt=player.last_seen).order_by('-added').all()[::-1]
        resp['new'] = [action.pk for action in new_actions]
        updated = Action.objects.filter(updated__gt=player.last_seen).all()
        resp['updated'] = [action.pk for action in updated]
    else:
        char = get_char(request.user)
        new_actions = Action.objects.filter(scene=char.scene).filter()

    player.last_seen = datetime.utcnow()
    player.save()
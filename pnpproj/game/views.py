from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from game.models import Character, CharParm, Influence, InfSet, Item, Status, ParmGroup, Players, Setting, Game, \
    Languages, Scene, Action, Roll, RollVisibility
from game.forms import BaseCharForm, GMCharForm, ItemForm, StatusForm, InfSetForm, ParmGroupForm, GroupInlineForm, \
    SceneForm, GMActionForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.forms import inlineformset_factory, modelformset_factory
from annoying.decorators import ajax_request
from datetime import timezone, datetime, timedelta
# functions

def authenticate_by_char(user, char):
    if char.owner == user or char.game.setting.owner == user:
        return True
    else:
        return False


def new_character(user):
    game = get_game(user)
    owner = user
    newchar = Character(owner=owner, game=game,
                        experience=0)
    newchar.save()
    return newchar

def get_game(user):
    return Game.objects.filter(invite=user.first_name).first()

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
    scene_parms = scenes(request, initial=True, scene=character.scene.pk)
    return render(request, 'game/game.html',
                  dict(game=game, gm=False, char_parms=char_parms, scene_parms=scene_parms))


def gm_view(request, game, **kw):
    char_list_parms = char_list(request, initial=True)
    scene_parms = scenes(request, initial=True, scene='-1')
    return render(request, 'game/game.html',
                  dict(game=game, gm=True, char_list_parms=char_list_parms, scene_parms=scene_parms))


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
def calc_online(seen):
    return True if (datetime.now(timezone.utc) - seen) < timedelta(minutes=5) else False

@ajax_request
def scenes_online(request, **kw):
    game = get_game(request.user)
    scene = Scene.objects.filter(pk=kw.pop('scene')).first()
    requested_player = Players.objects.filter(game=game).filter(user=request.user).first()
    if requested_player is not None:
        requested_player.last_seen = datetime.utcnow()
        requested_player.save()
    characters = Character.objects.filter(game=game).filter(scene=scene).all()
    ajax_object = dict(online=list())
    for char in characters:
        player = Players.objects.filter(game=game).filter(user=char.owner).first()
        ajax_tmp = dict(
            char=char.pk,
            name=char.name,
            active=calc_online(player.last_seen)
        )
        ajax_object['online'].append(ajax_tmp)
    return ajax_object

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
    requested_player = Players.objects.filter(game=game).filter(user=request.user).first()
    if requested_player is not None:
        requested_player.last_seen = datetime.utcnow()
        requested_player.save()
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
                online=calc_online(player.last_seen)
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


def action_log(request, initial=False, **kw):
    scene = Game.objects.filter(pk=kw.pop('scene')).first()
    if scene is None:
        return HttpResponse('BUUUUUUULLSHIIT')
    player = Players.objects.filter(game=scene.game).filter(user=request.user).first()
    if game.setting.owner = request.user:
        gm = True
    elif player is not None:
        gm = False
        player.last_seen = datetime.utcnow()
        player.save()
    else:
        return HttpResponse('BULLLLLLSHIT')
    parms = dict(parms=dict(
        actions=list(),
        include_container=True,
    ))
    last_id = request.GET.get('last_id')
    get_id = request.GET.get('get_id')
    if last_id is None and get_id is None: # first populate
        if gm:
            actions = Action.objects.filter(game=game).order_by('-added').all()[:10][::-1]
        else:
            actions = Action.objects.filter(game=game).filter(scene=scene).order_by('-added').all()[:10][::-1]
    elif last_id is not None: # repopulate render
        parms['parms']['include_container'] = False
        if gm:
            actions = Action.objects.filter(game=game).order_by('-added').filter(pk__gt=last_id).all()[::-1]
        else:
            actions = Action.objects.filter(game=game).filter(scene=scene).order_by('-added').filter(pk__gt=last_id).all()[::-1]
    else:
        parms['parms']['include_container'] = False
        actions = Action.objects.filter(pk=get_id).all()

    for action in actions:
        temp_dict = dict(action=action, rolls=list(), finished=True, form=None)
        rolls = Roll.objects.filter(action=action).order_by('added').all()
        for roll in rolls:
            if gm:
                visibility = dict(visible_dice=True,
                                visible_parm_bonus=True,
                                visible_free_bonus=True,
                                visible_difficulty=True,
                                visible_result=True,
                                visibility=True
                                  )
            else:
                visibility = RollVisibility.objects.filter(roll=roll).filter(player=player).first()
            temp_dict['rolls'].append(dict(
                roll=roll,
                visibility=visibility
            ))
        parms['parms']['actions'].append(temp_dict)  #parms.actions.0.action\0.rolls.0.roll\0.rolls.0.visibility
        if not action.finished:
            temp_dict['finished'] = False
            temp_dict['form'] = GMActionForm(instance=action)
    if initial:
        return parms
    else:
        return render(request, 'game/action_log.html', parms)

def action_finish(request):
    return True  # submit form reload container with resulting html (HTML to render (!))


def roll(request):  # works in modal, submits reload with link to self repopulating;
                    # when reloading outputs html with rolls (add button is created by action)
                    # initial - returns parms for action_log?
    return True
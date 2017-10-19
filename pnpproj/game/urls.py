from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'play/?', views.game_main, name='game'),
    url(r'char_list/?', views.char_list, name='char_list'),
    url(r'char_parm_edit/(?P<character>[0-9]*)/?', views.char_edit, name='char_edit'),
    url(r'group_edit/(?P<character>[0-9]*)/(?P<group>-?[0-9]*)/?', views.group_edit, name='group_edit'),
    url(r'char_edit/(?P<character>[0-9]*)/?$', views.base_char_edit, name='base_char_edit'),
    url(r'inf_set_edit/(?P<character>[0-9]*)/(?P<set>-?[0-9]*)/?$', views.inf_set_edit, name='inf_set_edit'),
    url(r'scenes/(?P<scene>-?[0-9]*)/?$', views.scenes, name='scenes'),
    url(r'scene_edit/(?P<scene>-?[0-9]*)/?$', views.scene_edit, name='scene_edit'),
    url(r'action_submit/(?P<char>-?[0-9]*)/?$', views.action_submit, name='action_submit'),
    url(r'get_actions/?$', views.get_actions, name='get_actions'),
    url(r'get_action/?$', views.get_action, name='get_action'),
    url(r'finish_action/(?P<action>[0-9]*)/?$', views.finish_action, name='finish_action'),
    url(r'add_roll/(?P<action>[0-9]*)/?$', views.add_roll, name='add_roll'),
]


"""
n/(?P<gamehash>.{16})/?$', views.switch_game, name='join_game'),
To add:
    0) initial char edit CHECK
    1) Base char edit CHECK
    2) Crazy formsets (all parms within groups) CHECK
    3) inventory management ? wut
    4) parm edit
    5) char formset
"""
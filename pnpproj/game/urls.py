from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'play/?', views.game_main, name='game'),
    url(r'char_list/?', views.char_list, name='char_list'),
    url(r'char_parm_edit/(?P<character>[0-9]*)/?', views.char_edit, name='char_edit'),
    url(r'group_edit/(?P<group>[0-9]*)/?', views.char_edit, name='group_edit'),
    url(r'char_edit/(?P<character>[0-9]*)/?$', views.base_char_edit, name='base_char_edit')
]


"""
n/(?P<gamehash>.{16})/?$', views.switch_game, name='join_game'),
To add:
    0) initial char edit
    1) Base char edit
    2) Crazy formsets (all parms within groups)
    3) inventory management
    4) parm edit
    5) char formset
"""
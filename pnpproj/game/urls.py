from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'play/?', views.game_main, name='game'),
    url(r'base_char_create/(?P<setting>)/(?P<character>)/?$', views.base_char_edit, name='base_char_edit')
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
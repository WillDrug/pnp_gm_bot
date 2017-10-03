from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'gameindex/?', views.gameindex, name='game_index'),
    url(r'newgame/?', views.new_game, name='new_game'),
    url(r'join/(?P<gamehash>.{16})/?$', views.switch_game, name='join_game')
    url(r'/new_char', views.new_character, name='new_char')
]

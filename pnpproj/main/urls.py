from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^/?$', views.index, name='index'),
    url(r'^games/?$', views.gameindex, name='game_index'),
    url(r'^edit_setting/?$', views.add_languages, name='edit_setting'),
    url(r'^join/(?P<gamehash>.{16})/?$', views.switch_game, name='join_game'),
    url(r'^new/?$', views.new_game, name='new_game'),
]

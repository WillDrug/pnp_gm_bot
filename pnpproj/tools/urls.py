from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^login/$', views.login),
    url(r'^logout/$', views.login),
]

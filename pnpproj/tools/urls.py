from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'login/?$', views.login_view, name='login'),
    url(r'logout/?$', views.logout_view, name='logout'),
]

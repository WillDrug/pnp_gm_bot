from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import AnonymousUser
from game.views import gameindex
from tools.views import login_view


# Create your views here.
def index(request):
    if isinstance(request.user, AnonymousUser):
        return login_view(request)
    else:
        return gameindex(request)

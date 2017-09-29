from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
# Create your views here.

def game(request):
    return HttpResponse(b'gametest')
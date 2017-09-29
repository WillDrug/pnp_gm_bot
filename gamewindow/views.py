from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def index(request, **kwargs):
    return HttpResponse("Hello, world. You're in index."+kwargs.__str__())

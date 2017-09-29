from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
# Create your views here.

def login(request):
    return HttpResponse(b'TESTSETT')
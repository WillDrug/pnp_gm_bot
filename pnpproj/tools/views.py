from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from tools.forms import UserForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
# Create your views here.

def login_view(request):
    if 'index' in request.GET:
        next_page = request.GET['index']
    else:
        next_page = reverse('game_index')
    if request.method == 'POST':
        form = UserForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        if form.is_valid(): #registering
            user = User.objects.create_user(username, '', password)
            user.save()
            user = User.objects.get(username=username)
            login(request, user)
            return redirect(request.POST['next_page'])
        else: #trying to log in
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(request.POST['next_page'])
            else:
                next_page=request.POST['next_page']
                return render(request, 'tools/login.html', {'loginform': form, 'error': 'Неправильный пароль или существующий логин', 'next_page': next_page})
    else:
        form = UserForm(auto_id=False)
        return render(request, 'tools/login.html', {'loginform': form, 'next_page': next_page})
def logout_view(request):
    logout(request)
    return redirect('index')
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, LoginForm
from django.contrib import messages

def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def account(request):
    return render(request, "account.html")

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Вы успешно зарегистрировались!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register-login-form.html', 
        {
            'form': form,
            "page_name": "Регистрация", 
            "button_text": "Зарегистрироваться",
            "altern_text": "Уже есть аккаунт?",
            "altern_url": "login",
            "altern_url_text": "Войти"
        })

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Вы вошли в систему!')
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')
    else:
        form = LoginForm()
    return render(request, 'register-login-form.html', 
        {
            'form': form,
            "page_name": "Вход", 
            "button_text": "Войти",
            "altern_text": "Нет аккаунта?",
            "altern_url": "register",
            "altern_url_text": "Зарегистрироваться"
        })

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы!')
    return redirect('login')
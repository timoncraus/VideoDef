from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, LoginForm, UserEditForm, ProfileEditForm
from django.contrib import messages

def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def account(request):
    user = request.user
    if not user.is_authenticated:
        return render(request, "account.html")
    profile = user.profile
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form:
            user = user_form.save()
            profile = profile_form.save()
            login(request, user)
            messages.success(request, 'Данные были изменены!')
            return redirect('account')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(instance=profile)
    return render(request, "register-login-edit-form.html", 
        {
            'forms': [profile_form, user_form], 
            "page_name": "Ваш профиль",
            "button_text": "Отправить изменения",
            "altern_url": "logout",
            "altern_url_text": "Выйти",
            "type": "edit"
        })

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
    return render(request, 'register-login-edit-form.html', 
        {
            'forms': [form],
            "page_name": "Регистрация", 
            "button_text": "Зарегистрироваться",
            "altern_text": "Уже есть аккаунт?",
            "altern_url": "login",
            "altern_url_text": "Войти",
            "type": "register"
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
    return render(request, 'register-login-edit-form.html', 
        {
            'forms': [form],
            "page_name": "Вход", 
            "button_text": "Войти",
            "altern_text": "Нет аккаунта?",
            "altern_url": "register",
            "altern_url_text": "Зарегистрироваться",
            "type": "login"
        })

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы!')
    return redirect('login')
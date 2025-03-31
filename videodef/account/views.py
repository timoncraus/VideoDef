from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, LoginForm, UserEditForm, ProfileEditForm
from django.contrib import messages

def home(request):
    return render(request, "account/home.html")

def about(request):
    return render(request, "account/about.html")

def account(request):
    user = request.user
    if not user.is_authenticated:
        return render(request, "account/account.html")
    profile = user.profile
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user, auth_user=user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=profile, auth_user=user)
        if user_form.is_valid() and profile_form:
            user = user_form.save()
            profile = profile_form.save()
            login(request, user)
            messages.success(request, 'Данные были изменены!')
            return redirect('account')
    else:
        user_form = UserEditForm(instance=user, auth_user=user)
        profile_form = ProfileEditForm(instance=profile, auth_user=user)
    return render(request, "account/edit-form.html", 
        {
            'forms': {'user_form': user_form, 'profile_form': profile_form},
            "unique_id":user.unique_id,
            "date_registr":user.date_registr
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
    return render(request, 'account/register-form.html', { 'forms': {'register_form': form} })

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
    return render(request, 'account/login-form.html', { 'forms': {'login_form': form} })

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы!')
    return redirect('login')
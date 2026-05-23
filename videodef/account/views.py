from django.db import DatabaseError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.backends import ModelBackend

from .forms import RegisterForm, LoginForm, UserEditForm, ProfileEditForm
from .models import User
from resume.models import Resume
from child.models import Child


def home(request):
    return render(request, "account/home.html")


def about(request):
    return render(request, "account/about.html")


def account(request):
    user = request.user
    if not user.is_authenticated:
        return render(request, "account/account.html")
    
    # Проверяем, есть ли профиль у пользователя
    if not hasattr(user, 'profile') or user.profile is None:
        # Если профиля нет, создаем его
        from .models import Profile, Role, Gender
        # Получаем роль по умолчанию (например, "Родитель" с id=1)
        default_role = Role.objects.first()
        default_gender = Gender.objects.first()
        
        profile = Profile.objects.create(
            first_name="",
            last_name="",
            date_birth="2000-01-01",
            role=default_role,
            gender=default_gender,
            max_search_distance=10
        )
        user.profile = profile
        user.save()
    
    profile = user.profile
    
    if request.method == "POST":
        user_form = UserEditForm(request.POST, instance=user, auth_user=user)
        profile_form = ProfileEditForm(
            request.POST, request.FILES, instance=profile, auth_user=user
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                user = user_form.save()
                profile = profile_form.save()
                
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(request, "Данные были изменены!")
                return redirect("account:account")
            except DatabaseError as e:
                messages.error(request, f"Ошибка при изменении профиля: {e}")
        else:
            error_messages = []
            if not user_form.is_valid():
                for field, errors in user_form.errors.items():
                    error_messages.append(f"{field}: {', '.join(errors)}")
            if not profile_form.is_valid():
                for field, errors in profile_form.errors.items():
                    error_messages.append(f"{field}: {', '.join(errors)}")
            
            if error_messages:
                messages.error(request, f"Пожалуйста, исправьте ошибки: {'; '.join(error_messages)}")
            else:
                messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        user_form = UserEditForm(instance=user, auth_user=user)
        profile_form = ProfileEditForm(instance=profile, auth_user=user)
    
    # Безопасное получение координат
    location_lat_str = ""
    location_lon_str = ""
    if profile and profile.location_lat:
        location_lat_str = f"{profile.location_lat:.9f}".replace(' ', '')
    if profile and profile.location_lon:
        location_lon_str = f"{profile.location_lon:.9f}".replace(' ', '')
    
    return render(
        request,
        "account/edit_form.html",
        {
            "forms": {"user_form": user_form, "profile_form": profile_form},
            "unique_id": user.unique_id,
            "date_registr": user.date_registr,
            "last_seen": user.last_seen,
            "default_lat": 55.751244,
            "default_lng": 37.618423,
            "location_lat_str": location_lat_str,
            "location_lon_str": location_lon_str,
        },
    )


def view_other_user(request, user_id):
    user_info = get_object_or_404(User, unique_id=user_id)
    resumes = Resume.objects.filter(status=Resume.ACTIVE, user=user_info)
    children = Child.objects.filter(user=user_info)
    return render(
        request,
        "account/user_view.html",
        {"user_info": user_info, "resumes": resumes, "children": children},
    )


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(request, "Вы успешно зарегистрировались!")
                return redirect("account:home")
            except DatabaseError as e:
                messages.error(request, f"Ошибка при сохранении профиля: {e}")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = RegisterForm()
    return render(
        request, "account/register_form.html", {"forms": {"register_form": form}}
    )


def login_view(request):
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, "Вы вошли в систему!")
            return redirect("account:home")
        else:
            messages.error(request, "Неверный логин или пароль")
    else:
        form = LoginForm()
    return render(request, "account/login_form.html", {"forms": {"login_form": form}})


def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы!")
    return redirect("account:login")
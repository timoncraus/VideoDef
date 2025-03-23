from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator
from django.contrib.auth import authenticate
from django.conf import settings
from .models import User, Profile
from django import forms
from .auth_backends import CustomAuthBackend

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=40, required=True, label="Имя")
    last_name = forms.CharField(max_length=40, required=True, label="Фамилия")
    patronymic = forms.CharField(max_length=40, required=False, label="Отчество")
    date_birth = forms.DateField(required=True, label="Дата рождения", widget=forms.DateInput(attrs={'type': 'date'}))
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, required=True, label="Роль", initial="S")
    gender = forms.ChoiceField(choices=Profile.GENDER_CHOICES, required=True, label="Пол", initial="M")
    photo = forms.ImageField(required=False, label="Фото")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].validators = [RegexValidator(r'^\+?1?\d{9,15}$')]

    def save(self, commit=True):
        user = super().save(commit=False)
        profile = Profile.objects.create(
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            patronymic=self.cleaned_data['patronymic'],
            date_birth=self.cleaned_data['date_birth'],
            photo=self.cleaned_data.get('photo', None)
        )
        user.profile = profile
        user.backend = settings.AUTHENTICATION_BACKENDS[0]
        if commit:
            profile.save()
            user.save()
        return user


class LoginForm(forms.Form):
    identifier = forms.CharField(label="Логин, E-mail, ID или Телефон", required=True)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput, required=True)

    def clean(self):
        identifier = self.cleaned_data.get("identifier")
        password = self.cleaned_data.get("password")

        if identifier and password:
            try:
                user = User.objects.authenticate_user(identifier, password)  # Используем метод из UserManager
            except Exception as e:
                raise forms.ValidationError(str(e))

            if not user:
                raise forms.ValidationError("Неверные данные")

            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            self.user = user

        return self.cleaned_data

    def get_user(self):
        return getattr(self, "user", None)


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number']


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['photo', 'first_name', 'last_name', 'patronymic', 'date_birth', 'role', 'gender']
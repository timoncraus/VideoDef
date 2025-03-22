from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Profile
from django.core.validators import RegexValidator

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=40, required=True, label="Имя")
    last_name = forms.CharField(max_length=40, required=True, label="Фамилия")
    patronymic = forms.CharField(max_length=40, required=False, label="Отчество")
    date_birth = forms.DateField(required=True, label="Дата рождения", widget=forms.DateInput(attrs={'type': 'date'}))
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, required=True, label="Роль")
    photo = forms.ImageField(required=False, label="Фото")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].validators = [RegexValidator(r'^\d{1,10}$')]

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
        profile.user = user
        if commit:
            profile.save()
            user.save()
        return user


class LoginForm(AuthenticationForm):
    fields = ['username', 'password']
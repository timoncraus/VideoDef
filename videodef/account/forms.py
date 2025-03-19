from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django.core.validators import RegexValidator

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['photo', 'username', 'first_name', 'last_name', 'patronymic', 'email', 'phone_number', 
        'date_birth', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = False
        self.fields['patronymic'].required = False
        self.fields['phone_number'].validators = [RegexValidator(r'^\d{1,10}$')]



class LoginForm(AuthenticationForm):
    fields = ['username', 'password']
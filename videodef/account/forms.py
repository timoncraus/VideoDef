from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from django.conf import settings
from django import forms

from .models import User, Profile, Role, Gender


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=40, required=True, label="Имя")
    last_name = forms.CharField(max_length=40, required=True, label="Фамилия")
    patronymic = forms.CharField(max_length=40, required=False, label="Отчество")
    date_birth = forms.DateField(
        required=True,
        label="Дата рождения",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=True,
        label="Роль",
        empty_label="Выберите роль",
    )
    gender = forms.ModelChoiceField(
        queryset=Gender.objects.all(),
        required=True,
        label="Пол",
        empty_label="Выберите пол",
    )
    photo = forms.ImageField(required=False, label="Фото")

    # Координаты
    location_lat = forms.FloatField(
        required=False, 
        widget=forms.HiddenInput()
    )
    location_lon = forms.FloatField(
        required=False, 
        widget=forms.HiddenInput()
    )
    max_search_distance = forms.IntegerField(
        initial=10,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'км'})
    )

    class Meta:
        model = User
        fields = ["username", "email", "phone_number", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        profile = Profile.objects.create(
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            patronymic=self.cleaned_data["patronymic"],
            date_birth=self.cleaned_data["date_birth"],
            role=self.cleaned_data["role"],
            gender=self.cleaned_data["gender"],
            photo=self.cleaned_data.get("photo", None),
            location_lat=self.cleaned_data.get("location_lat"),
            location_lon=self.cleaned_data.get("location_lon"),
            max_search_distance=self.cleaned_data.get("max_search_distance", 10),
        )
        user.profile = profile
        user.backend = settings.AUTHENTICATION_BACKENDS[0]
        if commit:
            profile.save()
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    """Форма редактирования профиля с геолокацией"""
    
    def __init__(self, *args, auth_user, **kwargs):
        super().__init__(*args, **kwargs)
        # Блокируем поле role
        if 'role' in self.fields:
            self.fields['role'].disabled = True
            self.fields['role'].help_text = "Роль нельзя изменить самостоятельно. Обратитесь к администратору."
        
        # Делаем поля геолокации необязательными
        self.fields['location_lat'].required = False
        self.fields['location_lon'].required = False
    
    class Meta:
        model = Profile
        fields = [
            "photo",
            "first_name",
            "last_name",
            "patronymic",
            "date_birth",
            "role",
            "gender",
            "location_lat",
            "location_lon",
            "max_search_distance",
        ]
        widgets = {
            'location_lat': forms.HiddenInput(),
            'location_lon': forms.HiddenInput(),
            'max_search_distance': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 50000}),
        }
    
    def clean_location_lat(self):
        """Очистка и валидация широты"""
        lat = self.cleaned_data.get('location_lat')
        if lat is None or lat == '':
            return None
        try:
            return float(lat)
        except (TypeError, ValueError):
            return None
    
    def clean_location_lon(self):
        """Очистка и валидация долготы"""
        lon = self.cleaned_data.get('location_lon')
        if lon is None or lon == '':
            return None
        try:
            return float(lon)
        except (TypeError, ValueError):
            return None


class LoginForm(forms.Form):
    identifier = forms.CharField(label="Логин, E-mail, ID или Телефон", required=True)
    password = forms.CharField(
        label="Пароль", widget=forms.PasswordInput, required=True
    )

    def clean(self):
        identifier = self.cleaned_data.get("identifier")
        password = self.cleaned_data.get("password")

        if identifier and password:
            try:
                user = User.objects.authenticate_user(
                    identifier, password
                )
            except Exception as e:
                raise forms.ValidationError(str(e))

            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            self.user = user

        return self.cleaned_data

    def get_user(self):
        return getattr(self, "user", None)


class UserEditForm(forms.ModelForm):
    def __init__(self, *args, auth_user, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ["username", "email", "phone_number"]
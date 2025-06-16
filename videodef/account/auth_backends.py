from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Аутентифицирует пользователя по ID, username, email или телефону"""
        return User.objects.authenticate_user(username, password)
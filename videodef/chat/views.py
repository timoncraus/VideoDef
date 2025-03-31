from django.shortcuts import render
from .models import SmallChat
from django.contrib.auth.models import User

def chats(request):
    # Получаем все чаты, в которых участвует пользователь
    user_chats = SmallChat.objects.filter(user1=request.user) | SmallChat.objects.filter(user2=request.user)
    return render(request, 'chat/chats.html', {'user_chats': user_chats})

from django.shortcuts import render, get_object_or_404
from .models import SmallChat
from django.contrib.auth.models import User

def chats(request):
    # Получаем все чаты, в которых участвует пользователь
    user_chats = SmallChat.objects.filter(user1=request.user) | SmallChat.objects.filter(user2=request.user)
    return render(request, 'chat/chats.html', {'user_chats': user_chats})

def chat_room(request, chat_id):
    chat = get_object_or_404(SmallChat, id=chat_id)
    return render(request, 'chat/chat_room.html', {'chat': chat})
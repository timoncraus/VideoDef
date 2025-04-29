from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.utils.timezone import now
from .models import SmallChat, Message
from account.models import User

def chats(request):
    user_chats = SmallChat.objects.filter(user1=request.user) | SmallChat.objects.filter(user2=request.user)
    chats_info = []
    for chat in user_chats:
        last_message = Message.objects.filter(chat=chat).order_by('-timestamp').first()
        if last_message:
            if last_message.sender_id == request.user.unique_id:
                sender_name = "Вы"
            else:
                sender_name = User.objects.get(unique_id=last_message.sender_id).profile.first_name
            last_message_content = sender_name + ": " + last_message.content
        else:
            last_message_content = ""
        chats_info.append((chat, last_message_content))
    return render(request, 'chat/chats.html', {'chats_info': chats_info})

def chat_room(request, chat_id):
    chat = SmallChat.objects.get(id=chat_id)
    return render(request, 'chat/chat_room.html', {'chat': chat, 'curr_date': now()})

def get_chat(request, user1_id, user2_id):
    if user1_id == user2_id:
        return redirect('chats')  # запретить создавать чат с самим собой, если нужно

    user1 = get_object_or_404(User, unique_id=user1_id)
    user2 = get_object_or_404(User, unique_id=user2_id)

    chat = SmallChat.objects.filter(
        (Q(user1=user1) & Q(user2=user2)) | (Q(user1=user2) & Q(user2=user1))
    ).first()

    if not chat:
        chat = SmallChat.objects.create(user1=user1, user2=user2)

    return redirect('chat_room', chat_id=chat.id)
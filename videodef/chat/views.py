from django.shortcuts import render, get_object_or_404
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
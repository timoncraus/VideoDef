from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path('', views.chats, name='chats'),
    path('<int:chat_id>/', views.chat_room, name='chat_room'),
    path('get/<str:user1_id>/<str:user2_id>/', views.get_chat, name='get_chat'),
]

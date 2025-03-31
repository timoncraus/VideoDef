import json
from channels.generic.websocket import AsyncWebsocketConsumer
from account.models import User
from .models import SmallChat, Message
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        # Проверяем, авторизован ли пользователь
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()  # Закрываем соединение, если пользователь не авторизован
        else:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Используем текущего пользователя из self.scope["user"]
        sender = self.user

        # Сохраняем сообщение
        await self.save_message(sender, message)

        # Отправляем сообщение всем в чате
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': sender.unique_id,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user_id': event['user_id'],
        }))

    @database_sync_to_async
    def save_message(self, sender, message):
        """ Сохраняем сообщение в базу данных """
        chat = SmallChat.objects.get(id=self.chat_id)
        Message.objects.create(chat=chat, sender=sender, content=message)

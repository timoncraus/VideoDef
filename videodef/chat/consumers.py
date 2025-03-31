import json
from channels.generic.websocket import AsyncWebsocketConsumer
from account.models import User
from .models import SmallChat, Message
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Получаем chat_id из URL
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        
        # Название комнаты
        self.room_group_name = f'chat_{self.chat_id}'

        # Присоединяемся к группе WebSocket
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Отключение от группы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Обрабатываем сообщение от клиента
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user_id = text_data_json['user_id']
        sender = await self.get_user(user_id)

        # Сохраняем сообщение в базу данных
        await self.save_message(sender, message)

        # Отправляем сообщение в группу WebSocket
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': user_id
            }
        )


    async def chat_message(self, event):
        # Получаем сообщение из события
        message = event['message']
        user_id = event['user_id']

        # Отправляем сообщение клиенту
        await self.send(text_data=json.dumps({
            'message': message,
            'user_id': user_id
        }))

    #async def chat_message(self, event):
    #    # Получаем сообщение из события
    #    message = event['message']
    #    sender_id = event['sender']
#
    #    # Получаем профиль отправителя асинхронно
    #    sender = await self.get_user(sender_id)
    #    sender_profile = await self.get_user_profile(sender)
    #    print(sender_profile)
#
    #    # Отправляем сообщение клиенту
    #    await self.send(text_data=json.dumps({
    #        'message': message,
    #        'sender_info': str(sender_profile)
    #    }))

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(unique_id=user_id)

    #@database_sync_to_async
    #def get_user_profile(self, user):
    #    return user.profile  # Возвращаем профиль пользователя
        

    @database_sync_to_async
    def save_message(self, sender, message):
        """ Сохраняем сообщение в базу данных """
        chat = SmallChat.objects.get(id=self.chat_id)  # Получаем чат
        Message.objects.create(chat=chat, sender=sender, content=message)  # Создаём сообщение

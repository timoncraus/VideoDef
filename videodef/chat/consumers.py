import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import SmallChat, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        await self.update_last_seen()
        sender = self.user

        mes_obj = await self.save_message(sender, message)

        await self.channel_layer.group_send(

            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender.unique_id,
                'timestamp': mes_obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")

            }
        )

    async def chat_message(self, event):
        message_type = "sent" if self.user.unique_id == event['sender_id'] else "received"
        await self.send(text_data=json.dumps({
            'message_type': message_type,
            'message': event['message'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, sender, message):
        chat = SmallChat.objects.get(id=self.chat_id)
        return Message.objects.create(chat=chat, sender=sender, content=message)

    @database_sync_to_async
    def update_last_seen(self):
        self.user.update_last_seen()

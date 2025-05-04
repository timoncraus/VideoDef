from channels.generic.websocket import AsyncWebsocketConsumer
import json

# Хранилище для инициаторов по комнатам (на уровне процесса)
initiators = {}
connected_clients = {}  # ключ — room_name, значение — список channel_name


class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"videocall_{self.room_name}"
        print(f"📥 CONNECT {self.channel_name} to {self.room_group_name}")

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Определяем инициатора по room_name
        is_initiator = self.room_name not in initiators
        if is_initiator:
            initiators[self.room_name] = self.channel_name

        self.is_initiator = is_initiator
        await self.send(text_data=json.dumps({'type': 'role', 'initiator': self.is_initiator}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if initiators.get(self.room_name) == self.channel_name:
            del initiators[self.room_name]

    async def receive(self, text_data):
        print("🔁 WS RECEIVE:", text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast',
                'message': text_data,
                'sender': self.channel_name
            }
        )

    async def broadcast(self, event):
        # Не пересылаем сообщения отправителю
        if event['sender'] != self.channel_name:
            print(f"📤 BROADCASTING to {self.channel_name}: {event['message']}")
            await self.send(text_data=event['message'])


class NotifyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['user'].unique_id
        self.room_group_name = f"notify_{self.user_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def incoming_call(self, event):
        await self.send(text_data=json.dumps(event))

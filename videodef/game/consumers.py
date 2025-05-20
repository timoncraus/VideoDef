import json
from channels.generic.websocket import AsyncWebsocketConsumer


class PuzzleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "puzzle_room"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_piece',
                'message': text_data
            }
        )

    async def send_piece(self, event):
        await self.send(text_data=event['message'])


class WhiteboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Имя группы, к которой подключаются все пользователи доски
        self.room_group_name = 'whiteboard' 

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # При отключении — удаляем из группы
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # При получении сообщения от клиента пересылаем его всем в группе
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',  # Метод, который будет вызван
                'message': text_data,      # Передаём сообщение дальше
            }
        )

    async def broadcast_message(self, event):
        # Отправляем полученные данные обратно всем участникам
        await self.send(text_data=event['message'])
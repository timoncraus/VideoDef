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

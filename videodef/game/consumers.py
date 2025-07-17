import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PuzzleOnBoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_room_name = self.scope['url_route']['kwargs']['board_room_name']
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        
        # Уникальное имя группы для каждого экземпляра пазла на конкретной доске
        self.puzzle_instance_group_name = f'puzzle_on_board_{self.board_room_name}_{self.game_id}'

        await self.channel_layer.group_add(
            self.puzzle_instance_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"PuzzleOnBoardConsumer: User {self.channel_name} connected to puzzle {self.game_id} on board {self.board_room_name}")

    async def disconnect(self, close_code):
        if hasattr(self, 'puzzle_instance_group_name'):
            await self.channel_layer.group_discard(
                self.puzzle_instance_group_name,
                self.channel_name
            )
            print(f"PuzzleOnBoardConsumer: User {self.channel_name} disconnected from puzzle {self.game_id} on board {self.board_room_name}")

    async def receive(self, text_data):
        if hasattr(self, 'puzzle_instance_group_name'):
            await self.channel_layer.group_send(
                self.puzzle_instance_group_name,
                {
                    'type': 'puzzle_event',
                    'message': text_data,
                    'sender_channel_name': self.channel_name
                }
            )

    async def puzzle_event(self, event):
        message = event['message']
        await self.send(text_data=message)

class MemoryGameOnBoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_room_name = self.scope['url_route']['kwargs']['board_room_name']
        self.game_id = self.scope['url_route']['kwargs']['game_id']

        # Уникальное имя группы для каждого экземпляра игры "Поиск пар" на доске
        self.memory_game_instance_group_name = f'memory_game_on_board_{self.board_room_name}_{self.game_id}'

        await self.channel_layer.group_add(
            self.memory_game_instance_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"MemoryGameOnBoardConsumer: User {self.channel_name} connected to memory game {self.game_id} on board {self.board_room_name}")

    async def disconnect(self, close_code):
        if hasattr(self, 'memory_game_instance_group_name'):
            await self.channel_layer.group_discard(
                self.memory_game_instance_group_name,
                self.channel_name
            )
            print(f"MemoryGameOnBoardConsumer: User {self.channel_name} disconnected from memory game {self.game_id} on board {self.board_room_name}")

    async def receive(self, text_data):
        if hasattr(self, 'memory_game_instance_group_name'):
            await self.channel_layer.group_send(
                self.memory_game_instance_group_name,
                {
                    'type': 'memory_game_event',
                    'message': text_data,
                    'sender_channel_name': self.channel_name
                }
            )

    async def memory_game_event(self, event):
        message = event['message']
        await self.send(text_data=message)


class WhiteboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # Имя группы, к которой подключаются все пользователи доски
        self.room_group_name = f'whiteboard_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"WhiteboardConsumer: Пользователь {self.channel_name} подключен к комнате {self.room_group_name}")

    async def disconnect(self, close_code):
        # Отсоединяемся от группы комнаты
        if hasattr(self, 'room_group_name'): # Проверка на случай, если connect не завершился успешно
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"WhiteboardConsumer: Пользователь {self.channel_name} отключен от комнаты {self.room_group_name}")

    async def receive(self, text_data):
        # При получении сообщения от одного WebSocket, отправляем его всем остальным в той же группе (комнате)
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'message': text_data,
                    'sender_channel_name': self.channel_name
                }
            )

    async def broadcast_message(self, event):
        message = event['message']
        await self.send(text_data=message)
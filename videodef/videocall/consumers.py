from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.utils import timezone
import json

from videocall.models import VideoCall

# Хранилище для инициаторов по комнатам (на уровне процесса)
initiators = {}
connected_clients = {}  # ключ — room_name, значение — список channel_name


class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"videocall_{self.room_name}"
        self.user = self.scope["user"]

        if isinstance(self.user, AnonymousUser):
            await self.close()
            return

        try:
            self.videocall = await sync_to_async(VideoCall.objects.get)(room_name=self.room_name)
            if self.videocall.ended_at is not None:
                return
        except VideoCall.DoesNotExist:
            await self.close()
            return

        if not await is_participant(self.user, self.videocall):
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.room_name not in connected_clients:
            connected_clients[self.room_name] = []
        connected_clients[self.room_name].append(self.channel_name)

        is_initiator = (self.room_name not in initiators) and (self.user.unique_id == self.videocall.caller_id)
        if is_initiator:
            initiators[self.room_name] = self.channel_name

        self.is_initiator = is_initiator
        await self.send(text_data=json.dumps({'type': 'role', 'initiator': self.is_initiator}))

        if len(connected_clients[self.room_name]) == 2 and is_initiator:
            await self.send(text_data=json.dumps({'type': 'ready'}))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'channel': self.channel_name
            }
        )

    async def user_joined(self, event):
        if self.is_initiator and event['channel'] != self.channel_name:
            await self.send(text_data=json.dumps({'type': 'resend_offer'}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        
        if self.room_name in connected_clients:
            connected_clients[self.room_name].remove(self.channel_name)
            if not connected_clients[self.room_name]:
                try:
                    videocall = await sync_to_async(VideoCall.objects.get)(room_name=self.room_name)
                    videocall.ended_at = timezone.now()
                    await sync_to_async(videocall.save)()
                except VideoCall.DoesNotExist:
                    pass
                del connected_clients[self.room_name]

        if initiators.get(self.room_name) == self.channel_name:
            del initiators[self.room_name]


    async def receive(self, text_data):
        if not await is_participant(self.user, self.videocall):
            await self.close()
            return
        dict_data = json.loads(text_data)
        if dict_data["type"] == "end_call":
            try:
                videocall = await sync_to_async(VideoCall.objects.get)(room_name=self.room_name)
                videocall.ended_at = timezone.now()
                await sync_to_async(videocall.save)()
            except VideoCall.DoesNotExist:
                pass

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast',
                'message': text_data,
                'sender': self.channel_name
            }
        )

    async def broadcast(self, event):
        if event['sender'] != self.channel_name:
            await self.send(text_data=event['message'])

    


class NotifyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.user = user
        self.room_group_name = f"notify_{self.user.unique_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def incoming_call(self, event):
        await self.send(text_data=json.dumps(event))

    async def receive(self, text_data):
        data = json.loads(text_data)
        room_name = data.get("room_name")
        answer = data.get("answer")

        if (not room_name) or (answer not in ["rejection", "acceptance"]):
            await self.close()
            return

        try:
            videocall = await sync_to_async(VideoCall.objects.get)(room_name=room_name)
        except VideoCall.DoesNotExist:
            await self.close()
            return

        if not await is_participant(self.user, videocall):
            await self.close()
            return

        if answer == "rejection":
            videocall.ended_at = timezone.now()
            videocall.accepted = False
        elif answer == "acceptance":
            videocall.accepted = True

        await sync_to_async(videocall.save)()

        if answer == "rejection":
            await self.channel_layer.group_send(
                f"videocall_{room_name}",
                {
                    'type': 'broadcast',
                    'message': json.dumps({"type": "end_call"}),
                    'sender': '#'
                }
            )


async def is_participant(user, videocall):
    return user.unique_id in [videocall.caller_id, videocall.receiver_id]
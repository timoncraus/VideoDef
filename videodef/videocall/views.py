from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
import uuid
import json

from .models import VideoCall
from account.models import User


def videocall(request, room_name):
    return render(request, "videocall/videocall.html", {"room_name": room_name})


@login_required
def start_call(request):
    if request.method == "POST":
        data = json.loads(request.body)
        receiver_id = data.get("receiver_id")
        receiver = get_object_or_404(User, unique_id=receiver_id)
        room_name = str(uuid.uuid4())

        VideoCall.objects.create(
            caller=request.user, receiver=receiver, room_name=room_name
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notify_{receiver.unique_id}",
            {
                "type": "incoming_call",
                "from": str(request.user.profile),
                "room_name": room_name,
            },
        )

        return JsonResponse({"success": True, "room_name": room_name})

    return JsonResponse({"success": False}, status=400)

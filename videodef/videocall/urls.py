from django.urls import path
from . import views

app_name = "videocall"

urlpatterns = [
    path("call/<str:room_name>/", views.videocall, name="videocall"),
    path("start-call/", views.start_call, name="start_call"),
]

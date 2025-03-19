"""
URL configuration for videodef project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from account.views import *
from chat.views import *
from videocall.views import *
from game.views import *

account_patterns = [
    path('', home),
    path('account', account),
    path('about', about),
]

chat_patterns = [
    path('', chats),
]

videocall_patterns = [
    path('', videocall),
]

game_patterns = [
    path('', games),
]

urlpatterns = [
    path('admin', admin.site.urls),
    path('', include(account_patterns)),
    path('chats', include(chat_patterns)),
    path('videocall', include(videocall_patterns)),
    path('games', include(game_patterns))
]
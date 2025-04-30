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
from django.conf import settings
from django.conf.urls.static import static


from account import views as account_views
from chat import views as chat_views
from videocall import views as videocall_views
from game import views as game_views
from resume import views as resume_views

account_patterns = [
    path('', account_views.home, name="home"),
    path('account/', account_views.account, name="account"),
    path('about/', account_views.about, name="about"),
    path("register/", account_views.register_view, name="register"),
    path("login/", account_views.login_view, name="login"),
    path("logout/", account_views.logout_view, name="logout"),
    path('view/<str:user_id>/', account_views.view_other_user, name='view_other_user'),
]

chat_patterns = [
    path('', chat_views.chats, name='chats'),
    path('<int:chat_id>/', chat_views.chat_room, name='chat_room'),
    path('get/<str:user1_id>/<str:user2_id>/', chat_views.get_chat, name='get_chat'),
]


videocall_patterns = [
    path('', videocall_views.videocall, name="videocall"),
]

game_patterns = [
    path('', game_views.games, name="games"),
    path('puzzles/', game_views.puzzle_game, name="puzzle_game"),
    path('whiteboard/', game_views.whiteboard, name="whiteboard"),
]

resume_urlpatterns = [
    # для преподавателей:
    path('my/', resume_views.ResumeListView.as_view(), name='my_resumes'),
    path('create/', resume_views.ResumeCreateView.as_view(), name='create_my_resume'),
    path('edit/<int:pk>/', resume_views.ResumeUpdateView.as_view(), name='edit_my_resume_form'),
    path('delete/<int:pk>/', resume_views.ResumeDeleteView.as_view(), name='resume_confirm_delete'),
   

    # для родителей:
    path('search/', resume_views.PublicResumeListView.as_view(), name='public_resume_list'),
    path('view/<int:pk>/', resume_views.ResumeDetailView.as_view(), name='public_resume_detail'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(account_patterns)),
    path('chats/', include(chat_patterns)),
    path('videocall/', include(videocall_patterns)),
    path('games/', include(game_patterns)),
    path('resumes/', include(resume_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
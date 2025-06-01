from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("account.urls", namespace="account")),
    path("chats/", include("chat.urls", namespace="chat")),
    path("videocall/", include("videocall.urls", namespace="videocall")),
    path("games/", include("game.urls", namespace="game")),
    path("resumes/", include("resume.urls", namespace="resume")),
    path("documents/", include("document.urls", namespace="document")),
    path("children/", include("child.urls", namespace="child")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

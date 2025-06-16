from django.urls import path
from . import views

app_name = "account"

urlpatterns = [
    path("", views.home, name="home"),
    path("account/", views.account, name="account"),
    path("about/", views.about, name="about"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("view/<str:user_id>/", views.view_other_user, name="view_other_user"),
]

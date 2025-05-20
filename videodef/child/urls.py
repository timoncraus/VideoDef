from django.urls import path
from . import views

app_name = "child"

urlpatterns = [
    path('my/', views.ChildListView.as_view(), name='my_children'),
    path('create/', views.ChildCreateView.as_view(), name='create_my_child'),
    path('edit/<int:pk>/', views.ChildUpdateView.as_view(), name='edit_my_child'),
    path('delete/<int:pk>/', views.ChildDeleteView.as_view(), name='child_confirm_delete'),
    path('view/<int:pk>/', views.ChildDetailView.as_view(), name='public_child_detail'),
]

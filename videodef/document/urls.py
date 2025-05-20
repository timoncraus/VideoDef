from django.urls import path
from . import views

app_name = "document"

urlpatterns = [
    path('my/', views.DocumentListView.as_view(), name='my_documents'),
    path('create/', views.DocumentCreateView.as_view(), name='create_my_document'),
    path('edit/<int:pk>/', views.DocumentUpdateView.as_view(), name='edit_my_document'),
    path('delete/<int:pk>/', views.DocumentDeleteView.as_view(), name='document_confirm_delete'),
    path('view/<int:pk>/', views.DocumentDetailView.as_view(), name='public_document_detail'),
]

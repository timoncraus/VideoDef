from django.urls import path
from . import views

app_name = "resume"

urlpatterns = [
    path('my/', views.ResumeListView.as_view(), name='my_resumes'),
    path('create/', views.ResumeCreateView.as_view(), name='create_my_resume'),
    path('edit/<int:pk>/', views.ResumeUpdateView.as_view(), name='edit_my_resume'),
    path('delete/<int:pk>/', views.ResumeDeleteView.as_view(), name='resume_confirm_delete'),
    path('search/', views.PublicResumeListView.as_view(), name='public_resume_list'),
    path('view/<int:pk>/', views.ResumeDetailView.as_view(), name='public_resume_detail'),
]

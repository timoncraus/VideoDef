from django.urls import path
from . import views

app_name = "resume"

urlpatterns = [
    # API для админ-панели
    path('api/calculate-criteria-weights/', views.api_calculate_criteria_weights, name='api_calculate_criteria_weights'),
    path('api/calculate-alternatives-weights/', views.api_calculate_alternatives_weights, name='api_calculate_alternatives_weights'),
    path('api/check-consistency/', views.api_check_consistency, name='api_check_consistency'),
    path('api/child-violations/', views.get_child_violations, name='get_child_violations'),
    path('api/create-document/', views.ajax_create_document, name='ajax_create_document'),
    
    # Fuzzy анализ
    path('fuzzy/what-if/', views.what_if_analysis, name='what_if_analysis'),
    path('fuzzy/settings/', views.admin_fuzzy_settings, name='admin_fuzzy_settings'),
    path('fuzzy/demo/', views.fuzzy_demo, name='fuzzy_demo'),
    
    # Основные URL для резюме
    path("my/", views.ResumeListView.as_view(), name="my_resumes"),
    path("create/", views.ResumeCreateView.as_view(), name="create_my_resume"),
    path("edit/<int:pk>/", views.ResumeUpdateView.as_view(), name="edit_my_resume"),
    path("delete/<int:pk>/", views.ResumeDeleteView.as_view(), name="resume_confirm_delete"),
    path("search/", views.PublicResumeListView.as_view(), name="public_resume_list"),
    path("view/<int:pk>/", views.ResumeDetailView.as_view(), name="public_resume_detail"),
    path('review/<str:teacher_id>/', views.create_review, name='create_review'),
]
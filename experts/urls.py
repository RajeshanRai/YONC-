from django.urls import path
from . import views

urlpatterns = [
    path('', views.expert_list, name='expert_list'),
    path('category/<slug:category_slug>/', views.expert_list_by_category, name='expert_list_by_category'),
    path('province/<str:province_code>/', views.expert_list_by_province, name='expert_list_by_province'),
    path('apply/', views.apply_expert, name='apply_expert'),
    path('application-status/', views.application_status, name='application_status'),
    path('dashboard/', views.expert_dashboard, name='expert_dashboard'),
    path('dashboard/edit/', views.expert_profile_edit, name='expert_profile_edit'),
    path('dashboard/availability/', views.expert_availability, name='expert_availability'),
    path('dashboard/availability/<int:pk>/delete/', views.expert_availability_delete, name='expert_availability_delete'),
    path('dashboard/experience/', views.expert_experience, name='expert_experience'),
    path('dashboard/experience/<int:pk>/delete/', views.expert_experience_delete, name='expert_experience_delete'),
    path('<int:pk>/', views.expert_detail, name='expert_detail'),
]

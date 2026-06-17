from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('<int:pk>/register/', views.register_for_event, name='register_for_event'),
    path('<int:pk>/unregister/', views.unregister_for_event, name='unregister_for_event'),
]

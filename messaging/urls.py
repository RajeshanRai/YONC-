from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('chat/<int:user_id>/', views.chat_view, name='chat_view'),
    path('send/', views.send_message, name='send_message'),
    path('get/<int:user_id>/', views.get_messages, name='get_messages'),
    path('conversations/', views.get_conversations, name='get_conversations'),
    path('start/<int:expert_id>/', views.start_chat, name='start_chat'),
]

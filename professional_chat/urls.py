from django.urls import path
from . import views

app_name = 'professional_chat'

urlpatterns = [
    path('', views.chat_group_list, name='chat_group_list'),
    path('create/', views.create_chat_group, name='create_chat_group'),
    path('invite/<str:token>/', views.join_private_group_with_token, name='join_private_group_with_token'),
    path('<int:pk>/', views.chat_group_detail, name='chat_group_detail'),
    path('<int:pk>/add-member/', views.add_private_group_member, name='add_private_group_member'),
    path('<int:pk>/members/<int:user_id>/promote/', views.promote_group_member_to_moderator, name='promote_group_member_to_moderator'),
    path('<int:pk>/members/<int:user_id>/remove/', views.remove_group_member, name='remove_group_member'),
    path('<int:pk>/send/', views.send_message, name='send_message'),
    path(
        '<int:pk>/members/<int:user_id>/demote/',
        views.demote_group_moderator,
        name='demote_group_moderator',
    ),
    path('<int:pk>/messages/', views.get_messages, name='get_messages'),
    path('<int:pk>/messages/<int:message_id>/edit/', views.edit_group_message, name='edit_group_message'),
    path('<int:pk>/messages/<int:message_id>/delete/', views.delete_group_message, name='delete_group_message'),
    path('<int:pk>/join/', views.join_group, name='join_group'),
    path('<int:pk>/leave/', views.leave_group, name='leave_group'),
    path('<int:pk>/delete/', views.delete_chat_group, name='delete_chat_group'),
]

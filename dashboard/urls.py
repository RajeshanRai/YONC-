from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('experts/', views.manage_experts, name='manage_experts'),
    path('applications/', views.manage_applications, name='manage_applications'),
    path('users/', views.manage_users, name='manage_users'),
    path('partners/', views.manage_partners, name='manage_partners'),
    path('partners/add/', views.create_partner, name='create_partner'),
    path('partners/<int:partner_id>/edit/', views.edit_partner, name='edit_partner'),
    path('events/', views.manage_events, name='manage_events'),
    path('events/add/', views.create_event, name='create_event'),
    path('events/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('messages/', views.manage_messages, name='manage_messages'),
    path('messages/conversation/<int:conversation_id>/delete-all/', views.delete_conversation_messages, name='delete_conversation_messages'),
    path('messages/group/<int:group_id>/delete-all/', views.delete_group_messages, name='delete_group_messages'),
    path('messages/group/<int:group_id>/delete/', views.delete_group, name='delete_group'),
    path('contacts/', views.manage_contacts, name='manage_contacts'),
    path('contacts/<int:contact_id>/', views.contact_detail, name='contact_detail'),
    path('api/contacts/<int:contact_id>/toggle-read/', views.toggle_contact_read, name='toggle_contact_read'),
    path('api/contacts/<int:contact_id>/toggle-replied/', views.toggle_contact_replied, name='toggle_contact_replied'),
    path('api/contacts/<int:contact_id>/delete/', views.delete_contact, name='delete_contact'),
    # AJAX endpoints
    path('api/applications/<int:app_id>/approve/', views.approve_application, name='approve_application'),
    path('api/applications/<int:app_id>/reject/', views.reject_application, name='reject_application'),
    path('api/experts/<int:expert_id>/toggle-featured/', views.toggle_expert_featured, name='toggle_expert_featured'),
    path('api/users/<int:user_id>/toggle-active/', views.toggle_user_active, name='toggle_user_active'),
    path('api/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('api/partners/<int:partner_id>/toggle-active/', views.toggle_partner_active, name='toggle_partner_active'),
    path('api/stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
]

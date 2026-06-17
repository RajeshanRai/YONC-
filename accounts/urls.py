from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('accounts/profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('accounts/profile/<int:pk>/', views.public_profile_view, name='public_profile'),
    path('accounts/messages/read/', views.mark_messages_read, name='mark_messages_read'),
    path('accounts/email-verification/sent/', views.verification_sent_view, name='email_verification_sent'),
    path('accounts/email-verification/', views.verify_email_view, name='verify_email'),
    path('accounts/email-verification/resend/', views.resend_verification_view, name='resend_verification'),
]

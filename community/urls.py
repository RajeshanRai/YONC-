from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.forum_home, name='forum_home'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/like/', views.post_like, name='post_like'),
    path('post/<int:pk>/comment_ajax/', views.comment_ajax, name='comment_ajax'),
    path('comments/<int:comment_id>/replies/', views.comment_replies, name='comment_replies'),
    path('post/new/', views.new_post, name='new_post'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('comment/<int:comment_id>/edit/', views.comment_edit, name='comment_edit'),
    path('comment/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
    path('comment/<int:comment_id>/pin/', views.comment_pin, name='comment_pin'),
]

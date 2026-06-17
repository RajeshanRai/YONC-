from django.contrib import admin

from .models import ForumPost, ForumComment


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_at', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('title', 'content', 'author__username')
    date_hierarchy = 'created_at'


@admin.register(ForumComment)
class ForumCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('content', 'author__username', 'post__title')
    date_hierarchy = 'created_at'

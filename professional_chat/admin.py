from django.contrib import admin
from .models import ChatGroup, GroupMember, ChatMessage


@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_public', 'member_count', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Group Information', {
            'fields': ('name', 'description', 'is_public')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'group__name')
    readonly_fields = ('joined_at',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'group', 'is_flagged', 'toxicity_reason', 'created_at')
    list_filter = ('is_flagged', 'toxicity_reason', 'created_at')
    search_fields = ('sender__username', 'group__name', 'content')
    readonly_fields = ('created_at', 'updated_at', 'toxicity_score')
    fieldsets = (
        ('Message', {
            'fields': ('group', 'sender', 'content')
        }),
        ('Moderation', {
            'fields': ('is_flagged', 'toxicity_score', 'toxicity_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


from django.contrib import admin
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'get_subject_display', 'created_at', 'is_read', 'replied')
    list_filter = ('created_at', 'is_read', 'subject', 'replied')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email')
        }),
        ('Message', {
            'fields': ('subject', 'message', 'created_at')
        }),
        ('Status', {
            'fields': ('is_read', 'replied')
        }),
    )

    def get_subject_display(self, obj):
        return obj.get_subject_display()
    get_subject_display.short_description = 'Subject'

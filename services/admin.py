from django.contrib import admin
from .models import ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'display_order', 'is_active', 'expert_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')
    
    def expert_count(self, obj):
        return obj.expert_profiles.filter(is_approved=True).count()
    expert_count.short_description = 'Active Experts'

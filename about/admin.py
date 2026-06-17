from django.contrib import admin
from .models import Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'website')
    ordering = ('sort_order', 'name')

from django.contrib import admin

from .models import Event, EventRegistration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'location', 'is_online', 'is_ticketed', 'price', 'total_seats')
    list_filter = ('is_online', 'is_ticketed', 'is_featured')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_time'


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'registered_at')
    search_fields = ('event__title', 'user__username', 'user__email')
    date_hierarchy = 'registered_at'

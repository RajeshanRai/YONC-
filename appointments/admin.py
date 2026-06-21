from django.contrib import admin

from .models import TimeSlot, Appointment


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('expert', 'start_time', 'end_time', 'capacity', 'is_booked')
    list_filter = ('is_booked', 'expert__category', 'expert__province')
    search_fields = ('expert__user__username', 'expert__user__first_name', 'expert__user__last_name')
    date_hierarchy = 'start_time'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('subject', 'expert', 'user', 'timeslot', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject', 'user__username', 'expert__user__username')
    date_hierarchy = 'created_at'

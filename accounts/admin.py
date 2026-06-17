from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, PendingUserRegistration


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'province')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('YONC Profile', {'fields': ('role', 'phone_number', 'province', 'city', 'profile_picture', 'bio')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('YONC Profile', {
            'classes': ('wide',),
            'fields': ('role', 'phone_number', 'province', 'city'),
        }),
    )


@admin.register(PendingUserRegistration)
class PendingUserRegistrationAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'created_at', 'is_valid', 'remaining_seconds')
    list_filter = ('created_at', 'is_used')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('verification_code', 'created_at')
    
    fieldsets = (
        ('Registration Info', {
            'fields': ('email', 'username', 'first_name', 'last_name', 'phone_number', 'province', 'city')
        }),
        ('Verification', {
            'fields': ('verification_code', 'created_at', 'is_used')
        }),
    )
    
    def get_queryset(self, request):
        """Only show valid (non-expired) pending registrations."""
        return PendingUserRegistration.objects.valid()
    
    def has_add_permission(self, request):
        """Prevent manual creation from admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing pending registrations."""
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_role', 'get_province', 'get_city', 'created_at')
    list_filter = ('is_profile_complete',)
    search_fields = ('user__username', 'user__email', 'user__city')

    def get_role(self, obj):
        return obj.user.get_role_display()
    get_role.short_description = 'Role'

    def get_province(self, obj):
        return obj.user.get_province_display()
    get_province.short_description = 'Province'

    def get_city(self, obj):
        return obj.user.city
    get_city.short_description = 'City'

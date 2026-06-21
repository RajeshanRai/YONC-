from django.contrib import admin
from .models import ExpertProfile, ExpertApplication


@admin.register(ExpertProfile)
class ExpertProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'get_full_name', 'province', 'city', 'years_experience', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('is_approved', 'is_featured', 'category', 'province')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'bio', 'city')
    list_editable = ('is_approved', 'is_featured')
    date_hierarchy = 'created_at'
    
    def get_full_name(self, obj):
        return obj.user.get_full_name_display()
    get_full_name.short_description = 'Expert Name'
    
    actions = ['approve_experts', 'feature_experts', 'unfeature_experts']
    
    def approve_experts(self, request, queryset):
        queryset.update(is_approved=True)
        for profile in queryset:
            profile.user.role = 'expert'
            profile.user.save()
    approve_experts.short_description = 'Approve selected experts'
    
    def feature_experts(self, request, queryset):
        queryset.update(is_featured=True)
    feature_experts.short_description = 'Feature selected experts'
    
    def unfeature_experts(self, request, queryset):
        queryset.update(is_featured=False)
    unfeature_experts.short_description = 'Unfeature selected experts'


@admin.register(ExpertApplication)
class ExpertApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'province', 'city', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('status', 'category', 'province')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'submitted_at'
    
    actions = ['approve_applications', 'reject_applications']
    readonly_fields = ('submitted_at', 'reviewed_at', 'reviewed_by')
    
    def save_model(self, request, obj, form, change):
        if change and obj.pk:
            original = ExpertApplication.objects.get(pk=obj.pk)
            if original.status != obj.status:
                if obj.status == 'approved':
                    obj.approve(reviewer=request.user)
                    return
                if obj.status == 'rejected':
                    obj.reject(reviewer=request.user)
                    return
        super().save_model(request, obj, form, change)
    
    def approve_applications(self, request, queryset):
        for app in queryset:
            app.approve(reviewer=request.user)
    approve_applications.short_description = 'Approve selected applications'
    
    def reject_applications(self, request, queryset):
        for app in queryset:
            app.reject(reviewer=request.user)
    reject_applications.short_description = 'Reject selected applications'

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Notification, AuditLog


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'profile__role')
    
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return "No Profile"
    get_role.short_description = 'Role'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'employee_id', 'department', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'department')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'priority', 'is_read', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')
    readonly_fields = ('created_at', 'read_at')
    
    def mark_as_read(self, request, queryset):
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(request, f"{queryset.count()} notifications marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    actions = ['mark_as_read']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'description', 'model_name')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'user_agent', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

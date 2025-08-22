from django.contrib import admin
from .models import User, Status, Issue, Comment, Settings, Tag


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at', 'is_staff')
    list_filter = ('is_staff', 'is_active', 'created_at')
    search_fields = ('name', 'email')
    readonly_fields = ('created_at',)


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_open')
    list_filter = ('is_open',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'issue_count')
    search_fields = ('name',)
    ordering = ('name',)
    
    def issue_count(self, obj):
        return obj.issues.count()
    issue_count.short_description = 'Issues'


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('summary', 'status', 'author', 'assignee', 'created_at', 'updated_at')
    list_filter = ('status', 'tags', 'created_at', 'updated_at')
    search_fields = ('summary', 'description')
    raw_id_fields = ('author', 'assignee')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('status', 'author', 'assignee').prefetch_related('tags')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('issue', 'author', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('content',)
    raw_id_fields = ('author', 'issue')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'issue')


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Slack Configuration', {
            'fields': ('slack_bot_token', 'slack_channel_id')
        }),
        ('GitHub Configuration', {
            'fields': ('github_access_token', 'github_repository_owner', 'github_repository_name')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance of settings
        return not Settings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False
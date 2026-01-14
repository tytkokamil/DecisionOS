from django.contrib import admin
from .models import Team, TeamMember, Decision, DecisionOption, DecisionReview, DecisionAudit, DecisionAttachment, Notification, DecisionComment


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['team', 'user', 'role', 'joined_at']
    list_filter = ['role', 'team']


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ['title', 'team', 'status', 'priority', 'created_by', 'created_at']
    list_filter = ['status', 'priority', 'team']
    search_fields = ['title', 'description']


@admin.register(DecisionOption)
class DecisionOptionAdmin(admin.ModelAdmin):
    list_display = ['title', 'decision', 'created_at']


@admin.register(DecisionReview)
class DecisionReviewAdmin(admin.ModelAdmin):
    list_display = ['decision', 'reviewer', 'status', 'created_at', 'reviewed_at']
    list_filter = ['status']


@admin.register(DecisionAudit)
class DecisionAuditAdmin(admin.ModelAdmin):
    list_display = ['decision', 'user', 'action', 'timestamp']
    list_filter = ['action']


@admin.register(DecisionAttachment)
class DecisionAttachmentAdmin(admin.ModelAdmin):
    list_display = ['decision', 'filename', 'uploaded_by', 'uploaded_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notif_type', 'title', 'is_read', 'created_at']
    list_filter = ['notif_type', 'is_read']
    search_fields = ['title', 'message', 'user__username']


@admin.register(DecisionComment)
class DecisionCommentAdmin(admin.ModelAdmin):
    list_display = ['decision', 'user', 'parent', 'created_at']
    list_filter = ['decision']
    search_fields = ['text', 'user__username', 'decision__title']

# admin.py

from django.contrib import admin
from .models import (
    CustomUser, Domain, Tag, Project, CollaborationRequest, ProjectMember,
    Workspace, WorkspaceNote, Task, WorkspaceFile, WorkspaceChatMessage, Milestone,
    Follow, Comment, Like, ChatMessage, Community, Badge, UserBadge,
    AIRecommendation, ProjectTemplate, ProjectCollaboration
)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'name', 'email', 'location', 'reputation_points', 'contribution_streak']
    list_filter = ['date', 'location']
    search_fields = ['username', 'name', 'email']


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain']
    list_filter = ['domain']
    search_fields = ['name']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'domain', 'stage', 'status', 'visibility', 'created_at']
    list_filter = ['stage', 'status', 'visibility', 'domain', 'created_at']
    search_fields = ['title', 'description', 'user__username']
    filter_horizontal = ['tags']


@admin.register(CollaborationRequest)
class CollaborationRequestAdmin(admin.ModelAdmin):
    list_display = ['project', 'requester', 'role', 'status', 'created_at']
    list_filter = ['status', 'role', 'created_at']
    search_fields = ['project__title', 'requester__username']


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['project__title', 'user__username']


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['project', 'created_at']
    search_fields = ['project__title']


@admin.register(WorkspaceNote)
class WorkspaceNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'workspace', 'author', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['title', 'content']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'workspace', 'status', 'priority', 'assigned_to', 'due_date']
    list_filter = ['status', 'priority', 'due_date']
    search_fields = ['title', 'description']


@admin.register(WorkspaceFile)
class WorkspaceFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'workspace', 'file_type', 'uploaded_by', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['name']


@admin.register(WorkspaceChatMessage)
class WorkspaceChatMessageAdmin(admin.ModelAdmin):
    list_display = ['workspace', 'sender', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['message']


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'workspace', 'due_date', 'completed']
    list_filter = ['completed', 'due_date']
    search_fields = ['title', 'description']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'user__username']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['project__title', 'user__username']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'project', 'timestamp', 'read']
    list_filter = ['timestamp', 'read']
    search_fields = ['message']


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ['name', 'community_type', 'created_by', 'created_at']
    list_filter = ['community_type', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['members']


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_required']
    search_fields = ['name']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_at']
    list_filter = ['earned_at']
    search_fields = ['user__username', 'badge__name']


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'project__title']


@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'created_at']
    list_filter = ['domain', 'created_at']
    search_fields = ['name', 'description']


@admin.register(ProjectCollaboration)
class ProjectCollaborationAdmin(admin.ModelAdmin):
    list_display = ['project', 'requester', 'invitee', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['project__title', 'requester__username', 'invitee__username']

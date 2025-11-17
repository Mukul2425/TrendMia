# myapp/models.py

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json


# ==================== USER MODEL ====================
class CustomUserManager(models.Manager):
    pass


class CustomUser(AbstractUser):
    """Enhanced user model with skills, location, and profile information"""
    name = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    bio = models.TextField(blank=True, null=True, max_length=500)
    location = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    college = models.CharField(max_length=200, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    skills = models.JSONField(default=dict, blank=True, help_text="JSON format: {'skill_name': 'level'}")
    reputation_points = models.IntegerField(default=0)
    contribution_streak = models.IntegerField(default=0)
    last_contribution_date = models.DateField(null=True, blank=True)
    
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return self.username
    
    @property
    def followers_count(self):
        return self.followers.count()
    
    @property
    def following_count(self):
        return self.following.count()
    
    @property
    def projects_count(self):
        return self.project_set.count()
    
    def update_contribution_streak(self):
        """Update contribution streak based on daily activity"""
        today = timezone.now().date()
        if self.last_contribution_date:
            days_diff = (today - self.last_contribution_date).days
            if days_diff == 1:
                self.contribution_streak += 1
            elif days_diff > 1:
                self.contribution_streak = 1
        else:
            self.contribution_streak = 1
        self.last_contribution_date = today
        self.save()


# ==================== DOMAIN & TAGS ====================
class Domain(models.Model):
    """Project domains (AI, Robotics, Web Dev, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or emoji")
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tags for projects"""
    name = models.CharField(max_length=100, unique=True)
    domain = models.ForeignKey(Domain, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name


# ==================== PROJECT MODEL ====================
class Project(models.Model):
    """Main project model with all required fields"""
    STAGE_CHOICES = [
        ('idea', 'Idea'),
        ('seeking_collaborators', 'Seeking Collaborators'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('unlisted', 'Unlisted'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200, blank=True)
    heading = models.TextField(blank=True)  # Keep for backward compatibility
    project_name = models.CharField(max_length=200, blank=True)  # Keep for backward compatibility
    description = models.TextField(blank=True)
    project_description = models.TextField(blank=True)  # Keep for backward compatibility
    problem_statement = models.TextField(blank=True)
    
    # Project Details
    domain = models.ForeignKey(Domain, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    skills_required = models.JSONField(default=list, blank=True, help_text="List of required skills")
    
    # Status & Visibility
    status = models.CharField(max_length=20, choices=[('ongoing', 'Ongoing'), ('completed', 'Completed')], default='ongoing')
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES, default='idea')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    
    # Location
    location = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Media
    cover_image = models.ImageField(upload_to='project_covers/', blank=True, null=True)
    demo_video_url = models.URLField(blank=True, null=True)
    
    # Owner & Timestamps
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metrics
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title or self.project_name or self.heading or "Untitled Project"
    
    def save(self, *args, **kwargs):
        # Auto-populate title from project_name or heading for backward compatibility
        if not self.title:
            if self.project_name:
                self.title = self.project_name
            elif self.heading:
                self.title = self.heading
            else:
                self.title = "Untitled Project"
        # Auto-populate description from project_description for backward compatibility
        if not self.description and self.project_description:
            self.description = self.project_description
        super().save(*args, **kwargs)
    
    def get_tags_list(self):
        """Get tags as comma-separated string for backward compatibility"""
        return ', '.join([tag.name for tag in self.tags.all()])


# ==================== COLLABORATION ====================
class CollaborationRequest(models.Model):
    """Collaboration requests with skills and role"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('researcher', 'Researcher'),
        ('designer', 'Designer'),
        ('mentor', 'Mentor'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='collaboration_requests')
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_collab_requests')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='developer')
    skills = models.JSONField(default=list, help_text="List of skills")
    experience = models.TextField(blank=True)
    message = models.TextField(help_text="Why they want to join")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('project', 'requester')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.requester.username} -> {self.project.title} ({self.status})"


class ProjectMember(models.Model):
    """Members of a project (accepted collaborators)"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('developer', 'Developer'),
        ('researcher', 'Researcher'),
        ('designer', 'Designer'),
        ('mentor', 'Mentor'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='developer')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('project', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.project.title} ({self.role})"


# ==================== WORKSPACE ====================
class Workspace(models.Model):
    """Private workspace for each project"""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='workspace')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Workspace: {self.project.title}"


class WorkspaceNote(models.Model):
    """Collaborative notes in workspace"""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} - {self.workspace.project.title}"


class Task(models.Model):
    """Tasks in workspace (Kanban board)"""
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.workspace.project.title}"


class WorkspaceFile(models.Model):
    """Files uploaded to workspace"""
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('image', 'Image'),
        ('code', 'Code'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='workspace_files/')
    name = models.CharField(max_length=200)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='other')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.name} - {self.workspace.project.title}"


class WorkspaceChatMessage(models.Model):
    """Chat messages in workspace"""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username} - {self.workspace.project.title}"


class Milestone(models.Model):
    """Project milestones"""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['due_date', 'created_at']
    
    def __str__(self):
        return f"{self.title} - {self.workspace.project.title}"


# ==================== SOCIAL FEATURES ====================
class Follow(models.Model):
    """User following system"""
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Comment(models.Model):
    """Comments on projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.project.title}"


class Like(models.Model):
    """Likes on projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('project', 'user')
    
    def __str__(self):
        return f"{self.user.username} likes {self.project.title}"


class ChatMessage(models.Model):
    """Direct messages between users"""
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}"


# ==================== COMMUNITIES ====================
class Community(models.Model):
    """Micro-communities (college, tech clubs, etc.)"""
    COMMUNITY_TYPES = [
        ('college', 'College'),
        ('tech_club', 'Tech Club'),
        ('research_group', 'Research Group'),
        ('hackathon', 'Hackathon'),
        ('general', 'General'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    community_type = models.CharField(max_length=30, choices=COMMUNITY_TYPES, default='general')
    domain = models.ForeignKey(Domain, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    college = models.CharField(max_length=200, blank=True, null=True)
    cover_image = models.ImageField(upload_to='community_covers/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='communities', blank=True)
    
    def __str__(self):
        return self.name


# ==================== GAMIFICATION ====================
class Badge(models.Model):
    """Badges for achievements"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)
    points_required = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """User badges"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


# ==================== AI FEATURES ====================
class AIRecommendation(models.Model):
    """AI-generated recommendations"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_recommendations')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ai_recommendations')
    score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'project')
        ordering = ['-score', '-created_at']
    
    def __str__(self):
        return f"AI Rec: {self.user.username} -> {self.project.title} ({self.score:.2f})"


# ==================== PROJECT TEMPLATES ====================
class ProjectTemplate(models.Model):
    """Templates for starting projects"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    domain = models.ForeignKey(Domain, on_delete=models.SET_NULL, null=True, blank=True)
    template_data = models.JSONField(default=dict, help_text="Template structure with milestones, tasks, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


# ==================== BACKWARD COMPATIBILITY ====================
# Keep old ProjectCollaboration model for backward compatibility
class ProjectCollaboration(models.Model):
    """Legacy collaboration model - kept for backward compatibility"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='legacy_collaborations')
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='legacy_sent_collab_requests')
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='legacy_received_collab_requests')
    role = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'requester', 'invitee')

    def __str__(self):
        return f"{self.requester.username} -> {self.invitee.username} for {self.project.title} ({self.status})"

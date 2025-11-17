# myapp/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    CustomUser, Project, CollaborationRequest, WorkspaceNote, Task,
    WorkspaceFile, Milestone, Comment, Community, ProjectTemplate
)

# Skill levels for user skills
SKILL_LEVELS = [
    ('beginner', 'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
    ('expert', 'Expert'),
]

# Domain choices (will be populated from database)
DOMAIN_CHOICES = [
    ('AI', 'AI'),
    ('Robotics', 'Robotics'),
    ('Web Development', 'Web Development'),
    ('Mobile Development', 'Mobile Development'),
    ('Cybersecurity', 'Cybersecurity'),
    ('Data Science', 'Data Science'),
    ('Biotech', 'Biotech'),
    ('IoT', 'IoT'),
    ('Blockchain', 'Blockchain'),
    ('AR/VR', 'AR/VR'),
    ('Other', 'Other'),
]


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City, State, Country'})
    )
    college = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your college/university'})
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'password1', 'password2', 'location', 'college']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username or email'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )


class ProjectForm(forms.ModelForm):
    """Enhanced project form with all required fields"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Title'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Project Description'})
    )
    problem_statement = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What problem does this solve?'})
    )
    skills_required = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated skills (e.g., Python, React, ML)'}),
        help_text="Enter skills separated by commas"
    )
    demo_video_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Demo video URL (YouTube, Vimeo, etc.)'})
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location (City, State, Country)'})
    )

    class Meta:
        model = Project
        fields = [
            'title', 'description', 'problem_statement', 'domain', 'tags',
            'skills_required', 'stage', 'visibility', 'location', 'cover_image', 'demo_video_url'
        ]
        widgets = {
            'domain': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'stage': forms.Select(attrs={'class': 'form-control'}),
            'visibility': forms.Select(attrs={'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_skills_required(self):
        skills = self.cleaned_data.get('skills_required', '')
        if skills:
            return [skill.strip() for skill in skills.split(',') if skill.strip()]
        return []

    def save(self, commit=True):
        project = super().save(commit=False)
        skills = self.cleaned_data.get('skills_required', [])
        if skills:
            project.skills_required = skills
        if commit:
            project.save()
            self.save_m2m()
        return project


class CollaborationRequestForm(forms.ModelForm):
    """Form for requesting collaboration"""
    skills = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated skills'}),
        help_text="List your relevant skills"
    )
    experience = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your experience and background'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Why do you want to join this project?'})
    )

    class Meta:
        model = CollaborationRequest
        fields = ['role', 'skills', 'experience', 'message']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_skills(self):
        skills = self.cleaned_data.get('skills', '')
        if skills:
            return [skill.strip() for skill in skills.split(',') if skill.strip()]
        return []


class WorkspaceNoteForm(forms.ModelForm):
    """Form for workspace notes"""
    class Meta:
        model = WorkspaceNote
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Note title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Write your notes here...'}),
        }


class TaskForm(forms.ModelForm):
    """Form for creating/editing tasks"""
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Task description'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class WorkspaceFileForm(forms.ModelForm):
    """Form for uploading files to workspace"""
    class Meta:
        model = WorkspaceFile
        fields = ['file', 'name', 'file_type']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'File name'}),
            'file_type': forms.Select(attrs={'class': 'form-control'}),
        }


class MilestoneForm(forms.ModelForm):
    """Form for creating milestones"""
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Milestone title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Milestone description'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class CommentForm(forms.ModelForm):
    """Form for commenting on projects"""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write a comment...',
                'style': 'resize: none;'
            }),
        }


class CommunityForm(forms.ModelForm):
    """Form for creating communities"""
    class Meta:
        model = Community
        fields = ['name', 'description', 'community_type', 'domain', 'location', 'college', 'cover_image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Community name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Community description'}),
            'community_type': forms.Select(attrs={'class': 'form-control'}),
            'domain': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'college': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'College/University'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile"""
    skills_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="JSON format: {'skill_name': 'level'}"
    )

    class Meta:
        model = CustomUser
        fields = ['name', 'bio', 'location', 'city', 'state', 'country', 'college', 'website', 'avatar']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'college': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

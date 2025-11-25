# myapp/views.py

from django.shortcuts import render, redirect, HttpResponse,render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from .forms import SignUpForm, ProjectForm
from datetime import datetime
import supabase
from .models import Tag,Project
from django.utils import timezone
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.db import models

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ipywidgets as widgets

from .models import (
    ChatMessage, CustomUser, Project, Follow, Comment, ProjectCollaboration,
    Domain, Tag, CollaborationRequest, ProjectMember, Workspace, WorkspaceNote,
    Task, WorkspaceFile, WorkspaceChatMessage, Milestone, Like, Community,
    Badge, UserBadge, AIRecommendation, ProjectTemplate
)
from .forms import (
    SignUpForm, ProjectForm, CollaborationRequestForm, WorkspaceNoteForm,
    TaskForm, WorkspaceFileForm, MilestoneForm, CommentForm, CommunityForm, ProfileEditForm
)
from .ai_utils import (
    find_collaborator_matches, get_ai_project_recommendations,
    generate_project_starter_kit, suggest_next_steps
)
from django.db.models import Q, Count
from django.core.paginator import Paginator  

# Initialize Supabase client
supabase_url = 'https://oypasfbahsankiotfziv.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im95cGFzZmJhaHNhbmtpb3Rmeml2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTAwODIxNTEsImV4cCI6MjAyNTY1ODE1MX0.buYR2zFe7Y9mjNbDDvl--CVAWwb8XoQUN6y0iKKiyhg'
supabase_client = supabase.create_client(supabase_url, supabase_key)


def index(request):
    context = {
        "variable": "This is sent",
        "form": SignUpForm(),  # Pass the SignUpForm instance to the context
    }
    return render(request, 'index.html', context)

# def trending(request):
#     return HttpResponse("This is t page")

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.signup_datetime = datetime.now()
                user.save()

                # Redirect to login page upon successful signup
                return redirect('login')
            except Exception as e:
                # Handle any exceptions
                print(e)
                # Redirect to homepage if an error occurs
                return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'index.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)  # Use Django's built-in AuthenticationForm
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)  # Log the user in
                return redirect('feed')  # Redirect to the feed page upon successful login
            else:
                # Authentication failed, display an error message
                return render(request, 'login.html', {'login_form': form, 'error_message': 'Invalid username or password.'})
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'login_form': form})

def logout_view(request):
    logout(request)
    return redirect('login')



def about(request):
    return HttpResponse("This is about page")


def plot_tag_history(tag):
    data = pd.read_excel('projects.xlsx', sheet_name='Sheet1')

    # Convert 'date/timestamp' column to datetime
    data['date/timestamp'] = pd.to_datetime(data['date/timestamp'])

    # Extract month and year from the 'date/timestamp' column
    data['month_year'] = data['date/timestamp'].dt.to_period('M')

    # Split tags and convert them to lists
    data['tags'] = data['tags'].str.split(', ')

    if tag in data['tags'].sum():
        # Prepare data for the specified tag
        tag_history = data[data['tags'].apply(lambda x: tag in x)]
        tag_history_counts = tag_history.groupby('month_year').size()

        # Plotting tag history
        plt.figure(figsize=(6, 4))
        tag_history_counts.plot(kind='line', color='r', linewidth=2)
        plt.xlabel('MonthYear')
        plt.ylabel('Occurrences')
        plt.title(f'History of Tag "{tag}" Over Past Months')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.legend().set_visible(False)
        # In your plot_tag_history function
        plt.savefig('static/dist/images/tag_history_plot.png')  # Save the plot to a static file
        plt.close()
    else:
        print("Tag not found in the data.")

def trending(request):
    # Load and process data
    data = pd.read_excel('projects.xlsx', sheet_name='Sheet1')
    data['date/timestamp'] = pd.to_datetime(data['date/timestamp'])
    data['month_year'] = data['date/timestamp'].dt.to_period('M')
    data['tags'] = data['tags'].str.split(', ')

    # Calculate tag counts
    unique_months = sorted(data['month_year'].unique())
    weights = {month: 1 / (len(unique_months) - i) for i, month in enumerate(unique_months)}
    tag_counts = {}
    for index, row in data.iterrows():
        for tag in row['tags']:
            tag_counts[tag] = tag_counts.get(tag, 0) + weights[row['month_year']]

    # Sort tag counts
    tag_counts_sorted = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    context = {
        'tag_counts': tag_counts_sorted,
    }

    if request.method == 'POST':
        # Get selected tag from the form
        selected_tag = request.POST.get('tag_dropdown', None)
        if selected_tag:
            plot_tag_history(selected_tag)
            context['selected_tag'] = selected_tag

    return render(request, 'trending.html', context)

def contact(request):
    return HttpResponse("This is contact page")

def profile_view(request):
    user = request.user
    posts = Project.objects.filter(user=user).order_by('-created_at')
    # Accepted collaborations where the user is requester or invitee
    collaborated = ProjectCollaboration.objects.filter(
        models.Q(requester=user) | models.Q(invitee=user), status='accepted'
    ).select_related('project').order_by('-created_at')
    collaborated_projects = [c.project for c in collaborated]
    
    # Get followers and following
    followers = user.followers.all()
    following = user.following.all()
    
    # Get follower and following user objects
    follower_users = [follow.follower for follow in followers]
    following_users = [follow.following for follow in following]
    
    collab_requests = CollaborationRequest.objects.filter(
        project__user=user
    ).select_related('project', 'requester').order_by('-created_at')
    
    context = {
        'user': user,
        'posts': posts,
        'collaborated_projects': collaborated_projects,
        'followers': follower_users,
        'following': following_users,
        'followers_count': len(follower_users),
        'following_count': len(following_users),
        'collab_requests': collab_requests,
    }
    
    return render(request, 'profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'profile_edit.html', {'form': form})

def user_profile_view(request, username):
    """View another user's profile"""
    try:
        profile_user = CustomUser.objects.get(username=username)
        posts = Project.objects.filter(user=profile_user).order_by('-created_at')
        
        # Get followers and following
        followers = profile_user.followers.all()
        following = profile_user.following.all()
        
        # Get follower and following user objects
        follower_users = [follow.follower for follow in followers]
        following_users = [follow.following for follow in following]
        
        # Check if current user is following this profile user
        is_following = False
        if request.user.is_authenticated:
            is_following = Follow.objects.filter(
                follower=request.user, 
                following=profile_user
            ).exists()
        
        context = {
            'profile_user': profile_user,
            'posts': posts,
            'followers': follower_users,
            'following': following_users,
            'followers_count': len(follower_users),
            'following_count': len(following_users),
            'is_following': is_following,
            'is_own_profile': request.user == profile_user,
        }
        
        return render(request, 'user_profile.html', context)
    except CustomUser.DoesNotExist:
        return HttpResponse("User not found")

@login_required
def update_status_view(request, post_id):
    project = Project.objects.get(pk=post_id)
    if project.status == 'ongoing':
        project.status = 'completed'
    elif project.status == 'completed':
        project.status = 'ongoing'
    project.save()
    return redirect('profile')  

def feed(request):
    """Primary social feed with lightweight filters and ordering."""
    projects_qs = (
        Project.objects.select_related('user', 'domain')
        .prefetch_related('tags', 'comments__user')
        .order_by('-created_at')
    )
    
    city = request.GET.get('city', '').strip()
    tag_name = request.GET.get('tags', '').strip()
    status = request.GET.get('status', '').strip()
    
    if city:
        projects_qs = projects_qs.filter(
            Q(location__icontains=city) |
            Q(city__icontains=city) |
            Q(state__icontains=city) |
            Q(country__icontains=city)
        )
    if tag_name:
        projects_qs = projects_qs.filter(tags__name__icontains=tag_name)
    if status:
        projects_qs = projects_qs.filter(status=status)
    
    projects_qs = projects_qs.distinct()
    
    if request.user.is_authenticated:
        followed_ids = request.user.following.values_list('following_id', flat=True)
        followed_posts = list(projects_qs.filter(user_id__in=followed_ids))
        other_posts = list(projects_qs.exclude(user_id__in=followed_ids))
        recommended_posts = get_ai_recommendations(request.user, other_posts)
        
        ordered_posts = []
        seen_ids = set()
        for bucket in (followed_posts, recommended_posts, other_posts):
            for project in bucket:
                if project.id in seen_ids:
                    continue
                seen_ids.add(project.id)
                ordered_posts.append(project)
        posts = ordered_posts
    else:
        # Limit to 2 posts for non-authenticated users
        posts = list(projects_qs[:2])
    
    if request.user.is_authenticated:
        following_set = set(request.user.following.values_list('following_id', flat=True))
        liked_project_ids = set(Like.objects.filter(user=request.user).values_list('project_id', flat=True))
        for project in posts:
            project.is_following = project.user_id in following_set
            project.is_liked = project.id in liked_project_ids
    else:
        for project in posts:
            project.is_following = False
            project.is_liked = False
    
    tags = Tag.objects.all()
    return render(request, 'feed.html', {
        'posts': posts,
        'tags': tags,
    })

def get_ai_recommendations(user, posts):
    """Simple AI recommendation system based on user's project tags and interests"""
    if not posts:
        return []
    
    # Get user's project tags
    user_projects = Project.objects.filter(user=user).prefetch_related('tags')
    user_tags = []
    for project in user_projects:
        user_tags.extend([tag.name.lower() for tag in project.tags.all()])
    
    # Count tag frequency
    from collections import Counter
    tag_counts = Counter(user_tags)
    top_tags = [tag for tag, count in tag_counts.most_common(5)]
    
    # Score posts based on tag similarity
    scored_posts = []
    for post in posts:
        post_tags = [tag.name.lower() for tag in post.tags.all()]
        score = 0
        
        # Calculate similarity score
        for user_tag in top_tags:
            for post_tag in post_tags:
                if user_tag in post_tag or post_tag in user_tag:
                    score += 1
                elif any(word in post_tag for word in user_tag.split()):
                    score += 0.5
        
        if score > 0:
            post.ai_score = score
            scored_posts.append(post)
    
    # Sort by AI score and return top recommendations
    scored_posts.sort(key=lambda x: x.ai_score, reverse=True)
    return scored_posts[:10]  # Return top 10 recommendations

@login_required
def follow_user(request, username):
    """Follow or unfollow a user"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
        
    try:
        user_to_follow = CustomUser.objects.get(username=username)
        
        if request.user == user_to_follow:
            return JsonResponse({'success': False, 'error': 'Cannot follow yourself'})
        
        follow_obj, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            action = 'followed'
        else:
            follow_obj.delete()
            action = 'unfollowed'
        
        return JsonResponse({
            'success': True, 
            'action': action,
            'followers_count': user_to_follow.followers_count,
            'following_count': user_to_follow.following_count
        })
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def add_comment(request, project_id):
    """Add a comment to a project"""
    if request.method == 'POST':
        try:
            project = Project.objects.get(id=project_id)
            content = request.POST.get('content', '').strip()
            
            if not content:
                return JsonResponse({'success': False, 'error': 'Comment cannot be empty'})
            
            comment = Comment.objects.create(
                project=project,
                user=request.user,
                content=content
            )
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'user': comment.user.name,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
                }
            })
            
        except Project.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Project not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def post_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                project = form.save(commit=False)
                project.user = request.user
                
                # Auto-create workspace when project is created
                project.save()
                form.save_m2m()  # Save many-to-many relationships (tags)
                
                # Create workspace and add owner as member
                workspace, created = Workspace.objects.get_or_create(project=project)
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=request.user,
                    defaults={'role': 'owner'}
                )
                
                # Update user contribution streak
                request.user.update_contribution_streak()
                
                messages.success(request, "Project created successfully! Workspace is ready.")
                return redirect('project_detail', project_id=project.id)
            except Exception as e:
                messages.error(request, f"Error saving project: {str(e)}")
                return render(request, 'project/create.html', {'form': form})
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProjectForm()
    
    domains = Domain.objects.all()
    tags = Tag.objects.all()
    
    return render(request, 'project/create.html', {
        'form': form,
        'domains': domains,
        'tags': tags,
    })

    

@login_required
@require_POST
def request_collaboration(request, project_id, username):
    try:
        project = Project.objects.get(id=project_id)
        invitee = CustomUser.objects.get(username=username)
        role = request.POST.get('role', '')
        # Prevent sending a request to yourself
        if invitee == request.user:
            return JsonResponse({'success': False, 'error': 'You cannot collaborate with yourself'})
        collab, created = ProjectCollaboration.objects.get_or_create(
            project=project,
            requester=request.user,
            invitee=invitee,
            defaults={'role': role}
        )
        if not created and collab.status == 'declined':
            collab.status = 'pending'
            collab.role = role
            collab.save()
        return JsonResponse({'success': True, 'status': collab.status})
    except (Project.DoesNotExist, CustomUser.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Invalid project or user'})


@login_required
@require_POST
def respond_collaboration(request, collab_id):
    try:
        action = request.POST.get('action')  # 'accept' or 'decline'
        collab = ProjectCollaboration.objects.get(id=collab_id, invitee=request.user)
        if action == 'accept':
            collab.status = 'accepted'
        else:
            collab.status = 'declined'
        collab.save()
        # If AJAX, return JSON; otherwise redirect back to inbox or profile
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'status': collab.status})
        from django.contrib import messages as dj_messages
        if collab.status == 'accepted':
            dj_messages.success(request, 'Collaboration accepted.')
        else:
            dj_messages.info(request, 'Collaboration declined.')
        # Prefer redirect to profile to show Collaborated tab
        return redirect('profile')
    except ProjectCollaboration.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Request not found'})


@login_required
def chat_page(request, username):
    try:
        recipient = CustomUser.objects.get(username=username)
        if request.method == 'POST':
            message = request.POST.get('message', '').strip()
            project_id = request.POST.get('project_id')
            project = None
            if project_id:
                try:
                    project = Project.objects.get(id=project_id)
                except Project.DoesNotExist:
                    project = None
            if not message:
                return HttpResponse("Message cannot be empty")
            ChatMessage.objects.create(sender=request.user, recipient=recipient, project=project, message=message)
            return redirect('chat', username=username)
        else:
            messages = ChatMessage.objects.filter(sender=request.user, recipient=recipient) | \
                       ChatMessage.objects.filter(sender=recipient, recipient=request.user)
            messages = messages.order_by('timestamp')
            return render(request, 'chat.html', {'messages': messages, 'recipient': recipient})
    except CustomUser.DoesNotExist:
        return HttpResponse("User not found")



@login_required
def some_view_function(request):
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient_username')
        message = request.POST.get('message')
        project_name = request.POST.get('project_name')
        project_description = request.POST.get('project_description')
        # Assuming you also have the recipient user object based on the recipient username
        
        # Assuming project_data is populated based on the form data
        project_data = {
            'name': project_name,
            'description': project_description,
            'owner': request.user,
            'created_at': datetime.now(),
            # Add other project attributes as needed
        }

        # Get or create a Project object
        project, _ = Project.objects.get_or_create(**project_data)

        if recipient_username and message:
            try:
                recipient = CustomUser.objects.get(username=recipient_username)
                # Create a new ChatMessage object
                chat_message = ChatMessage.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    project=project,
                    message=message
                )
                return redirect('chat_page', username=recipient_username)
            except CustomUser.DoesNotExist:
                return HttpResponse("Recipient not found")
        else:
            return HttpResponse("Recipient username and message are required")
    else:
        return HttpResponse("Invalid request method")


@login_required
def inbox(request):
    # Distinct chat partners by latest message
    threads = (ChatMessage.objects
               .filter(models.Q(sender=request.user) | models.Q(recipient=request.user))
               .order_by('-timestamp'))
    partners = {}
    for msg in threads:
        other = msg.recipient if msg.sender == request.user else msg.sender
        if other.username not in partners:
            partners[other.username] = {
                'user': other,
                'last_message': msg,
                'time': msg.timestamp,
            }
    conversations = list(partners.values())
    # Group by following
    following_usernames = set(request.user.following.values_list('following__username', flat=True))
    conv_following = [c for c in conversations if c['user'].username in following_usernames]
    conv_others = [c for c in conversations if c['user'].username not in following_usernames]
    # Pending collaboration requests
    collab_requests = ProjectCollaboration.objects.filter(invitee=request.user, status='pending').select_related('project','requester')
    new_collab_requests = CollaborationRequest.objects.filter(project__user=request.user, status='pending').select_related('project', 'requester')
    return render(request, 'inbox.html', {
        'conversations_following': conv_following,
        'conversations_others': conv_others,
        'collab_requests': collab_requests,
        'new_collab_requests': new_collab_requests,
    })


# ==================== WORKSPACE VIEWS ====================

@login_required
def workspace_dashboard(request, project_id):
    """Workspace dashboard for a project"""
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user is a member
        is_member = ProjectMember.objects.filter(project=project, user=request.user).exists()
        is_owner = project.user == request.user
        
        if not (is_member or is_owner):
            messages.error(request, "You don't have access to this workspace")
            return redirect('feed')
        
        # Get or create workspace
        workspace, created = Workspace.objects.get_or_create(project=project)
        
        # If workspace was just created and collaborators exist, add them as members
        if created:
            # Add owner as member
            ProjectMember.objects.get_or_create(project=project, user=project.user, defaults={'role': 'owner'})
            # Add accepted collaborators
            accepted_collabs = CollaborationRequest.objects.filter(project=project, status='accepted')
            for collab in accepted_collabs:
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=collab.requester,
                    defaults={'role': collab.role}
                )
        
        # Get workspace data
        members = ProjectMember.objects.filter(project=project).select_related('user')
        tasks = workspace.tasks.all().order_by('-created_at')[:10]
        milestones = workspace.milestones.all().order_by('due_date')[:5]
        notes = workspace.notes.all().order_by('-updated_at')[:5]
        recent_files = workspace.files.all().order_by('-uploaded_at')[:5]
        recent_chat = workspace.chat_messages.all().order_by('-timestamp')[:10]
        
        # AI suggestions
        ai_suggestions = suggest_next_steps(workspace)
        
        # Get AI collaborator recommendations
        ai_collaborators = find_collaborator_matches(project, limit=5) if is_owner else []
        
        context = {
            'project': project,
            'workspace': workspace,
            'members': members,
            'tasks': tasks,
            'milestones': milestones,
            'notes': notes,
            'recent_files': recent_files,
            'recent_chat': recent_chat,
            'ai_suggestions': ai_suggestions,
            'ai_collaborators': ai_collaborators,
            'is_owner': is_owner,
        }
        
        return render(request, 'workspace/dashboard.html', context)
    except Project.DoesNotExist:
        messages.error(request, "Project not found")
        return redirect('feed')


@login_required
def workspace_chat(request, project_id):
    """Workspace chat room"""
    try:
        project = Project.objects.get(id=project_id)
        workspace, _ = Workspace.objects.get_or_create(project=project)
        
        # Check access
        is_member = ProjectMember.objects.filter(project=project, user=request.user).exists()
        is_owner = project.user == request.user
        if not (is_member or is_owner):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        if request.method == 'POST':
            message_text = request.POST.get('message', '').strip()
            if message_text:
                message = WorkspaceChatMessage.objects.create(
                    workspace=workspace,
                    sender=request.user,
                    message=message_text
                )
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'text': message.message,
                        'sender': message.sender.name,
                        'sender_id': message.sender.id,
                        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'timesince': message.timestamp.strftime('%b %d, %Y %I:%M %p')
                    }
                })
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        messages = workspace.chat_messages.all().order_by('timestamp')
        members = ProjectMember.objects.filter(project=project).select_related('user')
        
        return render(request, 'workspace/chat.html', {
            'project': project,
            'workspace': workspace,
            'messages': messages,
            'members': members,
        })
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)


@login_required
def workspace_notes(request, project_id):
    """Workspace notes"""
    try:
        project = Project.objects.get(id=project_id)
        workspace, _ = Workspace.objects.get_or_create(project=project)
        
        # Check access
        is_member = ProjectMember.objects.filter(project=project, user=request.user).exists()
        is_owner = project.user == request.user
        if not (is_member or is_owner):
            messages.error(request, "Access denied")
            return redirect('feed')
        
        if request.method == 'POST':
            form = WorkspaceNoteForm(request.POST)
            if form.is_valid():
                note = form.save(commit=False)
                note.workspace = workspace
                note.author = request.user
                note.save()
                messages.success(request, "Note created successfully")
                return redirect('workspace_notes', project_id=project_id)
        else:
            form = WorkspaceNoteForm()
        
        notes = workspace.notes.all().order_by('-updated_at')
        
        return render(request, 'workspace/notes.html', {
            'project': project,
            'workspace': workspace,
            'notes': notes,
            'form': form,
        })
    except Project.DoesNotExist:
        messages.error(request, "Project not found")
        return redirect('feed')


@login_required
def workspace_tasks(request, project_id):
    """Workspace task board (Kanban)"""
    try:
        project = Project.objects.get(id=project_id)
        workspace, _ = Workspace.objects.get_or_create(project=project)
        
        # Check access
        is_member = ProjectMember.objects.filter(project=project, user=request.user).exists()
        is_owner = project.user == request.user
        if not (is_member or is_owner):
            messages.error(request, "Access denied")
            return redirect('feed')
        
        if request.method == 'POST':
            form = TaskForm(request.POST)
            if form.is_valid():
                task = form.save(commit=False)
                task.workspace = workspace
                task.created_by = request.user
                task.save()
                messages.success(request, "Task created successfully")
                return redirect('workspace_tasks', project_id=project_id)
        else:
            form = TaskForm()
            # Filter assigned_to to workspace members only
            members = ProjectMember.objects.filter(project=project).select_related('user')
            form.fields['assigned_to'].queryset = CustomUser.objects.filter(
                id__in=[m.user.id for m in members] + [project.user.id]
            )
        
        # Group tasks by status
        tasks_todo = workspace.tasks.filter(status='todo').order_by('-created_at')
        tasks_in_progress = workspace.tasks.filter(status='in_progress').order_by('-created_at')
        tasks_review = workspace.tasks.filter(status='review').order_by('-created_at')
        tasks_done = workspace.tasks.filter(status='done').order_by('-created_at')
        
        members = ProjectMember.objects.filter(project=project).select_related('user')
        
        return render(request, 'workspace/tasks.html', {
            'project': project,
            'workspace': workspace,
            'form': form,
            'tasks_todo': tasks_todo,
            'tasks_in_progress': tasks_in_progress,
            'tasks_review': tasks_review,
            'tasks_done': tasks_done,
            'members': members,
        })
    except Project.DoesNotExist:
        messages.error(request, "Project not found")
        return redirect('feed')


@login_required
@require_POST
def update_task_status(request, task_id):
    """Update task status (AJAX)"""
    try:
        task = Task.objects.get(id=task_id)
        # Check access
        is_member = ProjectMember.objects.filter(project=task.workspace.project, user=request.user).exists()
        is_owner = task.workspace.project.user == request.user
        if not (is_member or is_owner):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        new_status = request.POST.get('status')
        if new_status in ['todo', 'in_progress', 'review', 'done']:
            task.status = new_status
            task.save()
            return JsonResponse({'success': True, 'status': new_status})
        return JsonResponse({'error': 'Invalid status'}, status=400)
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)


@login_required
def workspace_files(request, project_id):
    """Workspace file storage"""
    try:
        project = Project.objects.get(id=project_id)
        workspace, _ = Workspace.objects.get_or_create(project=project)
        
        # Check access
        is_member = ProjectMember.objects.filter(project=project, user=request.user).exists()
        is_owner = project.user == request.user
        if not (is_member or is_owner):
            messages.error(request, "Access denied")
            return redirect('feed')
        
        if request.method == 'POST':
            form = WorkspaceFileForm(request.POST, request.FILES)
            if form.is_valid():
                file_obj = form.save(commit=False)
                file_obj.workspace = workspace
                file_obj.uploaded_by = request.user
                file_obj.save()
                messages.success(request, "File uploaded successfully")
                return redirect('workspace_files', project_id=project_id)
        else:
            form = WorkspaceFileForm()
        
        files = workspace.files.all().order_by('-uploaded_at')
        
        return render(request, 'workspace/files.html', {
            'project': project,
            'workspace': workspace,
            'files': files,
            'form': form,
        })
    except Project.DoesNotExist:
        messages.error(request, "Project not found")
        return redirect('feed')


# ==================== ENHANCED FEED VIEWS ====================

@login_required
def enhanced_feed(request):
    """Enhanced feed with smart filters"""
    feed_type = request.GET.get('type', 'all')  # all, following, collaborators, domain, location, stage
    domain_id = request.GET.get('domain')
    location = request.GET.get('location')
    stage = request.GET.get('stage')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    projects = Project.objects.filter(visibility='public').order_by('-created_at')
    
    # Apply filters
    if feed_type == 'following' and request.user.is_authenticated:
        followed_users = request.user.following.values_list('following', flat=True)
        projects = projects.filter(user_id__in=followed_users)
    
    elif feed_type == 'collaborators' and request.user.is_authenticated:
        # Projects where user has collaborated
        collaborated_project_ids = ProjectMember.objects.filter(
            user=request.user
        ).values_list('project_id', flat=True)
        projects = projects.filter(id__in=collaborated_project_ids)
    
    elif feed_type == 'domain' and domain_id:
        projects = projects.filter(domain_id=domain_id)
    
    elif feed_type == 'location' and location:
        projects = projects.filter(
            Q(location__icontains=location) |
            Q(city__icontains=location) |
            Q(state__icontains=location) |
            Q(country__icontains=location)
        )
    
    elif feed_type == 'stage' and stage:
        projects = projects.filter(stage=stage)
    
    # Search
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(problem_statement__icontains=search_query)
        )
    
    # Get AI recommendations if user is authenticated
    ai_recommendations = []
    if request.user.is_authenticated and feed_type == 'all':
        ai_recommendations = get_ai_project_recommendations(request.user, limit=5)
    
    # Pagination
    paginator = Paginator(projects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    domains = Domain.objects.all()
    tags = Tag.objects.all()
    
    context = {
        'projects': page_obj,
        'feed_type': feed_type,
        'domains': domains,
        'tags': tags,
        'ai_recommendations': ai_recommendations,
        'selected_domain': domain_id,
        'selected_location': location,
        'selected_stage': stage,
        'search_query': search_query,
    }
    
    return render(request, 'feed_enhanced.html', context)


# ==================== COLLABORATION VIEWS ====================

@login_required
def request_collaboration_new(request, project_id):
    """New collaboration request with enhanced form"""
    try:
        project = Project.objects.get(id=project_id)
        
        if request.method == 'POST':
            form = CollaborationRequestForm(request.POST)
            if form.is_valid():
                collab_request = form.save(commit=False)
                collab_request.project = project
                collab_request.requester = request.user
                collab_request.save()
                messages.success(request, "Collaboration request sent!")
                return redirect('project_detail', project_id=project_id)
        else:
            form = CollaborationRequestForm()
        
        return render(request, 'collaboration/request.html', {
            'project': project,
            'form': form,
        })
    except Project.DoesNotExist:
        messages.error(request, "Project not found")
        return redirect('feed')


@login_required
@require_POST
def respond_collaboration_new(request, collab_id):
    """Respond to collaboration request and auto-create workspace"""
    try:
        collab = CollaborationRequest.objects.get(id=collab_id)
        
        # Only project owner can respond
        if collab.project.user != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        action = request.POST.get('action')  # 'accept' or 'decline'
        
        if action == 'accept':
            collab.status = 'accepted'
            collab.save()
            
            # Add as project member
            ProjectMember.objects.get_or_create(
                project=collab.project,
                user=collab.requester,
                defaults={'role': collab.role}
            )
            
            # Ensure workspace exists
            workspace, created = Workspace.objects.get_or_create(project=collab.project)
            
            # Add owner as member if not already
            ProjectMember.objects.get_or_create(
                project=collab.project,
                user=collab.project.user,
                defaults={'role': 'owner'}
            )
            
            messages.success(request, f"{collab.requester.name} has been added to the project!")
        else:
            collab.status = 'declined'
            collab.save()
            messages.info(request, "Collaboration request declined")
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'status': collab.status})
        
        return redirect('inbox')
    except CollaborationRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)


# ==================== PROJECT DETAIL VIEW ====================

def project_detail(request, project_id):
    """Detailed project view"""
    try:
        project = Project.objects.get(id=project_id)
        
        # Require login to view project details
        if not request.user.is_authenticated:
            messages.info(request, "Please sign in to view project details")
            return redirect('login')
        
        # Check visibility
        if project.visibility == 'private':
            is_member = ProjectMember.objects.filter(project=project, user=request.user).exists()
            is_owner = project.user == request.user
            if not (is_member or is_owner or request.user.is_staff):
                messages.error(request, "This project is private")
                return redirect('feed')
        
        # Increment view count
        project.views_count += 1
        project.save(update_fields=['views_count'])
        
        # Get related data
        comments = project.comments.all().order_by('-created_at')[:20]
        members = ProjectMember.objects.filter(project=project).select_related('user')
        collaboration_requests = CollaborationRequest.objects.filter(
            project=project, status='pending'
        ).select_related('requester') if project.user == request.user else []
        
        # Check if user can collaborate
        can_collaborate = False
        has_requested = False
        if request.user.is_authenticated:
            can_collaborate = (
                project.user != request.user and
                not ProjectMember.objects.filter(project=project, user=request.user).exists() and
                project.stage in ['idea', 'seeking_collaborators']
            )
            has_requested = CollaborationRequest.objects.filter(
                project=project, requester=request.user
            ).exists()
        
        # Check if liked
        is_liked = False
        if request.user.is_authenticated:
            is_liked = Like.objects.filter(project=project, user=request.user).exists()
        
        # AI collaborator recommendations (for project owner)
        ai_collaborators = []
        if project.user == request.user:
            ai_collaborators = find_collaborator_matches(project, limit=5)
        
        context = {
            'project': project,
            'comments': comments,
            'members': members,
            'collaboration_requests': collaboration_requests,
            'can_collaborate': can_collaborate,
            'has_requested': has_requested,
            'is_liked': is_liked,
            'ai_collaborators': ai_collaborators,
        }
        
        return render(request, 'project/detail.html', context)
    except Project.DoesNotExist:
        messages.error(request, "Project not found")
        return redirect('feed')


@login_required
@require_POST
def like_project(request, project_id):
    """Like/unlike a project"""
    try:
        project = Project.objects.get(id=project_id)
        like, created = Like.objects.get_or_create(project=project, user=request.user)
        
        if not created:
            like.delete()
            project.likes_count = max(0, project.likes_count - 1)
            action = 'unliked'
        else:
            project.likes_count += 1
            action = 'liked'
        
        project.save(update_fields=['likes_count'])
        
        return JsonResponse({
            'success': True,
            'action': action,
            'likes_count': project.likes_count
        })
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)


# ==================== COMMUNITY VIEWS ====================

@login_required
def communities(request):
    """List all communities"""
    community_type = request.GET.get('type')
    domain_id = request.GET.get('domain')
    
    communities_list = Community.objects.all()
    
    if community_type:
        communities_list = communities_list.filter(community_type=community_type)
    if domain_id:
        communities_list = communities_list.filter(domain_id=domain_id)
    
    communities_list = communities_list.annotate(
        member_count=Count('members')
    ).order_by('-member_count', '-created_at')
    
    # User's communities
    user_communities = request.user.communities.all() if request.user.is_authenticated else []
    
    return render(request, 'communities/list.html', {
        'communities': communities_list,
        'user_communities': user_communities,
        'selected_type': community_type,
        'selected_domain': domain_id,
    })


@login_required
def community_detail(request, community_id):
    """Community detail page"""
    try:
        community = Community.objects.get(id=community_id)
        is_member = request.user in community.members.all()
        
        # Get community projects
        projects = Project.objects.filter(
            user__in=community.members.all()
        ).order_by('-created_at')[:20]
        
        return render(request, 'communities/detail.html', {
            'community': community,
            'is_member': is_member,
            'projects': projects,
        })
    except Community.DoesNotExist:
        messages.error(request, "Community not found")
        return redirect('communities')


@login_required
@require_POST
def join_community(request, community_id):
    """Join a community"""
    try:
        community = Community.objects.get(id=community_id)
        community.members.add(request.user)
        messages.success(request, f"You joined {community.name}!")
        return redirect('community_detail', community_id=community_id)
    except Community.DoesNotExist:
        return JsonResponse({'error': 'Community not found'}, status=404)


@login_required
@require_POST
def leave_community(request, community_id):
    """Leave a community"""
    try:
        community = Community.objects.get(id=community_id)
        community.members.remove(request.user)
        messages.info(request, f"You left {community.name}")
        return redirect('community_detail', community_id=community_id)
    except Community.DoesNotExist:
        return JsonResponse({'error': 'Community not found'}, status=404)


@login_required
def create_community(request):
    """Create a new community"""
    if request.method == 'POST':
        form = CommunityForm(request.POST, request.FILES)
        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user
            community.save()
            community.members.add(request.user)  # Creator is automatically a member
            messages.success(request, "Community created successfully!")
            return redirect('community_detail', community_id=community.id)
    else:
        form = CommunityForm()
    
    return render(request, 'communities/create.html', {'form': form})


# ==================== AI PROJECT STARTER KIT ====================

@login_required
def ai_project_starter(request):
    """AI-powered project starter kit generator"""
    if request.method == 'POST':
        project_data = {
            'domain': request.POST.get('domain', ''),
            'skills_required': request.POST.get('skills_required', '').split(',') if request.POST.get('skills_required') else [],
        }
        
        starter_kit = generate_project_starter_kit(project_data)
        
        return JsonResponse({
            'success': True,
            'starter_kit': starter_kit
        })
    
    domains = Domain.objects.all()
    return render(request, 'ai/starter_kit.html', {'domains': domains})


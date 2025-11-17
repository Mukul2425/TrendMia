# myapp/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from myapp import views
from . import views
from myapp.forms import UserLoginForm


urlpatterns = [
    # Basic pages
    path("", views.index, name='home'),
    path("about/", views.about, name='about'),
    path("contact/", views.contact, name='contact'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Feed
    path('feed/', views.feed, name='feed'),
    path('feed/enhanced/', views.enhanced_feed, name='enhanced_feed'),
    
    # Projects
    path('project/create/', views.post_project, name='post_project'),
    path('post_project/', views.post_project, name='post_project_legacy'),  # Legacy URL
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('project/<int:project_id>/like/', views.like_project, name='like_project'),
    path('update_status/<int:post_id>/', views.update_status_view, name='update_status'),
    
    # Workspace
    path('workspace/<int:project_id>/', views.workspace_dashboard, name='workspace_dashboard'),
    path('workspace/<int:project_id>/chat/', views.workspace_chat, name='workspace_chat'),
    path('workspace/<int:project_id>/notes/', views.workspace_notes, name='workspace_notes'),
    path('workspace/<int:project_id>/tasks/', views.workspace_tasks, name='workspace_tasks'),
    path('workspace/<int:project_id>/files/', views.workspace_files, name='workspace_files'),
    path('task/<int:task_id>/update-status/', views.update_task_status, name='update_task_status'),
    
    # Collaboration
    path('collab/request/<int:project_id>/<str:username>/', views.request_collaboration, name='request_collaboration'),
    path('collab/request/<int:project_id>/', views.request_collaboration_new, name='request_collaboration_new'),
    path('collab/respond/<int:collab_id>/', views.respond_collaboration, name='respond_collaboration'),
    path('collab/respond-new/<int:collab_id>/', views.respond_collaboration_new, name='respond_collaboration_new'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.user_profile_view, name='user_profile'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    
    # Social
    path('chat/<str:username>/', views.chat_page, name='chat'),
    path('messages/', views.inbox, name='inbox'),
    path('comment/<int:project_id>/', views.add_comment, name='add_comment'),
    
    # Communities
    path('communities/', views.communities, name='communities'),
    path('communities/create/', views.create_community, name='create_community'),
    path('communities/<int:community_id>/', views.community_detail, name='community_detail'),
    path('communities/<int:community_id>/join/', views.join_community, name='join_community'),
    path('communities/<int:community_id>/leave/', views.leave_community, name='leave_community'),
    
    # AI Features
    path('ai/starter-kit/', views.ai_project_starter, name='ai_project_starter'),
    
    # Trending
    path('trending/', views.trending, name='trending'),
]
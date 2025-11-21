# myapp/ai_utils.py

"""
AI utility functions for TRENDMIA
- Collaborator matching
- Project recommendations
- Project assistant features
"""

from .models import Project, CustomUser, CollaborationRequest, ProjectMember, Domain, Tag
from django.db.models import Q
from collections import Counter
import json


def calculate_skill_similarity(user_skills, required_skills):
    """Calculate similarity between user skills and required skills"""
    if not user_skills or not required_skills:
        return 0.0
    
    user_skills_lower = [skill.lower().strip() for skill in user_skills if skill]
    required_skills_lower = [skill.lower().strip() for skill in required_skills if skill]
    
    if not user_skills_lower or not required_skills_lower:
        return 0.0
    
    # Exact matches
    matches = len(set(user_skills_lower) & set(required_skills_lower))
    
    # Partial matches (substring matching)
    partial_matches = 0
    for req_skill in required_skills_lower:
        for user_skill in user_skills_lower:
            if req_skill in user_skill or user_skill in req_skill:
                partial_matches += 0.5
                break
    
    total_score = matches + partial_matches
    max_possible = len(required_skills_lower)
    
    return min(total_score / max_possible if max_possible > 0 else 0, 1.0)


def get_user_skills_list(user):
    """Extract skills list from user's skills JSON field"""
    if isinstance(user.skills, dict):
        return list(user.skills.keys())
    elif isinstance(user.skills, str):
        try:
            skills_dict = json.loads(user.skills)
            return list(skills_dict.keys())
        except:
            return []
    return []


def find_collaborator_matches(project, limit=10):
    """
    Find best matching collaborators for a project based on:
    - Required skills
    - Location proximity
    - Past project domains
    - User interests
    """
    required_skills = project.skills_required if isinstance(project.skills_required, list) else []
    if not required_skills:
        return []
    
    # Get all users except project owner
    all_users = CustomUser.objects.exclude(id=project.user.id)
    
    # Score each user
    scored_users = []
    for user in all_users:
        score = 0.0
        reasons = []
        
        # Skill matching (weight: 0.5)
        user_skills = get_user_skills_list(user)
        skill_match = calculate_skill_similarity(user_skills, required_skills)
        score += skill_match * 0.5
        if skill_match > 0.3:
            reasons.append(f"Matches {int(skill_match * 100)}% of required skills")
        
        # Location matching (weight: 0.2)
        if project.location and user.location:
            if project.location.lower() in user.location.lower() or user.location.lower() in project.location.lower():
                score += 0.2
                reasons.append("Same location")
        
        # Domain interest matching (weight: 0.2)
        if project.domain:
            user_projects = Project.objects.filter(user=user)
            user_domains = [p.domain for p in user_projects if p.domain]
            if project.domain in user_domains:
                score += 0.2
                reasons.append(f"Experience in {project.domain.name}")
        
        # Activity score (weight: 0.1)
        activity_score = min(user.contribution_streak / 30, 1.0)  # Normalize to 0-1
        score += activity_score * 0.1
        
        if score > 0.2:  # Only include users with meaningful match
            scored_users.append({
                'user': user,
                'score': score,
                'reasons': reasons[:3]  # Top 3 reasons
            })
    
    # Sort by score and return top matches
    scored_users.sort(key=lambda x: x['score'], reverse=True)
    return scored_users[:limit]


def get_ai_project_recommendations(user, limit=10):
    """
    Get AI-powered project recommendations for a user based on:
    - User's skills
    - Past projects
    - Followed users' projects
    - Location
    - Domain interests
    """
    user_skills = get_user_skills_list(user)
    
    # Get projects user hasn't created or already collaborated on
    user_projects = Project.objects.filter(user=user).values_list('id', flat=True)
    collaborated_projects = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
    excluded_ids = list(user_projects) + list(collaborated_projects)
    
    available_projects = Project.objects.exclude(id__in=excluded_ids).filter(
        visibility='public',
        stage__in=['idea', 'seeking_collaborators']
    )
    
    scored_projects = []
    for project in available_projects:
        score = 0.0
        reasons = []
        
        # Skill matching (weight: 0.4)
        required_skills = project.skills_required if isinstance(project.skills_required, list) else []
        if required_skills:
            skill_match = calculate_skill_similarity(user_skills, required_skills)
            score += skill_match * 0.4
            if skill_match > 0.3:
                reasons.append(f"Matches your skills ({int(skill_match * 100)}%)")
        
        # Domain matching (weight: 0.3)
        if project.domain:
            user_domains = [p.domain for p in Project.objects.filter(user=user) if p.domain]
            if project.domain in user_domains:
                score += 0.3
                reasons.append(f"Similar to your {project.domain.name} projects")
        
        # Location matching (weight: 0.2)
        if project.location and user.location:
            if project.location.lower() in user.location.lower() or user.location.lower() in project.location.lower():
                score += 0.2
                reasons.append("Near your location")
        
        # Popularity boost (weight: 0.1)
        popularity = min((project.views_count + project.likes_count) / 100, 1.0)
        score += popularity * 0.1
        
        if score > 0.2:
            scored_projects.append({
                'project': project,
                'score': score,
                'reasons': reasons[:3]
            })
    
    scored_projects.sort(key=lambda x: x['score'], reverse=True)
    return scored_projects[:limit]


def generate_project_starter_kit(project_data):
    """
    Generate a starter kit for a new project including:
    - Suggested milestones
    - Initial task breakdown
    - Recommended tools/tech stack
    - Requirements document outline
    """
    domain = project_data.get('domain', '')
    skills = project_data.get('skills_required', [])
    
    starter_kit = {
        'milestones': [],
        'tasks': [],
        'tech_stack': [],
        'requirements': []
    }
    
    # Generate milestones based on project stage
    if domain:
        if 'AI' in domain or 'Machine Learning' in domain:
            starter_kit['milestones'] = [
                {'title': 'Data Collection & Preprocessing', 'description': 'Gather and clean datasets'},
                {'title': 'Model Development', 'description': 'Build and train ML models'},
                {'title': 'Testing & Validation', 'description': 'Test model performance'},
                {'title': 'Deployment', 'description': 'Deploy model to production'}
            ]
            starter_kit['tech_stack'] = ['Python', 'TensorFlow/PyTorch', 'Pandas', 'NumPy', 'Scikit-learn']
        elif 'Web' in domain:
            starter_kit['milestones'] = [
                {'title': 'Design & Planning', 'description': 'Create wireframes and plan architecture'},
                {'title': 'Frontend Development', 'description': 'Build user interface'},
                {'title': 'Backend Development', 'description': 'Implement server and API'},
                {'title': 'Testing & Deployment', 'description': 'Test and deploy application'}
            ]
            starter_kit['tech_stack'] = ['React/Vue', 'Node.js/Django', 'PostgreSQL/MongoDB']
        else:
            starter_kit['milestones'] = [
                {'title': 'Planning & Research', 'description': 'Research and plan project'},
                {'title': 'Development', 'description': 'Build core features'},
                {'title': 'Testing', 'description': 'Test functionality'},
                {'title': 'Launch', 'description': 'Launch project'}
            ]
    
    # Generate initial tasks
    starter_kit['tasks'] = [
        {'title': 'Set up development environment', 'status': 'todo', 'priority': 'high'},
        {'title': 'Create project repository', 'status': 'todo', 'priority': 'high'},
        {'title': 'Write project documentation', 'status': 'todo', 'priority': 'medium'},
    ]
    
    # Generate requirements outline
    starter_kit['requirements'] = [
        'Project Overview',
        'Functional Requirements',
        'Non-functional Requirements',
        'Technical Specifications',
        'Timeline & Milestones'
    ]
    
    return starter_kit


def suggest_next_steps(workspace):
    """Suggest next steps for a project workspace"""
    project = workspace.project
    tasks = workspace.tasks.all()
    milestones = workspace.milestones.all()
    
    suggestions = []
    
    # Check if project has no tasks
    if tasks.count() == 0:
        suggestions.append({
            'type': 'task',
            'message': 'Create your first task to get started',
            'priority': 'high'
        })
    
    # Check for overdue tasks
    from django.utils import timezone
    overdue_tasks = tasks.filter(due_date__lt=timezone.now(), status__in=['todo', 'in_progress'])
    if overdue_tasks.exists():
        suggestions.append({
            'type': 'overdue',
            'message': f'You have {overdue_tasks.count()} overdue task(s)',
            'priority': 'urgent'
        })
    
    # Check for upcoming milestones
    upcoming_milestones = milestones.filter(completed=False, due_date__isnull=False)
    if upcoming_milestones.exists():
        suggestions.append({
            'type': 'milestone',
            'message': f'You have {upcoming_milestones.count()} upcoming milestone(s)',
            'priority': 'medium'
        })
    
    # Check if project needs more collaborators
    if project.stage == 'seeking_collaborators' and project.members.count() < 3:
        suggestions.append({
            'type': 'collaboration',
            'message': 'Consider inviting more collaborators',
            'priority': 'medium'
        })
    
    return suggestions






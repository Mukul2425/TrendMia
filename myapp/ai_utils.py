# myapp/ai_utils.py

"""
AI utility functions for TRENDMIA
- Collaborator matching
- Project recommendations
- Project assistant features
"""

from .models import Project, CustomUser, CollaborationRequest, ProjectMember, Domain, Tag
from django.db.models import Q, Count
from django.utils import timezone
from collections import Counter
import os
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


def _normalize_text(value):
    return (value or "").strip().lower()


def _tokenize_text(value):
    cleaned = _normalize_text(value)
    if not cleaned:
        return set()
    tokens = [t for t in cleaned.replace(',', ' ').replace('.', ' ').split() if len(t) > 2]
    return set(tokens)


def _token_jaccard_similarity(text_a, text_b):
    tokens_a = _tokenize_text(text_a)
    tokens_b = _tokenize_text(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    if union == 0:
        return 0.0
    return intersection / union


def _cosine_similarity(vec_a, vec_b):
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_gemini_client():
    """Return a configured google-genai client or None."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def _get_embedding(text):
    """Best-effort embedding via Gemini text-embedding-004; returns None when unavailable."""
    if not text:
        return None
    client = _get_gemini_client()
    if not client:
        return None
    try:
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )
        return list(result.embeddings[0].values)
    except Exception:
        return None


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

    project_text = " ".join([
        project.title or "",
        project.description or "",
        project.problem_statement or "",
        " ".join(required_skills),
        project.domain.name if project.domain else "",
    ]).strip()

    project_embedding = _get_embedding(project_text)

    # Get all users except project owner
    all_users = CustomUser.objects.exclude(id=project.user.id)

    # Historical collaboration reliability for each requester
    requester_stats = {
        row['requester_id']: row
        for row in CollaborationRequest.objects.values('requester_id').annotate(
            total=Count('id'),
            accepted=Count('id', filter=Q(status='accepted')),
        )
    }
    
    # Score each user
    scored_users = []
    for user in all_users:
        score = 0.0
        reasons = []

        # Skill matching (weight: 0.35)
        user_skills = get_user_skills_list(user)
        skill_match = calculate_skill_similarity(user_skills, required_skills)
        score += skill_match * 0.35
        if skill_match > 0.3:
            reasons.append(f"Matches {int(skill_match * 100)}% of required skills")

        # Semantic profile-project matching (weight: 0.25)
        user_text = " ".join([
            user.bio or "",
            user.location or "",
            " ".join(user_skills),
            " ".join(Project.objects.filter(user=user).values_list('title', flat=True)[:10]),
            " ".join(Project.objects.filter(user=user).values_list('description', flat=True)[:10]),
        ]).strip()

        semantic_score = _token_jaccard_similarity(project_text, user_text)
        if project_embedding:
            user_embedding = _get_embedding(user_text)
            if user_embedding:
                semantic_score = max(semantic_score, _cosine_similarity(project_embedding, user_embedding))
        score += semantic_score * 0.25
        if semantic_score > 0.2:
            reasons.append("Strong semantic match with project context")

        # Location matching (weight: 0.15)
        if project.location and user.location:
            if project.location.lower() in user.location.lower() or user.location.lower() in project.location.lower():
                score += 0.15
                reasons.append("Same location")

        # Domain interest matching (weight: 0.15)
        if project.domain:
            user_projects = Project.objects.filter(user=user)
            user_domains = [p.domain for p in user_projects if p.domain]
            if project.domain in user_domains:
                score += 0.15
                reasons.append(f"Experience in {project.domain.name}")

        # Collaboration reliability (weight: 0.05)
        stat = requester_stats.get(user.id)
        if stat and stat.get('total'):
            acceptance_rate = (stat.get('accepted', 0) / stat['total'])
            score += acceptance_rate * 0.05
            if acceptance_rate >= 0.5:
                reasons.append("Historically high acceptance in collaborations")

        # Activity score (weight: 0.05)
        activity_score = min(user.contribution_streak / 30, 1.0)  # Normalize to 0-1
        score += activity_score * 0.05

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


def get_hybrid_feed_projects(user, base_queryset=None, limit=60):
    """
    Two-stage feed ranking:
    1) Candidate retrieval from follows, domain affinity, collaboration context, and trending.
    2) Deterministic reranking with affinity, semantic overlap, recency, and popularity.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        projects = (base_queryset or Project.objects.filter(visibility='public').order_by('-created_at'))[:limit]
        return list(projects)

    base_qs = base_queryset or Project.objects.filter(visibility='public').order_by('-created_at')
    followed_user_ids = set(user.following.values_list('following_id', flat=True))
    user_projects = Project.objects.filter(user=user).prefetch_related('tags')
    user_project_ids = set(user_projects.values_list('id', flat=True))
    collaborated_project_ids = set(ProjectMember.objects.filter(user=user).values_list('project_id', flat=True))

    user_domain_ids = set(user_projects.exclude(domain__isnull=True).values_list('domain_id', flat=True))
    user_tags = set()
    for p in user_projects:
        user_tags.update([t.name.lower() for t in p.tags.all()])

    # Candidate retrieval buckets
    candidates_following = base_qs.filter(user_id__in=followed_user_ids)[:120]
    candidates_domain = base_qs.filter(domain_id__in=user_domain_ids)[:120] if user_domain_ids else base_qs.none()
    candidates_collab_stage = base_qs.filter(stage='seeking_collaborators')[:120]
    candidates_trending = base_qs.order_by('-likes_count', '-views_count')[:120]
    candidates_recent = base_qs[:120]

    candidate_map = {}
    for bucket in [candidates_following, candidates_domain, candidates_collab_stage, candidates_trending, candidates_recent]:
        for project in bucket:
            if project.id in user_project_ids:
                continue
            candidate_map[project.id] = project

    candidates = list(candidate_map.values())
    if not candidates:
        return []

    user_profile_text = " ".join([
        user.bio or "",
        user.location or "",
        " ".join(sorted(user_tags)),
        " ".join(user_projects.values_list('title', flat=True)[:10]),
    ]).strip()

    scored = []
    now = timezone.now()
    for project in candidates:
        project_tags = set(tag.name.lower() for tag in project.tags.all())
        project_skills = set(s.lower() for s in (project.skills_required or []) if isinstance(s, str))
        tag_overlap = len(user_tags & (project_tags | project_skills))
        union_size = len(user_tags | project_tags | project_skills) or 1
        tag_score = tag_overlap / union_size

        project_text = " ".join([
            project.title or "",
            project.description or "",
            project.problem_statement or "",
            " ".join(project.skills_required or []),
        ]).strip()
        semantic_score = _token_jaccard_similarity(user_profile_text, project_text)

        age_days = max((now - project.created_at).days, 0)
        recency_score = 1.0 / (1.0 + (age_days / 7.0))
        popularity_score = min((project.likes_count * 2 + project.views_count) / 200.0, 1.0)

        follow_score = 1.0 if project.user_id in followed_user_ids else 0.0
        domain_score = 1.0 if project.domain_id and project.domain_id in user_domain_ids else 0.0
        collab_context_score = 1.0 if project.id in collaborated_project_ids else 0.0

        final_score = (
            follow_score * 0.30 +
            tag_score * 0.24 +
            domain_score * 0.12 +
            semantic_score * 0.16 +
            recency_score * 0.12 +
            popularity_score * 0.04 +
            collab_context_score * 0.02
        )

        reasons = []
        if follow_score:
            reasons.append("From creators you follow")
        if tag_score > 0.15:
            reasons.append("Skill/tag overlap")
        if domain_score:
            reasons.append("Matches your domain history")
        if semantic_score > 0.15:
            reasons.append("Text relevance to your profile")
        if not reasons:
            reasons.append("High recent engagement")

        project.ai_feed_score = round(final_score, 4)
        project.ai_feed_reasons = reasons[:3]
        scored.append(project)

    scored.sort(key=lambda p: p.ai_feed_score, reverse=True)
    return scored[:limit]


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


def _heuristic_copilot_output(idea, domain, skills_required, constraints):
    """Deterministic fallback when no LLM key is configured."""
    skills = [s.strip() for s in skills_required if s and s.strip()]
    constraints_text = constraints.strip() if constraints else "No explicit constraints provided"

    domain_label = domain or "General"
    title = f"{domain_label} Project: {idea[:60].strip()}" if idea else f"{domain_label} Project"
    title = title[:140]

    milestones = [
        {
            "title": "Problem framing and success criteria",
            "description": "Define the target user, key pain point, and measurable success metrics.",
            "duration_weeks": 1,
        },
        {
            "title": "MVP architecture and implementation",
            "description": "Build a minimal version that validates the core hypothesis with real usage.",
            "duration_weeks": 3,
        },
        {
            "title": "Validation and iteration",
            "description": "Collect feedback, benchmark outcomes, and iterate on weak areas.",
            "duration_weeks": 2,
        },
    ]

    risks = [
        {
            "risk": "Scope expansion",
            "severity": "medium",
            "mitigation": "Freeze MVP scope and prioritize by user impact.",
        },
        {
            "risk": "Insufficient user validation",
            "severity": "high",
            "mitigation": "Run regular user interviews and instrument usage analytics.",
        },
        {
            "risk": "Team execution bottlenecks",
            "severity": "medium",
            "mitigation": "Assign clear ownership and weekly delivery checkpoints.",
        },
    ]

    collaboration_ask = {
        "summary": "Looking for contributors who can ship quickly and validate with users.",
        "roles": ["Developer", "Designer", "Domain Specialist"],
    }

    return {
        "title": title,
        "one_liner": f"Build a focused {domain_label.lower()} solution that solves: {idea[:180].strip()}" if idea else "Build a focused solution with clear user value.",
        "problem_statement": idea.strip() if idea else "Problem statement not provided.",
        "proposed_solution": "Develop an MVP with clear user journey, telemetry, and feedback loops to iterate fast.",
        "skills_required": skills,
        "recommended_stack": [
            "Django",
            "PostgreSQL",
            "REST API",
            "Bootstrap/Frontend framework",
        ],
        "milestones": milestones,
        "risks": risks,
        "acceptance_criteria": [
            "Users can complete the primary workflow end-to-end.",
            "At least one measurable outcome improves versus baseline.",
            "Core reliability and performance checks pass.",
        ],
        "collaboration_ask": collaboration_ask,
        "constraints": constraints_text,
        "source": "heuristic",
    }


def _extract_json(raw):
    """Strip markdown code fences if present and parse JSON."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(raw)


def generate_project_copilot_brief(idea, domain="", skills_required=None, constraints=""):
    """
    Generate a structured project brief from a rough idea.
    Uses Gemini 2.5 Flash when GEMINI_API_KEY is available, otherwise deterministic fallback.
    """
    skills_required = skills_required or []
    cleaned_skills = [s.strip() for s in skills_required if s and s.strip()]

    client = _get_gemini_client()
    if not client:
        return _heuristic_copilot_output(idea, domain, cleaned_skills, constraints)

    try:
        from google.genai import types

        prompt = f"""You are an expert startup and product advisor.
Convert the following rough project idea into a structured JSON object.

Input:
- Idea: {idea}
- Domain: {domain}
- Skills provided by user: {cleaned_skills}
- Constraints: {constraints}

Return ONLY valid JSON (no markdown fences) with this exact top-level schema:
{{
  "title": string,
  "one_liner": string,
  "problem_statement": string,
  "proposed_solution": string,
  "skills_required": string[],
  "recommended_stack": string[],
  "milestones": [{{"title": string, "description": string, "duration_weeks": number}}],
  "risks": [{{"risk": string, "severity": "low"|"medium"|"high", "mitigation": string}}],
  "acceptance_criteria": string[],
  "collaboration_ask": {{"summary": string, "roles": string[]}},
  "constraints": string
}}

Keep output concise, practical, and implementation-oriented."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1800,
            ),
        )

        parsed = _extract_json(response.text)
        parsed["source"] = "gemini"
        return parsed
    except Exception:
        return _heuristic_copilot_output(idea, domain, cleaned_skills, constraints)


# ==================== WORKSPACE AI PM ====================

def _build_workspace_context(workspace):
    """Collect raw workspace signals into a plain dict for PM report."""
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    window_start = now - timedelta(hours=48)

    tasks = list(workspace.tasks.select_related('assigned_to').all())
    milestones = list(workspace.milestones.all())
    recent_messages = list(
        workspace.chat_messages.filter(timestamp__gte=window_start)
        .select_related('sender')
        .order_by('-timestamp')[:60]
    )
    members = list(workspace.project.members.select_related('user').all())

    done       = [t for t in tasks if t.status == 'done']
    in_progress = [t for t in tasks if t.status == 'in_progress']
    todo       = [t for t in tasks if t.status == 'todo']
    overdue    = [
        t for t in tasks
        if t.status in ('todo', 'in_progress') and t.due_date and t.due_date < now
    ]
    stalled    = [
        t for t in in_progress
        if (now - t.updated_at).days >= 3
    ]

    upcoming_milestones = [
        m for m in milestones
        if not m.completed and m.due_date and m.due_date >= now
    ]
    overdue_milestones = [
        m for m in milestones
        if not m.completed and m.due_date and m.due_date < now
    ]

    return {
        'project_title': workspace.project.title,
        'members': [{'name': m.user.name, 'role': m.role, 'id': m.user.id} for m in members],
        'tasks': {
            'done': [{'title': t.title, 'assigned_to': t.assigned_to.name if t.assigned_to else None} for t in done],
            'in_progress': [{'title': t.title, 'assigned_to': t.assigned_to.name if t.assigned_to else None} for t in in_progress],
            'todo': [{'title': t.title, 'assigned_to': t.assigned_to.name if t.assigned_to else None} for t in todo],
            'overdue': [{'title': t.title, 'assigned_to': t.assigned_to.name if t.assigned_to else None, 'due_date': str(t.due_date.date())} for t in overdue],
            'stalled': [{'title': t.title, 'assigned_to': t.assigned_to.name if t.assigned_to else None} for t in stalled],
        },
        'milestones': {
            'upcoming': [{'title': m.title, 'due': str(m.due_date.date())} for m in upcoming_milestones],
            'overdue': [{'title': m.title, 'due': str(m.due_date.date())} for m in overdue_milestones],
        },
        'recent_messages': [
            {'sender': msg.sender.name, 'text': msg.message[:200]} for msg in recent_messages[:20]
        ],
    }


def _heuristic_pm_report(ctx):
    """Build a structured PM standup without LLM."""
    blockers = []
    if ctx['tasks']['overdue']:
        for t in ctx['tasks']['overdue']:
            owner = t['assigned_to'] or 'unassigned'
            blockers.append(f"Overdue: \"{t['title']}\" (owner: {owner}, due: {t['due_date']})")
    if ctx['tasks']['stalled']:
        for t in ctx['tasks']['stalled']:
            owner = t['assigned_to'] or 'unassigned'
            blockers.append(f"Stalled >3 days: \"{t['title']}\" (owner: {owner})")
    if ctx['milestones']['overdue']:
        for m in ctx['milestones']['overdue']:
            blockers.append(f"Milestone overdue: \"{m['title']}\" (was due {m['due']})")

    next_actions = []
    for t in ctx['tasks']['todo'][:3]:
        owner = t['assigned_to'] or 'unassigned'
        next_actions.append(f"Start: \"{t['title']}\" — owner: {owner}")
    if ctx['tasks']['stalled']:
        next_actions.append("Review stalled in-progress tasks and reassign if needed")
    if len(ctx['tasks']['in_progress']) > 4:
        next_actions.append("Too many items in progress — consider limiting WIP to 3")

    accomplishments = [f"\"{t['title']}\"" for t in ctx['tasks']['done'][:5]]

    member_names = ", ".join(m['name'] for m in ctx['members']) or "No members yet"
    chat_count = len(ctx['recent_messages'])

    summary = (
        f"Team ({member_names}) has {len(ctx['tasks']['done'])} done, "
        f"{len(ctx['tasks']['in_progress'])} in progress, "
        f"{len(ctx['tasks']['todo'])} to-do tasks. "
        f"{len(blockers)} blocker(s) detected. "
        f"{chat_count} messages in the last 48 h."
    )

    return {
        'project': ctx['project_title'],
        'summary': summary,
        'accomplishments': accomplishments,
        'in_progress': [
            f"\"{t['title']}\" — {t['assigned_to'] or 'unassigned'}"
            for t in ctx['tasks']['in_progress'][:5]
        ],
        'blockers': blockers,
        'next_actions': next_actions,
        'upcoming_milestones': [f"\"{m['title']}\" due {m['due']}" for m in ctx['milestones']['upcoming'][:3]],
        'suggested_focus': (
            blockers[0] if blockers else
            (next_actions[0] if next_actions else "All clear — great momentum!")
        ),
        'source': 'heuristic',
    }


def generate_workspace_pm_report(workspace):
    """
    Generate an AI PM standup report for a workspace.
    Uses Gemini 2.5 Flash when GEMINI_API_KEY is set, deterministic fallback otherwise.
    """
    ctx = _build_workspace_context(workspace)

    client = _get_gemini_client()
    if not client:
        return _heuristic_pm_report(ctx)

    try:
        from google.genai import types

        ctx_json = json.dumps(ctx, default=str, indent=2)
        prompt = f"""You are an expert AI project manager assistant.
Given the following workspace context for the project "{ctx['project_title']}",
generate a daily standup report as a JSON object.

Context:
{ctx_json}

Return ONLY valid JSON (no markdown fences) with this schema:
{{
  "project": string,
  "summary": string,
  "accomplishments": string[],
  "in_progress": string[],
  "blockers": string[],
  "next_actions": string[],
  "upcoming_milestones": string[],
  "suggested_focus": string,
  "source": "gemini"
}}

Be concrete, concise, and name owners where available."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1200,
            ),
        )

        parsed = _extract_json(response.text)
        parsed["source"] = "gemini"
        return parsed
    except Exception:
        return _heuristic_pm_report(ctx)




# TRENDMIA

A social collaboration platform for builders, researchers, and innovators.

TRENDMIA combines project publishing, collaborator discovery, workspaces, communities, and AI-assisted flows in one Django application.

## What Is Already Implemented

### Core product features
- Custom user profiles (skills, location, bio, reputation, streaks)
- Project posting and discovery
- Collaboration requests and accept/decline workflows
- Workspace modules for team execution:
  - dashboard
  - chat
  - notes
  - tasks
  - files
  - milestones
- Social features (follow, likes, comments, inbox/chat)
- Communities and community participation
- Enhanced feed filters (domain, location, stage, following, collaborators)

### AI features already present in this codebase
- Collaborator matching (skills + domain + location + activity weighting)
- AI project recommendations for users
- Starter kit generation for new projects (milestones, tasks, tech stack, requirements)
- Workspace next-step suggestions (overdue tasks, milestones, collaboration prompts)

## Tech Stack

- Backend: Django 5, Django Channels, Django REST Framework
- Database: PostgreSQL (configured in settings)
- Async/background-ready: Celery + Redis dependencies included
- AI integration dependency: OpenAI Python SDK
- Optional analytics dependencies: pandas, matplotlib, seaborn, ipywidgets

## Quick Start

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

Core only:

```bash
pip install -r requirements-core.txt
```

Full (includes analytics packages):

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Update .env values for your machine and PostgreSQL instance:
- DJANGO_SECRET_KEY
- DJANGO_DEBUG
- DJANGO_ALLOWED_HOSTS
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_HOST
- DB_PORT

### 4. Create database and run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed domains and tags (optional but recommended)

```bash
python manage.py seed_data
```

### 6. Create an admin user

```bash
python manage.py createsuperuser
```

### 7. Start development server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000

## Primary App Routes

- Home: /
- Feed: /feed/
- Enhanced feed: /feed/enhanced/
- Post project: /project/create/
- Workspace: /workspace/<project_id>/
- Communities: /communities/
- AI starter kit: /ai/starter-kit/

## AI Roadmap: High-Depth Features You Can Add

The list below is prioritized for practical impact and technical depth.

### 1. LLM Project Copilot (creation + refinement)
- What it does:
  - Converts rough user idea into a structured project brief
  - Suggests problem framing, milestones, risks, and acceptance criteria
- AI depth:
  - Prompt-chaining + schema-constrained output (JSON)
  - Optional retrieval from successful past projects
- Why it matters:
  - Improves project quality before publishing

### 2. Semantic Collaborator Matching 2.0
- What it does:
  - Uses semantic skill embeddings and portfolio text embeddings
  - Ranks collaborators by capability fit, reliability, and availability
- AI depth:
  - Embedding model + hybrid scoring (semantic + graph + behavioral features)
  - Learning-to-rank pipeline from accepted/declined collaboration outcomes
- Why it matters:
  - Better match quality than keyword overlap

### 3. Personalized Feed with Hybrid Retrieval + Re-ranking
- What it does:
  - Candidate retrieval from follows/domains/recent trends
  - LLM or smaller ranker re-orders feed by relevance and novelty
- AI depth:
  - Two-stage recommender system
  - Contextual bandits to optimize for long-term engagement quality
- Why it matters:
  - Increases discovery quality and reduces feed noise

### 4. Workspace AI PM (Project Manager Agent)
- What it does:
  - Daily standup summaries from chats/tasks
  - Auto-generates next actions, blockers, and owner suggestions
- AI depth:
  - Multi-source summarization (chat + tasks + milestones)
  - Agentic action suggestions with permission-gated automation
- Why it matters:
  - Keeps teams aligned without manual coordination overhead

### 5. Proposal/Grant/Investor Draft Assistant
- What it does:
  - Generates grant applications, pitch summaries, and technical narratives
  - Adapts tone and structure for different audiences
- AI depth:
  - Template-conditioned generation + retrieval from project facts
  - Iterative critique-and-revise loop using rubric scoring
- Why it matters:
  - Helps teams convert projects into opportunities

### 6. AI Mentor Feedback for Projects
- What it does:
  - Produces expert-style feedback on feasibility, product risk, and execution plan
- AI depth:
  - Domain-specific rubrics + self-consistency checking
  - Evidence-linked feedback (points to project details that triggered advice)
- Why it matters:
  - Accelerates learning quality for early-stage builders

### 7. Knowledge Graph + Team Memory (RAG)
- What it does:
  - Builds a project/team knowledge graph from docs, tasks, and chat
  - Enables ask-anything queries with source-grounded answers
- AI depth:
  - Retrieval-augmented generation with citation grounding
  - Graph-enhanced retrieval (entities: skills, tools, tasks, milestones)
- Why it matters:
  - Preserves context and avoids repeating decisions

### 8. Predictive Project Health and Risk Alerts
- What it does:
  - Predicts completion risk, delay probability, and collaboration churn
  - Alerts teams before failure states happen
- AI depth:
  - Time-series and tabular modeling on activity signals
  - Explainable feature attributions for trust
- Why it matters:
  - Moves from reactive management to proactive intervention

### 9. AI-Powered Community Moderation and Safety
- What it does:
  - Detects spam, abuse, toxic behavior, and suspicious collaboration patterns
- AI depth:
  - Multi-label safety classification + policy thresholds
  - Human-in-the-loop moderation queue with confidence scores
- Why it matters:
  - Protects platform quality as usage grows

### 10. Multimodal Project Understanding
- What it does:
  - Understands screenshots, design mockups, pitch decks, and code snippets
  - Improves recommendations and AI mentoring using richer context
- AI depth:
  - Vision-language models + document parsing pipelines
- Why it matters:
  - Project understanding becomes much closer to real-world submissions

## Suggested Implementation Order

### Phase 1 (fast ROI)
- LLM Project Copilot
- Semantic Collaborator Matching 2.0
- Workspace AI PM summaries

### Phase 2 (platform intelligence)
- Hybrid feed retrieval + re-ranking
- Knowledge Graph + Team Memory (RAG)
- AI Mentor Feedback

### Phase 3 (advanced and scale)
- Predictive project health/risk
- Moderation/safety intelligence
- Multimodal project understanding

## Notes

- The app is configured for PostgreSQL in settings.
- Keep secrets in .env and never commit real keys.
- If you plan to use OpenAI or other model providers, store API keys in environment variables and call them from server-side code only.

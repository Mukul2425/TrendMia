# TRENDMIA - Setup Guide

## 🚀 Project Overview

TRENDMIA is a comprehensive social network platform for builders, researchers, and innovators. It combines project collaboration, workspace management, AI-powered features, and community building.

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)
- Virtual environment (recommended)

## 🔧 Installation Steps

### 1. Database Setup

First, create a PostgreSQL database:

```sql
CREATE DATABASE trendmia_db;
CREATE USER trendmia_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trendmia_db TO trendmia_user;
```

### 2. Environment Variables

Create a `.env` file in the `trendmia/` directory:

```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

DB_NAME=trendmia_db
DB_USER=trendmia_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 3. Install Dependencies

```bash
cd trendmia
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Load Initial Data (Optional)

Create some initial domains and tags:

```bash
python manage.py shell
```

Then in the shell:

```python
from myapp.models import Domain, Tag

# Create domains
domains = ['AI', 'Robotics', 'Web Development', 'Mobile Development', 
           'Cybersecurity', 'Data Science', 'Biotech', 'IoT', 
           'Blockchain', 'AR/VR']

for domain_name in domains:
    Domain.objects.get_or_create(name=domain_name)

# Create some tags
tags = ['Machine Learning', 'Deep Learning', 'React', 'Django', 
        'Python', 'JavaScript', 'Mobile App', 'API', 'Database']

for tag_name in tags:
    Tag.objects.get_or_create(name=tag_name)
```

### 7. Collect Static Files

```bash
python manage.py collectstatic
```

### 8. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## 📁 Project Structure

```
trendmia/
├── myapp/
│   ├── models.py          # All database models
│   ├── views.py           # All view functions
│   ├── forms.py           # Django forms
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin configuration
│   ├── ai_utils.py        # AI helper functions
│   └── migrations/        # Database migrations
├── myproject/
│   ├── settings.py        # Django settings
│   └── urls.py            # Main URL configuration
├── templates/             # HTML templates
├── static/                # Static files (CSS, JS, images)
├── media/                 # User uploads
└── requirements.txt       # Python dependencies
```

## 🎯 Key Features Implemented

### ✅ Core Features

1. **User Management**
   - Custom user model with skills, location, bio
   - Profile pages with project portfolios
   - Follow/unfollow system
   - Contribution streak tracking

2. **Project System**
   - Create projects with rich metadata
   - Domain and tag categorization
   - Project stages (idea, seeking collaborators, in progress, completed)
   - Visibility settings (public, private, unlisted)
   - Like and comment system

3. **Workspace System** (Auto-created when collaborators join)
   - Dashboard with project overview
   - Team chat room
   - Collaborative notes
   - Kanban task board
   - File storage
   - Milestones tracking

4. **Collaboration System**
   - Request to collaborate with skills and role
   - Accept/decline collaboration requests
   - Auto-add members to workspace
   - Role-based access (owner, developer, researcher, designer, mentor)

5. **Smart Feed**
   - Multiple feed types (all, following, collaborators, domain, location, stage)
   - Advanced filtering
   - AI-powered recommendations
   - Search functionality

6. **AI Features**
   - Collaborator matching based on skills, location, interests
   - Project recommendations
   - Project starter kit generator
   - Next steps suggestions

7. **Communities**
   - Create and join communities
   - Community types (college, tech club, research group, etc.)
   - Community projects feed

8. **Gamification** (Models ready, logic to be implemented)
   - Badge system
   - Reputation points
   - Contribution streaks

## 🔄 Next Steps

### 1. Create Templates

You need to create HTML templates for all the views. Key templates needed:

- `templates/base.html` - Base template with navigation
- `templates/feed_enhanced.html` - Enhanced feed page
- `templates/project/detail.html` - Project detail page
- `templates/workspace/dashboard.html` - Workspace dashboard
- `templates/workspace/chat.html` - Workspace chat
- `templates/workspace/notes.html` - Workspace notes
- `templates/workspace/tasks.html` - Task board (Kanban)
- `templates/workspace/files.html` - File storage
- `templates/communities/list.html` - Communities list
- `templates/communities/detail.html` - Community detail
- `templates/collaboration/request.html` - Collaboration request form
- `templates/ai/starter_kit.html` - AI starter kit

### 2. Static Files

Create modern CSS and JavaScript files:
- Responsive design
- Modern UI components
- Interactive elements
- Real-time chat (WebSocket integration)

### 3. Additional Features to Implement

- Real-time notifications
- Email notifications
- Advanced search
- Project templates
- Badge awarding logic
- Analytics dashboard
- Export/import functionality

### 4. Production Deployment

- Set `DEBUG = False`
- Configure proper `ALLOWED_HOSTS`
- Set up HTTPS
- Configure static file serving
- Set up media file storage (S3, etc.)
- Set up Celery for background tasks
- Set up Redis for caching
- Configure email backend

## 🐛 Troubleshooting

### Database Connection Issues

If you get database connection errors:
1. Check PostgreSQL is running
2. Verify database credentials in `.env`
3. Ensure database exists
4. Check user permissions

### Migration Issues

If migrations fail:
```bash
python manage.py makemigrations --empty myapp
python manage.py migrate --fake
```

### Static Files Not Loading

```bash
python manage.py collectstatic --noinput
```

## 📚 API Endpoints

All views are currently function-based. For API access, consider adding Django REST Framework views.

## 🔐 Security Notes

- Never commit `.env` file
- Use strong `SECRET_KEY` in production
- Enable HTTPS in production
- Configure CORS properly
- Validate all user inputs
- Use CSRF protection (already enabled)

## 📞 Support

For issues or questions, check the code comments or Django documentation.

## 🎨 UI/UX Recommendations

For a modern social media-like UI, consider:
- Tailwind CSS or Bootstrap 5
- React/Vue.js for interactive components
- WebSocket for real-time features
- Progressive Web App (PWA) capabilities
- Dark mode support
- Mobile-first responsive design






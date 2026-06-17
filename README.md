# Youth of Nepal in Canada (YONC)

A comprehensive community platform built with Django that connects Nepali youth across Canada with verified experts in various fields including accounting, IT, legal services, counselling, sports, culture, and emergency contacts.

## Features

### Three-Tier User System
- **Admin**: Full platform control with analytics dashboard
- **Expert**: Verified professionals offering services
- **End User**: Community members seeking help

### Core Functionality
- **Expert Directory**: Browse experts by province, category, or search
- **Expert Profiles**: Detailed profiles with bio, experience, specialties, contact info
- **Approval Workflow**: Expert applications reviewed and approved by admins
- **Real-time Messaging**: One-to-one chat between users and experts
- **Admin Dashboard**: Analytics, user management, application reviews
- **Province Filtering**: All 13 Canadian provinces and territories supported
- **Service Categories**: 13 categories covering all community needs

### Service Categories
1. Accounting & Tax
2. IT & Technology
3. Legal Services
4. Counselling & Mental Health
5. Sports & Recreation
6. Culture & Arts
7. Education & Career
8. Healthcare & Wellness
9. Real Estate & Housing
10. Transportation & Driving
11. Community & Social
12. Emergency Contacts
13. Business & Entrepreneurship

## Tech Stack

- **Backend**: Django 4.2+
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Database**: SQLite (default), easily switchable to PostgreSQL/MySQL
- **Styling**: Tailwind CSS CDN
- **Icons**: Font Awesome 6
- **Charts**: Chart.js

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

1. Clone or download the project:
```bash
cd youth_of_nepal_canada
```

2. Create virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Seed sample data:
```bash
python seed_data.py
```

6. Run development server:
```bash
python manage.py runserver
```

7. Open browser and go to: `http://127.0.0.1:8000/`

### Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Expert | rajesh_sharma | demo123 |
| User | (register new) | - |

## Project Structure

```
youth_of_nepal_canada/
├── accounts/          # User authentication & profiles
├── services/          # Service category management
├── experts/           # Expert profiles & applications
├── messaging/         # One-to-one chat system
├── dashboard/         # Admin dashboard & analytics
├── static/            # CSS, JS, images
├── templates/         # HTML templates
├── manage.py          # Django management
├── seed_data.py       # Database seeding
└── requirements.txt   # Python dependencies
```

## Key URLs

| URL | Description |
|-----|-------------|
| `/` | Home page with province selector |
| `/accounts/login/` | User login |
| `/accounts/register/` | User registration |
| `/accounts/profile/` | User profile |
| `/experts/` | Expert directory with filters |
| `/experts/<id>/` | Expert detail page |
| `/experts/apply/` | Apply to become expert |
| `/messages/` | Message inbox |
| `/messages/chat/<id>/` | Chat with user |
| `/services/` | Service categories |
| `/dashboard/` | Admin dashboard |

## Customization

### Adding New Service Categories
Use the Django admin panel at `/admin/` or create via shell:
```python
from services.models import ServiceCategory
ServiceCategory.objects.create(
    name='New Category',
    slug='new-category',
    description='Description here',
    icon_class='fa-solid fa-icon',
    color='#2563EB'
)
```

### Switching Database
Edit `settings.py` DATABASES configuration:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'yonc_db',
        'USER': 'dbuser',
        'PASSWORD': 'dbpass',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Production Deployment

1. Set `DEBUG = False` in settings.py
2. Set a strong `SECRET_KEY`
3. Configure allowed hosts
4. Run `python manage.py collectstatic`
5. Use a production WSGI server (Gunicorn, uWSGI)
6. Configure a reverse proxy (Nginx, Apache)

## License

This project is built for the Nepali community in Canada.

## Support

For questions or support, contact: info@yonc.ca

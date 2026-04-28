# Hima Informatika - Web Application

A modern, feature-rich web application for a university Informatics Student Association (Himpunan Mahasiswa Informatika). Built with Flask (Python) and Tailwind CSS.

## Features

### Admin Dashboard
- **Statistics Overview**: Real-time metrics for members, events, announcements, and projects
- **Interactive Charts**: Monthly growth trends and member distribution visualizations (Chart.js)
- **Quick Actions**: Streamlined access to create members, events, announcements
- **Activity Feed**: Recent events and announcements at a glance
- **Alert System**: Notifications for pending registrations

### Member Management
- Full CRUD operations for member profiles
- Search and filter by name, NIM, or study program
- Member detail pages with registration history
- Toggle active/inactive status
- Import/Export capabilities (CSV)

### Event Management
- Create, edit, and delete events
- Event categories: Workshop, Seminar, Hackathon, Talkshow, Project
- Date/time scheduling with registration deadlines
- Featured events and draft/publish workflow
- Image upload support
- Location and online meeting link management

### Announcement/News Management
- Content management system for news and announcements
- Rich text content with categories
- Featured announcement support
- Draft/publish workflow
- Automatic excerpt generation

### Project Showcase
- Display student projects and portfolios
- Technology tag system
- GitHub and demo link integration
- Featured project highlighting

### Public-Facing Pages
- **Homepage**: Hero section with gradient backgrounds, upcoming events, announcements, featured projects
- **Events**: Filterable listing of all published events
- **News**: Blog-style announcement listings
- **Projects**: Portfolio grid with tech stack badges
- **About**: Organizational info, vision/mission, statistics
- **Contact**: Contact form with company information

## Tech Stack

- **Backend**: Python 3.9+, Flask 3.0
- **Database**: SQLAlchemy ORM (SQLite development, PostgreSQL production)
- **Frontend**: HTML5, Tailwind CSS, Chart.js
- **Authentication**: Flask-Login with password hashing (Werkzeug)
- **Templates**: Jinja2 with base layout

## Installation

1. **Clone the repository**
```bash
cd "web hima informatika"
```

2. **Create virtual environment**
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
copy .env.example .env
```
Edit `.env` and change the `SECRET_KEY` for production.

5. **Initialize database**
```bash
python init_db.py
```
This creates all database tables and adds a default admin user:
- Username: `admin`
- Password: `admin123` ⚠️ *Change after first login*

6. **Run the development server**
```bash
python run.py
```
or
```bash
flask run
```

The application will be available at **http://localhost:5000**

## Project Structure

```
web hima informatika/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication routes
│   │   ├── admin.py         # Admin dashboard routes
│   │   └── main.py          # Public routes
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css    # Custom styles
│   │   └── js/              # Custom JavaScript
│   └── templates/
│       ├── base.html        # Base template
│       ├── index.html       # Homepage
│       ├── login.html       # Login page
│       ├── events.html      # Events listing
│       ├── news.html        # News listing
│       ├── projects.html    # Projects listing
│       ├── about.html       # About page
│       ├── contact.html     # Contact page
│       └── admin/
│           ├── dashboard.html
│           ├── members.html
│           ├── member_detail.html
│           ├── events.html
│           ├── event_form.html
│           ├── announcements.html
│           ├── announcement_form.html
│           └── projects.html
├── config.py                # Configuration
├── run.py                   # Application entry point
├── init_db.py              # Database initialization
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md
```

## Database Models

### User
- Authentication fields (username, email, password)
- Role-based access: `admin`, `struct`, `member`
- Linked to Member profile (one-to-one)

### Member
- Extended profile (NIM, phone, address, program)
- Academic info (semester, study_program)
- Skills and interests (JSON)
- Event registration history

### Event
- Full event details (title, description, dates)
- Category labeling and featured status
- Location/online link
- Registration management

### Announcement
- News and announcements
- Categories: news, announcement, article
- Author attribution
- Publish scheduling

### Project
- Student project portfolios
- Technology stack tracking
- External links (GitHub, demo)
- Team member associations

### EventRegistration
- Tracks member signups for events
- Attendance marking
- Unique constraint prevents duplicate registrations

## Admin Access

After running `init_db.py`:

| Field | Value |
|-------|-------|
| URL | http://localhost:5000/admin/login |
| Username | admin |
| Password | admin123 |

**Important**: Change the default password immediately after first login.

## Customization

### Brand Colors

Edit `app/templates/base.html` Tailwind config:

```javascript
colors: {
    primary: { ... },   // Blue (#3b82f6)
    secondary: { ... }, // Green (#22c55e)
    accent: { ... }     // Orange (#f97316)
}
```

### Adding New Event Categories

1. Update the Event model `category` field enum
2. Add options in admin form templates
3. Filter dropdowns auto-populate from database

### Upload Configuration

File uploads are stored in `app/static/uploads/`. Default allowed extensions: png, jpg, jpeg, gif, pdf, doc, docx. Max size: 16MB.

## Deployment

### Production Settings

1. Set `FLASK_ENV=production` in `.env`
2. Use PostgreSQL: `DATABASE_URL=postgresql://...`
3. Generate strong `SECRET_KEY`
4. Disable debug mode: `FLASK_DEBUG=False`

### Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```

## Security Notes

- Passwords hashed with Werkzeug
- SQLAlchemy prevents SQL injection
- CSRF protection via Flask-WTF (if implemented)
- File upload validation
- Session-based authentication

## Future Enhancements

- Member registration form (public)
- Event registration system with QR codes
- Email notifications (SMTP)
- WhatsApp integration
- Volunteer hour tracking
- Achievement/rewards system
- API endpoints for mobile app
- Multi-language support (i18n)

## License

This project is created for educational purposes. Modify and use as needed for your university organization.

---

Built with ❤️ by Kilo for Hima Informatika

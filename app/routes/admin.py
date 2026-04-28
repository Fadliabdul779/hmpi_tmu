import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract, and_, or_
from app import db
from app.models import User, Member, Event, EventRegistration, Announcement, Project, ContentBlock, OrganizationalStructure

admin_bp = Blueprint('admin', __name__)

# Role-based access decorators
def admin_required(f):
    """Require admin or superadmin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'superadmin']:
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def structural_required(f):
    """Require structural, admin, or superadmin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['structural', 'admin', 'superadmin']:
            flash('Structural access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_or_structural_required(f):
    """Require structural or higher role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['structural', 'admin', 'superadmin']:
            flash('Structural or admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    """Require superadmin role only"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'superadmin':
            flash('Super admin access required.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    return _render_dashboard(current_user.role)

@admin_bp.route('/structural')
@login_required
@structural_required
def structural_dashboard():
    """Structural dashboard with limited statistics"""
    return _render_dashboard(current_user.role, structural=True)

def _render_dashboard(role, structural=False):
    """Shared dashboard rendering logic"""
    # Date range for filtering (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Key metrics
    total_members = Member.query.count()
    total_events = Event.query.count()
    total_announcements = Announcement.query.count()
    total_projects = Project.query.count()
    
    # Recent members (last 7 days)
    recent_members = Member.query.filter(
        Member.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    # Upcoming events (next 7 days)
    upcoming_events = Event.query.filter(
        and_(
            Event.start_date >= datetime.utcnow(),
            Event.start_date <= datetime.utcnow() + timedelta(days=7),
            Event.is_published == True
        )
    ).count()
    
    # Monthly registration data for chart
    monthly_data = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_name = month_start.strftime('%B %Y')
        member_count = Member.query.filter(
            extract('year', Member.created_at) == month_start.year,
            extract('month', Member.created_at) == month_start.month
        ).count()
        event_count = Event.query.filter(
            extract('year', Event.created_at) == month_start.year,
            extract('month', Event.created_at) == month_start.month
        ).count()
        monthly_data.append({
            'month': month_name,
            'members': member_count,
            'events': event_count
        })
    monthly_data.reverse()
    
    # Member distribution by program
    program_stats = db.session.query(
        Member.study_program, func.count(Member.id)
    ).filter(
        Member.study_program.isnot(None)
    ).group_by(Member.study_program).all()
    
    program_labels = [p[0] for p in program_stats]
    program_values = [p[1] for p in program_stats]
    
    # Recent activities
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    pending_registrations = EventRegistration.query.filter_by(status='registered').count()
    
    template = 'admin/structural_dashboard.html' if structural else 'admin/dashboard.html'
    
    return render_template(template,
                         total_members=total_members,
                         total_events=total_events,
                         total_announcements=total_announcements,
                         total_projects=total_projects,
                         recent_members=recent_members,
                         upcoming_events=upcoming_events,
                         monthly_data=json.dumps(monthly_data),
                         program_labels=json.dumps(program_labels),
                         program_values=json.dumps(program_values),
                         recent_events=recent_events,
                         recent_announcements=recent_announcements,
                         pending_registrations=pending_registrations,
                         user_role=role,
                         is_structural=structural)

@admin_bp.route('/members')
@login_required
@admin_or_structural_required
def members():
    """Member management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    program = request.args.get('program', '')
    
    query = Member.query.join(User)
    
    if search:
        query = query.filter(
            or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                Member.nim.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%')
            )
        )
    
    if program:
        query = query.filter(Member.study_program == program)
    
    members = query.order_by(Member.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get unique programs for filter
    programs = db.session.query(Member.study_program).filter(
        Member.study_program.isnot(None)
    ).distinct().all()
    
    return render_template('admin/members.html', 
                         members=members, 
                         search=search, 
                         program=program,
                         programs=[p[0] for p in programs])

@admin_bp.route('/members/<int:id>')
@login_required
@admin_or_structural_required
def member_detail(id):
    """Member detail view"""
    member = Member.query.get_or_404(id)
    registrations = EventRegistration.query.filter_by(member_id=id).all()
    return render_template('admin/member_detail.html', 
                         member=member, 
                         registrations=registrations)

@admin_bp.route('/members/create', methods=['GET', 'POST'])
@login_required
@admin_required
def member_create():
    """Create new member"""
    from werkzeug.security import generate_password_hash
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        nim = request.form.get('nim')
        phone = request.form.get('phone')
        study_program = request.form.get('study_program')
        semester = request.form.get('semester', type=int)
        password = request.form.get('password')
        skills = request.form.get('skills', '')
        interests = request.form.get('interests', '')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.member_create'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.member_create'))
        if Member.query.filter_by(nim=nim).first():
            flash('NIM already exists.', 'danger')
            return redirect(url_for('admin.member_create'))
        
        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=generate_password_hash(password),
            role='member',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Create member profile
        member = Member(
            user_id=user.id,
            nim=nim,
            phone=phone,
            study_program=study_program,
            semester=semester,
            skills=skills,
            interests=interests
        )
        db.session.add(member)
        db.session.commit()
        
        flash(f'Member {user.full_name} created successfully!', 'success')
        return redirect(url_for('admin.members'))
    
    return render_template('admin/member_form.html', member=None)

@admin_bp.route('/members/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def member_edit(id):
    """Edit member"""
    member = Member.query.get_or_404(id)
    user = member.user

    # Permission check: only allow editing members/structural, not admin/superadmin unless you're superadmin
    if user.role in ['admin', 'superadmin'] and current_user.role != 'superadmin':
        flash('You do not have permission to edit this user.', 'danger')
        return redirect(url_for('admin.members'))

    # Determine allowed roles for this user based on current_user's role
    if current_user.role == 'superadmin':
        allowed_roles = ['superadmin', 'admin', 'structural', 'member']
    else:  # admin
        allowed_roles = ['structural', 'member']

    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        member.nim = request.form.get('nim')
        member.phone = request.form.get('phone')
        member.study_program = request.form.get('study_program')
        member.semester = request.form.get('semester', type=int)
        member.skills = request.form.get('skills', '')
        member.interests = request.form.get('interests', '')

        # Handle role update if present
        if 'role' in request.form:
            new_role = request.form.get('role')
            if new_role in allowed_roles:
                user.role = new_role
            else:
                flash('Invalid role selection.', 'danger')
                return redirect(url_for('admin.member_edit', id=id))

        db.session.commit()
        flash(f'Member {user.full_name} updated successfully!', 'success')
        return redirect(url_for('admin.members'))

    return render_template('admin/member_form.html', member=member, available_roles=allowed_roles)

@admin_bp.route('/members/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_member(id):
    """Toggle member active status"""
    member = Member.query.get_or_404(id)
    # Superadmin cannot be deactivated
    if member.user.role == 'superadmin':
        flash('Super admin account cannot be modified.', 'danger')
        return redirect(url_for('admin.members'))
    member.is_active = not member.is_active
    db.session.commit()
    flash(f'Member {member.user.full_name} status updated.', 'success')
    return redirect(url_for('admin.members'))

@admin_bp.route('/members/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_member(id):
    """Delete member - only superadmin can delete any user"""
    member = Member.query.get_or_404(id)
    # Superadmin cannot be deleted by anyone
    if member.user.role == 'superadmin':
        flash('Super admin account cannot be deleted.', 'danger')
        return redirect(url_for('admin.members'))
    # Only superadmin can delete users
    if current_user.role != 'superadmin':
        flash('Only super admin can delete users.', 'danger')
        return redirect(url_for('admin.members'))
    
    db.session.delete(member.user)  # This cascades to Member via relationship
    db.session.commit()
    flash('Member deleted successfully.', 'success')
    return redirect(url_for('admin.members'))


@admin_bp.route('/events')
@login_required
@admin_or_structural_required
def events():
    """Event management page"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    status = request.args.get('status', '')

    query = Event.query

    if category:
        query = query.filter(Event.category == category)

    if status == 'published':
        query = query.filter(Event.is_published == True)
    elif status == 'draft':
        query = query.filter(Event.is_published == False)

    events = query.order_by(Event.start_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    categories = db.session.query(Event.category).distinct().all()
    return render_template('admin/events.html',
                         events=events,
                         category=category,
                         status=status,
                         categories=[c[0] for c in categories])

@admin_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
@admin_required
def event_create():
    """Create new event"""
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug') or title.lower().replace(' ', '-')
        description = request.form.get('description')
        short_description = request.form.get('short_description')
        category = request.form.get('category')
        location = request.form.get('location')
        online_link = request.form.get('online_link')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        end_date = request.form.get('end_date')
        registration_deadline = request.form.get('registration_deadline')
        max_participants = request.form.get('max_participants')
        is_published = request.form.get('is_published') == 'on'
        is_featured = request.form.get('is_featured') == 'on'
        
        event = Event(
            title=title,
            slug=slug,
            description=description,
            short_description=short_description,
            category=category,
            location=location,
            online_link=online_link,
            start_date=start_date,
            organizer_id=current_user.id,
            is_published=is_published,
            is_featured=is_featured
        )
        
        if end_date:
            event.end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
        if registration_deadline:
            event.registration_deadline = datetime.strptime(registration_deadline, '%Y-%m-%dT%H:%M')
        if max_participants:
            event.max_participants = int(max_participants)
        
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/event_form.html', event=None)

@admin_bp.route('/events/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def event_edit(id):
    """Edit event"""
    event = Event.query.get_or_404(id)
    
    if request.method == 'POST':
        event.title = request.form.get('title')
        event.slug = request.form.get('slug') or event.title.lower().replace(' ', '-')
        event.description = request.form.get('description')
        event.short_description = request.form.get('short_description')
        event.category = request.form.get('category')
        event.location = request.form.get('location')
        event.online_link = request.form.get('online_link')
        event.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        event.is_published = request.form.get('is_published') == 'on'
        event.is_featured = request.form.get('is_featured') == 'on'
        
        end_date = request.form.get('end_date')
        event.end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M') if end_date else None
        
        registration_deadline = request.form.get('registration_deadline')
        event.registration_deadline = datetime.strptime(registration_deadline, '%Y-%m-%dT%H:%M') if registration_deadline else None
        
        max_participants = request.form.get('max_participants')
        event.max_participants = int(max_participants) if max_participants else None
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/event_form.html', event=event)

@admin_bp.route('/events/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def event_delete(id):
    """Delete event"""
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin.events'))

@admin_bp.route('/announcements')
@login_required
@admin_or_structural_required
def announcements():
    """Announcement management page"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    
    query = Announcement.query
    
    if category:
        query = query.filter(Announcement.category == category)
    
    if status == 'published':
        query = query.filter(Announcement.is_published == True, Announcement.published_at.isnot(None))
    elif status == 'draft':
        query = query.filter(or_(
            Announcement.is_published == False,
            Announcement.published_at.is_(None)
        ))
    
    announcements = query.order_by(Announcement.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = db.session.query(Announcement.category).distinct().all()
    return render_template('admin/announcements.html',
                         announcements=announcements,
                         category=category,
                         status=status,
                         categories=[c[0] for c in categories])

@admin_bp.route('/announcements/create', methods=['GET', 'POST'])
@login_required
@admin_required
def announcement_create():
    """Create new announcement"""
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug') or title.lower().replace(' ', '-')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt') or content[:500]
        category = request.form.get('category', 'news')
        is_published = request.form.get('is_published') == 'on'
        is_featured = request.form.get('is_featured') == 'on'
        
        announcement = Announcement(
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            category=category,
            author_id=current_user.id,
            is_published=is_published,
            is_featured=is_featured
        )
        
        if is_published:
            announcement.published_at = datetime.utcnow()
        
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('admin.announcements'))
    
    return render_template('admin/announcement_form.html', announcement=None)

@admin_bp.route('/announcements/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def announcement_edit(id):
    """Edit announcement"""
    announcement = Announcement.query.get_or_404(id)
    
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.slug = request.form.get('slug') or announcement.title.lower().replace(' ', '-')
        announcement.content = request.form.get('content')
        announcement.excerpt = request.form.get('excerpt') or announcement.content[:500]
        announcement.category = request.form.get('category')
        announcement.is_published = request.form.get('is_published') == 'on'
        announcement.is_featured = request.form.get('is_featured') == 'on'
        
        if announcement.is_published and not announcement.published_at:
            announcement.published_at = datetime.utcnow()
        
        db.session.commit()
        flash('Announcement updated successfully!', 'success')
        return redirect(url_for('admin.announcements'))
    
    return render_template('admin/announcement_form.html', announcement=announcement)

@admin_bp.route('/announcements/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def announcement_delete(id):
    """Delete announcement"""
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    flash('Announcement deleted successfully!', 'success')
    return redirect(url_for('admin.announcements'))

@admin_bp.route('/projects')
@login_required
@admin_or_structural_required
def projects():
    """Project management page"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = Project.query
    
    if category:
        query = query.filter(Project.category == category)
    
    projects = query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = db.session.query(Project.category).distinct().all()
    return render_template('admin/projects.html',
                         projects=projects,
                         category=category,
                         categories=[c[0] for c in categories])

@admin_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
@admin_required
def project_create():
    """Create new project"""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug') or name.lower().replace(' ', '-')
        description = request.form.get('description')
        short_description = request.form.get('short_description')
        category = request.form.get('category')
        technologies = request.form.get('technologies')
        github_url = request.form.get('github_url')
        demo_url = request.form.get('demo_url')
        is_published = request.form.get('is_published') == 'on'
        is_featured = request.form.get('is_featured') == 'on'
        team_leader_id = request.form.get('team_leader_id', type=int)
        
        # Use current user as team leader if not specified
        if not team_leader_id:
            team_leader_id = current_user.id
        
        project = Project(
            name=name,
            slug=slug,
            description=description,
            short_description=short_description,
            category=category,
            technologies=technologies,
            github_url=github_url,
            demo_url=demo_url,
            team_leader_id=team_leader_id,
            is_published=is_published,
            is_featured=is_featured
        )
        
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('admin.projects'))
    
    members = Member.query.join(User).all()
    return render_template('admin/project_form.html', project=None, members=members)

@admin_bp.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def project_edit(id):
    """Edit project"""
    project = Project.query.get_or_404(id)
    
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.slug = request.form.get('slug') or project.name.lower().replace(' ', '-')
        project.description = request.form.get('description')
        project.short_description = request.form.get('short_description')
        project.category = request.form.get('category')
        project.technologies = request.form.get('technologies')
        project.github_url = request.form.get('github_url')
        project.demo_url = request.form.get('demo_url')
        project.is_published = request.form.get('is_published') == 'on'
        project.is_featured = request.form.get('is_featured') == 'on'
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('admin.projects'))
    
    members = Member.query.join(User).all()
    return render_template('admin/project_form.html', project=project, members=members)

@admin_bp.route('/projects/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def project_delete(id):
    """Delete project"""
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('admin.projects'))


# Helper function for default content
def _get_default_content(identifier):
    defaults = {
        'about.hero.subtitle': 'Himpunan Mahasiswa Informatika (HIMA) adalah organisasi resmi mahasiswa jurusan/Program Studi Informatika yang berfungsi sebagai wadah untuk mengembangkan potensi akademik, teknologi, dan karakter mahasiswa.',
        'about.vision.title': 'Visi',
        'about.vision.content': 'Menjadi organisasi mahasiswa yang unggul, inovatif, dan Berjiwa teknologi serta berperan aktif dalam pengembangan ilmiah dan karakter mahasiswa Informatika.',
        'about.mission.title': 'Misi',
        'about.mission.items': "Mengembangkan potensi teknologi dan inovasi mahasiswa\nMenciptakan lingkungan belajar yang kolaboratif dan kreatif\nMengadakan kegiatan akademik dan teknologi yang bermanfaat\nMembangun jejaring dengan industri dan organisasi profesional",
        'about.programs.workshop.title': 'Workshop Teknologi',
        'about.programs.workshop.description': 'Kelas praktis mingguan untuk meningkatkan kemampuan teknis mahasiswa dalam berbagai bidang teknologi.',
        'about.programs.seminar.title': 'Seminar & Talkshow',
        'about.programs.seminar.description': 'Sesi dengan praktisi industri dan pakar untuk update pengetahuan teknologi terkini.',
        'about.programs.hackathon.title': 'Hackathon & Kompetisi',
        'about.programs.hackathon.description': 'Ajang kompetisi untuk menguji kemampuan dalam menyelesaikan masalah dengan teknologi.',
        'contact.header.title': 'Hubungi Kami',
        'contact.header.subtitle': 'Punya pertanyaan, saran, atau ingin berkolaborasi? Jangan ragu untuk menghubungi kami.',
        'contact.email': 'himitikatmu@gmail.com',
        'contact.phone': '+62 858-6923-0249',
        'contact.address': 'Jl. Melati No. 27, Kejambon\nKec. Tegal Timur, Kota Tegal\nJawa Tengah, Indonesia',
        'contact.instagram': '@hmpi_tmu',
    }
    return defaults.get(identifier, '')


@admin_bp.route('/content')
@login_required
@admin_required
def content_blocks():
    """Manage site content blocks (super admin only)"""
    block_definitions = [
        {'identifier': 'about.hero.subtitle', 'name': 'About - Hero Subtitle', 'description': 'Subtitle under main title on about page'},
        {'identifier': 'about.vision.title', 'name': 'About - Vision Title', 'description': 'Title for vision section'},
        {'identifier': 'about.vision.content', 'name': 'About - Vision Content', 'description': 'Vision statement text'},
        {'identifier': 'about.mission.title', 'name': 'About - Mission Title', 'description': 'Title for mission section'},
        {'identifier': 'about.mission.items', 'name': 'About - Mission Items', 'description': 'Mission items (one per line)'},
        {'identifier': 'about.programs.workshop.title', 'name': 'About - Workshop Program Title', 'description': 'Workshop program title'},
        {'identifier': 'about.programs.workshop.description', 'name': 'About - Workshop Description', 'description': 'Workshop program description'},
        {'identifier': 'about.programs.seminar.title', 'name': 'About - Seminar Program Title', 'description': 'Seminar program title'},
        {'identifier': 'about.programs.seminar.description', 'name': 'About - Seminar Description', 'description': 'Seminar program description'},
        {'identifier': 'about.programs.hackathon.title', 'name': 'About - Hackathon Program Title', 'description': 'Hackathon program title'},
        {'identifier': 'about.programs.hackathon.description', 'name': 'About - Hackathon Description', 'description': 'Hackathon program description'},
        {'identifier': 'contact.header.title', 'name': 'Contact - Header Title', 'description': 'Contact page title'},
        {'identifier': 'contact.header.subtitle', 'name': 'Contact - Header Subtitle', 'description': 'Contact page subtitle'},
        {'identifier': 'contact.email', 'name': 'Contact - Email', 'description': 'Contact email address'},
        {'identifier': 'contact.phone', 'name': 'Contact - Phone', 'description': 'Contact phone number'},
        {'identifier': 'contact.address', 'name': 'Contact - Address', 'description': 'Contact address'},
        {'identifier': 'contact.instagram', 'name': 'Contact - Instagram', 'description': 'Instagram handle'},
    ]

    identifiers = [b['identifier'] for b in block_definitions]
    blocks = ContentBlock.query.filter(ContentBlock.identifier.in_(identifiers)).all()
    block_dict = {b.identifier: b for b in blocks}

    # Create missing blocks with defaults
    new_blocks = []
    for b in block_definitions:
        if b['identifier'] not in block_dict:
            default_content = _get_default_content(b['identifier'])
            block = ContentBlock(
                identifier=b['identifier'],
                title=b['name'],
                content=default_content
            )
            new_blocks.append(block)
    if new_blocks:
        try:
            db.session.add_all(new_blocks)
            db.session.commit()
            # Refresh blocks dict
            blocks = ContentBlock.query.filter(ContentBlock.identifier.in_(identifiers)).all()
            block_dict = {b.identifier: b for b in blocks}
        except Exception as e:
            db.session.rollback()
            flash('Error creating default content blocks: ' + str(e), 'danger')

    return render_template('admin/content_blocks.html', block_list=block_definitions, blocks=block_dict)


@admin_bp.route('/content/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def content_block_edit(id):
    """Edit a content block"""
    block = ContentBlock.query.get_or_404(id)
    if request.method == 'POST':
        block.title = request.form.get('title')

        # Special handling for mission items
        if block.identifier == 'about.mission.items':
            mission_items = request.form.getlist('mission_items[]')
            # Filter out empty items and join with newlines
            block.content = '\n'.join(item.strip() for item in mission_items if item.strip())
        else:
            block.content = request.form.get('content')

        block.updated_by = current_user.id
        db.session.commit()
        flash('Content updated successfully!', 'success')
        return redirect(url_for('admin.content_blocks'))
    return render_template('admin/content_block_form.html', block=block)


@admin_bp.route('/organizational-structure')
@login_required
@admin_or_structural_required
def organizational_structure():
    """Organizational structure management page"""
    structure = OrganizationalStructure.query.filter_by(is_active=True).order_by(
        OrganizationalStructure.level, OrganizationalStructure.order
    ).all()

    # Group by level for display
    levels = {}
    for item in structure:
        if item.level not in levels:
            levels[item.level] = []
        levels[item.level].append(item)

    return render_template('admin/organizational_structure.html', structure=structure, levels=levels)


@admin_bp.route('/organizational-structure/create', methods=['GET', 'POST'])
@login_required
@admin_required
def organizational_structure_create():
    """Create new organizational structure position"""
    if request.method == 'POST':
        position_name = request.form.get('position_name')
        member_id = request.form.get('member_id') or None
        parent_id = request.form.get('parent_id') or None
        level = int(request.form.get('level', 0))
        order = int(request.form.get('order', 0))

        # Validate parent exists if specified
        if parent_id:
            parent = OrganizationalStructure.query.get(parent_id)
            if not parent:
                flash('Parent position not found.', 'danger')
                return redirect(url_for('admin.organizational_structure_create'))

        # Validate member exists if specified
        if member_id:
            member = Member.query.get(member_id)
            if not member:
                flash('Member not found.', 'danger')
                return redirect(url_for('admin.organizational_structure_create'))

        structure = OrganizationalStructure(
            position_name=position_name,
            member_id=member_id,
            parent_id=parent_id,
            level=level,
            order=order,
            is_active=True
        )

        db.session.add(structure)
        db.session.commit()
        flash('Organizational position created successfully!', 'success')
        return redirect(url_for('admin.organizational_structure'))

    # Get available parents and members
    parents = OrganizationalStructure.query.filter_by(is_active=True).all()
    members = Member.query.join(User).filter(User.is_active == True).all()

    return render_template('admin/organizational_structure_form.html',
                         structure=None, parents=parents, members=members)


@admin_bp.route('/organizational-structure/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def organizational_structure_edit(id):
    """Edit organizational structure position"""
    structure = OrganizationalStructure.query.get_or_404(id)

    if request.method == 'POST':
        structure.position_name = request.form.get('position_name')
        structure.member_id = request.form.get('member_id') or None
        structure.parent_id = request.form.get('parent_id') or None
        structure.level = int(request.form.get('level', 0))
        structure.order = int(request.form.get('order', 0))

        # Validate parent exists if specified
        if structure.parent_id:
            parent = OrganizationalStructure.query.get(structure.parent_id)
            if not parent:
                flash('Parent position not found.', 'danger')
                return redirect(url_for('admin.organizational_structure_edit', id=id))

        # Validate member exists if specified
        if structure.member_id:
            member = Member.query.get(structure.member_id)
            if not member:
                flash('Member not found.', 'danger')
                return redirect(url_for('admin.organizational_structure_edit', id=id))

        db.session.commit()
        flash('Organizational position updated successfully!', 'success')
        return redirect(url_for('admin.organizational_structure'))

    # Get available parents (excluding self and descendants) and members
    parents = OrganizationalStructure.query.filter(
        OrganizationalStructure.is_active == True,
        OrganizationalStructure.id != id
    ).all()

    members = Member.query.join(User).filter(User.is_active == True).all()

    return render_template('admin/organizational_structure_form.html',
                         structure=structure, parents=parents, members=members)


@admin_bp.route('/organizational-structure/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def organizational_structure_delete(id):
    """Delete organizational structure position"""
    structure = OrganizationalStructure.query.get_or_404(id)

    # Check if position has children
    if structure.children:
        flash('Cannot delete position that has subordinates. Remove or reassign subordinates first.', 'danger')
        return redirect(url_for('admin.organizational_structure'))

    db.session.delete(structure)
    db.session.commit()
    flash('Organizational position deleted successfully!', 'success')
    return redirect(url_for('admin.organizational_structure'))


@admin_bp.route('/api/organizational-structure')
@login_required
@admin_required
def api_organizational_structure():
    """API endpoint for organizational structure tree data"""
    structure = OrganizationalStructure.query.filter_by(is_active=True).order_by(
        OrganizationalStructure.level, OrganizationalStructure.order
    ).all()

    # Build tree structure
    def build_tree(items, parent_id=None):
        tree = []
        for item in items:
            if item.parent_id == parent_id:
                node = {
                    'id': item.id,
                    'position_name': item.position_name,
                    'level': item.level,
                    'order': item.order,
                    'member': {
                        'id': item.member.id if item.member else None,
                        'name': f"{item.member.user.first_name} {item.member.user.last_name}" if item.member else None,
                        'nim': item.member.nim if item.member else None,
                        'avatar': item.member.avatar if item.member else None
                    } if item.member else None,
                    'children': build_tree(items, item.id)
                }
                tree.append(node)
        return tree

    tree_data = build_tree(structure)
    return jsonify(tree_data)


@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API endpoint for dashboard statistics"""
    # Monthly data for last 6 months
    monthly_data = {'labels': [], 'members': [], 'events': []}

    for i in range(5, -1, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_name = month_start.strftime('%b %Y')

        member_count = Member.query.filter(
            extract('year', Member.created_at) == month_start.year,
            extract('month', Member.created_at) == month_start.month
        ).count()

        event_count = Event.query.filter(
            extract('year', Event.created_at) == month_start.year,
            extract('month', Event.created_at) == month_start.month
        ).count()

        monthly_data['labels'].append(month_name)
        monthly_data['members'].append(member_count)
        monthly_data['events'].append(event_count)

    # Member distribution by program
    program_stats = db.session.query(
        Member.study_program, func.count(Member.id)
    ).filter(Member.study_program.isnot(None)).group_by(Member.study_program).all()

    program_data = {
        'labels': [p[0] for p in program_stats],
        'values': [p[1] for p in program_stats]
    }

    return jsonify({
        'total_members': Member.query.count(),
        'total_events': Event.query.filter_by(is_published=True).count(),
        'total_announcements': Announcement.query.filter_by(is_published=True).count(),
        'total_projects': Project.query.filter_by(is_published=True).count(),
        'monthly_data': monthly_data,
        'program_data': program_data
    })

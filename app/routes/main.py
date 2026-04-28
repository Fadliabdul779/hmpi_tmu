from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import Event, Announcement, Project, Member, ContentBlock, Sponsor, OrganizationalStructure

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage"""
    now = datetime.utcnow()
    featured_events = Event.query.filter(
        Event.is_published == True,
        Event.is_featured == True,
        Event.start_date >= now
    ).order_by(Event.start_date).limit(3).all()
    
    upcoming_events = Event.query.filter(
        Event.is_published == True,
        Event.start_date >= now
    ).order_by(Event.start_date).limit(6).all()
    
    featured_announcements = Announcement.query.filter_by(
        is_published=True,
        is_featured=True
    ).order_by(Announcement.published_at.desc()).limit(3).all()
    
    recent_announcements = Announcement.query.filter_by(
        is_published=True
    ).order_by(Announcement.published_at.desc()).limit(4).all()
    
    featured_projects = Project.query.filter_by(
        is_published=True,
        is_featured=True
    ).limit(6).all()
    
    recent_projects = Project.query.filter_by(
        is_published=True
    ).order_by(Project.created_at.desc()).limit(3).all()
    
    total_members = Member.query.count()
    
    return render_template('index.html',
                         featured_events=featured_events,
                         upcoming_events=upcoming_events,
                         featured_announcements=featured_announcements,
                         recent_announcements=recent_announcements,
                         featured_projects=featured_projects,
                         recent_projects=recent_projects,
                         total_members=total_members)

@main_bp.route('/events')
def events_list():
    """Public events listing"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = Event.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    events = query.order_by(Event.start_date.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    categories = db.session.query(Event.category).filter(Event.is_published==True).distinct().all()
    
    return render_template('events.html',
                         events=events,
                         category=category,
                         categories=[c[0] for c in categories])

@main_bp.route('/news')
def news_list():
    """Public news/announcements listing"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = Announcement.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    announcements = query.order_by(Announcement.published_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    categories = db.session.query(Announcement.category).filter(Announcement.is_published==True).distinct().all()
    
    return render_template('news.html',
                         announcements=announcements,
                         category=category,
                         categories=[c[0] for c in categories])

@main_bp.route('/projects')
def projects_list():
    """Public projects listing"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = Project.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    projects = query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    categories = db.session.query(Project.category).filter(Project.is_published==True).distinct().all()
    
    return render_template('projects.html',
                         projects=projects,
                         category=category,
                         categories=[c[0] for c in categories])

@main_bp.route('/about')
def about():
    """About page"""
    total_members = Member.query.count()

    # Get member statistics by program
    program_stats = db.session.query(
        Member.study_program, func.count(Member.id)
    ).filter(Member.study_program.isnot(None)).group_by(Member.study_program).all()

    # Get recent projects
    recent_projects = Project.query.filter_by(is_published=True).limit(6).all()

    # Get content blocks for about page
    block_identifiers = [
        'about.hero.subtitle',
        'about.vision.title',
        'about.vision.content',
        'about.mission.title',
        'about.mission.items',
        'about.programs.workshop.title',
        'about.programs.workshop.description',
        'about.programs.seminar.title',
        'about.programs.seminar.description',
        'about.programs.hackathon.title',
        'about.programs.hackathon.description',
    ]
    blocks = ContentBlock.query.filter(ContentBlock.identifier.in_(block_identifiers)).all()
    content_blocks = {b.identifier: b for b in blocks}

    return render_template('about.html',
                          total_members=total_members,
                          program_stats=program_stats,
                          recent_projects=recent_projects,
                          content_blocks=content_blocks)

@main_bp.route('/contact')
def contact():
    """Contact page"""
    # Get content blocks for contact page
    block_identifiers = [
        'contact.header.title',
        'contact.header.subtitle',
        'contact.email',
        'contact.phone',
        'contact.address',
        'contact.instagram',
    ]
    blocks = ContentBlock.query.filter(ContentBlock.identifier.in_(block_identifiers)).all()
    content_blocks = {b.identifier: b for b in blocks}

    return render_template('contact.html', content_blocks=content_blocks)


@main_bp.route('/events/<slug>')
def events_detail(slug):
    """Event detail page"""
    event = Event.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    # Get related events (same category, excluding current event)
    related_events = Event.query.filter(
        Event.category == event.category,
        Event.id != event.id,
        Event.is_published == True
    ).order_by(Event.start_date.desc()).limit(3).all()
    
    return render_template('events_detail.html', event=event, related_events=related_events)


@main_bp.route('/projects/<slug>')
def projects_detail(slug):
    """Project detail page"""
    project = Project.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template('projects_detail.html', project=project)


@main_bp.route('/sponsor')
def sponsor():
    """Sponsor & Mitra page"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = Sponsor.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    sponsors = query.order_by(Sponsor.name.asc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    categories = db.session.query(Sponsor.category).filter(Sponsor.is_published==True).distinct().all()
    sponsor_categories = [c[0] for c in categories if c[0]]
    
    sponsor_count = Sponsor.query.filter_by(is_published=True, type='sponsor').count()
    partner_count = Sponsor.query.filter_by(is_published=True, type='partner').count()
    total_support = db.session.query(db.func.sum(Sponsor.support_value)).filter_by(is_published=True).scalar() or 0
    
    return render_template('sponsor.html',
                         sponsors=sponsors,
                         category=category,
                         sponsor_categories=sponsor_categories,
                         sponsor_count=sponsor_count,
                         partner_count=partner_count,
                         total_support=total_support)


@main_bp.route('/gallery')
def gallery():
    """Gallery page"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    from app.models import Gallery
    query = Gallery.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    gallery_items = query.order_by(Gallery.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = db.session.query(Gallery.category).filter(Gallery.is_published==True).distinct().all()
    
    return render_template('gallery.html',
                         gallery_items=gallery_items,
                         category=category,
                         categories=[c[0] for c in categories])


@main_bp.route('/resources')
def resources():
    """Resources page"""
    return render_template('resources.html')


@main_bp.route('/api/organizational-structure')
def api_organizational_structure():
    """Public API endpoint for organizational structure tree data"""
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

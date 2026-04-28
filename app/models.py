from flask_login import UserMixin
from datetime import datetime
from app import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='member', nullable=False)  # superadmin, admin, structural, member
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    member_profile = db.relationship('Member', backref='user', uselist=False, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def can_be_modified_by(self, current_user):
        """Check if current user can modify/delete this user"""
        # Superadmin cannot be modified/deleted by anyone
        if self.role == 'superadmin':
            return False
        # Users can only be modified/deleted by superadmin
        return current_user.role == 'superadmin'
    
    def can_be_deactivated_by(self, current_user):
        """Check if current user can deactivate this user"""
        # Superadmin cannot be deactivated by anyone
        if self.role == 'superadmin':
            return False
        # Only superadmin can deactivate users
        return current_user.role == 'superadmin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Member(db.Model):
    """Extended member profile"""
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    nim = db.Column(db.String(20), unique=True, nullable=False)  # Nomor Induk Mahasiswa
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    study_program = db.Column(db.String(100), nullable=True)  # Program Studi
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    skills = db.Column(db.Text, nullable=True)  # JSON string of skills
    interests = db.Column(db.Text, nullable=True)  # JSON string of interests
    avatar = db.Column(db.String(255), default='default-avatar.png')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Member {self.nim}>'

class Event(db.Model):
    """Event/Activity model"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    short_description = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(50), nullable=False, default='workshop')  # workshop, seminar, hackathon, talkshow, project
    location = db.Column(db.String(200), nullable=True)
    online_link = db.Column(db.String(500), nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    registration_deadline = db.Column(db.DateTime, nullable=True)
    max_participants = db.Column(db.Integer, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    registrations = db.relationship('EventRegistration', backref='event', cascade='all, delete-orphan')
    organizer = db.relationship('User', backref='organized_events', foreign_keys=[organizer_id])
    
    def __repr__(self):
        return f'<Event {self.title}>'

class EventRegistration(db.Model):
    """Event registration model"""
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='registered')  # registered, attended, cancelled
    attendance = db.Column(db.Boolean, default=False)
    
    # Relationships
    member = db.relationship('Member', backref='event_registrations')
    
    __table_args__ = (
        db.UniqueConstraint('event_id', 'member_id', name='unique_event_registration'),
    )
    
    def __repr__(self):
        return f'<EventRegistration {self.id}>'

class Announcement(db.Model):
    """Announcement/News model"""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(50), nullable=False, default='news')  # news, announcement, article
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='announcements')
    
    def __repr__(self):
        return f'<Announcement {self.title}>'

class Project(db.Model):
    """Project model"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    short_description = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(50), nullable=False)  # website, mobile, ai, research, etc.
    technologies = db.Column(db.Text, nullable=True)  # JSON string of used technologies
    github_url = db.Column(db.String(500), nullable=True)
    demo_url = db.Column(db.String(500), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    team_leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team_members = db.relationship('ProjectMember', backref='project', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.name}>'

class ProjectMember(db.Model):
    """Project team members"""
    __tablename__ = 'project_members'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='member')  # leader, developer, designer, etc.

    # Relationships
    member = db.relationship('Member')

    __table_args__ = (
        db.UniqueConstraint('project_id', 'member_id', name='unique_project_member'),
    )

    def __repr__(self):
        return f'<ProjectMember {self.id}>'


class Sponsor(db.Model):
    """Sponsor & Partner model"""
    __tablename__ = 'sponsors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)  # platinum, gold, silver, bronze, partner
    type = db.Column(db.String(20), nullable=False, default='sponsor')  # sponsor, partner
    logo_url = db.Column(db.String(500), nullable=True)
    website = db.Column(db.String(500), nullable=True)
    support_value = db.Column(db.Numeric(15, 2), nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Sponsor {self.name}>'


class Gallery(db.Model):
    """Gallery/photo model"""
    __tablename__ = 'gallery'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default='other')  # event, workshop, seminar, community_service, social, other
    image = db.Column(db.String(255), nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Gallery {self.title}>'


class ContentBlock(db.Model):
    """Editable content blocks for static pages"""
    __tablename__ = 'content_blocks'

    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(identifier):
        block = ContentBlock.query.filter_by(identifier=identifier).first()
        return block.content if block else ''

    def __repr__(self):
        return f'<ContentBlock {self.identifier}>'


class OrganizationalStructure(db.Model):
    """Organizational structure with hierarchical positions"""
    __tablename__ = 'organizational_structure'

    id = db.Column(db.Integer, primary_key=True)
    position_name = db.Column(db.String(100), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('organizational_structure.id'), nullable=True)
    level = db.Column(db.Integer, default=0, nullable=False)  # 0 = top level, increases downward
    order = db.Column(db.Integer, default=0, nullable=False)  # ordering within same level
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    member = db.relationship('Member', backref='organizational_positions')
    parent = db.relationship('OrganizationalStructure', remote_side=[id], backref='children')

    def __repr__(self):
        return f'<OrganizationalStructure {self.position_name}>'


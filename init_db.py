#!/usr/bin/env python
"""Initialize database and create default admin user"""
import os
import sys
from app import create_app, db
from app.models import User, Member
from werkzeug.security import generate_password_hash

app = create_app()

# Ensure stdout can handle UTF-8 on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with app.app_context():
    # Create all tables
    db.create_all()
    print("Database tables created successfully")
    
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@hima.edu',
            password_hash=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='Hima',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  WARNING: Change password after first login!")
        
        # Create member profile for admin
        member = Member(
            user_id=admin.id,
            nim='ADMIN001',
            study_program='Informatika',
            is_active=True
        )
        db.session.add(member)
        db.session.commit()
        print("Member profile created")
    else:
        print("Admin user already exists")
    
    print("\nDatabase initialization complete!")
    print("\nYou can now log in at http://localhost:5000/admin/login")
    print("With credentials: admin / admin123")

from app import create_app

app = create_app()

with app.app_context():
    try:
        from flask import render_template
        html = render_template('index.html',
                              featured_events=[],
                              upcoming_events=[],
                              featured_announcements=[],
                              recent_announcements=[],
                              featured_projects=[],
                              recent_projects=[],
                              total_members=0)
        print("SUCCESS: Template renders correctly")
        print(f"HTML length: {len(html)} characters")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

from app import create_app, db
from app.models import OrganizationalStructure

app = create_app()

with app.app_context():
    # Create sample organizational structure
    # Level 0 - Top level
    ketua = OrganizationalStructure(
        position_name="Ketua Himpunan",
        level=0,
        order=0,
        is_active=True
    )
    db.session.add(ketua)

    wakil_ketua = OrganizationalStructure(
        position_name="Wakil Ketua Himpunan",
        level=0,
        order=1,
        is_active=True
    )
    db.session.add(wakil_ketua)

    # Level 1 - Department heads
    sekertaris = OrganizationalStructure(
        position_name="Sekretaris",
        parent_id=1,  # Will be set after commit
        level=1,
        order=0,
        is_active=True
    )
    db.session.add(sekertaris)

    bendahara = OrganizationalStructure(
        position_name="Bendahara",
        parent_id=1,
        level=1,
        order=1,
        is_active=True
    )
    db.session.add(bendahara)

    # Level 2 - Sub departments
    sekertaris_umum = OrganizationalStructure(
        position_name="Sekretaris Umum",
        level=2,
        order=0,
        is_active=True
    )
    db.session.add(sekertaris_umum)

    bendahara_umum = OrganizationalStructure(
        position_name="Bendahara Umum",
        level=2,
        order=1,
        is_active=True
    )
    db.session.add(bendahara_umum)

    # Commit to get IDs
    db.session.commit()

    # Set parent relationships
    sekertaris.parent_id = ketua.id
    bendahara.parent_id = ketua.id
    sekertaris_umum.parent_id = sekertaris.id
    bendahara_umum.parent_id = bendahara.id

    db.session.commit()

    print("Sample organizational structure created successfully!")
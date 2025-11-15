# init_db.py  — GENERIC SETUP, NO DEMO DATA

from app import create_app, db
from app.models import User, Institution
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # WARNING: Uncomment only if you are okay wiping everything
    # db.drop_all()

    db.create_all()

    # ---------- Institution ----------
    inst = Institution.query.filter_by(name="Demo University").first()
    if not inst:
        inst = Institution(name="Demo University")
        db.session.add(inst)
        db.session.commit()
        print(f"Created Institution: {inst.name} (id={inst.id})")
    else:
        print(f"Institution already exists: {inst.name} (id={inst.id})")

    # ---------- Super Admin ----------
    admin_email = "admin@demo.edu"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            username="superadmin",
            email=admin_email,
            role="admin",           # you’re using: admin, hod, faculty, student
            institution_id=inst.id,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin user: {admin_email} / admin123")
    else:
        print(f"Admin user already exists: {admin_email}")

    print("DB initialized. No rooms/batches/subjects/faculties were seeded.")

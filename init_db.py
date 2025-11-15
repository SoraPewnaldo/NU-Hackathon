from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()

    # Check if admin exists
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@example.com",
            role="admin"
        )
        admin.set_password("admin123")  # you can change the password later
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin / admin123")
    else:
        print("Admin user already exists.")
from app import create_app, db
from app.models import User, Room, Batch, Subject, Faculty, Timeslot, Timetable, TimetableEntry, FacultySubject

app = create_app()

with app.app_context():
    db.create_all()

    # ----- ADMIN -----
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin @example.com",
            role=User.ROLE_ADMIN,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        print("Admin user created: admin / admin123")

    # ----- HOD -----
    hod = User.query.filter_by(username="hod_cse").first()
    if not hod:
        hod = User(
            username="hod_cse",
            email="hod_cse @example.com",
            role=User.ROLE_HOD,
        )
        hod.set_password("hod123")
        db.session.add(hod)
        print("HOD user created: hod_cse / hod123")

    # ----- FACULTY -----
    faculty_user = User.query.filter_by(username="fac_alice").first()
    if not faculty_user:
        faculty_user = User(
            username="fac_alice",
            email="alice @example.com",
            role=User.ROLE_FACULTY,
        )
        faculty_user.set_password("faculty123")
        db.session.add(faculty_user)
        print("Faculty user created: fac_alice / faculty123")

    # ----- STUDENT -----
    student_user = User.query.filter_by(username="stud_bob").first()
    if not student_user:
        student_user = User(
            username="stud_bob",
            email="bob @example.com",
            role=User.ROLE_STUDENT,
        )
        student_user.set_password("student123")
        db.session.add(student_user)
        print("Student user created: stud_bob / student123")

    db.session.commit()
    print("DB init complete.")
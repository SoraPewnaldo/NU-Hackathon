from datetime import time

from app import create_app, db
from app.models import (
    User,
    Room,
    Batch,
    Subject,
    Faculty,
    Timeslot,
    Timetable,
    TimetableEntry,
    FacultySubject,
)

app = create_app()

with app.app_context():
    db.create_all()

    # -------------------
    # 1) USERS (ROLES)
    # -------------------
    def get_or_create_user(username, email, role, password):
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            print(f"Created user: {username} / {password} ({role})")
        return user

    admin = get_or_create_user("admin", "admin@example.com", User.ROLE_ADMIN, "admin123")
    hod_cse = get_or_create_user("hod_cse", "hod_cse@example.com", User.ROLE_HOD, "hod123")
    faculty_user = get_or_create_user("fac_alice", "alice@example.com", User.ROLE_FACULTY, "faculty123")
    student_user = get_or_create_user("stud_bob", "bob@example.com", User.ROLE_STUDENT, "student123")

    db.session.commit()

    # -------------------
    # 2) ROOMS
    # -------------------
    if Room.query.count() == 0:
        rooms = [
            Room(name="C-301", capacity=60, room_type="classroom"),
            Room(name="C-302", capacity=60, room_type="classroom"),
            Room(name="Lab-1", capacity=30, room_type="lab"),
            Room(name="Seminar-Hall", capacity=120, room_type="seminar"),
        ]
        db.session.add_all(rooms)
        print("Seeded rooms.")

    # -------------------
    # 3) BATCHES
    # -------------------
    if Batch.query.count() == 0:
        batches = [
            Batch(name="CSE-2A", program="BTech CSE", semester=2, size=65),
            Batch(name="CSE-2B", program="BTech CSE", semester=2, size=62),
        ]
        db.session.add_all(batches)
        print("Seeded batches.")

    # -------------------
    # 4) SUBJECTS
    # -------------------
    if Subject.query.count() == 0:
        subjects = [
            Subject(code="CS201", name="Data Structures", semester=2, classes_per_week=4, is_lab=False),
            Subject(code="CS202", name="Algorithms", semester=2, classes_per_week=3, is_lab=False),
            Subject(code="CS203", name="Computer Organization", semester=2, classes_per_week=3, is_lab=False),
            Subject(code="CS204", name="DS Lab", semester=2, classes_per_week=2, is_lab=True),
        ]
        db.session.add_all(subjects)
        print("Seeded subjects.")

    db.session.commit()

    # -------------------
    # 5) FACULTIES
    # -------------------
    if Faculty.query.count() == 0:
        # Link one faculty to the fac_alice user; others are just faculty entries
        fac1 = Faculty(
            name="Alice Sharma",
            code="F001",
            max_load_per_week=16,
            user_id=faculty_user.id,
        )
        fac2 = Faculty(
            name="Rohit Verma",
            code="F002",
            max_load_per_week=18,
        )
        fac3 = Faculty(
            name="Neha Singh",
            code="F003",
            max_load_per_week=14,
        )

        db.session.add_all([fac1, fac2, fac3])
        print("Seeded faculties.")
        db.session.commit()
    else:
        fac1 = Faculty.query.filter_by(code="F001").first()
        fac2 = Faculty.query.filter_by(code="F002").first()
        fac3 = Faculty.query.filter_by(code="F003").first()

    # -------------------
    # 6) FACULTY-SUBJECT MAPPING
    # -------------------
    if FacultySubject.query.count() == 0:
        cs201 = Subject.query.filter_by(code="CS201").first()
        cs202 = Subject.query.filter_by(code="CS202").first()
        cs203 = Subject.query.filter_by(code="CS203").first()
        cs204 = Subject.query.filter_by(code="CS204").first()

        mappings = [
            # Alice teaches DS + DS Lab
            FacultySubject(faculty_id=fac1.id, subject_id=cs201.id),
            FacultySubject(faculty_id=fac1.id, subject_id=cs204.id),

            # Rohit teaches Algorithms
            FacultySubject(faculty_id=fac2.id, subject_id=cs202.id),

            # Neha teaches CO
            FacultySubject(faculty_id=fac3.id, subject_id=cs203.id),
        ]
        db.session.add_all(mappings)
        print("Seeded faculty-subject mappings.")

    # -------------------
    # 7) TIMESLOTS (Mon–Fri, 9–11 & 1–3 for demo)
    # -------------------
    if Timeslot.query.count() == 0:
        days = list(range(0, 5))  # 0=Mon ... 4=Fri
        periods = [
            (time(9, 0), time(10, 0)),
            (time(10, 0), time(11, 0)),
            (time(11, 0), time(12, 0)),
            (time(13, 0), time(14, 0)),
            (time(14, 0), time(15, 0)),
        ]

        timeslots = []
        for d in days:
            for start, end in periods:
                timeslots.append(Timeslot(day_of_week=d, start_time=start, end_time=end))

        db.session.add_all(timeslots)
        print("Seeded timeslots (Mon–Fri, 5 periods/day).")

    db.session.commit()

    print("✅ Database seeding complete.")
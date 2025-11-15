# init_db.py

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
    Student,    # <-- NEW
)

app = create_app()

with app.app_context():
    # Optional: full reset while you are still developing:
    # db.drop_all()

    db.create_all()

    # ---------- helper ----------

    def get_or_create_user(username, email, role, password):
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            print(f"Created user: {username} / {password} ({role})")
        return user

    # ---------- core admin / hod for demo login ----------

    admin = get_or_create_user(
        "admin", "admin@example.com", User.ROLE_ADMIN, "admin123"
    )
    hod_cse = get_or_create_user(
        "hod_cse", "hod_cse@example.com", User.ROLE_HOD, "hod123"
    )

    db.session.commit()

    # ---------- 25 classrooms ----------

    if Room.query.count() < 25:
        print("Seeding 25 classrooms...")
        rooms = []
        for i in range(1, 26):
            room_name = f"C-{100 + i}"  # C-101 .. C-125
            if not Room.query.filter_by(name=room_name).first():
                rooms.append(
                    Room(
                        name=room_name,
                        capacity=60,
                        room_type="classroom",
                    )
                )
        db.session.add_all(rooms)
        db.session.commit()
        print(f"✅ Total rooms now: {Room.query.count()}")
    else:
        print(f"Rooms already present: {Room.query.count()}")

    # ---------- 4 batches = 1st, 2nd, 3rd, 4th year ----------

    # We'll represent each year by its "current semester":
    #   1st year -> sem 1
    #   2nd year -> sem 3
    #   3rd year -> sem 5
    #   4th year -> sem 7
    #
    # Program: "BTech CSE" for all.

    if Batch.query.count() == 0:
        print("Seeding year-wise batches...")
        batches = [
            Batch(name="CSE-Y1", program="BTech CSE", semester=1, size=125),
            Batch(name="CSE-Y2", program="BTech CSE", semester=3, size=125),
            Batch(name="CSE-Y3", program="BTech CSE", semester=5, size=125),
            Batch(name="CSE-Y4", program="BTech CSE", semester=7, size=125),
        ]
        db.session.add_all(batches)
        db.session.commit()
        print("✅ Batches (years) seeded.")
    else:
        print(f"Found existing batches: {Batch.query.count()} (skipping batch seed)")

    # ---------- subjects per programme/year ----------

    if Subject.query.count() == 0:
        print("Seeding subjects per year (BTech CSE)...")

        subjects_data = [
            # 1st year – Semester 1
            dict(code="CS101", name="Programming Fundamentals", semester=1, classes_per_week=4, is_lab=False),
            dict(code="MA101", name="Engineering Mathematics I", semester=1, classes_per_week=3, is_lab=False),
            dict(code="PH101", name="Engineering Physics", semester=1, classes_per_week=3, is_lab=False),
            dict(code="HS101", name="Communication Skills", semester=1, classes_per_week=2, is_lab=False),

            # 2nd year – Semester 3
            dict(code="CS201", name="Data Structures", semester=3, classes_per_week=4, is_lab=False),
            dict(code="CS202", name="Object Oriented Programming", semester=3, classes_per_week=3, is_lab=False),
            dict(code="MA201", name="Discrete Mathematics", semester=3, classes_per_week=3, is_lab=False),
            dict(code="EC201", name="Digital Logic Design", semester=3, classes_per_week=3, is_lab=False),

            # 3rd year – Semester 5
            dict(code="CS301", name="Database Systems", semester=5, classes_per_week=4, is_lab=False),
            dict(code="CS302", name="Operating Systems", semester=5, classes_per_week=4, is_lab=False),
            dict(code="CS303", name="Computer Networks", semester=5, classes_per_week=3, is_lab=False),
            dict(code="CS304", name="Software Engineering", semester=5, classes_per_week=3, is_lab=False),

            # 4th year – Semester 7
            dict(code="CS401", name="Artificial Intelligence", semester=7, classes_per_week=3, is_lab=False),
            dict(code="CS402", name="Machine Learning", semester=7, classes_per_week=3, is_lab=False),
            dict(code="CS403", name="Distributed Systems", semester=7, classes_per_week=3, is_lab=False),
            dict(code="CS404", name="Major Project", semester=7, classes_per_week=2, is_lab=False),
        ]

        subjects = []
        for s in subjects_data:
            subject = Subject(
                code=s["code"],
                name=s["name"],
                semester=s["semester"],
                classes_per_week=s["classes_per_week"],
                is_lab=s["is_lab"],
            )
            subjects.append(subject)

        db.session.add_all(subjects)
        db.session.commit()
        print(f"✅ Subjects seeded: {Subject.query.count()}")
    else:
        print(f"Subjects already present: {Subject.query.count()}")

    # ---------- 50 teachers (User + Faculty) ----------

    existing_faculty_count = Faculty.query.count()
    if existing_faculty_count < 50:
        print("Seeding faculty users & profiles up to 50...")
        for i in range(1, 51):
            username = f"fac_{i:03d}"
            email = f"{username}@example.com"
            fac_code = f"F{i:03d}"

            user = get_or_create_user(
                username=username,
                email=email,
                role=User.ROLE_FACULTY,
                password="faculty123",
            )
            db.session.flush()

            faculty = Faculty.query.filter_by(code=fac_code).first()
            if not faculty:
                faculty = Faculty(
                    name=f"Faculty {i}",
                    code=fac_code,
                    max_load_per_week=16,
                    user_id=user.id,
                )
                db.session.add(faculty)
        db.session.commit()
        print(f"✅ Total faculty now: {Faculty.query.count()}")
    else:
        print(f"Faculty already present: {existing_faculty_count}")

    # ---------- map faculty to subjects (rough but enough for demo) ----------

    if FacultySubject.query.count() == 0:
        print("Seeding Faculty–Subject mappings...")
        all_subjects = Subject.query.order_by(Subject.semester, Subject.id).all()
        all_faculty = Faculty.query.order_by(Faculty.id).all()

        if all_subjects and all_faculty:
            mappings = []
            # simple round-robin: assign one faculty per subject
            for idx, subject in enumerate(all_subjects):
                fac = all_faculty[idx % len(all_faculty)]
                mappings.append(FacultySubject(faculty_id=fac.id, subject_id=subject.id))

            db.session.add_all(mappings)
            db.session.commit()
            print("✅ Faculty–Subject mappings seeded.")
        else:
            print("⚠️ Not enough faculties or subjects to map.")
    else:
        print("Faculty–Subject mappings already present.")

    # ---------- 500 students (User, role=student) + Student profiles ----------

    current_student_users = User.query.filter_by(role=User.ROLE_STUDENT).count()
    if current_student_users < 500:
        print("Seeding student users up to 500...")
        for i in range(1, 501):
            username = f"stud_{i:03d}"
            email = f"{username}@example.com"
            if not User.query.filter_by(username=username).first():
                get_or_create_user(
                    username=username,
                    email=email,
                    role=User.ROLE_STUDENT,
                    password="student123",
                )
        db.session.commit()
        print(f"✅ Total student users now: {User.query.filter_by(role=User.ROLE_STUDENT).count()}")
    else:
        print(f"Student users already present: {current_student_users}")

    # Now create Student records and distribute across year-batches

    if Student.query.count() == 0:
        print("Creating Student profiles and distributing across batches (years)...")

        student_users = (
            User.query.filter_by(role=User.ROLE_STUDENT)
            .order_by(User.id)
            .all()
        )
        batches = Batch.query.order_by(Batch.semester).all()  # sem 1,3,5,7 order

        if not batches:
            raise RuntimeError("No batches found. Check batch seeding.")

        total_students = len(student_users)
        num_batches = len(batches)
        base_per_batch = total_students // num_batches
        remainder = total_students % num_batches

        idx = 0
        for b_index, batch in enumerate(batches):
            # distribute remainders to first 'remainder' batches
            count_for_this_batch = base_per_batch + (1 if b_index < remainder else 0)
            print(f" - Assigning {count_for_this_batch} students to {batch.name} (Year {b_index+1})")

            for j in range(count_for_this_batch):
                user = student_users[idx]
                idx += 1

                # roll_no pattern: e.g., CSEY1-001
                roll_no = f"{batch.name.replace('-', '')}-{j + 1:03d}"

                student = Student(
                    name=f"Student {user.username.split('_')[-1]}",
                    roll_no=roll_no,
                    user_id=user.id,
                    batch_id=batch.id,
                )
                db.session.add(student)

        db.session.commit()
        print(f"✅ Student profiles created: {Student.query.count()}")
    else:
        print(f"Student profiles already present: {Student.query.count()}")

    # ---------- timeslots (Mon–Fri, 5 per day) ----------

    if Timeslot.query.count() == 0:
        print("Seeding timeslots (Mon–Fri, 5 periods/day)...")
        days = list(range(0, 5))  # 0=Mon .. 4=Fri
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
                timeslots.append(
                    Timeslot(day_of_week=d, start_time=start, end_time=end)
                )

        db.session.add_all(timeslots)
        db.session.commit()
        print("✅ Timeslots seeded.")

    print("🎉 Database seeding complete.")
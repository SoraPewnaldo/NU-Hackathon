# init_db.py  — SMALL DEMO DATASET

from datetime import time, timedelta, datetime

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
    Student,    # <-- make sure you have this model
)

app = create_app()

with app.app_context():
    # While testing, you can uncomment this to hard-reset:
    db.drop_all()

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

    # ---------- 10 rooms ----------

    if Room.query.count() < 10:
        print("Seeding 10 rooms...")
        rooms = []
        for i in range(1, 11):
            room_name = f"R-{100 + i}"  # R-101 .. R-110
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

    # ---------- 4 year batches (1st–4th year) ----------

    # Each batch has a "current semester":
    #   Year 1 → sem 1 (odd)
    #   Year 2 → sem 3 (odd)
    #   Year 3 → sem 5 (odd)
    #   Year 4 → sem 7 (odd)
    #
    # You can later change 1→2, 3→4, 5→6, 7→8 to test even sem.

    if Batch.query.count() == 0:
        print("Seeding year-wise batches...")
        batches = [
            Batch(name="CSE-Y1", program="BTech CSE", year=1, section="A"),
            Batch(name="CSE-Y2", program="BTech CSE", year=2, section="A"),
            Batch(name="CSE-Y3", program="BTech CSE", year=3, section="A"),
            Batch(name="CSE-Y4", program="BTech CSE", year=4, section="A"),
        ]
        db.session.add_all(batches)
        db.session.commit()
        print("✅ Batches (years) seeded.")
    else:
        print(f"Found existing batches: {Batch.query.count()} (skipping batch seed)")

    # ---------- subjects for ALL 8 semesters ----------

    # 20 subjects total, spread across 8 sems.
    # You can treat "odd sem" = semester % 2 == 1, "even sem" = semester % 2 == 0

    if Subject.query.count() == 0:
        print("Seeding subjects for 8 semesters (BTech CSE)...")

        subjects_data = [
            # Sem 1 (odd)
            dict(code="CS101", name="Programming Fundamentals", semester=1, classes_per_week=4),
            dict(code="MA101", name="Engineering Mathematics I", semester=1, classes_per_week=3),
            dict(code="PH101", name="Engineering Physics", semester=1, classes_per_week=3),

            # Sem 2 (even)
            dict(code="CS102", name="Structured Programming in C", semester=2, classes_per_week=4),
            dict(code="MA102", name="Engineering Mathematics II", semester=2, classes_per_week=3),

            # Sem 3 (odd)
            dict(code="CS201", name="Object Oriented Programming", semester=3, classes_per_week=4),
            dict(code="MA201", name="Discrete Mathematics", semester=3, classes_per_week=3),
            dict(code="EC201", name="Digital Logic Design", semester=3, classes_per_week=3),

            # Sem 4 (even)
            dict(code="CS202", name="Data Structures and Algorithms", semester=4, classes_per_week=4),
            dict(code="CS204", name="Computer Organization", semester=4, classes_per_week=3),

            # Sem 5 (odd)
            dict(code="CS301", name="Database Systems", semester=5, classes_per_week=4),
            dict(code="CS302", name="Operating Systems", semester=5, classes_per_week=4),
            dict(code="CS303", name="Computer Networks", semester=5, classes_per_week=3),

            # Sem 6 (even)
            dict(code="CS304", name="Software Engineering", semester=6, classes_per_week=3),
            dict(code="CS305", name="Web Technologies", semester=6, classes_per_week=3),

            # Sem 7 (odd)
            dict(code="CS401", name="Artificial Intelligence", semester=7, classes_per_week=3),
            dict(code="CS402", name="Distributed Systems", semester=7, classes_per_week=3),
            dict(code="CS403", name="Compiler Design", semester=7, classes_per_week=3),

            # Sem 8 (even)
            dict(code="CS404", name="Machine Learning", semester=8, classes_per_week=3),
            dict(code="CS405", name="Project / Internship", semester=8, classes_per_week=2),
        ]

        subjects = []
        for s in subjects_data:
            subject = Subject(
                code=s["code"],
                name=s["name"],
                semester=s["semester"],
                classes_per_week=s["classes_per_week"],
                is_lab=False,
            )
            subjects.append(subject)

        db.session.add_all(subjects)
        db.session.commit()
        print(f"✅ Subjects seeded: {Subject.query.count()}")
    else:
        print(f"Subjects already present: {Subject.query.count()}")

    # Get all subjects in a stable order
    all_subjects = Subject.query.order_by(Subject.semester, Subject.code).all()
    num_subjects = len(all_subjects)
    print(f"Found {num_subjects} subjects.")

    # ---------- faculty: 1 teacher per subject ----------

    existing_faculty_count = Faculty.query.count()
    if existing_faculty_count < num_subjects:
        print(f"Seeding {num_subjects} faculty users & profiles (1 per subject)...")

        for i, subject in enumerate(all_subjects, start=1):
            username = f"fac_{i:03d}"
            email = f"{username}@example.com"
            fac_code = f"F{i:03d}"

            # Create faculty user
            user = get_or_create_user(
                username=username,
                email=email,
                role=User.ROLE_FACULTY,
                password="faculty123",  # same password for all demo faculty
            )
            db.session.flush()

            # Human-readable name that also tells you what they teach
            display_name = f"{subject.name} Teacher"

            faculty = Faculty.query.filter_by(code=fac_code).first()
            if not faculty:
                faculty = Faculty(
                    name=display_name,
                    code=fac_code,
                    max_load_per_week=12,
                    user_id=user.id,
                )
                db.session.add(faculty)

        db.session.commit()
        print(f"✅ Total faculty now: {Faculty.query.count()}")
    else:
        print(f"Faculty already present: {existing_faculty_count}")

    # ---------- 1:1 Faculty–Subject mappings ----------

    if FacultySubject.query.count() == 0:
        print("Creating 1:1 Faculty–Subject mappings...")

        # make sure we have them in the same order
        all_subjects = Subject.query.order_by(Subject.semester, Subject.code).all()
        all_faculty = Faculty.query.order_by(Faculty.id).all()

        if len(all_faculty) < len(all_subjects):
            print("⚠️ Not enough faculty for each subject. Check faculty seeding.")
        else:
            mappings = []
            for idx, subject in enumerate(all_subjects):
                faculty = all_faculty[idx]  # 1:1
                mappings.append(
                    FacultySubject(
                        faculty_id=faculty.id,
                        subject_id=subject.id,
                    )
                )
                print(f" - {faculty.name} assigned to {subject.code} ({subject.name})")

            db.session.add_all(mappings)
            db.session.commit()
            print("✅ 1:1 Faculty–Subject mappings created.")
    else:
        print("Faculty–Subject mappings already present.")

    # ---------- student users + Student profiles ----------

    # Small dataset: 80 students total, 20 per year-batch
    target_students_per_batch = 20

    current_student_users = User.query.filter_by(role=User.ROLE_STUDENT).count()
    total_target_students = target_students_per_batch * 4  # 4 batches

    if current_student_users < total_target_students:
        print(f"Seeding {total_target_students} student users...")
        for i in range(1, total_target_students + 1):
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

    # Create Student records and distribute across year-batches

    if Student.query.count() == 0:
        print("Creating Student profiles and distributing across batches (years)...")

        student_users = (
            User.query.filter_by(role=User.ROLE_STUDENT)
            .order_by(User.id)
            .limit(total_target_students)
            .all()
        )
        batches = Batch.query.order_by(Batch.year).all()  # Y1:Y4 -> year 1,2,3,4

        if len(batches) != 4:
            raise RuntimeError("Expected exactly 4 batches for 4 years.")

        idx = 0
        for b_index, batch in enumerate(batches):
            print(f" - Assigning {target_students_per_batch} students to {batch.name}")

            for j in range(target_students_per_batch):
                if idx >= len(student_users):
                    break
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
                user.batch_id = batch.id # Assign batch_id to the User object

        db.session.commit()
        print(f"✅ Student profiles created: {Student.query.count()}")
    else:
        print(f"Student profiles already present: {Student.query.count()}")

    # ---------- timeslots (Mon–Fri, 5 per day) ----------

    if Timeslot.query.count() == 0:
        days = list(range(0, 5))  # 0=Mon ... 4=Fri

        # 1-hour periods from 8:30 to 17:30
        start_hour = 8
        start_minute = 30
        end_hour = 17
        end_minute = 30

        timeslots = []

        for d in days:
            current = datetime(2000, 1, 1, start_hour, start_minute)  # dummy date
            end_day = datetime(2000, 1, 1, end_hour, end_minute)

            while current < end_day:
                start_t = current.time()
                end_t = (current + timedelta(hours=1)).time()

                ts = Timeslot(
                    day_of_week=d,
                    start_time=start_t,
                    end_time=end_t,
                )
                timeslots.append(ts)
                current += timedelta(hours=1)

        db.session.add_all(timeslots)
        db.session.commit()
        print("Seeded timeslots (Mon–Fri, 8:30–17:30, 1-hour slots).")

    print("🎉 SMALL demo database seeding complete.")

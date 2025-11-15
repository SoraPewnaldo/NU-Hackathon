# Project Codebase Summary

This document provides a comprehensive overview of the project's codebase, outlining its architecture, key components, and their functionalities. The project is a web-based timetable management system built using the Flask framework, SQLAlchemy ORM for database interactions, and Jinja2 for templating.

## 1. Core Application Structure

*   **`run.py`**: This is the entry point of the Flask application. It initializes the Flask app and runs the development server.
*   **`config.py`**: Contains configuration settings for the Flask application, such as database URI, secret key, and other environment-specific variables.
*   **`init_db.py`**: A standalone script responsible for initializing the SQLite database (`instance/timetable.db`), creating all necessary tables based on SQLAlchemy models, and populating them with initial demo data (users, rooms, batches, subjects, faculty, students, timeslots).

## 2. `app/` Package - Main Flask Application

This directory contains the core logic and components of the Flask application.

### 2.1. `app/__init__.py`

*   Initializes the Flask application instance.
*   Configures the application using settings from `config.py`.
*   Initializes SQLAlchemy (`db`) for database management.
*   Initializes Flask-Login (`login_manager`) for user authentication.
*   Registers blueprints (e.g., `main` blueprint for routes).

### 2.2. `app/models.py`

This file defines the SQLAlchemy ORM models, representing the database schema.

*   **`User`**: Manages user authentication and roles (admin, HOD, faculty, student). Includes methods for password hashing and checking, and role-based checks. Now includes a `batch_id` to directly link student users to their batches.
*   **`Room`**: Represents physical classrooms or labs with properties like name, capacity, and type.
*   **`Batch`**: Defines academic batches (e.g., "CSE-Y1") with program, year, and section details.
*   **`Subject`**: Stores information about academic subjects, including code, name, semester, and classes per week.
*   **`Faculty`**: Represents faculty members, linked to a `User` account, with details like name, code, and maximum teaching load.
*   **`Student`**: Represents student profiles, linked to a `User` account and a `Batch`, with roll number and name.
*   **`Timeslot`**: Defines available time slots for classes, including day of the week, start time, and end time.
*   **`FacultySubject`**: A many-to-many relationship table linking faculty members to the subjects they can teach.
*   **`FacultyUnavailableSlot`**: Stores faculty preferences for unavailable time slots.
*   **`Timetable`**: Represents a generated timetable instance, with a name, creation timestamp, and status.
*   **`TimetableEntry`**: The core of the timetable, linking a specific `Timetable`, `Batch`, `Subject`, `Faculty`, `Room`, and `Timeslot`.

### 2.3. `app/routes.py`

This file defines all the URL routes and their corresponding view functions, handling requests and rendering templates.

*   **Authentication Routes**: `/`, `/login`, `/logout` for user authentication and session management.
*   **Role-Based Dashboard Redirection**: The `/dashboard` route redirects users to their specific dashboard based on their role (`admin_dashboard`, `hod_dashboard`, `faculty_dashboard`, `student_dashboard`).
*   **Admin Routes**:
    *   `/admin/dashboard`: Displays the admin overview, including metrics and quick actions.
    *   `/admin/batches`, `/admin/batches/add`, `/admin/batches/<int:batch_id>/delete`: CRUD operations for managing academic batches.
    *   `/admin/faculty`, `/admin/faculty/<int:faculty_id>/edit`, `/admin/faculty/<int:faculty_id>/delete`: CRUD operations for managing faculty members.
    *   `/admin/generate_timetable`: Triggers the timetable generation process.
*   **HOD Routes**: `/hod/dashboard`: Displays the Head of Department dashboard.
*   **Faculty Routes**:
    *   `/faculty/dashboard`: Displays the faculty member's personal timetable.
    *   `/faculty/preferences`: Allows faculty to set their unavailable time slots.
*   **Student Routes**:
    *   `/student/dashboard`: Displays the student's personal timetable based on their linked batch.
    *   `/student/batch_timetable`: Allows students (or admin/HOD) to view timetables for specific batches.
*   **General Timetable Views**: `/timetables` (list all) and `/timetable/<int:timetable_id>` (view specific).
*   **Helper Functions**: `roles_required` decorator for role-based access control, `build_periods` and `build_grid_for_entries` for structuring timetable data for display.

### 2.4. `app/scheduler.py`

*   Contains the core logic for generating timetables.
*   Utilizes the OR-Tools CP-SAT solver to solve the complex constraint satisfaction problem of timetable generation.
*   Defines various constraints such as faculty availability, room capacity, subject classes per week, and lunch breaks.
*   The `generate_timetable` function orchestrates the solver, creates `Timetable` and `TimetableEntry` records, and persists them to the database.

### 2.5. `app/static/`

*   **`app/static/css/style.css`**: Contains custom CSS rules for styling the application's user interface, including layout, component styling, and specific timetable grid aesthetics (e.g., colored text for timetable entries, period numbers).

### 2.6. `app/templates/`

This directory holds all the Jinja2 HTML templates used for rendering the web pages.

*   **`base.html`**: The base template that all other templates extend. It defines the common structure, including the sidebar navigation, top bar, and content area, ensuring a consistent look and feel across the application.
*   **`landing.html`**: The initial page displayed to unauthenticated users.
*   **`login.html`**: The user login form.
*   **`dashboard.html`**: A simple template that acts as a redirector to the appropriate role-based dashboard.
*   **`admin_dashboard.html`**: Admin-specific dashboard displaying key metrics and quick action links.
*   **`hod_dashboard.html`**: Head of Department dashboard.
*   **`faculty_dashboard.html`**: Faculty-specific dashboard displaying their assigned timetable.
*   **`student_dashboard.html`**: Student-specific dashboard displaying their batch's timetable in a structured grid format.
*   **`admin_manage_faculty.html`**: Template for the admin interface to list, add, and manage faculty members.
*   **`admin_edit_faculty.html`**: Template for the admin interface to edit details of a specific faculty member.
*   **`admin_batches.html`**: Template for the admin interface to manage academic batches.
*   **`timetable_list.html`**: Displays a list of all generated timetables.
*   **`timetable_view.html`**: Displays a detailed view of a specific timetable.
*   **`faculty_preferences.html`**: Interface for faculty members to set their unavailable time slots.
*   **`student_batch_timetable.html`**: Allows students to select a batch and view its timetable.

## 3. `instance/`

*   **`instance/timetable.db`**: The SQLite database file where all application data is stored.

## Conclusion

The project provides a robust framework for managing academic timetables, offering distinct interfaces and functionalities for administrators, HODs, faculty, and students. It leverages Flask's modularity, SQLAlchemy's ORM capabilities, and OR-Tools for complex scheduling, all presented through a responsive and user-friendly interface.

---

# Full Code Listing

## `run.py`
```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
```

## `config.py`
```python

```

## `init_db.py`
```python
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
```

## `app/__init__.py`
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # BASIC CONFIG
    app.config['SECRET_KEY'] = 'supersecretkey'  # change later if you want
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetable.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # INIT EXTENSIONS
    db.init_app(app)
    login_manager.init_app(app)

    # Where to redirect if user is not logged in
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'warning'

    # Import and register routes
    from .routes import main
    app.register_blueprint(main)

    return app
```

## `app/models.py`
```python
from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --------------------
# USER & AUTH
# --------------------
class User(UserMixin, db.Model):
    __tablename__ = "user"

    # ---- ROLE CONSTANTS ----
    ROLE_ADMIN = "admin"
    ROLE_HOD = "hod"            # department head
    ROLE_FACULTY = "faculty"
    ROLE_STUDENT = "student"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # default = faculty so normal users become faculty by default
    role = db.Column(db.String(20), default=ROLE_FACULTY, nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("batch.id"), nullable=True)
    batch = db.relationship("Batch", backref="students")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ---- HELPER METHODS ----
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_hod(self):
        return self.role == self.ROLE_HOD

    def is_faculty(self):
        return self.role == self.ROLE_FACULTY

    def is_student(self):
        return self.role == self.ROLE_STUDENT

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# --------------------
# CORE ACADEMIC ENTITIES
# --------------------
class Room(db.Model):
    __tablename__ = "room"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # e.g. C-301
    capacity = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(32), default="classroom")  # classroom/lab/seminar

    def __repr__(self):
        return f"<Room {self.name} cap={self.capacity}>"


class Batch(db.Model):
    __tablename__ = "batch"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)          # e.g. "CSE-Y1"
    program = db.Column(db.String(100), nullable=False)      # e.g. "B.Tech CSE"
    year = db.Column(db.Integer, nullable=False)             # 1,2,3,4
    section = db.Column(db.String(10), nullable=True)        # e.g. "A"
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Batch {self.name}>"


class Subject(db.Model):
    __tablename__ = "subject"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False)  # e.g. CS201
    name = db.Column(db.String(128), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    classes_per_week = db.Column(db.Integer, nullable=False)  # how many slots per week
    is_lab = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Subject {self.code} {self.name}>"


class Faculty(db.Model):
    __tablename__ = "faculty"

    id = db.Column(db.Integer, primary_key=True)
    # Optional link to User for login
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(32), unique=True, nullable=False)  # e.g. F001
    max_load_per_week = db.Column(db.Integer, default=16)

    user = db.relationship("User", backref=db.backref("faculty_profile", uselist=False))

    def __repr__(self):
        return f"<Faculty {self.code} {self.name}>"


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("batch.id"), nullable=False)

    # relationships
    user = db.relationship("User", backref=db.backref("student_profile", uselist=False))
    batch = db.relationship("Batch")

    def __repr__(self):
        return f"<Student {self.roll_no} - {self.name}>"


# --------------------
# TIMESLOTS
# --------------------
class Timeslot(db.Model):
    __tablename__ = "timeslot"

    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Mon ... 6=Sun
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f"<Timeslot day={self.day_of_week} {self.start_time}-{self.end_time}>"


# --------------------
# FACULTY-SUBJECT MAPPING
# --------------------
class FacultySubject(db.Model):
    __tablename__ = "faculty_subject"

    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)

    faculty = db.relationship("Faculty", backref=db.backref("faculty_subjects", lazy="dynamic"))
    subject = db.relationship("Subject", backref=db.backref("subject_faculties", lazy="dynamic"))

    def __repr__(self):
        return f"<FacultySubject faculty={self.faculty_id} subject={self.subject_id}>"


class FacultyUnavailableSlot(db.Model):
    __tablename__ = "faculty_unavailable_slot"

    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    timeslot_id = db.Column(db.Integer, db.ForeignKey("timeslot.id"), nullable=False)

    faculty = db.relationship("Faculty", backref=db.backref("unavailable_slots", lazy="dynamic"))
    timeslot = db.relationship("Timeslot", backref=db.backref("unavailable_for", lazy="dynamic"))

    def __repr__(self):
        return f"<FacultyUnavailableSlot faculty={self.faculty_id} slot={self.timeslot_id}>"


# --------------------
# TIMETABLE & ENTRIES
# --------------------
class Timetable(db.Model):
    __tablename__ = "timetable"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)  # e.g. "CSE Sem4 v1"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), default="generated")  # generated/final/archived

    entries = db.relationship(
        "TimetableEntry",
        backref="timetable",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Timetable {self.name} id={self.id}>"


class TimetableEntry(db.Model):
    __tablename__ = "timetable_entry"

    id = db.Column(db.Integer, primary_key=True)

    timetable_id = db.Column(db.Integer, db.ForeignKey("timetable.id"), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("batch.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    timeslot_id = db.Column(db.Integer, db.ForeignKey("timeslot.id"), nullable=False)

    batch = db.relationship("Batch", backref=db.backref("timetable_entries", lazy="dynamic", cascade="all, delete-orphan"))
    subject = db.relationship("Subject", backref=db.backref("timetable_entries", lazy="dynamic"))
    faculty = db.relationship("Faculty", backref=db.backref("timetable_entries", lazy="dynamic"))
    room = db.relationship("Room", backref=db.backref("timetable_entries", lazy="dynamic"))
    timeslot = db.relationship("Timeslot", backref=db.backref("timetable_entries", lazy="dynamic"))

    def __repr__(self):
        return (
            f"<Entry tt={self.timetable_id} batch={self.batch_id} "
            f"sub={self.subject_id} fac={self.faculty_id} room={self.room_id} slot={self.timeslot_id}>"
        )
```

## `app/routes.py`
```python
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps

from .models import (
    User,
    Timetable,
    TimetableEntry,
    Timeslot,
    Batch,
    Subject,
    Room,
    Faculty,
    FacultyUnavailableSlot,
    FacultySubject,
)
from . import db
from .scheduler import generate_timetable

main = Blueprint("main", __name__)

def roles_required(*roles):
    """
    Usage:
        @roles_required("admin")
        @roles_required("admin", "hod")
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.login"))
            if current_user.role not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("main.dashboard"))
            return view_func(*args, **kwargs)
        return wrapper
    return decorator

@main.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username_or_email = request.form.get("username")
        password = request.form.get("password")

        # Allow login via username OR email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        else:
            flash("Invalid credentials.", "danger")

    return render_template("login.html")

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))

@main.route("/dashboard")
@login_required
def dashboard():
    # Central router based on role
    if current_user.is_admin():
        return redirect(url_for("main.admin_dashboard"))
    elif current_user.is_hod():
        return redirect(url_for("main.hod_dashboard"))
    elif current_user.is_faculty():
        return redirect(url_for("main.faculty_dashboard"))
    elif current_user.is_student():
        return redirect(url_for("main.student_dashboard"))
    else:
        flash("Unknown role, contact administrator.", "danger")
        return redirect(url_for("main.logout"))


@main.route("/admin/dashboard")
@login_required
@roles_required("admin")
def admin_dashboard():
    latest_tt = Timetable.query.order_by(Timetable.created_at.desc()).first()
    
    periods = build_periods()
    grid = {}
    has_timetable = False

    if latest_tt:
        entries = (
            TimetableEntry.query
            .filter_by(timetable_id=latest_tt.id)
            .join(Timeslot)
            .order_by(Timeslot.day_of_week, Timeslot.start_time)
            .all()
        )
        grid = build_grid_for_entries(entries, periods)
        has_timetable = True

    return render_template(
        "admin_dashboard.html",
        user=current_user,
        latest_tt=latest_tt,
        has_timetable=has_timetable,
        days=DAYS,
        periods=periods,
        grid=grid,
    )


# -------------------------
# ADMIN – MANAGE FACULTY
# -------------------------

@main.route("/admin/faculty", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def admin_manage_faculty():
    # Handle simple "Add Faculty" in same page
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        max_load = request.form.get("max_load_per_week", "").strip()
        user_id = request.form.get("user_id")  # optional link to User

        if not name or not code:
            flash("Name and code are required.", "danger")
        else:
            # Basic uniqueness check for code
            existing = Faculty.query.filter_by(code=code).first()
            if existing:
                flash("Faculty code already exists.", "danger")
            else:
                try:
                    max_load_val = int(max_load) if max_load else 16
                except ValueError:
                    max_load_val = 16

                faculty = Faculty(
                    name=name,
                    code=code,
                    max_load_per_week=max_load_val,
                    user_id=int(user_id) if user_id else None,
                )
                db.session.add(faculty)
                db.session.commit()
                flash("Faculty added successfully.", "success")
                return redirect(url_for("main.admin_manage_faculty"))

    faculties = Faculty.query.order_by(Faculty.code).all()
    users = User.query.order_by(User.username).all()

    return render_template(
        "admin_manage_faculty.html",
        user=current_user,
        faculties=faculties,
        users=users,
    )


@main.route("/admin/faculty/<int:faculty_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def admin_edit_faculty(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    users = User.query.order_by(User.username).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        max_load = request.form.get("max_load_per_week", "").strip()
        user_id = request.form.get("user_id")

        if not name or not code:
            flash("Name and code are required.", "danger")
        else:
            # Check code uniqueness for others
            existing = Faculty.query.filter(
                Faculty.code == code,
                Faculty.id != faculty.id
            ).first()
            if existing:
                flash("Another faculty already uses this code.", "danger")
            else:
                faculty.name = name
                faculty.code = code
                try:
                    faculty.max_load_per_week = int(max_load) if max_load else 16
                except ValueError:
                    pass
                faculty.user_id = int(user_id) if user_id else None

                db.session.commit()
                flash("Faculty updated.", "success")
                return redirect(url_for("main.admin_manage_faculty"))

    return render_template(
        "admin_edit_faculty.html",
        user=current_user,
        faculty=faculty,
        users=users,
    )


@main.route("/admin/faculty/<int:faculty_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def admin_delete_faculty(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)

    # TODO: in the future check if faculty has timetable entries etc.
    db.session.delete(faculty)
    db.session.commit()
    flash("Faculty deleted.", "info")
    return redirect(url_for("main.admin_manage_faculty"))


@main.route("/admin/batches")
@login_required
def admin_batches():
    # You can filter by department / role later
    batches = Batch.query.order_by(Batch.year.asc(), Batch.name.asc()).all()
    return render_template("admin_batches.html", batches=batches)


@main.route("/admin/batches/add", methods=["POST"])
@login_required
def admin_add_batch():
    name = request.form.get("name")
    program = request.form.get("program")
    year = request.form.get("year", type=int)
    section = request.form.get("section")

    if not name or not program or not year:
        flash("Name, program, and year are required.", "danger")
        return redirect(url_for("main.admin_batches"))

    batch = Batch(name=name, program=program, year=year, section=section or None)
    db.session.add(batch)
    db.session.commit()
    flash("Batch added successfully.", "success")
    return redirect(url_for("main.admin_batches"))


@main.route("/admin/batches/<int:batch_id>/delete", methods=["POST"])
@login_required
def admin_delete_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    db.session.delete(batch)
    db.session.commit()
    flash("Batch deleted.", "success")
    return redirect(url_for("main.admin_batches"))


@main.route("/hod/dashboard")
@login_required
@roles_required("admin", "hod")   # admin can also see HOD view if you want
def hod_dashboard():
    return render_template("hod_dashboard.html", user=current_user)


@main.route("/faculty/dashboard")
@login_required
@roles_required("faculty", "hod", "admin")


def faculty_dashboard():


    # 1) Find the Faculty row for this logged-in user


    faculty = Faculty.query.filter_by(user_id=current_user.id).first()





    latest_tt = Timetable.query.order_by(Timetable.created_at.desc()).first()





    # If no faculty record or no timetable → show empty grid + message


    if not latest_tt or not faculty:


        if not faculty:


            flash("Your user is not linked to any Faculty record (user_id).", "warning")


        elif not latest_tt:


            flash("No timetable has been generated yet.", "warning")





        return render_template(


            "faculty_dashboard.html",


            user=current_user,


            days=[],


            periods=[],


            grid={},


        )





    # 2) All timeslots


    all_slots = Timeslot.query.order_by(


        Timeslot.day_of_week,


        Timeslot.start_time


    ).all()





    # Unique periods (columns)


    periods = []


    for ts in all_slots:


        key = (ts.start_time, ts.end_time)


        if key not in periods:


            periods.append(key)





    # Day indices + labels (rows)


    days = [


        (0, "MON"),


        (1, "TUE"),


        (2, "WED"),


        (3, "THU"),


        (4, "FRI"),


        (5, "SAT"),


    ]





    # 3) Get all entries for THIS faculty in the latest timetable


    entries = (


        TimetableEntry.query


        .filter_by(timetable_id=latest_tt.id, faculty_id=faculty.id)


        .all()


    )





    # 4) Build grid: (day_index, period_index) -> entry


    grid = {}


    for e in entries:


        ts = e.timeslot


        key = (ts.start_time, ts.end_time)


        if key not in periods:


            continue


        p_idx = periods.index(key)


        d_idx = ts.day_of_week


        grid[(d_idx, p_idx)] = e





    # If entries is empty, we’ll show all "No Class" – which might be correct


    if not entries:


        flash(


            f"No classes assigned to you in timetable #{latest_tt.id}. "


            "Check FacultySubject mapping & scheduler.",


            "info",


        )





    return render_template(


        "faculty_dashboard.html",


        user=current_user,


        days=days,


        periods=periods,


        grid=grid,


    )


@main.route("/student/dashboard")
@login_required
@roles_required("student", "admin")
def student_dashboard():
    # Student → Batch mapping (assumes User has batch_id)
    student_batch = None
    if hasattr(current_user, "batch_id") and current_user.batch_id:
        student_batch = Batch.query.get(current_user.batch_id)

    latest_tt = Timetable.query.order_by(Timetable.created_at.desc()).first()

    if not latest_tt or not student_batch:
        return render_template(
            "student_dashboard.html",
            user=current_user,
            batch=student_batch,
            days=[],
            periods=[],
            grid={},
        )

    all_slots = Timeslot.query.order_by(
        Timeslot.day_of_week,
        Timeslot.start_time
    ).all()

    # Unique periods across all days
    periods = []
    for ts in all_slots:
        key = (ts.start_time, ts.end_time)
        if key not in periods:
            periods.append(key)

    days = [
        (0, "MON"),
        (1, "TUE"),
        (2, "WED"),
        (3, "THU"),
        (4, "FRI"),
        (5, "SAT"),
    ]

    # Build grid for this batch
    entries = (
        TimetableEntry.query
        .filter_by(timetable_id=latest_tt.id, batch_id=student_batch.id)
        .all()
    )

    grid = {}
    for e in entries:
        ts = e.timeslot
        key = (ts.start_time, ts.end_time)
        if key not in periods:
            continue
        p_idx = periods.index(key)
        d_idx = ts.day_of_week
        grid[(d_idx, p_idx)] = e

    return render_template(
        "student_dashboard.html",
        user=current_user,
        batch=student_batch,
        days=days,
        periods=periods,
        grid=grid,
    )

@main.route("/admin/generate_timetable", methods=["GET"])
@login_required
@roles_required("admin")
def admin_generate_timetable():
    tt = generate_timetable("Admin Generated Timetable")

    if tt is None:
        flash("Failed to generate timetable. Check data and constraints.", "danger")
    else:
        flash(f"Timetable #{tt.id} generated with {tt.entries.count()} entries.", "success")

    return redirect(url_for("main.admin_dashboard"))


@main.route("/timetable/<int:timetable_id>")
@login_required
def view_timetable(timetable_id):
    # 1) Get timetable or 404
    timetable = Timetable.query.get_or_404(timetable_id)

    # 2) Get all timeslots, ordered by day + time
    all_slots = Timeslot.query.order_by(
        Timeslot.day_of_week, Timeslot.start_time
    ).all()
    if not all_slots:
        flash("No timeslots defined yet.", "warning")
        return render_template("timetable_view.html",
                               timetable=timetable,
                               days=[],
                               periods=[],
                               grid={})

    # 3) Build unique period list (same time ranges for all days)
    period_keys = []
    for ts in all_slots:
        key = (ts.start_time, ts.end_time)
        if key not in period_keys:
            period_keys.append(key)

    # 4) Day index + label mapping
    days = [
        (0, "MON"),
        (1, "TUE"),
        (2, "WED"),
        (3, "THU"),
        (4, "FRI"),
        (5, "SAT"),
    ]

    # 5) Map (day_index, period_index) -> Timeslot.id
    slot_id_by_day_period = {}
    for day_index, _ in days:
        for p_idx, (start, end) in enumerate(period_keys):
            ts = next(
                (
                    t for t in all_slots
                    if t.day_of_week == day_index
                    and t.start_time == start
                    and t.end_time == end
                ),
                None,
            )
            if ts:
                slot_id_by_day_period[(day_index, p_idx)] = ts.id

    # 6) Load all entries for this timetable
    entries = TimetableEntry.query.filter_by(timetable_id=timetable_id).all()

    # 7) Build grid: (day_index, period_index) -> entry
    grid = {}
    for e in entries:
        ts = e.timeslot
        key = (ts.start_time, ts.end_time)
        if key not in period_keys:
            continue
        p_idx = period_keys.index(key)
        grid[(ts.day_of_week, p_idx)] = e

    return render_template(
        "timetable_view.html",
        timetable=timetable,
        days=days,
        periods=period_keys,
        grid=grid,
    )

@main.route("/timetables")
@login_required
@roles_required("admin", "hod", "faculty", "student")
def list_timetables():
    timetables = Timetable.query.order_by(Timetable.created_at.desc()).all()
    return render_template("timetable_list.html", timetables=timetables)



@main.route("/students")
@login_required
@roles_required("admin", "hod")
def view_students():
    flash("Students page is under construction.", "info")
    return redirect(url_for("main.admin_dashboard"))



@main.route("/subjects")
@login_required
@roles_required("admin", "hod")
def view_subjects():
    flash("Subjects page is under construction.", "info")
    return redirect(url_for("main.admin_dashboard"))

@main.route("/rooms")
@login_required
@roles_required("admin", "hod")
def view_rooms():
    flash("Rooms page is under construction.", "info")
    return redirect(url_for("main.admin_dashboard"))

@main.route("/timeslots")
@login_required
@roles_required("admin", "hod")
def view_timeslots():
    flash("Timeslots page is under construction.", "info")
    return redirect(url_for("main.admin_dashboard"))

@main.route("/settings")
@login_required
@roles_required("admin")
def settings():
    flash("Settings page is under construction.", "info")
    return redirect(url_for("main.admin_dashboard"))

@main.route("/student/batch_timetable", methods=["GET", "POST"])
@login_required
@roles_required("student", "hod", "admin")
def student_batch_timetable():
    tt = Timetable.query.order_by(Timetable.created_at.desc()).first()
    if tt is None:
        flash("No timetable generated yet.", "warning")
        return redirect(url_for("main.dashboard"))

    batches = Batch.query.order_by(Batch.name).all()
    periods = build_periods()
    grid = {}
    selected_batch_id = None
    has_timetable = False

    if request.method == "POST":
        selected_batch_id = int(request.form.get("batch_id"))
        entries = (
            TimetableEntry.query
            .filter_by(timetable_id=tt.id, batch_id=selected_batch_id)
            .join(Timeslot)
            .order_by(Timeslot.day_of_week, Timeslot.start_time)
            .all()
        )
        grid = build_grid_for_entries(entries, periods)
        has_timetable = True

    return render_template(
        "student_batch_timetable.html",
        timetable=tt,
        batches=batches,
        selected_batch_id=selected_batch_id,
        has_timetable=has_timetable,
        days=DAYS,
        periods=periods,
        grid=grid,
    )

@main.route("/faculty/preferences", methods=["GET", "POST"])
@login_required
@roles_required("faculty", "hod", "admin")  # HOD/admin can test, but main target is faculty
def faculty_preferences():
    # Get faculty profile linked to logged-in user
    fac = current_user.faculty_profile
    if fac is None:
        flash("No faculty profile linked to this user.", "danger")
        return redirect(url_for("main.dashboard"))

    # All timeslots in order
    timeslots = Timeslot.query.order_by(
        Timeslot.day_of_week, Timeslot.start_time
    ).all()
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    if request.method == "POST":
        # Get list of timeslot IDs that the user marked as UNAVAILABLE
        selected_ids = request.form.getlist("unavailable_slots")
        selected_ids = set(int(x) for x in selected_ids)

        # Delete old preferences
        FacultyUnavailableSlot.query.filter_by(faculty_id=fac.id).delete()

        # Insert new ones
        for ts_id in selected_ids:
            db.session.add(FacultyUnavailableSlot(faculty_id=fac.id, timeslot_id=ts_id))

        db.session.commit()
        flash("Preferences saved.", "success")
        return redirect(url_for("main.faculty_preferences"))

    # For GET: load existing unavailable slots to pre-check in form
    existing = FacultyUnavailableSlot.query.filter_by(faculty_id=fac.id).all()
    unavailable_ids = {u.timeslot_id for u in existing}

    return render_template(
        "faculty_preferences.html",
        faculty=fac,
        timeslots=timeslots,
        unavailable_ids=unavailable_ids,
        day_names=day_names,
    )


from .models import Timetable, TimetableEntry, Timeslot, Batch, Faculty
from datetime import datetime, time as dtime

DAYS = [
    {"index": 0, "label": "MON"},
    {"index": 1, "label": "TUE"},
    {"index": 2, "label": "WED"},
    {"index": 3, "label": "THU"},
    {"index": 4, "label": "FRI"},
]

def build_periods():
    """Build period list from Monday's timeslots (assuming all days share same time grid)."""
    slots = (
        Timeslot.query
        .filter_by(day_of_week=0)
        .order_by(Timeslot.start_time)
        .all()
    )
    periods = []
    for i, ts in enumerate(slots, start=1):
        label = f"{ts.start_time.strftime('%H:%M')} - {ts.end_time.strftime('%H:%M')}"
        periods.append(
            {
                "index": i,
                "label": label,
                "start_time": ts.start_time,
            }
        )
    return periods

def build_grid_for_entries(entries, periods):
    """entries = list of TimetableEntry (already filtered for a faculty/batch/etc)"""
    # map (day, start_time) -> period_index
    period_index_by_time = {}
    for p in periods:
        period_index_by_time[p["start_time"]] = p["index"]

    # init empty grid
    grid = {d["index"]: {p["index"]: [] for p in periods} for d in DAYS}

    for e in entries:
        ts = e.timeslot
        day_idx = ts.day_of_week
        p_idx = period_index_by_time.get(ts.start_time)
        if p_idx is None or day_idx not in grid:
            continue
        grid[day_idx][p_idx].append(e)

    return grid
```

## `app/scheduler.py`
```python
from ortools.sat.python import cp_model
from flask import current_app
from datetime import time
from .models import (
    Room,
    Batch,
    Subject,
    Faculty,
    Timeslot,
    Timetable,
    TimetableEntry,
    FacultySubject,
    FacultyUnavailableSlot,
)
from . import db


def generate_timetable(name: str = "Auto Generated Timetable"):
    """
    Build and solve a basic timetable using OR-Tools CP-SAT.
    Returns the created Timetable instance or None if no solution.
    """

    # We need an app context to talk to the DB when called from scripts/other code
    with current_app.app_context():
        rooms = Room.query.all()
        batches = Batch.query.all()
        subjects = Subject.query.all()
        timeslots = Timeslot.query.order_by(
            Timeslot.day_of_week, Timeslot.start_time
        ).all()

        # Load unavailability: faculty_id -> set(timeslot_id)
        unavailable_map = {}
        all_unavail = FacultyUnavailableSlot.query.all()
        for ua in all_unavail:
            unavailable_map.setdefault(ua.faculty_id, set()).add(ua.timeslot_id)

        if not rooms or not batches or not subjects or not timeslots:
            print("❌ Not enough data to generate timetable.")
            return None

        # --------------------------------------------------
        # 1) Build class instances (what we need to schedule)
        # --------------------------------------------------
        # Each class instance = one weekly session:
        # (batch, subject, faculty, is_lab)
        class_instances = []

        for batch in batches:
            for subject in subjects:
                # simple rule: subject is only for a matching semester for the batch year
                if subject.semester not in [batch.year * 2 - 1, batch.year * 2]:
                    continue

                # Which faculties can teach this subject?
                fs_mappings = FacultySubject.query.filter_by(
                    subject_id=subject.id
                ).all()
                if not fs_mappings:
                    print(
                        f"⚠️ No faculty mapping for subject {subject.code}, skipping."
                    )
                    continue

                # For hackathon simplicity, pick first mapped faculty
                faculty = fs_mappings[0].faculty

                # classes_per_week tells us how many sessions this subject needs
                for _ in range(subject.classes_per_week):
                    class_instances.append(
                        {
                            "batch_id": batch.id,
                            "subject_id": subject.id,
                            "faculty_id": faculty.id,
                            "is_lab": subject.is_lab,
                        }
                    )

        if not class_instances:
            print("❌ No class instances built. Check seed data.")
            return None

        num_classes = len(class_instances)
        num_rooms = len(rooms)
        num_slots = len(timeslots)

        print(f"📊 Building model for {num_classes} class instances ...")

        # --------------------------------------------------
        # 2) Define CP-SAT model and decision variables
        # --------------------------------------------------
        model = cp_model.CpModel()

        # x[c, r, s] = 1 if class c happens in room r at timeslot s
        x = {}
        for c in range(num_classes):
            is_lab = class_instances[c]["is_lab"]
            faculty_id = class_instances[c]["faculty_id"]

            # timeslots this faculty is unavailable
            fac_unavail = unavailable_map.get(faculty_id, set())

            for r in range(num_rooms):
                # Lab subjects must be in lab rooms
                if is_lab and rooms[r].room_type != "lab":
                    continue
                # Optional: non-lab subjects don't use labs
                if not is_lab and rooms[r].room_type == "lab":
                    continue

                for s in range(num_slots):
                    ts_id = timeslots[s].id

                    # If this faculty marked this timeslot as unavailable, skip it
                    if ts_id in fac_unavail:
                        continue

                    x[(c, r, s)] = model.NewBoolVar(f"x_c{c}_r{r}_s{s}")

        # --------------------------------------------------
        # 3) Constraints
        # --------------------------------------------------

        # (a) Each class must be scheduled exactly once
        for c in range(num_classes):
            relevant_vars = [
                x[(c, r, s)]
                for r in range(num_rooms)
                for s in range(num_slots)
                if (c, r, s) in x
            ]
            if not relevant_vars:
                print(f"❌ Class {c} has no valid (room, slot) combinations.")
                return None
            model.Add(sum(relevant_vars) == 1)

        # (b) Room clash: at most one class per room per timeslot
        for r in range(num_rooms):
            for s in range(num_slots):
                vars_in_room_slot = [
                    x[(c, r, s)]
                    for c in range(num_classes)
                    if (c, r, s) in x
                ]
                if vars_in_room_slot:
                    model.Add(sum(vars_in_room_slot) <= 1)

        # (c) Faculty clash: a faculty can't be in two places at same time
        all_faculties = Faculty.query.all()
        for s in range(num_slots):
            for faculty in all_faculties:
                vars_for_faculty = []
                for c in range(num_classes):
                    if class_instances[c]["faculty_id"] != faculty.id:
                        continue
                    for r in range(num_rooms):
                        if (c, r, s) in x:
                            vars_for_faculty.append(x[(c, r, s)])
                if vars_for_faculty:
                    model.Add(sum(vars_for_faculty) <= 1)

        # (d) Batch clash: a batch can't attend two classes at same time
        for s in range(num_slots):
            for batch in batches:
                vars_for_batch = []
                for c in range(num_classes):
                    if class_instances[c]["batch_id"] != batch.id:
                        continue
                    for r in range(num_rooms):
                        if (c, r, s) in x:
                            vars_for_batch.append(x[(c, r, s)])
                if vars_for_batch:
                    model.Add(sum(vars_for_batch) <= 1)

        # -------------------------
        # LUNCH BREAK CONSTRAINTS
        # -------------------------
        # For each batch, for each day: lunch break is either 12:30–13:30 OR 13:30–14:30.
        # The solver decides which one (no user/batch choice).
        lunch1_start = time(12, 30)
        lunch2_start = time(13, 30)

        for batch in batches:
            for day in range(0, 5):  # Mon–Fri
                slot_l1 = None
                slot_l2 = None

                # Find slot indexes for the two lunch slots for this day
                for s, ts in enumerate(timeslots):
                    if ts.day_of_week != day:
                        continue
                    if ts.start_time == lunch1_start:
                        slot_l1 = s
                    if ts.start_time == lunch2_start:
                        slot_l2 = s

                # If that day doesn't have both lunch slots, skip
                if slot_l1 is None or slot_l2 is None:
                    continue

                # Binary decision: which slot is the BREAK
                # z = 0 -> second slot (13:30–14:30) is break (no class there)
                # z = 1 -> first slot (12:30–13:30) is break
                z = model.NewBoolVar(f"lunch_choice_b{batch.id}_d{day}")

                vars_l1 = []
                vars_l2 = []

                for c in range(num_classes):
                    if class_instances[c]["batch_id"] != batch.id:
                        continue
                    for r in range(num_rooms):
                        if (c, r, slot_l1) in x:
                            vars_l1.append(x[(c, r, slot_l1)])
                        if (c, r, slot_l2) in x:
                            vars_l2.append(x[(c, r, slot_l2)])

                # Because batch clash is already enforced, sum(...) <= 1 anyway.
                # Here we force ONE of the two slots to be empty for this batch.
                if vars_l1:
                    model.Add(sum(vars_l1) <= 1 - z)
                if vars_l2:
                    model.Add(sum(vars_l2) <= z)

        # --------------------------------------------------
        # 4) Solve (we only care about "any" feasible solution)
        # --------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0  # safety limit

        result_status = solver.Solve(model)

        if result_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("❌ No feasible timetable found.")
            return None

        print("✅ Timetable solution found. Saving to database...")

        # --------------------------------------------------
        # 5) Save solution as Timetable + TimetableEntry rows
        # --------------------------------------------------
        timetable = Timetable(name=name)
        db.session.add(timetable)
        db.session.commit()  # now timetable.id is available

        for c in range(num_classes):
            ci = class_instances[c]
            chosen_room_id = None
            chosen_slot_id = None

            for r in range(num_rooms):
                for s in range(num_slots):
                    if (c, r, s) in x and solver.Value(x[(c, r, s)]) == 1:
                        chosen_room_id = rooms[r].id
                        chosen_slot_id = timeslots[s].id
                        break
                if chosen_room_id is not None:
                    break

            if chosen_room_id is None or chosen_slot_id is None:
                print(f"⚠️ Class {c} has no chosen room/slot in solution, skipping.")
                continue

            entry = TimetableEntry(
                timetable_id=timetable.id,
                batch_id=ci["batch_id"],
                subject_id=ci["subject_id"],
                faculty_id=ci["faculty_id"],
                room_id=chosen_room_id,
                timeslot_id=chosen_slot_id,
            )
            db.session.add(entry)

        db.session.commit()
        print(
            f"✅ Timetable saved with id={timetable.id} and "
            f"{timetable.entries.count()} entries."
        )

        return timetable
```

## `app/static/css/style.css`
```css
/* Global */
body.app-body {
    margin: 0;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background-color: #f4f5fb;
    color: #111827;
}

.app-layout {
    display: flex;
    min-height: 100vh;
}

/* Sidebar */
.app-sidebar {
    width: 240px;
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    padding: 1rem 0.75rem;
}

.sidebar-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0 0.5rem 1rem 0.5rem;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 0.75rem;
}

.sidebar-logo {
    font-size: 1.4rem;
}

.sidebar-title {
    font-weight: 600;
    font-size: 0.95rem;
}

.sidebar-nav {
    flex: 1;
    display: flex;
    flex-direction: column;
    margin-top: 0.5rem;
}

.sidebar-link {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.55rem 0.65rem;
    border-radius: 0.55rem;
    font-size: 0.9rem;
    color: #4b5563;
    text-decoration: none;
    margin-bottom: 0.15rem;
}

.sidebar-link .icon {
    font-size: 1.05rem;
}

.sidebar-link:hover {
    background-color: #eef2ff;
    color: #1d4ed8;
}

.sidebar-link.active {
    background-color: #e0ebff;
    color: #1d4ed8;
    font-weight: 500;
}

.sidebar-footer {
    border-top: 1px solid #e5e7eb;
    padding-top: 0.75rem;
}

.sidebar-user {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.avatar-circle {
    width: 32px;
    height: 32px;
    border-radius: 999px;
    background-color: #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.9rem;
}

/* Main area */
.app-main {
    flex: 1;
    display: flex;
    flex-direction: column;
}

/* Top bar */
.app-topbar {
    height: 64px;
    background-color: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
}

.topbar-title {
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0;
}

/* Content */
.app-content {
    padding: 1.5rem 1.5rem 2.5rem;
}

/* Cards / widgets */
.card {
    border: none;
    border-radius: 14px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.metric-card-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #9ca3af;
    margin-bottom: 0.25rem;
}

.metric-card-value {
    font-size: 1.5rem;
    font-weight: 600;
}

.metric-card-sub {
    font-size: 0.75rem;
    color: #10b981;
}

/* Timetable grid */
.timetable-grid {
    display: grid;
    grid-template-columns: 100px repeat(5, 1fr);
    gap: 1px;
    background-color: #d1d5db;
    border-radius: 12px;
    overflow: hidden;
    margin-top: 1rem;
}

.timetable-cell {
    background-color: #f9fafb;
    padding: 0.6rem 0.75rem;
    font-size: 0.8rem;
}

.timetable-header {
    background-color: #e5e7eb;
    font-weight: 600;
}

.text-muted-soft {
    color: #9ca3af;
    font-size: 0.8rem;
}
.timetable-wrapper {
    overflow-x: auto;
    margin-top: 20px;
}

.timetable-table {
    width: 100%;
    border-collapse: collapse;
    text-align: center;
    font-size: 13px;
}

.timetable-table th,
.timetable-table td {
    border: 2px solid #444;   /* Darker, bold grid lines */
}

.day-label {
    font-weight: 600;
    background: #f0f0f0;
}

.time-range {
    font-weight: 600;
    font-size: 12px;
}

/* Cell height and layout */
.tt-cell {
    height: 85px;
    vertical-align: top;
    padding: 6px;
}

/* Empty cell text */
.tt-empty {
    color: #777;
    font-style: italic;
    font-size: 12px;
    padding-top: 18px;
    display: block;
}

.tt-course {
    color: #ff6600; /* Orange */
    font-weight: 700;
}

.tt-room {
    color: #0066ff; /* Blue */
    font-weight: 700;
}

.tt-faculty {
    color: #b30000; /* Red */
    font-weight: 700;
}

.tt-section {
    color: #008520; /* Green */
    font-weight: 700;
}

.period-number {
    font-weight: 700;
    margin-bottom: 2px;
}
```

## `app/templates/admin_dashboard.html`
```html
{% extends "base.html" %}
{% block title %}Admin · Timetable System{% endblock %}
{% block page_title %}Dashboard{% endblock %}

{% block content %}

<!-- Top metric cards -->
<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="card h-100">
            <div class="card-body">
                <div class="metric-card-label">Total Students</div>
                <div class="metric-card-value">80</div>
                <div class="metric-card-sub">+12% from last year</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card h-100">
            <div class="card-body">
                <div class="metric-card-label">Faculty Members</div>
                <div class="metric-card-value">20</div>
                <div class="metric-card-sub text-muted">Active this semester</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card h-100">
            <div class="card-body">
                <div class="metric-card-label">Rooms Available</div>
                <div class="metric-card-value">10</div>
                <div class="metric-card-sub text-muted">2 under maintenance</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card h-100">
            <div class="card-body">
                <div class="metric-card-label">Active Timetables</div>
                <div class="metric-card-value">4</div>
                <div class="metric-card-sub text-muted">This academic year</div>
            </div>
        </div>
    </div>
</div>

<!-- Quick actions + recent activity -->
<div class="row g-3">
    <div class="col-md-6">
        <h6 class="mb-2">Quick Actions</h6>
        <div class="row g-3">
            <div class="col-6">
                <div class="card h-100">
                    <div class="card-body d-flex flex-column justify-content-between">
                        <div>
                            <h5 class="card-title mb-1">Create Timetable</h5>
                            <p class="text-muted-soft mb-3">Run AI scheduler for selected batches.</p>
                        </div>
                        <a href="{{ url_for('main.admin_generate_timetable') }}"
                           class="btn btn-primary btn-sm w-100">Generate</a>
                    </div>
                </div>
            </div>
            <div class="col-6">
                <div class="card h-100">
                    <div class="card-body d-flex flex-column justify-content-between">
                        <div>
                            <h5 class="card-title mb-1">Manage Faculty</h5>
                            <p class="text-muted-soft mb-3">Add / edit faculty and workloads.</p>
                        </div>
                        <a href="{{ url_for('main.admin_manage_faculty') }}"
                           class="btn btn-outline-secondary btn-sm w-100">Open</a>
                    </div>
                </div>
            </div>
            <div class="col-6">
                <div class="card h-100">
                    <div class="card-body d-flex flex-column justify-content-between">
                        <div>
                            <h5 class="card-title mb-1">Add Batch</h5>
                            <p class="text-muted-soft mb-3">Create a new year / section.</p>
                        </div>
                        <a href="{{ url_for('main.admin_batches') }}"
                           class="btn btn-outline-secondary btn-sm w-100">Add</a>
                    </div>
                </div>
            </div>
            <div class="col-6">
                <div class="card h-100">
                    <div class="card-body d-flex flex-column justify-content-between">
                        <div>
                            <h5 class="card-title mb-1">Room Setup</h5>
                            <p class="text-muted-soft mb-3">Manage capacities and statuses.</p>
                        </div>
                        <a href="{{ url_for('main.view_rooms') }}"
                           class="btn btn-outline-secondary btn-sm w-100">Manage</a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Recent Activity -->
    <div class="col-md-6">
        <h6 class="mb-2">Recent Activity</h6>
        <div class="card">
            <div class="card-body">
                <ul class="list-unstyled mb-0 small">
                    <li class="mb-3">
                        <strong>Timetable created for CSE-Y1</strong><br>
                        <span class="text-muted-soft">admin · 2 hours ago</span>
                    </li>
                    <li class="mb-3">
                        <strong>New faculty member added: Dr. Smith</strong><br>
                        <span class="text-muted-soft">admin · 5 hours ago</span>
                    </li>
                    <li class="mb-3">
                        <strong>Batch CSE-Y2 updated</strong><br>
                        <span class="text-muted-soft">hod_cse · 1 day ago</span>
                    </li>
                    <li>
                        <strong>Room R-105 capacity changed</strong><br>
                        <span class="text-muted-soft">admin · 2 days ago</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>

{% endblock %}
```

## `app/templates/base.html`
```html
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{% block title %}Timetable System{% endblock %}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Bootstrap -->
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
    <!-- Your custom styles -->
    <link rel="stylesheet"
          href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body class="app-body">

<div class="app-layout">
    <!-- SIDEBAR -->
    <aside class="app-sidebar">
        <div class="sidebar-header">
            <span class="sidebar-logo">🧠</span>
            <span class="sidebar-title">Timetable System</span>
        </div>

        <nav class="sidebar-nav">
            <a href="{{ url_for('main.admin_dashboard') }}"
               class="sidebar-link{% if request.path.endswith('/dashboard') %} active{% endif %}">
                <span class="icon">🏠</span> Dashboard
            </a>
            <a href="{{ url_for('main.list_timetables') }}"
               class="sidebar-link">
                <span class="icon">📅</span> Timetables
            </a>
            <a href="{{ url_for('main.admin_batches') }}"
               class="sidebar-link{% if request.endpoint == 'main.admin_batches' %} active{% endif %}">
                <span class="icon">🎓</span> Batches
            </a>
            <a href="{{ url_for('main.view_students') }}"
               class="sidebar-link">
                <span class="icon">👨‍🎓</span> Students
            </a>
            <a href="{{ url_for('main.admin_manage_faculty') }}"
               class="sidebar-link">
                <span class="icon">👩‍🏫</span> Faculty
            </a>
            <a href="{{ url_for('main.view_subjects') }}"
               class="sidebar-link">
                <span class="icon">📚</span> Subjects
            </a>
            <a href="{{ url_for('main.view_rooms') }}"
               class="sidebar-link">
                <span class="icon">🏫</span> Rooms
            </a>
            <a href="{{ url_for('main.view_timeslots') }}"
               class="sidebar-link">
                <span class="icon">⏱️</span> Timeslots
            </a>
            <a href="{{ url_for('main.settings') }}"
               class="sidebar-link">
                <span class="icon">⚙️</span> Settings
            </a>
        </nav>

        <div class="sidebar-footer">
            {% if current_user.is_authenticated %}
                <div class="sidebar-user">
                    <div class="avatar-circle">{{ current_user.username[0] | upper }}</div>
                    <div>
                        <div class="user-name">{{ current_user.username }}</div>
                        <div class="user-role text-muted">{{ current_user.role|capitalize }}</div>
                    </div>
                </div>
                <a href="{{ url_for('main.logout') }}" class="btn btn-outline-secondary btn-sm w-100 mt-2">
                    Logout
                </a>
            {% endif %}
        </div>
    </aside>

    <!-- MAIN AREA -->
    <div class="app-main">
        <!-- TOP BAR -->
        <header class="app-topbar">
            <div class="topbar-left">
                <h1 class="topbar-title">{% block page_title %}Dashboard{% endblock %}</h1>
            </div>
            <div class="topbar-right">
                <form class="d-flex align-items-center gap-2">
                    <label class="text-muted small mb-0">Switch User Role (Demo)</label>
                    <select class="form-select form-select-sm" style="width: 180px;">
                        <option>Admin</option>
                        <option>HOD</option>
                        <option>Faculty</option>
                        <option>Student</option>
                    </select>
                </form>
            </div>
        </header>

        <main class="app-content">
            {% with messages = get_flashed_messages(with_categories=True) %}
              {% if messages %}
                <div class="mb-3">
                  {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                      {{ message }}
                      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                  {% endfor %}
                </div>
              {% endif %}
            {% endwith %}

            {% block content %}{% endblock %}
        </main>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

## `app/templates/student_dashboard.html`
```html
{% extends "base.html" %}
{% block title %}Student · Intelligent Timetable{% endblock %}

{% block content %}

<div class="section-header">
    <h2>Student Dashboard</h2>
    <span>
        {% if batch %}
            Weekly schedule for {{ batch.name }}
        {% else %}
            Weekly schedule
        {% endif %}
    </span>
</div>

<div class="row g-4">
    <div class="col-md-12">
        <div class="mb-2">
            <div class="text-muted-soft">
                Course Name <span class="tt-course">Sample</span>
                &nbsp; Room Name <span class="tt-room">Sample</span>
                &nbsp; Faculty Name <span class="tt-faculty">Sample</span>
                &nbsp; Section / Batch <span class="tt-section">Sample</span>
            </div>
        </div>

        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">Your Timetable</h5>
                <p class="text-muted-soft mb-2">
                    Generated from the latest timetable. Empty slots show "No Class".
                </p>

                {% if days and periods %}
                <div class="timetable-wrapper">
                    <table class="timetable-table">
                        <thead>
                            <tr>
                                <th>Day / Time</th>
                                {% for start, end in periods %}
                                    <th>
                                        <div class="period-number">
                                            {{ loop.index }}
                                        </div>
                                        <div class="time-range">
                                            {{ start.strftime('%H:%M') }}<br>
                                            - {{ end.strftime('%H:%M') }}
                                        </div>
                                    </th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for day_index, day_label in days %}
                            <tr>
                                <td class="day-label">{{ day_label }}</td>

                                {% for p_idx in range(periods|length) %}
                                    {% set entry = grid.get((day_index, p_idx)) %}
                                    <td class="tt-cell">
                                        {% if entry %}
                                            <div class="tt-course">
                                                {{ entry.subject.code }} {{ entry.subject.name }}
                                            </div>
                                            <div class="tt-room">
                                                {{ entry.room.name }}
                                            </div>
                                            <div class="tt-faculty">
                                                {{ entry.faculty.name }}
                                            </div>
                                            <div class="tt-section">
                                                {{ entry.batch.name }}
                                            </div>
                                        {% else %}
                                            <div class="tt-empty">No Class</div>
                                        {% endif %}
                                    </td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                    <p class="text-muted-soft mb-0">
                        {% if not batch %}
                            Your batch is not linked to your account yet. Ask the admin to set it.
                        {% else %}
                            No timetable generated yet for your batch.
                        {% endif %}
                    </p>
                {% endif %}
            </div>
        </div>
    </div>
</div>

{% endblock %}
```

## `app/templates/admin_edit_faculty.html`
```html
{% extends "base.html" %}
{% block title %}Edit Faculty · Intelligent Timetable{% endblock %}

{% block content %}
<div class="section-header">
    <h2>Edit Faculty</h2>
    <span>Update details for {{ faculty.code }}</span>
</div>

<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card mb-3">
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Name</label>
                        <input name="name" class="form-control" required value="{{ faculty.name }}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Code</label>
                        <input name="code" class="form-control" required value="{{ faculty.code }}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Max Load / Week (hours)</label>
                        <input name="max_load_per_week" class="form-control"
                               type="number" min="1" max="40"
                               value="{{ faculty.max_load_per_week }}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Linked User (optional)</label>
                        <select name="user_id" class="form-select">
                            <option value="">-- none --</option>
                            {% for u in users %}
                                <option value="{{ u.id }}"
                                        {% if faculty.user_id == u.id %}selected{% endif %}>
                                    {{ u.username }} ({{ u.role }})
                                </option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="d-flex justify-content-between">
                        <a href="{{ url_for('main.admin_manage_faculty') }}" class="btn btn-outline-secondary">
                            Back
                        </a>
                        <button type="submit" class="btn btn-primary">
                            Save Changes
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## `app/templates/admin_manage_faculty.html`
```html
{% extends "base.html" %}
{% block title %}Manage Faculty · Intelligent Timetable{% endblock %}

{% block content %}
<div class="section-header">
    <h2>Manage Faculty</h2>
    <span>Add, edit, or remove faculty members.</span>
</div>

<div class="row g-4">
    <!-- Add Faculty form -->
    <div class="col-md-4">
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title mb-3">Add Faculty</h5>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Name</label>
                        <input name="name" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Code</label>
                        <input name="code" class="form-control" required placeholder="e.g. F007">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Max Load / Week (hours)</label>
                        <input name="max_load_per_week" class="form-control" type="number" min="1" max="40" value="16">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Link to User (optional)</label>
                        <select name="user_id" class="form-select">
                            <option value="">-- none --</option>
                            {% for u in users %}
                                <option value="{{ u.id }}">{{ u.username }} ({{ u.role }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">
                        Add Faculty
                    </button>
                </form>
            </div>
        </div>
    </div>

    <!-- Faculty list -->
    <div class="col-md-8">
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title mb-3">Faculty List</h5>
                {% if faculties %}
                    <div class="table-responsive">
                        <table class="table align-middle">
                            <thead>
                                <tr>
                                    <th>Code</th>
                                    <th>Name</th>
                                    <th>Max Load</th>
                                    <th>Linked User</th>
                                    <th style="width: 130px;">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for fac in faculties %}
                                <tr>
                                    <td>{{ fac.code }}</td>
                                    <td>{{ fac.name }}</td>
                                    <td>{{ fac.max_load_per_week }}</td>
                                    <td>
                                        {% if fac.user %}
                                            {{ fac.user.username }} ({{ fac.user.role }})
                                        {% else %}
                                            <span class="text-muted">None</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <a href="{{ url_for('main.admin_edit_faculty', faculty_id=fac.id) }}"
                                           class="btn btn-sm btn-outline-secondary">
                                            Edit
                                        </a>
                                        <form method="POST"
                                              action="{{ url_for('main.admin_delete_faculty', faculty_id=fac.id) }}"
                                              class="d-inline"
                                              onsubmit="return confirm('Delete this faculty?');">
                                            <button type="submit" class="btn btn-sm btn-outline-danger">
                                                Delete
                                            </button>
                                        </form>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <p class="text-muted mb-0">No faculty added yet.</p>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## `app/templates/hod_dashboard.html`
```html
{% extends "base.html" %}
{% block content %}
<h2>Department Head Dashboard</h2>
<p>Welcome, {{ user.username }} (HOD)</p>

<div class="row">
    <div class="col-md-6">
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">Department Overview</h5>
                <ul>
                    <li>See timetable for your department's batches</li>
                    <li>Review faculty loads and room allocations</li>
                    <li>Approve / reject timetable versions</li>
                </ul>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## `app/templates/faculty_dashboard.html`
```html
{% extends "base.html" %}
{% block title %}Faculty · Intelligent Timetable{% endblock %}

{% block content %}

<div class="section-header">
    <h2>Faculty Dashboard</h2>
    <span>Weekly schedule for {{ user.username }}</span>
</div>

<div class="row g-4">
    <div class="col-md-4">
        <!-- your overview card stays as you like -->
        <div class="card">
            <div class="card-body">
                <h5 class="card-title mb-2">Overview</h5>
                <p class="text-muted-soft mb-2">
                    Auto-generated load for the week.
                </p>
                <!-- mock / calculated stats can go here -->
            </div>
        </div>
    </div>

    <div class="col-md-8">
        <div class="card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="card-title mb-0">Your Timetable</h5>
                </div>
                <p class="text-muted-soft mb-2">
                    Generated from the latest timetable. Empty slots show "No Class".
                </p>

                {% if days and periods %}
                <div class="timetable-wrapper">
                    <table class="timetable-table">
                        <thead>
                            <tr>
                                <th>Day / Time</th>
                                {% for start, end in periods %}
                                    <th>
                                        <div class="time-range">
                                            {{ start.strftime('%H:%M') }}<br>
                                            - {{ end.strftime('%H:%M') }}
                                        </div>
                                    </th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for day_index, day_label in days %}
                            <tr>
                                <td class="day-label">{{ day_label }}</td>

                                {% for p_idx in range(periods|length) %}
                                    {% set entry = grid.get((day_index, p_idx)) %}
                                    <td class="tt-cell">
                                        {% if entry %}
                                            <div class="tt-course">
                                                {{ entry.subject.code }} {{ entry.subject.name }}
                                            </div>
                                            <div class="tt-room">
                                                {{ entry.room.name }}
                                            </div>
                                            <div class="tt-faculty">
                                                {{ entry.faculty.name }}
                                            </div>
                                            <div class="tt-section">
                                                {{ entry.batch.name }}
                                            </div>
                                        {% else %}
                                            <div class="tt-empty">No Class</div>
                                        {% endif %}
                                    </td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                    <p class="text-muted-soft mb-0">
                        No timetable generated yet for you.
                    </p>
                {% endif %}
            </div>
        </div>
    </div>
</div>

{% endblock %}
```

## `app/templates/login.html`
```html
{% extends "base.html" %}
{% block title %}Login · Intelligent Timetable{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-4">
        <div class="text-center mb-4">
            <h1 class="h3 mb-1">Welcome back</h1>
            <p class="text-muted-soft mb-0">Sign in to manage your timetable.</p>
        </div>
        <div class="card">
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Username or Email</label>
                        <input type="text" name="username" class="form-control" required autocomplete="username">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" name="password" class="form-control" required autocomplete="current-password">
                    </div>
                    <button type="submit" class="btn btn-primary w-100 mb-2">Login</button>
                    <p class="text-muted-soft mb-0">
                        Demo users: admin / hod_cse / fac_alice / stud_bob
                    </p>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## `app/templates/landing.html`
```html
{% extends "base.html" %}
{% block title %}Intelligent Timetable · Welcome{% endblock %}
{% block content %}

<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="text-center mb-4">
            <h1 class="h2 mb-2">Intelligent Timetable</h1>
            <p class="text-muted-soft">
                AI-powered timetable generation for admins, HODs, faculty, and students.
                No more clashes, manual spreadsheets, or juggling rooms.
            </p>
        </div>

        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">What you can do</h5>
                <ul>
                    <li><strong>Admins</strong>: configure data & generate full timetables.</li>
                    <li><strong>HODs</strong>: review department timetables & conflicts.</li>
                    <li><strong>Faculty</strong>: view your personal weekly schedule.</li>
                    <li><strong>Students</strong>: see your batch timetable.</li>
                </ul>
                <div class="text-center mt-3">
                    <a href="{{ url_for('main.login') }}" class="btn btn-primary">
                        Go to Login
                    </a>
                </div>
            </div>
        </div>

        <p class="text-muted-soft text-center">
            Demo users: admin / hod_cse / fac_alice / stud_bob
        </p>
    </div>
</div>

{% endblock %}
```

## `app/templates/timetable_list.html`
```html
{% extends "base.html" %}
{% block title %}All Timetables · Intelligent Timetable{% endblock %}
{% block content %}

<div class="section-header">
    <h2>All Timetables</h2>
    <span class="text-muted-soft">Select a timetable to view its schedule.</span>
</div>

{% if timetables %}
    <div class="card">
        <div class="card-body">
            <table class="table align-middle mb-0">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Created At</th>
                        <th>Status</th>
                        <th>Entries</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {% for tt in timetables %}
                        <tr>
                            <td>{{ tt.id }}</td>
                            <td>{{ tt.name }}</td>
                            <td>{{ tt.created_at }}</td>
                            <td>{{ tt.status }}</td>
                            <td>{{ tt.entries.count() }}</td>
                            <td>
                                <a href="{{ url_for('main.view_timetable', timetable_id=tt.id) }}"
                                   class="btn btn-sm btn-outline-secondary">
                                    View
                                </a>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% else %}
    <p class="text-muted-soft">No timetables generated yet.</p>
{% endif %}

{% endblock %}
```

## `app/templates/timetable_view.html`
```html
{% extends "base.html" %}
{% block title %}Timetable · {{ timetable.name }}{% endblock %}

{% block content %}
<h2>{{ timetable.name }}</h2>
<p class="text-muted-soft">Auto-generated timetable view</p>

{% if not days or not periods %}
    <p>No timeslots or days configured.</p>
{% else %}
<div class="timetable-wrapper">
    <table class="timetable-table">
        <thead>
            <tr>
                <th>Day / Time</th>
                {% for start, end in periods %}
                    <th>
                        <div class="time-range">
                            {{ start.strftime('%H:%M') }}<br>
                            - {{ end.strftime('%H:%M') }}
                        </div>
                    </th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for day_index, day_label in days %}
            <tr>
                <td class="day-label">{{ day_label }}</td>

                {% for p_idx in range(periods|length) %}
                    {% set entry = grid.get((day_index, p_idx)) %}
                    <td class="tt-cell">
                        {% if entry %}
                            <div class="tt-course">
                                {{ entry.subject.code }} {{ entry.subject.name }}
                            </div>
                            <div class="tt-room">
                                {{ entry.room.name }}
                            </div>
                            <div class="tt-faculty">
                                {{ entry.faculty.name }}
                            </div>
                            <div class="tt-section">
                                {{ entry.batch.name }}
                            </div>
                        {% else %}
                            <div class="tt-empty">No Class</div>
                        {% endif %}
                    </td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}
{% endblock %}
```

## `app/templates/faculty_preferences.html`
```html
{% extends "base.html" %}
{% block title %}Preferences · Faculty{% endblock %}
{% block content %}

<div class="section-header">
    <h2>Teaching Preferences</h2>
    <span class="text-muted-soft">
        {{ faculty.name }} – select slots you are <strong>NOT</strong> available to teach.
    </span>
</div>

<div class="card">
    <div class="card-body">
        <p class="text-muted-soft mb-3">
            Tick the time slots when you <strong>cannot</strong> take classes
            (meetings, research, personal constraints, etc.).
            The scheduler will try to avoid putting you in those slots.
        </p>

        <form method="POST">
            <div class="timetable-grid">
                <!-- Header row -->
                <div class="timetable-cell timetable-header">Time</div>
                <div class="timetable-cell timetable-header">Day</div>
                <div class="timetable-cell timetable-header">Unavailable?</div>

                {% for slot in timeslots %}
                    <div class="timetable-cell timetable-header">
                        {{ slot.start_time.strftime("%H:%M") }}–{{ slot.end_time.strftime("%H:%M") }}
                    </div>
                    <div class="timetable-cell">
                        {{ day_names[slot.day_of_week] }}
                    </div>
                    <div class="timetable-cell">
                        <div class="form-check">
                            <input class="form-check-input"
                                   type="checkbox"
                                   name="unavailable_slots"
                                   value="{{ slot.id }}"
                                   id="slot_{{ slot.id }}"
                                   {% if slot.id in unavailable_ids %}checked{% endif %}>
                            <label class="form-check-label text-muted-soft" for="slot_{{ slot.id }}">
                                I am not available
                            </label>
                        </div>
                    </div>
                {% endfor %}
            </div>

            <button type="submit" class="btn btn-primary mt-3">
                Save Preferences
            </button>
        </form>
    </div>
</div>

{% endblock %}
```

## `app/templates/student_batch_timetable.html`
```html
{% extends "base.html" %}
{% block title %}Batch Timetable · Student{% endblock %}
{% block content %}

<div class="section-header">
    <h2>Batch Timetable</h2>
    <span class="text-muted-soft">
        View timetable for a specific batch from the latest generated timetable.
    </span>
</div>

<div class="card mb-3">
    <div class="card-body">
        <form method="POST" class="row g-2 align-items-end">
            <div class="col-md-6">
                <label class="form-label">Select Batch</label>
                <select name="batch_id" class="form-select" required>
                    <option value="" disabled {% if not selected_batch_id %}selected{% endif %}>
                        Choose...
                    </option>
                    {% for batch in batches %}
                        <option value="{{ batch.id }}"
                            {% if selected_batch_id == batch.id %}selected{% endif %}>
                            {{ batch.name }} (Sem {{ batch.semester }})
                        </option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3">
                <button type="submit" class="btn btn-primary w-100">Show Timetable</button>
            </div>
        </form>
    </div>
</div>

{% if selected_batch_id %}
    {% if not has_timetable %}
        <div class="alert alert-warning">
            No timetable generated yet for this batch.
        </div>
    {% else %}
        {% include "_timetable_grid.html" with context %}
    {% endif %}
{% endif %}

{% endblock %}
```

## `app/templates/admin_batches.html`
```html
{% extends "base.html" %}
{% block title %}Batches · Timetable System{% endblock %}
{% block page_title %}Batches{% endblock %}
{% block page_subtitle %}
<p class="text-muted-soft mb-0">
    Manage batches / years that will have timetables generated.
</p>
{% endblock %}

{% block content %}

<div class="card mb-3">
    <div class="card-body">
        <form class="row g-2 align-items-end" action="{{ url_for('main.admin_add_batch') }}" method="post">
            <div class="col-md-3">
                <label class="form-label form-label-sm">Batch Name</label>
                <input type="text" name="name" class="form-control form-control-sm"
                       placeholder="CSE-Y1" required>
            </div>
            <div class="col-md-3">
                <label class="form-label form-label-sm">Program</label>
                <input type="text" name="program" class="form-control form-control-sm"
                       placeholder="B.Tech CSE" required>
            </div>
            <div class="col-md-2">
                <label class="form-label form-label-sm">Year</label>
                <select name="year" class="form-select form-select-sm" required>
                    <option value="">Select</option>
                    <option value="1">1st Year</option>
                    <option value="2">2nd Year</option>
                    <option value="3">3rd Year</option>
                    <option value="4">4th Year</option>
                </select>
            </div>
            <div class="col-md-2">
                <label class="form-label form-label-sm">Section</label>
                <input type="text" name="section" class="form-control form-control-sm"
                       placeholder="A">
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-primary btn-sm w-100">
                    <i class="bi bi-plus-lg me-1"></i> Add Batch
                </button>
            </div>
        </form>
    </div>
</div>

<div class="card">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0">Existing Batches</h6>
            <span class="text-muted-soft">
                Total: {{ batches|length }}
            </span>
        </div>

        <div class="table-responsive">
            <table class="table align-middle">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Batch Name</th>
                        <th>Program</th>
                        <th>Year</th>
                        <th>Section</th>
                        <th>Status</th>
                        <th class="text-end">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for batch in batches %}
                    <tr>
                        <td>{{ batch.id }}</td>
                        <td>{{ batch.name }}</td>
                        <td>{{ batch.program }}</td>
                        <td>{{ batch.year }}{% if batch.year == 1 %}st{% elif batch.year == 2 %}nd{% elif batch.year == 3 %}rd{% else %}th{% endif %} Year</td>
                        <td>{{ batch.section or "-" }}</td>
                        <td>
                            <span class="badge badge-soft">Active</span>
                        </td>
                        <td class="text-end">
                            <!-- For now only delete; edit can be added later -->
                            <form action="{{ url_for('main.admin_delete_batch', batch_id=batch.id) }}"
                                  method="post"
                                  style="display:inline-block"
                                  onsubmit="return confirm('Delete this batch?');">
                                <button type="submit" class="btn btn-outline-danger btn-sm">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="7" class="text-center text-muted-soft">
                            No batches added yet. Create your first batch above.
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

{% endblock %}
```
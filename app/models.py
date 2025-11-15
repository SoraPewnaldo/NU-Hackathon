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


class FacultyUnavailability(db.Model):
    __tablename__ = "faculty_unavailability"

    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Mon, 6=Sun
    timeslot_id = db.Column(db.Integer, db.ForeignKey("timeslot.id"), nullable=True)  # NULL = whole day

    reason = db.Column(db.String(255))
    status = db.Column(db.String(20), default="PENDING")  # PENDING, APPROVED, REJECTED

    faculty = db.relationship("Faculty", backref="unavailabilities")
    timeslot = db.relationship("Timeslot", backref="unavailabilities", lazy="joined")


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

    # NEW:
    status = db.Column(
        db.String(30),
        default="NORMAL"
    )  # NORMAL, RESCHEDULED_REPLACEMENT, RESCHEDULED_MOVED, CANCELLED

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
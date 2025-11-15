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

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='faculty')  # admin / hod / faculty

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    name = db.Column(db.String(64), unique=True, nullable=False)  # e.g. CSE-2A
    program = db.Column(db.String(64))  # e.g. BTech CSE
    semester = db.Column(db.Integer, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Batch {self.name} sem={self.semester} size={self.size}>"


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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(32), unique=True, nullable=False)  # e.g. F001
    max_load_per_week = db.Column(db.Integer, default=16)

    user = db.relationship("User", backref=db.backref("faculty_profile", uselist=False))

    def __repr__(self):
        return f"<Faculty {self.code} {self.name}>"


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

    faculty = db.relationship("Faculty", backref=db.backref("subjects", lazy="dynamic"))
    subject = db.relationship("Subject", backref=db.backref("faculties", lazy="dynamic"))

    def __repr__(self):
        return f"<FacultySubject faculty={self.faculty_id} subject={self.subject_id}>"


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

    batch = db.relationship("Batch", backref=db.backref("timetable_entries", lazy="dynamic"))
    subject = db.relationship("Subject", backref=db.backref("timetable_entries", lazy="dynamic"))
    faculty = db.relationship("Faculty", backref=db.backref("timetable_entries", lazy="dynamic"))
    room = db.relationship("Room", backref=db.backref("timetable_entries", lazy="dynamic"))
    timeslot = db.relationship("Timeslot", backref=db.backref("timetable_entries", lazy="dynamic"))

    def __repr__(self):
        return (
            f"<Entry tt={self.timetable_id} batch={self.batch_id} "
            f"sub={self.subject_id} fac={self.faculty_id} room={self.room_id} slot={self.timeslot_id}>"
        )
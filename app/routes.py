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
    return redirect(url_for("main.login"))

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
    return render_template("admin_dashboard.html", user=current_user, latest_tt=latest_tt)


@main.route("/hod/dashboard")
@login_required
@roles_required("admin", "hod")   # admin can also see HOD view if you want
def hod_dashboard():
    return render_template("hod_dashboard.html", user=current_user)


@main.route("/faculty/dashboard")
@login_required
@roles_required("faculty", "hod", "admin")  # allow HOD/admin to peek as faculty
def faculty_dashboard():
    return render_template("faculty_dashboard.html", user=current_user)


@main.route("/student/dashboard")
@login_required
@roles_required("student", "admin")  # admin can impersonate/check student view
def student_dashboard():
    return render_template("student_dashboard.html", user=current_user)

@main.route("/admin/generate_timetable", methods=["POST"])
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
@roles_required("admin", "hod", "faculty", "student")
def view_timetable(timetable_id):
    timetable = Timetable.query.get_or_404(timetable_id)

    # Order timeslots by day + time
    timeslots = Timeslot.query.order_by(
        Timeslot.day_of_week, Timeslot.start_time
    ).all()
    batches = Batch.query.order_by(Batch.name).all()

    # Preload all entries for this timetable
    entries = TimetableEntry.query.filter_by(timetable_id=timetable.id).all()

    # Build quick lookup: (batch_id, timeslot_id) -> entry
    entry_map = {}
    for e in entries:
        entry_map[(e.batch_id, e.timeslot_id)] = e

    # We also need day names
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return render_template(
        "timetable_view.html",
        timetable=timetable,
        timeslots=timeslots,
        batches=batches,
        entry_map=entry_map,
        day_names=day_names,
    )
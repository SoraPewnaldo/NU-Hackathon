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


@main.route("/hod/dashboard")
@login_required
@roles_required("admin", "hod")   # admin can also see HOD view if you want
def hod_dashboard():
    return render_template("hod_dashboard.html", user=current_user)


@main.route("/faculty/dashboard")
@login_required
@roles_required("faculty", "hod", "admin")
def faculty_dashboard():
    faculty = current_user.faculty_profile

    if not faculty:
        flash("No faculty profile linked to this user.", "warning")
        return render_template("faculty_dashboard.html", user=current_user, has_timetable=False)

    latest_tt = Timetable.query.order_by(Timetable.created_at.desc()).first()
    if not latest_tt:
        flash("No timetable generated yet.", "warning")
        return render_template("faculty_dashboard.html", user=current_user, has_timetable=False)

    periods = build_periods()

    entries = (
        TimetableEntry.query
        .filter_by(timetable_id=latest_tt.id, faculty_id=faculty.id)
        .join(Timeslot)
        .order_by(Timeslot.day_of_week, Timeslot.start_time)
        .all()
    )

    grid = build_grid_for_entries(entries, periods)

    return render_template(
        "faculty_dashboard.html",
        user=current_user,
        has_timetable=True,
        days=DAYS,
        periods=periods,
        grid=grid,
        faculty=faculty,
    )


@main.route("/student/dashboard")
@login_required
@roles_required("student", "admin")  # admin can impersonate/check student view
def student_dashboard():
    # TODO: link user to a Batch via a real relation.
    # For now, pick first batch as demo:
    batch = Batch.query.first()

    latest_tt = Timetable.query.order_by(Timetable.created_at.desc()).first()
    if not latest_tt or not batch:
        return render_template("student_dashboard.html", user=current_user, has_timetable=False)

    periods = build_periods()

    entries = (
        TimetableEntry.query
        .filter_by(timetable_id=latest_tt.id, batch_id=batch.id)
        .join(Timeslot)
        .order_by(Timeslot.day_of_week, Timeslot.start_time)
        .all()
    )

    grid = build_grid_for_entries(entries, periods)

    return render_template(
        "student_dashboard.html",
        user=current_user,
        has_timetable=True,
        days=DAYS,
        periods=periods,
        grid=grid,
        batch=batch,
    )

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

    periods = build_periods()

    entries = (
        TimetableEntry.query
        .filter_by(timetable_id=timetable.id)
        .join(Timeslot)
        .order_by(Timeslot.day_of_week, Timeslot.start_time)
        .all()
    )

    grid = build_grid_for_entries(entries, periods)

    return render_template(
        "timetable_view.html",
        timetable=timetable,
        has_timetable=True,
        days=DAYS,
        periods=periods,
        grid=grid,
    )

@main.route("/timetables")
@login_required
@roles_required("admin", "hod", "faculty", "student")
def list_timetables():
    timetables = Timetable.query.order_by(Timetable.created_at.desc()).all()
    return render_template("timetable_list.html", timetables=timetables)

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
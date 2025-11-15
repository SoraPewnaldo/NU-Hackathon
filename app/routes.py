from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from sqlalchemy import func

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

def build_clash_report(timetable_id):
    """
    Scan TimetableEntry for:
      - batch clashes   (same batch, same timeslot, >1 class)
      - faculty clashes (same faculty, same timeslot, >1 class)
      - room clashes    (same room, same timeslot, >1 class)
    Returns a dict with lists of conflicts.
    """
    from .models import TimetableEntry, Timeslot, Batch, Faculty, Room, Subject

    # Base query for this timetable
    base_q = TimetableEntry.query.filter_by(timetable_id=timetable_id)

    # --- Batch clashes ---
    batch_conf_keys = (
        base_q.with_entities(
            TimetableEntry.timeslot_id,
            TimetableEntry.batch_id,
            func.count(TimetableEntry.id).label("cnt"),
        )
        .group_by(TimetableEntry.timeslot_id, TimetableEntry.batch_id)
        .having(func.count(TimetableEntry.id) > 1)
        .all()
    )

    batch_clashes = []
    for ts_id, batch_id, cnt in batch_conf_keys:
        ts = Timeslot.query.get(ts_id)
        batch = Batch.query.get(batch_id)
        entries = (
            base_q.filter_by(timeslot_id=ts_id, batch_id=batch_id)
            .all()
        )
        batch_clashes.append(
            {
                "timeslot": ts,
                "batch": batch,
                "entries": entries,
                "count": cnt,
            }
        )

    # --- Faculty clashes ---
    faculty_conf_keys = (
        base_q.with_entities(
            TimetableEntry.timeslot_id,
            TimetableEntry.faculty_id,
            func.count(TimetableEntry.id).label("cnt"),
        )
        .group_by(TimetableEntry.timeslot_id, TimetableEntry.faculty_id)
        .having(func.count(TimetableEntry.id) > 1)
        .all()
    )

    faculty_clashes = []
    for ts_id, faculty_id, cnt in faculty_conf_keys:
        ts = Timeslot.query.get(ts_id)
        faculty = Faculty.query.get(faculty_id)
        entries = (
            base_q.filter_by(timeslot_id=ts_id, faculty_id=faculty_id)
            .all()
        )
        faculty_clashes.append(
            {
                "timeslot": ts,
                "faculty": faculty,
                "entries": entries,
                "count": cnt,
            }
        )

    # --- Room clashes ---
    room_conf_keys = (
        base_q.with_entities(
            TimetableEntry.timeslot_id,
            TimetableEntry.room_id,
            func.count(TimetableEntry.id).label("cnt"),
        )
        .group_by(TimetableEntry.timeslot_id, TimetableEntry.room_id)
        .having(func.count(TimetableEntry.id) > 1)
        .all()
    )

    room_clashes = []
    for ts_id, room_id, cnt in room_conf_keys:
        ts = Timeslot.query.get(ts_id)
        room = Room.query.get(room_id)
        entries = (
            base_q.filter_by(timeslot_id=ts_id, room_id=room_id)
            .all()
        )
        room_clashes.append(
            {
                "timeslot": ts,
                "room": room,
                "entries": entries,
                "count": cnt,
            }
        )

    return {
        "batch_clashes": batch_clashes,
        "faculty_clashes": faculty_clashes,
        "room_clashes": room_clashes,
    }

def build_scheduling_metrics(timetable_id):
    """
    Compute high-level scheduling metrics:
      - room utilization (overall + per room)
      - faculty load vs. max_load_per_week
    """
    from .models import Room, Faculty, Timeslot, TimetableEntry

    # Base query for this timetable
    base_q = TimetableEntry.query.filter_by(timetable_id=timetable_id)

    # ---------- ROOM UTILIZATION ----------

    rooms = Room.query.all()
    timeslots = Timeslot.query.all()

    total_room_slots = len(rooms) * len(timeslots)  # each room can host 1 class per slot

    # Count how many (room, timeslot) combinations actually used
    used_room_slots = (
        base_q.with_entities(
            TimetableEntry.room_id,
            TimetableEntry.timeslot_id
        )
        .distinct()
        .count()
    )

    overall_room_util_pct = (
        (used_room_slots / total_room_slots * 100.0) if total_room_slots > 0 else 0.0
    )

    # Per-room utilization
    per_room_util = []
    for room in rooms:
        room_classes = (
            base_q.filter_by(room_id=room.id)
            .with_entities(TimetableEntry.timeslot_id)
            .distinct()
            .count()
        )
        room_total_slots = len(timeslots)
        room_util_pct = (
            (room_classes / room_total_slots * 100.0) if room_total_slots > 0 else 0.0
        )
        per_room_util.append(
            {
                "room": room,
                "classes": room_classes,
                "total_slots": room_total_slots,
                "util_pct": room_util_pct,
            }
        )

    # ---------- FACULTY LOAD ----------

    faculties = Faculty.query.all()
    faculty_load = []
    overloaded_count = 0

    for fac in faculties:
        classes_for_fac = base_q.filter_by(faculty_id=fac.id).count()
        max_load = fac.max_load_per_week or 0

        if max_load > 0:
            load_pct = classes_for_fac / max_load * 100.0
        else:
            load_pct = 0.0

        overloaded = max_load > 0 and classes_for_fac > max_load
        if overloaded:
            overloaded_count += 1

        faculty_load.append(
            {
                "faculty": fac,
                "classes": classes_for_fac,
                "max_load": max_load,
                "load_pct": load_pct,
                "overloaded": overloaded,
            }
        )

    # Aggregate faculty stats
    total_faculty = len(faculties)
    total_classes = sum(f["classes"] for f in faculty_load)
    avg_classes_per_faculty = (total_classes / total_faculty) if total_faculty > 0 else 0.0

    metrics = {
        "overall_room_util_pct": overall_room_util_pct,
        "used_room_slots": used_room_slots,
        "total_room_slots": total_room_slots,
        "per_room_util": per_room_util,

        "faculty_load": faculty_load,
        "total_faculty": total_faculty,
        "total_classes": total_classes,
        "avg_classes_per_faculty": avg_classes_per_faculty,
        "overloaded_count": overloaded_count,
    }

    return metrics

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

    total_students = User.query.filter_by(role="student").count()

    # --- Calculate percentage change ---
    # Hardcoded previous year's student count for demonstration
    previous_year_students = 100 
    percentage_change = 0
    if previous_year_students > 0:
        percentage_change = ((total_students - previous_year_students) / previous_year_students) * 100

    return render_template(
        "admin_dashboard.html",
        user=current_user,
        latest_tt=latest_tt,
        has_timetable=has_timetable,
        days=DAYS,
        periods=periods,
        grid=grid,
        total_students=total_students,
        student_percentage_change=percentage_change,
    )


@main.route("/admin/add_test_student")
@login_required
@roles_required("admin")
def admin_add_test_student():
    username = f"test_student_{User.query.count() + 1}"
    email = f"test_student_{User.query.count() + 1}@example.com"
    password = "password" # Default password for test student

    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        flash(f"User {username} or {email} already exists.", "warning")
        return redirect(url_for("main.admin_dashboard"))

    new_user = User(username=username, email=email, role=User.ROLE_STUDENT)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash(f"Test student '{username}' added successfully.", "success")
    return redirect(url_for("main.admin_dashboard"))


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

@main.route("/admin/timetable/<int:timetable_id>/clashes")
@login_required
@roles_required("admin")
def admin_timetable_clashes(timetable_id):
    timetable = Timetable.query.get_or_404(timetable_id)

    report = build_clash_report(timetable_id)
    batch_clashes = report["batch_clashes"]
    faculty_clashes = report["faculty_clashes"]
    room_clashes = report["room_clashes"]

    total_clashes = (
        len(batch_clashes)
        + len(faculty_clashes)
        + len(room_clashes)
    )

    return render_template(
        "admin_clashes.html",
        user=current_user,
        timetable=timetable,
        batch_clashes=batch_clashes,
        faculty_clashes=faculty_clashes,
        room_clashes=room_clashes,
        total_clashes=total_clashes,
    )

@main.route("/admin/timetable/<int:timetable_id>/metrics")
@login_required
@roles_required("admin")
def admin_timetable_metrics(timetable_id):
    timetable = Timetable.query.get_or_404(timetable_id)

    metrics = build_scheduling_metrics(timetable_id)

    return render_template(
        "admin_metrics.html",
        user=current_user,
        timetable=timetable,
        metrics=metrics,
    )
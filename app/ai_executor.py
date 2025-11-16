# app/ai_executor.py

from app.models import Batch, Faculty, TimetableEntry, Room, Timeslot, User, Student, Timetable
from app import db
from app.scheduler import generate_timetable # Import generate_timetable
from datetime import datetime # Import datetime for naming timetables

def execute_ai_action(action, params, user):
    # ---------- PERMISSIONS ----------
    role = getattr(user, "role", None)

    # Only admin can do data-creation / full timetable ops
    admin_only_actions = {
        "create_batch",
        "create_faculty",
        "create_student", # Added create_student
        "regenerate_timetable",
    }

    if action in admin_only_actions and role != "admin":
        return {"success": False, "message": "Not allowed: only admin can do this."}

    # ---------- ACTION HANDLERS ----------

    # 1) CREATE BATCH (be forgiving with params)
    if action == "create_batch":
        # Try to infer as much as possible, ask only if absolutely needed
        name = params.get("name")           # e.g. "IMBA"
        section = params.get("section", "A")
        programme = params.get("programme", name)
        students = params.get("students", 25)
        semester = params.get("semester", 1)

        if not name:
            return {"success": False, "message": "Batch name is required."}

        full_name = f"{name}-{section}"

        b = Batch(
            name=full_name,
            # adjust these fields to match your actual Batch model
            size=students if hasattr(Batch, "size") else None,
            programme=programme if hasattr(Batch, "programme") else None,
            semester=semester if hasattr(Batch, "semester") else None,
        )

        db.session.add(b)
        db.session.commit()
        return {"success": True, "message": f"Batch {full_name} created with {students} students."}

    # 2) CREATE FACULTY
    if action == "create_faculty":
        name = params.get("name")
        if not name:
            return {"success": False, "message": "Faculty name is required."}

        # Adjust fields to match your Faculty model
        f = Faculty(name=name)
        db.session.add(f)
        db.session.commit()

        return {"success": True, "message": f"Faculty {name} created."}

    # 3) CREATE STUDENT
    if action == "create_student":
        username = params.get("username")
        email = params.get("email")
        password = params.get("password")
        batch_id = params.get("batch_id")

        if not all([username, email, password, batch_id]):
            return {"success": False, "message": "Username, email, password, and batch_id are required."}

        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return {"success": False, "message": f"User with username '{username}' or email '{email}' already exists."}

        # Check if batch exists
        batch = Batch.query.get(batch_id)
        if not batch:
            return {"success": False, "message": f"Batch with ID {batch_id} not found."}

        # Create User
        new_user = User(username=username, email=email, role=User.ROLE_STUDENT)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush() # Flush to get user.id

        # Create Student profile
        new_student = Student(name=username, roll_no=f"STU-{new_user.id}", user_id=new_user.id, batch_id=batch_id)
        db.session.add(new_student)
        db.session.commit()

        return {"success": True, "message": f"Student '{username}' created and assigned to batch '{batch.name}'."}


    # 4) REGENERATE TIMETABLE (admin-triggered)
    if action == "regenerate_timetable":
        # You can read optional params or just ignore and regenerate everything
        even_or_odd = params.get("even_or_odd")  # "even" or "odd" or None
        semester = params.get("semester")        # number or None

        # 1. Deactivate old timetables
        Timetable.query.update({Timetable.is_active: False})
        db.session.commit()

        # 2. Create a new one and mark active
        new_tt = Timetable(name=f"Timetable Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", is_active=True)
        db.session.add(new_tt)
        db.session.commit()

        # 3. Generate entries using new_tt.id
        tt = generate_timetable(new_tt.name, new_tt.id) # Pass new_tt.id to generate_timetable

        if tt is None:
            return {"success": False, "message": "Failed to generate timetable. Check data and constraints."}
        else:
            return {"success": True, "message": f"Timetable #{tt.id} generated with {tt.entries.count()} entries and set as active."}

    # 5) RESCHEDULE ENTRY (can be allowed for faculty too)
    if action == "reschedule_entry":
        entry_id = params.get("entry_id")
        new_ts_id = params.get("new_timeslot_id")
        new_room_id = params.get("new_room_id")

        if not entry_id or not new_ts_id or not new_room_id:
            return {"success": False, "message": "entry_id, new_timeslot_id, new_room_id are required."}

        entry = TimetableEntry.query.get(entry_id)
        if not entry:
            return {"success": False, "message": f"Entry {entry_id} not found."}

        # Minimal clash check
        room_clash = TimetableEntry.query.filter_by(
            room_id=new_room_id,
            timeslot_id=new_ts_id
        ).first()
        if room_clash and room_clash.id != entry_id:
            return {"success": False, "message": "Room already occupied at that time."}

        faculty_clash = TimetableEntry.query.filter_by(
            faculty_id=entry.faculty_id,
            timeslot_id=new_ts_id
        ).first()
        if faculty_clash and faculty_clash.id != entry_id:
            return {"success": False, "message": "Faculty already has class at that time."}

        batch_clash = TimetableEntry.query.filter_by(
            batch_id=entry.batch_id,
            timeslot_id=new_ts_id
        ).first()
        if batch_clash and batch_clash.id != entry_id:
            return {"success": False, "message": "Batch already has class at that time."}

        entry.timeslot_id = new_ts_id
        entry.room_id = new_room_id
        db.session.commit()

        return {"success": True, "message": f"Entry {entry_id} rescheduled."}

    # ---------- UNKNOWN ACTION ----------
    return {"success": False, "message": f"Unknown action: {action}"}
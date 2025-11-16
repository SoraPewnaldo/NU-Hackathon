# app/ai_executor.py

from app.models import Batch, Faculty, TimetableEntry, Room, Timeslot
from app import db

def execute_ai_action(action, params, user):
    # ---------- PERMISSIONS ----------
    role = getattr(user, "role", None)

    # Only admin can do data-creation / full timetable ops
    admin_only_actions = {
        "create_batch",
        "create_faculty",
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

    # 3) REGENERATE TIMETABLE (admin-triggered)
    if action == "regenerate_timetable":
        # You can read optional params or just ignore and regenerate everything
        even_or_odd = params.get("even_or_odd")  # "even" or "odd" or None
        semester = params.get("semester")        # number or None

        # TODO: plug in your real timetable generation function here:
        # from app.timetable import generate_timetable_for_semester
        #
        # if semester:
        #     generate_timetable_for_semester(semester, even_or_odd)
        # else:
        #     generate_full_timetable()

        # For now, just pretend:
        return {"success": True, "message": "Timetable regeneration triggered (stub, wire your generator here)."}

    # 4) RESCHEDULE ENTRY (can be allowed for faculty too)
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
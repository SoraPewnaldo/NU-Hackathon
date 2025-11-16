from app.models import TimetableEntry, Timeslot, Room, Batch, Faculty, Subject, db

def can_reschedule(entry_id, new_timeslot_id, new_room_id):
    entry = TimetableEntry.query.get(entry_id)
    if not entry:
        return False, "Entry not found."

    new_ts = Timeslot.query.get(new_timeslot_id)
    new_room = Room.query.get(new_room_id)

    if not new_ts or not new_room:
        return False, "Invalid timeslot or room."

    # 1) Check room clash
    room_conflict = TimetableEntry.query.filter_by(
        room_id=new_room_id,
        timeslot_id=new_timeslot_id
    ).first()
    if room_conflict and room_conflict.id != entry_id:
        return False, "Room already occupied at that time."

    # 2) Check faculty clash
    fac_conflict = TimetableEntry.query.filter_by(
        faculty_id=entry.faculty_id,
        timeslot_id=new_timeslot_id
    ).first()
    if fac_conflict and fac_conflict.id != entry_id:
        return False, "Faculty already has a class at that time."

    # 3) Check batch clash
    batch_conflict = TimetableEntry.query.filter_by(
        batch_id=entry.batch_id,
        timeslot_id=new_timeslot_id
    ).first()
    if batch_conflict and batch_conflict.id != entry_id:
        return False, "Batch already has a class at that time."

    return True, "OK"
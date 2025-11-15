from app import db
from app.models import (
    FacultyUnavailability,
    TimetableEntry,
    Timeslot,
    Faculty,
    FacultySubject,
    Room,
    Batch,
    Subject,
)

def apply_faculty_unavailability(unav: FacultyUnavailability) -> int:
    """
    For an approved FacultyUnavailability:
    1. Find all conflicting timetable entries.
    2. Try to assign a replacement faculty for same slot.
    3. If not possible, try to move that class to another timeslot.
    4. If still not possible, mark as CANCELLED.

    Returns: number of entries changed.
    """
    faculty_id = unav.faculty_id
    day = unav.day_of_week
    ts_id = unav.timeslot_id  # may be None = whole day

    # 1. Find affected entries
    q = TimetableEntry.query.join(Timeslot).filter(
        TimetableEntry.faculty_id == faculty_id,
        Timeslot.day_of_week == day,
    )
    if ts_id:
        q = q.filter(TimetableEntry.timeslot_id == ts_id)

    affected = q.all()
    if not affected:
        return 0

    changed = 0

    for entry in affected:
        if try_assign_replacement_faculty(entry, unav):
            changed += 1
            continue

        if try_move_to_other_timeslot(entry, unav):
            changed += 1
            continue

        # no solution -> cancel
        entry.status = "CANCELLED"
        db.session.add(entry)
        changed += 1

    db.session.commit()
    return changed


def try_assign_replacement_faculty(entry: TimetableEntry, unav: FacultyUnavailability) -> bool:
    """
    Try to find another faculty who can teach the same subject
    and is free in the same timeslot.
    """
    subject_id = entry.subject_id
    timeslot_id = entry.timeslot_id

    # 1. All faculties that can teach this subject
    teachable_faculty_ids = [
        fs.faculty_id
        for fs in FacultySubject.query.filter_by(subject_id=subject_id).all()
        if fs.faculty_id != entry.faculty_id
    ]
    if not teachable_faculty_ids:
        return False

    for fid in teachable_faculty_ids:
        # Check if that faculty already has a class in that timeslot
        clash = (
            TimetableEntry.query
            .filter_by(faculty_id=fid, timeslot_id=timeslot_id)
            .first()
        )
        if clash:
            continue

        # Also check they are not unavailable for this slot
        if is_faculty_unavailable(fid, timeslot_id):
            continue

        # Assign replacement
        entry.faculty_id = fid
        entry.status = "RESCHEDULED_REPLACEMENT"
        db.session.add(entry)
        return True

    return False


def try_move_to_other_timeslot(entry: TimetableEntry, unav: FacultyUnavailability) -> bool:
    """
    Try to move the class to some other timeslot where:
    - same batch is free
    - faculty is free
    - room is free
    - faculty is not unavailable on that slot
    """
    from app.models import Timeslot  # avoid circular

    original_ts = Timeslot.query.get(entry.timeslot_id)
    if not original_ts:
        return False

    # For simple MVP: same day only
    candidate_slots = Timeslot.query.filter_by(
        day_of_week=original_ts.day_of_week
    ).order_by(Timeslot.start_time).all()

    for ts in candidate_slots:
        if ts.id == entry.timeslot_id:
            continue

        # faculty free?
        if TimetableEntry.query.filter_by(
            faculty_id=entry.faculty_id,
            timeslot_id=ts.id,
        ).first():
            continue

        # batch free?
        if TimetableEntry.query.filter_by(
            batch_id=entry.batch_id,
            timeslot_id=ts.id,
        ).first():
            continue

        # room free?
        if TimetableEntry.query.filter_by(
            room_id=entry.room_id,
            timeslot_id=ts.id,
        ).first():
            continue

        if is_faculty_unavailable(entry.faculty_id, ts.id):
            continue

        # OK, move
        entry.timeslot_id = ts.id
        entry.status = "RESCHEDULED_MOVED"
        db.session.add(entry)
        return True

    return False


def is_faculty_unavailable(faculty_id: int, timeslot_id: int) -> bool:
    """
    Check FacultyUnavailability table:
    - full-day unavailability for that day_of_week
    - OR specific timeslot unavailability
    """
    ts = Timeslot.query.get(timeslot_id)
    if not ts:
        return False

    # full day unavailable
    full_day = FacultyUnavailability.query.filter_by(
        faculty_id=faculty_id,
        day_of_week=ts.day_of_week,
        timeslot_id=None,
        status="APPROVED",
    ).first()
    if full_day:
        return True

    # slot-specific unavailability
    specific = FacultyUnavailability.query.filter_by(
        faculty_id=faculty_id,
        timeslot_id=timeslot_id,
        status="APPROVED",
    ).first()
    return specific is not None
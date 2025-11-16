from app import db
from app.models import (
    FacultyUnavailability,
    TimetableEntry,
    Timeslot,
    FacultySubject,
)


def apply_faculty_unavailability(unav_id: int) -> int:
    """
    Freshly load the unavailability from DB and update timetable.
    """
    unav = FacultyUnavailability.query.get(unav_id)
    if not unav:
        return 0

    faculty_id = unav.faculty_id
    day = unav.day_of_week
    ts_id = unav.timeslot_id  # may be None = full day

    # 1. Find affected entries
    q = (
        TimetableEntry.query
        .join(Timeslot, TimetableEntry.timeslot_id == Timeslot.id)
        .filter(
            TimetableEntry.faculty_id == faculty_id,
            Timeslot.day_of_week == day,
        )
    )

    if ts_id:
        q = q.filter(TimetableEntry.timeslot_id == ts_id)

    affected = q.all()

    if not affected:
        return 0

    changed = 0

    for entry in affected:
        # First try replacement faculty
        if try_assign_replacement_faculty(entry):
            changed += 1
            continue

        # Then try moving the class
        if try_move_to_other_timeslot(entry):
            changed += 1
            continue

        # Finally, cancel if nothing works
        entry.status = "CANCELLED"
        db.session.add(entry)
        changed += 1

    db.session.commit()
    return changed


def try_assign_replacement_faculty(entry: TimetableEntry) -> bool:
    """
    Try to find another faculty who can teach the same subject
    and is free in the same timeslot.
    """
    subject_id = entry.subject_id
    timeslot_id = entry.timeslot_id

    # Faculties that can teach this subject (excluding current)
    teachable_faculty_ids = [
        fs.faculty_id
        for fs in FacultySubject.query.filter_by(subject_id=subject_id).all()
        if fs.faculty_id != entry.faculty_id
    ]
    if not teachable_faculty_ids:
        return False

    for fid in teachable_faculty_ids:
        # Clash check on same slot
        clash = TimetableEntry.query.filter_by(
            faculty_id=fid,
            timeslot_id=timeslot_id,
        ).first()
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


def try_move_to_other_timeslot(entry: TimetableEntry) -> bool:
    """
    Try to move class to another slot on the same day
    where faculty, batch and room are all free, and faculty is available.
    """
    from app.models import Timeslot  # avoid circular

    original_ts = Timeslot.query.get(entry.timeslot_id)
    if not original_ts:
        return False

    candidate_slots = (
        Timeslot.query
        .filter_by(day_of_week=original_ts.day_of_week)
        .order_by(Timeslot.start_time)
        .all()
    )

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

        # Move entry
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

    # Full-day unavailability
    full_day = FacultyUnavailability.query.filter_by(
        faculty_id=faculty_id,
        day_of_week=ts.day_of_week,
        timeslot_id=None,
        status="APPROVED",
    ).first()
    if full_day:
        return True

    # Slot-specific unavailability
    specific = FacultyUnavailability.query.filter_by(
        faculty_id=faculty_id,
        timeslot_id=timeslot_id,
        status="APPROVED",
    ).first()
    return specific is not None
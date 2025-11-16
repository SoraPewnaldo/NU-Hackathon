from app.models import TimetableEntry, Faculty, Room, Batch, Subject, User, Timeslot

def build_faculty_context(user):
    # adjust if your relationship is different
    faculty = Faculty.query.filter_by(user_id=user.id).first()
    if not faculty:
        return "No faculty record found for this user."

    entries = (
        TimetableEntry.query
        .filter_by(faculty_id=faculty.id)
        .join(Timeslot, TimetableEntry.timeslot_id == Timeslot.id)
        .join(Room, TimetableEntry.room_id == Room.id)
        .join(Batch, TimetableEntry.batch_id == Batch.id)
        .join(Subject, TimetableEntry.subject_id == Subject.id)
        .order_by(Timeslot.day_of_week, Timeslot.start_time)
        .limit(100)
        .all()
    )

    lines = []
    lines.append(f"Faculty: {faculty.name}")
    lines.append("Upcoming timetable (entry_id, day, start-end, batch, subject, room):")

    for e in entries:
        t = e.timeslot
        lines.append(
            f"- entry_id={e.id}, {t.day_of_week} {t.start_time}-{t.end_time}, "
            f"Batch={e.batch.name}, Subject={e.subject.name}, Room={e.room.name}"
        )

    return "\n".join(lines)


def build_admin_context(user):
    total_faculty = Faculty.query.count()
    total_batches = Batch.query.count()
    total_rooms = Room.query.count()
    total_entries = TimetableEntry.query.count()

    entries = (
        TimetableEntry.query
        .join(Timeslot, TimetableEntry.timeslot_id == Timeslot.id)
        .join(Room, TimetableEntry.room_id == Room.id)
        .join(Batch, TimetableEntry.batch_id == Batch.id)
        .join(Faculty, TimetableEntry.faculty_id == Faculty.id)
        .join(Subject, TimetableEntry.subject_id == Subject.id)
        .order_by(Timeslot.day_of_week, Timeslot.start_time)
        .limit(30)
        .all()
    )

    lines = []
    lines.append("Admin overview:")
    lines.append(f"- Faculty: {total_faculty}")
    lines.append(f"- Batches: {total_batches}")
    lines.append(f"- Rooms: {total_rooms}")
    lines.append(f"- Timetable entries: {total_entries}")
    lines.append("")
    lines.append("Sample entries (entry_id, day, time, batch, subject, faculty, room):")

    for e in entries:
        t = e.timeslot
        lines.append(
            f"- entry_id={e.id}, {t.day_of_week} {t.start_time}-{t.end_time}, "
            f"Batch={e.batch.name}, Subject={e.subject.name}, "
            f"Faculty={e.faculty.name}, Room={e.room.name}"
        )

    return "\n".join(lines)

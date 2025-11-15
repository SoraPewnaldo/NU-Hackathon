# app/scheduler.py

from app import db
from app.models import (
    Institution,
    Room,
    Batch,
    Subject,
    Faculty,
    FacultySubject,
    Timeslot,
    Timetable,
    TimetableEntry,
)

from ortools.sat.python import cp_model


def generate_timetable_for_institution(institution_id: int) -> int:
    """
    Generic timetable generator using current DB data
    for a given institution.

    Returns: number of TimetableEntry rows created.
    """

    inst = Institution.query.get(institution_id)
    if not inst:
        raise ValueError(f"Institution {institution_id} not found")

    # 1) Fetch data for this institution
    rooms = Room.query.filter_by(institution_id=institution_id).all()
    batches = Batch.query.filter_by(institution_id=institution_id).all()
    subjects = Subject.query.filter_by(institution_id=institution_id).all()
    faculties = Faculty.query.filter_by(institution_id=institution_id).all()
    timeslots = Timeslot.query.order_by(
        Timeslot.day_of_week, Timeslot.start_time
    ).all()

    print(f"Rooms: {len(rooms)}")
    print(f"Batches: {len(batches)}")
    print(f"Subjects: {len(subjects)}")
    print(f"Faculties: {len(faculties)}")
    print(f"Timeslots: {len(timeslots)}")

    if not rooms or not batches or not subjects or not faculties or not timeslots:
        # You can throw or return 0, but better to crash visibly in dev
        raise RuntimeError("Not enough data to generate timetable "
                           "(need rooms, batches, subjects, faculty, timeslots).")

    # Map subject_id -> list of faculty_ids that can teach it
    subject_faculty_map = {}
    fs_links = (
        FacultySubject.query
        .join(Faculty, FacultySubject.faculty_id == Faculty.id)
        .filter(Faculty.institution_id == institution_id)
        .all()
    )
    for fs in fs_links:
        subject_faculty_map.setdefault(fs.subject_id, []).append(fs.faculty_id)

    # 2) Build "class requirements"
    # For now: for each Batch, all Subjects (you can refine by programme/semester)
    class_reqs = []  # list of dicts with ids
    for batch in batches:
        # TODO: filter subjects per batch using your own logic
        batch_subjects = subjects

        for subj in batch_subjects:
            # Use classes_per_week defined by admin
            cpw = subj.classes_per_week or 0
            for _ in range(cpw):
                class_reqs.append(
                    {
                        "batch_id": batch.id,
                        "subject_id": subj.id,
                    }
                )

    if not class_reqs:
        raise RuntimeError("No class requirements (classes_per_week likely 0).")

    # 3) Setup OR-Tools CP-SAT model
    model = cp_model.CpModel()

    # Index maps for easier variable naming
    room_ids = [r.id for r in rooms]
    timeslot_ids = [t.id for t in timeslots]
    faculty_ids = [f.id for f in faculties]

    # Decision variables:
    # For each class requirement i and each (timeslot, room, faculty), 0/1 var
    x = {}  # (i, ts_id, room_id, faculty_id) -> BoolVar

    for i, c in enumerate(class_reqs):
        subj_id = c["subject_id"]
        possible_faculties = subject_faculty_map.get(subj_id, [])
        if not possible_faculties:
            # no faculty can teach this subject: skip / or raise
            continue

        for ts in timeslot_ids:
            for room in room_ids:
                for f_id in possible_faculties:
                    x[(i, ts, room, f_id)] = model.NewBoolVar(
                        f"x_c{i}_ts{ts}_r{room}_f{f_id}"
                    )

        # each class must be assigned exactly once (one slot, one room, one faculty)
        model.Add(
            sum(
                x[(i, ts, room, f_id)]
                for ts in timeslot_ids
                for room in room_ids
                for f_id in possible_faculties
            ) == 1
        )

    # 4) No faculty clashes, no room clashes, no batch clashes
    # We need a quick way to know which class_reqs belong to same batch, etc.
    # Precompute:
    class_batch_ids = [c["batch_id"] for c in class_reqs]
    class_subject_ids = [c["subject_id"] for c in class_reqs]

    # Faculty clashes:
    for f_id in faculty_ids:
        for ts in timeslot_ids:
            model.Add(
                sum(
                    x[(i, ts, room, f_id)]
                    for i, c in enumerate(class_reqs)
                    for room in room_ids
                    if (i, ts, room, f_id) in x
                ) <= 1
            )

    # Room clashes:
    for room in room_ids:
        for ts in timeslot_ids:
            model.Add(
                sum(
                    x[(i, ts, room, f_id)]
                    for i, c in enumerate(class_reqs)
                    for f_id in faculty_ids
                    if (i, ts, room, f_id) in x
                ) <= 1
            )

    # Batch clashes:
    for batch in batches:
        for ts in timeslot_ids:
            model.Add(
                sum(
                    x[(i, ts, room, f_id)]
                    for i, c in enumerate(class_reqs)
                    if c["batch_id"] == batch.id
                    for room in room_ids
                    for f_id in faculty_ids
                    if (i, ts, room, f_id) in x
                ) <= 1
            )

    # (OPTIONAL) Example: soften faculty load / spread classes etc. with objective later.
    model.Maximize(0)  # no specific objective for now, just any feasible solution.

    # 5) Solve
    solver = cp_model.CpSolver()
    solver_status = solver.Solve(model)

    if solver_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("No feasible timetable solution found.")

    # 6) Get or create active timetable
    timetable = (
        Timetable.query
        .filter_by(institution_id=institution_id, is_active=True)
        .order_by(Timetable.created_at.desc())
        .first()
    )
    if not timetable:
        timetable = Timetable(
            institution_id=institution_id,
            name=f"{inst.name} Timetable",
            is_active=True,
        )
        db.session.add(timetable)
        db.session.commit()

    # Clear old entries for this active timetable
    TimetableEntry.query.filter_by(timetable_id=timetable.id).delete()
    db.session.commit()

    # 7) Store new entries in DB
    created = 0
    for i, c in enumerate(class_reqs):
        batch_id = c["batch_id"]
        subj_id = c["subject_id"]

        # Find assignment chosen by solver
        assigned = None
        for ts in timeslot_ids:
            for room in room_ids:
                for f_id in faculty_ids:
                    key = (i, ts, room, f_id)
                    if key in x and solver.Value(x[key]) == 1:
                        assigned = (ts, room, f_id)
                        break
                if assigned:
                    break
            if assigned:
                break

        if not assigned:
            # This should not happen if constraints are correct, but be safe.
            continue

        ts_id, room_id, faculty_id = assigned

        entry = TimetableEntry(
            timetable_id=timetable.id,
            batch_id=batch_id,
            subject_id=subj_id,
            faculty_id=faculty_id,
            room_id=room_id,
            timeslot_id=ts_id,
            status="NORMAL",
        )
        db.session.add(entry)
        created += 1

    db.session.commit()
    return created

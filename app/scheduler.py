from ortools.sat.python import cp_model
from flask import current_app
from .models import (
    Room,
    Batch,
    Subject,
    Faculty,
    Timeslot,
    Timetable,
    TimetableEntry,
    FacultySubject,
)
from . import db


def generate_timetable(name: str = "Auto Generated Timetable"):
    """
    Build and solve a basic timetable using OR-Tools CP-SAT.
    Returns the created Timetable instance or None if no solution.
    """

    # We need an app context to talk to the DB when called from scripts/other code
    with current_app.app_context():
        rooms = Room.query.all()
        batches = Batch.query.all()
        subjects = Subject.query.all()
        timeslots = Timeslot.query.order_by(
            Timeslot.day_of_week, Timeslot.start_time
        ).all()

        if not rooms or not batches or not subjects or not timeslots:
            print("❌ Not enough data to generate timetable.")
            return None

        # --------------------------------------------------
        # 1) Build class instances (what we need to schedule)
        # --------------------------------------------------
        # Each class instance = one weekly session:
        # (batch, subject, faculty, is_lab)
        class_instances = []

        for batch in batches:
            for subject in subjects:
                # simple rule: subject is only for matching semester
                if subject.semester != batch.semester:
                    continue

                # Which faculties can teach this subject?
                fs_mappings = FacultySubject.query.filter_by(
                    subject_id=subject.id
                ).all()
                if not fs_mappings:
                    print(
                        f"⚠️ No faculty mapping for subject {subject.code}, skipping."
                    )
                    continue

                # For hackathon simplicity, pick first mapped faculty
                faculty = fs_mappings[0].faculty

                # classes_per_week tells us how many sessions this subject needs
                for _ in range(subject.classes_per_week):
                    class_instances.append(
                        {
                            "batch_id": batch.id,
                            "subject_id": subject.id,
                            "faculty_id": faculty.id,
                            "is_lab": subject.is_lab,
                        }
                    )

        if not class_instances:
            print("❌ No class instances built. Check seed data.")
            return None

        num_classes = len(class_instances)
        num_rooms = len(rooms)
        num_slots = len(timeslots)

        print(f"📊 Building model for {num_classes} class instances ...")

        # --------------------------------------------------
        # 2) Define CP-SAT model and decision variables
        # --------------------------------------------------
        model = cp_model.CpModel()

        # x[c, r, s] = 1 if class c happens in room r at timeslot s
        x = {}
        for c in range(num_classes):
            is_lab = class_instances[c]["is_lab"]

            for r in range(num_rooms):
                # Lab subjects must be in lab rooms
                if is_lab and rooms[r].room_type != "lab":
                    continue
                # Optional rule: non-lab subjects don't use labs
                if not is_lab and rooms[r].room_type == "lab":
                    continue

                for s in range(num_slots):
                    x[(c, r, s)] = model.NewBoolVar(f"x_c{c}_r{r}_s{s}")

        # --------------------------------------------------
        # 3) Constraints
        # --------------------------------------------------

        # (a) Each class must be scheduled exactly once
        for c in range(num_classes):
            relevant_vars = [
                x[(c, r, s)]
                for r in range(num_rooms)
                for s in range(num_slots)
                if (c, r, s) in x
            ]
            if not relevant_vars:
                print(f"❌ Class {c} has no valid (room, slot) combinations.")
                return None
            model.Add(sum(relevant_vars) == 1)

        # (b) Room clash: at most one class per room per timeslot
        for r in range(num_rooms):
            for s in range(num_slots):
                vars_in_room_slot = [
                    x[(c, r, s)]
                    for c in range(num_classes)
                    if (c, r, s) in x
                ]
                if vars_in_room_slot:
                    model.Add(sum(vars_in_room_slot) <= 1)

        # (c) Faculty clash: a faculty can't be in two places at same time
        all_faculties = Faculty.query.all()
        for s in range(num_slots):
            for faculty in all_faculties:
                vars_for_faculty = []
                for c in range(num_classes):
                    if class_instances[c]["faculty_id"] != faculty.id:
                        continue
                    for r in range(num_rooms):
                        if (c, r, s) in x:
                            vars_for_faculty.append(x[(c, r, s)])
                if vars_for_faculty:
                    model.Add(sum(vars_for_faculty) <= 1)

        # (d) Batch clash: a batch can't attend two classes at same time
        for s in range(num_slots):
            for batch in batches:
                vars_for_batch = []
                for c in range(num_classes):
                    if class_instances[c]["batch_id"] != batch.id:
                        continue
                    for r in range(num_rooms):
                        if (c, r, s) in x:
                            vars_for_batch.append(x[(c, r, s)])
                if vars_for_batch:
                    model.Add(sum(vars_for_batch) <= 1)

        # --------------------------------------------------
        # 4) Solve (we only care about "any" feasible solution)
        # --------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0  # safety limit

        result_status = solver.Solve(model)

        if result_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("❌ No feasible timetable found.")
            return None

        print("✅ Timetable solution found. Saving to database...")

        # --------------------------------------------------
        # 5) Save solution as Timetable + TimetableEntry rows
        # --------------------------------------------------
        timetable = Timetable(name=name)
        db.session.add(timetable)
        db.session.commit()  # now timetable.id is available

        for c in range(num_classes):
            ci = class_instances[c]
            chosen_room_id = None
            chosen_slot_id = None

            for r in range(num_rooms):
                for s in range(num_slots):
                    if (c, r, s) in x and solver.Value(x[(c, r, s)]) == 1:
                        chosen_room_id = rooms[r].id
                        chosen_slot_id = timeslots[s].id
                        break
                if chosen_room_id is not None:
                    break

            if chosen_room_id is None or chosen_slot_id is None:
                print(f"⚠️ Class {c} has no chosen room/slot in solution, skipping.")
                continue

            entry = TimetableEntry(
                timetable_id=timetable.id,
                batch_id=ci["batch_id"],
                subject_id=ci["subject_id"],
                faculty_id=ci["faculty_id"],
                room_id=chosen_room_id,
                timeslot_id=chosen_slot_id,
            )
            db.session.add(entry)

        db.session.commit()
        print(
            f"✅ Timetable saved with id={timetable.id} and "
            f"{timetable.entries.count()} entries."
        )

        return timetable
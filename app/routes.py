
@main.route("/timetables")
@login_required
@roles_required("admin", "hod", "faculty", "student")
def list_timetables():
    timetables = Timetable.query.order_by(Timetable.created_at.desc()).all()
    return render_template("timetable_list.html", timetables=timetables)

@main.route("/faculty/my_timetable")
@login_required
@roles_required("faculty", "hod", "admin")
def faculty_my_timetable():
    # Find faculty profile linked to current user
    fac = current_user.faculty_profile
    if fac is None:
        flash("No faculty profile linked to this user.", "danger")
        return redirect(url_for("main.dashboard"))

    # Use latest timetable
    tt = Timetable.query.order_by(Timetable.created_at.desc()).first()
    if tt is None:
        flash("No timetable generated yet.", "warning")
        return redirect(url_for("main.dashboard"))

    # All entries in this timetable for this faculty
    entries = TimetableEntry.query.filter_by(
        timetable_id=tt.id,
        faculty_id=fac.id
    ).all()

    timeslots = Timeslot.query.order_by(
        Timeslot.day_of_week, Timeslot.start_time
    ).all()

    # Build lookup: timeslot_id -> list of entries (usually 0 or 1)
    slot_entries = {}
    for e in entries:
        slot_entries.setdefault(e.timeslot_id, []).append(e)

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return render_template(
        "faculty_my_timetable.html",
        timetable=tt,
        faculty=fac,
        timeslots=timeslots,
        slot_entries=slot_entries,
        day_names=day_names,
    )

@main.route("/student/batch_timetable", methods=["GET", "POST"])
@login_required
@roles_required("student", "hod", "admin")
def student_batch_timetable():
    tt = Timetable.query.order_by(Timetable.created_at.desc()).first()
    if tt is None:
        flash("No timetable generated yet.", "warning")
        return redirect(url_for("main.dashboard"))

    batches = Batch.query.order_by(Batch.name).all()

    selected_batch_id = None
    entries_map = {}
    timeslots = Timeslot.query.order_by(
        Timeslot.day_of_week, Timeslot.start_time
    ).all()
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    if request.method == "POST":
        selected_batch_id = int(request.form.get("batch_id"))
        entries = TimetableEntry.query.filter_by(
            timetable_id=tt.id,
            batch_id=selected_batch_id
        ).all()
        # timeslot_id -> entry
        for e in entries:
            entries_map[e.timeslot_id] = e

    return render_template(
        "student_batch_timetable.html",
        timetable=tt,
        batches=batches,
        selected_batch_id=selected_batch_id,
        timeslots=timeslots,
        entries_map=entries_map,
        day_names=day_names,
    )

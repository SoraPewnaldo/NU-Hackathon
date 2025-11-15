
@main.route("/admin/generate_timetable", methods=["POST"])
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
@roles_required("admin", "hod", "faculty", "student")
def view_timetable(timetable_id):
    timetable = Timetable.query.get_or_404(timetable_id)

    # Order timeslots by day + time
    timeslots = Timeslot.query.order_by(
        Timeslot.day_of_week, Timeslot.start_time
    ).all()
    batches = Batch.query.order_by(Batch.name).all()

    # Preload all entries for this timetable
    entries = TimetableEntry.query.filter_by(timetable_id=timetable.id).all()

    # Build quick lookup: (batch_id, timeslot_id) -> entry
    entry_map = {}
    for e in entries:
        entry_map[(e.batch_id, e.timeslot_id)] = e

    # We also need day names
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return render_template(
        "timetable_view.html",
        timetable=timetable,
        timeslots=timeslots,
        batches=batches,
        entry_map=entry_map,
        day_names=day_names,
    )

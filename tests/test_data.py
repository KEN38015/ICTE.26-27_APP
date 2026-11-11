"""Data quality checks: every required dataset exists and links are valid."""


def test_minimum_datasets_present(data):
    assert data.teachers and data.rooms and data.policies and data.periods
    assert data.events and data.faqs and data.students and data.timetable


def test_teachers_have_required_fields(data):
    for t in data.teachers.values():
        assert t["first_name"] and t["last_name"] and t["subjects"] and t["department"] and t["room_id"]


def test_rooms_have_directions(data):
    for r in data.rooms.values():
        assert r["building_id"] and r["floor"] and r["directions"], r["room_id"]


def test_periods_are_in_time_order(data):
    starts = [p["start"] for p in data.periods]
    assert starts == sorted(starts)


def test_every_class_has_a_full_week(data):
    slots = {(r["day"], r["period_id"]) for r in data.timetable}
    for group in {s["class_group"] for s in data.students.values()}:
        rows = {(r["day"], r["period_id"]) for r in data.timetable if r["class_group"] == group}
        assert rows == slots, group


def test_live_data_folder_is_valid():
    """The real /data folder (not just the test sample) must load without problems."""
    from app.data import DEFAULT_DATA_DIR, load_data
    live = load_data(DEFAULT_DATA_DIR)
    assert live.teachers and live.rooms


def test_students_have_no_sensitive_fields(data):
    sensitive = {"address", "phone", "email", "dob", "birthday", "medical", "grades", "password"}
    for s in data.students.values():
        assert not sensitive & {k.lower() for k in s}

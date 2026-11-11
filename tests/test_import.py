"""Tests for the spreadsheet template and importer, using a deliberately messy sheet."""

import datetime as dt
import shutil
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from tools import import_sheet, make_template

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_data"


@pytest.fixture
def out_dir(tmp_path):
    d = tmp_path / "data"
    shutil.copytree(FIXTURE, d)
    return d


def messy_workbook(path: Path, *, break_it: bool = False) -> Path:
    """Looks like a real team sheet: odd tab names, title rows, mixed formats."""
    wb = Workbook()
    wb.remove(wb.active)

    ws = wb.create_sheet("Buildings")
    ws.append(["Code", "Building name", "Name (Vietnamese)"])
    ws.append(["A", "Main Block", "Khu chính"])
    ws.append(["b", "Science Block", "Khu Khoa học"])
    ws.append(["G", "Gym", "Nhà thể chất"])

    ws = wb.create_sheet("rooms ")
    ws.append(["ROOM LIST — updated by Minh"])            # title row above the header
    ws.append([])
    ws.append(["Room number", "Name", "Other names", "Building", "Level", "Directions", "Directions (Vietnamese)"])
    ws.append(["a 101", "Reception", "office, front office, lễ tân", "A", "Ground", "Walk in the front door. It is on the left.", ""])
    ws.append(["B201", "ICT Room", "computer lab; IT room ;phòng máy", "B", "Level 1", "Take the stairs. First door on the right.", ""])
    ws.append([])                                           # blank row in the middle
    ws.append(["B202", "Science Lab", "lab", "B", "Level 2", "Take the stairs to Level 2.", ""])
    ws.append(["G001", "Gym", "sports hall", "G", "Ground", "Through the double doors.", ""])
    ws.append(["A102", "Maths Room", "math room", "A", "Level 1", "Upstairs, second door.", ""])

    ws = wb.create_sheet("Staff")
    ws.append(["ID", "Full name", "Job title", "Subjects", "Dept", "Room", "Phone"])
    ws.append(["T1", "Ms. Sarah Nguyen", "English Teacher", "English, Literature", "English", "A101", "0901 234 567"])
    ws.append(["T2", "Thầy Trần Văn Hùng", "Maths Teacher", "Maths", "Mathematics", "A102", ""])
    ws.append(["T3", "Mr James Walker", "Science Teacher", "Physics", "Science", "B202", ""])
    ws.append(["T4", "Cô Lê Thị Lan", "ICT Teacher", "ICT", "Technology", "B201", ""])
    ws.append(["T5", "Mr Tuan Vo", "PE Teacher", "PE", "Sport", "G001" if not break_it else "GYM-9", ""])
    ws.append(["T6", "Dr Robert Hughes", "Principal", "Leadership", "Leadership", "A101", ""])

    ws = wb.create_sheet("Policy")
    ws.append(["Title", "Category", "Keywords", "Summary"])
    ws.append(["Mobile Phone Policy", "Conduct", "phone, mobile", "Phones stay in lockers during class."])
    ws.append(["Uniform Policy", "Conduct", "uniform;dress code", "Wear full uniform every day."])

    ws = wb.create_sheet("FAQ")
    ws.append(["Question", "Category", "Keywords", "Answer"])
    ws.append(["What do I do if I'm late?", "Attendance", "late, missed bus", "Sign in at Reception."])

    ws = wb.create_sheet("Bell times")
    ws.append(["Period", "Name", "Start time", "End time", "Type"])
    ws.append(["P2", "Period 2", "9h05", "9:55", "Lesson"])          # out of order on purpose
    ws.append(["P1", "Period 1", dt.time(8, 15), "9.05am", "class"])
    ws.append(["L", "Lunch", "11:55", "12:40", "Lunch"])
    ws.append(["P3", "Period 3", "12:40", "1:30 pm", "tiết học"])
    ws.append(["END", "School finishes", "13:30", "", "tan học"])

    ws = wb.create_sheet("Calendar")
    ws.append(["Event", "Date", "Start", "End", "Venue", "Details"])
    ws.append(["Sports Day", dt.datetime(2027, 2, 12), "8:30", "14:00", "G001", "Athletics."])
    ws.append(["Science Fair", "20/11/2026", "9:00", "14:00", "b202", ""])
    if break_it:
        ws.append(["Concert", "next Friday", "18:00", "17:00", "", ""])

    wb.save(path)
    return path


def test_template_has_all_tabs_and_dropdowns(tmp_path):
    path = make_template.build(tmp_path / "t.xlsx")
    wb = load_workbook(path)
    for name in ["Instructions", "School", "Buildings", "Rooms", "Teachers", "Policies", "FAQs", "Schedule",
                 "Events", "Clubs", "Examples"]:
        assert name in wb.sheetnames
    rooms = wb["Rooms"]
    assert [c.value for c in rooms[1]][:2] == ["room_id", "name"]
    assert any("Buildings!" in dv.formula1 for dv in rooms.data_validations.dataValidation)


def test_template_round_trip_reports_empty_tabs(tmp_path, out_dir):
    path = make_template.build(tmp_path / "t.xlsx")
    report = import_sheet.run(path, out_dir, check_only=True)
    assert any("Buildings: tab is missing or empty" in e for e in report.errors)


def test_messy_sheet_imports_cleanly(tmp_path, out_dir):
    report = import_sheet.run(messy_workbook(tmp_path / "messy.xlsx"), out_dir)
    assert report.errors == [], report.errors

    from app.data import load_data
    data = load_data(out_dir)
    # codes cleaned: "a 101" -> A101, "b" -> B
    assert "A101" in data.rooms and data.rooms["B201"]["building_id"] == "B"
    # lists: commas and spaces -> ;
    assert data.rooms["B201"]["aliases"] == ["computer lab", "IT room", "phòng máy"]
    # full names split, Vietnamese order handled, titles cleaned
    hung = data.teachers["T2"]
    assert (hung["title"], hung["first_name"], hung["last_name"]) == ("Thầy", "Hùng", "Trần")
    assert data.teachers["T1"]["title"] == "Ms"
    # phone column ignored (privacy)
    assert all("phone" not in k.lower() for k in data.teachers["T1"])
    assert any("Phone" in w for w in report.warnings)
    # times normalised and schedule sorted
    assert [(p["period_id"], p["start"], p["end"]) for p in data.periods][:2] == [("P1", "08:15", "09:05"), ("P2", "09:05", "09:55")]
    assert next(p for p in data.periods if p["period_id"] == "P3")["end"] == "13:30"
    assert next(p for p in data.periods if p["period_id"] == "END")["end"] == "13:30"
    # dates: real date cell and day-first text
    assert {e["name"]: e["date"] for e in data.events} == {"Sports Day": "2027-02-12", "Science Fair": "2026-11-20"}
    # automatic IDs, sample banner off, fictional students rebuilt on the new teachers
    assert {p["policy_id"] for p in data.policies} == {"POL01", "POL02"}
    assert data.school["is_sample"] is False
    assert all(r["teacher_id"] in data.teachers for r in data.timetable)
    assert data.users["teacher"]["linked_id"] in data.teachers


def test_imported_data_answers_questions(tmp_path, out_dir):
    import_sheet.run(messy_workbook(tmp_path / "messy.xlsx"), out_dir)
    from app.data import load_data
    from app.search import Viewer, answer
    data = load_data(out_dir)
    assert answer(data, "where is the computer lab").hits[0].item["room_id"] == "B201"
    assert answer(data, "thầy Hùng").hits[0].item["teacher_id"] == "T2"
    assert answer(data, "my timetable", Viewer("student", "S001")).status == "ok"


def test_broken_sheet_writes_nothing(tmp_path, out_dir):
    before = (out_dir / "teachers.csv").read_text()
    report = import_sheet.run(messy_workbook(tmp_path / "broken.xlsx", break_it=True), out_dir)
    text = "\n".join(report.errors)
    assert "room_id 'GYM-9' doesn't exist in the Rooms tab" in text
    assert "can't read date 'next Friday'" in text
    assert (out_dir / "teachers.csv").read_text() == before


def test_cleaners():
    r = import_sheet.Report()
    assert import_sheet.clean_time("8h15", "x", r) == "08:15"
    assert import_sheet.clean_time("1:30 pm", "x", r) == "13:30"
    assert import_sheet.clean_time("0815", "x", r) == "08:15"
    assert import_sheet.clean_time(0.5, "x", r) == "12:00"
    assert import_sheet.clean_date("2026/11/20", "x", r) == "2026-11-20"
    assert import_sheet.clean_date("20 Nov 2026", "x", r) == "2026-11-20"
    assert import_sheet.clean_day("thứ 2", "x", r) == "Monday"
    assert import_sheet.clean_list("a, b ; a\nc") == "a;b;c"
    assert r.errors == []

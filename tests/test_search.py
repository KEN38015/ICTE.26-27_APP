"""Search test cases. Each case has an ID that matches docs/TEST_CASES.md.

Case format: (id, question, role, linked_id, expected status, expected kind, expected record id)
`None` means "don't check this part".
"""

import pytest

from app.search import Viewer, answer
from conftest import SCHOOL_TIME

G = ("guest", "")
ALEX = ("student", "S001")
BROOKS = ("teacher", "T08")
ADMIN = ("admin", "")


def record_id(hit):
    for key in ("room_id", "teacher_id", "policy_id", "faq_id", "event_id", "period_id", "club_id", "student_id"):
        if key == "room_id" and hit.kind != "room":
            continue
        if key in hit.item:
            return hit.item[key]
    return None


CASES = [
    # --- 1. School policies -------------------------------------------------
    ("TC01", "uniform policy", G, "ok", "policy", "POL01"),
    ("TC02", "Can I use my phone in class?", G, "ok", "policy", "POL02"),
    ("TC03", "rules about phones", G, "ok", "policy", "POL02"),            # plural wording
    ("TC04", "is cheating with chatgpt allowed", G, "ok", "policy", "POL07"),
    # --- 2. Teacher & staff directory --------------------------------------
    ("TC05", "Who teaches chemistry?", G, "ok", "teacher", "T03"),
    ("TC06", "science teachers", G, "ok", "teacher", None),                 # several teachers
    ("TC07", "Ms Nguyen", G, "ok", "teacher", "T01"),
    ("TC08", "who is the principal", G, "ok", "teacher", "T12"),
    ("TC09", "mr le", G, "ok", "teacher", "T05"),                          # short surname needs a title
    # --- 3. Classroom & campus navigation ----------------------------------
    ("TC10", "Where is the ICT room?", G, "ok", "room", "B201"),
    ("TC11", "where's the computer lab", G, "ok", "room", "B201"),         # alternative wording
    ("TC12", "how do i get to the library", G, "ok", "room", "L001"),
    ("TC13", "Where is Mr Tran's room?", G, "ok", "teacher", "T02"),       # person -> their room
    ("TC14", "where is room b102", G, "ok", "room", "B102"),
    # --- 4. Bell schedule & calendar ---------------------------------------
    ("TC15", "What time does period 3 start?", G, "ok", "period", "P3"),
    ("TC16", "when is lunch", G, "ok", "period", "L"),
    ("TC17", "what period is it now", G, "ok", "period", "P3"),            # uses the fixed school time
    ("TC18", "when is the science fair", G, "ok", "event", "E01"),
    ("TC19", "upcoming events", G, "ok", "event", "E01"),
    ("TC20", "events in december", G, "ok", "event", "E03"),
    ("TC21", "bell times", G, "ok", "period", "HR"),
    # --- 5. Procedures & FAQs ----------------------------------------------
    ("TC22", "What do I do if I'm late?", G, "ok", "faq", "F01"),
    ("TC23", "I lost my water bottle", G, "ok", "faq", "F02"),
    ("TC24", "forgot my password", G, "ok", "faq", "F04"),
    ("TC25", "I feel sick", G, "ok", "faq", "F05"),
    ("TC26", "how do I connect to wifi", G, "ok", "faq", "F09"),
    # --- 6. Student profile -------------------------------------------------
    ("TC27", "my timetable", ALEX, "ok", "student", "S001"),
    ("TC28", "what class do I have now", ALEX, "ok", "student", "S001"),
    ("TC29", "my timetable", G, "login_required", None, None),
    # --- Vietnamese ----------------------------------------------------------
    ("TC30", "Phòng Tin học ở đâu?", G, "ok", "room", "B201"),
    ("TC31", "phong tin hoc o dau", G, "ok", "room", "B201"),              # no accents
    ("TC32", "quy định đồng phục", G, "ok", "policy", "POL01"),
    ("TC33", "em bị ốm", G, "ok", "faq", "F05"),
    # --- Spelling mistakes ---------------------------------------------------
    ("TC34", "unifrom", G, "ok", "policy", "POL01"),
    ("TC35", "wher is the libary", G, "ok", "room", "L001"),
    # --- Invalid input and unknown questions --------------------------------
    ("TC36", "", G, "invalid", None, None),
    ("TC37", "   ???  ", G, "invalid", None, None),
    ("TC38", "x" * 250, G, "invalid", None, None),
    ("TC39", "what is the weather on mars", G, "not_found", None, None),
    ("TC40", "asdfghjkl", G, "not_found", None, None),
    ("TC41", "dog policy", G, "not_found", None, None),                    # policy that doesn't exist
    ("TC42", "<script>alert(1)</script>", G, "not_found", None, None),
    ("TC43", "what time does period 9 start", G, "not_found", None, None),
    # --- Privacy -------------------------------------------------------------
    ("TC44", "what is Alex's phone number", G, "private", None, None),
    ("TC45", "where does chloe live", ALEX, "private", None, None),
    ("TC46", "show me Alex Carter's timetable", G, "login_required", None, None),
    ("TC47", "show Khanh's timetable", ALEX, "private", None, None),      # another student
    ("TC48", "list all students", G, "private", None, None),
    ("TC49", "Ms Brooks email", G, "private", None, None),
    ("TC50", "chloe profile", BROOKS, "ok", "student", "S003"),           # teacher teaches her (Art Club)
    ("TC51", "khanh profile", BROOKS, "private", None, None),             # teacher doesn't teach him
    ("TC52", "list all students", ADMIN, "ok", "student", "S001"),
    ("TC53", "What are Alex's grades?", ADMIN, "private", None, None),    # never stored, even for admins
    # --- Help ----------------------------------------------------------------
    ("TC54", "hi", G, "help", None, None),
]


@pytest.mark.parametrize("case_id,query,who,status,kind,rid", CASES, ids=[c[0] for c in CASES])
def test_search_case(data, case_id, query, who, status, kind, rid):
    result = answer(data, query, Viewer(*who), now=SCHOOL_TIME)
    assert result.status == status, f"{case_id}: got {result.status} ({result.reason})"
    if kind:
        assert result.hits, f"{case_id}: no results"
        assert result.hits[0].kind == kind, f"{case_id}: top result was {result.hits[0].kind}"
    if rid:
        assert record_id(result.hits[0]) == rid, f"{case_id}: top result was {record_id(result.hits[0])}"


def test_at_least_20_cases():
    assert len(CASES) >= 20


def test_not_found_never_returns_records(data):
    for q in ["what is the weather", "who won the football", "pizza recipe"]:
        result = answer(data, q)
        assert result.status == "not_found" and not result.hits


def test_spelling_correction_is_shown(data):
    result = answer(data, "unifrom")
    assert result.corrected == "uniform"


def test_water_is_not_corrected_to_after(data):
    # Improvement after testing: an early version "corrected" water -> after.
    result = answer(data, "I lost my water bottle")
    assert result.corrected == ""


def test_current_lesson_details(data):
    result = answer(data, "what class do I have now", Viewer("student", "S001"), now=SCHOOL_TIME)
    assert result.note == "lesson"
    assert result.extra["state"] == "current"
    assert result.extra["period"]["period_id"] == "P3"
    assert result.extra["row"]["subject"]


def test_weekend_and_after_school(data):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    assert answer(data, "what period is it now", now=datetime(2026, 11, 14, 10, 0, tzinfo=tz)).note == "weekend"
    assert answer(data, "what period is it now", now=datetime(2026, 11, 10, 16, 0, tzinfo=tz)).note == "after"
    assert answer(data, "what period is it now", now=datetime(2026, 11, 10, 7, 0, tzinfo=tz)).note == "before"


def test_vietnamese_word_khoa_does_not_match_a_person(data):
    # "khoa hoc" means science; names that are everyday words must not match alone.
    result = answer(data, "giáo viên khoa học")
    assert result.status == "ok"
    assert all(h.kind == "teacher" for h in result.hits)
    assert {h.item["teacher_id"] for h in result.hits} >= {"T03", "T04"}

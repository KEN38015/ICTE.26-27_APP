"""SenTia handbook test cases: real student questions against the live /data folder.

IDs match the "SenTia handbook cases" table in docs/TEST_CASES.md.
Unlike tests/test_search.py (fixed sample school), these run on the real data.
"""

import pytest

from app.data import DEFAULT_DATA_DIR, load_data
from app.search import answer


@pytest.fixture(scope="module")
def live():
    return load_data(DEFAULT_DATA_DIR)


def top_id(result):
    item = result.hits[0].item
    return (item.get("policy_id") or item.get("faq_id") or item.get("room_id") or item.get("period_id")
            or item.get("event_id"))


def ids(result):
    return {h.item.get("policy_id") or h.item.get("faq_id") for h in result.hits}


# (id, question, acceptable top results)
CASES = [
    ("ST01", "What do I do if I'm late?", {"F01"}),
    ("ST02", "uniform policy", {"POL01"}),
    ("ST03", "I forgot my uniform", {"POL01", "F02"}),
    ("ST04", "can I use my phone", {"POL03"}),
    ("ST05", "my phone was confiscated", {"POL37", "F09"}),
    ("ST06", "can I bring snacks", {"POL15", "F06"}),
    ("ST07", "can I bring medicine", {"POL17", "F05"}),
    ("ST08", "I feel sick", {"F04"}),
    ("ST09", "how do I take a day off", {"F03"}),
    ("ST10", "how many days can I miss", {"F19"}),
    ("ST11", "how many library books can I borrow", {"POL29", "F11"}),
    ("ST12", "I lost my locker key", {"F10"}),
    ("ST13", "what time is breakfast", {"POL28", "F13"}),
    ("ST14", "can I leave early", {"POL19", "F07"}),                # improved after testing
    ("ST15", "I'm being bullied", {"F12"}),
    ("ST16", "can I take photos at school", {"POL23", "F15"}),
    ("ST17", "when are the exams", {"E16", "E21", "F17"}),          # real exam dates since the calendar was added
    ("ST18", "what happens if I cheat", {"F18"}),
    ("ST19", "what are civility points", {"POL08"}),
    ("ST20", "can I have a birthday party", {"POL16", "F14"}),
    ("ST21", "what if I break something", {"F23"}),                # improved after testing
    ("ST22", "can I bring my dog", {"POL20"}),                     # improved after testing
    ("ST23", "what is the voice level in the library", {"POL29"}), # improved after testing
    ("ST24", "which gate do I use", {"POL26"}),
    ("ST25", "how do I contact the school", {"F22"}),
    ("ST26", "Em đến muộn thì làm gì?", {"F01"}),
    ("ST27", "quên đồng phục", {"F02", "POL01"}),
    ("ST28", "bị tịch thu điện thoại", {"POL37", "F09"}),
    ("ST29", "em bị ốm", {"F04", "POL17"}),
    ("ST30", "mất chìa khóa tủ", {"POL33", "F10"}),
    ("ST31", "bị bắt nạt", {"F12", "POL24"}),
    ("ST32", "điểm văn minh", {"POL08"}),
    ("ST33", "kỷ luật", {"POL40"}),
    ("ST34", "thẻ tự ra về", {"POL26"}),
    ("ST35", "hút thuốc", {"POL20"}),
]


@pytest.mark.parametrize("case_id,query,expected", CASES, ids=[c[0] for c in CASES])
def test_handbook_question(live, case_id, query, expected):
    result = answer(live, query)
    assert result.status == "ok", f"{case_id}: {result.status}"
    assert top_id(result) in expected, f"{case_id}: top result was {top_id(result)}"


def test_recess_still_works_after_break_fix(live):
    assert top_id(answer(live, "when is recess")) == "R"


def test_every_handbook_entry_cites_its_section(live):
    for item in live.policies + live.faqs:
        assert item.get("source"), item.get("policy_id") or item.get("faq_id")
    handbook = [i for i in live.policies + live.faqs if "Sổ tay" in i["source"]]
    assert len(handbook) >= 60


def test_every_entry_is_bilingual(live):
    for p in live.policies:
        assert p["summary_vi"] and p["title_vi"], p["policy_id"]
    for f in live.faqs:
        assert f["answer_vi"] and f["question_vi"], f["faq_id"]


def test_unknown_questions_still_not_found(live):
    for q in ["what is the weather", "who won the football", "pizza recipe"]:
        assert answer(live, q).status == "not_found"


# ---- SenTia bell schedule (from the school, 2025–2026) ----
from datetime import datetime  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from app.search import Viewer  # noqa: E402

TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def at(hm, day=10):  # 10 Nov 2026 is a Tuesday
    h, m = map(int, hm.split(":"))
    return datetime(2026, 11, day, h, m, tzinfo=TZ)


BELL = [
    ("SB01", "when does school start", "MM", "07:45"),
    ("SB02", "when does school end", "END", "16:05"),
    ("SB03", "when is lunch", "L", "12:15"),
    ("SB04", "when is recess", "R", "10:25"),
    ("SB05", "period 8", "P8", "15:05"),
    ("SB06", "afternoon snack", "SN", "15:50"),
    ("SB07", "mấy giờ tan học", "END", "16:05"),
]


@pytest.mark.parametrize("case_id,query,pid,start", BELL, ids=[c[0] for c in BELL])
def test_bell_times(live, case_id, query, pid, start):
    hit = answer(live, query).hits[0].item
    assert (hit["period_id"], hit["start"]) == (pid, start)


@pytest.mark.parametrize("hm,note,pid", [
    ("07:30", "before", "MM"),
    ("07:50", "current", "MM"),
    ("08:47", "between", "P2"),     # changeover gap: improved after testing
    ("10:30", "current", "R"),
    ("15:00", "between", "P8"),     # 10-minute gap before the last period
    ("15:55", "current", "SN"),
    ("16:30", "after", "END"),
])
def test_what_is_happening_now(live, hm, note, pid):
    r = answer(live, "what period is it now", now=at(hm))
    assert r.note == note and r.hits[0].item["period_id"] == pid


def test_next_period_after_the_last_class(live):
    assert answer(live, "next period", now=at("15:55")).note == "last"
    assert answer(live, "next period", now=at("08:47")).hits[0].item["period_id"] == "P2"


def test_student_class_during_changeover(live):
    r = answer(live, "what class do I have now", Viewer("student", "S001"), now=at("08:47"))
    assert r.extra["state"] == "between" and r.extra["row"]["period_id"] == "P2"


def test_timetable_covers_all_eight_periods(live):
    lessons = [p["period_id"] for p in live.periods if p["kind"] == "class" and p["period_id"] != "MM"]
    assert lessons == [f"P{i}" for i in range(1, 9)]
    for s in live.students.values():
        days = {r["day"] for r in live.student_timetable(s["student_id"])}
        for day in days:
            got = {r["period_id"] for r in live.student_timetable(s["student_id"]) if r["day"] == day}
            assert got == set(lessons), (s["student_id"], day)


def test_clubs_do_not_clash_with_lessons(live):
    end = next(p["start"] for p in live.periods if p["kind"] == "end")
    lunch = next(p for p in live.periods if p["period_id"] == "L")
    for c in live.clubs.values():
        assert c["start"] >= end or (lunch["start"] <= c["start"] and c["end"] <= lunch["end"]), c["club_id"]


def test_lunch_time_agrees_everywhere(live):
    """Policies and FAQs must give the same lunch time as the bell schedule."""
    lunch = next(p for p in live.periods if p["period_id"] == "L")
    en = f"{lunch['start'].lstrip('0')}–{lunch['end']}"
    for item in live.policies + live.faqs:
        text = item.get("summary") or item.get("answer")
        if "Lunch and rest time" in text:
            assert en in text, item.get("policy_id") or item.get("faq_id")
    r = answer(live, "what time is lunch")
    assert r.hits[0].item["start"] == "12:15"


def test_demo_students_are_in_real_sentia_classes(live):
    """Fictional students, real SenTia class names; the demo teacher teaches Alex and Chloe, not Khanh."""
    classes = {s["student_id"]: s["class_group"] for s in live.students.values()}
    assert classes == {"S001": "10A1", "S002": "11A", "S003": "12A1"}   # high school (team decision)
    assert {s["year"] for s in live.students.values()} == {"10", "11", "12"}
    assert len({s["homeroom_teacher_id"] for s in live.students.values()}) == 3
    teacher = live.users["teacher"]["linked_id"]
    assert teacher in live.student_teacher_ids("S001") and teacher in live.student_teacher_ids("S003")
    assert teacher not in live.student_teacher_ids("S002")

"""SenTia 2026–2027 secondary calendar cases, against the live /data folder.
"Today" is fixed at Tuesday 10 November 2026. IDs match docs/TEST_CASES.md."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.data import DEFAULT_DATA_DIR, event_months, load_data
from app.search import answer

TODAY = datetime(2026, 11, 10, 10, 30, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))


@pytest.fixture(scope="module")
def live():
    return load_data(DEFAULT_DATA_DIR)


def names(result):
    return [h.item["name"] for h in result.hits if h.kind == "event"]


CASES = [  # (id, question, expected first event name)
    ("SC01", "when is the next holiday", "Teachers' Day Holiday (school closed)"),
    ("SC02", "khi nào nghỉ", "Teachers' Day Holiday (school closed)"),
    ("SC03", "when is tet", "Lunar New Year (Tết) Holiday"),
    ("SC04", "nghỉ tết khi nào", "Lunar New Year (Tết) Holiday"),
    ("SC05", "when are the end of term tests", "Term 1 End-of-term Exams"),
    ("SC06", "kiểm tra cuối kỳ", "Term 1 End-of-term Exams"),
    ("SC07", "when is the midterm", "Term 2 Mid-term Exams"),       # term 1's is over
    ("SC08", "when is the mid-term break", "Term 2 Mid-term Break"),
    ("SC09", "when is teachers day", "Teachers' Day Holiday (school closed)"),
    ("SC10", "christmas", "Christmas Event"),
    ("SC11", "when is the field trip", "Lower Secondary Field Trip"),      # October's trip is over
    ("SC12", "when does school year end", "Closing Ceremony & Grade 9 Graduation"),
    ("SC13", "igcse", "IGCSE Exams (November series)"),
    ("SC14", "graduation", "Closing Ceremony & Grade 9 Graduation"),
]


@pytest.mark.parametrize("case_id,query,expected", CASES, ids=[c[0] for c in CASES])
def test_calendar_question(live, case_id, query, expected):
    r = answer(live, query, now=TODAY)
    assert r.status == "ok", f"{case_id}: {r.status}"
    assert names(r) and names(r)[0] == expected, f"{case_id}: got {names(r)}"


def test_upcoming_includes_events_still_running(live):
    """The November project started on the 1st but is still on, so it counts as upcoming."""
    got = names(answer(live, "upcoming events", now=TODAY))
    assert "Interdisciplinary Social Sciences Project" in got
    assert all(e["date"] >= "2026-11-01" for e in live.events if e["name"] in got)


def test_today_shows_running_events(live):
    got = names(answer(live, "what's happening today", now=TODAY))
    assert "IGCSE Exams (November series)" in got


def test_month_question_includes_multi_day_events(live):
    got = names(answer(live, "events in december", now=TODAY))
    assert "Christmas & End-of-Term 1 Break" in got or len(got) >= 3


def test_past_holiday_is_not_the_next_one(live):
    assert "National Day Holiday" not in names(answer(live, "when is the next holiday", now=TODAY))


def test_break_time_still_means_the_bell_period(live):
    r = answer(live, "when is break time", now=TODAY)
    assert r.hits[0].kind == "period" and r.hits[0].item["period_id"] == "R"


def test_calendar_matches_the_school_sheet(live):
    by_name = {e["name"]: e for e in live.events}
    assert len(live.events) == 44
    assert (by_name["Lunar New Year (Tết) Holiday"]["date"], by_name["Lunar New Year (Tết) Holiday"]["end_date"]) \
        == ("2027-02-01", "2027-02-12")
    assert by_name["Term 1 Mid-term Exams"]["end_date"] == "2026-10-13"
    assert all(e["start"] == "" for e in live.events)              # the calendar gives no times
    assert all(e["category"] in {"event", "day_off", "parents", "exam", "project", "holiday"} for e in live.events)


def test_event_months_cover_the_whole_range():
    assert event_months({"date": "2026-12-23", "end_date": "2027-01-02"}) == {"2026-12", "2027-01"}
    assert event_months({"date": "2026-11-20", "end_date": ""}) == {"2026-11"}


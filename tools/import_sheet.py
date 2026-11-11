"""Import the team's Google Sheet into /data.

    1. Google Sheets: File -> Download -> Microsoft Excel (.xlsx)
    2. .venv/bin/python -m tools.import_sheet path/to/file.xlsx            # check + write
       .venv/bin/python -m tools.import_sheet path/to/file.xlsx --check    # check only

What it does:
  - finds each tab and its header row, even if names differ a little
    ("Teacher", "Staff", "Giáo viên"; "Room number" for room_id ...)
  - cleans every cell: extra spaces, times like 8:15 / 8h15 / 8.15am / 1:30 pm,
    real date cells or 20/11/2026, lists separated by , or ; , "Ms." -> "Ms",
    "thứ 2" -> "Monday", codes like "b 201" -> "B201"
  - checks required fields, duplicate codes, and that every code points to
    something that exists (a teacher's room, a room's building ...)
  - adds what the team doesn't enter: map positions and the fictional
    demo students, timetables and clubs
  - writes nothing unless there are no errors; then checks the result loads
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import load_workbook

from tools.sheet_spec import TABS, TAB_BY_NAME, Col, Tab

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))

from app.text import normalize, split_list, strip_accents  # noqa: E402

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_WORDS = {
    "mon": 0, "monday": 0, "thu 2": 0, "thu hai": 0, "t2": 0,
    "tue": 1, "tues": 1, "tuesday": 1, "thu 3": 1, "thu ba": 1, "t3": 1,
    "wed": 2, "wednesday": 2, "thu 4": 2, "thu tu": 2, "t4": 2,
    "thur": 3, "thurs": 3, "thursday": 3, "thu 5": 3, "thu nam": 3, "t5": 3,
    "fri": 4, "friday": 4, "thu 6": 4, "thu sau": 4, "t6": 4,
    "sat": 5, "saturday": 5, "thu 7": 5, "thu bay": 5, "t7": 5,
    "sun": 6, "sunday": 6, "chu nhat": 6, "cn": 6,
}
KIND_WORDS = {
    "class": "class", "lesson": "class", "period": "class", "tiet": "class", "tiet hoc": "class", "homeroom": "class",
    "break": "break", "recess": "break", "lunch": "break", "ra choi": "break", "nghi": "break", "nghi trua": "break",
    "end": "end", "finish": "end", "dismissal": "end", "end of day": "end", "tan hoc": "end",
}
TITLES = {"mr": "Mr", "ms": "Ms", "mrs": "Mrs", "miss": "Miss", "dr": "Dr", "thay": "Thầy", "co": "Cô"}
VN_SURNAMES = set("""nguyen tran le pham hoang huynh phan vu vo dang bui do ho ngo duong ly dinh truong
mai cao ta lam trinh luu ha chau quach la kieu ton thai doan luong to vuong tang giang""".split())


# ---------------------------------------------------------------- report
@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, where: str, msg: str):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str):
        self.warnings.append(f"{where}: {msg}")

    def print(self):
        for title, items, mark in (("Notes", self.notes, "·"), ("Warnings (please check)", self.warnings, "!"),
                                   ("Errors (must fix)", self.errors, "✗")):
            if items:
                print(f"\n{title} — {len(items)}")
                for item in items:
                    print(f"  {mark} {item}")


# --------------------------------------------------------------- cleaning
def clean_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return " ".join(str(value).replace(" ", " ").split())


def clean_id(value) -> str:
    return re.sub(r"\s+", "", clean_text(value)).upper()


def clean_list(value) -> str:
    raw = "" if value is None else str(value)
    out = []
    for p in (clean_text(x) for x in re.split(r"[;,\n|]+", raw)):
        if p and p.lower() not in (o.lower() for o in out):
            out.append(p)
    return ";".join(out)


def clean_time(value, where: str, report: Report) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, dt.datetime):
        value = value.time()
    if isinstance(value, dt.time):
        return f"{value.hour:02d}:{value.minute:02d}"
    if isinstance(value, (int, float)) and 0 <= value < 1:          # Excel time as fraction of a day
        minutes = round(value * 24 * 60)
        return f"{minutes // 60:02d}:{minutes % 60:02d}"
    text = strip_accents(clean_text(value)).lower().replace(" ", "")
    text = text.replace("sang", "am").replace("chieu", "pm").replace("toi", "pm")
    m = (re.fullmatch(r"(\d{1,2})[:h.](\d{2})(?::\d{2})?(am|pm)?", text)
         or re.fullmatch(r"(\d{1,2})()(am|pm)", text)
         or re.fullmatch(r"(\d{1,2})(\d{2})()", text)
         or re.fullmatch(r"(\d{1,2})h()()", text))
    if not m:
        report.error(where, f"can't read time '{clean_text(value)}' (use 24-hour HH:MM, e.g. 08:15)")
        return ""
    hour, minute, ampm = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        report.error(where, f"'{clean_text(value)}' is not a valid time")
        return ""
    return f"{hour:02d}:{minute:02d}"


def clean_date(value, where: str, report: Report) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, (int, float)) and 20000 < value < 80000:  # Excel serial date
        return (dt.date(1899, 12, 30) + dt.timedelta(days=int(value))).isoformat()
    text = clean_text(value)
    m = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", text)
    if m:
        y, mo, d = map(int, m.groups())
    else:
        m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", text)
        if m:
            d, mo, y = map(int, m.groups())          # Vietnam writes day first
            if d <= 12 and mo <= 12 and d != mo:
                report.warn(where, f"'{text}' read as day/month/year = {y}-{mo:02d}-{d:02d}")
        else:
            for fmt in ("%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y", "%b %d, %Y", "%B %d, %Y"):
                try:
                    return dt.datetime.strptime(text, fmt).date().isoformat()
                except ValueError:
                    continue
            report.error(where, f"can't read date '{text}' (use YYYY-MM-DD, e.g. 2026-11-20)")
            return ""
    try:
        return dt.date(y, mo, d).isoformat()
    except ValueError:
        report.error(where, f"'{text}' is not a real date")
        return ""


def clean_title(value, where: str, report: Report) -> str:
    text = clean_text(value).rstrip(".")
    key = normalize(text)
    if key in TITLES:
        return TITLES[key]
    if text:
        report.warn(where, f"unusual title '{text}' (expected Mr, Ms, Mrs, Dr, Thầy, Cô)")
    return text


def clean_day(value, where: str, report: Report) -> str:
    key = normalize(clean_text(value))
    if key in DAY_WORDS:
        return DAYS[DAY_WORDS[key]]
    if key:
        report.error(where, f"can't read day '{clean_text(value)}' (use Monday ... Friday)")
    return ""


def clean_kind(value, where: str, report: Report) -> str:
    key = normalize(clean_text(value))
    if key in KIND_WORDS:
        return KIND_WORDS[key]
    if key:
        report.error(where, f"kind must be class, break or end (got '{clean_text(value)}')")
    return ""


def clean_cell(col: Col, value, where: str, report: Report) -> str:
    if col.type == "id":
        return clean_id(value)
    if col.type == "list":
        return clean_list(value)
    if col.type == "time":
        return clean_time(value, where, report)
    if col.type == "date":
        return clean_date(value, where, report)
    if col.type == "title":
        return clean_title(value, where, report)
    if col.type == "day":
        return clean_day(value, where, report)
    if col.type == "kind":
        return clean_kind(value, where, report)
    return clean_text(value)


# ------------------------------------------------------ finding the tabs
def header_key(text) -> str:
    key = normalize(clean_text(text)).replace(" ", "_")
    for suffix in ("_vietnamese", "_tieng_viet", "_vn", "_viet"):
        if key.endswith(suffix):
            key = key[: -len(suffix)] + "_vi"
    if key.startswith("vietnamese_"):
        key = key[len("vietnamese_"):] + "_vi"
    return key


def match_tab(sheet_name: str) -> Tab | None:
    key = normalize(sheet_name)
    for tab in TABS:
        names = {normalize(tab.name), normalize(tab.file)} | {normalize(s) for s in tab.synonyms}
        if key in names or key.rstrip("s") in names:
            return tab
    return None


def map_headers(tab: Tab, row: list) -> dict[int, Col]:
    """Column index -> spec column, using names and synonyms."""
    lookup: dict[str, Col] = {}
    for col in tab.columns:
        lookup[col.name] = col
        for s in col.synonyms:
            lookup.setdefault(header_key(s), col)
    mapping, used = {}, set()
    for idx, cell in enumerate(row):
        key = header_key(cell)
        col = lookup.get(key)
        if col and col.name not in used:
            mapping[idx] = col
            used.add(col.name)
    return mapping


def read_tab(ws, tab: Tab, report: Report) -> list[dict]:
    rows = list(ws.iter_rows(values_only=True))
    # The header row is the first of the top 10 rows that matches at least 2 known columns.
    header_idx, mapping = None, {}
    for i, row in enumerate(rows[:10]):
        m = map_headers(tab, list(row))
        if len(m) >= 2:
            header_idx, mapping = i, m
            break
    if header_idx is None:
        report.error(f"{ws.title}", "couldn't find the header row (row 1 should hold the column names)")
        return []
    header = rows[header_idx]
    # A single "full name" column can stand in for first_name + last_name.
    full_name_idx = next((i for i, h in enumerate(header) if header_key(h) in ("full_name", "name", "ho_ten", "teacher_name")
                          and i not in mapping), None) if tab.name == "Teachers" else None
    for idx, h in enumerate(header):
        if h and idx not in mapping and idx != full_name_idx:
            report.warn(f"{ws.title}", f"column '{clean_text(h)}' isn't used by the app and was ignored")
    missing = [c.name for c in tab.columns if c.required and c not in mapping.values()]
    if tab.name == "Teachers" and full_name_idx is not None:
        missing = [m for m in missing if m not in ("first_name", "last_name", "title")]
    for name in missing:
        if not (tab.auto_id and name == tab.id_col):
            report.error(f"{ws.title}", f"missing required column '{name}'")

    records = []
    for r_offset, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        if all(clean_text(v) == "" for v in row):
            continue
        where = f"{ws.title} row {r_offset}"
        rec = {c.name: "" for c in tab.columns}
        for idx, col in mapping.items():
            rec[col.name] = clean_cell(col, row[idx] if idx < len(row) else None, f"{where}, {col.name}", report)
        if full_name_idx is not None and not (rec["first_name"] and rec["last_name"]):
            split_full_name(rec, clean_text(row[full_name_idx]), where, report)
        rec["_where"] = where
        records.append(rec)
    return records


def split_full_name(rec: dict, full: str, where: str, report: Report) -> None:
    words = full.split()
    if words and normalize(words[0]).rstrip(".") in TITLES:
        rec["title"] = rec["title"] or TITLES[normalize(words[0]).rstrip(".")]
        words = words[1:]
    if len(words) < 2:
        report.error(where, f"can't split name '{full}' into first and last name")
        return
    if normalize(words[0]) in VN_SURNAMES:      # Vietnamese order: family name first, given name last
        rec["last_name"], rec["first_name"] = words[0], words[-1]
    else:
        rec["first_name"], rec["last_name"] = words[0], words[-1]
    report.warn(where, f"split '{full}' into first_name='{rec['first_name']}', last_name='{rec['last_name']}'")


# ---------------------------------------------------------------- checks
def finish_tab(tab: Tab, records: list[dict], report: Report) -> list[dict]:
    seen, n = set(), 0
    for rec in records:
        where = rec["_where"]
        if tab.auto_id and not rec[tab.id_col]:
            n += 1
            while f"{tab.auto_id}{n:02d}" in seen or any(r[tab.id_col] == f"{tab.auto_id}{n:02d}" for r in records):
                n += 1
            rec[tab.id_col] = f"{tab.auto_id}{n:02d}"
        if tab.name == "Schedule" and rec.get("kind") == "end" and not rec["end"]:
            rec["end"] = rec["start"]          # end of the day has no length
        for col in tab.columns:
            already = any(e.startswith(f"{where}, {col.name}:") for e in report.errors)
            if col.required and not rec[col.name] and not already:
                report.error(where, f"'{col.name}' is empty")
        rid = rec[tab.id_col]
        if rid in seen:
            report.error(where, f"code '{rid}' is used more than once in {tab.name}")
        seen.add(rid)
        if "start" in rec and "end" in rec and rec["start"] and rec["end"] and rec["end"] < rec["start"]:
            report.error(where, f"ends ({rec['end']}) before it starts ({rec['start']})")
        if rec.get("end_date") and rec.get("date") and rec["end_date"] < rec["date"]:
            report.error(where, f"last day ({rec['end_date']}) is before the first day ({rec['date']})")
    return records


def check_refs(tables: dict[str, list[dict]], report: Report) -> None:
    for tab in TABS:
        for col in tab.columns:
            if not col.ref:
                continue
            valid = {r[TAB_BY_NAME[col.ref].id_col] for r in tables.get(col.ref, [])}
            for rec in tables.get(tab.name, []):
                value = rec.get(col.name)
                if value and value not in valid:
                    report.error(rec["_where"], f"{col.name} '{value}' doesn't exist in the {col.ref} tab")


def check_schedule(periods: list[dict], report: Report) -> list[dict]:
    for p in periods:
        if p["kind"] == "end" and not p["end"]:
            p["end"] = p["start"]
    ordered = sorted(periods, key=lambda p: (p["start"], p["kind"] == "end"))
    if [p["period_id"] for p in ordered] != [p["period_id"] for p in periods]:
        report.notes.append("Schedule rows were sorted into time order.")
    if periods and not any(p["kind"] == "end" for p in periods):
        report.warn("Schedule", "no row with kind 'end' (end of the school day); add one so 'when does school finish' works")
    if not any(p["kind"] == "class" for p in periods):
        report.error("Schedule", "needs at least one row with kind 'class'")
    return ordered


# ------------------------------------------------------- map positions
def layout_buildings(buildings: list[dict], old: dict[str, dict], school: dict, report: Report) -> None:
    """Keep existing positions; otherwise place buildings in two rows around a central path."""
    keys = ("x", "y", "w", "h", "entrance_x", "entrance_y")
    if buildings and all(b["building_id"] in old for b in buildings):
        for b in buildings:
            b.update({k: old[b["building_id"]][k] for k in keys})
        return
    width, margin, gap, path_gap = 800, 40, 30, 70
    half = (len(buildings) + 1) // 2
    top, bottom = buildings[:half], buildings[half:]

    def place(row: list[dict], y: int, entrance_y: int, gap_after: int | None) -> int | None:
        """Lay a row of buildings left to right. Leave room for the main path after `gap_after`."""
        extra = path_gap if gap_after is not None else 0
        w = max(60, (width - 2 * margin - gap * (len(row) - 1) - extra) // max(1, len(row)))
        x, path_x = margin, None
        for i, b in enumerate(row):
            b.update(x=x, y=y, w=w, h=150, entrance_x=x + w // 2, entrance_y=entrance_y)
            x += w + gap
            if i == gap_after:
                path_x = x - gap + (gap + path_gap) // 2
                x += path_gap
        return path_x

    place(top, 50, 200, None)
    if bottom:
        path_x = place(bottom, 290, 290, gap_after=0 if len(bottom) == 1 else len(bottom) // 2 - 1)
    else:
        path_x = width // 2
    school.setdefault("map", {}).update(width=width, height=500, hub=[path_x, 245])
    report.notes.append("Map: buildings were laid out automatically. Send a campus map sketch to place them accurately.")


def layout_rooms(rooms: list[dict], buildings: dict[str, dict], old: dict[str, dict], report: Report) -> None:
    moved = 0
    by_building: dict[str, list[dict]] = {}
    for r in rooms:
        by_building.setdefault(r["building_id"], []).append(r)
    for bid, group in by_building.items():
        b = buildings.get(bid)
        if not b:
            continue
        bx, by_, bw, bh = (int(b[k]) for k in ("x", "y", "w", "h"))
        cols = max(1, min(len(group), bw // 50))
        rows = (len(group) + cols - 1) // cols
        for i, r in enumerate(group):
            prev = old.get(r["room_id"])
            if prev and prev["building_id"] == bid:
                r["map_x"], r["map_y"] = prev["map_x"], prev["map_y"]
                continue
            cx, cy = i % cols, i // cols
            r["map_x"] = bx + int(bw * (cx + 0.5) / cols)
            r["map_y"] = by_ + 40 + int((bh - 55) * (cy + 0.5) / rows)
            moved += 1
    if moved:
        report.notes.append(f"Map: {moved} room pin(s) placed automatically inside their building.")


# ------------------------------------------------ fictional demo students
NON_TEACHING = ("principal", "hieu truong", "librar", "thu thu", "counsel", "tu van", "technician", "ky thuat",
                "support", "office", "van phong", "nurse", "y te", "reception", "le tan", "admin")
FAKE_CLUBS = [("Coding Club", "Câu lạc bộ Lập trình"), ("School Choir", "Dàn hợp xướng"),
              ("Basketball", "Bóng rổ"), ("Art Club", "Câu lạc bộ Mỹ thuật"), ("Debate Club", "Câu lạc bộ Tranh biện")]


# Real SenTia class names for the three fictional demo students (Alex, Khanh, Chloe).
# Only the class names are real; the students themselves are made up.
DEMO_CLASSES = [("6A1", "6"), ("7A1", "7"), ("8A1", "8")]


def generate_fictional(tables: dict[str, list[dict]], old_users: list[dict], report: Report) -> dict[str, list[dict]]:
    teachers, periods = tables["Teachers"], tables["Schedule"]
    homeroomish = ("home", "roll", "meeting", "sinh hoat", "chao co", "assembly")
    lesson_periods = [p["period_id"] for p in periods if p["kind"] == "class"
                      and not any(w in normalize(f"{p['name']} {p['aliases']}") for w in homeroomish)]
    if not lesson_periods:
        lesson_periods = [p["period_id"] for p in periods if p["kind"] == "class"]
    teaching = [t for t in teachers if t["subjects"]
                and not any(w in normalize(f"{t['position']} {t['department']}") for w in NON_TEACHING)]
    subjects, seen = [], set()
    for t in teaching:
        s = split_list(t["subjects"])[0]
        if normalize(s) not in seen:
            seen.add(normalize(s))
            subjects.append((s, t["teacher_id"], t["room_id"]))
    if len(subjects) < 3:
        report.error("Teachers", "need at least 3 teaching staff with different subjects to build demo timetables")
        return {}
    base = subjects[:9]
    (a, _), (b, _), (c, _) = DEMO_CLASSES       # Alex, Khanh, Chloe
    if len(base) >= 4:
        groups = {a: base[:-1], b: base[:-2] + base[-1:], c: base}
        demo_teacher = base[-2][1]               # teaches Alex's and Chloe's classes, not Khanh's
    else:
        groups = {a: base, b: base, c: base}
        demo_teacher = base[0][1]
        report.warn("Teachers", "few subjects: the demo teacher account will teach every demo student")

    timetable = []
    days = DAYS[:5]
    for gi, (group, subs) in enumerate(groups.items()):
        for di, day in enumerate(days):
            for pi, pid in enumerate(lesson_periods):
                s, tid, rid = subs[(di * 3 + pi + gi + 2) % len(subs)]
                timetable.append({"class_group": group, "day": day, "period_id": pid, "subject": s,
                                  "teacher_id": tid, "room_id": rid})

    clubs = [dict(c) for c in tables.get("Clubs", [])]
    if not clubs:
        leaders = [t for t in teaching if t["teacher_id"] != demo_teacher] or teaching
        end = next((p["start"] for p in periods if p["kind"] == "end"), periods[-1]["end"])
        h, m = map(int, end.split(":"))
        start = f"{(h * 60 + m + 10) // 60:02d}:{(h * 60 + m + 10) % 60:02d}"
        finish = f"{(h * 60 + m + 70) // 60:02d}:{(h * 60 + m + 70) % 60:02d}"
        for i, (name, name_vi) in enumerate(FAKE_CLUBS[:4]):
            t = leaders[i % len(leaders)]
            clubs.append({"club_id": f"C{i + 1:02d}", "name": name, "name_vi": name_vi, "teacher_id": t["teacher_id"],
                          "room_id": t["room_id"], "day": days[i % 4], "start": start, "end": finish})
        report.notes.append("Clubs tab was empty: 4 fictional clubs were created for the demo profiles.")
    safe = [c["club_id"] for c in clubs if c["teacher_id"] != demo_teacher] or [c["club_id"] for c in clubs]
    pick = lambda i: safe[i % len(safe)]  # noqa: E731

    by_group_teachers = {g: [s[1] for s in subs] for g, subs in groups.items()}
    # each class gets its own homeroom teacher; Khanh's must not be the demo teacher (privacy demo)
    homeroom_a = by_group_teachers[a][0]
    homeroom_b = next((t for t in by_group_teachers[b] if t not in (demo_teacher, homeroom_a)),
                      next((t for t in by_group_teachers[b] if t != demo_teacher), by_group_teachers[b][0]))
    homeroom_c = next((t for t in by_group_teachers[c] if t not in (homeroom_a, homeroom_b)), by_group_teachers[c][0])
    (_, year_a), (_, year_b), (_, year_c) = DEMO_CLASSES
    students = [
        {"student_id": "S001", "first_name": "Alex", "last_name": "Carter", "year": year_a, "class_group": a,
         "homeroom_teacher_id": homeroom_a, "club_ids": f"{pick(0)};{pick(1)}"},
        {"student_id": "S002", "first_name": "Khanh", "last_name": "Ngo", "year": year_b, "class_group": b,
         "homeroom_teacher_id": homeroom_b, "club_ids": f"{pick(1)};{pick(2)}"},
        {"student_id": "S003", "first_name": "Chloe", "last_name": "Reed", "year": year_c, "class_group": c,
         "homeroom_teacher_id": homeroom_c,
         "club_ids": f"{pick(2)};{pick(3)}"},
    ]
    for s in students:  # remove duplicate club ids (when there are few clubs)
        s["club_ids"] = ";".join(dict.fromkeys(s["club_ids"].split(";")))

    users = [dict(u) for u in old_users]
    for u in users:
        if u["role"] == "teacher":
            u["linked_id"] = demo_teacher
    t = next(t for t in teachers if t["teacher_id"] == demo_teacher)
    report.notes.append(f"Demo students regenerated (fictional). The 'teacher' login is now "
                        f"{t['title']} {t['first_name']} {t['last_name']} ({demo_teacher}).")
    return {"timetable": timetable, "clubs": clubs, "students": students, "users": users}


# ----------------------------------------------------------------- main
def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_school_tab(ws, school: dict, report: Report) -> None:
    for row in ws.iter_rows(values_only=True):
        if not row or len(row) < 2:
            continue
        key, value = header_key(row[0]), clean_text(row[1])
        if key in ("name", "name_vi", "timezone") and value:
            school[key] = value


def run(xlsx: Path, out_dir: Path = DATA, check_only: bool = False) -> Report:
    report = Report()
    wb = load_workbook(xlsx, data_only=True)
    school = json.loads((out_dir / "school.json").read_text(encoding="utf-8"))
    tables: dict[str, list[dict]] = {}
    for ws in wb.worksheets:
        if normalize(ws.title) in ("instructions", "examples", "huong dan"):
            continue
        if normalize(ws.title) in ("school", "truong"):
            read_school_tab(ws, school, report)
            continue
        tab = match_tab(ws.title)
        if not tab:
            report.warn(ws.title, "tab name not recognised, so it was skipped "
                                  f"(expected one of: {', '.join(t.name for t in TABS)})")
            continue
        if tab.name in tables:
            report.error(ws.title, f"a second tab for {tab.name}; merge them into one tab")
            continue
        if tab.name != ws.title:
            report.notes.append(f"Tab '{ws.title}' was read as {tab.name}.")
        tables[tab.name] = finish_tab(tab, read_tab(ws, tab, report), report)

    missing_tabs = [t.name for t in TABS if t.required_tab and not tables.get(t.name)]
    for name in missing_tabs:
        report.error(name, "tab is missing or empty")
    if missing_tabs:
        return report

    check_refs(tables, report)     # report broken links together with the other errors
    tables["Schedule"] = check_schedule(tables["Schedule"], report)
    if report.errors:
        return report

    old_buildings = {b["building_id"]: b for b in read_csv(out_dir / "buildings.csv")}
    old_rooms = {r["room_id"]: r for r in read_csv(out_dir / "rooms.csv")}
    layout_buildings(tables["Buildings"], old_buildings, school, report)
    layout_rooms(tables["Rooms"], {b["building_id"]: b for b in tables["Buildings"]}, old_rooms, report)
    fictional = generate_fictional(tables, read_csv(out_dir / "users.csv"), report)
    if report.errors:
        return report

    school["is_sample"] = False
    counts = ", ".join(f"{t.name}: {len(tables.get(t.name, []))}" for t in TABS)
    report.notes.append(f"Read {counts}.")

    # Write everything to a temporary folder, check it loads, then copy into /data.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for tab in TABS:
            if tab.name == "Clubs":
                continue
            cols = [c.name for c in tab.columns] + tab.extra_out
            write_csv(tmp_dir / f"{tab.file}.csv", tables[tab.name], cols)
        write_csv(tmp_dir / "clubs.csv", fictional["clubs"], [c.name for c in TAB_BY_NAME["Clubs"].columns])
        write_csv(tmp_dir / "students.csv", fictional["students"],
                  ["student_id", "first_name", "last_name", "year", "class_group", "homeroom_teacher_id", "club_ids"])
        write_csv(tmp_dir / "timetable.csv", fictional["timetable"],
                  ["class_group", "day", "period_id", "subject", "teacher_id", "room_id"])
        write_csv(tmp_dir / "users.csv", fictional["users"], ["username", "password_hash", "role", "linked_id"])
        (tmp_dir / "school.json").write_text(json.dumps(school, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        from app.data import load_data
        try:
            load_data(tmp_dir)
        except Exception as exc:  # noqa: BLE001
            report.error("Final check", str(exc))
            return report
        if check_only:
            report.notes.append("Check only: nothing was written.")
            return report
        for f in tmp_dir.iterdir():
            shutil.copy(f, out_dir / f.name)
    report.notes.append(f"Data written to {out_dir}. Restart the app (or it reloads automatically in dev mode).")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Import the school data spreadsheet into /data.")
    parser.add_argument("xlsx", type=Path, help="The .xlsx downloaded from Google Sheets")
    parser.add_argument("--check", action="store_true", help="Only check the sheet; don't write anything")
    parser.add_argument("--out", type=Path, default=DATA, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.xlsx.exists():
        print(f"File not found: {args.xlsx}")
        return 2
    report = run(args.xlsx, args.out, args.check)
    report.print()
    if report.errors:
        print(f"\n✗ {len(report.errors)} error(s). Nothing was written. Fix them in the sheet and run again.")
        return 1
    print("\n✓ Import OK" + (" (check only)." if args.check else "."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

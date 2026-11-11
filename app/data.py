"""Data layer: loads the school's CSV files into memory.

The CSV files in /data can be opened and edited in Microsoft Excel.
Each row becomes a Python dict; list columns (separated by ';') become lists.
"""

import csv
import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .text import split_list

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def data_dir() -> Path:
    """The folder holding the CSV files. Tests point SSA_DATA_DIR at a fixed sample copy."""
    return Path(os.environ.get("SSA_DATA_DIR") or DEFAULT_DATA_DIR)

LIST_COLUMNS = {"aliases", "subjects", "keywords", "club_ids"}


def _read_csv(name: str, folder: Path) -> list[dict]:
    with open(folder / f"{name}.csv", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key in list(row):
            value = (row[key] or "").strip()
            row[key] = split_list(value) if key in LIST_COLUMNS else value
    return rows


def event_end(e: dict) -> str:
    """Last day of an event (ISO date). Single-day events have no end_date."""
    return e.get("end_date") or e["date"]


def event_months(e: dict) -> set[str]:
    """Every 'YYYY-MM' an event touches, so a 25 Dec – 3 Jan break shows in both months."""
    y, m = int(e["date"][:4]), int(e["date"][5:7])
    last = event_end(e)[:7]
    out = set()
    while f"{y:04d}-{m:02d}" <= last:
        out.add(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def display_name(t: dict) -> str:
    """'Ms Sarah Nguyen', or the name as written at school ('Đỗ Ngọc Anh') with the title if known."""
    name = t.get("display_name") or f"{t['first_name']} {t['last_name']}"
    return f"{t['title']} {name}".strip()


def _index(rows: list[dict], key: str) -> dict[str, dict]:
    return {row[key]: row for row in rows}


@dataclass
class SchoolData:
    school: dict
    buildings: dict[str, dict]
    rooms: dict[str, dict]
    teachers: dict[str, dict]
    periods: list[dict]
    events: list[dict]
    policies: list[dict]
    faqs: list[dict]
    students: dict[str, dict]
    clubs: dict[str, dict]
    timetable: list[dict]
    users: dict[str, dict] = field(repr=False)

    # ---- convenient lookups -------------------------------------------
    def teacher_name(self, teacher_id: str) -> str:
        t = self.teachers.get(teacher_id)
        return display_name(t) if t else ""

    def student_timetable(self, student_id: str) -> list[dict]:
        student = self.students.get(student_id)
        if not student:
            return []
        return [row for row in self.timetable if row["class_group"] == student["class_group"]]

    def student_teacher_ids(self, student_id: str) -> set[str]:
        student = self.students.get(student_id)
        if not student:
            return set()
        ids = {row["teacher_id"] for row in self.student_timetable(student_id)}
        ids.add(student["homeroom_teacher_id"])
        ids.update(self.clubs[c]["teacher_id"] for c in student["club_ids"] if c in self.clubs)
        return ids


def _validate(data: SchoolData) -> None:
    """Fail fast if a row points at something that doesn't exist."""
    problems = []
    for t in data.teachers.values():
        if t["room_id"] and t["room_id"] not in data.rooms:
            problems.append(f"teacher {t['teacher_id']} -> unknown room {t['room_id']}")
    for r in data.rooms.values():
        if r["building_id"] not in data.buildings:
            problems.append(f"room {r['room_id']} -> unknown building {r['building_id']}")
    for e in data.events:
        if e["room_id"] and e["room_id"] not in data.rooms:
            problems.append(f"event {e['event_id']} -> unknown room {e['room_id']}")
    period_ids = {p["period_id"] for p in data.periods}
    for row in data.timetable:
        if row["period_id"] not in period_ids:
            problems.append(f"timetable row {row} has an unknown period")
        if row["teacher_id"] not in data.teachers or row["room_id"] not in data.rooms:
            problems.append(f"timetable row {row} has an unknown teacher or room")
    for s in data.students.values():
        for c in s["club_ids"]:
            if c not in data.clubs:
                problems.append(f"student {s['student_id']} -> unknown club {c}")
    if problems:
        raise ValueError("Data problems found:\n  " + "\n  ".join(problems))


def load_data(folder: Path | None = None) -> SchoolData:
    return _load(str(folder or data_dir()))


@lru_cache(maxsize=4)
def _load(folder_str: str) -> SchoolData:
    folder = Path(folder_str)

    def read(name: str) -> list[dict]:
        return _read_csv(name, folder)

    data = SchoolData(
        school=json.loads((folder / "school.json").read_text(encoding="utf-8")),
        buildings=_index(read("buildings"), "building_id"),
        rooms=_index(read("rooms"), "room_id"),
        teachers=_index(read("teachers"), "teacher_id"),
        periods=read("schedule"),
        events=sorted(read("events"), key=lambda e: (e["date"], e["start"])),
        policies=read("policies"),
        faqs=read("faqs"),
        students=_index(read("students"), "student_id"),
        clubs=_index(read("clubs"), "club_id"),
        timetable=read("timetable"),
        users=_index(read("users"), "username"),
    )
    _validate(data)
    return data

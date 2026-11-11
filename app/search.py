"""Logic layer: turns a question into an answer using rules and keyword matching.

Pipeline (each step is a small function below):
  1. validate      - reject empty / too long / symbol-only input
  2. greet / help  - "hi", "help"
  3. privacy       - personal details, student lists, named students
  4. intent        - location, staff, schedule, event, policy, faq, profile
  5. special rules - "now", "period 3", "upcoming events", "my timetable"
  6. spelling      - correct typos against the words we actually know
  7. scoring       - weighted phrase + keyword matches, boosted by intent
  8. answer        - best records, or "not found" (we never invent answers)
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .data import SchoolData, event_end, event_months
from .text import normalize

MAX_QUERY_LENGTH = 200
MIN_SCORE = 3.0          # below this, a record is not a real match
MAX_RESULTS = 5

# Words that carry no meaning for matching records ("the", "is", ...).
STOPWORDS = set("""
a an the is are was were be to of in on at for and or i me my we you it its this that these those
what whats where wheres when who whom which why how do does did can could should would will
please tell show find give get about with from there here any some have has had am im
room rooms school policy policies rule rules teacher teachers staff period class time day teach teaches taught
la cua co khong nao gi o voi va cho em toi minh ban duoc nhu the thi
""".split())

# Short names that are also everyday Vietnamese/English words. These only
# match a person when written with a title ("Mr Le") or as a full name.
AMBIGUOUS_NAMES = {"le", "do", "vo", "dang", "kim", "mai", "bui", "tuan", "nam", "minh", "khoa", "bao"}

TITLES = {"mr", "ms", "mrs", "miss", "dr", "sir", "thay", "co"}

INTENT_PHRASES: dict[str, list[str]] = {
    "location": [
        "where", "located", "location", "directions", "direction", "how do i get to", "how to get to",
        "get to", "way to", "map", "which building", "what floor", "which floor", "floor",
        "o dau", "cho nao", "duong den", "di den", "nam o", "tang may", "phong nao", "toa nao",
    ],
    "staff": [
        "who", "teacher", "teachers", "teaches", "teach", "staff", "head of", "department",
        "giao vien", "thay", "co giao", "ai day", "nguoi day", "truong bo mon",
        "homeroom", "form teacher", "gvcn", "chu nhiem",
    ],
    "schedule": [
        "what time", "bell", "bell times", "period", "start", "starts", "finish", "finishes",
        "end", "ends", "recess", "lunch", "break", "may gio", "tiet", "bat dau", "ket thuc", "gio hoc",
    ],
    "event": [
        "when is", "event", "events", "date", "calendar", "happening", "upcoming", "coming up",
        "su kien", "khi nao", "bao gio", "ngay nao", "lich", "hoat dong",
    ],
    "policy": [
        "policy", "policies", "rule", "rules", "allowed", "can i", "am i allowed", "permitted",
        "banned", "dress code", "quy dinh", "noi quy", "chinh sach", "duoc phep", "luat",
    ],
    "faq": [
        "how do i", "how can i", "what do i do", "what should i", "what happens", "help me",
        "i lost", "forgot", "i feel", "procedure", "lam sao", "lam gi", "the nao", "phai lam",
    ],
    "profile": [
        "my profile", "my timetable", "my schedule", "my classes", "my class", "my lessons",
        "my teachers", "my teacher", "my clubs", "my club", "my subjects", "my homeroom",
        "what do i have", "who teaches me", "thoi khoa bieu", "lich hoc", "ho so", "cua em", "cua toi",
    ],
}

# Which record kinds each intent prefers.
INTENT_KINDS = {
    "location": {"room", "teacher"},
    "staff": {"teacher"},
    "schedule": {"period"},
    "event": {"event"},
    "policy": {"policy"},
    "faq": {"faq"},
}

GREETINGS = {"hi", "hello", "hey", "help", "xin chao", "chao", "start", "menu", "giup"}

SENSITIVE_PHRASES = [
    "address", "home address", "phone number", "phone numbers", "contact number", "mobile number",
    "birthday", "date of birth", "dob", "grades", "marks", "scores", "report card", "exam results",
    "medical", "allergy", "allergies", "health record", "password", "passwords", "email", "emails",
    "lives", "live", "parent contact", "parents contact", "parent phone", "so dien thoai", "dia chi", "ngay sinh",
    "diem so", "bang diem", "mat khau", "nha o dau",
]
PERSON_WORDS = {
    "student", "students", "his", "her", "their", "someone", "somebody", "everyone", "other",
    "others", "classmate", "classmates", "friend", "friends", "hoc sinh", "ban cua",
}
STUDENT_LIST_PHRASES = [
    "all students", "student list", "list of students", "list students", "every student",
    "students names", "student names", "danh sach hoc sinh", "tat ca hoc sinh",
]
STUDENT_PROFILE_WORDS = ["student profile", "student timetable", "timetable of", "profile of", "ho so hoc sinh"]

NOW_PHRASES = ["now", "right now", "current", "currently", "at the moment", "bay gio", "hien tai"]
NEXT_PHRASES = ["next period", "next class", "next lesson", "tiet tiep", "tiet sau"]
MY_LESSON_WORDS = ["i have", "my class", "my lesson", "my next", "do i", "em hoc", "em co", "mon gi"]
UPCOMING_PHRASES = [
    "upcoming", "coming up", "next event", "next events", "events this", "whats on", "what is on",
    "this week", "this month", "su kien sap", "sap toi", "sap dien ra",
]
ALL_PERIODS_PHRASES = ["bell times", "bell schedule", "bell", "all periods", "period times", "gio hoc", "lich chuong"]
MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
PERIOD_NUMBER = re.compile(r"\b(?:period|p|tiet)\s*(\d)\b")
THANG_NUMBER = re.compile(r"\bthang\s*(\d{1,2})\b")


# ---------------------------------------------------------------- data types
@dataclass
class Viewer:
    """Who is asking. role: guest | student | teacher | admin."""
    role: str = "guest"
    linked_id: str = ""      # student_id for students, teacher_id for teachers


@dataclass
class Hit:
    kind: str                # room, teacher, policy, faq, period, event, club, student
    item: dict
    score: float = 0.0


@dataclass
class Answer:
    status: str              # ok | not_found | invalid | private | login_required | help | need_name
    query: str
    intent: str | None = None
    hits: list[Hit] = field(default_factory=list)
    reason: str = ""         # extra detail for the template (e.g. "too_long", "personal_details")
    note: str = ""           # e.g. "current", "teacher_location", "upcoming"
    corrected: str = ""      # spelling-corrected query shown as "Showing results for ..."
    suggestions: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


# ------------------------------------------------------------------ helpers
def has_phrase(q: str, phrase: str) -> bool:
    """Whole-word phrase match on a normalized query."""
    return f" {phrase} " in f" {q} "


def count_phrases(q: str, phrases: list[str]) -> int:
    return sum(len(p.split()) for p in phrases if has_phrase(q, p))


def detect_intent(q: str) -> str | None:
    scores = {intent: count_phrases(q, phrases) for intent, phrases in INTENT_PHRASES.items()}
    if scores["profile"]:
        return "profile"
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def school_now(data: SchoolData, now: datetime | None) -> datetime:
    tz = ZoneInfo(data.school.get("timezone", "UTC"))
    return now.astimezone(tz) if now and now.tzinfo else (now or datetime.now(tz))


def _hhmm(value: str) -> int:
    h, m = value.split(":")
    return int(h) * 60 + int(m)


# ------------------------------------------------------------ search index
@dataclass
class Entry:
    kind: str
    item: dict
    phrases: list[tuple[str, float]]
    words: dict[str, float]
    names: dict[str, float] = field(default_factory=dict)   # person-name tokens
    full_names: list[str] = field(default_factory=list)


def _add_words(words: dict[str, float], text: str, weight: float) -> None:
    for w in normalize(text).split():
        if w not in STOPWORDS and len(w) > 1:
            words[w] = max(words.get(w, 0.0), weight)


def _entry(kind: str, item: dict, phrases: list[tuple[str, float]], words: list[tuple[str, float]]) -> Entry:
    e = Entry(kind, item, [(normalize(p), w) for p, w in phrases if normalize(p)], {})
    for text, weight in words:
        _add_words(e.words, text, weight)
    return e


# Vietnamese family names (without accents). Names that start with one are written family name first.
VN_SURNAMES = {"nguyen", "tran", "le", "pham", "hoang", "huynh", "phan", "vu", "vo", "dang", "bui", "do", "ho",
               "ngo", "duong", "ly", "ha", "dao", "dinh", "khuat", "trinh", "doan", "kieu", "mai", "luong", "tong"}
# Students say "cô" to a Ms and "thầy" to a Mr.
TITLE_GROUPS = {
    "ms": {"ms", "mrs", "miss", "co", "teacher"}, "mrs": {"ms", "mrs", "miss", "co", "teacher"},
    "miss": {"ms", "mrs", "miss", "co", "teacher"}, "co": {"ms", "mrs", "miss", "co", "teacher"},
    "mr": {"mr", "sir", "thay", "teacher"}, "thay": {"mr", "sir", "thay", "teacher"},
}


def _person_names(e: Entry, first: str, last: str, title: str = "", full: str = "") -> None:
    f, l = normalize(first), normalize(last)
    e.full_names.append(f"{f} {l}".strip())
    words = normalize(full).split()
    # "Đỗ Ngọc Anh", "Hà Hoài": family name first, given name last. A single name ("Lan") is treated the same.
    vietnamese = bool(words) and (len(words) == 1 or words[0] in VN_SURNAMES)
    given = words[:-1] if len(words) > 1 and len(words[-1]) == 1 else words   # "... Thu Hà A": A/B tells two apart
    for name in (f, l):
        if not name:
            continue
        # Long, unambiguous names may match on their own; short or everyday words need a title.
        # Vietnamese given names are everyday words without accents ("hoa" = hóa, "ly" = lý, "lan" = lần),
        # so on their own they never match a person.
        e.names[name] = 5.0 if (len(name) >= 3 and name not in AMBIGUOUS_NAMES and not vietnamese) else 0.0
    # The title on record, plus its Vietnamese equivalent; with no title, any title works.
    # ("giáo viên Hoa" is left out on purpose: without accents it reads "giáo viên hóa", chemistry teacher.)
    t = normalize(title)
    titles = sorted(TITLE_GROUPS.get(t, {t})) if t else sorted(TITLES | {"teacher"})
    # Vietnamese staff are called by their given name ("cô Hà", "cô Thu Hà"), never the family name.
    called = {f, " ".join(given[-2:])} if vietnamese else {f, l}
    e.phrases += [(f"{t} {n}", 7.0) for t in titles for n in called if n]
    if l:
        e.phrases.append((f"{f} {l}", 8.0))
    if len(words) >= 2:
        e.phrases.append((" ".join(words), 9.0))
        if vietnamese and len(given) >= 3:
            e.phrases.append((" ".join(given[-2:]), 6.0))


def build_index(data: SchoolData) -> list[Entry]:
    entries: list[Entry] = []
    for t in data.teachers.values():
        e = _entry(
            "teacher", t,
            [(s, 4) for s in t["subjects"]] + [(k, 4) for k in t.get("keywords", [])]
            + [(t["department"], 3), (t["department_vi"], 3),
                                               (t["position"], 3), (t["position_vi"], 3)],
            [(" ".join(t["subjects"]), 2), (t["department"], 1.5), (t["position"], 1.5),
             (t["position_vi"], 1.5), (t["department_vi"], 1)],
        )
        _person_names(e, t["first_name"], t["last_name"], t["title"], t.get("display_name", ""))
        cls = normalize(t.get("homeroom_class", ""))
        if cls:   # "who is 6A1's homeroom teacher", "gvcn 6a1", "chủ nhiệm lớp 6A1"
            e.phrases += [(f"{cls} homeroom", 9.0), (f"homeroom {cls}", 9.0), (f"homeroom teacher {cls}", 9.0),
                          (f"chu nhiem {cls}", 9.0), (f"chu nhiem lop {cls}", 9.0), (f"gvcn {cls}", 9.0),
                          (f"gvcn lop {cls}", 9.0), (f"{cls} form teacher", 9.0), (f"form teacher {cls}", 9.0),
                          (f"homeroom teacher of {cls}", 9.0), (f"teacher of {cls}", 7.0),
                          (f"homeroom of {cls}", 9.0), (f"form teacher of {cls}", 9.0)]
        entries.append(e)
    for r in data.rooms.values():
        b = data.buildings[r["building_id"]]
        entries.append(_entry(
            "room", r,
            [(r["name"], 4), (r["name_vi"], 4), (r["room_id"], 6)] + [(a, 5) for a in r["aliases"]],
            [(r["name"], 2), (r["name_vi"], 2), (" ".join(r["aliases"]), 1.5), (b["name"], 0.5)],
        ))
    for p in data.policies:
        entries.append(_entry(
            "policy", p,
            [(p["title"], 5), (p["title_vi"], 5)] + [(k, 4) for k in p["keywords"]],
            [(p["title"], 2), (p["title_vi"], 2), (" ".join(p["keywords"]), 2),
             (p["category"], 1), (p["summary"], 0.3)],
        ))
    for f in data.faqs:
        entries.append(_entry(
            "faq", f,
            [(f["question"], 5), (f["question_vi"], 5)] + [(k, 4) for k in f["keywords"]],
            [(f["question"], 1.5), (f["question_vi"], 1.5), (" ".join(f["keywords"]), 2),
             (f["category"], 1), (f["answer"], 0.3)],
        ))
    for ev in data.events:
        entries.append(_entry(
            "event", ev,
            [(ev["name"], 5), (ev["name_vi"], 5)] + [(a, 5) for a in ev["aliases"]],
            [(ev["name"], 2), (ev["name_vi"], 2), (" ".join(ev["aliases"]), 1.5), (ev["description"], 0.3)],
        ))
    for p in data.periods:
        entries.append(_entry(
            "period", p,
            [(p["name"], 5), (p["name_vi"], 5)] + [(a, 5) for a in p["aliases"]],
            [(p["name"], 1.5), (" ".join(p["aliases"]), 1.5)],
        ))
    for c in data.clubs.values():
        entries.append(_entry("club", c, [(c["name"], 5), (c["name_vi"], 5)], [(c["name"], 2), (c["name_vi"], 2)]))
    return entries


_INDEX_CACHE: dict[int, tuple[SchoolData, list[Entry], set[str]]] = {}


def get_index(data: SchoolData) -> tuple[list[Entry], set[str]]:
    cached = _INDEX_CACHE.get(id(data))
    if cached and cached[0] is data:
        return cached[1], cached[2]
    entries = build_index(data)
    vocab: set[str] = set()
    for e in entries:
        vocab.update(e.words)
        vocab.update(e.names)
        for phrase, _ in e.phrases:
            vocab.update(phrase.split())
    for s in data.students.values():
        vocab.update(normalize(f"{s['first_name']} {s['last_name']}").split())
    _INDEX_CACHE.clear()
    _INDEX_CACHE[id(data)] = (data, entries, vocab)
    return entries, vocab


def singular(word: str, vocab: set[str]) -> str | None:
    """'phones' -> 'phone', 'boxes' -> 'box' (only if we know the singular word)."""
    if len(word) < 4 or not word.endswith("s") or word.endswith("ss"):
        return None
    for cut in (2, 1) if word.endswith("es") else (1,):
        if word[:-cut] in vocab:
            return word[:-cut]
    return None


def correct_spelling(q: str, vocab: set[str]) -> tuple[str, str]:
    """Return (query used for matching, typo-corrected query to show the user).

    - Typos are replaced by the closest known word ('unifrom' -> 'uniform').
    - Plurals keep the original word AND add the singular, so both
      'sports day' and 'rules about phones' still match.
    """
    out, extra, changed = [], [], False
    for word in q.split():
        one = singular(word, vocab)
        if one:
            extra.append(one)
        if word in vocab or word in STOPWORDS or len(word) < 4 or word.isdigit() or one:
            out.append(word)
            continue
        # Only accept close words that start with the same letter
        # (so 'water' is never "corrected" to 'after').
        candidates = [v for v in vocab if v[0] == word[0]]
        close = difflib.get_close_matches(word, candidates, n=1, cutoff=0.82)
        if close:
            changed = True
        out.append(close[0] if close else word)
    shown = " ".join(out)
    return " ".join(out + extra), (shown if changed else "")


def score_entry(e: Entry, q: str) -> float:
    score = 0.0
    for phrase, weight in e.phrases:
        if has_phrase(q, phrase):
            score += weight
    qwords = [w for w in q.split() if w not in STOPWORDS]
    for w in qwords:
        score += e.words.get(w, 0.0)
        score += e.names.get(w, 0.0)
    return score


def rank(data: SchoolData, q: str, intent: str | None) -> list[Hit]:
    entries, _ = get_index(data)
    preferred = INTENT_KINDS.get(intent or "", set())
    hits = []
    for e in entries:
        s = score_entry(e, q)
        if s <= 0:
            continue
        if e.kind in preferred:
            s = s * 1.5 + 2
        hits.append(Hit(e.kind, e.item, round(s, 2)))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits


def prefer_upcoming(hits: list[Hit], today: str) -> list[Hit]:
    """Events that are over count for half, so "when is the next holiday" skips last month's.
    Equal scores keep calendar order (the index is sorted by date), so the soonest comes first."""
    for h in hits:
        if h.kind == "event" and event_end(h.item) < today:
            h.score = round(h.score * 0.5, 2)
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits


def pick_results(hits: list[Hit], intent: str | None) -> list[Hit]:
    """Keep only strong matches. With a clear intent, stay in that kind; otherwise
    show the best match from each kind that scored close to the top."""
    strong = [h for h in hits if h.score >= MIN_SCORE]
    if not strong:
        return []
    top = strong[0]
    if intent in INTENT_KINDS and top.kind in INTENT_KINDS[intent]:
        return [h for h in strong if h.kind == top.kind and h.score >= top.score * 0.6][:MAX_RESULTS]
    same_kind = [h for h in strong if h.kind == top.kind and h.score >= top.score * 0.75]
    others, seen = [], {top.kind}
    for h in strong:
        if h.kind not in seen and h.score >= top.score * 0.7:
            others.append(h)
            seen.add(h.kind)
    return (same_kind[:3] + others)[:MAX_RESULTS]


# ----------------------------------------------------------- privacy rules
def mentioned_students(data: SchoolData, q: str) -> list[dict]:
    found = []
    for s in data.students.values():
        first, last = normalize(s["first_name"]), normalize(s["last_name"])
        # Students aren't called "cô"/"thầy"/"Mr": "thầy Alex" or "cô Khanh" is a staff member
        # who shares a demo student's name, not a question about the student.
        titled = any(has_phrase(q, f"{t} {first}") for t in TITLES | {"teacher"})
        if titled and not has_phrase(q, f"{first} {last}"):
            continue
        if (has_phrase(q, f"{first} {last}")
                or (len(first) >= 3 and first not in AMBIGUOUS_NAMES and has_phrase(q, first))
                or (len(last) >= 4 and last not in AMBIGUOUS_NAMES and has_phrase(q, last))):
            found.append(s)
    return found


def mentions_teacher(data: SchoolData, q: str) -> bool:
    entries, _ = get_index(data)
    for e in entries:
        if e.kind != "teacher":
            continue
        if any(has_phrase(q, n) for n in e.full_names):
            return True
        if any(has_phrase(q, p) for p, w in e.phrases if w >= 7):
            return True
        if any(weight > 0 and has_phrase(q, name) for name, weight in e.names.items()):
            return True
    return False


def can_view_student(data: SchoolData, viewer: Viewer, student_id: str) -> bool:
    if viewer.role == "admin":
        return True
    if viewer.role == "student":
        return viewer.linked_id == student_id
    if viewer.role == "teacher":
        return viewer.linked_id in data.student_teacher_ids(student_id)
    return False


def privacy_check(data: SchoolData, q: str, viewer: Viewer, query: str) -> Answer | None:
    students = mentioned_students(data, q)
    sensitive = any(has_phrase(q, p) for p in SENSITIVE_PHRASES)
    about_person = bool(students) or any(has_phrase(q, w) for w in PERSON_WORDS) or mentions_teacher(data, q)

    # Rule A: personal details (phone, address, grades, passwords...) about anyone else.
    if sensitive and about_person:
        return Answer("private", query, intent="privacy", reason="personal_details")

    # Rule B: lists of students.
    if any(has_phrase(q, p) for p in STUDENT_LIST_PHRASES):
        if viewer.role == "admin":
            hits = [Hit("student", s) for s in data.students.values()]
            return Answer("ok", query, intent="profile", hits=hits, note="student_list")
        return Answer("private", query, intent="privacy", reason="student_list")

    # Rule C: a named student.
    if students:
        allowed = [s for s in students if can_view_student(data, viewer, s["student_id"])]
        if allowed:
            return Answer("ok", query, intent="profile", hits=[Hit("student", s) for s in allowed])
        if viewer.role == "guest":
            return Answer("login_required", query, intent="profile", reason="student_info")
        return Answer("private", query, intent="privacy", reason="other_student")

    # Rule D: "student timetable" without a name.
    if any(has_phrase(q, p) for p in STUDENT_PROFILE_WORDS):
        if viewer.role == "student":
            return profile_answer(data, viewer, q, query)
        if viewer.role == "guest":
            return Answer("login_required", query, intent="profile", reason="student_info")
        return Answer("need_name", query, intent="profile")
    return None


# --------------------------------------------------------- special answers
def profile_answer(data: SchoolData, viewer: Viewer, q: str, query: str, now: datetime | None = None) -> Answer:
    if viewer.role == "guest":
        return Answer("login_required", query, intent="profile", reason="own_profile")
    if viewer.role != "student" or viewer.linked_id not in data.students:
        return Answer("not_found", query, intent="profile", reason="profile_students_only")
    student = data.students[viewer.linked_id]
    ans = Answer("ok", query, intent="profile", hits=[Hit("student", student)])
    if any(has_phrase(q, p) for p in NOW_PHRASES + NEXT_PHRASES):
        lesson = current_lesson(data, student, q, now)
        ans.note, ans.extra = "lesson", lesson
    return ans


def current_period(data: SchoolData, now: datetime | None) -> tuple[str, dict | None]:
    """Return (state, period). state: current | between | before | after | weekend.

    "between" is the few minutes of changeover between two periods (e.g. 8:45–8:50);
    the period returned is the one about to start.
    """
    t = school_now(data, now)
    if t.weekday() >= 5:
        return "weekend", None
    minutes = t.hour * 60 + t.minute
    timed = [p for p in data.periods if p["kind"] != "end"]
    if minutes < _hhmm(timed[0]["start"]):
        return "before", timed[0]
    for p in timed:
        if _hhmm(p["start"]) <= minutes < _hhmm(p["end"]):
            return "current", p
        if minutes < _hhmm(p["start"]):
            return "between", p
    return "after", next((p for p in data.periods if p["kind"] == "end"), None)


def current_lesson(data: SchoolData, student: dict, q: str, now: datetime | None) -> dict:
    state, period = current_period(data, now)
    want_next = any(has_phrase(q, p) for p in NEXT_PHRASES)
    if state == "between":  # changeover: the answer to "now" and "next" is the class about to start
        upcoming = next((p for p in data.periods if p["kind"] == "class"
                         and _hhmm(p["start"]) >= _hhmm(period["start"])), None)
        if not upcoming:
            return {"state": "after"}
        state, period, want_next = "current", upcoming, False
        label = "between"
    else:
        label = None
    if state != "current" and not (want_next and state == "before"):
        return {"state": state}
    order = [p["period_id"] for p in data.periods if p["kind"] == "class"]
    pid = period["period_id"]
    if want_next:
        if state == "before":
            pid = order[0]
        else:
            later = [p for p in data.periods if p["kind"] == "class" and _hhmm(p["start"]) >= _hhmm(period["end"])]
            if not later:
                return {"state": "after"}
            pid = later[0]["period_id"]
    day = school_now(data, now).strftime("%A")
    row = next((r for r in data.student_timetable(student["student_id"])
                if r["day"] == day and r["period_id"] == pid), None)
    p = next(p for p in data.periods if p["period_id"] == pid)
    return {"state": label or ("next" if want_next else "current"), "period": p, "row": row}


def schedule_answer(data: SchoolData, q: str, query: str, now: datetime | None) -> Answer | None:
    m = PERIOD_NUMBER.search(q)
    if m:
        p = next((p for p in data.periods if p["period_id"] == f"P{m.group(1)}"), None)
        if p:
            return Answer("ok", query, intent="schedule", hits=[Hit("period", p)])
        return Answer("not_found", query, intent="schedule", reason="no_such_period")
    if any(has_phrase(q, p) for p in NEXT_PHRASES):
        state, period = current_period(data, now)
        if state == "before":
            nxt = next(p for p in data.periods if p["kind"] == "class")
        elif state == "current":
            nxt = next((p for p in data.periods if p["kind"] == "class"
                        and _hhmm(p["start"]) >= _hhmm(period["end"])), None)
        elif state == "between":
            nxt = next((p for p in data.periods if p["kind"] == "class"
                        and _hhmm(p["start"]) >= _hhmm(period["start"])), None)
        else:
            nxt = None
        if nxt:
            return Answer("ok", query, intent="schedule", hits=[Hit("period", nxt)], note="next")
        # no class left today: after school, or during/after the last period
        return Answer("ok", query, intent="schedule",
                      note=state if state in ("weekend", "after") else "last")
    if any(has_phrase(q, p) for p in NOW_PHRASES) and not any(has_phrase(q, w) for w in ("event", "events", "su kien")):
        state, period = current_period(data, now)
        return Answer("ok", query, intent="schedule", hits=[Hit("period", period)] if period else [], note=state)
    if any(has_phrase(q, p) for p in ALL_PERIODS_PHRASES) or q in ("schedule", "bell schedule", "periods"):
        return Answer("ok", query, intent="schedule", hits=[Hit("period", p) for p in data.periods], note="all")
    return None


def event_answer(data: SchoolData, q: str, query: str, now: datetime | None) -> Answer | None:
    today = school_now(data, now).date()
    month = next((n for name, n in MONTHS.items() if has_phrase(q, name)), None)
    m = THANG_NUMBER.search(q)
    if m and 1 <= int(m.group(1)) <= 12:
        month = int(m.group(1))
    if month and (has_phrase(q, "event") or has_phrase(q, "events") or has_phrase(q, "su kien")
                  or has_phrase(q, "whats on") or has_phrase(q, "happening") or has_phrase(q, "lich")):
        hits = [Hit("event", e) for e in data.events
                if any(int(ym[5:]) == month for ym in event_months(e))]
        if hits:
            return Answer("ok", query, intent="event", hits=hits, note="month", extra={"month": month})
        return Answer("not_found", query, intent="event", reason="no_events_month", extra={"month": month})
    if has_phrase(q, "today") or has_phrase(q, "hom nay"):
        if has_phrase(q, "event") or has_phrase(q, "events") or has_phrase(q, "su kien") or has_phrase(q, "happening"):
            hits = [Hit("event", e) for e in data.events if e["date"] <= today.isoformat() <= event_end(e)]
            if hits:
                return Answer("ok", query, intent="event", hits=hits, note="today")
            return Answer("not_found", query, intent="event", reason="no_events_today")
    if any(has_phrase(q, p) for p in UPCOMING_PHRASES) or q in ("events", "calendar", "su kien"):
        # still running (e.g. a month-long project) or still to come
        hits = [Hit("event", e) for e in data.events if event_end(e) >= today.isoformat()][:MAX_RESULTS]
        if hits:
            return Answer("ok", query, intent="event", hits=hits, note="upcoming")
        return Answer("not_found", query, intent="event", reason="no_upcoming")
    return None


def suggestions_for(hits: list[Hit]) -> list[str]:
    """Weak matches become 'Did you mean ...?' suggestions."""
    out = []
    for h in hits[:3]:
        name = (h.item.get("title") or h.item.get("question") or h.item.get("name")
                or f"{h.item.get('title', '')} {h.item.get('first_name', '')} {h.item.get('last_name', '')}".strip())
        if h.kind == "teacher":
            name = f"{h.item['title']} {h.item['first_name']} {h.item['last_name']}"
        if name and name not in out:
            out.append(name)
    return out


# ------------------------------------------------------------- entry point
def answer(data: SchoolData, query: str, viewer: Viewer | None = None, now: datetime | None = None) -> Answer:
    viewer = viewer or Viewer()
    query = (query or "").strip()

    # 1. validate
    if not query:
        return Answer("invalid", query, reason="empty")
    if len(query) > MAX_QUERY_LENGTH:
        return Answer("invalid", query[:MAX_QUERY_LENGTH], reason="too_long")
    q = normalize(query)
    if not re.search(r"[a-z0-9]", q):
        return Answer("invalid", query, reason="no_words")

    # 2. greetings / help
    if q in GREETINGS:
        return Answer("help", query)

    # 3. privacy rules always run first
    private = privacy_check(data, q, viewer, query)
    if private:
        return private

    # 4. intent
    intent = detect_intent(q)
    # "What class do I have now / next?" is about the student's own timetable.
    if (viewer.role in ("guest", "student")
            and any(has_phrase(q, p) for p in NOW_PHRASES + NEXT_PHRASES)
            and any(has_phrase(q, w) for w in MY_LESSON_WORDS)):
        intent = "profile"
    if intent == "profile":
        return profile_answer(data, viewer, q, query, now)

    # 5. special rules
    special = schedule_answer(data, q, query, now) if intent in ("schedule", None, "event") else None
    special = special or (event_answer(data, q, query, now) if intent in ("event", None, "schedule") else None)
    if special:
        return special

    # 6. spelling + 7. scoring
    _, vocab = get_index(data)
    match_q, corrected = correct_spelling(q, vocab)
    hits = prefer_upcoming(rank(data, match_q, intent), school_now(data, now).date().isoformat())
    results = pick_results(hits, intent)

    if not results:
        return Answer("not_found", query, intent=intent, suggestions=suggestions_for(hits))

    ans = Answer("ok", query, intent=intent, hits=results, corrected=corrected)
    if intent == "location" and results[0].kind == "teacher":
        ans.note = "teacher_location"
    return ans

"""UI layer: web routes. Each route reads the request, asks the logic layer
(search.py) or the data layer (data.py), and renders a Jinja2 template.

HTMX requests (header "HX-Request") get just the answer fragment, so the
page updates without a full reload. Normal requests get the whole page,
so the app still works with JavaScript turned off.
"""

from __future__ import annotations

import logging
import os
import re
import secrets
import time
from collections import Counter
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from . import auth, store
from .data import SchoolData, event_months, load_data
from .i18n import LANGS, t, tr
from .search import answer as run_search, can_view_student, current_period, school_now
from .text import has_vietnamese_accents, normalize

log = logging.getLogger("ssa")
BASE = Path(__file__).resolve().parent

app = FastAPI(title="Smart School Assistant", docs_url=None, redoc_url=None, openapi_url=None)

SECRET = os.environ.get("SSA_SECRET_KEY")
if not SECRET:
    SECRET = secrets.token_hex(32)
    log.warning("SSA_SECRET_KEY is not set; using a random key (logins reset when the server restarts).")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET,
    session_cookie="ssa_session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=bool(os.environ.get("VERCEL")),
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' https://unpkg.com; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    return response


app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals.update(t=t, tr=tr)

# ------------------------------------------------------------------ data
_merged: dict = {"version": None, "data": None}


def get_data() -> SchoolData:
    """School data from the CSV files plus anything an admin added."""
    base = load_data()
    version = store.version()
    if version == 0:
        return base
    if _merged["version"] != version:
        faqs = base.faqs + store.extra_items("faqs")
        events = sorted(base.events + store.extra_items("events"), key=lambda e: (e["date"], e["start"]))
        _merged.update(version=version, data=replace(base, faqs=faqs, events=events))
    return _merged["data"]


# --------------------------------------------------------------- helpers
def get_lang(request: Request) -> str:
    lang = request.session.get("lang", "en")
    return lang if lang in LANGS else "en"


def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def safe_next(target: str | None) -> str:
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return "/"


def render(request: Request, name: str, status_code: int = 200, **context) -> HTMLResponse:
    data = get_data()
    user = auth.current_user(request)
    lang = context.pop("lang", None) or get_lang(request)
    context.update(
        request=request, data=data, user=user, lang=lang, page_lang=get_lang(request),
        school_name=tr(data.school, "name", get_lang(request)), path=request.url.path,
        today=school_now(data, None).date(),
    )
    return templates.TemplateResponse(request, name, context, status_code=status_code)


def filter_text(items: list[dict], q: str, fields: list[str]) -> list[dict]:
    words = normalize(q).split()
    if not words:
        return items
    out = []
    for item in items:
        haystack = normalize(" ".join(
            " ".join(v) if isinstance(v, list) else str(v)
            for k, v in item.items() if any(k.startswith(f) for f in fields)
        ))
        if all(w in haystack for w in words):
            out.append(item)
    return out


def remember(request: Request, query: str) -> None:
    history = [h for h in request.session.get("history", []) if h != query]
    request.session["history"] = ([query] + history)[:8]


# ---------------------------------------------------------------- routes
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, "index.html", result=None)


@app.api_route("/ask", methods=["GET", "POST"], response_class=HTMLResponse)
async def ask(request: Request):
    if request.method == "POST":
        form = await request.form()
        query = str(form.get("q", ""))
    else:
        query = request.query_params.get("q", "")
    data = get_data()
    user = auth.current_user(request)
    result = run_search(data, query, auth.viewer_for(user))
    # Answer in Vietnamese automatically if the question was typed with Vietnamese accents.
    lang = "vi" if has_vietnamese_accents(query) else get_lang(request)
    store.log_search(query, result.status, result.intent, user.role if user else "guest", lang)
    if result.status in ("ok", "not_found") and query.strip():
        remember(request, query.strip()[:200])
    template = "partials/answer.html" if is_htmx(request) else "index.html"
    return render(request, template, result=result, lang=lang)


@app.post("/history/clear", response_class=HTMLResponse)
def clear_history(request: Request):
    request.session.pop("history", None)
    if is_htmx(request):
        return HTMLResponse("")
    return RedirectResponse("/", status_code=303)


@app.get("/policies", response_class=HTMLResponse)
def policies(request: Request, category: str = "", q: str = ""):
    data = get_data()
    items = [p for p in data.policies if not category or p["category"] == category]
    items = filter_text(items, q, ["title", "keywords", "summary", "category"])
    categories = sorted({p["category"] for p in data.policies})
    return render(request, "policies.html", items=items, categories=categories, category=category, q=q)


@app.get("/directory", response_class=HTMLResponse)
def directory(request: Request, department: str = "", q: str = ""):
    data = get_data()
    items = [x for x in data.teachers.values() if not department or x["department"] == department]
    items = filter_text(items, q, ["first_name", "last_name", "display_name", "title", "subjects", "department", "position", "room_id",
                                 "homeroom_class"])
    departments = sorted({x["department"] for x in data.teachers.values()})
    return render(request, "directory.html", items=items, departments=departments, department=department, q=q)


@app.get("/map", response_class=HTMLResponse)
def campus_map(request: Request, room: str = "", building: str = ""):
    data = get_data()
    selected = data.rooms.get(room.upper()) if room else None
    bld = data.buildings.get((building or (selected or {}).get("building_id", "")).upper())
    rooms_here = [r for r in data.rooms.values() if bld and r["building_id"] == bld["building_id"]]
    return render(request, "map.html", selected=selected, building=bld, rooms_here=rooms_here,
                  bad_room=bool(room and not selected))


@app.get("/schedule", response_class=HTMLResponse)
def schedule(request: Request, month: str = ""):
    data = get_data()
    today = school_now(data, None).date()
    events = data.events
    if month and re.fullmatch(r"\d{4}-\d{2}", month):
        events = [e for e in events if month in event_months(e)]
    months = sorted(set().union(*(event_months(e) for e in data.events))) if data.events else []
    state_period = None
    state, period = current_period(data, None)
    if state == "current":
        state_period = period["period_id"]
    return render(request, "schedule.html", events=events, months=months, month=month,
                  current_period_id=state_period, today_iso=today.isoformat())


@app.get("/faqs", response_class=HTMLResponse)
def faqs(request: Request, category: str = "", q: str = ""):
    data = get_data()
    items = [f for f in data.faqs if not category or f["category"] == category]
    items = filter_text(items, q, ["question", "keywords", "answer", "category"])
    categories = sorted({f["category"] for f in data.faqs})
    return render(request, "faqs.html", items=items, categories=categories, category=category, q=q)


@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, student: str = ""):
    user = auth.current_user(request)
    if not user:
        return RedirectResponse("/login?next=/profile", status_code=303)
    data = get_data()
    viewer = auth.viewer_for(user)
    visible = [s for s in data.students.values() if can_view_student(data, viewer, s["student_id"])]
    if user.role == "student":
        student = user.linked_id
    elif not student and visible:
        student = visible[0]["student_id"]
    chosen = data.students.get(student)
    if chosen and not can_view_student(data, viewer, chosen["student_id"]):
        return render(request, "message.html", status_code=403, message=t("forbidden", get_lang(request)))
    return render(request, "profile.html", student=chosen, visible=visible)


# ----------------------------------------------------------------- login
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/"):
    return render(request, "login.html", error="", next=safe_next(next), username="")


@app.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, username: str = Form(""), password: str = Form(""), next: str = Form("/")):
    client = request.client.host if request.client else ""
    user, error = auth.authenticate(username, password, client)
    if not user:
        return render(request, "login.html", status_code=401, error=error, next=safe_next(next), username=username[:50])
    auth.login(request, user)
    return RedirectResponse(safe_next(next), status_code=303)


@app.post("/logout")
def logout(request: Request):
    auth.logout(request)
    return RedirectResponse("/", status_code=303)


@app.get("/lang/{code}")
def set_lang(request: Request, code: str, next: str = "/"):
    if code in LANGS:
        request.session["lang"] = code
    return RedirectResponse(safe_next(next), status_code=303)


# ----------------------------------------------------------------- admin
def require_admin(request: Request):
    user = auth.current_user(request)
    if not user:
        return RedirectResponse("/login?next=/admin", status_code=303)
    if user.role != "admin":
        return render(request, "message.html", status_code=403, message=t("forbidden", get_lang(request)))
    return None


def admin_stats() -> dict:
    entries = store.search_log()
    total = len(entries)
    statuses = Counter(e["status"] for e in entries)
    answered = statuses.get("ok", 0) + statuses.get("help", 0)
    top = Counter(normalize(e["query"]) for e in entries if e["status"] == "ok").most_common(8)
    unanswered = [e for e in reversed(entries) if e["status"] in ("not_found", "invalid")][:20]
    return {
        "total": total,
        "answered_pct": round(100 * answered / total) if total else 0,
        "statuses": dict(statuses),
        "intents": dict(Counter(e["intent"] or "none" for e in entries)),
        "roles": dict(Counter(e["role"] for e in entries)),
        "top": top,
        "unanswered": unanswered,
        "recent": list(reversed(entries))[:15],
    }


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, saved: str = "", error: str = ""):
    blocked = require_admin(request)
    if blocked:
        return blocked
    return render(request, "admin.html", stats=admin_stats(), extra_faqs=store.extra_items("faqs"),
                  extra_events=store.extra_items("events"), temporary=store.is_temporary(),
                  saved=saved, error=error)


def _clean(value: str, limit: int) -> str:
    return " ".join((value or "").split())[:limit]


@app.post("/admin/faq")
def admin_add_faq(request: Request, question: str = Form(""), answer: str = Form(""), category: str = Form(""),
                  keywords: str = Form(""), question_vi: str = Form(""), answer_vi: str = Form("")):
    blocked = require_admin(request)
    if blocked:
        return blocked
    question, answer_text = _clean(question, 200), _clean(answer, 1000)
    if len(question) < 5 or len(answer_text) < 5:
        return RedirectResponse("/admin?error=faq", status_code=303)
    store.add_item("faqs", {
        "faq_id": f"AF{int(time.time() * 1000)}", "question": question, "question_vi": _clean(question_vi, 200),
        "category": _clean(category, 40) or "General",
        "keywords": [k.strip() for k in _clean(keywords, 300).split(";") if k.strip()],
        "answer": answer_text, "answer_vi": _clean(answer_vi, 1000), "added_by_admin": True,
    })
    return RedirectResponse("/admin?saved=faq", status_code=303)


@app.post("/admin/event")
def admin_add_event(request: Request, name: str = Form(""), event_date: str = Form(""), start: str = Form(""),
                    end: str = Form(""), room_id: str = Form(""), description: str = Form(""),
                    name_vi: str = Form(""), description_vi: str = Form("")):
    blocked = require_admin(request)
    if blocked:
        return blocked
    data = get_data()
    name = _clean(name, 100)
    try:
        date.fromisoformat(event_date)
        valid_times = all(re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", x) for x in (start, end)) and start <= end
    except ValueError:
        valid_times = False
    if len(name) < 3 or not valid_times or (room_id and room_id not in data.rooms):
        return RedirectResponse("/admin?error=event", status_code=303)
    store.add_item("events", {
        "event_id": f"AE{int(time.time() * 1000)}", "name": name, "name_vi": _clean(name_vi, 100),
        "aliases": [], "date": event_date, "end_date": "", "start": start, "end": end, "room_id": room_id,
        "category": "event",
        "description": _clean(description, 500), "description_vi": _clean(description_vi, 500),
        "added_by_admin": True,
    })
    return RedirectResponse("/admin?saved=event", status_code=303)


@app.post("/admin/delete")
def admin_delete(request: Request, kind: str = Form(""), item_id: str = Form("")):
    blocked = require_admin(request)
    if blocked:
        return blocked
    if kind == "faqs":
        store.delete_item("faqs", item_id, "faq_id")
    elif kind == "events":
        store.delete_item("events", item_id, "event_id")
    return RedirectResponse("/admin?saved=deleted", status_code=303)


@app.post("/admin/clear-log")
def admin_clear_log(request: Request):
    blocked = require_admin(request)
    if blocked:
        return blocked
    store.clear_log()
    return RedirectResponse("/admin?saved=cleared", status_code=303)


# ----------------------------------------------------------------- misc
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return render(request, "about.html")


@app.get("/healthz")
def healthz():
    data = get_data()
    return JSONResponse({"ok": True, "teachers": len(data.teachers), "rooms": len(data.rooms),
                         "time": datetime.now().isoformat(timespec="seconds")})


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return render(request, "message.html", status_code=404, message=t("not_found_page", get_lang(request)))
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)

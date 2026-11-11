"""Small persistent store for things the app *writes*:

  - log.json      the search log (admin dashboard; used to improve the data)
  - content.json  FAQs and events added by an admin

Locally the files live in ./instance. On Vercel the project files are
read-only, so they live in /tmp, which is temporary: it resets when the
server restarts. For permanent storage, replace these functions with calls
to a database such as Supabase; nothing else in the app needs to change.

Privacy: the log never stores usernames, only the role, and questions that
were blocked by a privacy rule are stored as "[private request]".
"""

import json
import os
import threading
import time
from pathlib import Path

MAX_LOG = 2000
_lock = threading.Lock()


def store_dir() -> Path:
    if os.environ.get("SSA_STORE_DIR"):
        return Path(os.environ["SSA_STORE_DIR"])
    if os.environ.get("VERCEL"):
        return Path("/tmp/ssa")
    return Path(__file__).resolve().parent.parent / "instance"


def is_temporary() -> bool:
    return bool(os.environ.get("VERCEL")) and not os.environ.get("SSA_STORE_DIR")


def _read(name: str, default):
    try:
        return json.loads((store_dir() / name).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write(name: str, value) -> None:
    path = store_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


# ------------------------------------------------------------- search log
def log_search(query: str, status: str, intent: str | None, role: str, lang: str) -> None:
    private = status in ("private", "login_required")
    entry = {
        "ts": int(time.time()),
        "query": "[private request]" if private else query[:200],
        "status": status,
        "intent": intent or "",
        "role": role,
        "lang": lang,
    }
    with _lock:
        log = _read("log.json", [])
        _write("log.json", (log + [entry])[-MAX_LOG:])


def search_log() -> list[dict]:
    return _read("log.json", [])


def clear_log() -> None:
    with _lock:
        _write("log.json", [])


# ------------------------------------------------------ admin-added data
def _content() -> dict:
    return _read("content.json", {"version": 0, "faqs": [], "events": []})


def version() -> int:
    return _content().get("version", 0)


def extra_items(kind: str) -> list[dict]:
    return _content().get(kind, [])


def add_item(kind: str, item: dict) -> None:
    with _lock:
        content = _content()
        content.setdefault(kind, []).append(item)
        content["version"] = content.get("version", 0) + 1
        _write("content.json", content)


def delete_item(kind: str, item_id: str, id_field: str) -> None:
    with _lock:
        content = _content()
        content[kind] = [i for i in content.get(kind, []) if i.get(id_field) != item_id]
        content["version"] = content.get("version", 0) + 1
        _write("content.json", content)

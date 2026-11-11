"""Login and role-based access.

Demo accounts live in data/users.csv. Passwords are never stored in plain
text: each row holds a salted PBKDF2-SHA256 hash. After logging in, the
user's username, role and linked ID are kept in a signed session cookie.
"""

import hashlib
import hmac
import time
from dataclasses import dataclass

from fastapi import Request

from .data import load_data
from .search import Viewer

MAX_FAILURES = 5
LOCKOUT_SECONDS = 300
_failures: dict[str, list[float]] = {}


@dataclass
class User:
    username: str
    role: str          # student | teacher | admin
    linked_id: str     # student_id or teacher_id


def hash_password(password: str, salt: bytes, iterations: int = 120_000) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, _ = stored.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    expected = hash_password(password, bytes.fromhex(salt_hex), int(iterations))
    return hmac.compare_digest(expected, stored)


def is_locked(key: str) -> bool:
    now = time.time()
    recent = [t for t in _failures.get(key, []) if now - t < LOCKOUT_SECONDS]
    _failures[key] = recent
    return len(recent) >= MAX_FAILURES


def authenticate(username: str, password: str, client: str = "") -> tuple[User | None, str]:
    """Return (user, error). error is '' on success, else 'login_failed' / 'login_locked'."""
    username = (username or "").strip().lower()
    key = f"{username}|{client}"
    if is_locked(key):
        return None, "login_locked"
    row = load_data().users.get(username)
    if row and verify_password(password or "", row["password_hash"]):
        _failures.pop(key, None)
        return User(username, row["role"], row["linked_id"]), ""
    _failures.setdefault(key, []).append(time.time())
    return None, "login_failed"


def current_user(request: Request) -> User | None:
    data = request.session.get("user")
    if not data:
        return None
    # Re-check the account still exists (e.g. after data changes).
    row = load_data().users.get(data.get("username", ""))
    if not row:
        request.session.pop("user", None)
        return None
    return User(data["username"], row["role"], row["linked_id"])


def viewer_for(user: User | None) -> Viewer:
    return Viewer(user.role, user.linked_id) if user else Viewer()


def login(request: Request, user: User) -> None:
    request.session["user"] = {"username": user.username}


def logout(request: Request) -> None:
    request.session.pop("user", None)
    request.session.pop("history", None)

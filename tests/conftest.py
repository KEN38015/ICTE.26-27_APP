import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SSA_SECRET_KEY", "test-secret")
# Tests always run on the fixed sample school, so they keep passing after the real data is imported.
os.environ["SSA_DATA_DIR"] = str(ROOT / "tests" / "fixtures" / "sample_data")

from app.data import load_data  # noqa: E402

# A fixed school-day moment so time-based answers are repeatable:
# Tuesday 10 November 2026, 10:30 (Period 3).
SCHOOL_TIME = datetime(2026, 11, 10, 10, 30, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

# Demo accounts (fictional, for testing only). Passwords are listed in README.md.
# In the sample data the "teacher" account is Ms Hannah Brooks (T08).
PASSWORDS = {
    "alex": "Alex-Demo-2026",
    "khanh": "Khanh-Demo-2026",
    "chloe": "Chloe-Demo-2026",
    "teacher": "Teacher-Demo-2026",
    "admin": "Admin-Demo-2026",
}


@pytest.fixture(scope="session")
def data():
    return load_data()


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Each test writes its search log / admin items to a fresh temp folder."""
    monkeypatch.setenv("SSA_STORE_DIR", str(tmp_path))
    from app import auth
    auth._failures.clear()
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def login(client, username):
    return client.post("/login", data={"username": username, "password": PASSWORDS[username], "next": "/"},
                       follow_redirects=False)

"""Tests for the web app: pages, HTMX answers, login, roles and admin."""

from conftest import PASSWORDS, login


def test_all_pages_load(client):
    for path in ["/", "/policies", "/directory", "/map", "/map?room=B201", "/map?building=A",
                 "/schedule", "/faqs", "/login", "/about", "/healthz"]:
        assert client.get(path).status_code == 200, path


def test_unknown_page_is_404(client):
    assert client.get("/does-not-exist").status_code == 404


def test_htmx_answer_is_a_fragment(client):
    r = client.post("/ask", data={"q": "Where is the ICT room?"}, headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert "B201" in r.text and "<html" not in r.text


def test_answer_works_without_javascript(client):
    r = client.post("/ask", data={"q": "Where is the ICT room?"})
    assert "<html" in r.text and "B201" in r.text


def test_user_input_is_escaped(client):
    r = client.post("/ask", data={"q": "<script>alert(1)</script>"}, headers={"HX-Request": "true"})
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text


def test_vietnamese_question_gets_vietnamese_answer(client):
    r = client.post("/ask", data={"q": "Phòng Tin học ở đâu?"}, headers={"HX-Request": "true"})
    assert "Chỉ đường" in r.text


def test_language_switch(client):
    client.get("/lang/vi")
    assert "Trang chủ" in client.get("/").text
    client.get("/lang/en")
    assert "Home" in client.get("/").text


def test_open_redirect_is_blocked(client):
    r = client.get("/lang/vi?next=//evil.example.com", follow_redirects=False)
    assert r.headers["location"] == "/"


def test_security_headers(client):
    r = client.get("/")
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]


def test_search_history_is_per_session(client):
    client.post("/ask", data={"q": "uniform policy"})
    assert "uniform policy" in client.get("/").text
    client.post("/history/clear")
    assert "Your recent searches" not in client.get("/").text


# ----------------------------------------------------------------- login
def test_login_success_and_logout(client):
    r = login(client, "alex")
    assert r.status_code == 303
    assert "alex" in client.get("/").text
    client.post("/logout")
    assert "Log out" not in client.get("/").text


def test_login_wrong_password(client):
    r = client.post("/login", data={"username": "alex", "password": "wrong"})
    assert r.status_code == 401 and "Incorrect" in r.text


def test_login_lockout_after_repeated_failures(client):
    for _ in range(5):
        client.post("/login", data={"username": "alex", "password": "wrong"})
    r = client.post("/login", data={"username": "alex", "password": PASSWORDS["alex"]})
    assert r.status_code == 401 and "Too many attempts" in r.text


def test_passwords_are_not_stored_in_plain_text():
    from pathlib import Path
    text = (Path(__file__).resolve().parent.parent / "data" / "users.csv").read_text()
    for pw in PASSWORDS.values():
        assert pw not in text


# ------------------------------------------------------- role-based access
def test_profile_requires_login(client):
    r = client.get("/profile", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/login")


def test_student_sees_only_own_profile(client):
    login(client, "alex")
    r = client.get("/profile?student=S002")       # tries to open Khanh's profile
    assert "Alex Carter" in r.text and "Khanh Ngo" not in r.text


def test_teacher_sees_only_their_students(client):
    login(client, "teacher")
    assert "Chloe Reed" in client.get("/profile?student=S003").text
    r = client.get("/profile?student=S002")
    assert r.status_code == 403


def test_admin_page_blocked_for_students(client):
    login(client, "alex")
    assert client.get("/admin").status_code == 403
    assert client.post("/admin/faq", data={"question": "x" * 10, "answer": "y" * 10}).status_code == 403


def test_admin_adds_faq_and_it_becomes_searchable(client):
    login(client, "admin")
    r = client.post("/admin/faq", data={"question": "Is there a school bus?", "answer": "Yes, from 7:00.",
                                        "category": "Transport", "keywords": "bus;school bus;transport"},
                    follow_redirects=False)
    assert r.status_code == 303 and "saved" in r.headers["location"]
    a = client.post("/ask", data={"q": "school bus"}, headers={"HX-Request": "true"})
    assert "Is there a school bus?" in a.text


def test_admin_rejects_invalid_event(client):
    login(client, "admin")
    r = client.post("/admin/event", data={"name": "Bad", "event_date": "not-a-date", "start": "10:00", "end": "11:00"},
                    follow_redirects=False)
    assert "error" in r.headers["location"]


def test_search_log_hides_private_questions(client):
    client.post("/ask", data={"q": "what is Alex's phone number"})
    login(client, "admin")
    page = client.get("/admin").text
    assert "[private request]" in page
    assert "phone number" not in page.split("Recent searches")[1]

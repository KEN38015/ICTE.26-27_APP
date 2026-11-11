"""SenTia campus cases: real rooms (from the floor-map signs and door signs) and real staff,
against the live /data folder. IDs match the "SenTia campus cases" table in docs/TEST_CASES.md."""

import pytest

from app.data import DEFAULT_DATA_DIR, display_name, load_data  # noqa: F401
from app.search import answer


@pytest.fixture(scope="module")
def live():
    return load_data(DEFAULT_DATA_DIR)


def label(hit):
    return hit.item["display_name"] if hit.kind == "teacher" else hit.item.get("room_id") or hit.item.get("policy_id")


CASES = [  # (id, question, acceptable top result)
    ("CC01", "where is 6A1", {"B2-06"}),
    ("CC02", "lớp 9A1 ở đâu", {"B3-05"}),
    ("CC03", "where is room B4-07", {"B4-07"}),
    ("CC04", "b407", {"B4-07"}),
    ("CC05", "where is the ICT room", {"B4-07"}),
    ("CC06", "phòng máy ở đâu", {"B4-07"}),
    ("CC07", "thư viện ở đâu", {"B3-06"}),
    ("CC08", "where is the toilet", {"WC-B1", "WC-B2", "WC-B3", "WC-B4", "WC-A1", "WC-A2", "WC-A3"}),
    ("CC09", "căng tin ở đâu", {"CANTEEN"}),
    ("CC10", "where is the gym", {"GYM"}),
    ("CC11", "where is the school office", {"1-01"}),
    ("CC12", "principal's office", {"B2-03"}),
    ("CC13", "where is A2-03", {"A2-03"}),
    ("CC14", "who is 6A1's homeroom teacher", {"Đỗ Ngọc Anh"}),
    ("CC15", "gvcn lớp 9A1", {"Đặng Thị Hà"}),                     # improved after testing
    ("CC16", "homeroom teacher of 10A2", {"Nguyễn Văn Vinh"}),      # improved after testing
    ("CC17", "chủ nhiệm lớp 12A2", {"Đoàn Thị Phương"}),
    ("CC18", "thầy Trung", {"Nguyễn Thành Trung"}),
    ("CC19", "where is cô Huyền", {"Nguyễn Thị Huyền"}),
    ("CC20", "Mr Kingsley", {"Alex Kingsley"}),
    ("CC21", "cô Tuệ Thư", {"Nguyễn Thị Tuệ Thư"}),
    ("CC22", "who is the principal", {"Joey"}),
    ("CC23", "vice principal", {"Nguyễn Thị Kim Khánh"}),             # improved after testing
    ("CC24", "phó hiệu trưởng", {"Nguyễn Thị Kim Khánh"}),            # improved after testing
    ("CC25", "secondary principal", {"Philip MacDonald-Milner"}),
    ("CC26", "who is the librarian", {"Lan"}),
    ("CC27", "where is the nurse", {"Hà Hoài", "Kiều Thị Hương Mai"}),
    ("CC28", "school counsellor", {"Đặng Quỳnh Trang", "Ngô Phương Linh"}),
    ("CC29", "bảo vệ", {"Tuấn"}),
    ("CC30", "thầy Alex", {"Alex Kingsley"}),                         # improved after testing
    ("CC31", "cô Khanh", {"Vũ Ngọc Khanh", "Nguyễn Thị Kim Khánh"}),  # improved after testing
    ("CC32", "Mr Austin", {"James Austin"}),
    ("CC33", "who teaches IGCSE science", {"R-Jay Bool"}),
]


@pytest.mark.parametrize("case_id,query,expected", CASES, ids=[c[0] for c in CASES])
def test_campus_question(live, case_id, query, expected):
    r = answer(live, query)
    assert r.status == "ok", f"{case_id}: {r.status}"
    assert label(r.hits[0]) in expected, f"{case_id}: top result was {label(r.hits[0])}"


def test_chemistry_teacher_question_does_not_match_a_teacher_named_hoa(live):
    """'giáo viên hóa học' without accents is 'giao vien hoa hoc'; cô Diệu Hoa is not a chemistry teacher."""
    names = {label(h) for h in answer(live, "giáo viên hóa học").hits}
    assert names == {"Trần Minh Phúc", "Bùi Xuân Dũng"}


def test_family_name_alone_does_not_match(live):
    """Vietnamese teachers are called by their given name: 'cô Hà' must not find Hà Thu Ly."""
    names = {label(h) for h in answer(live, "cô Hà").hits}
    assert "Hà Thu Ly" not in names and names <= {"Nguyễn Thị Thu Hà A", "Nguyễn Thị Thu Hà B", "Đặng Thị Hà"}


def test_thu_ha_is_not_thu(live):
    names = {label(h) for h in answer(live, "cô Thu Hà").hits}
    assert names == {"Nguyễn Thị Thu Hà A", "Nguyễn Thị Thu Hà B"}


def test_nurse_is_not_invented(live):
    """There is no nurse's room on the floor maps, so no room is returned."""
    assert all(h.kind != "room" for h in answer(live, "where is the nurse").hits)


def test_every_class_on_a_door_sign_has_its_room_and_homeroom_teacher(live):
    signs = {"6A1": "B2-06", "6A2": "B2-07", "7A1": "B2-05", "7A2": "B2-04", "8A1": "B2-01", "8A2": "B2-02",
             "9A1": "B3-05", "9A2": "B3-04", "10A1": "B4-03", "10A2": "B4-04", "11A": "B4-05",
             "12A1": "B4-06", "12A2": "B4-08"}
    homeroom = {t["homeroom_class"]: t for t in live.teachers.values() if t.get("homeroom_class")}
    assert set(homeroom) == set(signs)
    for cls, room in signs.items():
        assert homeroom[cls]["room_id"] == room
        assert live.rooms[room]["name"] == f"Class {cls}"


def test_directions_name_the_stair_and_neighbouring_doors(live):
    d = live.rooms["B2-06"]["directions"]
    assert "stair 4" in d and "floor 2" in d and "B2-05" in d and "B2-07" in d
    assert "cầu thang 4" in live.rooms["B2-06"]["directions_vi"]


def test_titles_come_from_the_sheet(live):
    """Titles are the team's (Ms/Mr), shown before the name; none are guessed."""
    assert {t["title"] for t in live.teachers.values()} == {"Ms", "Mr"}
    assert display_name(next(t for t in live.teachers.values() if t["display_name"] == "Đỗ Ngọc Anh")) == "Ms Đỗ Ngọc Anh"


def test_map_pins_stay_inside_their_building(live):
    for r in live.rooms.values():
        b = live.buildings[r["building_id"]]
        assert int(b["x"]) <= int(r["map_x"]) <= int(b["x"]) + int(b["w"]), r["room_id"]
        assert int(b["y"]) <= int(r["map_y"]) <= int(b["y"]) + int(b["h"]), r["room_id"]


def test_demo_student_names_still_private_without_a_title(live):
    """'where is Khanh' (no title) could mean the fictional student, so it still asks for a login."""
    assert answer(live, "where is Khanh").status == "login_required"
    assert answer(live, "Alex Carter").status == "login_required"


def test_removed_staff_member_is_gone(live):
    assert not any(t["last_name"] == "Soriano" for t in live.teachers.values())
    assert answer(live, "who is Richard Soriano").status == "not_found"


def test_single_name_staff_need_a_title(live):
    """'Ms Lan' works, but the everyday word 'lần' (times) doesn't find her."""
    assert all(h.kind != "teacher" for h in answer(live, "bao nhiêu lần").hits)


def test_cards_do_not_show_search_words_as_subjects(live):
    nurse = next(t for t in live.teachers.values() if t["display_name"] == "Hà Hoài")
    assert nurse["subjects"] == [] and "nurse" in nurse["keywords"]


def test_names_the_team_corrected(live):
    shown = {t["display_name"] for t in live.teachers.values()}
    assert {"Joey", "Christopher Robinson", "Tuấn"} <= shown
    assert not shown & {"Hồ Nghi Joey", "Chirstopher Robinson", "Tuân"}
    assert answer(live, "Hồ Nghi Joey").hits[0].item["display_name"] == "Joey"   # full name still works


def test_librarian_is_in_the_secondary_library(live):
    """Team confirmed: the librarian is in the room to the right of B3-05, which is B3-06."""
    lan = next(t for t in live.teachers.values() if t["position"] == "Librarian")
    assert lan["room_id"] == "B3-06"
    hit = answer(live, "where is the librarian").hits[0]
    assert hit.kind == "teacher" and hit.item["room_id"] == "B3-06"


def test_map_draws_no_gates(live):
    """The gates were removed from the map until their real positions are known."""
    from fastapi.testclient import TestClient
    from app.main import app
    page = TestClient(app).get("/map?room=L001").text   # the web app runs on the test fixture school
    assert "map-gate" not in page and "Main gate" not in page and "map-route" in page
    assert "gate" not in live.school["map"]

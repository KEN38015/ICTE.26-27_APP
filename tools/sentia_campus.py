"""Build SenTia's real campus data from the team's photos and sheet.

Sources (November 2026):
  - the four official "SENTIA SCHOOL MAP" floor signs (Tầng 1–4), photographed by the team
  - door signs: room number, class and homeroom teacher
  - the team's Google Sheet, tab teacherProfiles (names, subjects, departments)

Writes data/buildings.csv, rooms.csv, teachers.csv, timetable.csv, students.csv,
clubs.csv and events.csv room links, plus the map layout in school.json.

Nothing here is guessed about real people: titles (Ms/Mr) come from the sheet, and
rooms whose purpose isn't on a sign are just "Room X".
The demo students, their timetables and clubs are fictional.

Run:  .venv/bin/python -m tools.sentia_campus
"""

import csv
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# ---------------------------------------------------------------- floor plans
# Each corridor is listed in order along the building, as on the floor signs.
# "S4" = stair 4, "WC" = toilets. Zone B has stairs 4 and 5; Zone A has 1, 2 and 3.
B_ROWS = {
    1: (["B1-06", "WC", "S4"], ["B1-05", "S5", "B1-04", "B1-03", "B1-02", "B1-01", "1-01"]),
    2: (["B2-04", "B2-05", "B2-06", "B2-07", "WC", "S4", "2-03", "2-04"],
        ["B2-03", "S5", "B2-02", "B2-01", "2-01", "2-02"]),
    3: (["B3-04", "B3-05", "B3-06", "WC", "S4", "3-02"], ["B3-03", "S5", "B3-02", "B3-01", "3-01"]),
    4: (["B4-08", "B4-09", "B4-10", "B4-11", "WC", "S4", "B4-12"],
        ["B4-07", "S5", "B4-06", "B4-05", "B4-04", "B4-03", "B4-02", "B4-01"]),
}
A_ROWS = {
    1: (["S2", "A1-11", "WC", "A1-10", "A1-09", "A1-08", "A1-07"],
        ["S1", "A1-01", "A1-02", "A1-03", "A1-04", "S3", "A1-05", "A1-06"]),
    2: (["S2", "A2-10", "WC", "A2-09", "A2-08", "A2-07", "A2-06"],
        ["S1", "A2-01", "A2-02", "A2-03", "A2-04", "S3", "A2-05"]),
    3: (["S2", "A3-08", "WC", "A3-07", "A3-06", "A3-05", "A3-04"],
        ["S1", "A3-01", "A3-02", "S3", "A3-03"]),
    4: (["S2", "A4-01"], []),
}

# Rooms whose purpose is written on the door sign or floor map.
# room_id: (name, name_vi, aliases)
NAMED = {
    "1-01": ("School Office", "Văn phòng nhà trường",
             "office;school office;front office;reception;admin office;van phong;le tan;phong hanh chinh"),
    "2-02": ("Multi-functional Room", "Phòng đa năng",
             "multi-functional room;multi-purpose room;multipurpose room;hall;phong da nang"),
    "B2-03": ("Secondary School Board's Room", "Phòng Ban Giám hiệu Trung học",
              "principal's office;principal office;school board;board room;"
              "ban giam hieu;phong bgh;bgh;phong hieu truong"),
    "B3-03": ("Primary Department Room", "Phòng Bộ môn Tiểu học", "primary department;bo mon tieu hoc"),
    "B3-06": ("Secondary & High School Library", "Thư viện cấp THCS – THPT",
              "library;secondary library;high school library;thu vien;thu vien thcs;thu vien thpt"),
    "3-01": ("Primary Library", "Thư viện cấp Tiểu học", "primary library;thu vien tieu hoc"),
    "B4-02": ("Career Counselling Room", "Phòng Tư vấn hướng nghiệp",
              "career counselling;careers;career advice;career guidance;huong nghiep;tu van huong nghiep"),
    "B4-07": ("ICT Room (Secondary)", "Phòng ICT Trung học",
              "ict room;ict;computer lab;computer room;it room;phong may;phong tin hoc;tin hoc;phong ict"),
    "B4-12": ("Communications & Marketing Room", "Phòng Truyền thông & Tiếp thị",
              "pr;marketing;communications;pr mkt;truyen thong;tiep thi"),
}

# Door signs: class -> (room, homeroom teacher's full name as written on the sign)
CLASSES = {
    "6A1": ("B2-06", "Đỗ Ngọc Anh"), "6A2": ("B2-07", "Khuất Thị Tuấn"),
    "7A1": ("B2-05", "Nguyễn Thị Thanh Hiếu"), "7A2": ("B2-04", "Nguyễn Thị Huyền"),
    "8A1": ("B2-01", "Trần Ngọc Linh"), "8A2": ("B2-02", "Nguyễn Thị Thu Hà A"),
    "9A1": ("B3-05", "Đặng Thị Hà"), "9A2": ("B3-04", "Bùi Xuân Dũng"),
    "10A1": ("B4-03", "Nguyễn Thị Thúy"), "10A2": ("B4-04", "Nguyễn Văn Vinh"),
    "11A": ("B4-05", "Trần Minh Phúc"),
    "12A1": ("B4-06", "Hà Thu Ly"), "12A2": ("B4-08", "Đoàn Thị Phương"),
}

# ---------------------------------------------------------------- teachers
# teacherProfiles tab (11 Nov 2026), in sheet order: title, last, middle, first, subjects, department
SHEET_TEACHERS = [
    ("Ms", "Đỗ", "Ngọc", "Anh", "Literature", "Literature"),
    ("Ms", "Nguyễn", "Thị Thu", "Hà B", "Maths", "Maths"),
    ("Mr", "Nguyễn", "Thành", "Trung", "Physics", "Science"),
    ("Mr", "Trần", "Minh", "Phúc", "Chemistry", "Science"),
    ("Ms", "Hà", "Thu", "Ly", "Biology", "Science"),
    ("Ms", "Nguyễn", "Thị Thanh", "Hiếu", "History", "Social Studies"),
    ("Ms", "Nguyễn", "Thị", "Huyền", "Geography", "Social Studies"),
    ("Ms", "Lê", "Khánh", "Linh", "ICT", "ICT"),
    ("Ms", "Lê", "Nguyễn Trúc", "Vy", "Music", "Arts & Music"),
    ("Ms", "Phạm", "Thị Thúy", "Hằng", "Arts", "Arts & Music"),
    ("Ms", "Đặng", "Quỳnh", "Trang", "Life Skills; Counselor", "Life Skills"),
    ("Mr", "Đào", "Nam", "Hải", "PE", "PE"),
    ("Ms", "Khuất", "Thị", "Tuấn", "Maths", "Maths"),
    ("Mr", "Nguyễn", "Anh", "Đức", "Science", "Science"),
    ("Ms", "Đặng", "Thị", "Hà", "Literature", "Literature"),
    ("Ms", "Nguyễn", "Thị", "Len", "Biology", "Science"),
    ("Ms", "Trần", "Ngọc", "Linh", "English", "Literature"),
    ("Ms", "Nguyễn", "Thị Thu", "Hà A", "Maths", "Maths"),
    ("Ms", "Nguyễn", "Diệu", "Hoa", "Literature", "Literature"),
    ("Mr", "Trịnh", "Mạnh", "Khuê", "Music", "Arts & Music"),
    ("Mr", "Kingsley", "Katandawa", "Alex", "ICT", "ICT"),
    ("Mr", "Trần", "Quốc", "Thư", "ICT", "ICT"),
    ("Mr", "Soriano", "Santos", "Richard", "PE", "PE"),
    ("Ms", "Nguyễn", "Thị", "Thúy", "Physics", "Science"),
    ("Mr", "Bùi", "Xuân", "Dũng", "Chemistry", "Science"),
    ("Ms", "Ngô", "Phương", "Linh", "Life Skills; Counselor", "Life Skills"),
    ("Ms", "Vũ", "Ngọc", "Khanh", "English", "Literature"),
    ("Ms", "Nguyễn", "Thị Vân", "Anh", "Economics and Law", "Social Studies"),
    ("Mr", "Nguyễn", "Văn", "Vinh", "Geography", "Social Studies"),
    ("Ms", "Vũ", "Thị Hương", "Quỳnh", "Maths", "Maths"),
    ("Ms", "Trần", "Thị Kim", "Oanh", "History", "Social Studies"),
    ("Ms", "Đoàn", "Thị", "Phương", "Maths", "Maths"),
    ("Ms", "Trần", "Minh", "Tâm", "Literature", "Literature"),
    ("Mr", "Nguyễn", "Nhật", "Minh", "Music", "Arts & Music"),
    ("Ms", "Nguyễn", "Thị Tuệ", "Thư", "Arts", "Arts & Music"),
    ("Ms", "Đinh", "Hồng", "Điệp", "Career Counselling", "Social Studies"),
    ("Ms", "Bùi", "Thị", "Thùy", "Literature", "Literature"),
    ("Ms", "Hồ", "Nghi", "Joey", "Principal", "School administration board"),
    ("Mr", "MacDonald-Milner", "James", "Philip", "Principal of Secondary", "School administration board"),
    ("Ms", "Nguyễn", "Thị Kim", "Khánh", "Vice-principal of Secondary", "School administration board"),
    ("Ms", "", "", "Lan", "Librarian", "Others"),
    ("Mr", "Robinson", "", "Christopher", "English", "Literature"),     # sheet typo "Chirstopher" fixed (team confirmed)
    ("Mr", "Austin", "", "James", "English", "Literature"),
    ("Mr", "Alcantara", "Kelvin", "John", "Maths", "Maths"),
    ("Mr", "Suyat", "Rouen", "Renz", "Science", "Science"),
    ("Ms", "Magtibay", "Dianne Dimatatac", "Lara", "Wellbeing", "Social Studies"),
    ("Mr", "Bool", "Delizo", "R-Jay", "IGCSE Science", "Science"),
    ("Ms", "", "", "Tuấn", "School guard", "Others"),                    # team confirmed: Ms Tuấn
    ("Ms", "Hà", "", "Hoài", "School nurse", "Others"),
    ("Ms", "Kiều", "Thị Hương", "Mai", "School nurse", "Others"),
    ("Ms", "Phạm", "Thị", "Hương", "School chef", "Others"),
]
EXCLUDED = {"Richard"}   # removed at the team's request (still in the sheet)
# How people are known at school, when it differs from the full name (team confirmed).
# The full name stays searchable.
GOES_BY = {"Hồ Nghi Joey": "Joey"}

# Vietnamese family names: these names are shown family name first ("Đỗ Ngọc Anh").
# Others are shown Western style, first + last ("Alex Kingsley").
VN_SURNAMES = {"Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ",
               "Ngô", "Dương", "Lý", "Hà", "Đào", "Đinh", "Khuất", "Trịnh", "Đoàn", "Kiều", "Mai", "Lương", "Tống"}

SUBJECT_VI = {
    "Literature": "Ngữ văn", "Maths": "Toán", "Physics": "Vật lý", "Chemistry": "Hóa học",
    "Biology": "Sinh học", "History": "Lịch sử", "Geography": "Địa lý", "ICT": "Tin học",
    "Music": "Âm nhạc", "Arts": "Mỹ thuật", "Life Skills": "Kỹ năng sống", "PE": "Thể dục",
    "English": "Tiếng Anh", "Economics and Law": "Giáo dục kinh tế và pháp luật",
    "Career Counselling": "Tư vấn hướng nghiệp", "Science": "Khoa học", "IGCSE Science": "Khoa học IGCSE",
    "Wellbeing": "Chăm sóc sức khỏe tinh thần", "Counselor": "Tư vấn tâm lý",
}
DEPT = {   # sheet department -> (English, Vietnamese)
    "Literature": ("Literature", "Ngữ văn"), "Maths": ("Maths", "Toán"), "Science": ("Science", "Khoa học tự nhiên"),
    "Social Studies": ("Social Studies", "Khoa học xã hội"), "ICT": ("ICT", "Tin học"),
    "Arts & Music": ("Arts & Music", "Nghệ thuật"), "Life Skills": ("Life Skills", "Kỹ năng sống"),
    "PE": ("PE", "Giáo dục thể chất"),
    "School administration board": ("School Board", "Ban Giám hiệu"), "Others": ("Other staff", "Nhân viên khác"),
}
# Jobs that aren't subjects: sheet value -> (position, position_vi, room, extra search words)
ROLES = {
    "Principal": ("Principal", "Hiệu trưởng nhà trường", "", "head;headmaster;head teacher;head of school;hieu truong"),
    "Principal of Secondary": ("Principal of Secondary", "Hiệu trưởng cấp Trung học", "B2-03",
                               "secondary principal;head of secondary;hieu truong trung hoc;hieu truong cap trung hoc"),
    "Vice-principal of Secondary": ("Vice-principal of Secondary", "Phó Hiệu trưởng cấp Trung học", "B2-03",
                                    "vice principal;deputy principal;deputy head;pho hieu truong;hieu pho"),
    "Librarian": ("Librarian", "Thủ thư", "B3-06", "librarian;library;thu thu;thu vien"),
    "School guard": ("School Guard", "Bảo vệ", "", "guard;security;security guard;bao ve"),
    "School nurse": ("School Nurse", "Nhân viên y tế", "", "nurse;school nurse;medical;sick;y te;phong y te;nhan vien y te"),
    "School chef": ("School Chef", "Đầu bếp", "CANTEEN", "chef;cook;kitchen;canteen;dau bep;nau an"),
}
SUBJECT_ROOM = {"ICT": "B4-07", "PE": "GYM", "Career Counselling": "B4-02"}


def full_name(last: str, middle: str, first: str) -> str:
    if not last:
        return first
    if last in VN_SURNAMES:
        return " ".join(p for p in (last, middle, first) if p)
    return f"{first} {last}"


def build_teachers() -> list[dict]:
    homeroom = {name: cls for cls, (_, name) in CLASSES.items()}
    rows = []
    for title, last, middle, first, subject_cell, dept in SHEET_TEACHERS:
        if first in EXCLUDED:
            continue
        name = full_name(last.strip(), middle.strip(), first.strip())
        known_as = GOES_BY.get(name, name)
        subjects = [s.strip() for s in subject_cell.split(";") if s.strip()]
        teaching = [s for s in subjects if s in SUBJECT_VI and s not in ROLES]
        cls = homeroom.get(name, "")
        room, extra = "", ""
        if subject_cell in ROLES:
            position, position_vi, room, extra = ROLES[subject_cell]
            teaching = []
        elif cls:
            position, position_vi = f"Homeroom Teacher, Class {cls}", f"Giáo viên chủ nhiệm lớp {cls}"
            room = CLASSES[cls][0]
        elif teaching == ["Career Counselling"]:
            position, position_vi, room = "Career Counsellor", "Tư vấn hướng nghiệp", SUBJECT_ROOM["Career Counselling"]
        elif "Counselor" in teaching:
            main = [s for s in teaching if s != "Counselor"]
            position = f"{' & '.join(main)} Teacher, School Counsellor"
            position_vi = f"Giáo viên {', '.join(SUBJECT_VI[s] for s in main)}, Tư vấn tâm lý"
            extra = "counsellor;counselor;school counsellor;tu van tam ly;tu van hoc duong"
        elif teaching == ["Wellbeing"]:
            position, position_vi = "Wellbeing Teacher", "Giáo viên chăm sóc sức khỏe tinh thần"
            extra = "wellbeing;well being;mental health;suc khoe tinh than"
        else:
            position = f"{teaching[0]} Teacher"
            position_vi = f"Giáo viên {SUBJECT_VI[teaching[0]]}"
        if not room and teaching:
            room = SUBJECT_ROOM.get(teaching[0], "")
        words = [w for s in teaching for w in (s, SUBJECT_VI[s])]
        dept_en, dept_vi = DEPT[dept]
        rows.append({
            "teacher_id": f"T{len(rows) + 1:02d}", "title": title,
            "first_name": first.split()[0], "last_name": last.strip(), "display_name": known_as,
            "position": position, "position_vi": position_vi,
            "subjects": ";".join(words),
            "keywords": ";".join(k for k in (extra, name if known_as != name else "") if k),
            "department": dept_en, "department_vi": dept_vi,
            "room_id": room, "homeroom_class": cls,
        })
    return rows


# ---------------------------------------------------------------- rooms
def floor_label(n: int) -> str:
    return f"Floor {n} (Tầng {n})"


def ordinal(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def directions(zone: str, floor: int, row: list[str], room: str) -> tuple[str, str]:
    """Directions from the nearest stair in the room's own corridor, naming the doors on each side."""
    i = row.index(room)
    stairs = [j for j, tok in enumerate(row) if tok.startswith("S")]
    j = min(stairs, key=lambda s: abs(s - i))
    stair = row[j][1:]
    between = row[min(i, j) + 1:max(i, j)]
    doors = sum(1 for tok in between if not tok.startswith(("S", "WC"))) + 1
    past_wc = "WC" in between
    side = [tok for tok in (row[i - 1] if i > 0 else None, row[i + 1] if i + 1 < len(row) else None)
            if tok and not tok.startswith(("S", "WC"))]
    label = f"Room {room}" if room not in NAMED else NAMED[room][0]
    label_vi = f"Phòng {room}" if room not in NAMED else NAMED[room][1]

    if floor == 1:
        en = [f"Go to Zone {zone} on the ground floor (Tầng 1) and find stair {stair}"]
        vi = [f"Đến Khu {zone}, Tầng 1, tìm cầu thang {stair}"]
    else:
        en = [f"Go to Zone {zone} and take stair {stair} up to floor {floor} (Tầng {floor})"]
        vi = [f"Đến Khu {zone} và đi cầu thang {stair} lên Tầng {floor}"]
    wc_en = ", past the toilets" if past_wc else ""
    wc_vi = ", qua nhà vệ sinh" if past_wc else ""
    en.append(f"{label} is the {ordinal(doors)} door from stair {stair} along this corridor{wc_en}")
    vi.append(f"{label_vi} là cửa thứ {doors} tính từ cầu thang {stair} dọc hành lang này{wc_vi}")
    if len(side) == 2:
        en.append(f"It is between {side[0]} and {side[1]}")
        vi.append(f"Phòng nằm giữa {side[0]} và {side[1]}")
    elif side:
        en.append(f"It is next to {side[0]}")
        vi.append(f"Phòng nằm cạnh {side[0]}")
    return ". ".join(en) + ".", ". ".join(vi) + "."


def room_row(room: str, zone: str, floor: int, row: list[str], x: int, y: int) -> dict:
    cls = next((c for c, (r, _) in CLASSES.items() if r == room), "")
    if room in NAMED:
        name, name_vi, aliases = NAMED[room]
    elif cls:
        name, name_vi = f"Class {cls}", f"Lớp {cls}"
        aliases = f"{cls};{cls} classroom;class {cls};lop {cls};phong {cls}".lower()
    else:
        name, name_vi, aliases = f"Room {room}", f"Phòng {room}", ""
    compact = room.replace("-", "").lower()
    aliases = ";".join(a for a in (aliases, compact, f"room {compact}", f"phong {room.lower()}") if a)
    en, vi = directions(zone, floor, row, room)
    return {"room_id": room, "name": name, "name_vi": name_vi, "aliases": aliases, "building_id": zone,
            "floor": floor_label(floor), "map_x": x, "map_y": y, "directions": en, "directions_vi": vi}


# Map layout (800 x 500). The real campus is drawn at an angle on the signs; this is a
# simplified top view in the same arrangement. Zones A and B are shown as stacked floor bands.
MAP = {"width": 800, "height": 520, "hub": [465, 455]}   # gates left off until their positions are known
BUILDINGS = [
    # id, name, name_vi, x, y, w, h, entrance_x, entrance_y
    ("F", "Sports Fields", "Sân thể thao", 40, 20, 400, 110, 465, 95),
    ("S", "Canteen, Pool & Gym", "Căng-tin, Bể bơi & Phòng thể chất", 490, 20, 270, 150, 465, 120),
    ("B", "Zone B", "Khu B", 40, 160, 400, 260, 240, 420),
    ("A", "Zone A", "Khu A", 490, 200, 270, 220, 625, 420),
]
BAND_LABELS = []


def place_zone(rows_by_floor: dict, zone: str, x0: int, y0: int, w: int, h: int) -> list[dict]:
    """Pins in floor bands: floor 4 at the top, floor 1 at the bottom; two corridors per band."""
    out = []
    band = (h - 30) / 4
    for floor, (north, south) in rows_by_floor.items():
        top = y0 + 30 + (4 - floor) * band
        BAND_LABELS.append([x0 + 8, int(top + band / 2 + 4), f"T{floor}"])
        for k, row in enumerate((north, south)):
            y = int(top + band * (0.32 if k == 0 else 0.72))
            span = w - 60
            for n, tok in enumerate(row):
                if tok.startswith("S"):
                    continue
                x = int(x0 + 40 + span * (n + 0.5) / len(row))
                if tok == "WC":
                    out.append(wc_row(zone, floor, row, x, y))
                else:
                    out.append(room_row(tok, zone, floor, row, x, y))
    return out


def wc_row(zone: str, floor: int, row: list[str], x: int, y: int) -> dict:
    stair = next(tok for tok in row if tok.startswith("S"))[1:]
    where_en = "on the ground floor (Tầng 1)" if floor == 1 else f"on floor {floor} (Tầng {floor})"
    where_vi = "ở Tầng 1" if floor == 1 else f"ở Tầng {floor}"
    up_en = "" if floor == 1 else f"Take stair {stair} up to floor {floor}. "
    up_vi = "" if floor == 1 else f"Đi cầu thang {stair} lên Tầng {floor}. "
    return {
        "room_id": f"WC-{zone}{floor}", "name": f"Toilets – Zone {zone}, floor {floor}",
        "name_vi": f"Nhà vệ sinh – Khu {zone}, Tầng {floor}",
        "aliases": "toilet;toilets;wc;bathroom;restroom;washroom;nha ve sinh;ve sinh;nhà vệ sinh",
        "building_id": zone, "floor": floor_label(floor), "map_x": x, "map_y": y,
        "directions": f"{up_en}The toilets in Zone {zone} {where_en} are near stair {stair}.",
        "directions_vi": f"{up_vi}Nhà vệ sinh Khu {zone} {where_vi} ở gần cầu thang {stair}.",
    }


def outdoor_rooms() -> list[dict]:
    def r(rid, name, name_vi, aliases, b, floor, x, y, en, vi):
        return {"room_id": rid, "name": name, "name_vi": name_vi, "aliases": aliases, "building_id": b,
                "floor": floor, "map_x": x, "map_y": y, "directions": en, "directions_vi": vi}
    return [
        r("CANTEEN", "Canteen", "Căng-tin", "canteen;cafeteria;lunch room;dining room;can tin;cang tin;nha an",
          "S", floor_label(1), 560, 110,
          "The canteen is on the ground floor (Tầng 1), next to the swimming pool. It is beside the football pitch, across from Zone B's stair 4.",
          "Căng-tin ở Tầng 1, cạnh bể bơi. Căng-tin nằm cạnh sân bóng, đối diện cầu thang 4 của Khu B."),
        r("POOL", "Swimming Pool", "Bể bơi", "pool;swimming pool;swimming;be boi;ho boi;boi",
          "S", floor_label(1), 690, 110,
          "The swimming pool is on the ground floor (Tầng 1), next to the canteen. Follow the pool rules in the handbook.",
          "Bể bơi ở Tầng 1, cạnh căng-tin. Hãy tuân thủ nội quy bể bơi trong Sổ tay."),
        r("GYM", "Gym", "Phòng thể chất",
          "gym;gymnasium;sports hall;indoor sports;pe hall;phong the chat;nha the chat;nha thi dau",
          "S", "Floors 2–3 (Tầng 2–3)", 625, 55,
          "The gym is above the canteen, on floors 2–3 (Tầng 2–3). From Zone B, take stair 4 to floor 2 and walk past rooms 2-03 and 2-04 into the gym. There are also outside stairs beside the gym.",
          "Phòng thể chất ở trên căng-tin, Tầng 2–3. Từ Khu B, đi cầu thang 4 lên Tầng 2 rồi đi qua phòng 2-03 và 2-04 để vào phòng thể chất. Bên cạnh phòng thể chất còn có cầu thang ngoài trời."),
        r("PITCH", "Football Pitch", "Sân bóng đá", "football pitch;football field;soccer field;pitch;san bong;san bong da",
          "F", "Outdoor (Ngoài trời)", 300, 75,
          "The football pitch is behind Zone B, between the sports court and the canteen. Walk past Zone B's stair 4 to reach it.",
          "Sân bóng đá ở phía sau Khu B, giữa sân thể thao và căng-tin. Đi qua cầu thang 4 của Khu B để tới sân."),
        r("COURT", "Sports Court", "Sân thể thao", "sports court;court;basketball court;tennis court;san the thao",
          "F", "Outdoor (Ngoài trời)", 100, 75,
          "The sports court is at the far end of Zone B, next to the football pitch.",
          "Sân thể thao ở cuối Khu B, cạnh sân bóng đá."),
    ]


# ---------------------------------------------------------------- fictional demo data
# Alex, Khanh and Chloe are fictional. Their homeroom teachers are the real ones from the
# door signs; subject teachers are picked from real teachers of that subject.
DEMO = [("S001", "Alex", "Carter", "6A1"), ("S002", "Khanh", "Ngo", "7A1"), ("S003", "Chloe", "Reed", "8A1")]
DEMO_TEACHER = "Trần Thị Kim Oanh"   # the 'teacher' login: teaches 6A1 and 8A1, not 7A1 (privacy demo)
LESSONS = {   # class -> [(subject, teacher full name)]
    "6A1": [("Literature", "Đỗ Ngọc Anh"), ("Maths", "Nguyễn Thị Thu Hà B"), ("English", "Trần Ngọc Linh"),
            ("Physics", "Nguyễn Thành Trung"), ("History", "Trần Thị Kim Oanh"), ("Geography", "Nguyễn Thị Huyền"),
            ("ICT", "Lê Khánh Linh"), ("Music", "Lê Nguyễn Trúc Vy"), ("PE", "Đào Nam Hải"),
            ("Life Skills", "Đặng Quỳnh Trang")],
    "7A1": [("Literature", "Nguyễn Diệu Hoa"), ("Maths", "Vũ Thị Hương Quỳnh"), ("English", "Vũ Ngọc Khanh"),
            ("Biology", "Nguyễn Thị Len"), ("History", "Nguyễn Thị Thanh Hiếu"), ("Geography", "Nguyễn Văn Vinh"),
            ("ICT", "Trần Quốc Thư"), ("Arts", "Phạm Thị Thúy Hằng"), ("PE", "Đào Nam Hải"),
            ("Life Skills", "Ngô Phương Linh")],
    "8A1": [("Literature", "Bùi Thị Thùy"), ("Maths", "Nguyễn Thị Thu Hà A"), ("English", "Trần Ngọc Linh"),
            ("Chemistry", "Bùi Xuân Dũng"), ("History", "Trần Thị Kim Oanh"), ("Biology", "Hà Thu Ly"),
            ("ICT", "Alex Kingsley"), ("Music", "Trịnh Mạnh Khuê"), ("PE", "Đào Nam Hải"),
            ("Physics", "Nguyễn Thị Thúy")],
}
CLUBS = [   # club_id, name, name_vi, leader, room, day, start, end
    ("C01", "Coding Club", "Câu lạc bộ Lập trình", "Lê Khánh Linh", "B4-07", "Tuesday", "16:15", "17:15"),
    ("C02", "Robotics Club", "Câu lạc bộ Robot", "Nguyễn Thành Trung", "2-02", "Thursday", "16:15", "17:15"),
    ("C03", "School Choir", "Dàn hợp xướng", "Trịnh Mạnh Khuê", "2-02", "Wednesday", "16:15", "17:15"),
    ("C04", "Basketball", "Bóng rổ", "Đào Nam Hải", "GYM", "Monday", "16:15", "17:30"),
    ("C05", "Art Club", "Câu lạc bộ Mỹ thuật", "Nguyễn Thị Tuệ Thư", "2-02", "Friday", "16:15", "17:15"),
    ("C06", "Debate Club", "Câu lạc bộ Tranh biện", "Trần Minh Tâm", "B3-06", "Thursday", "12:35", "13:15"),
]
STUDENT_CLUBS = {"S001": "C01;C04", "S002": "C02;C03", "S003": "C05;C06"}
EVENT_ROOMS = {   # sample events -> real places
    "G001": "GYM", "L001": "2-02", "A001": "1-01", "C102": "2-02", "C101": "2-02", "B201": "B4-07",
}


def write(name: str, rows: list[dict]) -> None:
    with open(DATA / f"{name}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    teachers = build_teachers()
    by_name = {t["display_name"]: t["teacher_id"] for t in teachers}

    rooms = place_zone(B_ROWS, "B", 40, 160, 400, 260) + place_zone(A_ROWS, "A", 490, 200, 270, 220)
    rooms += outdoor_rooms()
    room_ids = {r["room_id"] for r in rooms}
    for t in teachers:
        assert not t["room_id"] or t["room_id"] in room_ids, t

    buildings = [{"building_id": b, "name": n, "name_vi": nv, "x": x, "y": y, "w": w, "h": h,
                  "entrance_x": ex, "entrance_y": ey} for b, n, nv, x, y, w, h, ex, ey in BUILDINGS]

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    periods = [f"P{i}" for i in range(1, 9)]
    timetable = []
    for cls, lessons in LESSONS.items():
        home = CLASSES[cls][0]
        for di, day in enumerate(days):
            for pi, pid in enumerate(periods):
                subject, teacher = lessons[(di * 3 + pi) % len(lessons)]
                timetable.append({"class_group": cls, "day": day, "period_id": pid, "subject": subject,
                                  "teacher_id": by_name[teacher], "room_id": SUBJECT_ROOM.get(subject, home)})
    students = [{"student_id": sid, "first_name": f, "last_name": l, "year": cls[:-2], "class_group": cls,
                 "homeroom_teacher_id": by_name[CLASSES[cls][1]], "club_ids": STUDENT_CLUBS[sid]}
                for sid, f, l, cls in DEMO]
    clubs = [{"club_id": c, "name": n, "name_vi": nv, "teacher_id": by_name[t], "room_id": r,
              "day": d, "start": s, "end": e} for c, n, nv, t, r, d, s, e in CLUBS]

    demo = by_name[DEMO_TEACHER]
    teaches = {cls for cls, ls in LESSONS.items() if any(t == DEMO_TEACHER for _, t in ls)}
    assert teaches == {"6A1", "8A1"}, teaches

    with open(DATA / "events.csv", encoding="utf-8") as f:
        events = list(csv.DictReader(f))
    for e in events:
        e["room_id"] = EVENT_ROOMS.get(e["room_id"], e["room_id"]) if e["room_id"] else ""
        assert not e["room_id"] or e["room_id"] in room_ids, e

    with open(DATA / "users.csv", encoding="utf-8") as f:
        users = list(csv.DictReader(f))
    for u in users:
        if u["role"] == "teacher":
            u["linked_id"] = demo

    school = json.loads((DATA / "school.json").read_text(encoding="utf-8"))
    school["map"] = dict(MAP, labels=BAND_LABELS)

    for name, rows in [("buildings", buildings), ("rooms", rooms), ("teachers", teachers),
                       ("timetable", timetable), ("students", students), ("clubs", clubs),
                       ("events", events), ("users", users)]:
        write(name, rows)
    (DATA / "school.json").write_text(json.dumps(school, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(buildings)} buildings, {len(rooms)} rooms, {len(teachers)} teachers, "
          f"{len(timetable)} lessons; 'teacher' login -> {DEMO_TEACHER} ({demo})")


if __name__ == "__main__":
    main()

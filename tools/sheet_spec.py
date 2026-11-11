"""The one place that defines the spreadsheet format.

Both `make_template.py` (builds the blank template) and `import_sheet.py`
(reads the team's filled-in sheet) use this, so they always agree.

Column types:
  id     short code, made UPPERCASE with spaces removed (B201, T05)
  text   free text
  list   several values in one cell, separated by ';'
  time   24-hour HH:MM
  date   YYYY-MM-DD
  title  Mr / Ms / Mrs / Dr / Thầy / Cô ...
  day    Monday ... Friday
  kind   class / break / end
"""

from dataclasses import dataclass, field


@dataclass
class Col:
    name: str
    type: str = "text"
    required: bool = False
    help: str = ""
    example: str = ""
    ref: str = ""            # "Rooms" = value must exist in that tab's id column
    synonyms: tuple = ()     # other header names the team might have used


@dataclass
class Tab:
    name: str
    file: str                # CSV file name in /data (without .csv)
    columns: list[Col]
    id_col: str
    auto_id: str = ""        # prefix for generated IDs when blank (e.g. "POL")
    required_tab: bool = True
    help: str = ""
    synonyms: tuple = ()
    extra_out: list[str] = field(default_factory=list)   # columns the importer adds (map positions)


TABS: list[Tab] = [
    Tab("Buildings", "buildings", id_col="building_id", synonyms=("building", "toa nha", "blocks"),
        help="One row per building. Map positions are added automatically.",
        extra_out=["x", "y", "w", "h", "entrance_x", "entrance_y"],
        columns=[
            Col("building_id", "id", True, "Short code, e.g. A, B, SCI", "B", synonyms=("id", "code", "building", "building_code")),
            Col("name", "text", True, "Building name in English", "Science & Technology Building", synonyms=("building_name", "name_en")),
            Col("name_vi", "text", False, "Building name in Vietnamese", "Tòa Khoa học & Công nghệ"),
        ]),
    Tab("Rooms", "rooms", id_col="room_id", synonyms=("room", "phong", "locations", "places"),
        help="One row per room or place (office, library, canteen...).",
        extra_out=["map_x", "map_y"],
        columns=[
            Col("room_id", "id", True, "Room number as on the door, e.g. B201", "B201", synonyms=("id", "room", "room_number", "room_no", "number", "code")),
            Col("name", "text", True, "Room name in English", "ICT Room (Computer Lab)", synonyms=("room_name", "name_en")),
            Col("name_vi", "text", False, "Room name in Vietnamese", "Phòng Tin học"),
            Col("aliases", "list", True, "Other names students use, separated by ;  (both languages)", "computer lab;IT room;phòng máy", synonyms=("alias", "other_names", "also_called", "nicknames")),
            Col("building_id", "id", True, "Building code from the Buildings tab", "B", ref="Buildings", synonyms=("building", "building_code", "block")),
            Col("floor", "text", True, "Floor, e.g. Ground, Level 1", "Level 1", synonyms=("level", "tang")),
            Col("directions", "text", True, "Directions from the building entrance. One step per sentence.", "Take the stairs to Level 1. The ICT Room is the first door on the right.", synonyms=("direction", "how_to_get_there", "directions_en")),
            Col("directions_vi", "text", False, "Directions in Vietnamese", "Đi cầu thang lên Tầng 1. Phòng Tin học là cửa đầu tiên bên phải."),
        ]),
    Tab("Teachers", "teachers", id_col="teacher_id", synonyms=("teacher", "staff", "giao vien", "directory", "staff directory"),
        help="One row per teacher or staff member. No phone numbers or personal emails.",
        columns=[
            Col("teacher_id", "id", True, "Short code, e.g. T01, T02 ...", "T01", synonyms=("id", "staff_id", "code")),
            Col("title", "title", False, "Mr, Ms, Mrs, Dr, Thầy, Cô ... (leave blank if unsure)", "Ms", synonyms=("salutation", "prefix")),
            Col("first_name", "text", True, "Given name (the name students use with Thầy/Cô)", "Sarah", synonyms=("first", "given_name", "ten")),
            Col("last_name", "text", True, "Family name", "Nguyen", synonyms=("last", "surname", "family_name", "ho")),
            Col("position", "text", True, "Job title in English", "Head of English", synonyms=("role", "job", "job_title", "position_en")),
            Col("position_vi", "text", False, "Job title in Vietnamese", "Trưởng bộ môn Tiếng Anh"),
            Col("subjects", "list", True, "Subjects taught, separated by ;", "English;Literature", synonyms=("subject", "teaches", "mon")),
            Col("department", "text", True, "Department in English", "English", synonyms=("dept", "faculty", "department_en")),
            Col("department_vi", "text", False, "Department in Vietnamese", "Tiếng Anh"),
            Col("room_id", "id", False, "Their main room, from the Rooms tab", "A101", ref="Rooms", synonyms=("room", "room_number", "office")),
            Col("display_name", "text", False, "Name as written at school, e.g. on the door sign", "Đỗ Ngọc Anh", synonyms=("name_on_sign", "ho_va_ten")),
            Col("keywords", "list", False, "Other words people use for this job, separated by ;", "nurse;y tế", synonyms=("tags", "search_words")),
            Col("homeroom_class", "text", False, "Class they are homeroom teacher of (chủ nhiệm), e.g. 6A1", "6A1", synonyms=("homeroom", "chu_nhiem", "gvcn", "form_class")),
        ]),
    Tab("Policies", "policies", id_col="policy_id", auto_id="POL", synonyms=("policy", "rules", "quy dinh"),
        help="Approved school policies only. Keep summaries short and accurate.",
        columns=[
            Col("policy_id", "id", False, "Leave blank to number automatically", "", synonyms=("id", "code")),
            Col("title", "text", True, "Policy title in English", "Mobile Phone Policy", synonyms=("policy", "name", "title_en")),
            Col("title_vi", "text", False, "Policy title in Vietnamese", "Quy định về điện thoại"),
            Col("category", "text", True, "e.g. Student Conduct, Attendance, Technology", "Student Conduct", synonyms=("type", "group")),
            Col("keywords", "list", True, "Words people might search for, separated by ;", "phone;mobile;điện thoại", synonyms=("keyword", "tags", "search_words")),
            Col("summary", "text", True, "Approved summary in English", "Phones must be switched off and kept in lockers from 8:00 to 14:20.", synonyms=("details", "description", "content", "summary_en")),
            Col("summary_vi", "text", False, "Approved summary in Vietnamese", "Điện thoại phải tắt và để trong tủ khóa từ 8:00 đến 14:20."),
            Col("source", "text", False, "Where this comes from (shown under the answer)", "Sổ tay học đường 2025–2026, mục D.6", synonyms=("reference", "section", "nguon")),
        ]),
    Tab("FAQs", "faqs", id_col="faq_id", auto_id="F", synonyms=("faq", "procedures", "questions", "procedures faqs", "thu tuc"),
        help="Common questions and approved answers (late arrival, lost property, ICT support...).",
        columns=[
            Col("faq_id", "id", False, "Leave blank to number automatically", "", synonyms=("id", "code")),
            Col("question", "text", True, "Question in English", "What do I do if I arrive late?", synonyms=("q", "question_en")),
            Col("question_vi", "text", False, "Question in Vietnamese", "Em phải làm gì nếu đến muộn?"),
            Col("category", "text", True, "e.g. Attendance, Facilities, Technology", "Attendance", synonyms=("type", "group")),
            Col("keywords", "list", True, "Words people might search for, separated by ;", "late;missed bus;đi muộn", synonyms=("keyword", "tags", "search_words")),
            Col("answer", "text", True, "Approved answer in English", "Go straight to Reception, sign in and collect a late slip.", synonyms=("a", "answer_en", "procedure")),
            Col("answer_vi", "text", False, "Answer in Vietnamese", "Đến thẳng Lễ tân, ký tên và nhận phiếu đi muộn."),
            Col("source", "text", False, "Where this comes from (shown under the answer)", "Sổ tay học đường 2025–2026, mục A.4.3", synonyms=("reference", "section", "nguon")),
        ]),
    Tab("Schedule", "schedule", id_col="period_id", synonyms=("bell schedule", "bell times", "periods", "timetable", "gio hoc"),
        help="One row per part of the school day, in time order. Include breaks and the end of the day.",
        columns=[
            Col("period_id", "id", True, "Short code: P1, P2 ... (breaks: R, L; end of day: END)", "P1", synonyms=("id", "code", "period")),
            Col("name", "text", True, "Name in English", "Period 1", synonyms=("period_name", "name_en")),
            Col("name_vi", "text", False, "Name in Vietnamese", "Tiết 1"),
            Col("aliases", "list", False, "Other names, separated by ;", "first period;tiết 1", synonyms=("alias", "other_names")),
            Col("start", "time", True, "Start time, 24-hour HH:MM", "08:15", synonyms=("start_time", "from", "begins")),
            Col("end", "time", True, "End time, 24-hour HH:MM (for END, same as start)", "09:05", synonyms=("end_time", "to", "finish", "finishes")),
            Col("kind", "kind", True, "class, break or end", "class", synonyms=("type", "category")),
        ]),
    Tab("Events", "events", id_col="event_id", auto_id="E", synonyms=("event", "calendar", "su kien"),
        help="School calendar events.",
        columns=[
            Col("event_id", "id", False, "Leave blank to number automatically", "", synonyms=("id", "code")),
            Col("name", "text", True, "Event name in English", "Sports Day", synonyms=("event", "title", "event_name", "name_en")),
            Col("name_vi", "text", False, "Event name in Vietnamese", "Ngày hội Thể thao"),
            Col("aliases", "list", False, "Other names, separated by ;", "athletics carnival;thể thao", synonyms=("alias", "other_names", "keywords")),
            Col("date", "date", True, "First day, YYYY-MM-DD (or a real date cell)", "2027-02-12", synonyms=("day", "event_date", "start_date")),
            Col("end_date", "date", False, "Last day, for events longer than one day", "", synonyms=("to_date", "until", "last_day")),
            Col("start", "time", False, "Start time, 24-hour HH:MM (blank = all day)", "08:30", synonyms=("start_time", "from", "time")),
            Col("end", "time", False, "End time, 24-hour HH:MM (blank = all day)", "14:00", synonyms=("end_time", "to", "finish")),
            Col("category", "text", False, "event, exam, holiday, day_off, parents or project", "event", synonyms=("type", "kind")),
            Col("room_id", "id", False, "Where, from the Rooms tab (optional)", "G001", ref="Rooms", synonyms=("room", "location", "venue", "where")),
            Col("description", "text", False, "Short description in English", "Whole-school athletics competition.", synonyms=("details", "description_en", "notes")),
            Col("description_vi", "text", False, "Description in Vietnamese", "Thi đấu điền kinh toàn trường."),
        ]),
    Tab("Clubs", "clubs", id_col="club_id", auto_id="C", required_tab=False, synonyms=("club", "cau lac bo", "activities"),
        help="Optional. If left empty, fictional clubs are created for the demo student profiles.",
        columns=[
            Col("club_id", "id", False, "Leave blank to number automatically", "", synonyms=("id", "code")),
            Col("name", "text", True, "Club name in English", "Coding Club", synonyms=("club", "club_name", "name_en")),
            Col("name_vi", "text", False, "Club name in Vietnamese", "Câu lạc bộ Lập trình"),
            Col("teacher_id", "id", True, "Teacher in charge, from the Teachers tab", "T05", ref="Teachers", synonyms=("teacher", "leader", "staff")),
            Col("room_id", "id", True, "Room, from the Rooms tab", "B201", ref="Rooms", synonyms=("room", "location", "venue")),
            Col("day", "day", True, "Monday ... Friday", "Tuesday", synonyms=("weekday",)),
            Col("start", "time", True, "Start time, 24-hour HH:MM", "14:30", synonyms=("start_time", "from")),
            Col("end", "time", True, "End time, 24-hour HH:MM", "15:30", synonyms=("end_time", "to", "finish")),
        ]),
]

TAB_BY_NAME = {t.name: t for t in TABS}

# Optional "School" tab: two columns, field | value.
SCHOOL_FIELDS = [
    ("name", "School name in English", "Lakeside Academy"),
    ("name_vi", "School name in Vietnamese", "Trường Lakeside Academy"),
    ("timezone", "Time zone (leave as is for Vietnam)", "Asia/Ho_Chi_Minh"),
]

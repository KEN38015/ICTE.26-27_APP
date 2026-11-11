"""Build data/events.csv from SenTia's secondary-school calendar for 2026–2027.

Source: "LỊCH NĂM HỌC TRUNG HỌC 2026 - 2027" (Oxford International Curriculum), shared by the team.
The school marks it as provisional: project dates and themes are set by each subject
department and year group, and changes are announced to parents.

The calendar gives no start/end times, so every event is all-day (start/end left blank).
Learning projects and IGCSE/Cambridge exams are listed for a whole month with no exact days;
they are stored as running for that month, and their description says so.

Run:  .venv/bin/python -m tools.sentia_calendar
"""

import calendar
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# The calendar's legend (Ghi chú)
CATEGORY_WORDS = {
    "event": "school event;su kien",
    "day_off": "no school;day off;students off;hoc sinh nghi;hs nghi;nghi hoc",
    "parents": "parent meeting;parents meeting;parent teacher;hop phu huynh;hop ph;hop phhs",
    "exam": "exam;exams;test;tests;kiem tra;thi;ky thi",
    "project": "project;learning project;du an;du an hoc tap",
    "holiday": "holiday;holidays;public holiday;day off;no school;school closed;nghi le;ngay nghi;truong nghi",
}

# (date, end date or "", category, name, name_vi, extra aliases, description, description_vi)
EVENTS = [
    ("2026-07-25", "", "parents", "Start-of-Year Parent Meeting", "Họp phụ huynh đầu năm",
     "start of year parent meeting;first parent meeting", "", ""),
    ("2026-07-29", "", "event", "Orientation for New Students", "Định hướng học sinh đầu cấp và học sinh mới",
     "orientation;new students;new student orientation;dinh huong", "For students starting a new school level and students new to SenTia.",
     "Dành cho học sinh đầu cấp và học sinh mới."),
    ("2026-08-04", "", "event", "Welcome Day", "Ngày chào đón",
     "welcome day;first day;first day of school;start of school year;ngay chao don;ngay dau tien", "", ""),
    ("2026-08-31", "", "day_off", "Whole-School Staff Training (no school for students)", "Tập huấn toàn trường (học sinh nghỉ)",
     "staff training;teacher training;tap huan", "", ""),
    ("2026-09-01", "2026-09-02", "holiday", "National Day Holiday", "Nghỉ Quốc khánh",
     "national day;independence day;quoc khanh;2/9", "", ""),
    ("2026-09-01", "2026-09-30", "project", "English Science Project", "Dự án môn Khoa học tiếng Anh",
     "science project;english science", "Runs during September; dates are set by the subject department.",
     "Diễn ra trong tháng 9; thời gian cụ thể do bộ môn sắp xếp."),
    ("2026-09-25", "", "event", "Mid-Autumn Festival", "Lễ hội Trung thu",
     "mid autumn festival;moon festival;trung thu;le hoi trung thu", "", ""),
    ("2026-10-05", "2026-10-13", "exam", "Term 1 Mid-term Exams", "Kiểm tra giữa kỳ I",
     "mid term;midterm;midterms;mid term tests;mid term exams;kiem tra giua ky;giua ky 1;thi giua ky", "", ""),
    ("2026-10-09", "", "event", "World Mental Health Day", "Ngày sức khỏe tâm thần thế giới",
     "mental health day;mental health;suc khoe tam than", "", ""),
    ("2026-10-21", "2026-10-22", "parents", "Parent-Teacher Meetings (Term 1)", "Họp phụ huynh học sinh (Học kỳ I)",
     "parent teacher meetings;parent teacher interviews;parents evening", "", ""),
    ("2026-10-21", "2026-10-23", "day_off", "Term 1 Mid-term Break", "Học sinh nghỉ giữa kỳ I",
     "mid term break;midterm break;half term;nghi giua ky", "", ""),
    ("2026-10-26", "2026-10-30", "event", "Spirit Week", "Spirit Week", "spirit week;tuan le tinh than", "", ""),
    ("2026-10-29", "2026-10-30", "event", "Sports Day & Halloween Camping Night (Lower Secondary)",
     "Ngày Thể thao & Halloween Camping Night (THCS)",
     "sports day;halloween;camping night;camping;ngay the thao;thcs", "For lower secondary (grades 6–9).", "Dành cho khối THCS (lớp 6–9)."),
    ("2026-10-29", "2026-10-30", "event", "Halloween Field Trip (Upper Secondary)", "Dã ngoại Halloween (THPT)",
     "halloween trip;field trip;trip;excursion;da ngoai;thpt", "For upper secondary (grades 10–12).", "Dành cho khối THPT (lớp 10–12)."),
    ("2026-11-01", "2026-11-30", "project", "Interdisciplinary Social Sciences Project", "Dự án liên môn Khoa học xã hội",
     "social science project;social sciences;interdisciplinary project;lien mon", "Runs during November; dates are set by the subject department.",
     "Diễn ra trong tháng 11; thời gian cụ thể do bộ môn sắp xếp."),
    ("2026-11-01", "2026-11-30", "exam", "IGCSE Exams (November series)", "Kỳ thi IGCSE (đợt tháng 11)",
     "igcse;igcse exams;cambridge exams", "During November; check exact exam days with your teacher.",
     "Trong tháng 11; hỏi giáo viên để biết ngày thi cụ thể."),
    ("2026-11-20", "", "holiday", "Teachers' Day Holiday (school closed)", "Nghỉ Ngày Nhà giáo Việt Nam",
     "teachers day;teacher day;20/11;nha giao;ngay nha giao", "", ""),
    ("2026-11-24", "", "event", "Vietnamese Culture Day (provisional)", "Ngày Văn hóa Việt Nam (dự kiến)",
     "culture day;vietnamese culture;van hoa viet nam", "Date to be confirmed.", "Ngày dự kiến."),
    ("2026-11-28", "", "event", "\"Gió đầu mùa\" Event", "Sự kiện Gió đầu mùa",
     "gio dau mua;first winds", "", ""),
    ("2026-12-01", "2026-12-31", "project", "Natural Sciences Project", "Dự án Khoa học tự nhiên",
     "natural science project;science project;khoa hoc tu nhien", "Runs during December; dates are set by the subject department.",
     "Diễn ra trong tháng 12; thời gian cụ thể do bộ môn sắp xếp."),
    ("2026-12-07", "2026-12-15", "exam", "Term 1 End-of-term Exams", "Kiểm tra cuối học kỳ I",
     "end of term tests;end of term exams;final exams;finals;semester exams;kiem tra cuoi ky;cuoi ky 1;thi cuoi ky", "", ""),
    ("2026-12-22", "", "event", "Christmas Event", "Sự kiện Giáng sinh", "christmas;xmas;giang sinh;noel", "", ""),
    ("2026-12-23", "2026-12-31", "day_off", "Christmas & End-of-Term 1 Break", "Nghỉ Giáng sinh và cuối học kỳ I",
     "christmas holiday;christmas break;winter break;end of term break;nghi giang sinh", "", ""),
    ("2027-01-01", "", "holiday", "New Year's Day Holiday", "Nghỉ Tết Dương lịch",
     "new year;new years day;tet duong lich;1/1", "", ""),
    ("2027-01-29", "", "event", "Tết Celebration", "Sự kiện Tết", "tet event;tet celebration;su kien tet", "", ""),
    ("2027-02-01", "2027-02-12", "holiday", "Lunar New Year (Tết) Holiday", "Nghỉ Tết Nguyên Đán",
     "tet;lunar new year;tet holiday;tet nguyen dan;nghi tet", "", ""),
    ("2027-02-01", "2027-02-28", "project", "Natural Sciences Project", "Dự án Khoa học tự nhiên",
     "natural science project;science project;khoa hoc tu nhien", "Runs during February; dates are set by the subject department.",
     "Diễn ra trong tháng 2; thời gian cụ thể do bộ môn sắp xếp."),
    ("2027-02-01", "2027-02-28", "project", "International Curriculum Project Day", "Ngày dự án các môn chương trình Quốc tế",
     "international curriculum;project day;chuong trinh quoc te", "In February; the exact day will be announced.",
     "Trong tháng 2; ngày cụ thể sẽ được thông báo."),
    ("2027-03-08", "2027-03-16", "exam", "Term 2 Mid-term Exams", "Kiểm tra giữa kỳ II",
     "mid term;midterm;midterms;mid term tests;mid term exams;kiem tra giua ky;giua ky 2;thi giua ky", "", ""),
    ("2027-03-18", "2027-03-19", "event", "Lower Secondary Field Trip", "Dã ngoại THCS",
     "field trip;trip;excursion;da ngoai;thcs", "For lower secondary (grades 6–9).", "Dành cho khối THCS (lớp 6–9)."),
    ("2027-03-18", "2027-03-19", "event", "Sports Day & Camping Night (Upper Secondary)", "Ngày Thể thao & Camping Night (THPT)",
     "sports day;camping night;camping;ngay the thao;thpt", "For upper secondary (grades 10–12).", "Dành cho khối THPT (lớp 10–12)."),
    ("2027-03-25", "2027-03-26", "parents", "Parent-Teacher Meetings (Term 2)", "Họp phụ huynh học sinh (Học kỳ II)",
     "parent teacher meetings;parent teacher interviews;parents evening", "", ""),
    ("2027-03-25", "2027-03-26", "day_off", "Term 2 Mid-term Break", "Học sinh nghỉ giữa kỳ II",
     "mid term break;midterm break;half term;nghi giua ky", "", ""),
    ("2027-04-01", "2027-04-30", "project", "Interdisciplinary Social Sciences Project", "Dự án liên môn Khoa học xã hội",
     "social science project;social sciences;interdisciplinary project;lien mon", "Runs during April; dates are set by the subject department.",
     "Diễn ra trong tháng 4; thời gian cụ thể do bộ môn sắp xếp."),
    ("2027-04-10", "", "event", "\"April Story\" Event", "Câu chuyện tháng Tư", "april story;cau chuyen thang tu", "", ""),
    ("2027-04-16", "", "holiday", "Hùng Kings' Commemoration Day Holiday", "Nghỉ Giỗ Tổ Hùng Vương",
     "hung kings;hung vuong;gio to", "", ""),
    ("2027-04-30", "", "holiday", "Reunification Day Holiday", "Nghỉ ngày Chiến thắng",
     "reunification day;liberation day;30/4;chien thang;giai phong", "", ""),
    ("2027-05-03", "", "holiday", "Labour Day (substitute holiday)", "Nghỉ bù ngày Quốc tế Lao động",
     "labour day;labor day;may day;1/5;quoc te lao dong;nghi bu", "", ""),
    ("2027-05-01", "2027-05-31", "exam", "Cambridge International Certificate Exams", "Thi chứng chỉ quốc tế Cambridge",
     "cambridge;cambridge exams;certificate exams;chung chi quoc te", "During May; check exact exam days with your teacher.",
     "Trong tháng 5; hỏi giáo viên để biết ngày thi cụ thể."),
    ("2027-05-01", "2027-05-31", "exam", "IGCSE Exams (May series)", "Kỳ thi IGCSE (đợt tháng 5)",
     "igcse;igcse exams", "During May; check exact exam days with your teacher.",
     "Trong tháng 5; hỏi giáo viên để biết ngày thi cụ thể."),
    ("2027-05-10", "2027-05-18", "exam", "Term 2 End-of-term Exams", "Kiểm tra cuối học kỳ II",
     "end of term tests;end of term exams;final exams;finals;semester exams;kiem tra cuoi ky;cuoi ky 2;thi cuoi ky", "", ""),
    ("2027-05-26", "", "event", "Music Showcase", "Báo cáo Âm nhạc", "music showcase;music concert;concert;bao cao am nhac", "", ""),
    ("2027-05-27", "", "event", "Grade 12 Coming-of-Age Ceremony", "Lễ Trưởng thành K12",
     "coming of age;grade 12 ceremony;truong thanh;k12", "", ""),
    ("2027-05-28", "", "event", "Closing Ceremony & Grade 9 Graduation", "Lễ bế giảng & Lễ tốt nghiệp K9",
     "closing ceremony;last day of school;end of school year;school year end;end of the year;last day;graduation;be giang;tot nghiep;k9;ket thuc nam hoc", "", ""),
]


def main() -> None:
    rows = []
    for i, (start, end, cat, name, name_vi, aliases, desc, desc_vi) in enumerate(sorted(EVENTS, key=lambda e: e[0]), 1):
        if end:
            assert end >= start, name
        y, m = int(start[:4]), int(start[5:7])
        if end and start.endswith("-01") and end == f"{start[:8]}{calendar.monthrange(y, m)[1]:02d}":
            assert desc, f"{name}: month-long items must say so"
        rows.append({"event_id": f"E{i:02d}", "name": name, "name_vi": name_vi,
                     "aliases": f"{aliases};{CATEGORY_WORDS[cat]}", "date": start, "end_date": end,
                     "start": "", "end": "", "room_id": "", "category": cat,
                     "description": desc, "description_vi": desc_vi})
    with open(DATA / "events.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} events written")


if __name__ == "__main__":
    main()

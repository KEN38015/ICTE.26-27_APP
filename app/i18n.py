"""Interface text in English and Vietnamese.

`t(key, lang)` returns interface text. `tr(item, field, lang)` returns a data
field in the chosen language, using the `<field>_vi` CSV column when it
exists and falling back to English when it is empty.
"""

LANGS = ("en", "vi")

STRINGS: dict[str, dict[str, str]] = {
    # navigation & layout
    "home": {"en": "Home", "vi": "Trang chủ"},
    "policies": {"en": "Policies", "vi": "Quy định"},
    "directory": {"en": "Staff Directory", "vi": "Danh bạ giáo viên"},
    "map": {"en": "Campus Map", "vi": "Bản đồ trường"},
    "schedule": {"en": "Bell Schedule & Calendar", "vi": "Giờ học & Lịch sự kiện"},
    "faqs": {"en": "Procedures & FAQs", "vi": "Thủ tục & Câu hỏi thường gặp"},
    "profile": {"en": "Student Profile", "vi": "Hồ sơ học sinh"},
    "admin": {"en": "Admin", "vi": "Quản trị"},
    "login": {"en": "Log in", "vi": "Đăng nhập"},
    "logout": {"en": "Log out", "vi": "Đăng xuất"},
    "logged_in_as": {"en": "Logged in as", "vi": "Đăng nhập với"},
    "theme": {"en": "Toggle dark mode", "vi": "Bật/tắt chế độ tối"},
    "language": {"en": "Tiếng Việt", "vi": "English"},
    "sample_banner": {
        "en": "Demo prototype: school data is sample data and all student information is fictional.",
        "vi": "Bản mẫu: dữ liệu trường là dữ liệu mẫu và mọi thông tin học sinh đều là hư cấu.",
    },
    "tagline": {"en": "Smart School Assistant", "vi": "Trợ lý Trường học Thông minh"},
    "hero": {"en": "How can I help you today?", "vi": "Hôm nay mình có thể giúp gì cho bạn?"},
    "placeholder": {"en": "Ask a question, e.g. Where is the ICT room?", "vi": "Đặt câu hỏi, ví dụ: Phòng Tin học ở đâu?"},
    "ask": {"en": "Ask", "vi": "Hỏi"},
    "voice": {"en": "Speak your question", "vi": "Nói câu hỏi"},
    "listening": {"en": "Listening…", "vi": "Đang nghe…"},
    "voice_unsupported": {"en": "Voice input isn't supported in this browser.", "vi": "Trình duyệt này không hỗ trợ nhập giọng nói."},
    "read_aloud": {"en": "Read aloud", "vi": "Đọc to"},
    "quick_actions": {"en": "Quick questions", "vi": "Câu hỏi nhanh"},
    "browse": {"en": "Browse", "vi": "Xem theo mục"},
    "recent": {"en": "Your recent searches", "vi": "Tìm kiếm gần đây"},
    "clear": {"en": "Clear", "vi": "Xóa"},
    "searching": {"en": "Searching…", "vi": "Đang tìm…"},
    "you_asked": {"en": "You asked", "vi": "Bạn hỏi"},
    "showing_for": {"en": "Showing results for", "vi": "Hiển thị kết quả cho"},
    "did_you_mean": {"en": "Did you mean:", "vi": "Có phải bạn muốn tìm:"},
    "all": {"en": "All", "vi": "Tất cả"},
    "filter": {"en": "Filter", "vi": "Lọc"},
    "search_list": {"en": "Search this list", "vi": "Tìm trong danh sách"},
    "no_items": {"en": "No matching items.", "vi": "Không có mục phù hợp."},
    "privacy_note": {
        "en": "Privacy: student information is fictional and only visible to the student, their teachers and admins.",
        "vi": "Quyền riêng tư: thông tin học sinh là hư cấu và chỉ học sinh đó, giáo viên của em và quản trị viên được xem.",
    },
    "ai_note": {"en": "AI usage declaration", "vi": "Khai báo sử dụng AI"},
    # quick questions
    "q_ict": {"en": "Where is the ICT room?", "vi": "Phòng Tin học ở đâu?"},
    "q_late": {"en": "What do I do if I'm late?", "vi": "Em đến muộn thì làm gì?"},
    "q_now": {"en": "What period is it now?", "vi": "Bây giờ là tiết mấy?"},
    "q_events": {"en": "Upcoming events", "vi": "Sự kiện sắp tới"},
    "q_phone": {"en": "Phone policy", "vi": "Quy định điện thoại"},
    "q_science": {"en": "Who teaches science?", "vi": "Ai dạy môn Khoa học?"},
    "q_lost": {"en": "Lost property", "vi": "Đồ thất lạc"},
    "q_timetable": {"en": "My timetable", "vi": "Thời khóa biểu của em"},
    # card labels
    "room": {"en": "Room", "vi": "Phòng"},
    "building": {"en": "Building", "vi": "Tòa nhà"},
    "floor": {"en": "Floor", "vi": "Tầng"},
    "directions": {"en": "Directions", "vi": "Chỉ đường"},
    "show_map": {"en": "Show on map", "vi": "Xem trên bản đồ"},
    "subjects": {"en": "Subjects", "vi": "Môn dạy"},
    "department": {"en": "Department", "vi": "Bộ môn"},
    "time": {"en": "Time", "vi": "Thời gian"},
    "date": {"en": "Date", "vi": "Ngày"},
    "location": {"en": "Location", "vi": "Địa điểm"},
    "category": {"en": "Category", "vi": "Danh mục"},
    "staff_member": {"en": "Staff", "vi": "Giáo viên / Nhân viên"},
    "policy": {"en": "Policy", "vi": "Quy định"},
    "faq": {"en": "Procedure / FAQ", "vi": "Thủ tục / Hỏi đáp"},
    "period": {"en": "Bell schedule", "vi": "Giờ học"},
    "source": {"en": "Source", "vi": "Nguồn"},
    "period_col": {"en": "Period", "vi": "Tiết"},
    "event": {"en": "Event", "vi": "Sự kiện"},
    "cat_event": {"en": "School event", "vi": "Sự kiện"},
    "cat_day_off": {"en": "No school for students", "vi": "Học sinh nghỉ"},
    "cat_parents": {"en": "Parent meeting", "vi": "Họp phụ huynh"},
    "cat_exam": {"en": "Exams", "vi": "Kỳ thi / kiểm tra"},
    "cat_project": {"en": "Learning project", "vi": "Dự án học tập"},
    "cat_holiday": {"en": "Holiday – school closed", "vi": "Nghỉ lễ, trường đóng cửa"},
    "all_day": {"en": "All day (no set time)", "vi": "Cả ngày (chưa có giờ cụ thể)"},
    "club": {"en": "Club", "vi": "Câu lạc bộ"},
    "student": {"en": "Student profile", "vi": "Hồ sơ học sinh"},
    "year": {"en": "Grade", "vi": "Khối"},
    "class_group": {"en": "Class", "vi": "Lớp"},
    "homeroom": {"en": "Homeroom teacher", "vi": "Giáo viên chủ nhiệm"},
    "clubs": {"en": "Clubs", "vi": "Câu lạc bộ"},
    "my_teachers": {"en": "Teachers", "vi": "Giáo viên"},
    "timetable": {"en": "Weekly timetable", "vi": "Thời khóa biểu tuần"},
    "subject": {"en": "Subject", "vi": "Môn học"},
    "teacher": {"en": "Teacher", "vi": "Giáo viên"},
    "starts": {"en": "Starts", "vi": "Bắt đầu"},
    "ends": {"en": "Ends", "vi": "Kết thúc"},
    "rooms_in": {"en": "Rooms in", "vi": "Các phòng trong"},
    "map_help": {"en": "Tap a building or a room pin to see details and directions.", "vi": "Chạm vào tòa nhà hoặc phòng để xem chi tiết và chỉ đường."},
    "day_Monday": {"en": "Mon", "vi": "T2"},
    "day_Tuesday": {"en": "Tue", "vi": "T3"},
    "day_Wednesday": {"en": "Wed", "vi": "T4"},
    "day_Thursday": {"en": "Thu", "vi": "T5"},
    "day_Friday": {"en": "Fri", "vi": "T6"},
    "bell_times": {"en": "Bell times", "vi": "Giờ chuông"},
    "calendar": {"en": "School calendar", "vi": "Lịch sự kiện"},
    "upcoming": {"en": "Upcoming", "vi": "Sắp diễn ra"},
    "past": {"en": "Past", "vi": "Đã diễn ra"},
    "now_marker": {"en": "Now", "vi": "Hiện tại"},
    # answer messages
    "help": {
        "en": "I can help with school policies, finding teachers and staff, rooms and directions, bell times and events, procedures and FAQs, and your student profile (after logging in). Try one of the quick questions below.",
        "vi": "Mình có thể giúp về quy định của trường, tìm giáo viên và nhân viên, phòng học và chỉ đường, giờ học và sự kiện, thủ tục và câu hỏi thường gặp, và hồ sơ học sinh (sau khi đăng nhập). Hãy thử một câu hỏi nhanh bên dưới.",
    },
    "invalid_empty": {"en": "Please type a question first.", "vi": "Vui lòng nhập câu hỏi trước."},
    "invalid_too_long": {"en": "That question is too long. Please keep it under 200 characters.", "vi": "Câu hỏi quá dài. Vui lòng viết dưới 200 ký tự."},
    "invalid_no_words": {"en": "I couldn't read that. Please use words, e.g. \"Where is the library?\"", "vi": "Mình không đọc được. Vui lòng dùng chữ, ví dụ: \"Thư viện ở đâu?\""},
    "not_found": {
        "en": "Sorry, I couldn't find that in the school's information. I only answer from approved school data, so I won't guess. Try different words, or ask at Reception.",
        "vi": "Xin lỗi, mình không tìm thấy thông tin này trong dữ liệu của trường. Mình chỉ trả lời từ dữ liệu đã được duyệt nên sẽ không đoán. Hãy thử từ khác hoặc hỏi tại Lễ tân.",
    },
    "not_found_no_such_period": {"en": "There is no period with that number. The school day has Periods 1 to 6.", "vi": "Không có tiết học số đó. Một ngày học có Tiết 1 đến Tiết 6."},
    "not_found_no_events_month": {"en": "There are no school events listed for that month.", "vi": "Không có sự kiện nào trong tháng đó."},
    "not_found_no_events_today": {"en": "There are no school events listed for today.", "vi": "Hôm nay không có sự kiện nào."},
    "not_found_no_upcoming": {"en": "There are no upcoming events listed.", "vi": "Không có sự kiện sắp tới."},
    "not_found_profile_students_only": {"en": "Profiles are for student accounts. Ask about a student by name to view a profile you're allowed to see.", "vi": "Hồ sơ dành cho tài khoản học sinh. Hãy hỏi theo tên học sinh để xem hồ sơ bạn được phép xem."},
    "private_personal_details": {
        "en": "I can't share personal details such as phone numbers, addresses, passwords, grades or medical information. The school doesn't store these in this assistant.",
        "vi": "Mình không thể chia sẻ thông tin cá nhân như số điện thoại, địa chỉ, mật khẩu, điểm số hay thông tin y tế. Trợ lý này không lưu những thông tin đó.",
    },
    "private_student_list": {"en": "Student lists are private and only available to administrators.", "vi": "Danh sách học sinh là thông tin riêng tư, chỉ quản trị viên được xem."},
    "private_other_student": {"en": "That student's information is private. You can only view profiles you're allowed to see (your own, or students you teach).", "vi": "Thông tin của học sinh đó là riêng tư. Bạn chỉ xem được hồ sơ mình được phép (của chính mình, hoặc học sinh mình dạy)."},
    "login_required_student_info": {"en": "Student information is private. Please log in to view a profile you are allowed to see.", "vi": "Thông tin học sinh là riêng tư. Vui lòng đăng nhập để xem hồ sơ bạn được phép xem."},
    "login_required_own_profile": {"en": "Please log in with your student account to see your profile and timetable.", "vi": "Vui lòng đăng nhập bằng tài khoản học sinh để xem hồ sơ và thời khóa biểu."},
    "need_name": {"en": "Which student? Please include the student's name.", "vi": "Học sinh nào? Vui lòng ghi tên học sinh."},
    "note_teacher_location": {"en": "Here is where to find them:", "vi": "Đây là nơi bạn có thể tìm gặp:"},
    "note_current": {"en": "Right now it is:", "vi": "Bây giờ là:"},
    "note_next": {"en": "Next up:", "vi": "Tiếp theo là:"},
    "note_between": {"en": "Classes are changing over. Coming up next:", "vi": "Đang chuyển tiết. Tiếp theo là:"},
    "note_before": {"en": "School hasn't started yet. The day begins with:", "vi": "Chưa đến giờ học. Một ngày bắt đầu với:"},
    "note_after": {"en": "School has finished for today.", "vi": "Hôm nay đã tan học."},
    "note_last": {"en": "There are no more classes today.", "vi": "Hôm nay không còn tiết học nào nữa."},
    "note_weekend": {"en": "It's the weekend, so there are no classes today.", "vi": "Hôm nay là cuối tuần nên không có tiết học."},
    "note_all": {"en": "Here are today's bell times:", "vi": "Đây là giờ chuông trong ngày:"},
    "note_upcoming": {"en": "Upcoming school events:", "vi": "Các sự kiện sắp tới:"},
    "note_month": {"en": "Events that month:", "vi": "Sự kiện trong tháng:"},
    "note_today": {"en": "Events today:", "vi": "Sự kiện hôm nay:"},
    "note_student_list": {"en": "All students (admin view):", "vi": "Tất cả học sinh (chế độ quản trị):"},
    "lesson_current": {"en": "Your class right now", "vi": "Tiết học hiện tại của em"},
    "lesson_next": {"en": "Your next class", "vi": "Tiết học tiếp theo của em"},
    "lesson_between": {"en": "Changing over: your next class", "vi": "Đang chuyển tiết: tiết tiếp theo của em"},
    "lesson_none": {"en": "You don't have a class at this time.", "vi": "Em không có tiết học vào lúc này."},
    # login
    "username": {"en": "Username", "vi": "Tên đăng nhập"},
    "password": {"en": "Password", "vi": "Mật khẩu"},
    "login_failed": {"en": "Incorrect username or password.", "vi": "Sai tên đăng nhập hoặc mật khẩu."},
    "login_locked": {"en": "Too many attempts. Please wait a few minutes and try again.", "vi": "Thử quá nhiều lần. Vui lòng đợi vài phút rồi thử lại."},
    "login_intro": {"en": "Log in with a demo account to see a student profile or the admin dashboard.", "vi": "Đăng nhập bằng tài khoản mẫu để xem hồ sơ học sinh hoặc trang quản trị."},
    "role_student": {"en": "Student", "vi": "Học sinh"},
    "role_teacher": {"en": "Teacher", "vi": "Giáo viên"},
    "role_admin": {"en": "Admin", "vi": "Quản trị viên"},
    "forbidden": {"en": "You don't have permission to view this page.", "vi": "Bạn không có quyền xem trang này."},
    "my_students": {"en": "Students you can view", "vi": "Học sinh bạn được xem"},
    "not_found_page": {"en": "Page not found.", "vi": "Không tìm thấy trang."},
}


def t(key: str, lang: str = "en") -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry["en"]


def tr(item: dict, field: str, lang: str = "en") -> str:
    if lang == "vi":
        value = item.get(f"{field}_vi")
        if value:
            return value
    return item.get(field, "")

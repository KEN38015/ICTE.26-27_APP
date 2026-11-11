# Test cases and testing evidence

Every case below is an automated test in `tests/test_search.py` with the same ID. Run all tests with:

```bash
.venv/bin/python -m pytest -v
```

Time-based cases use a fixed moment: **Tuesday 10 November 2026, 10:30 (Period 3)**.

**Result (latest run): 134 passed, 0 failed** (54 sample-school cases, 35 SenTia handbook cases, and 45 extra web, login, role, data and importer checks).

These cases run on the fixed sample school in `tests/fixtures/sample_data/`. After importing your real school data, add cases with real questions about your school.

## Numbered cases

| ID | Category | Question | User | Expected result |
|---|---|---|---|---|
| TC01 | Policies | uniform policy | Guest | Uniform Policy |
| TC02 | Policies | Can I use my phone in class? | Guest | Mobile Phone Policy |
| TC03 | Policies (alt. wording) | rules about phones | Guest | Mobile Phone Policy |
| TC04 | Policies | is cheating with chatgpt allowed | Guest | Academic Integrity Policy |
| TC05 | Staff | Who teaches chemistry? | Guest | Mrs Linh Pham |
| TC06 | Staff | science teachers | Guest | Both science teachers |
| TC07 | Staff | Ms Nguyen | Guest | Ms Sarah Nguyen |
| TC08 | Staff | who is the principal | Guest | Dr Robert Hughes |
| TC09 | Staff | mr le | Guest | Mr Huy Le (short name with title) |
| TC10 | Navigation | Where is the ICT room? | Guest | B201 + directions + map |
| TC11 | Navigation (alt. wording) | where's the computer lab | Guest | B201 |
| TC12 | Navigation | how do i get to the library | Guest | Library L001 |
| TC13 | Navigation | Where is Mr Tran's room? | Guest | Mr Tran + room A102 directions |
| TC14 | Navigation | where is room b102 | Guest | B102 |
| TC15 | Schedule | What time does period 3 start? | Guest | Period 3, 10:15–11:05 |
| TC16 | Schedule | when is lunch | Guest | Lunch 11:55–12:40 |
| TC17 | Schedule | what period is it now | Guest | Period 3 (at 10:30) |
| TC18 | Calendar | when is the science fair | Guest | Science Fair, 20 Nov 2026 |
| TC19 | Calendar | upcoming events | Guest | Events from today onwards |
| TC20 | Calendar | events in december | Guest | December events |
| TC21 | Schedule | bell times | Guest | Full bell schedule |
| TC22 | FAQ | What do I do if I'm late? | Guest | Late arrival procedure |
| TC23 | FAQ (alt. wording) | I lost my water bottle | Guest | Lost property |
| TC24 | FAQ | forgot my password | Guest | Password reset procedure |
| TC25 | FAQ | I feel sick | Guest | Sick Bay procedure |
| TC26 | FAQ | how do I connect to wifi | Guest | Wi-Fi help |
| TC27 | Profile | my timetable | Student Alex | Alex's profile and timetable |
| TC28 | Profile | what class do I have now | Student Alex | Alex's current lesson |
| TC29 | Profile | my timetable | Guest | Asked to log in |
| TC30 | Vietnamese | Phòng Tin học ở đâu? | Guest | B201 (answer in Vietnamese) |
| TC31 | Vietnamese (no accents) | phong tin hoc o dau | Guest | B201 |
| TC32 | Vietnamese | quy định đồng phục | Guest | Uniform Policy |
| TC33 | Vietnamese | em bị ốm | Guest | Sick Bay procedure |
| TC34 | Spelling | unifrom | Guest | Uniform Policy ("Showing results for uniform") |
| TC35 | Spelling | wher is the libary | Guest | Library |
| TC36 | Invalid | (empty) | Guest | "Please type a question" |
| TC37 | Invalid | ??? | Guest | "Please use words" |
| TC38 | Invalid | 250 characters | Guest | "Too long" |
| TC39 | Unknown | what is the weather on mars | Guest | Not found (no guessing) |
| TC40 | Unknown | asdfghjkl | Guest | Not found |
| TC41 | Missing data | dog policy | Guest | Not found (no such policy) |
| TC42 | Invalid / security | `<script>alert(1)</script>` | Guest | Not found, shown escaped |
| TC43 | Missing data | what time does period 9 start | Guest | "There is no period with that number" |
| TC44 | Privacy | what is Alex's phone number | Guest | Refused (personal details) |
| TC45 | Privacy | where does chloe live | Student Alex | Refused (personal details) |
| TC46 | Privacy | show me Alex Carter's timetable | Guest | Asked to log in |
| TC47 | Privacy | show Khanh's timetable | Student Alex | Refused (another student) |
| TC48 | Privacy | list all students | Guest | Refused (admins only) |
| TC49 | Privacy | Ms Brooks email | Guest | Refused (personal details) |
| TC50 | Role access | chloe profile | Teacher (Ms Brooks) | Allowed (she teaches Chloe) |
| TC51 | Role access | khanh profile | Teacher (Ms Brooks) | Refused (doesn't teach Khanh) |
| TC52 | Role access | list all students | Admin | All students |
| TC53 | Privacy | What are Alex's grades? | Admin | Refused (never stored) |
| TC54 | Help | hi | Guest | Help message |

## SenTia handbook cases (`tests/test_sentia.py`, live data)

Real student questions answered from the SenTia School Handbook 2025–2026 (42 policies, 24 handbook FAQs). Each answer cites its handbook section.

| ID | Question | Expected answer |
|---|---|---|
| ST01 | What do I do if I'm late? | FAQ: arriving late (A.4.3, D.2) |
| ST02 | uniform policy | Uniform Policy (D.3) |
| ST03 | I forgot my uniform | Uniform Policy / forgot-uniform FAQ |
| ST04 | can I use my phone | Mobile Phone & Electronic Devices Policy (D.6, D.8) |
| ST05 | my phone was confiscated | Confiscation Policy / phone FAQ (D.8) |
| ST06 | can I bring snacks | Food Safety Policy (B.1) |
| ST07 | can I bring medicine | Health & Medicine Policy (B.3) |
| ST08 | I feel sick | FAQ: feeling sick at school (B.3) |
| ST09 | how do I take a day off | FAQ: taking a day off (A.4.2) |
| ST10 | how many days can I miss | FAQ: 45-day limit, 20% per subject (A.4.3–4) |
| ST11 | how many library books can I borrow | Library Rules: 2 books, 1 week (D.5.2) |
| ST12 | I lost my locker key | FAQ: 100,000 VND key (D.6) |
| ST13 | what time is breakfast | Canteen Rules / meal-times FAQ (7:15–7:40) |
| ST14 | can I leave early | Drop-off & Pick-up Times / early-leave FAQ (B.5) |
| ST15 | I'm being bullied | FAQ: being bullied (C.5) |
| ST16 | can I take photos at school | Privacy, Photos & Recording (C.4) |
| ST17 | when are the exams | FAQ: weeks 10, 19, 28, 38 (A.2) |
| ST18 | what happens if I cheat | FAQ: cheating consequences (D.9) |
| ST19 | what are civility points | Civility Points & Conduct Result (A.4.1) |
| ST20 | can I have a birthday party | Birthday Celebrations (B.2) |
| ST21 | what if I break something | FAQ: breaking things (C.3) |
| ST22 | can I bring my dog | Banned Behaviour & Items (C.1) |
| ST23 | what is the voice level in the library | Library Rules (D.5.2) |
| ST24 | which gate do I use | Entering & Leaving Campus (D.4) |
| ST25 | how do I contact the school | FAQ: office contact details |
| ST26 | Em đến muộn thì làm gì? | FAQ: arriving late (Vietnamese answer) |
| ST27 | quên đồng phục | Forgot-uniform FAQ / Uniform Policy |
| ST28 | bị tịch thu điện thoại | Confiscation Policy / phone FAQ |
| ST29 | em bị ốm | Feeling-sick FAQ / Health Policy |
| ST30 | mất chìa khóa tủ | Lockers policy / key FAQ |
| ST31 | bị bắt nạt | Bullying FAQ / Anti-Bullying Policy |
| ST32 | điểm văn minh | Civility Points (A.4.1) |
| ST33 | kỷ luật | Behaviour Levels & Consequences (E) |
| ST34 | thẻ tự ra về | Entering & Leaving Campus (D.4) |
| ST35 | hút thuốc | Banned Behaviour & Items (C.1) |

Also checked: every entry cites its source, every entry has English and Vietnamese, "when is recess" still works, and unknown questions are still "not found".

### SenTia bell schedule (`tests/test_sentia.py`, live data)

| ID | Question / time | Expected |
|---|---|---|
| SB01 | when does school start | Morning Meeting, 07:45 |
| SB02 | when does school end | End of Day, 16:05 |
| SB03 | when is lunch | Lunch Time, 12:15–13:20 |
| SB04 | when is recess | Break Time, 10:25–10:40 |
| SB05 | period 8 | 15:05–15:50 |
| SB06 | afternoon snack | 15:50–16:05 |
| SB07 | mấy giờ tan học | End of Day, 16:05 |
| SB08 | "what period is it now" at 07:30 / 07:50 / 10:30 / 15:55 / 16:30 | Before school / Morning Meeting / Break / Snack / School finished |
| SB09 | "what period is it now" at 08:47 and 15:00 (changeover gaps) | "Classes are changing over", next is Period 2 / Period 8 |
| SB10 | "next period" at 15:55 | "There are no more classes today." |
| SB11 | Alex asks "what class do I have now" at 08:47 | Their Period 2 lesson, marked as changing over |

Also checked: every demo student has all 8 periods every day, and no club clashes with lessons (clubs run after 16:05 or inside lunch).

### SenTia campus (`tests/test_campus.py`, live data)

Rooms come from the four "SENTIA SCHOOL MAP" floor signs and the door signs; staff from the team's teacherProfiles tab.

| ID | Question | Expected |
|---|---|---|
| CC01 | where is 6A1 | Class 6A1, room B2-06, with directions from stair 4 |
| CC02 | lớp 9A1 ở đâu | Class 9A1, room B3-05 (Vietnamese) |
| CC03 | where is room B4-07 | ICT Room (Secondary) |
| CC04 | b407 | ICT Room (room number typed without the dash) |
| CC05 | where is the ICT room | B4-07 |
| CC06 | phòng máy ở đâu | B4-07 |
| CC07 | thư viện ở đâu | Secondary & High School Library, B3-06 |
| CC08 | where is the toilet | Toilets (by zone and floor) |
| CC09 | căng tin ở đâu | Canteen |
| CC10 | where is the gym | Gym, floors 2–3 above the canteen |
| CC11 | where is the school office | School Office, 1-01 |
| CC12 | principal's office | Secondary School Board's Room, B2-03 |
| CC13 | where is A2-03 | Room A2-03 (purpose not on the sign, found by number) |
| CC14 | who is 6A1's homeroom teacher | Đỗ Ngọc Anh |
| CC15 | gvcn lớp 9A1 | Đặng Thị Hà |
| CC16 | homeroom teacher of 10A2 | Nguyễn Văn Vinh |
| CC17 | chủ nhiệm lớp 12A2 | Đoàn Thị Phương |
| CC18 | thầy Trung | Nguyễn Thành Trung |
| CC19 | where is cô Huyền | Nguyễn Thị Huyền, with directions to B2-04 |
| CC20 | Mr Kingsley | Alex Kingsley |
| CC21 | cô Tuệ Thư | Nguyễn Thị Tuệ Thư |
| CC22 | who is the principal | Ms Joey (full name Hồ Nghi Joey, also searchable) |
| CC23 | vice principal | Ms Nguyễn Thị Kim Khánh |
| CC24 | phó hiệu trưởng | Ms Nguyễn Thị Kim Khánh |
| CC25 | secondary principal | Mr Philip MacDonald-Milner |
| CC26 | who is the librarian | Ms Lan, room B3-06 (team confirmed) |
| CC27 | where is the nurse | The two school nurses |
| CC28 | school counsellor | Ms Đặng Quỳnh Trang, Ms Ngô Phương Linh |
| CC29 | bảo vệ | Ms Tuấn (school guard) |
| CC30 | thầy Alex | Mr Alex Kingsley (not the fictional student Alex) |
| CC31 | cô Khanh | Ms Vũ Ngọc Khanh, Ms Nguyễn Thị Kim Khánh |
| CC32 | Mr Austin | Mr James Austin |
| CC33 | who teaches IGCSE science | Mr R-Jay Bool |

Also checked: "giáo viên hóa học" doesn't return cô Diệu Hoa; "cô Hà" doesn't match by family name; "cô Thu Hà" doesn't return the Thư teachers; "where is the nurse" returns no room (none is on the maps); every class on a door sign has its room and homeroom teacher; directions name the stair and neighbouring doors; titles are the team's (Ms/Mr), and "cô"/"thầy" find Ms/Mr staff; every map pin sits inside its building; "where is Khanh" with no title still asks for a login (it could be the fictional student); the removed staff member is gone; "bao nhiêu lần" doesn't find Ms Lan; job search words aren't shown as subjects.

### SenTia 2026–2027 calendar (`tests/test_calendar.py`, live data, "today" = 10 Nov 2026)

| ID | Question | Expected first answer |
|---|---|---|
| SC01 | when is the next holiday | Teachers' Day Holiday, 20 Nov (not September's, which is over) |
| SC02 | khi nào nghỉ | Teachers' Day Holiday |
| SC03 | when is tet | Lunar New Year (Tết) Holiday, 1–12 Feb 2027 |
| SC04 | nghỉ tết khi nào | Lunar New Year (Tết) Holiday |
| SC05 | when are the end of term tests | Term 1 End-of-term Exams, 7–15 Dec |
| SC06 | kiểm tra cuối kỳ | Term 1 End-of-term Exams |
| SC07 | when is the midterm | Term 2 Mid-term Exams (term 1's is over) |
| SC08 | when is the mid-term break | Term 2 Mid-term Break |
| SC09 | when is teachers day | Teachers' Day Holiday |
| SC10 | christmas | Christmas Event, 22 Dec |
| SC11 | when is the field trip | Lower Secondary Field Trip, 18–19 Mar (October's is over) |
| SC12 | when does school year end | Closing Ceremony & Grade 9 Graduation, 28 May 2027 |
| SC13 | igcse | IGCSE Exams (November series) |
| SC14 | graduation | Closing Ceremony & Grade 9 Graduation |

Also checked: "upcoming events" and "what's happening today" include events that started earlier but are still running (the November project and IGCSE series); a month question includes multi-day events; "when is break time" still means the bell period; the 44 entries, Tết dates and categories match the school's calendar; no times are invented (the calendar has none).

## Extra automated checks (`tests/test_web.py`, `tests/test_data.py`, `tests/test_import.py`)

- All pages load, unknown pages return 404, answers work with and without JavaScript.
- User input is HTML-escaped (no script injection).
- Vietnamese questions get Vietnamese answers; the language switch works.
- Redirects to other websites are blocked.
- Login works and logout clears the session. Wrong passwords are rejected, and five failures lock the account.
- Passwords are not stored in plain text.
- A student can't open another student's profile, even by editing the URL (`/profile?student=S002`).
- A teacher can only open profiles of students they teach (403 otherwise).
- Students can't open or post to the admin dashboard.
- An FAQ added by an admin is immediately searchable. Invalid events are rejected.
- The search log hides privacy-blocked questions.
- Data quality: required fields are present, links between files are valid, every class has a full week, and students have no sensitive fields. The live `/data` folder also loads.
- Spreadsheet importer: a deliberately messy sheet (odd tab names, a title row, full names, `8h15`, `20/11/2026`, commas in lists, a Phone column) imports correctly and answers questions. A broken sheet is rejected with row-level errors, and nothing is written.

## Improvements made after testing

| # | Problem found in testing | Fix |
|---|---|---|
| 1 | "rules about phones" returned **not found**: the plural "phones" didn't match "phone". | Plurals now also match the singular form. TC03. |
| 2 | "I lost my water bottle": spelling correction changed **water → after**. | Corrections must start with the same letter and be at least 82% similar. `test_water_is_not_corrected_to_after`. |
| 3 | Vietnamese words matched people: "khoa học" (science) matched a teacher named Khoa, and "bao giờ" (when) matched a student named Bảo. | Added the `AMBIGUOUS_NAMES` rule: short or everyday-word names need a title or full name. Sample names that clash were changed. `test_vietnamese_word_khoa_does_not_match_a_person`. |
| 4 | "What class do I have now?" showed the bell period, not the student's actual lesson. | Questions about "my" class now/next use the logged-in student's timetable. TC28. |
| 5 | "who teaches chemistry" displayed "Showing results for: who teacher chemistry". | "teach / teaches / taught" are treated as question words, not search terms. |
| 6 | Single answers appeared in a narrow column on wide screens. | Single results now use the full width. |
| 7 | On the map, the selected room's label covered the building name. | Room labels are placed beside the pin. |
| 8 | SenTia data: "can I leave early" returned the general absence policy, because "leave" was a keyword there. | Removed the vague keyword and added "leave early" to the pick-up policy. ST14. |
| 9 | SenTia data: "what if I break something" returned the **Recess** bell period ("break"). | Added the phrase "break something" to the damage FAQ; "when is recess" still works. ST21. |
| 10 | SenTia data: "can I bring my dog" returned the laptop policy; the handbook only says "animals". | Added the words students use (dog, cat, pet) to the banned-items policy. ST22. |
| 11 | SenTia data: "voice level in the library" showed the library room before the library rules. | Added "voice level in the library" to the library rules. ST23. |
| 12 | SenTia bell schedule: in the 5–10 minute changeovers (e.g. 8:45–8:50) "what period is it now" said **school has finished**, because the sample schedule had no gaps. | Added a "changing over" state that shows the next period; students see their next lesson. SB09, SB11. |
| 13 | "next period" during or after the last period gave an empty answer. | It now says there are no more classes today. SB10. |
| 14 | The canteen policy, daily-schedule policy and meals FAQ gave lunch as 11:55–12:55 (handbook), but the bell schedule says 12:15–13:20. | The school confirmed the bell times; all three now say 12:15–13:20 and cite the bell schedule. `test_lunch_time_agrees_everywhere`. |
| 15 | Real campus: "gvcn lớp 9A1" (homeroom teacher of 9A1) showed the classroom, not the teacher. | "gvcn", "chủ nhiệm", "homeroom" and "form teacher" now mark a staff question, and each homeroom teacher matches their class. CC15–CC17. |
| 16 | Real staff: "giáo viên hóa học" (chemistry teacher) also returned cô Diệu Hoa, because without accents "giáo viên Hoa" reads "giáo viên hóa". | "giáo viên" is no longer used as a title in front of names; Vietnamese given names never match on their own. `test_chemistry_teacher_question_does_not_match_a_teacher_named_hoa`. |
| 17 | Real staff: "cô Hà" matched Hà Thu Ly by her family name. | Vietnamese teachers are matched by their given name ("cô Hà", "cô Thu Hà"), as students address them. `test_family_name_alone_does_not_match`. |
| 18 | Real staff: "cô Thu Hà" returned the two Thư teachers; the A/B the school adds to tell the two Thu Hà teachers apart broke the match. | The A/B suffix is ignored when matching given names. `test_thu_ha_is_not_thu`. |
| 19 | Real calendar: "when is the next holiday" returned National Day (2 Sep), which was already over. | Events that have ended count for half, and equal matches are shown soonest first. SC01, `test_past_holiday_is_not_the_next_one`. |
| 20 | Real calendar: "when are the exams" listed only IGCSE and Cambridge, because the school's own tests were called "Tests" and Teachers' Day had no "Holiday" in its name. | Renamed them to the words students use ("Exams", "Holiday"). SC01, SC05, ST17. |
| 21 | The calendar has multi-day events, month-long projects and no times, which the app couldn't store. | Events now have an optional last day, a category (holiday, exam, parent meeting…), and "All day" when there's no time; running events count as upcoming. `test_upcoming_includes_events_still_running`. |
| 22 | New staff: "thầy Alex" and "cô Khanh" were blocked as private questions, because the fictional demo students are also called Alex and Khanh. | A name with a title (cô, thầy, Mr, Ms) is a staff member, since students aren't addressed that way. Without a title the privacy rule still applies. CC30, CC31, `test_demo_student_names_still_private_without_a_title`. |
| 23 | New staff: "vice principal" / "phó hiệu trưởng" showed the Principal first ("hiệu trưởng" is inside "phó hiệu trưởng"). | The principals' search words were narrowed so the more specific job wins. CC23, CC24. |
| 24 | The team added Ms/Mr titles, but students say "cô" and "thầy". | Ms/Mrs/Miss also match "cô", and Mr matches "thầy". Single-name staff (Ms Lan, Ms Tuấn) need a title, so everyday words like "lần" don't find them. CC26, CC29, `test_single_name_staff_need_a_title`. |

## Manual checks (done in the browser)

- Home page, chat answer, map with route, login and student profile on desktop and on a phone-size screen (375 px).
- Dark mode follows the device setting and the toggle is remembered.
- Voice input button appears only in browsers that support it (Chrome, Edge, Safari).

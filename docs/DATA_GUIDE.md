# Data guide: from your Google Sheet to the app

The app reads its data from CSV files in `/data`. Your team keeps working in **Google Sheets**, and an importer turns the sheet into those files.

```
Google Sheet  →  File → Download → .xlsx  →  tools/import_sheet.py  →  data/*.csv  →  commit  →  Vercel redeploys
```

## Step 1: Set up the sheet from the template

1. Upload [`SSA_Data_Prefilled.xlsx`](../SSA_Data_Prefilled.xlsx) to Google Drive and open it with Google Sheets. Its **Policies** and **FAQs** tabs already hold the SenTia School Handbook 2025–2026 and its **Schedule** tab holds the real bell times, so the import won't lose them. (Rebuild it after changing that data: `.venv/bin/python -m tools.make_template --prefill Policies FAQs Schedule`. The blank version is `SSA_Data_Template.xlsx`.)
2. Copy your team's existing data into it, one tab at a time, in this order: **Buildings → Rooms → Teachers**, then the rest. The dropdowns in later tabs read from the earlier ones.
3. Hover any header to see what goes in that column. Dark-blue headers are required and light-blue ones are optional. The **Examples** tab shows one correct row for every tab.

To regenerate the blank template: `.venv/bin/python -m tools.make_template`

Policies and FAQs have an optional `source` column. Fill it with the handbook section, and it is shown under each answer.

## Step 2: Format rules

| Rule | Right | Wrong |
|---|---|---|
| One tab per dataset, one row per thing | One row per room | Several rooms in one cell |
| No merged cells or blank rows in the middle | | |
| One piece of information per column | `Ms` · `Sarah` · `Nguyen` | `Ms. Sarah Nguyen (English)` |
| Lists in one cell, separated by `;` | `English;Literature` | `English and Literature` |
| Times: 24-hour `HH:MM` | `08:15`, `13:30` | `quarter past 8` |
| Dates: `YYYY-MM-DD` | `2026-11-20` | `20/11`, `next Friday` |
| Codes must match exactly (use the dropdowns) | `B201` in Rooms and in Teachers | `B201` vs `ICT room` |
| English in the main column, Vietnamese in `_vi` | `name`: Library, `name_vi`: Thư viện | |

**What not to enter:**
- Real student information. Demo students are generated automatically and are fictional.
- Phone numbers, personal emails, addresses, grades or medical details.
- Map coordinates. Send a photo or sketch of the campus map instead.

**For good search results:**
- Fill `aliases` and `keywords` with the words students actually say, in both languages. For example, the ICT room: `computer lab;IT room;phòng máy;phòng tin học`.
- Write directions one step per sentence, starting at the building entrance. The app adds the "from the main gate" step.
- After launch, check the admin dashboard's **Unanswered questions** and add the missing words.

## Step 3: Import

1. Google Sheets: **File → Download → Microsoft Excel (.xlsx)**.
2. Check the file first (nothing is written):

   ```bash
   .venv/bin/python -m tools.import_sheet ~/Downloads/SSA_Data.xlsx --check
   ```

3. Fix anything listed under **Errors** in the Google Sheet, download again, and repeat until it says `✓ Import OK`.
4. Import for real:

   ```bash
   .venv/bin/python -m tools.import_sheet ~/Downloads/SSA_Data.xlsx
   ```

5. Run the tests (`.venv/bin/python -m pytest -q`), check the app locally, then commit the changed `data/` files.

### What the importer fixes for you

| You typed | It becomes |
|---|---|
| Tab named `Staff`, `teacher`, `Giáo viên` | Teachers |
| Header `Room number`, `Building`, `Name (Vietnamese)` | `room_id`, `building_id`, `name_vi` |
| A title row above the header, blank rows | Skipped |
| `b 201`, `a101` | `B201`, `A101` |
| `8h15`, `8.15am`, `1:30 pm`, a time cell | `08:15`, `13:30` |
| `20/11/2026` (day first), `20 Nov 2026`, a date cell | `2026-11-20` |
| `English, Literature` or one per line | `English;Literature` |
| `Ms.`, `thay`, `cô` | `Ms`, `Thầy`, `Cô` |
| `thứ 2`, `Mon`, `T2` | `Monday` |
| `Lesson`, `tiết học`, `recess`, `tan học` | `class`, `break`, `end` |
| One `Full name` column: `Thầy Trần Văn Hùng` | title `Thầy`, first `Hùng`, last `Trần` (shown as a warning to check) |
| Blank IDs for policies, FAQs, events, clubs | `POL01`, `F01`, `E01`, `C01`, … |
| Schedule rows out of order | Sorted by start time |

### What it refuses (listed as errors, nothing is written)

- A required column or tab is missing, or a required cell is empty.
- The same code is used twice in one tab.
- A code points to nothing, e.g. a teacher's room `GYM-9` that isn't in Rooms.
- A time or date it can't read, or an end time before the start time.

Columns the app doesn't use, such as a `Phone` column, are **ignored and listed as warnings**, so personal data never reaches the app.

### What it adds automatically

- **Map positions:** buildings that already exist keep their position. New ones are laid out in two rows around a central path, and room pins are placed inside their building. Send a campus sketch for an accurate map.
- **Fictional demo data:** three students (Alex, Khanh, Chloe), their timetables built from your real teachers, rooms and bell times, and clubs if your Clubs tab is empty. The `teacher` demo login is linked to a teacher who teaches Alex and Chloe but not Khanh, so the privacy demo still works.
- `"is_sample": false` in `school.json`, which removes the "sample data" banner. School name and time zone come from the **School** tab.

## Tests and real data

The automated tests run on a fixed copy of the sample school in `tests/fixtures/sample_data/`, so they keep passing whatever is in `/data`. `test_live_data_folder_is_valid` also checks that your real `/data` loads. Once the real data is in, add test cases that use real questions about your school; the brief wants your own testing evidence.

## Adding a demo login

Passwords are stored as hashes. To create one:

```bash
.venv/bin/python -c "import os; from app.auth import hash_password; print(hash_password('NEW-PASSWORD', os.urandom(16)))"
```

Paste the output into the `password_hash` column of `data/users.csv`.

# Smart School Assistant (SSA)

ICT Explorer 2026 · Smart School Assistant Challenge

**Live demo:** https://icte-26-27-app.vercel.app (opens in any browser, nothing to install; demo logins are listed below)

A web assistant that helps students, teachers and staff quickly find accurate school information by typing or speaking a question, or by browsing. Every answer comes from the school's approved data using programmed rules: keyword and phrase matching, intents, filters and privacy rules. **It never invents an answer.**

> **Status:** policies and procedures come from the **SenTia School Handbook 2025–2026** (42 policies, 24 FAQs, each citing its handbook section), and the bell schedule is SenTia's real one (8 periods, 07:45–16:05). Rooms and the campus map come from SenTia's floor-map signs and door signs (80 places across Zones A and B, 4 floors), and staff from the team's staff list (50 people, including the principals, nurses, librarian and counsellors, with the homeroom class of each of the 13 secondary classes). Events come from SenTia's provisional 2026–2027 secondary calendar (44 entries: holidays, exams, parent meetings, trips and projects). Rebuild with `.venv/bin/python -m tools.sentia_campus` and `.venv/bin/python -m tools.sentia_calendar`. All student data is fictional and must stay fictional.

## The six core functions

| # | Function | Try asking | Browse page |
|---|---|---|---|
| 1 | School policies | "Can I use my phone in class?" | `/policies` |
| 2 | Teacher & staff directory | "Who teaches chemistry?", "Ms Nguyen" | `/directory` |
| 3 | Classroom & campus navigation | "Where is the ICT room?", "Where is Mr Tran's room?" | `/map` |
| 4 | Bell schedule & calendar | "What period is it now?", "upcoming events" | `/schedule` |
| 5 | Procedures & FAQs | "What do I do if I'm late?", "lost property" | `/faqs` |
| 6 | Student profile | "my timetable", "what class do I have now?" (after login) | `/profile` |

**Bonus features:** user login · role-based access (student / teacher / admin) · interactive campus map · route guidance · voice input · text-to-speech · English + Vietnamese · mobile layout · dark mode · admin dashboard · search history · spelling correction · advanced search with filters.

## Tech stack

| Layer | Technology |
|---|---|
| UI | HTML + Jinja2 templates, HTMX (partial page updates), plain CSS and a little JavaScript |
| Logic | Python 3.12, FastAPI (`app/search.py` holds all the search rules) |
| Data | CSV files in `/data`, kept up to date from the team's Google Sheet |
| Hosting | Vercel (Python serverless function) |
| Tests | pytest (223 automated checks; the numbered cases are listed in `docs/TEST_CASES.md`) |

## Run it on your computer

You need [Python 3.12](https://www.python.org/downloads/) (3.11 or newer works) and Git.

**macOS / Linux**

```bash
git clone https://github.com/KEN38015/ICTE.26-27_APP.git
```

```bash
cd ICTE.26-27_APP
```

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements-dev.txt
```

```bash
.venv/bin/uvicorn app.main:app --reload
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/KEN38015/ICTE.26-27_APP.git
cd ICTE.26-27_APP
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\uvicorn app.main:app --reload
```

Then open http://localhost:8000 and log in with one of the demo accounts below. Stop the server with Ctrl+C.

Run the tests (Windows: `.venv\\Scripts\\python -m pytest -q`):

```bash
.venv/bin/python -m pytest -q
```

## Demo accounts (fictional, for judging only)

| Username | Password | Role | Can see |
|---|---|---|---|
| `alex` | `Alex-Demo-2026` | Student (Grade 6, 6A1) | Only Alex's own profile |
| `khanh` | `Khanh-Demo-2026` | Student (Grade 7, 7A1) | Only Khanh's own profile |
| `chloe` | `Chloe-Demo-2026` | Student (Grade 8, 8A1) | Only Chloe's own profile |
| `teacher` | `Teacher-Demo-2026` | Teacher (Ms Trần Thị Kim Oanh, History) | Students she teaches (Alex in 6A1, Chloe in 8A1), not Khanh |
| `admin` | `Admin-Demo-2026` | Admin | All profiles + admin dashboard |

Passwords are stored in `data/users.csv` only as salted PBKDF2 hashes.

## Project structure

```
app/
  main.py        UI layer: web routes (pages, /ask, login, admin)
  search.py      Logic layer: validation, privacy rules, intents, scoring
  data.py        Data layer: loads and checks the CSV files
  auth.py        Login, password hashing, roles
  store.py       Search log + admin-added FAQs/events
  i18n.py        English / Vietnamese interface text
  text.py        Text normalising (lowercase, remove accents)
  templates/     Jinja2 HTML templates (partials/ = reusable pieces)
  static/        CSS, JavaScript (voice, read-aloud, dark mode)
data/            School data (CSV) — generated from the Google Sheet
tools/           Spreadsheet template + importer
tests/           Automated tests (run on tests/fixtures/sample_data)
docs/            Architecture, test cases, data guide, AI usage
api/index.py     Vercel entry point
```

## Deploy to Vercel

1. Push this repository to GitHub.
2. On [vercel.com](https://vercel.com), choose **Add New → Project** and import the repository. No build settings are needed.
3. In **Settings → Environment Variables**, add `SSA_SECRET_KEY` with a long random value. It keeps logins working across servers. You can generate one with `python3 -c "import secrets; print(secrets.token_hex(32))"`.
4. Deploy. Vercel gives you a `https://<project>.vercel.app` link for the judges.

`vercel.json` runs the server in Singapore (`sin1`), close to Vietnam. Change `regions` if the judges are elsewhere. Open the link once a minute before judging so the server is already awake.

> On Vercel the search log and admin-added items are **temporary**: they reset when the server restarts. Core data in `/data` is permanent. For permanent admin edits, connect a database such as Supabase (see `app/store.py`).

## Updating the school data

1. Upload **`SSA_Data_Prefilled.xlsx`** to Google Drive and open it with Google Sheets. Its Policies, FAQs and Schedule tabs already hold the SenTia handbook and bell times; fill in the other tabs. (Using the blank `SSA_Data_Template.xlsx` would replace the handbook policies on import.)
2. **File → Download → Microsoft Excel (.xlsx)**, then:

   ```bash
   .venv/bin/python -m tools.import_sheet ~/Downloads/SSA_Data.xlsx --check
   ```

3. Fix any errors it lists (by tab and row), then run it again without `--check` to write `data/`.

Full format rules: [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md).

## Documents for judging

- [Architecture: UI → logic → data → response](docs/ARCHITECTURE.md)
- [Test cases and improvements after testing](docs/TEST_CASES.md)
- [Data guide](docs/DATA_GUIDE.md)
- [AI usage declaration](docs/AI_USAGE.md)

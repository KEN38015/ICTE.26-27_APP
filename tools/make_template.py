"""Build the data template.

    .venv/bin/python -m tools.make_template                      # blank: SSA_Data_Template.xlsx
    .venv/bin/python -m tools.make_template --prefill Policies FAQs Schedule
        # same, but those tabs are filled from the current /data files: SSA_Data_Prefilled.xlsx

Upload the file to Google Drive and open it with Google Sheets
(or File -> Import -> Upload in an existing sheet).
"""

import csv
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from tools.sheet_spec import SCHOOL_FIELDS, TABS, TAB_BY_NAME

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "SSA_Data_Template.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="2457D6")
OPTIONAL_FILL = PatternFill("solid", fgColor="7A92D9")
EXAMPLE_FONT = Font(italic=True, color="666666")
MAX_ROWS = 500

LISTS = {
    "kind": '"class,break,end"',
    "day": '"Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday"',
    "title": '"Mr,Ms,Mrs,Miss,Dr,Thầy,Cô"',
}

INSTRUCTIONS = [
    ("Smart School Assistant: data template", True),
    ("", False),
    ("HOW TO FILL THIS IN", True),
    ("1. Fill one tab per dataset. Do not rename tabs or change the blue header row.", False),
    ("2. One row = one thing (one room, one teacher, one policy...). No merged cells, no blank rows in the middle.", False),
    ("3. Dark-blue headers are required. Light-blue headers are optional. Hover a header to see what goes in it.", False),
    ("4. Lists go in one cell separated by ;   e.g.  English;Literature", False),
    ("5. Times are 24-hour HH:MM (08:15, 13:30). Dates are YYYY-MM-DD (2026-11-20).", False),
    ("6. Codes must match exactly. Use the dropdowns: a teacher's room must exist in Rooms, a room's building in Buildings.", False),
    ("7. English goes in the main column; Vietnamese goes in the column ending _vi.", False),
    ("8. Fill Buildings first, then Rooms, then Teachers (the dropdowns depend on them).", False),
    ("", False),
    ("WHAT NOT TO ENTER", True),
    ("- No real student information. Demo students are generated automatically and are fictional.", False),
    ("- No phone numbers, personal emails, addresses, grades or medical details.", False),
    ("- No map coordinates: send a photo or sketch of the campus map instead.", False),
    ("", False),
    ("TIPS FOR GOOD SEARCH RESULTS", True),
    ("- Fill 'aliases' and 'keywords' with the words students really say, in English AND Vietnamese.", False),
    ("  e.g. ICT room: computer lab;IT room;phòng máy;phòng tin học", False),
    ("- Write directions one step per sentence, starting at the building entrance.", False),
    ("- See the Examples tab for one correct row of every tab.", False),
    ("", False),
    ("WHEN YOU ARE DONE", True),
    ("Google Sheets: File -> Download -> Microsoft Excel (.xlsx). Then run:", False),
    ("    .venv/bin/python -m tools.import_sheet path/to/file.xlsx", False),
    ("The importer fixes small formatting problems and lists anything it cannot fix, by tab and row number.", False),
]


def current_rows(tab) -> list[list[str]]:
    path = ROOT / "data" / f"{tab.file}.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [[row.get(c.name, "") for c in tab.columns] for row in csv.DictReader(f)]


def build(path: Path = OUT, prefill: tuple[str, ...] = ()) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Instructions"
    for i, (text, bold) in enumerate(INSTRUCTIONS, start=1):
        cell = ws.cell(row=i, column=1, value=text)
        cell.font = Font(bold=bold, size=14 if i == 1 else 11)
    ws.column_dimensions["A"].width = 120

    # School settings
    school = wb.create_sheet("School")
    school.append(["field", "value", "help"])
    for c in school[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEADER_FILL
    for name, help_text, example in SCHOOL_FIELDS:
        school.append([name, example, help_text])
    school.column_dimensions["A"].width = 14
    school.column_dimensions["B"].width = 40
    school.column_dimensions["C"].width = 50

    # Data tabs
    for tab in TABS:
        sheet = wb.create_sheet(tab.name)
        sheet.append([c.name for c in tab.columns])
        sheet.freeze_panes = "A2"
        if tab.name in prefill:
            for row in current_rows(tab):
                sheet.append(row)
        for idx, col in enumerate(tab.columns, start=1):
            cell = sheet.cell(row=1, column=idx)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = HEADER_FILL if col.required else OPTIONAL_FILL
            cell.alignment = Alignment(vertical="center")
            note = f"{'REQUIRED' if col.required else 'Optional'}: {col.help}"
            if col.example:
                note += f"\nExample: {col.example}"
            cell.comment = Comment(note, "SSA")
            letter = get_column_letter(idx)
            width = max(len(col.name) + 4, min(48, len(col.example) + 4 if col.example else 14))
            sheet.column_dimensions[letter].width = width
            rng = f"{letter}2:{letter}{MAX_ROWS}"
            # Keep times/dates/ids as plain text so Sheets doesn't auto-convert them.
            if col.type in ("time", "date", "id"):
                for r in range(2, MAX_ROWS + 1):
                    sheet.cell(row=r, column=idx).number_format = "@"
            # Dropdowns
            formula = None
            if col.ref:
                ref_tab = TAB_BY_NAME[col.ref]
                ref_letter = get_column_letter([c.name for c in ref_tab.columns].index(ref_tab.id_col) + 1)
                formula = f"{col.ref}!${ref_letter}$2:${ref_letter}${MAX_ROWS}"
            elif col.type in LISTS:
                formula = LISTS[col.type]
            if formula:
                dv = DataValidation(type="list", formula1=formula, allow_blank=not col.required)
                dv.error = f"Choose a value from the list ({col.ref or col.type})."
                dv.errorTitle = "Not in the list"
                dv.showErrorMessage = col.type in ("kind", "day")   # titles/refs: warn only via dropdown
                sheet.add_data_validation(dv)
                dv.add(rng)

    # Examples
    ex = wb.create_sheet("Examples")
    row = 1
    for tab in TABS:
        ex.cell(row=row, column=1, value=f"{tab.name} — {tab.help}").font = Font(bold=True)
        row += 1
        for idx, col in enumerate(tab.columns, start=1):
            ex.cell(row=row, column=idx, value=col.name).font = Font(bold=True, color="FFFFFF")
            ex.cell(row=row, column=idx).fill = HEADER_FILL if col.required else OPTIONAL_FILL
            ex.cell(row=row + 1, column=idx, value=col.example).font = EXAMPLE_FONT
        row += 3
    for i in range(1, 12):
        ex.column_dimensions[get_column_letter(i)].width = 26

    wb.save(path)
    return path


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--prefill" in args:
        tabs = tuple(a for a in args[args.index("--prefill") + 1:] if a in TAB_BY_NAME)
        out = build(ROOT / "SSA_Data_Prefilled.xlsx", tabs)
        print(f"Template with {', '.join(tabs)} filled in written to {out}")
    else:
        out = build(Path(args[0]) if args else OUT)
        print(f"Template written to {out}")

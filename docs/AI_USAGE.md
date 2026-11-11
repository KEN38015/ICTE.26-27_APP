# AI usage declaration

> Team: please review and edit this page so it accurately describes your own work before submitting.

## Tools used

- **Claude (Anthropic), in Claude Code:** an AI coding assistant used during development.
- The finished assistant does **not** use any live AI service. Every answer comes from the school's approved data in `/data`, using the rules in `app/search.py`.

## How AI supported the project

| Stage | What AI did | What the team did |
|---|---|---|
| Planning | Summarised the challenge brief, compared tech stacks (HTMX + Jinja2 vs React + JSON), explained hosting and performance trade-offs | Chose the stack (FastAPI + HTMX + Jinja2), the data source (our real school) and the bonus features |
| Data | Created a sample dataset in the required format | Replace the sample data with the real school's information and check it |
| Coding | Wrote the first version of the data loader, search rules, privacy rules, templates and styles, explaining each part | Reviewed the code, asked for changes, and can explain UI → logic → data → response |
| Testing | Wrote automated tests (54 numbered cases + extra checks), ran them, and fixed problems it found | Add test cases from real student questions, run the tests, and check results |
| Improvement | Found and fixed issues after testing (see `docs/TEST_CASES.md`, "Improvements made after testing") | Use the admin dashboard's unanswered questions to keep improving the data |

## Prompt history

The full conversation with the AI assistant is the prompt history. Export it from Claude Code and attach it to the submission (for example as `docs/prompt-history.md` or a PDF).

Summary of the main prompts:

1. Shared the challenge brief (SSA_data.pdf) and asked to build a Smart School Assistant that meets its requirements.
2. Asked whether an HTMX/Jinja2 structure would work, with pros and cons compared to React + JSON.
3. Asked whether a backend limits performance, how to host the server, and for a performance comparison.
4. Chose: FastAPI + HTMX + Jinja2, real school data, all bonus features, AI builds with explanations along the way.
5. Shared the SenTia School Handbook 2025–2026; the AI turned it into bilingual policies and FAQs, each citing its section.
6. Shared the real bell schedule and confirmed the lunch time.
7. Shared the team's Google Sheet; the AI flagged that a tab held real student names and dates of birth on a public link, and used only class names.
8. Shared photos of the floor-map signs and door signs; the AI read the room numbers, classes and homeroom teachers from them and built the rooms, directions and campus map (`tools/sentia_campus.py`). Unknown rooms are labelled only by number, and no titles (Thầy/Cô) were guessed.
9. Shared the 2026–2027 secondary calendar image; the AI transcribed its 44 entries into events (`tools/sentia_calendar.py`), keeping the school's note that it is provisional. Corrected a teacher's name order and removed a staff member at the team's request.
10. The team added titles and 14 more staff (principals, librarian, nurses, guard, chef, more teachers); the AI added them and fixed the search problems this exposed.

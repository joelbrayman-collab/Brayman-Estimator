# Real-plan observations, first session (15 Nov 2026)

Joel's first real construction plan through Production (project BC-2026-0004, a subcontract job at 12620 County Road 15,
Merrickville). Six observations, and a seventh request, fixed together. Synthetic data only in the tests.

| # | Observation | Fix |
|---|-------------|-----|
| 1 | Home said "Good morning" at 16:27 (fixed text in `dashboard.html`) | The greeting follows the company clock (`local_time.local_now()`, America/Toronto): morning before 12:00, afternoon before 17:00, evening after. |
| 2 | Today was below the attention list; wanted Tomorrow after about 14:00 | The Today panel is the first block on Home. From 14:00 company time (`TOMORROW_FROM_HOUR` in `services/home_planning.py`) it shows Tomorrow; the coming days then start after tomorrow. |
| 3 | Drag the plan in first; read the address, designer and plan version | `app/plan_intelligence/title_block.py` reads the title block text (no AI, no OCR, no external service) and `POST /projects/plan-details` returns suggestions. They fill only empty boxes, are marked "Read from the plan", and nothing is saved until Create the project. The checked designer and plan version are kept: version as the project's drawing revision label, designer on the plan's note. No schema change. |
| 4 | Setup screen was meant to be compact like AiRIA's Open a New Case | Sections are numbered 1 to 4 and the plan area is one compact row (CSS only; every field, name and hook is unchanged). A tabbed one-section-at-a-time stepper was NOT built: it hides fields, which the browser evidence scripts fill directly. Left as a decision for Joel. PR #15 (five-step dialog) is merged on GitHub; the single-screen Set Up This Project (Slice C, 1 Nov) replaced it. |
| 5 | Plan upload had Browse only | Drop a PDF anywhere on Set Up This Project: it chooses Upload plan, fills the Plan PDF box and reads the plan. Browse still works. |
| 6 | "Error creating project: cryptography>=3.1 is required for AES algorithm" with the project already created | `cryptography` is now a requirement (and in the lock). A plan that needs a password says so; any plan problem after the project is saved reads "The project was saved, but the plan was not uploaded" and goes to the upload page. |
| 7 | A unique job (foundation, ICF main walls, concrete work) fits no standard type | "Other project" is now **Custom project**: choosing it opens the description box and requires it (also enforced by the server). The stored value is unchanged (`OTHER`), so no migration. The wording is set in `app/presentation/project_type_labels.py` when the app is created, not in the model file, because the release gate treats any `app/models` change as a schema change. |

Tests: `tests/test_protected_plan_upload.py`, `tests/test_home_today_tomorrow.py`, `tests/test_plan_drop_details.py`, `tests/test_custom_project_type.py`. Tests that read
"Today" on Home use the `morning_clock` fixture (`tests/conftest.py`), because Home now depends on the hour.

## 16 Nov 2026, after Production use (v0.6.1)

| # | Observation | Fix |
|---|-------------|-----|
| 5b | Drag and drop only worked on Set Up This Project | The Drawings page and the Upload PDF page take a dropped plan PDF anywhere on the page. |
| 9, 10, 11 | After an upload Joel landed on a page of audit events, a Pages table and a coordinates form, with no next step | After an upload (both from Set Up and from the plan pages) the landing says "Your plan uploaded successfully. What do you want to do next?" with **Estimate costs** (this project's Price This Job) and **Add more plans**. The engineering pages stay one click away ("See this plan's details"). A failed index still goes to the plan's own page, which has the retry. |

Still to build: the step bar on every project page and the Advanced fold (Build Drawings, Members, audit events). Joel, 16 Nov: "I should never have to click the logo top left, and I should never have to find my way back into the project."

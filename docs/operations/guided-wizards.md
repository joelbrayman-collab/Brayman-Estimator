# Guided Workflow Wizards (24 Oct 2026)

Branch `v1/wizards-2026-10-24`, built on the v1rel9 candidate `68f1a55` plus the office-clock fix (`c1e18db`).
One additive migration: `w2z9r4d7k1m6` (follows `g5e7c2a9d1b4`).

## What it is

One shared framework (`app/wizards/`) and four wizards over the existing pages and services. Home and the Supplier
Hub's Requests page ask **What do you need to do?**; each activity offers **Start Guided Wizard** and **Continue
Manually** on Home and on its own entry page (Start is a link: it only opens, or resumes, the person's own
wizard and writes no business record) (New Project form, Start New Estimate, the estimating workflow, the
project page, PRO Desk, a supplier request, a PRO Desk quotation).

| Framework piece | How |
| --- | --- |
| Back / Next / Save & Exit / Resume | `app/wizards/views.py`; the run remembers the step (`wizard_runs.current_step`) |
| Progress | every step's status is read from the real records each time (`StepView`), never stored |
| Required information | a required step that the records do not satisfy holds Next and lists what is missing; a step waiting for someone else (a quote, a customer, a supplier) never traps the person |
| Conditional steps | `Step.applies` (no drawings → no View Plan review; no subcontracted stage → no quote steps; contractor request vs walk-in quotation) |
| Automatic draft saving | Start a New Project steps 1–3 only (answers typed before the project exists, `wizard_runs.draft_json`) |
| Ask the Tutor | each step's what / do / next is its Help topic (`help_content` surface `wizard`); answers in place |
| Wizard ↔ manual | Continue manually opens the step's page; every page then shows **Return to the wizard** until Save & Exit |
| Return after an action | existing `return_to` (app/services/return_path.py) now also accepts a wizard step path |

## The wizards

| Wizard | Steps read / act through |
| --- | --- |
| Start a New Project (12 steps) | draft → `projects.create_project` (project, commercial context, location — created once: the run is claimed by a conditional update in the same transaction), plan upload / construction drawings / Site Plans / drawing requirement, View Plan and a recorded review of what the drawings give (no dimension is read or invented), `start_guided_estimate`, the guided scope page (Internal / Subcontracted / N/A), Company Calendar appointment, the setup resolver, then Guided Estimating |
| Guided Estimating (14 steps) | the v1rel9 engine only: stage status, quotes, approved supplier costs, the internal cost estimate, costing approval and company pricing (existing endpoints with `return_to`), proposals, acceptance and the work-plan hand-off |
| Manage a Project (12 steps) | accepted proposal, contract signing status, work plan and work schedule, assignments, scope-delivery routing, supplier accounts, requests and purchase orders, deliveries, monitor and job cost, change orders and extra work, punch list and walkthrough, Close Project (owner or System Administrator, the existing route). QuickBooks Time and schedule texts show whether they are switched on |
| Supplier Pro Desk (12 steps) | a contractor request (only what was shared; only the contractor orders) or a PRO Desk / Quick Quote quotation (the supplier's own price file, availability where the price file carries it, issue, answer, revisions followed, order package). No rewards program exists in CalibraytAI, so none is calculated |

## Database (`w2z9r4d7k1m6`)

New tables `wizard_runs`, `wizard_run_events`; no existing table changes. A contractor run must name its company and
no supplier; a supplier run must name its supplier and no company (check constraint). Downgrade refuses while either
table holds a row. Release gate: `--migration-to w2z9r4d7k1m6 --new-tables wizard_runs,wizard_run_events`.

## Tests

`tests/test_wizards.py` (pytest) and `tools/release/evidence_wizards.mjs` (browser, desktop and phone; in
`release_gate.sh`, 9 checks; `BROWSER_EXPECTED` 228). Training: contractor module 15 and supplier module 11
(`app/training/wizards_lessons.py`), pictures `app/static/training/shots/w-*.png` from
`tools/training/capture_wizard_shots.mjs`.

# Project Creation UX (27 Oct 2026)

Joel's brief "CALIBRAYTAI — PROJECT CREATION UX CORRECTION", after the Production finding of 27 Oct: a new customer
(Linda Bushel) added from Start a New Project came back to the wizard with another customer (Marc) selected.

## What changed

| Area | Now |
| --- | --- |
| Home | Greeting row with Company Calendar · WHAT NEEDS MY ATTENTION? (first, the only attention list) · one GUIDED WIZARDS band: Start a New Project, Estimate a Project, Manage a Project, each with Continue manually · Continue where you left off (one line per unfinished wizard) · Today and Coming days · counts. The separate + Start New Project / Start New Estimate buttons and the briefing's third attention column are gone (each repeated something above). |
| Start a New Project | 7 compact tasks (was 12): customer · what are we building · where is the job (creates the project) · drawings (optional) · your role · who is leading it (optional) · review and finish. `Wizard(compact=True)`, `wizards/_run_compact.html`. **Superseded 28 Oct 2026** by the five-step dialog below. |
| New customer | Entered inside step 1; Save & Continue creates it (`app/services/clients.create_client`), records `CUSTOMER_CREATED`, puts the new customer's exact id in the run's draft and moves to step 2. No detour to Clients; nothing is inferred from list order. A repeated submit with the same name does not create a second customer. |
| Customer form (Clients and wizard) | Shared partial `clients/_fields.html`: name (required), company, email, phone, street, unit, city/town, province/state (controlled list per country), postal code (Canadian codes normalized, e.g. `K0G 1J0`), country (Canada default). |
| Address data | Six nullable columns on `clients` (migration `q4c7l2n8t3a6`). `clients.address` is kept and, when structured parts are saved, is composed from them. An existing one-line address is never parsed; it is shown as "Address as written" until someone enters the parts. |
| Job site | Separate from the customer address; "Same as <customer>'s address" copies the structured parts (server side too, `projects._wizard_location_form`). |
| Missing email/phone/address | Not required. One Attention item per customer (`needs_attention.incomplete_customers`), "Complete information" → the customer form → back; it disappears as soon as the information is saved. Shown on Home, on the project page, and on the wizard review. Customers whose jobs are all closed are not listed. |

## Database

`q4c7l2n8t3a6` (down `e5d1v4r7y2k9`): `clients` gains `street_address`, `unit`, `city`, `province_state`,
`postal_code`, `country` (all nullable, plain `ADD COLUMN`, no table rebuild, no data change). Downgrade refuses while
any of them holds a value. Release gate: `--migration-to q4c7l2n8t3a6 --new-tables none --altered-tables clients`
(`--new-tables none` added 27 Oct 2026: the rehearsal then requires that no table is added).

## Tests

`tests/test_project_creation_ux.py` (the 13-point Linda regression and the rest), `tests/test_wizards.py`,
`tests/test_migration_check.py` (column-only rehearsal), and the browser walk
`tools/release/evidence_project_creation.mjs` (9 checks, desktop and phone; in `release_gate.sh`,
`BROWSER_EXPECTED` 263). Local page server: `tests/project_creation_page_server.py`.

## Compact Open a New Project (28 Oct 2026)

Joel's brief "Compact Open a New Project" (the AiRIA Open a New Case dialog as the density reference, and the approved
Calibrayt mockup). Same workflow, same information, same functionality, much more compact. Joel's decision (28 Oct
2026, "Option 2"): the project is still created on step 3, so plans upload to it with the proven Step-4 behaviour.

| Step | What it holds | Notes |
|---|---|---|
| 1 Project | name, project number, what is being built, description; commercial type and status (pre-filled, under More details) | draft (autosaved) |
| 2 Customer | existing customer (exact id) or a new one saved in place | unchanged rules |
| 3 Details | Site information (job site, Same as customer address, rural address) · Project settings (permit class, pricing posture, execution risk, schedule, site, estimate stage, delivery model, justification) · Your role (required) · Project Lead (optional) | **Create Project & Continue** posts to `projects.create_project` (refused without a role, nothing lost); after creation the guided estimate starts with that role. Afterwards the step shows the project and changes the role (if missing) and the lead on a real press only |
| 4 Plans | upload in place, no drawings needed, or later | unchanged (busy state, one plan per file, size limit) |
| 5 Review | Project information · Customer · Site and project details · Plans and documents, each with Edit; what is still to add; a site visit or meeting | **Finish** (a second press finishes nothing more) |
| Project Created | name, number, customer, status, role | `GET /wizards/run/<id>/created`: Open Project (primary), Start Guided Estimating, Create Another Project |

Removed as separate steps (their fields moved, nothing dropped): "What is your role on this job?" and "Who is leading
it, and when?" (role and Project Lead are on Details; "Add a site visit or meeting" is on Review). A run left on one of
those steps resumes at the first open step. The dialog: dimmed backdrop, `role="dialog"`/`aria-modal`, Tab kept
inside, × and Escape are Save & Exit, the page's messages are shown inside the dialog, the steps numbered across the
top; two columns at desktop and 1280, one column on narrow screens.

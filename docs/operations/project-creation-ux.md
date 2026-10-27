# Project Creation UX (27 Oct 2026)

Joel's brief "CALIBRAYTAI — PROJECT CREATION UX CORRECTION", after the Production finding of 27 Oct: a new customer
(Linda Bushel) added from Start a New Project came back to the wizard with another customer (Marc) selected.

## What changed

| Area | Now |
| --- | --- |
| Home | Greeting row with Company Calendar · WHAT NEEDS MY ATTENTION? (first, the only attention list) · one GUIDED WIZARDS band: Start a New Project, Estimate a Project, Manage a Project, each with Continue manually · Continue where you left off (one line per unfinished wizard) · Today and Coming days · counts. The separate + Start New Project / Start New Estimate buttons and the briefing's third attention column are gone (each repeated something above). |
| Start a New Project | 7 compact tasks (was 12): customer · what are we building · where is the job (creates the project) · drawings (optional) · your role · who is leading it (optional) · review and finish. `Wizard(compact=True)`, `wizards/_run_compact.html`. |
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

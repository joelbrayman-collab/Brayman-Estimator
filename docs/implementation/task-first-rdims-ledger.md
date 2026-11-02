# Task-First UX, Guided Tasks and standalone RDIMS — progress ledger (from 31 Oct 2026)

Mandate: Joel, 31 Oct 2026 ("CALIBRAYTAI — TASK-FIRST UX + GUIDED TASKS + RDIMS TRANSFORMATION"). One development
cycle through deployment; no routine approval stops (Joel: "all tasks and access are approved").

## Baseline (protected)
- Live: `7087d0d0`, Render `dep-dbj4bnff3r2c73eu4qvg`, database revision `s6f7a8b9c0d1`.
- Verification: 3,732 tests, no skips; 302/302 browser checks; migration rehearsal and production migration passed;
  post-release integrity explained; signed-out Live smoke passed.
- Branch: `feature/task-first-rdims-2026-10-31` (worktree), from main `7087d0d0`.

## Steps
1. Baseline recorded; branch created. AiRIA reference = read-only copy of `Discovery-Search` origin/main `b1ec1d1e`.
2. Tooling follow-up from e2p1 (done): `release_migrate.sh` records the rows the migration seeded
   (`MIGRATION_SEEDED=t=n,...` in the release state); `postrelease_check.sh` reads the seeded tables' counts on the
   live database (read-only) and `migration_check.py postcheck-rows` proves live = backup + new tables + exactly the
   declared seed, table by table; anything else still stops. Tests: `tests/test_release_postcheck_seed.py`.
3. Audits (done, durable): `docs/ux/task-first-ux-audit-2026-10-31.md` (333 templates / 237 screens, 636 routes,
   28 office nav destinations, 4 wizards / 44 steps of which 28 can be automated, removed or merged, 21 attention
   events not surfaced); `docs/rdims/airia-rdims-reuse-map-2026-10-31.md` and
   `docs/rdims/calibrayt-rdims-architecture-2026-10-31.md`.

## Implementation plan (internal; not an approval gate)
- Slice A (branch `task-first/ux`): design tokens + Task Screen macros; navigation to ~6 primary items + More +
  Admin; one attention list built from a provider registry with the missing events, each linking to the exact
  task; project page rebuilt as a Task Screen with a state-driven Next step; internal terms renamed in visible text.
- Slice B (branch `task-first/rdims`, in parallel): standalone documents layer — the release's ONE migration
  `t7a8b9c0d1e2` (additive tables only, no backfill rows), content-addressed storage, versions, links to every
  context, connect-existing (no file moves), FTS5 search with fallback, contextual Documents pages, Company Library,
  equipment, confirmed-date attention items, CaliSIGN links, standalone proof.
- Slice C (after A and B merge): Guided Tasks — Price This Job (one screen), Review This Estimate (one governed
  Approve action), Set Up This Project (software-only fields filled automatically, review step removed), wizard
  retirement/merging per the audit, field Today simplification, supplier hub CaliSIGN-awaiting item.
- Then: role/phone walks, full regression, whole-branch review, fixes, gate, release.

## Rulings
- Only one migration in the release (the gate allows exactly one added migration file): it lives in Slice B; any
  later schema need is folded into it before the gate.
- No backfill rows inside the migration: existing documents are connected by an idempotent service (lazy + CLI),
  so the release rehearsal stays "existing rows identical, new tables empty".

## RDIMS (company Documents) — implementation, 31 Oct 2026
Branch `task-first/rdims` (worktree `/home/claude/tf-rdims`). Design: `docs/rdims/calibrayt-rdims-architecture-2026-10-31.md`
and `docs/rdims/airia-rdims-reuse-map-2026-10-31.md`. Users see "Documents", "Company library", "Equipment"; never "RDIMS".

### Delivered
- **Migration `t7a8b9c0d1e2`** (down `s6f7a8b9c0d1`), the only migration of the release: `organization_equipment`,
  `organization_equipment_events`, `documents`, `document_versions`, `document_links`, `document_dates`,
  `document_events`, `document_text` + insert-only triggers on both event tables; `document_search` (FTS5, plus its 5
  shadow tables `document_search_data/_idx/_content/_docsize/_config`) only when the SQLite build has FTS5. No existing
  table altered, **no row written** (no backfill). Downgrade refuses while any new table holds a row.
  `migrations/env.py` excludes `document_search*` from autogenerate. A test proves models and migration build the same
  columns and indexes.
- **Services** `app/services/documents/` (types, dates, extract, contexts, access, ingest, sources, search, fts,
  attention), `app/services/document_storage.py` (content-addressed `instance/documents/<org>/<sha[:2]>/<sha><ext>`,
  write-once, 25 MB, extension + magic checks, symlink/traversal refused), `app/services/equipment.py`.
- **Routes** (blueprint `documents`, `equipment`): `/documents` (`documents.library`, stable), `/documents/upload`
  (pick file → suggested type + dates to confirm → Save; `quick=1` files at once), `/documents/upload/link`,
  `/documents/<public_id>` (+ `/file`, `/versions`, `/dates…`, `/correct`, `/confirm-type`, `/archive`, `/restore`,
  `/links…`), `/projects/<id>/documents`, `/customers/<id>/documents`, `/suppliers/<id>/documents`,
  `/documents/suppliers`, `/subcontractors` (list + add), `/subcontractors/<id>/documents`,
  `/people/<membership_id>/documents`, `/documents/people`, `/equipment`, `/equipment/new`, `/equipment/<id>`,
  `/equipment/<id>/retire`; field: `/field-documents/projects/<id>`, `/field-documents/<public_id>/file`.
- **Insertion points** (one line each, marked): nav "Documents" after Past jobs in Company library
  (`app/navigation.py`); project hub link `data-hub-documents` (`projects/detail.html`); client page link
  `data-customer-documents` (`clients/form.html`); Field job screen `data-field-documents-link` (`field/projects.html`);
  `needs_attention.assemble` extends with `document_attention_items` before the sort; two field endpoints added to
  `FIELD_ONLY_ALLOWED_ENDPOINTS`; blueprints/CLI/`DOCUMENT_ROOT` (temp in tests) in `app/__init__.py`.
- **CLI** `flask documents connect-existing [--organization ORG] [--dry-run]` (prints per-kind reconciliation,
  `RECONCILED=yes|no`), `flask documents reindex`.
- **Evidence walk** `tools/release/evidence_documents.mjs` (+ `tests/documents_page_server.py`): 4 browser checks, all
  pass locally. Not yet in the gate list or browser count (release owner).

### Rulings
- **R1 Person documents** anchor to `user_memberships` (the People & Access record; D1). Person pages and PEOPLE
  documents are for people administrators (instance owner / System Administrator) only; others get 404. Person-context
  uploads are `PEOPLE` sensitivity; sensitivity wins over context everywhere (lists, search, attention).
- **R2 Field crew** (task brief overrides D2): field-only members see, read-only, documents linked to the projects they
  work on (`field_visible_project_ids`) of crew-visible types only (Drawing / plan, Specification, Installation / work
  instructions, Safety), STANDARD sensitivity only, via two allow-listed field pages. Every other `documents.*` /
  `equipment.*` endpoint redirects them to Field Today (GET) or 403 (POST) — tested over the url map.
- **R3 Office access**: STANDARD for every office member; FINANCIAL with `has_office_financial_access` (today every
  active non-field-only member); PEOPLE for people administrators. Supplier Hub users never pass the office wall.
- **R4 Suppliers** (global table): a supplier context is allowed only with an ACTIVE `contractor_supplier_accounts`
  row for the organization; otherwise 404.
- **R5 Connect existing**: plans, generated contracts, CaliSIGN executed PDFs, drawing sets (only when not saved as a
  plan document) and past-job workbooks are registered by reference (one row per source, unique index), never copied.
  Not in the migration: lazily (project scope) when a project's Documents page opens, and by the CLI. Missing files are
  registered `MISSING` (shown, counted, reported in "to review"). No SAVEPOINTs (pysqlite commits on RELEASE outside a
  transaction): one commit per registration; a dry run rolls back.
- **R6 CaliSIGN**: no second signature system and no signing hook added; executed artifacts come in through
  connect-existing/lazy. The document page shows CaliSIGN status + history (`calisign.status_for`/`timeline`) and links
  to the existing contract / change order page. Signing arbitrary uploads remains D4 (deferred).
- **R7 Classification**: name keyword +3, text keyword +1, extension hints; ≥2 wins (one name keyword or two text
  keywords), else Other; plurals normalised. Uploads through the review step are CONFIRMED; `quick=1` stays SUGGESTED
  and is counted in the "documents to review" roll-up.
- **R8 Dates**: cue words only from the date's own sentence/line; ambiguous dd/mm proposed both ways; dates >1 year
  past or >25 years ahead dropped; max 2 per kind. Attention: only CONFIRMED action dates on the current version of an
  ACTIVE document within `remind_days_before` (default 30) or past; roll-ups for dates to confirm and documents to
  review. No compliance rules.
- **R9 Lists** are paged in SQL (50; offset cap 2,000) and never load bytes or text; a correlated-subquery bug found by
  the date-filter tests was fixed by putting the version table inside each EXISTS.

### For the release owner
- New tables for the migration check / post-release row step (**corrected 1 Nov 2026, review fix C1**): declare
  exactly the 8 above with `--new-tables` — not `document_search` or its shadow tables. The 8 are empty after the
  migration; their rows appear only after `flask documents connect-existing` (or the first project Documents page
  opened). `document_search` (FTS5, when the SQLite build has it) is **not** empty: FTS5 writes its own bookkeeping
  rows when it is created (`document_search_data` 2, `document_search_config` 1), and two shadow tables are WITHOUT
  ROWID. `migration_check.py` now detects virtual tables and their shadow tables itself and treats them as a search
  index: reported on `SEARCH_INDEX_NEW=` / `SEARCH_INDEX=`, never row-hashed, never in `--new-tables`, never in the
  `TABLES=/ROWS=` totals (gate backup count and post-release live count both use `migration_check.py count-rows`).
  See "Review fixes" below for the exact gate arguments.
- Add `instance/documents` to the post-release storage check; add `evidence_documents.mjs` (4 checks) to the gate.

### Verification (31 Oct 2026, local, no skips)
- Documents tests (7 files): 135 passed (service 82, search 19, attention 7, connect-existing 8, routes 16,
  migration 3, standalone 5) — included in the runs below.
- Head-asserting suites moved to `t7a8b9c0d1e2` (45 files, deliberate update of "current head" only): 713 passed.
- Broader affected suites (security sweep, field-only, nav/UAT presentation, contractor language, project hub,
  attention, people access, release tools, migration check, site plans, field, signing artifacts, access domains +
  documents): 409 passed, 3 failed → fixed and re-run green: the field-only endpoint freeze gained the two reviewed
  job-document endpoints (`tests/test_security_route_sweep.py`, 9 passed); `tests/test_uat3_workflow_documents.py`
  now asserts the per-job register stays out of the menu and the only "Documents" item is `documents.library`
  (5 passed).
- Browser: `tests/e2e` contractor workflow + job lifecycle 2 passed; `tools/release/evidence_documents.mjs` 4/4.
- Full 3,700+ regression not run in this worktree (2-CPU container); the release gate runs it.

## UX core (branch `task-first/ux`, 31 Oct 2026)
First half of the Task-First UX redesign, from `docs/ux/task-first-ux-audit-2026-10-31.md`. No migration, no model
change, no governed capability removed (every route kept; pages keep their own permission checks).

- **A. Design system.** `app/static/css/tokens.css` is the one token file (the `app.css` / `v1-refinement.css` split
  is gone; `--danger`, status pairs, a 4 px spacing scale and type steps are defined; 13 `var(--danger, #…)`
  fallbacks removed). Focus is a 3 px deep-gold outline (6.3:1 on white). Task Screen standard:
  `partials/task_screen.html` (context, purpose, state, attention, next_step, details) + `task-screen.css` +
  `task_screen.js` (an anchor inside a closed section opens it). Checked at 1280 and 390 px: no sideways scroll.
- **B. Navigation.** Office sidebar **28 destinations in 6 sections → 6 primary** (Attention · Projects · Calendar ·
  Customers · Purchasing · Time & Money) **+ More**; administrative pages behind a header **Admin gear**. More: 10
  calculators, Costs & pricing (+ Materials catalogue), Lists (estimates, proposals, change orders, extra work, job
  updates), Past jobs, Business tools (decision tools, supplier economics), Help. Admin: company profile, People &
  Access (owner/SA only, as before), crews, hours policy, texts, crew notices, calendar feed, reminders, How we
  price, labour rates, document templates, work catalog. Purchasing and Time & Money are new Task Screen landings
  over every page of their area. All 28 earlier destinations reachable (`reachable_endpoints()`, tested). The dead
  bell is the live count of items waiting on you (`/attention/count`, fetched after load). Field and Supplier Hub
  shells unchanged. Cal Find It reads the same three sources.
- **C. One attention list.** `needs_attention.py` is a registry: **1 monolithic function (12 sources, 21 item
  variants + 6 company fact types) → 28 scoped providers** (12 existing + failed crew texts, which was a Home banner,
  + 15 governed events: Gate 1 ready, calculator results not on the estimate, subcontract quotes waiting / received,
  material lines without a price, proposal unanswered, CaliSIGN awaiting signature / countersign / expiring /
  declined / expired, contract not generated after acceptance, Gate 3 subcontract approval, early order not placed,
  Company Schedule Change Requests, delivery notices to send, accepted work not scheduled, draft change orders,
  walkthrough returned, ready to close). Scopes use the existing permissions (office, financial, company = CM or
  owner, company facts = CM, owner/admin). Links are `url_for` (deep anchors added to planning and commitments).
  Hook: `register_attention_provider(AttentionProvider(...), app=app)` → `app.extensions["extra_attention_providers"]`.
  Home and `/operations/attention` are one list (Waiting on you / Waiting on others; kind filters).
- **D. Project page.** `projects/detail.html` rebuilt as a Task Screen: context header, ONE Next step from
  `services/project_next_step.py` (setup → scope → price → approve → customer → contract → buy → schedule → change →
  close; the setup resolver still owns everything before the estimate), What Calibrayt already knows, this job's
  attention items, 11 closed sections + More actions. On opening a new job: **0 buttons and 18 links visible (1
  primary) instead of 26 buttons and 65 links all at once**; every action and data-* hook kept.
- **E. Contractor words** in visible text only (see commit `40b5e2b7`).
- **Screens substantially simplified: 5** (Home, Project page, the attention list (2 pages → 1), Purchasing and Time
  & Money as Task Screens) + More and Admin pages replacing 22 sidebar rows.

Rulings
1. `/company-attention` stays as a view (job-by-job labour facts, still COMPANY_MANAGEMENT) and is linked from the
   attention list; its facts are in the one list (Home included) for CM members. Not a redirect: keeps FG-035.
2. Admin gear is shown to every office member; each link is filtered by the page's existing permission (People &
   Access stays owner/SA). Hiding pages from office members would remove access the permission model grants.
3. "Extra work not on a change order" still opens the work plan (where the governed "add change order work item"
   action is); the schedule conflict still opens the project's schedule section (it lists the fixes).
4. Wizards kept for now ("Guided Wizards" band renamed "Start something"); retiring them is the second half.
5. Browser walks: the Project page sections are closed, so walks open them (`openSectionsIfProjectPage` in
   `evidence_common.mjs`, inline in the two e2e walks). No check removed or added.
- **Verification (1 Nov 2026, cloud workspace).** Full suite run in two shards: 3,763 tests; 14 failures, every one an
  assertion of the old structure or text (each updated deliberately with a comment, equivalent coverage) plus one
  re-render path (`build._render_hub_with_actuals_form`) that now uses the same Task Screen; all re-run green.
  11 skipped are the existing office-Mac-only historical workbook tests (no source copy here). Browser walks: all 26
  evidence files (302 checks + identity_gate3's 1 = 303) and `tests/e2e/contractor_workflow.mjs` pass;
  `tests/e2e/job_lifecycle.mjs` passes. Walks changed: field_time, first_day, guided_estimating, magnificent_seven,
  selected_work, wizards, workflow_map (+ the two e2e walks); helpers in the new `tools/release/evidence_task_first.mjs`
  (`evidence_common.mjs` keeps its pinned bytes). Check count unchanged. The receipt walk now uses the company date
  (America/Toronto), which fixed a failure after 8 pm (UTC already tomorrow).
- **Open (not this branch):** `tests/e2e/job_lifecycle.mjs` (run by `tests/test_job_lifecycle_e2e.py`) passed on
  this branch on Saturday 31 Oct evening, then failed at 00:35 Sunday 1 Nov (Toronto): Field My Week (on a Sunday it
  opens the coming week) does not list tomorrow's concrete delivery. It fails the same way on the baseline commit
  `1d1448a0` at that hour, so it is a pre-existing day-of-week defect in Field week / deliveries. It needs its own
  root-cause fix and a test.

## My Week date fix (1 Nov 2026, branch `task-first/myweek-fix`)

Closes the "Open" item above (job_lifecycle walk failing just after midnight on Sunday 1 Nov).

- **Root cause.** Not My Week. The walk computed "tomorrow" as now + 24 hours. Sunday 1 Nov 2026 is the day Toronto
  leaves daylight time, a 25-hour day, so between 00:00 and 00:59 EDT now + 24 h was still 1 Nov: the concrete
  delivery was dated *today*, a Sunday, and My Week on a Sunday (by design, 25 Oct) shows the coming Monday–Sunday,
  so it was rightly not listed. Reproduced by running the walk with its clock and the app server's clock set to
  00:20 EDT on 1 Nov (fails at the My Week assertion, line 485); at 01:12 the same walk passed. The baseline
  `1d1448a0` fails the same way because the walk's arithmetic is older than it. A second wrong assumption in the walk:
  it took "today" from the machine's clock zone while the app's is the company zone (America/Toronto); the release
  gate sets no TZ, so on a UTC machine between 20:00 and midnight Toronto every walk date was a day ahead (on a
  Saturday evening "tomorrow" became Monday, outside that week's My Week).
- **App code checked.** `field_week_start`, `calendar_week_bounds`, `field_month_bounds`, the Field Today, Week and
  Month routes all read `local_today()` and are correct. Four sibling defaults read the server's date
  (`date.today()`, UTC in production) instead of the office's day and now use `local_today()`:
  `governed_schedule.procurement_plan` (the "late" flag; its route already passed `local_today()`),
  `documents.search.search` (library "expired" / "expiring within" filters), `documents.dates.find_dates` (proposed
  dates from uploads) and `documents.attention.document_attention_items`. No model, migration or template change.
- **Walk fixes (commented).** `tests/e2e/job_lifecycle.mjs` and `tests/e2e/contractor_workflow.mjs`: "today" is the
  company zone's calendar day (`COMPANY_TIME_ZONE`, default America/Toronto) and day offsets are calendar days
  (`new Date(y, m, d + n, 12)`), not multiples of 86,400,000 ms. No assertion changed.
- **Tests.** New `tests/test_field_week_tomorrow_delivery.py` (22 cases; each runs with the process zone UTC and
  America/Toronto): tomorrow's agreed delivery is on Kevin's default My Week, in tomorrow's day and no other, at a
  Sunday morning, Saturday 22:30 and 23:59 EDT (already Sunday in UTC), Sunday 00:20 EDT and 01:30 EST on the DST-end
  day, Saturday night before spring-forward and the 23-hour Sunday; week/month bounds follow the office day; Field
  Week and Month agree in the evening; the procurement and Documents defaults use the office day (these fail on the
  old code). Results: field/schedule/documents pytest files (26 files) 400 passed; `job_lifecycle.mjs` and
  `contractor_workflow.mjs` pass on the real clock; `job_lifecycle.mjs` also passes with its and the server's clock
  at 00:20 EDT on 1 Nov (where it failed before).
- **Noted, not changed:** Documents "uploaded from/to" filters compare naive-UTC `created_at` with local-midnight
  bounds (a document uploaded after 20:00 Toronto falls on the next day's filter); `tools/release/evidence_roles.mjs`
  uses UTC dates for moves, consistent within each check, so harmless.
- **Follow-up (main session, `b47d44a4`):** the "uploaded from/to" filters now use the office calendar day
  (midnight in the company's zone, converted to UTC); test `test_uploaded_filters_use_the_office_calendar_day`
  failed first, then passed; `tests/test_documents_search.py` 20 passed under TZ=UTC and TZ=America/Toronto.

## Slice C — Guided Tasks (branch `task-first/guided`, 1 Nov 2026)
From `feature/task-first-rdims-2026-10-31` @ `14a523cc` (Slices A and B merged). No migration, no model or schema
change, no route removed, no governed action weakened. Service `app/services/guided_tasks.py`; blueprint
`app/routes/guided_tasks.py` (`guided_tasks.review_list`, `guided_tasks.approve_estimate`).

### Built
1. **Price This Job** (`guided.workflow`, `/projects/<id>/guided`, `guided/workflow.html`): one Task Screen — context
   (job, Brayman #, customer, estimate and version), purpose, ONE primary action (`price_this_job`: the next
   unpriced work item → its page `guided.stage`; every item priced → Review This Estimate; only quotes outstanding →
   "Waiting on others"; nothing chosen → Choose the work), the progress and status counts, the totals (cost, selling
   price, true margin, labour hours from `estimate_economics`), the work list with each item's status, "Next:" and
   issues, this job's estimating attention items, then closed: More for this job (add/change work, Review This
   Estimate, internal cost, calculators, supplier prices, line items, labour rate and margin, compare versions,
   start a revision), Still to do, Recent decisions. Nothing re-implemented: calculators, quantities, labour hours,
   quotes, allowances, routing and completion stay on the work item's page. `/estimating/start` (`guided.start`) is
   the "choose the job" page for Price This Job.
2. **Review This Estimate** (`guided.pricing`, `guided/pricing.html`): context, purpose, ONE primary — **Approve
   Estimate** — with its consequence in figures ("confirms the costs, prices the job at M % margin and $R an hour,
   and locks version N at $T"), Needs a decision (unfinished work, costing blocks in plain words, no proposal
   template), What Calibrayt already knows (items priced, labour hours and rate, margin, HST, winter), the project
   pricing form (labour rate and margin per project, unchanged), then closed: Approve in separate steps (the earlier
   1-2-3 with `data-approve-costing` / `data-apply-pricing`), The customer proposal, Into the build, More for this
   job. **The Approve is the existing Gate 1** (`guided_tasks.approve_estimate` → `estimate_costing.approve_all_costing`
   when the costing is not current → `pricing_engine.apply_resolved_pricing_to_version` when the pricing is not
   current → `proposal_acceptance.sign_off_estimate`, which writes the `EstimateApproval` record (who, when, frozen
   summary, fingerprint), locks the version and builds the proposal). Same services, same refusals; any refusal
   rolls everything back. It also refuses when the priced customer total differs from the total the person was shown
   (`expected_total`), when the version changed, when it is already approved (Gate 1 immutable) or accepted.
3. **Set Up This Project** (`projects.create_project`, `projects/form.html`): one screen — customer (choose, or add a
   new one here: name, email, phone, created by `clients.create_client` in the same transaction), the job (name,
   what is being built, your role, Client Project #, description), job site (same as the customer's address, rural
   lot), plans (upload / generate / **No drawings needed** / later). Software-only fields are filled automatically
   and kept under the closed **Adjust project settings**: status (Lead), commercial project type (from what is being
   built; blank → `COMMERCIAL_TYPE_HINT`, else New Build), permit class (default), the six settings (company
   defaults), Project Lead (the person creating it), start the estimate (on). Brayman Project # still automatic. The
   wizard's separate Review step is removed. Every validation kept (name and customer, customer rules, reason for an
   exceptional posture/risk, project identity, location, permit).
4. **Wizard retirement**: `wizards.start` for NEW_PROJECT, GUIDED_ESTIMATING and MANAGE_PROJECT (GET and POST)
   redirects to the Guided Task (`/projects/new`; `/projects/<id>/guided` or `/estimating/start`; the project page or
   the project list) and starts no run. Runs started before keep working (resume, steps, end), and Home's "Continue
   where you left off" still lists them. `/wizards/` lists the Guided Tasks and those runs. The project page's wizard
   bar, the estimating start page's and the New Project form's wizard bars are replaced by Guided Task links;
   Project Created's "Start Guided Estimating" → Price This Job, "Create Another Project" → Set Up Another Project.
   Home's **Start something** band: Set Up This Project · Price This Job · Review This Estimate (no Continue manually
   fork); `data-start-wizard` and `data-home-start-estimate` stay on the task that took over the job.
   `WIZARD_STEP_LEDGER` records where every step went.
5. **Field Today** (`field/today.html`): the date, returned time and "Before you finish today", then **one list of
   today's work** with ONE primary (the first card's Enter time; with no work, Capture on the chosen job or Choose
   Project), banked hours, then a closed **More for today** (Log time, Extra work, My time, Shop / Company Work,
   Change project, Print, help). The seven quick actions stay (Magnificent Seven, owner approved).
   `FIELD_ONLY_ALLOWED_ENDPOINTS` unchanged.
6. **Supplier Hub**: registry scope `supplier` (`SCOPE_SUPPLIER`, never on the office list) and
   `assemble_for_supplier`; provider `supplier_calisign_awaiting`: purchase orders and delivery changes on CaliSIGN
   (status SENT) whose store participant has not signed, for that store only. Shown as "Waiting for your signature"
   on the Supplier Hub attention panel with Review and Sign links; not added to the panel's total (each is also an
   order to confirm or a change to answer).
7. **Surfaced**: the project Next step says "Price This Job" (→ `guided.workflow`) and "Review This Estimate"
   (→ `guided.pricing`); a Ready proposal (built on approval) is "Check and send the proposal"; the attention item
   "estimate ready for your approval" opens Review This Estimate.

### Wizard steps, before → after
- Before: 4 linear wizards, **44 steps** (5 + 15 + 12 + 12); audit: 28 automatable/removable/mergeable.
- After: the three contractor wizards (32 steps) are retired as linear runs. Their **21 A/R/M steps** are automated,
  removed or merged (New Project 3, Guided Estimating 10, Manage a Project 8); their **11 K steps** (human decisions)
  live on 3 Guided Task screens + the project Next step and the existing proposal / schedule / purchasing / change /
  close pages. Contractor linear wizard steps offered: **32 → 0**. The Supplier Pro Desk wizard (12 steps, 7 A/R/M)
  is unchanged in this slice (ruling C6). Total linear wizard steps offered: **44 → 12**; A/R/M steps done: **21 of 28**.

### Screens simplified
Home band, Set Up This Project (New Project form + the 5-step wizard → 1 screen), Price This Job (workflow page +
wizard steps 1–10), Review This Estimate (pricing page + wizard steps 11–13; 3 approval buttons → 1), the estimating
start page (Price This Job: choose the job), Project Created, the project page's wizard bar, `/wizards/`, Field Today,
the Supplier Hub attention panel. Visible on each Guided Task screen (walk, desktop 1280 px, page body only):
Set Up This Project 1 button (Create the project) and 1 link (Cancel) beside the job's questions, 12 settings closed
(was 29 fields and Save Project, all open); Price This Job 10 links, 0 buttons (was 1 primary + 6 secondary links + the wizard
bar's 2); Review This Estimate 11 links, 4 buttons with ONE primary, Approve Estimate (was 3 primary-styled steps:
Approve the costing, Apply the company pricing policy, Prepare the proposal); Field Today (390 px) 7 links, 4 buttons
with ONE primary (was a primary per scheduled card plus Capture, and every job button open). Each Guided Task screen has exactly one primary action.

### Rulings
- C1 **Gate 1 single action**: the costing approval and the pricing are run inside the one Approve by their own
  services (the audit's "software checks", 3.8); the estimator's decision is Approve with the figures shown. The
  separate buttons stay (closed). No commercial rule changes: the pricing applied is the company's method with the
  job's own labour rate and margin, exactly as "Apply the company pricing policy" applied it.
- C2 **Approve what you saw**: the Approve carries the customer total shown; a different priced total refuses and
  nothing is approved.
- C3 **Retired wizards keep in-flight runs**: no new run from the web; existing runs can be finished or closed. Tests
  and walks that check the runner open such a run (tests use the same service; walks use `tests/wizard_run_seed.py`
  in the walk's own temporary database) — same checks, new navigation.
- C4 **Set Up defaults**: blank settings are filled from the same defaults the form and wizard always pre-selected
  (`SET_UP_SETTING_DEFAULTS`); sent values are validated as before. The permit class is the default class (deriving
  it from the address needs municipal data: deferred).
- C5 **Field Today**: the seven quick actions and banked hours stay visible (owner decisions); only the secondary job
  buttons, print and help are closed. The texts consent question (one-time) is its own card.
- C6 **Deferred**: Price This Request (supplier) and the Supplier Pro Desk wizard retirement; Get Customer Approval,
  Award This Subcontract, Buy What's Needed, Schedule, Change and Close as Guided Task screens (their next steps
  already open the existing pages); permit class from the address. No schema need was found.

- C7 **Found while running the whole suite** (both predate this branch, both fixed): the Documents and Equipment
  history printed raw UTC clock times (`test_office_local_time`) — now `local_time`, as every office page; the Documents
  walk looked for a sidebar link that the Task-First menu moved to More — it now opens More (same check).

### Tests (1 Nov 2026, cloud workspace shared with other agents; commands per AGENTS.md)
- `tests/test_guided_tasks.py`: **23 passed** (band, retired starts GET/POST, in-flight runs, step ledger, Set Up
  screen/defaults/validations/new customer/no drawings/estimate start, Price This Job, Review This Estimate, Approve =
  Gate 1 record + lock + proposal, refusal on changed figures with nothing kept, refusal while unpriced, review list,
  Next step and attention, Field Today, the supplier provider's scope, the Supplier Hub signing item).
- Full suite, one log per file (`venv/bin/python -m pytest -q -p no:warnings -p no:cacheprovider <file>`, Family 05
  master env set), every file re-run at the final code where a later change could touch it: **328 files, 3,926 tests:
  3,915 passed, 11 skipped (the office-Mac-only historical workbook tests), 0 failed.** Updated assertions (each with a
  comment and equivalent coverage): `test_wizards` (band, Project Created, the run helper `_start` creates the run with
  the same service), `test_project_creation_ux`, `test_selected_work`, `test_home_planning`, `test_guided_estimating`,
  `test_projects_visual`. `test_concrete_calculator_access` and `test_stair_calculator_access` failed once while the
  machine was at load ~7 on 2 CPUs (their page server must start within 20 s) and passed on the re-run; not changed.
- Browser (`EVIDENCE_EXECUTABLE=… EVIDENCE_REPO=… node --test --test-reporter=tap --test-force-exit
  --test-concurrency=1`): **all 28 `tools/release/evidence_*.mjs` walks, 316 checks passed, 0 failed** (302 + identity
  gate 3's 1 at Slice A, + Documents 4, + the new **`evidence_guided_tasks.mjs`: 9 checks**); `tests/e2e/contractor_workflow.mjs`
  and `tests/e2e/job_lifecycle.mjs` pass. Walks changed for the new navigation (same checks): wizards, project_creation,
  compact_new_project, selected_work (open a run started before the retirement via `tests/wizard_run_seed.py`),
  guided_estimating, first_day, magnificent_seven, time_payroll, documents, both e2e walks; helpers in
  `evidence_task_first.mjs` (`seedWizardRun`, `openSetUpSections`, `openFieldTodayMore`); `evidence_common.mjs` and
  `hosted_postcheck.py` untouched. The project-creation walk's 25 MB upload-limit file gets a 120 s transfer
  allowance (it timed out at the 15 s default on the loaded workspace; the check is unchanged).

## Review fixes (branch `task-first/review-fixes`, 1 Nov 2026)

Independent code review of `feature/task-first-rdims-2026-10-31` @ 26a37fea; every finding re-verified in code before
fixing; a failing test first for each (the new tests were run against the pre-fix code and failed, except the guards
that pin behaviour already correct). The only migration stays `t7a8b9c0d1e2` (unchanged); `evidence_common.mjs` and
`hosted_postcheck.py` untouched (checksums still match `PROVEN_HELPERS`).

### Fixed
- **C1 (critical) release check vs. the FTS5 index.** `migration_check.py snapshot()` ordered every table by rowid;
  `document_search_idx` / `document_search_config` are WITHOUT ROWID ("no such column: rowid"), and FTS5 writes 3
  rows when created, so "new tables are empty" could never pass: the gate rehearsal of this release, and every later
  release's before-snapshot, would stop. Now `search_index_tables()` finds virtual tables (`sqlite_master`
  `CREATE VIRTUAL TABLE…`) and their shadow tables (`<vt>_data/_idx/_content/_docsize/_config`, plus the FTS3/4 and
  R*Tree suffixes) and treats them as a search index: counted and reported (`SEARCH_INDEX_NEW=`, `SEARCH_INDEX=`),
  not row-hashed, not in `--new-tables`, not in "new tables must be empty". An ordinary WITHOUT ROWID table is
  fingerprinted in primary-key order (and keyed by its primary key in the filled-column check). New read-only mode
  `count-rows` (`TABLES=n ROWS=n` without sqlite_* and the index, then `SEARCH_INDEX=TABLES=n ROWS=n`): the release
  gate counts the backup with it (state file `BACKUP_ROWS` + new `BACKUP_SEARCH_INDEX`) and `postrelease_check.sh`
  counts the live database with it (the same file piped over SSH, `count-rows --live`), so both sides count the same
  tables; `hosted_postcheck.py`'s own `TABLES=` line (every table) is no longer the comparison. `postcheck-rows` is
  unchanged (it now receives index-free totals on both sides). Rehearsal on a synthetic s6f7a8b9c0d1 copy:
  `EXISTING_TABLES_UNCHANGED=226 tables, 71 rows, schema and every row identical`; `NEW_TABLES=` the 8, `(empty)`;
  `SEARCH_INDEX_NEW=document_search,…_config,…_content,…_data,…_docsize,…_idx (search index; 3 row(s) …)`;
  `count-rows` before `TABLES=227 ROWS=72`, after `TABLES=235 ROWS=72` (+8 tables, +0 rows), `SEARCH_INDEX=TABLES=6 ROWS=3`.
- **I1 person documents.** `ingest.add_link` (also used by "Link it here" and the document page's "Link to") now
  raises a document to PEOPLE when an active PERSON link is added and records a `FIELD_CORRECTED` sensitivity event
  ("Linked to a person: …"; events stay insert-only). Defence in depth: `access.scope_filter` hides any document with
  an active PERSON link from a viewer who is not a people administrator (lists, FTS and LIKE search, attention,
  opening); `labels_for_documents(include_people=False)` leaves person labels out for them (search rows, document page,
  duplicate prompt, document attention); ending a PERSON link needs `may_see_context_kind` (404 otherwise). The FTS
  `labels` column still holds person names (people administrators search by them) — it can only match documents the
  viewer's scope already allows, so it never reaches a non-administrator (tested).
- **I2 attention cost.** (a) `count_for` (the bell) answers from a 60 s per-person, per-day cache kept per app process
  (`current_app.extensions`); `assemble()` of the full list for today (Home, the full list, Purchasing, Time & Money)
  primes it, so those pages' bell needs no second assembly; the attention list itself is always assembled fresh.
  (b) `AttentionContext.project_id`: the Project page and Price This Job pass it; material requests, delivery
  exceptions, job updates, punch list, guided estimates (Gate 1, subcontract quotes), calculator results and intakes,
  subcontract quote evidence, prices missing, CaliSIGN and change-order drafts filter by project in SQL; time, documents
  and failed crew texts (items never tied to one project) are skipped there. Result identical (tested against the
  org-wide list filtered by project). (c) `_supplier_prices_missing`: one aggregate COUNT over sections/lines/cost
  items for the draft versions (same rule) instead of lazy loads per section, line and cost item; `subcontract_quotes`
  prefetches versions and lines in one query each; `missing_time` reads the window's schedule items (assignments and
  workers eager-loaded) and time entries once instead of per day.
- **I3 extraction on open.** `ensure_extracted` skips a file over `MAX_SYNC_BYTES` (the page shows "Text not indexed
  yet"); `flask documents reindex` now extracts missing text first (`extract_missing`, large files included,
  `TEXT_EXTRACTED=n`) and then rebuilds the index. A concurrent first open's duplicate `DocumentText` insert
  (`IntegrityError`) is rolled back and the page carries on.
- **M2 types.** `file_document` refuses a type not offered for the filing context (`types_for_context`), with a plain
  message. `correct_field("document_type")` moves the sensitivity with the type when the document held its old type's
  default (an invoice → FINANCIAL, back → STANDARD; audited), keeps an administrator's explicit choice, and never goes
  below PEOPLE while a PERSON link is active.
- **M3 subcontractor code.** Generated codes keep `code + "-N"` within 30 characters. **Ruling:** `POST /subcontractors`
  stays open to any office member (office scope), the same as Scope delivery, where recording a subcontractor's quote
  creates the subcontractor; there is no narrower permission for managing subcontract parties.
- **M4 migrate rerun.** `release_migrate.sh` on `ALREADY_MIGRATED`: keeps a `MIGRATION_SEEDED` already in the state
  file; otherwise records it empty when no `--populated-tables` were declared; otherwise recovers it from the first
  apply's saved report (`$GEN/<label>-migrate-*-migrate.txt` with `MIGRATE=ok` and `POPULATED_TABLE=` lines); with no
  such report it stops and tells the operator to send Claude the status file (counts then read from the instance's
  pre-migration backup with Joel). Not needed by this release (no populated tables) but fixed for the next.
- **M5 owner reminder.** `reminders.owner_items` counts from the items, leaving out the providers the Task-First list
  added under an owner-reminder kind (`change_order_drafts`, the only one); the owner's text/email counts are exactly
  those before 31 Oct; the draft stays on the attention list.

### Release-gate migration arguments (this release)
`--migration-to t7a8b9c0d1e2 --new-tables organization_equipment,organization_equipment_events,documents,document_versions,document_links,document_dates,document_events,document_text`
— no `--altered-tables`, `--altered-checks`, `--filled-columns` or `--populated-tables`. Do **not** list
`document_search` or its shadow tables: the check finds them and reports them on `SEARCH_INDEX_NEW=` (whether or not
the SQLite build has FTS5, the arguments are the same). Expected post-release: live `TABLES` = backup + 8, `ROWS` =
backup rows (before `connect-existing`), search index on its own line.

### Tests (1 Nov 2026)
Commands per AGENTS.md (`venv/bin/python -m pytest -q -p no:warnings <files>`, Family 05 master env set; no xdist):
- New: `tests/test_migration_check_search_index.py` (10: real FTS5 rehearsal s6f7a8b9c0d1 → t7a8b9c0d1e2, FTS tables
  refused as `--new-tables`, a real row in a new table still stops, next-release snapshot of an indexed database,
  `count-rows` local and piped `--live`, apply + `count-rows` + `postcheck-rows` end to end vs. the pinned hosted
  post-check, ordinary WITHOUT ROWID table, scripts use the helper); `tests/test_release_postcheck_seed.py` +4 (M4
  rerun: keep, empty, recover from the first report, stop with an instruction); `tests/test_documents_review_fixes.py`
  (16: I1 ×6, I3 ×3 incl. reindex, M2 ×5, M3 ×1, labels); `tests/test_attention_review_fixes.py` (8: M5 ×2, statement
  count does not grow with sections/lines/cost items, prices-missing rule pinned, project list identical and cheaper,
  bell cache TTL/fresh list, per person + primed, narrowed/backdated lists never prime).
- Release tools: `test_migration_check_search_index.py`, `test_migration_check.py`, `test_release_tools.py`,
  `test_release_postcheck_seed.py`: **47 passed**; `test_release_postcheck_seed.py` after M4: **13 passed**.
- Documents: `tests/test_documents_*.py`, `test_uat3_workflow_documents.py`,
  `test_customer_documents_no_internal_costing_20261024.py` at the final code: **164 passed**.
- Attention / reminders: `test_attention_review_fixes.py`, `test_company_attention_fg035.py`,
  `test_core_close_slice_b_fg035.py`, `test_documents_attention.py`, `test_guided_tasks.py`, `test_magnificent_seven.py`,
  `test_project_creation_ux.py`, `test_project_needs_attention_fg035.py`, `test_quickbooks_project_sync.py`,
  `test_supplier_hub.py`, `test_task_first_ux.py` at the final code: **221 passed**.
- Browser: `evidence_documents.mjs evidence_guided_tasks.mjs` (`--test-concurrency=1`): **13 passed, 0 failed**.
- Full suite not re-run here (shared machine with a running browser-walk job); the release gate runs it.

### Deferred from the review (M1)

- M1 (minor): a file uploaded but never filed stays on disk under the documents storage folder. It is not in the database, not searchable and not shown to anyone, so nothing leaks. Deferred to a cleanup command (`flask documents sweep-unfiled`) in a later release, because deleting user files needs its own reviewed rule (age threshold, dry run first). Nothing is deleted automatically in this release.

### Release gate stop, 1 Nov 2026 (tf1)

- The gate stopped correctly: "an existing migration file was changed or removed: migrations/env.py". The documents work had added an `include_object` hook there so that `flask db migrate` (autogenerate) ignores the FTS5 `document_search` table and its shadow tables. It is a developer-time convenience only; no upgrade, test or app path uses it.
- Fix: `migrations/env.py` restored exactly to the live version. The release adds one migration file and changes no existing one.
- Note for the next person who runs `flask db migrate`: autogenerate will propose dropping `document_search*` tables because they are not models. Delete those lines from the generated file. Adding the hook back belongs in its own release, declared as a change to an existing migration file.

### Release gate stop 2, 1 Nov 2026 (tf1): Python 3.9

- The Mac regression ran 3,986 tests on Python 3.9.6 (production's version): 3,985 passed, 1 failed. `test_document_modules_import_only_calibrayt_stdlib_and_locked_packages` used `sys.stdlib_module_names`, which only exists from Python 3.10. The container's runs used Python 3.13, so it passed there.
- Fix: the test decides "standard library" with a 3.9-safe check (`_is_stdlib`: `sys.stdlib_module_names` when present, otherwise where the module is installed), with its own test.
- Guard: new `tests/test_python39_compat.py` parses every Python file under app/, tests/, tools/ and migrations/ with the 3.9 grammar and refuses standard-library APIs that need 3.10 (`sys.stdlib_module_names` unless read through getattr/hasattr, `zip(strict=)`, `dataclass(slots=/kw_only=)`, `itertools.pairwise`, `bisect(key=)`). It flags the old line 71.
- Both files pass on Python 3.9.6 (a locked-package 3.9 environment in the container) and on 3.13.

## Viewport-first density corrective (2 Nov 2026)

Branch `feature/viewport-density-2026-11-02` from the live commit `ec80e6f1`. Mandate: "AIRIA-DENSITY UX CORRECTIVE
RELEASE" (acceptance finding UX-DENSITY-001, Set Up This Project). Audit, AiRIA areas inspected, the reusable rules
and the plan: `docs/ux/viewport-density-audit-2026-11-02.md`. No migration, no model or schema change, no route,
form-field name, data-* hook, permission or governed action changed. Measured by the new browser walk
`tools/release/evidence_density.mjs` (server `tests/density_page_server.py`), Chromium, 100% zoom, laptop 1280 x 800
(the gate), 1280 x 720 recorded, phone 390 x 844. The baseline was taken with the same walk on the ec80e6f1 screens
(`DENSITY_BASELINE=1`) before any change.

### Shared changes
- `tokens.css`: header 64 -> 52 px; density tokens `--control-height` 38, `--control-pad-y/x` 6/10, `--label-gap` 4,
  `--field-gap-y/x` 10/14, `--stack-gap` 12, `--card-pad-y/x` 10/14, `--workspace-pad-top/bottom` 12/32. Touch targets
  stay 44 px on coarse pointers and at 720 px and below; no text below `--text-sm`.
- `task-screen.css`: the Task Screen blocks use the padding tokens (context, next step, state, attention, details);
  12 px screen gap; one-line purpose; `title_in_header` (the top bar's title is not repeated on a laptop); 38 px
  summaries on a mouse laptop. New shared layout: `.ts-details-grid` (closed sections side by side, opened one full
  width, one-line hints with a tooltip), `.ts-cols`/`.ts-col` (two working columns at >= 1100 px), `.ts-form`
  (light groups with inline legends, `.ts-row`, `.ts-inline`, `.ts-optional`, `.ts-actions`). Office form controls
  (`:where`, so component rules still win): label 20 -> 10 px, input margin 8 -> 4 px, padding 11-12 -> 6 x 10 px,
  `.form-panel` 22-28 -> 16 x 20 px. Compact flash messages; link-hub tiles 56 -> 44 px.
- `partials/task_screen.html`: `purpose(..., title_in_header=False)`; details hint carries a `title`.
- `guided-estimating.css`: task-screen cards (padding, headings, progress bar, badges, totals as a 2 x 2 grid).
- `v1-refinement.css` / `estimates/_project_pricing.html`: project pricing in compact rows (rate, margin, HST; winter;
  reason and Save), figures beside them; the winter explanation is the checkbox tooltip. Same fields and names.
- `field.css`: 44 px quick actions (were 52), tighter day navigation, header and work card.
- `calendar-months.js`: the month box is measured again on `load` (it was sized before the page finished loading and
  ended about 40 px below the window).

### Chrome changes
- Header 52 px. Below 1440 px the company box and the signed-in name collapse to icons (names stay as tooltip and
  accessible name; the company name is also at the top of the menu), so "Review This Estimate" is no longer cut off.
- Workspace top padding 12 px, bottom 32 px. Sidebar unchanged (six destinations + More already AiRIA-like).

### Screens reconstructed and progressive disclosure
- **Set Up This Project** (`projects/form.html`): one compact form. The customer choice and the customer on one row;
  with "A customer we have" the new-customer fields are hidden (not removed); with "A new customer" only name (marked
  *), email and phone (optional) on one row and the customer list and "Same as the customer's address" are hidden;
  switching back keeps what was typed. The job on one row (name, what is built, Client Project #); the role as one
  row of choices; the description behind "Add a description (optional)"; the five job-site fields on one row; the
  address as written behind its disclosure; the four plan choices as one row (their explanations are tooltips on a
  laptop and stay visible on a phone); settings four to a row with the reason in the grid. Optional parts open on
  their own when the screen comes back refused with something typed there; the settings open when a setting differs
  from the default or the refusal is about a setting (`settings_problem` from the route on
  `CommercialContextValidationError` / `ProjectLeadError`). The Brayman Project # note sits beside Create.
- **Price This Job**: two columns (next step, waiting calculations, work list | progress, counts, totals); the closed
  sections three across.
- **Review This Estimate**: decision, then the compact pricing (figures and rates in view), then what Calibrayt knows in
  two columns, closed sections three across.
- **Project page**: the 12 closed parts three across (one-line hints); the jump strip, which named the same parts, shows
  only below 900 px where the parts stack; fixed the doubly escaped "Scope &amp;amp; Estimate" headings.
- **Documents library**: the three date filters behind "Dates" (open on their own when one is set); tighter browse
  line and filter row. Context pages unchanged (they already fit).
- **Field Today** (phone): the one-time "Get a text" question moves below today's work (still asked on the screen); the
  template whitespace that put two empty lines above the job address is trimmed.
- Repeated explanatory blocks removed from view: the duplicate task title on Set Up / Price This Job / Review This
  Estimate (laptop), the project page's duplicate section strip (laptop), the four plan-choice explanations (laptop,
  as tooltips), the winter explanation (tooltip), the separate Project Lead note (merged into the settings note).

### Guided Task changes
Price This Job and Review This Estimate keep ONE primary action and every hook; Set Up This Project asks only the
branch that applies. No Gate 1/2/3, CaliSIGN or approval logic changed.

### Before / after at 1280 x 800 (task = bottom of the active task; scroll = page scroll)

| Screen | Before fits | Before task / scroll | After fits | After task / scroll | Remaining scroll, reason |
|---|---|---|---|---|---|
| Home | YES | 594 / 108 | YES | 578 / 59 | 59 px: Today and Coming days reference below the task |
| Attention | YES | 290 / 0 | YES | 274 / 0 | none (a long list scrolls) |
| Projects | YES | 725 / 0 | YES | 705 / 0 | none (fits at 720 now too) |
| Set Up This Project (customer we have) | **NO** | 1952 / 1255 | **YES** | 673 / 0 | none |
| Set Up This Project (new customer) | **NO** | 1952 / 1255 | **YES** | 699 / 0 | none |
| Project page | YES | 296 / 710 | YES | 254 / 0 | none |
| Price This Job (priced) | **NO** | 978 / 558 | **YES** | 426 / 0 | none |
| Price This Job (to price) | **NO** | 1031 / 545 | **YES** | 528 / 0 | none |
| Review This Estimate | YES (decision only) | 366 / 989 | YES (decision + figures) | 553 / 88 | 88 px: closed sections below the task |
| Documents library | YES | 757 / 461 | YES | 574 / 254 | 254 px: the document list itself (9 documents) |
| Project / customer / supplier / subcontractor / person documents | YES | 418 / 0 | YES | 394 / 0 | none |
| Equipment | YES | 506 / 0 | YES | 490 / 0 | none |
| Purchasing | YES | 354 / 0 | YES | 310 / 0 | none |
| Time & Money | YES | 490 / 0 | YES | 398 / 0 | none |
| Calendar | NO (marginal)\* | — / 274 | YES | 794 / 206 | 206 px: the colour key below the month box; months scroll inside their box by design |

\* The baseline selector measured the whole calendar workspace (1003 px); with the month box itself it ended about
40 px below the window (838 px measured after the shared header change, before the `load` fix).

At 1280 x 720 every screen's active task also fits after the change (before: Set Up, Price This Job, Projects,
Documents library and Calendar did not).

### Set Up This Project (UX-DENSITY-001) before / after
- Customer we have: page 2055 -> 800 px; Create at 1952 -> 673 px; 0 px scroll (was 1255).
- New customer: Create at 1952 -> 699 px; 0 px scroll.
- Refused (no customer name): Create at 2015 -> 746 px; 7 px scroll; the new-customer name is in view with what was
  typed kept.
- Optional settings opened: a 4-across block (asserted under 420 px; was a 2-column stack); page 2908 -> 1097 px.
- Refused for a setting (Premium without a reason): the settings open on their own with the reason in view; the reason
  field ends at 983 px, so this state scrolls 345 px (documented, not routine: it is the part with the problem, below
  the task).
- Visible text inputs and selects: customer we have 13 -> 9 (new-customer name/email/phone and the description are
  out of view); new customer 13 -> 11.

### Phone (390 x 844)
- Field Today: today's work and its primary action (Enter time) end at 817 px (was 1503): on the first screen. Seven
  quick actions kept (44 px). No sideways scrolling.
- Home, Set Up, Project page, Price This Job, Review This Estimate, Documents library: one column, no sideways scroll;
  they scroll vertically as phones may. Project page, Price This Job and Review This Estimate show their primary
  action on the first screen.

### Numbers
- Mean page height of the 18 measured laptop screens: 1072 -> 834 px; median page height 800 -> 800 px (most short
  pages already fit). Median bottom of the active task: 455 -> 412 px. Total page scroll across them: 4900 -> 607 px.
- Primary screens needing routine scroll at 1280 x 800: 4 (Set Up, Price This Job, Calendar marginally, Field Today
  on a phone) -> 0. One non-routine state scrolls (Set Up refused for a setting, above).
- Permanently visible fields on Set Up: 13 -> 9 (customer we have).
- Shared components compacted: 11 (header, workspace, form controls, form panel, flash, ts-context, ts-next, ts-state,
  ts-attention, ts-details, link-hub tiles) plus 3 new shared layouts (details grid, two columns, compact form).
- Repeated explanatory blocks removed from view: 6 kinds (listed above).

### Tests (2 Nov 2026)
- New `tests/test_viewport_density.py` (10, written first): the customer branch hides the other branch's fields,
  no-customers case, the page switch script, optional parts closed, refusal opens the settings / description /
  address as written, defaults sent back stay closed, Review keeps the figures out of closed sections after the
  decision, Field Today work before the texts question. 10 passed.
- Affected pytest files (74, per file, `venv/bin/python -m pytest -q -p no:warnings -p no:cacheprovider`, Family 05
  master env set): **1125 passed, 0 failed**.
- Browser: the 27 gate walks + `evidence_density.mjs` (added to `release_gate.sh`): **324 tests** (315 + 9 new).
  Full run: 320 passed, 4 failed — 2 density checks (a `white-space: nowrap` on the new-customer labels made the page
  74 px wider; fixed) and 2 `evidence_training.mjs` sign-in checks (the trainee landed on `/login` after Sign in; the
  training site and the sign-in page are not touched by this branch; `evidence_training.mjs` alone then failed 10/13
  the same way once and passed 13/13 on the next run: a timing flake under load, not fixed here).
  After the fix: `evidence_density.mjs` 9/9; `evidence_training.mjs` 13/13.
- Final full browser run on the branch head (all 28 files above, `--test-concurrency=1`): **324 passed, 0 failed**,
  no server or page errors in any walk.
- Gate: `--browser-expected 324`.

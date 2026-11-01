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
- New tables for the migration check / post-release row step: the 8 above + `document_search` and its 5 shadow tables
  when FTS5 is present (probe production SQLite first). All empty after the migration; rows appear only after
  `flask documents connect-existing` (or the first project Documents page opened).
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
Set Up This Project SETUP_COUNTS; Price This Job PRICE_COUNTS; Review This Estimate REVIEW_COUNTS; Field Today (390 px)
FIELD_COUNTS — each with exactly one primary action.

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

### Tests
TESTS_PLACEHOLDER

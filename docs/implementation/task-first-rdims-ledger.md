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

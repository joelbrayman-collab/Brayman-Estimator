# CalibraytAI Task-First UX Audit

**Date:** 31 Oct 2026
**Branch:** `feature/task-first-rdims-2026-10-31` (worktree `/home/claude/tf`)
**Baseline:** live Production commit `7087d0d0`
**Status:** Audit only. No code was changed. This is the first step of the "Task-First UX" redesign.

**What prompted it:** Kevin Garnett, an experienced residential contractor, called the platform "too busy and convoluted".

**Governing principle:** SIMPLE ON THE SURFACE, POWERFUL UNDERNEATH.

**Three-layer model**

| Layer | The question it answers | What it is |
|---|---|---|
| 1 | What requires me? | What Needs Your Attention |
| 2 | What am I trying to accomplish? | A Guided Task, named for its outcome |
| 3 | Show me the details | The task screen and its details, revealed only when asked for (progressive disclosure) |

**Rule:** Calibrayt does any work it can work out for itself. It never asks the user for a step "because the software needs it". All governed capability stays (section 10).

---

## 0. Numeric summary

| Measure | Now | Proposed |
|---|---|---|
| Templates (all `.html` under `app/templates`) | **333** | — |
| ↳ full-page screens (`{% extends %}` a base) | **237** | ~120 reachable as Task screens or Details; the rest are retired or merged (section 3) |
| ↳ partials (`_*.html`, `partials/`) | 54 | reused as Task Screen blocks |
| ↳ wizard form fragments (`wizards/forms/`) | 19 | reused inside Task screens |
| ↳ base layouts (office, field, supplier, training, site plans, useful calculators) | 6 | 3 (office, field, supplier); training, site plans and useful calculators become skins |
| ↳ standalone print and other templates | 15 | — |
| URL rules (Flask `url_map`) | **636** in 66 blueprints | unchanged (routes are kept and assembled by tasks) |
| ↳ GET only | 241 | |
| ↳ write only (POST) | 288 | |
| ↳ GET and POST | 107 | |
| ↳ human-facing GET pages (not files or API) | ~300 | |
| ↳ project-scoped GET pages | 76 | reached from the project's Next Step and the Task list |
| ↳ API, identity and webhook routes | 23 | |
| Office sidebar destinations (`NAV_SECTIONS`) | **28** (27 links + the "Costs & pricing" section link) in 6 sections | **6 primary** + More + Admin (gear) |
| Office header controls (`base.html`) | 7 (plan, Cal, disabled bell, company, user, password, sign out) | 5 (the bell becomes the attention count) |
| Field navigation | 4 tabs + 3 header links + 6 quick actions | 4 tabs + 1 Capture button |
| Supplier Hub navigation | 4 shell links + 9 per-store pages | 4 |
| Wizards | **4** (`app/wizards/registry.py`) | 0 linear wizards. They are replaced by **10 Guided Tasks** on one Task Screen standard |
| Wizard steps defined | **44** (5 + 15 + 12 + 12) | ~11 task screens hold every human decision |
| ↳ steps that need human judgment (keep) | 16 | |
| ↳ steps that are software-needs (automate or derive) | 6 | |
| ↳ redundant steps (remove) | 4 | |
| ↳ steps to merge into another task or into an attention item | 18 | |
| **Steps that can be automated, removed or merged** | **28 of 44 (64%)** | |
| Project-creation fields that are software-needs | 10 of ~23 visible inputs (commercial type, status, permit class, 6 commercial settings, estimate stage) | defaulted and hidden |
| Attention item types surfaced today (`app/services/needs_attention.py`) | 21 item variants + 6 Company Attention fact types, in 11 kinds | +21 governed events (section 5.3) |
| Pages that say "attention" | 3 (`/`, `/operations/attention`, `/company-attention`) + Supplier Hub | 1 office list (Home), 1 supplier list |

---

## 1. Inventory method

- **Routes:** `create_app({"TESTING": True, ...})` was run and `app.url_map.iter_rules()` was enumerated (script kept out of the repo). Counts are by blueprint (endpoint prefix).
- **Templates:** `find app/templates -name "*.html"`, split into full pages, partials, wizard forms, bases and standalone templates.
- **Navigation:** `app/navigation.py` (`NAV_SECTIONS`), `app/shell.py` (visibility filters), `app/templates/partials/sidebar.html`, `app/templates/base.html` (header), `app/templates/field/_field_nav.html` and `field/base.html`, `app/templates/supplier/base.html`.
- **Wizards:** `app.wizards.registry.all_wizards()` was enumerated, with every `Step` (`key`, `title`, `what`, `do`, `required`, `applies`, `handle`).
- **Attention:** `app/services/needs_attention.py::assemble`, `app/services/company_attention.py`, `app/services/supplier_insights.py::attention`, and the model status constants under `app/models/`.
- **Internal terms:** a script removed Jinja comments, expressions, `<style>`/`<script>` blocks and tags, then counted the visible template text, plus the string constants in `app/presentation/contractor_copy.py`.

### 1.1 Routes by blueprint (largest first)

| Blueprint | Rules | GET | Write | Area |
|---|---|---|---|---|
| plan_intelligence | 39 | 15 | 27 | Drawings, sheets, measurement, takeoff |
| estimates | 37 | 15 | 27 | Estimate, versions, calculations, quantities |
| field | 34 | 29 | 12 | Field crew (phone) |
| supplier_portal | 28 | 17 | 15 | Supplier Hub |
| projects | 26 | 19 | 16 | Project hub and project sub-pages |
| supplier_office | 25 | 8 | 19 | Purchasing: supplier requests, commitments, deliveries |
| supplier_pro_desk | 25 | 13 | 17 | Supplier PRO Desk |
| labour_engine | 24 | 15 | 13 | Labour standards and calibration |
| work_structure | 24 | 2 | 22 | Work plan and work catalog |
| training | 21 | 12 | 10 | Training and UAT Centre |
| accounting | 16 | 13 | 10 | Invoices, receipts, QuickBooks Online |
| schedule | 16 | 9 | 13 | Company Calendar, planning and Gantt, appointments |
| guided | 14 | 10 | 5 | Guided Estimating pages |
| calculators / useful_calculators | 13 / 13 | 11 / 12 | 9 / 9 | Office calculators and the iPhone calculators app |
| payroll_time / time_entry | 13 / 8 | 7 / 3 | 9 / 6 | Time approval, banked hours, QuickBooks Time |
| proposals / proposal_templates / proposal_link | 13 / 6 / 5 | 8 / 4 / 3 | 7 / 4 / 2 | Proposals and customer acceptance |
| operations | 12 | 10 | 7 | Attention list, material requests, job updates, deliveries, extra work |
| project_controls | 11 | 7 | 7 | Change orders |
| deck_takeoff, scope_delivery, supplier_package, package_controls | 10 / 10 / 10 / — | | | Takeoff and scope handoffs |
| signing_office / sign | 9 / 5 | 1 / 3 | 8 / 2 | CaliSIGN (office actions and the signing ceremony) |
| wizards | 9 | 7 | 4 | Wizard runner |
| 40 smaller blueprints | ≤9 each | | | Settings, people, crews, clients, costs, assemblies, pricing engine, site plans, walkthrough, punch list, etc. |

### 1.2 Templates by folder

wizards 29 · supplier 28 · projects 28 · field 28 · training 21 · operations 15 · labour_engine 14 · estimates 13 · accounting 13 · partials 12 · schedule 11 · plan_intelligence 11 · guided 11 · auth 9 · settings 7 · proposals 7 · payroll_time 7 · calculators 7 · useful_calculators 6 · suppliers 6 · site_plans 6 · pricing_engine 4 · 22 folders with 1–3 each.

### 1.3 Roles and permissions (`app/services/access_domains.py`, `instance_authority.py`)

| Role in code | How it is set | What it changes in the UI |
|---|---|---|
| Instance owner | `instance_authority.is_instance_owner` | Close/reopen, zero-cost decisions, People & Access, appointing administrators |
| System Administrator | `is_system_administrator` | Same as owner for People & Access and closing |
| COMPANY_MANAGEMENT access domain | `RECOGNIZED_STORED_DOMAINS`, the only stored grant | "Attention" nav item and the Company Attention facts |
| Office member (default) | membership without FIELD_ONLY | All office pages; scheduling authority (`has_office_scheduling_authority`) |
| Office financial access | `has_office_financial_access` | Receipts and QuickBooks attention items |
| FIELD_ONLY restriction | `set_field_only`; allowlist `FIELD_ONLY_ALLOWED_PREFIXES = ("field.",)` + `FIELD_ONLY_ALLOWED_ENDPOINTS` | Only `/field`, useful calculators and site plans; office pages redirect to `/field/today` |
| Supplier membership | Supplier Hub sign-in (`supplier_portal.login`), one or more stores | Supplier Hub and PRO Desk only |
| External parties (customer, subcontractor) | One-time credentials: `/proposal/<c>`, `/sign/<c>`, `/walkthrough/<c>`, `/quote/<c>` | No account |

**Finding R-1.** There is no project-manager, purchasing or estimator role in code. Every office member sees the same 26–28 sidebar items. A Task-First IA should filter the **attention list and the Task list by role**; it should not simply hide pages. Recommendation: derive a *view preference* (Owner/Estimator, Project Manager, Office/Purchasing) from the membership. It changes ordering and defaults only, never permissions, so governance is untouched.

**Finding R-2.** There is no subcontractor portal. Subcontractors are reached only through quote-request sheets (`scope_delivery.labour_quote_request`) and CaliSIGN. That is correct for V1. "Award This Subcontract" stays an office task.

---

## 2. Navigation audit

### 2.1 Office sidebar today (`app/navigation.py`)

| # | Section | Item | Endpoint | Class | Proposed home |
|---|---|---|---|---|---|
| 1 | — | Home | `main.dashboard` | **primary** | **Attention** (Home, renamed) |
| 2 | — | Calendar | `schedule.company` | **primary** | **Calendar** |
| 3 | — | Projects | `projects.list_projects` | **primary** | **Projects** |
| 4 | — | Clients | `clients.list_clients` | **primary** | **Customers** |
| 5–14 | Calculators (10) | Concrete, Stair, ICF wall, Employment vs Entrepreneurship, Wall framing, Footing, Roofing, Siding, Drywall, Flooring | `calculators.*` | **contextual** (opened from a work item in Price This Job) / **reference** | More › Calculators (one page with a tile grid). Employment vs Entrepreneurship is **redundant** with `decision_tools.employment_vs_entrepreneurship` and becomes More › Business tools |
| 15 | Costs & pricing (section link) | Costs & pricing | `costs_and_pricing.index` | **reference** | More › Prices & costs |
| 16 | Costs & pricing | What we pay | `cost_library.list_cost_items` | **reference / advanced** | More › Prices & costs |
| 17 | Costs & pricing | Reusable work | `assemblies.list_assemblies` | **advanced** | More › Prices & costs |
| 18 | Costs & pricing | How we price | `pricing_engine.index` | **administrative** | Admin › Pricing policy |
| 19 | Proposals | Templates | `proposal_templates.list_templates` | **administrative** | Admin › Document templates. The section title "Proposals" over a single Templates link misleads: there is no proposal list in the nav |
| 20 | Company library | Past jobs | `historical_estimates.index` | **reference** (calibration) | More › Past jobs |
| 21 | Company | Getting started | `getting_started.index` | **advanced / onboarding** | Shown as a Home card until finished, then More › Help |
| 22 | Company | Workflow Guide | `workflow_map.contractor` | **reference** | More › Help |
| 23 | Company | Attention | `company_attention.index` | **redundant / misleading**: it opens the labour-facts page, not the full attention list (`operations.attention`) | Folded into Attention |
| 24 | Company | People & Access | `people_access.index` | **administrative** (owner/SA) | Admin |
| 25 | Company | Crews | `organization_crew.index` | **administrative** | Admin › People |
| 26 | Company | Suppliers | `supplier_office.suppliers` | **primary for purchasing / administrative for setup** | **Purchasing** |
| 27 | Company | Accounting | `accounting.index` | **primary for office/finance** | **Time & Money** |
| 28 | Company | Work catalog | `work_structure.catalog_index` | **advanced** | Admin › Work catalog |

**Header** (`app/templates/base.html`):
- **contextual:** View project plan, Cal Find It
- **obsolete:** a *disabled* notifications bell ("coming soon")
- **administrative:** company box → `settings.brand_profile`
- **account:** user name, Change password, Sign out

**Not in the nav but primary in practice:**
- `operations.attention` (the full list)
- `time_entry.review` (approve time)
- `supplier_office.deliveries`
- `estimates.list_estimates`, `proposals.list_proposals`, `project_controls.list_change_orders`
- `operations.material_requests`, `operations.job_updates`, `operations.extra_work`
- `accounting.receipts_inbox`

These are reached only from Home counts, attention links or the project hub.

**Pages with no inbound link from another area** (orphan scan):
- `decision_tools.decision_tools_index`
- `material_catalogue.list_materials`
- `labour_engine.list_tasks|list_standards|list_candidates|list_mappings` (each linked only from other labour_engine pages)
- `accounting.reconcile_time`
- `field.schedule_today`
- `settings.settings_index` (redirects to brand profile)
- `useful_calculators.projects`

### 2.2 Proposed primary navigation (office roles)

| # | Item | Opens | Contains (contextual, not in the nav) |
|---|---|---|---|
| 1 | **Attention** (Home) | `/`: What Needs Your Attention, Today, Coming up | The full list, filters by kind and role, the "Start something" button |
| 2 | **Projects** | `projects.list_projects` → the Project page with Next Step | Estimate, proposal, contract, drawings, schedule, purchasing, change orders, closeout: all inside the project |
| 3 | **Calendar** | `schedule.company` | Appointments, the project planning/Gantt link per project |
| 4 | **Customers** | `clients.list_clients` | Customer detail, their projects and proposals |
| 5 | **Purchasing** | A new cross-project landing that assembles `supplier_office.deliveries`, open `SupplierRequestShare`s, `operations.material_requests`, commitments | Suppliers list (`supplier_office.suppliers`), subcontractors, delivery changes |
| 6 | **Time & Money** | A landing that assembles `time_entry.review`, `accounting.receipts_inbox`, `accounting.invoices`, QuickBooks status | Banked hours, QuickBooks Online/Time pages, reconciliation |
| — | **More** (one link) | Calculators, Prices & costs, Past jobs, Business tools, Help (Workflow Guide, Getting started, Training) | |
| — | **Admin** (gear in the header, owner/SA/COMPANY_MANAGEMENT) | Company profile, People & Access, Crews, Hours policy, Pricing policy, Document templates, Work catalog, Labour standards (`labour_engine.*`), Text-message settings, Calendar feed | |

**Result:** 28 destinations become 6 primary, plus More and Admin.

**Role variants (ordering and defaults only):**
- **Owner/Estimator:** Attention, Projects, Calendar, Customers, Purchasing, Time & Money
- **Project Manager:** Attention, Projects, Calendar, Purchasing, Customers (Time & Money moves under More if there is no financial access)
- **Office/Purchasing:** Attention, Purchasing, Projects, Time & Money, Calendar, Customers

**Field crew** (`field/*`, phone): **Today · Week · My time · Plans**, plus one persistent **Capture** button.
- Move Month and Company Today under Week.
- Move Guide, Texts and Password into a single "Me" menu.
- Field is already the most task-first surface (`field/today.html` leads with the day's job and "Before you finish today" reminders). Keep that pattern and reduce the quick-action row from 6 to 3: Capture, Time, Extra work.

**Supplier** (`supplier/base.html`): **Requests (attention) · Orders & Deliveries · PRO Desk · Account**.
- Dashboard, Demand and Insights move into the Requests page as one "This period" panel.
- Wizards are retired in favour of "Price This Request" (section 4.4).

---

## 3. Screen audit (the 10 questions)

**Key to the columns**
- **Who** is the primary user.
- **Accomplish** is what they are there to get done.
- **Know now** is what they must see immediately.
- **Decision** is the decision or action that belongs on this screen.
- **Primary** is the one primary action.
- **Auto** is what Calibrayt should do itself.
- **Hide** means hide until requested.
- **Impl** means implementation detail that should never show.
- **Exist?** asks whether the screen needs to exist.
- **Verdict:** Combine / Simplify / Contextualize / Retire.

### 3.1 Home: `main.dashboard` → `app/templates/dashboard.html`, `operations/_home_attention.html`, `wizards/_home_strip.html`, `wizards/_home_resume.html`, `app/services/home_planning.py`

**Who:** owner, PM, office.

**Accomplish:** know what needs them today and start the right task.

**Know now:** the attention items that block money or schedule, and today's crews.

**Decision:** which item to handle first.

**Primary:** the top attention item's task button.

**Auto:** rank items by consequence (overdue, blocks a gate, customer waiting) and pre-select the next task.

**Hide:** the pulse counts strip (`view.pulse`), the "What are Wizards?" help, the "Guided Wizards" band.

**Impl:** "Wizard", "Continue manually".

**Exist?:** yes.

**Verdict: Simplify.** Today's Home stacks:
- greeting + calendar link
- attention (4 shown)
- a band of 3 wizards × 2 buttons
- unfinished wizard runs
- an SMS failure banner
- Today/Coming columns
- 5 pulse counts

That is seven competing blocks. Proposed order:
1. **What Needs Your Attention** (top 5–7, each with one task button)
2. **Today on site**
3. a single **"Start something ▾"** menu (New project, Price a job, Record extra work, Add appointment)

The SMS failure banner becomes an attention item. The Company Attention facts are excluded on Home (`include_company_facts=False` in `app/routes/main.py`) but present on `/operations/attention`. Unify them.

### 3.2 Attention pages: `operations.attention` (`operations/attention.html`, `_attention_list.html`) and `company_attention.index` (`company_attention/index.html`)

**Who:** owner, PM, office.

**Accomplish:** clear the queue.

**Know now:** what, which project, why it is waiting, how long it has waited.

**Primary:** the item's own task button.

**Auto:** group by project, collapse duplicates, dismiss resolved items automatically.

**Impl:** the "kind" codes (`time`, `quotes`, `labour`, …).

**Verdict: Combine.** One list with role and kind filters. Retire `/company-attention` as a page and keep the service as one source of facts. The nav item "Attention" currently opens the narrower page, which is a defect in IA terms.

### 3.3 Project list: `projects.list_projects` (`projects/list.html`)

**Who:** all office.

**Accomplish:** find a job.

**Know now:** stage, next step, who is waiting.

**Primary:** open the project.

**Auto:** show each project's derived Next Step (from `project_setup.describe_setup` extended past estimating).

**Hide:** filters until used.

**Verdict: Simplify.** Add a "Next step" column. `estimates.list_estimates`, `proposals.list_proposals` and `project_controls.list_change_orders` stay as **Details** (filtered lists), not destinations.

### 3.4 Project hub: `projects.view_project` → `app/templates/projects/detail.html` (1,425 lines), `app/services/project_hub.py`

**Measured density:**
- 14 forms, ~42 buttons, 84 links
- ~74 panels/sections
- 4 `<details>`
- a lifecycle anchor bar
- a "More about this page" block of 5 explanatory paragraphs

Header actions (all always visible):
- Continue setup
- Drawings
- Scope of work
- Enter/Update construction information
- New Change Order
- Print
- Close

**Sections:** identity · Commercial settings · Money (record actual direct cost, actuals, previous entries) · Documents (Permit & Approvals, Drawings, Sheets, Scale/measurement, Take-off) · Estimates and proposals (Guided estimate, Related Estimates) · Contract (contract status, Related Proposals) · Project work (work plan, final walkthrough, punch list, schedule, purchasing, field operations, calculations, time, labour, change orders, field observations) · LEARN (future).

**Who:** owner, PM.

**Accomplish:** move this job to its next outcome.

**Know now:**
- stage (Lead → Estimating → Proposal Sent → Contracted → Active → Completed, from `app/services/project_stage.py`)
- the one next step
- money (contract value, cost to date, margin)
- schedule (next dates)
- what is waiting on whom

**Decision:** the next step only.

**Primary:** a **state-aware** Next Step. Today it is always "Continue setup" (`projects.project_setup`), even on an Active job. `describe_setup` (`app/services/project_setup.py`) only knows steps up to "Continue the estimate".

**Auto:** derive the stage and next task, the plan button, the customer-incomplete reminder (already present), the work plan build on acceptance.

**Hide:** Commercial settings, Sheets, Scale/measurement, Calculations, Field observations, history, "More about this page". Collapse each to a one-line status with "Open".

**Impl:** "LEARN · Future", "Sheets", "Scale / measurement", "Take-off", "Commercial settings (version N)", "immutable", "baseline".

**Verdict: Simplify + Contextualize.** Rebuild as the Task Screen standard (section 7.2):
- **Context bar:** project #, customer, stage.
- **Next Step card.**
- **Waiting on you / Waiting on others** list (project-filtered attention).
- **Tabs** (not anchors): **Overview · Estimate · Customer · Schedule · Purchasing · Field · Money · Documents**. Each tab is a one-line summary per sub-area with an "Open" link.

### 3.5 Project creation: `projects.create_project` (`projects/form.html`, 253 lines) and the NEW_PROJECT wizard (`wizards/forms/np_*.html`), plus `projects.project_setup` (`projects/setup.html`)

**Who:** owner, estimator, office.

**Accomplish:** get a job on the books.

**Know now:** customer, address, what is being built.

**Decision:** those three things, plus plans if they have them.

**Primary:** Create project.

**Auto:**
- commercial project type (from what is being built)
- status (always Lead)
- permit context class (from the address/municipality and the building type: `permit_foundation`, `jurisdiction`)
- the 6 commercial settings (Pricing posture, Execution risk, Schedule condition, Site condition, Estimate stage, Delivery model), from the company default policy (`app/services/commercial_context.py`)
- Project Lead (default to the creator)
- Brayman Project # (already automatic)

**Hide:** the settings under "Adjust project settings". Ask for Justification only when a non-default posture is chosen (already conditional server-side: `selection_requires_reason`).

**Impl:** "Permit context class", "Pricing posture", "Execution risk", "Estimate stage", "Delivery model".

**Exist?:** two creation surfaces (manual form + wizard) is one too many.

**Verdict: Combine.** One "Set Up This Project" task screen. Retire `projects/form.html` as a separate path. Keep `projects/setup.html` logic as the **Next Step engine**, extended to every stage.

### 3.6 Drawings and documents

Surfaces:
- `plan_intelligence.*` (39 rules, 11 templates): list, upload, view, sheets, measure, takeoff runs, packages, map to estimate
- `construction_drawings.*` (`projects/construction_drawings.html`, previews, DXF/PDF)
- `projects.construction_information`
- `deck_takeoff.*`
- `projects.workflow_documents`
- `projects.view_permit_report`
- `site_plans.*` (PWA)
- `field.drawings`

**Who:** estimator (office); crew (read-only).

**Accomplish:** have current plans attached to the job and get measurements out of them.

**Know now:** the current plan set, whether a drawing is needed, whether the takeoff is ready.

**Primary:** Add plans / View plan.

**Auto:**
- sheet indexing
- revision supersession
- takeoff run fingerprints
- mapping takeoff → estimate lines (`takeoff_estimate_mapping`), offered as a confirmation, not a separate page

**Hide:** sheets, measurement, takeoff runs, packages, fingerprints, SHA, "construction model" under Details.

**Impl:** "Plan Intelligence" (visible in 11 templates), "takeoff fingerprint", "SHA", "canonical", "revision sheets", "construction model member counts".

**Verdict: Combine** into one **Plans & Documents** area per project:
- **Plans:** current set; older versions hidden
- **Drawings we made:** construction drawings
- **Documents:** permit report, workflow documents, contract, signed PDFs

Measurement and takeoff open *from the work item* in Price This Job. `site_plans` and `field.drawings` stay as phone skins over the same data.

### 3.7 Scope

Surfaces:
- `guided.scope`
- `guided/work.html` (selected work)
- `projects.scope_of_work` (`projects/scope_of_work.html`)
- `scope_delivery.review` (`projects/scope_delivery.html`, 281 lines)
- `work_structure.project_work_plan` (`work_structure/project_work.html`, 335 lines, 16 forms)
- `projects.package_controls`

**Who:** estimator/owner.

**Accomplish:** say what work is in this job and who does it.

**Know now:** the work list; for each item, "Is Brayman doing this work?"; if not, by whom (By Others / By Owner-Client / named party); and Internal or Subcontracted.

**Primary:** Confirm scope.

**Auto:**
- suggest work from the project type (`selected_work`, `project_work_package` SUGGESTED)
- general conditions included automatically (Paulusse principle)
- keep quantities and intelligence when a line is excluded (non-destructive exclusion)

**Hide:** lineage, scope origin, packages, routing, delivery-scope status (DRAFT/PROPOSED/CONFIRMED).

**Impl:** "work package", "scope origin", "EXTRA_WORK", "routing", "leaf", "N/A".

**Verdict: Combine** `guided.scope`, `guided/work.html`, `projects.scope_of_work` and `scope_delivery.review` into **one Scope panel** inside Price This Job. The work plan (`work_structure`) becomes Schedule-side Details, generated on acceptance.

### 3.8 Estimating and pricing

Surfaces:
- `guided.workflow`, `guided.stage` (`guided/stage.html`: 19 forms, 19 buttons), `guided.calculation`, `guided.compare`, `guided.internal_cost`, `guided.pricing`
- `estimates.view_version` (`estimates/version_detail.html`: 600 lines, 20 forms, 37 buttons)
- `estimates.calculation_list|review|record`
- `estimates.framing_quantities|footing_quantities|wall_form_quantities`
- `estimate_labour.hours`
- `approved_costs.review`
- `estimates.internal_cost_breakdown`
- `pricing_engine.snapshot_detail`
- `estimate_quickbooks.review` (`projects/quickbooks_entry.html`, 338 lines)
- `supplier_package.*`
- the contractor-package PDF

**Who:** owner/estimator.

**Accomplish:** a correct internal cost and a selling price they trust.

**Know now:** for each work item, status (needs quantities / needs labour / waiting for a quote / done); totals for cost, price, true margin and hours; what still blocks approval.

**Decision:** quantities (via the calculator), labour hours (override with a reason), which quote to use, allowances, and the margin/labour-rate adjustment per project.

**Primary:** per work item, "Next: \<what's missing\>"; at the end, **Approve Estimate**.

**Auto:**
- routing of who supplies/builds each line (from scope + default supplier)
- applying approved supplier prices where they match (`supplier_pricing` step)
- marking a quote "waiting" when the request is sent
- "Use this cost on the line" when a quote is selected
- approving the costing and applying pricing policy (system checks) as part of the single Gate 1 approval
- winter settings from dates/location (`winter_job.py`) as a shown assumption

**Hide:** sections/line-item editor (Details), costing snapshot, calculation intake records, test-load, QuickBooks entry (an office follow-up, not estimating).

**Impl:**
- "Costing snapshot", "snapshot" (visible in 8 templates)
- "intake"
- "Approve the costing" vs "Sign off" vs "Lock" (three words for one gate)
- "pricing policy"
- "GE-" codes
- "allowance record"
- "Calculations waiting for a stage"

**Verdict: Combine + Simplify.** One **Price This Job** task screen: the work-item list on the left, the selected item's calculator/labour/quote on the right, the totals bar fixed. Then one **Review This Estimate** screen, a concise commercial summary with **Approve Estimate** (Gate 1). `estimates/version_detail.html` stays as the Details/"Line items" view. Today there are **three separate human-looking clicks for Gate 1**:
1. "Approve the costing" (`guided/pricing.html`)
2. "apply the company pricing policy"
3. "Sign off / Lock" (`estimates/version_detail.html`)

Only the third is a human decision. The first two are software checks.

### 3.9 Customer proposal, acceptance and contract

Surfaces:
- `proposals.view_proposal|edit|preview` (`proposals/detail.html`)
- `proposal_link.view` (customer)
- `projects.review_contract` (`projects/contract_review.html`)
- `projects/partials/contract_signing.html`
- `sign.ceremony|document|executed` (CaliSIGN customer)
- `signing_office.*` (POST)

**Who:** owner/estimator; the customer.

**Accomplish:** get a signed yes.

**Know now:** what the customer will see, whether it was sent, whether it was opened, whether it was accepted/signed, and when it expires.

**Primary:** Send for E-Signature, then (if a countersign is needed) Review and Sign.

**Auto:**
- build the proposal from the approved version (already done on sign-off)
- generate the contract on acceptance (`contract_generation`)
- Project Commercial Baseline on acceptance (Gate 2)
- reminders

**Hide:** proposal sections editor, brand logo, master SHA, consent version.

**Impl:** "PRESENTATION_MASTER_SHA", "artifact", "immutable", "Generating it does not sign it".

**Verdict: Combine** into **Get Customer Approval**: one screen with the preview, Send, and a status timeline. Joel's stated preference is a single client signing, with acceptance triggering the contract. The MANAGE_PROJECT step "generate and send the contract" makes a second human step that should be automatic or merged.

### 3.10 Purchasing and suppliers (office)

Surfaces:
- `supplier_office.project_requests` (`suppliers/project_requests.html`: 21 buttons, 5 `<details>`)
- `supplier_office.quote_comparison`
- `supplier_office.commitments` (`suppliers/commitments.html`: Subcontracts, Committed cost by work package, Early Procurement Exceptions)
- `supplier_office.deliveries`
- `supplier_office.suppliers`
- `operations.material_requests|material_request`
- `operations.deliveries|delivery`
- `supplier_package.*`
- `deck_takeoff` supplier requests
- `delivery_confirmations`
- CaliSIGN supplier signing

**Who:** office/purchasing, PM.

**Accomplish:** the right material ordered, priced and delivered on time.

**Know now:** for each order, what is needed and by when (from the schedule's procurement windows: `governed_schedule.procurement_plan`), its price status, its order status and its delivery status.

**Decision:** which supplier; approve the price and place the order (Gate 3); answer a delivery change; Early Procurement Exception before Gate 2 (reason, exposure, approver).

**Primary:** Review and order / Send request.

**Auto:**
- every quantity in the supplier request estimated by Calibrayt, never left to the supplier
- unit conversion (Supplier Unit Pricing & Conversion workstream)
- the concrete request kept separate
- choosing the authorized supplier when only one exists
- drafting delivery-change notices when the schedule moves (`ScheduleExternalDraft`)

**Hide:** history, cancelled orders, share numbers, fingerprints.

**Impl:** "share", "commitment", "work package", "Gate 3", "Early Procurement Exception" (keep it as the governed record, but name the action "Order before the customer has signed").

**Verdict: Combine** into **Buy What's Needed** (per project, plus a cross-project Purchasing landing) and **Award This Subcontract**.

### 3.11 Subcontracting

Surfaces:
- the guided stage subcontract block (`guided/stage.html`: "Subcontract")
- `scope_delivery.labour_quote_request`
- `guided.compare`
- `supplier_office.commitments` ("Propose a subcontract")
- `subcontract_quote`, `subcontract_signing` services

**Verdict: Combine** into **Award This Subcontract**:
1. request the quote (sheet/email)
2. record quotes
3. compare
4. select (this auto-applies to the estimate)
5. after Gate 2, propose the commitment
6. approve (Gate 3)
7. CaliSIGN

The same task is opened from the estimate (for price) and from the project (for award).

### 3.12 Scheduling, Gantt and calendar

Surfaces:
- `schedule.company` (`schedule/company.html`: 349 lines, 27 links, 9 `<details>`)
- `schedule.planning` (`schedule/planning.html`: Anticipated start, Preliminary schedule, Gantt, Company Schedule Change Requests, Supplier delivery change drafts, Procurement planning windows)
- `schedule.edit_item|new_item|new_appointment|edit_appointment`
- `schedule.calendar_feed_settings`, `schedule.print_calendar`
- the hub schedule panel (`schedule/_work_order.html`)
- `field.week|month`

**Who:** PM/owner; crew (read).

**Accomplish:** dates everyone can rely on.

**Know now:** conflicts, unscheduled accepted work ("waiting" list), what moves when a date moves (`governed_schedule.impact_analysis`).

**Decision:** confirm windows, approve/reject a change request, send the drafted supplier notices.

**Primary:** Schedule this project / Resolve conflict.

**Auto:**
- preliminary schedule from labour hours and crew size (`preliminary_schedule`, `calculated_duration_days`)
- working-day maths
- procurement windows
- delivery-change drafts
- SMS to crews

**Hide:** dependencies, history, work-order rules (`SCHEDULE_WORK_ORDER`), the calendar feed.

**Impl:** "Company Schedule Change Request", "ANTICIPATED/CONFIRMED window", "work order rules".

**Verdict:** keep the **Calendar** as primary. `schedule.planning` becomes **Schedule This Project**. Change requests and drafts become **Resolve This Schedule Conflict**, opened from attention.

### 3.13 Field (`/field`, 34 rules, 28 templates)

**Who:** crew on a phone.

**Accomplish:** know where to be, log time, capture problems, extra work and receipts.

**Verdict: Keep, light simplification** (see 2.2). Calibrayt already defaults the job from today's schedule (`field.choose_job`, `field.project_confirm`). Keep the "Before you finish today" reminders.

**Impl:** "Capture" vs "Field Observations" (office) vs "field events" (API): one name needed.

### 3.14 Change orders and extra work

Surfaces:
- `project_controls.*` (`project_controls/change_orders/detail.html`)
- `operations.extra_work|extra_work_report`
- `field.extra_work`
- `work_structure` "Add change order work item"
- `project_controls.create_from_estimate_version`

**Verdict: Combine** into **Review This Change**:
1. extra work reported
2. accept as extra
3. price it, using the same work-item pricing as Price This Job
4. send to the customer (CaliSIGN)
5. the approved change updates the baseline and the schedule

Attention already surfaces 4 variants. Each should deep-link to this single task, not to the work-structure page (the current link for "Extra work not on a change order").

### 3.15 Actuals, time and accounting

Surfaces:
- the hub "Money" (record actual direct cost, current actuals)
- `time_entry.review|detail`
- `payroll_time.*`
- `accounting.*` (13 templates)
- `estimate_quickbooks.review`
- `package_controls` (committed vs approved)

**Verdict: Combine** into the **Time & Money** primary area, plus the project Money tab. Approving time is an attention item. The QuickBooks pages are Details/Admin. `projects/quickbooks_entry.html` (338 lines, shows "artifact", "governed", "immutable", "routing") is internal hand-entry support and belongs under Money › QuickBooks entry.

### 3.16 Closeout

Surfaces:
- the hub final walkthrough + punch list
- `walkthrough.form` (customer)
- `projects.close_project|reopen_project` (`projects/close_confirm.html`)
- `ProjectCloseoutRecord`
- `final_walkthrough`, `punch_list` routes (POST only)

**Verdict: Combine** into **Close This Project**:
1. punch list
2. walkthrough invitation and response
3. final costs/actuals check
4. calibration capture (labour actual vs estimate → `labour_engine` candidates)
5. close (owner/SA)

### 3.17 Calibration and the libraries

Surfaces:
- `labour_engine.*` (24 rules, 14 templates: tasks, standards, cost rates, candidates, mappings)
- `historical_estimates.*`
- `cost_library.*`
- `assemblies.*`
- `material_catalogue.*`
- `pricing_engine.*`
- `work_structure.catalog_index`
- `calculation_mapping*`

**Who:** owner, rarely.

**Verdict: Contextualize/Admin.** Calibration candidates should arrive as attention items for the owner ("3 labour rates can be updated from finished jobs") that open a review task.

**Impl** (visible in templates): "Candidate {{id}}", "Promoted production standard", "Evidence refs", "canonical_name", "Source evidence (immutable)", "organization-approved rate". None should be on a contractor-facing surface.

### 3.18 People, settings and admin

Surfaces:
- `people_access.*`, `organization_crew.*`
- `settings.brand_profile`
- `payroll_time.hours_policy`
- `supplier_office.text_settings`
- `sms_notifications.*`
- `schedule.calendar_feed_settings`
- `training.admin`

**Verdict:** move all of these under **Admin** (the gear). "Getting started" stays as a dismissible Home card until done.

### 3.19 Help layers

Today a page can carry six help layers at once:
1. `contextual_help` (every office page)
2. "More about this page" `<details>`
3. "What are Wizards?"
4. Workflow Guide (`workflow_map`)
5. Getting started
6. Cal Find It (header)

The Training site bar adds a seventh in the Training Centre.

**Verdict: Simplify.** One help affordance per screen (the ? in the context bar, which opens contextual help + "Ask Cal"). Remove the "More about this page" paragraphs: they explain implementation ("Scale tools remain in Plan Intelligence. Counts are stored facts only.").

### 3.20 Supplier Hub and PRO Desk

Surfaces:
- `supplier_portal.*` (28 rules)
- `supplier_pro_desk.*` (25)
- `supplier/*` (28 templates)
- `supplier_quote_link.*` (walk-in customer)

**Who:** supplier counter/office staff.

**Accomplish:** price contractor requests fast, confirm orders and deliveries.

**Know now:** `supplier_insights.attention` already gives quotes to price, orders to confirm, contractor delivery changes and upcoming deliveries. It does **not** give CaliSIGN supplier signing requests awaiting signature.

**Verdict: Simplify.** Make Requests the landing page. Retire the supplier wizard. Fold Dashboard and Demand into one panel.

**Impl:** "Availability not confirmed. CalibraytAI holds no stock figures." (wizard copy), "share", "SKU matching: Nothing is filled in for you".

### 3.21 Mobile-specific surfaces

`/field` (crew), `/useful-calculators` (iPhone calculators app, 13 rules, duplicating `/calculators`), `/site-plans` (PWA, 8 rules, duplicating `field.drawings`).

**Verdict:** keep them as separate shells; they are correct for phones. Make sure they share templates and partials with the office versions. The near-duplicate views already share view functions, so this is mainly a template/IA note.

### 3.22 External-party screens

`proposal_link.view`, `sign.*`, `walkthrough.form`, `supplier_quote_link.view`. These are already single-purpose and task-first. **Keep.**

### 3.23 Training and Workflow Map

`training.*` (21 rules), `workflow_map.*`.

**Verdict:** these are reference and need no redesign now. They must be updated in lockstep with the Task names (the training-app sync principle).

---

## 4. Wizard audit

**Classification key**
- **K** = human judgment (keep)
- **A** = software-needs (automate or derive)
- **R** = redundant (remove)
- **M** = merge into another step, task or attention item

Source: `app/wizards/new_project.py`, `estimating.py`, `manage_project.py`, `supplier_pro_desk.py`; runner `app/wizards/framework.py`, `service.py`, `views.py`; templates `app/templates/wizards/**`, `supplier/wizards_*.html`.

### 4.1 Start a New Project (`NEW_PROJECT`, compact modal, 5 steps)

| # | Step | Why are we asking? | Class | Recommendation |
|---|---|---|---|---|
| 1 | Project: name, Client Project #, what is being built, description, **commercial project type**, **status** | Name and what is being built are human. Commercial type and status exist because the model needs them | **K** (+ 2 fields **A**) | Keep name, building type and optional Client #. Derive commercial type from the building type and customer; status is always Lead |
| 2 | Customer | Human | **M** → step 1 | Same screen as step 1 (customer picker + "add new": name only) |
| 3 | Details: address / same as customer, role, Project Lead, **permit context class**, **pricing posture, execution risk, schedule condition, site condition, estimate stage, delivery model**, justification | Address and role are human. The 7 settings are software-needs | **K** (+ 8 fields **A**) | Keep the address and role (default to the company's usual role). Derive the permit class from the address and building type; take the settings from company defaults behind "Adjust project settings"; derive estimate stage; Project Lead defaults to the creator |
| 4 | Plans: upload / no drawings / later | Human, optional | **M** | A drop zone on the same screen; "No drawings needed" becomes a link |
| 5 | Review | Redundant: the Project Created page and the project's Overview already show everything | **R** | Remove |

**Recommendation:** a **Guided Task "Set Up This Project"** on one screen (two at most). 5 steps → 1. 10 fields are defaulted. Retire the duplicate manual form `projects/form.html` (it posts to the same `projects.create_project`).

### 4.2 Guided Estimating (`GUIDED_ESTIMATING`, 15 steps; 12 apply to new selected-work projects, 14 to legacy stage projects)

| # | Step | Why are we asking? | Class | Recommendation |
|---|---|---|---|---|
| 1 | Select the project | The wizard is project-agnostic | **A** | Always open from the project (or from attention); never ask |
| 2 | What work are we doing? (work + Internal/Subcontracted) | Human: scope | **K** | Keep as the **Scope panel** ("Is Brayman doing this work?", responsible party only when unchecked) |
| 3 | Project type and your role (legacy) | Already captured in New Project step 3 | **R** | Remove |
| 4 | Review the construction stages (legacy) | Calibrayt knows the stages from the project type | **A** | Derive; the user can add a missing item from the scope list |
| 5 | Internal, Subcontracted or N/A (legacy) | Human, but it duplicates step 2 | **M** → 2 | One scope decision |
| 6 | Measurements and quantities | Human: measurement | **M** → 7 | Quantities are part of each work item's card |
| 7 | Calculators for internal work: calculator → confirm quantities → labour hours → **who supplies and builds** → Complete & Next | Quantities and labour are human. "Who supplies and builds" is derivable (scope + default supplier). "Complete & Next" is software bookkeeping | **K** (+ routing **A**) | **Price This Job** work-item card. Routing is defaulted; the item completes itself when its facts are complete (`stage_check`) |
| 8 | Request subcontractor quotations ("…and mark it as waiting") | Sending is human; "mark as waiting" is software | **M** | Becomes **Award This Subcontract**; waiting is set automatically when sent |
| 9 | Record, compare and select quotations ("press Use this cost on the line, then complete the stage") | Selecting is human; the rest is software | **K** (+ **A**) | Selecting applies the cost and completes the item automatically |
| 10 | Supplier material pricing | Software can match approved supplier prices | **A** | Apply automatically; show only mismatches or missing prices |
| 11 | Review labour, materials, equipment, subcontractors and allowances | A review of the same numbers as step 12 | **M** → 12 | One review screen |
| 12 | Complete the internal cost estimate (resolve open stages: confirmed / allowance / owner no-cost) | Human, for exceptions only | **K** | **Review This Estimate**: shows only unresolved items |
| 13 | Approved pricing and gross margin ("Approve the costing, then apply pricing policy") | The costing approval and policy application are system checks; the margin/labour-rate adjustment is human | **M** → Gate 1 | A single **Approve Estimate** with an editable margin and labour rate (per project) |
| 14 | Customer proposal (prepare, check, send) | Preparing is automatic; checking and sending are human | **K** | **Get Customer Approval** |
| 15 | Customer acceptance and into the build ("record acceptance, then build the work plan") | Recording is human only when acceptance is offline; building the work plan is software | **M** | Online acceptance is recorded automatically; "Record acceptance given another way" is a secondary action; the work plan is built on acceptance |

**Recommendation:** replace with **four Guided Tasks**: Price This Job (scope + work items), Award This Subcontract, Review This Estimate (Gate 1), Get Customer Approval (Gate 2). 15 steps → 4–5 screens. Keep `guided.*` routes and `app/services/guided_estimating.py` as the engine. Retire `guided.workflow`'s separate stage-list page in favour of the Price This Job work-item list.

### 4.3 Manage a Project (`MANAGE_PROJECT`, 12 steps)

| # | Step | Class | Recommendation |
|---|---|---|---|
| 1 | Select the accepted project | **A** | Context |
| 2 | Scope, contract and accepted estimate ("generate and send the contract") | **A** | The contract is generated on acceptance. Sending belongs to Get Customer Approval (single signing) |
| 3 | Milestones and schedule ("Build the work plan, then schedule each item") | **K** (+ build **A**) | **Schedule This Project** (preliminary schedule pre-filled) |
| 4 | Project Lead, employees, crews, subcontractors | **M** → 3 | Assign people per scheduled item inside Schedule This Project; Project Lead is a field on Overview |
| 5 | Material requirements ("check who supplies each line, then send") | **M** (routing **A**) | **Buy What's Needed** |
| 6 | Authorized suppliers | **R** | Reference; a link inside Buy What's Needed |
| 7 | Purchase requests and orders | **K** | Buy What's Needed (Gate 3 approve and order) |
| 8 | Deliveries and subcontractor schedules | **M** → attention | Delivery changes and problems are already attention items |
| 9 | Progress, costs and outstanding work | **M** → attention + Money tab | Time approval is an attention item; job cost is the Money tab |
| 10 | Changes and customer approvals | **K** | **Review This Change** |
| 11 | Completion and deficiencies | **M** → 12 | Close This Project |
| 12 | Close the project | **K** | **Close This Project** |

**Recommendation: retire as a linear wizard.** Managing a job is not a sequence. It is the project's **Next Step** plus attention-driven tasks. 12 steps → 0 wizard steps; the 4 human decisions live in 4 tasks.

### 4.4 Supplier Pro Desk (`SUPPLIER_PRO_DESK`, 12 steps)

| # | Step | Class | Recommendation |
|---|---|---|---|
| 1 | Open a request or start a quotation | **K** | It *is* the Requests list |
| 2 | Contractor, customer and project | **R** | Show as the context bar |
| 3 | Drawings, specifications and takeoffs | **K** (walk-in only) | Shown only for a walk-in quick quote (sketch → drawing) |
| 4 | Quantities and products ("Match each line to your SKU. Nothing is filled in for you.") | **K** (+ **A**) | Remember previous SKU matches and the store catalogue; ask only about unmatched lines |
| 5 | Availability | **M** | A per-line note on the pricing grid |
| 6 | Your pricing and customer terms | **K** | Pricing grid |
| 7 | Substitutions and alternatives | **M** → 6 | Per-line "Substitute" action |
| 8 | Prepare and send the quotation | **K** | Send |
| 9 | Responses and revisions | **M** → attention | Supplier attention item |
| 10 | Convert to an order | **M** → attention | "Order to confirm" (already in `supplier_insights.attention`) |
| 11 | Pickup or delivery | **M** → attention | Upcoming deliveries / delivery change |
| 12 | Fulfilment and history | **A** | Automatic history |

**Recommendation:** **Guided Task "Price This Request"** (supplier side): open → match and price → send. 12 → 3–4 screens.

### 4.5 Wizard totals

| Wizard | Steps | K | A | R | M | Proposed screens |
|---|---|---|---|---|---|---|
| Start a New Project | 5 | 2 | 0 (+10 fields) | 1 | 2 | 1 |
| Guided Estimating | 15 | 5 | 3 | 1 | 6 | 4–5 |
| Manage a Project | 12 | 4 | 2 | 1 | 5 | 0 (4 tasks) |
| Supplier Pro Desk | 12 | 5 | 1 | 1 | 5 | 3–4 |
| **Total** | **44** | **16** | **6** | **4** | **18** | **~11** |

The wizard **framework** (`app/wizards/framework.py`: `StepView(state, headline, items, missing, actions)`, `Step(what, do, next)`) is a good basis for the Task Screen standard. Reuse its evaluate/handle split and `Action`/`Item` types. Drop the linear stepper and the "Start Guided Wizard / Continue Manually" fork, which tells the user that two parallel ways of working exist.

---

## 5. What Needs Your Attention audit

### 5.1 Surfaces today

| Surface | File | Who | Shows |
|---|---|---|---|
| Home "WHAT NEEDS MY ATTENTION?" (top 4 + "Show all") | `operations/_home_attention.html`, `app/routes/main.py` | non-field office | `needs_attention.assemble(..., include_company_facts=False)` |
| Full list | `operations.attention` → `operations/attention.html` | non-field office | `assemble()` including company facts for COMPANY_MANAGEMENT |
| Company Attention (nav "Attention") | `company_attention.index` → `company_attention/index.html` | COMPANY_MANAGEMENT | labour/schedule facts only (`SEALED_FACT_TYPES`) |
| Supplier Hub attention | `supplier/_attention.html`, `supplier_insights.attention` | supplier | quotes to price, orders to confirm, contractor delivery changes, upcoming deliveries |
| Field "Before you finish today" | `field/today.html` | crew | the crew's own reminders, returned time |
| Home SMS banner | `dashboard.html` (`sms_schedule_attention()`) | office | failed schedule texts (outside the attention list) |

### 5.2 Items surfaced today (`app/services/needs_attention.py::assemble`)

| Kind | Item | Links to | Deep link to a task? |
|---|---|---|---|
| time | N time entries to approve | `/time?status=SUBMITTED&worker_user_id=` | filtered list: good; becomes "Approve Time" |
| time | Returned time not fixed | `/time?status=RETURNED…` | list |
| time | No time entered (scheduled) | `/time?worker_user_id=&from=&to=` | list |
| materials | Material request (submitted / approved, choose the supplier) | `/operations/material-requests/<id>` | specific: good → Buy What's Needed |
| extra_work | Change order for extra work | `/project-controls/change-orders/<id>` | specific → Review This Change |
| extra_work | Extra work reported | `/operations/extra-work/<id>` | specific → Review This Change |
| extra_work | Extra work not on a change order | `/work-structure/projects/<id>` | **generic work plan page**: should open Review This Change |
| extra_work | Change order Pending Approval | `/project-controls/change-orders/<id>` | specific |
| quotes | Price returned by supplier | `/projects/<id>/supplier-requests#share-<id>` | anchor on a busy page → Buy What's Needed (order step) |
| quotes | Waiting for a price | same | → Buy What's Needed |
| deliveries | Supplier reported a PO problem | same anchor | → Buy What's Needed |
| deliveries | Supplier asks to move a delivery | same anchor | → Resolve This Schedule Conflict (delivery) |
| deliveries | Delivery exception (field confirmation) | `/operations/deliveries/<id>` | specific |
| receipts | Receipt needs attention / QBO transfer failed | `/accounting/receipts/<id>` | specific |
| receipts | N receipts to review / reviewed | `/accounting/receipts?status=` | list |
| quickbooks | QuickBooks Time transfer failed | `/time/quickbooks-time` | list |
| quickbooks | Project sync to confirm/retry | `/accounting/quickbooks-online/projects#project-` | anchor |
| schedule | Schedule conflict (next 14 days) | `/projects/<id>#hub-schedule` | **hub anchor**: should open Resolve This Schedule Conflict (`schedule.planning`) |
| tasks | Problem/delay in a job update | `/operations/job-updates/<id>` | specific |
| tasks | Open punch list items (active project) | `/projects/<id>#hub-punch-list` | anchor → Close This Project |
| customers | Customer information incomplete | client edit | specific |
| labour (company facts, 6 types) | getting close / allowance used / over allowance / scheduled finish passed / scheduled work without approved time / sequence | the fact's destination or `/projects/<id>` | mostly generic |

**Implementation note:** item `href`s are hard-coded path strings, not `url_for`. A route rename will break them silently. Move to endpoint + args.

### 5.3 Governed events in the data model that are not surfaced

Each was confirmed absent from `needs_attention.py` by grep.

| # | Event (model / service) | Who | Proposed item text | Deep link (task) |
|---|---|---|---|---|
| 1 | Estimate ready for **Gate 1** approval: costing complete, version not locked (`EstimateVersion`, `estimate_approval.py`) | owner/estimator | "Bushel deck estimate is ready for your approval" | Review This Estimate (`guided.pricing` / `estimates.view_version`) |
| 2 | Work items needing review / calculator results not yet on the estimate (`GuidedEstimateStage` NEEDS_REVIEW; `CalculationEstimateMapping` STATUS_OPEN) | estimator | "2 calculator results waiting to go on the estimate" | Price This Job (item) |
| 3 | Subcontract quote **waiting** (overdue) / **received but not selected** (`GuidedEstimateStage` WAITING_FOR_QUOTE; `SubcontractorQuote` RECEIVED) | estimator | "Electrical quote from X received: choose one" | Award This Subcontract (`guided.compare`) |
| 4 | **Supplier pricing missing** (`supplier_pricing_request` TBD lines) / price returned after estimate | estimator | "3 lines still need a supplier price" | Price This Job |
| 5 | Contractor cost approval pending (`ContractorCostApproval` PENDING) | owner | "Approve the contractor-confirmed price" | `approved_costs.review` |
| 6 | **Proposal issued, customer has not answered** (`Proposal.status == "Issued"`, age, expiry) | owner | "Proposal sent 6 days ago: not opened" | Get Customer Approval |
| 7 | **CaliSIGN** request SENT / expiring / DECLINED / SIGNED awaiting countersign (`signing.py` STATUS_*) | owner | "Customer signed: your countersignature needed" | Get Customer Approval (`projects.review_contract`) |
| 8 | Accepted, but the contract was not generated (`BLOCK_CONTRACT_NOT_GENERATED`) | owner | "Contract not generated yet" | Get Customer Approval |
| 9 | **Subcontract commitment PROPOSED** awaiting Gate 3 (`SubcontractCommitment` COMMITMENT_PROPOSED) | owner | "Approve the framing subcontract ($18,400)" | Award This Subcontract (`supplier_office.commitments`) |
| 10 | **Early Procurement Exception** approved but unused, or a commitment needed before Gate 2 (`EarlyProcurementException` APPROVED) | owner | "Early order approved, not placed" | Buy What's Needed |
| 11 | Supplier PO awaiting contractor approval / supplier signature (CaliSIGN supplier) | office | "PO 1042 waiting for BMR's signature" | Buy What's Needed |
| 12 | **Company Schedule Change Request PROPOSED** (`CompanyScheduleChangeRequest` CSCR_PROPOSED) | owner/PM | "Ben asks to move framing to 12 Nov: 2 jobs affected" | Resolve This Schedule Conflict (`schedule.planning`) |
| 13 | **Schedule external drafts awaiting send** (`ScheduleExternalDraft` DRAFT_PENDING) | office | "2 supplier delivery notices drafted: send?" | Resolve This Schedule Conflict |
| 14 | Accepted work not yet scheduled (`list_unscheduled_elements`, shown only on the Calendar) | PM | "4 accepted items not on the schedule" | Schedule This Project |
| 15 | Order-by date approaching (`governed_schedule.procurement_plan`) | purchasing | "Order trusses by Fri for the 20 Nov window" | Buy What's Needed |
| 16 | Change order Draft not yet sent (only Pending Approval is surfaced) | owner | "Change order CO-3 drafted, not sent" | Review This Change |
| 17 | Final walkthrough RESPONDED (`ProjectFinalWalkthroughInvitation` WALKTHROUGH_STATUS_RESPONDED) | PM | "Customer returned the walkthrough: 3 items" | Close This Project |
| 18 | Project ready to close (punch complete, walkthrough done, no open orders) | owner | "Ready to close" | Close This Project |
| 19 | Field-event derived facts PROPOSED (`build` DERIVED_STATUS_PROPOSED) | PM | "Review what the crew captured" | `build.view_field_event` |
| 20 | Labour calibration candidates PROPOSED/IN_REVIEW (`labour_engine`) | owner | "Update 2 labour rates from finished jobs" | Admin › Labour standards (review) |
| 21 | Failed schedule texts (today a separate banner) | office | as now | `sms_notifications.office_notices` |

**Supplier side gap:** CaliSIGN supplier signing requests awaiting the store's signature are not in `supplier_insights.attention`.

**Home gap:** company facts are excluded on Home but included on `/operations/attention`. Home shows 4 items and does not show that more are hidden by kind.

### 5.4 Attention design rules (proposed)

1. Every item has exactly **one button** that opens **the task at the right state** (never a list or an anchor on a long page).
2. Each item states: what · project · why it is waiting on you · since when / due.
3. Items are grouped **Waiting on you** vs **Waiting on others** (proposal sent, quote requested, PO with supplier). The second group is collapsed by default.
4. Filter by role preference (Owner/Estimator · PM · Office/Purchasing). Permissions remain the existing gates (`has_office_financial_access`, COMPANY_MANAGEMENT, owner/SA).
5. The header bell (currently disabled) shows the count and opens Home.

---

## 6. Navigation reduction: summary

| Class | Count now | Items |
|---|---|---|
| primary | 6 | Home, Calendar, Projects, Clients, Suppliers (as Purchasing), Accounting (as Time & Money) |
| contextual | 10 | the 10 calculators (opened from a work item) |
| reference | 5 | Costs & pricing (section), What we pay, Past jobs, Workflow Guide, Getting started |
| administrative | 5 | How we price, Templates, People & Access, Crews, Work catalog |
| advanced | 1 | Reusable work (assemblies) |
| redundant | 2 | Attention (company-attention, duplicates the attention list), Employment vs Entrepreneurship (duplicate of decision_tools) |
| obsolete | 1 (header) | disabled notifications bell |

**Proposed:** 6 primary (Attention, Projects, Calendar, Customers, Purchasing, Time & Money) + More + Admin gear.

---

## 7. Proposed Task-First information architecture

### 7.1 Guided Tasks (contractor language) and what each assembles

| # | Guided Task | Opened from | Assembles (existing routes and services; nothing re-implemented) | Human decisions on the screen | Done automatically |
|---|---|---|---|---|---|
| 1 | **Set Up This Project** | "Start something", Customers | `projects.create_project` (POST), `clients` service, `project_identity` (BC-YYYY-NNNN), `commercial_context`, `project_drawing_requirement`, `plan_intelligence.upload_plan`, `permit_intelligence` | customer, address, what is being built, role, plans | project #, commercial type, status, permit class, settings, Project Lead default, guided estimate start, permit report |
| 2 | **Price This Job** | Project Next Step, attention #2/#4 | `guided.scope`/`guided/work.html` (scope), `guided.stage`, `guided.calculation`, `calculators.*` + `calculators.project_stages`, `estimates.calculation_review`, `estimate_labour.hours`, `plan_intelligence.takeoff_*` + `takeoff_map_to_estimate`, `deck_takeoff.*`, `selected_work`, `estimate_costing`, `winter_job`, `labour_engine` (rates), `supplier_catalogue`/approved supplier prices | is Brayman doing this work, quantities, labour hours (override + reason), allowances | suggested work, routing, supplier price matching, labour × rate, general conditions, non-destructive exclusion, totals and true margin |
| 3 | **Award This Subcontract** | the work item, attention #3/#9 | `scope_delivery.labour_quote_request`, `guided` subcontract actions (`setup_subcontract`, `request_quote`, `record_quote`), `guided.compare`, `subcontract_quote`, `supplier_office.commitments` (propose/approve), `procurement_gate` (Gate 3), `subcontract_signing` + CaliSIGN | which quote; approve the commitment | mark waiting, apply cost, completion, Gate 2 check, signing package |
| 4 | **Review This Estimate** (Gate 1) | Next Step, attention #1 | `guided.internal_cost`, `guided.pricing`, `estimates.view_version` (Details), `estimates.internal_cost_breakdown`, `approved_costs.review`, `estimate_approval.py`, the contractor-package PDF, document family 01–04/08 | resolve exceptions, margin and labour rate for this project, **Approve Estimate** | costing approval checks, pricing policy, lock/immutability, proposal draft, documents |
| 5 | **Get Customer Approval** (Gate 2) | Next Step, attention #6/#7/#8 | `proposals.view_proposal`/`preview`, `proposal_link`, `proposal_acceptance`, `contract_generation`, `projects.review_contract`, `signing_office.*`, `sign.*` (CaliSIGN) | check and send; countersign; record an offline acceptance | contract generation, Commercial Baseline, work plan build, reminders, stage advance |
| 6 | **Buy What's Needed** (Gate 3, purchasing) | Project › Purchasing, Purchasing landing, attention (quotes, PO, deliveries, #10/#11/#15) | `supplier_office.project_requests`, `supplier_package.*`, `supplier_pricing_request*` (approved form), `quote_comparison`, `operations.material_request`, `material_requirements`, `purchasing_quantity`, `unit_conversion`, `procurement_gate` (Early Procurement Exception), `supplier_signing` + CaliSIGN, `delivery_confirmations` | supplier choice (if more than 1), approve the price and order, order before the customer signs (with reason) | quantities, unit conversion, separate concrete request, needed-by dates from the schedule |
| 7 | **Schedule This Project** | Next Step after Gate 2, attention #14 | `schedule.planning` (anticipated start, preliminary schedule, Gantt), `governed_schedule.apply_preliminary_schedule`/`confirm_window`, `schedule.edit_item`, `organization_crew`, `project_lead`, `sms_notifications` | start date, confirm windows, crew per item | durations from hours, working days, procurement windows, crew texts |
| 8 | **Resolve This Schedule Conflict** | attention (conflict, #12, #13, supplier delivery change) | `schedule.list_schedule_conflicts`, `governed_schedule.impact_analysis`/`request_schedule_change`/`approve_change`/`reject_change`/`owner_override`, `pending_drafts`/`send_draft`, `supplier_hub` delivery changes | approve/reject/override; send notices | impact analysis, drafted supplier notices |
| 9 | **Review This Change** | attention (extra work, CO), Field extra work | `operations.extra_work_report`, `extra_work_reports`, `project_controls.*` (create/edit/view/pdf), `create_from_estimate_version`, `work_structure` change-order work item, CaliSIGN change order | is it extra; its price; send | pricing via the same work-item engine, baseline and schedule update on approval |
| 10 | **Close This Project** | Next Step at completion, attention #17/#18 | punch list (hub + `punch_list`), `project_final_walkthrough` + `walkthrough.form`, `direct_cost_actuals`, `package_controls`, `project_performance`, `labour_engine` candidates, `projects.close_project` | punch items done; close (owner/SA) | readiness check, calibration candidates, closeout record |

**Supporting tasks** (smaller, mostly opened from attention):
- **Approve Time** (`time_entry.review`)
- **Review Receipts** (`accounting.receipts_inbox`)
- **Review a Job Update** (`operations.job_update`)
- **Fix QuickBooks Sync** (`accounting.quickbooks_projects`, `payroll_time.quickbooks_time`)
- **Price This Request** (supplier: `supplier_portal.request_detail`, `supplier_pro_desk.quote`)

### 7.2 The Task Screen standard

Every Layer-2/3 screen uses one layout. The existing pieces it maps from:
- `wizards/_run_compact.html` and `framework.StepView`: state, headline, items, missing, actions
- `projects/setup.html`: what's ready / what's needed / one action
- `field/today.html`: the day's job first

| Zone | Content | Rule | Existing source |
|---|---|---|---|
| **Context** | project name + Brayman # + Client # · customer · stage · View plan · ? help | one line; never a heading stack | `hub-heading-identity`, header plan button (`office_plan_link`), `contextual_help` |
| **Purpose** | the task name in outcome language + one sentence ("Price this job so you can approve it") | no instructions about the software | `Step.what` |
| **Current state** | one headline + a short checklist of done/to do (max ~7 rows) | stored facts only | `StepView.headline`, `StepView.items` |
| **Attention / Decision** | only the decisions that need this person now, each with its consequence (e.g. "Approving locks version 3 at $48,200, 31% margin") | 0–3 decisions | `StepView.missing`, `stage_check`, gate blocks |
| **Primary action** | exactly **one** primary button; secondary actions in a "More" menu | never two primaries | `Action(primary=True)` |
| **Details** | collapsed sections: line items, history, documents, audit, settings | closed by default; state remembered per user | `estimates/version_detail.html`, history partials, `operations/_history.html` |

**Mapping of existing templates to the standard**

| Template | Becomes |
|---|---|
| `projects/detail.html` | Project Overview (Context + Next Step + Waiting lists) + tabs whose content is Details |
| `projects/setup.html` | the Next Step card (logic in `project_setup.describe_setup`, extended to every stage) |
| `guided/workflow.html` + `guided/stage.html` + `guided/work.html` + `guided/scope.html` | Price This Job (list + item panel) |
| `guided/internal_cost.html` + `guided/pricing.html` + summary from `estimates/version_detail.html` | Review This Estimate |
| `estimates/version_detail.html` | Details › Line items |
| `proposals/detail.html` + `projects/contract_review.html` + `partials/calisign.html` | Get Customer Approval |
| `suppliers/project_requests.html` + `projects/supplier_package.html` + `suppliers/commitments.html` | Buy What's Needed / Award This Subcontract |
| `schedule/planning.html` | Schedule This Project / Resolve This Schedule Conflict |
| `project_controls/change_orders/detail.html` + `operations/extra_work_report.html` | Review This Change |
| hub walkthrough/punch panels + `projects/close_confirm.html` | Close This Project |
| `wizards/_run*.html` | retired; its components move to the Task Screen partials |

### 7.3 Priority order of first-class journeys

Ordered by Kevin's main criterion (ease of estimating), then by daily frequency:

1. **What Needs Your Attention** (Home): the entry to everything; cheapest high-value change (one list, deep links, the gap items in 5.3)
2. **Create/open a project** (Set Up This Project + Project Overview with Next Step)
3. **Drawings/documents** (Plans & Documents; add plans during setup)
4. **Scope** ("Is Brayman doing this work?")
5. **Takeoff** (inside the work item: plan measurement → calculator)
6. **Estimate/pricing** (Price This Job)
7. **Contractor review/approval** (Review This Estimate, Gate 1)
8. **Customer proposal/acceptance** (Get Customer Approval, Gate 2, CaliSIGN)
9. **Purchasing** (Buy What's Needed, Gate 3, Early Procurement Exception)
10. **Subcontracting** (Award This Subcontract)
11. **Scheduling/Gantt** (Schedule This Project)
12. **Schedule change** (Resolve This Schedule Conflict)
13. **Field work** (already good; trim)
14. **Change orders** (Review This Change)
15. **Project documents** (contract, signed PDFs, master family documents under Documents)
16. **Closeout** (Close This Project + calibration)

---

## 8. Design system and density

### 8.1 CSS files (`app/static/css/`, 8,165 lines total)

| File | Lines | Role |
|---|---|---|
| `app.css` | 2,658 | shell, tokens (`--gold #c79a2b`, `--sidebar #17191d`, `--workspace #f6f5f2`, `--text`, `--muted`, `--border`, `--focus`, sidebar/header sizes, `--shadow-soft`), `.button*`, `.panel`, `.form-panel`, `.card`, `.data-table`, `.empty-state`, `.breadcrumbs`, `.grid`, `.form-grid` |
| `v1-refinement.css` | 1,383 | second layer of overrides (`--ink-soft`, `--radius-sm/md`, `--row-hover`, `--surface-line`, `--focus-ring`), `.action-group`, `.page-more`, hub lifecycle |
| `field.css` | 902 | field shell |
| `calculators.css`, `stair-calculator.css` | 439 / 203 | calculators |
| `wizards.css`, `home-compact.css` | 423 / 39 | wizard runner, Home |
| `guided-estimating.css` | 101 | guided |
| `signing.css`, `calisign.css` | 231 / 84 | CaliSIGN (approved navy #1F3A5F, gold #C79A2B, IBM Plex Sans) |
| `supplier-hub.css`, `supplier-economic-model.css` | 116 / 207 | supplier |
| `needs_attention.css` | 24 | attention list |
| `workflow-map.css`, `walkthrough.css`, `cal-assistant.css`, `proposal-preview.css`, `business-owner-assessment.css`, `opening-v1.css`, `customer.css`, `session-timeout.css`, `auth.css`, `style.css` | small | feature-specific |

**Problems found**
- Tokens are split across two files.
- `--danger` is used with a fallback (`var(--danger, #b42318)` in `dashboard.html`) but never defined.
- There is no spacing scale.
- There are no dark-mode tokens.
- There are **664 inline `style="…"` attributes** and **20 inline `<style>` blocks in 19 templates** (e.g. `projects/detail.html` hub identity, customer-incomplete, `dashboard.html` SMS banner).
- Feature CSS is linked from inside `{% block content %}` (e.g. `dashboard.html` links `wizards.css` and `home-compact.css` in the body).

**Layout primitives available:** `.page-heading`, `.form-panel`, `.panel`/`.panel-wide`, `.action-group(-primary)`, `.page-more`, `.data-table`, `.empty-state`, `.contextual-help`, `.hub-lifecycle`, `.flash-stack`, `.breadcrumbs`.

**Missing primitive:** a Task Screen shell (Context bar, Purpose, State checklist, Decision card, Primary action bar, Details accordion), plus an Attention item component shared by office, field and supplier.

### 8.2 Density problems observed

| Screen | Evidence |
|---|---|
| Project hub `projects/detail.html` | 1,425 lines, 14 forms, ~42 buttons, 84 links, ~74 panels, 7 header actions, 6 lifecycle anchors, 5 "More about this page" paragraphs; many equal-weight panels with "Related …" lists; the primary action is not state-aware |
| Estimate version `estimates/version_detail.html` | 600 lines, 20 forms, 37 buttons (Add Section / Add Cost Item / Add Assembly / Add Custom-Allowance per section) |
| Guided stage `guided/stage.html` | 19 forms, 19 buttons, 4 details: calculator, calculations, lines, labour, subcontract and change responsibility all at once |
| Work plan `work_structure/project_work.html` | 335 lines, 16 forms, 18 buttons |
| Supplier requests `suppliers/project_requests.html` | 21 buttons, 5 `<details>` per share |
| Schedule planning `schedule/planning.html` | 20 buttons, 14 sections on one page |
| Company calendar `schedule/company.html` | 27 links, 9 `<details>` |
| Home `dashboard.html` | 7 stacked blocks; the 3 wizards × (Start + Continue manually) fork; 5 pulse counts |
| Project creation | ~23 visible inputs incl. 7 settings dropdowns + justification |

### 8.3 Internal terms visible to users (rename or hide)

Counts are occurrences in visible template text (Jinja, tags and comments removed); "files" is the number of templates.

| Term (visible) | Count / files | Example template | Proposed |
|---|---|---|---|
| "version" / "Version N" | 91 / 34 | `estimates/version_detail.html`, `projects/detail.html` "(version N)" | "Estimate rev. 3" on Details only; Overview shows the current figures |
| "package" (work package, supplier package, QuickBooks package) | 72 / 22 (+11 in `contractor_copy`) | `projects/package_controls.html`, `suppliers/commitments.html` "Committed cost by work package" | "Work item", "Order", "Supplier request" |
| "stage" (guided stage, stages in construction order) | 69 / 24 | `guided/workflow.html`, `guided/stage.html` | "Work item" (stages only as a sort order) |
| "revision", "sheet(s)" | 38 / 21, 80 / 21 | `plan_intelligence/*` | "Plan set", "Page"; older versions in Details |
| "candidate" | 37 / 12 | `labour_engine/candidate_*`: "Candidate {{id}}", "Promoted production standard", "Evidence refs" | "Suggested rate update" (Admin) |
| "mapping" | 30 / 9 | `labour_engine/mappings_*`, `estimates/calculation_review.html` | hide; "Matched to" |
| "standard" (production/cost-rate standard) | 40 / 17 | `labour_engine/standard_detail.html` | "Labour rate" / "Production rate" |
| "costing" / "Costing snapshot" / "snapshot" | 26 / 11; 16 / 8 | `guided/internal_cost.html`, `estimates/internal_breakdown.html`, `pricing_engine/snapshot_detail.html`, `projects/edit_context.html` | "Internal cost"; never show "snapshot" |
| "Approve the costing" / "Sign off" / "Lock" / "Locked — read only" | 3 labels for Gate 1 | `guided/pricing.html`, `estimates/version_detail.html` | one label: **Approve Estimate**, then "Approved (locked)" |
| "allowance" | 22 / 12 | `estimates/internal_breakdown.html` | keep (contractor term), but only as a decision |
| "takeoff" / "Take-off" / "takeoff run" / fingerprint | 28 / 15; 24 / 10; 6 / 4 | `plan_intelligence/takeoff_*`, `projects/construction_drawing_preview.html` ("Takeoff {{fingerprint[:12]}}") | "Measurements"; hide fingerprints and SHA |
| "Plan Intelligence" | 12 / 11 | `plan_intelligence/detail.html`, hub "More" ("Scale tools remain in Plan Intelligence") | "Plans" |
| "construction model" / "member counts" | 9 / 5 | `projects/construction_information.html`, `estimates/calculation_list.html` | "Building details" |
| "canonical" | 4 / 3 (+55 in expressions) | `projects/supplier_package.html`, `plan_intelligence/takeoff_run.html` | hide |
| "commitment(s)" | 10 / 4 | `suppliers/commitments.html` page title "Commitments — …" | "Subcontracts & early orders" |
| "Early Procurement Exception" | 5 / 3 | `schedule/planning.html`, `suppliers/commitments.html` | action "Order before the customer signs"; keep the record name in the audit/Details |
| "Company Schedule Change Requests" | 1 / 1 | `schedule/planning.html` | "Requested date changes" |
| "Supplier delivery changes (drafts)" | | `schedule/planning.html` | "Delivery notices to send" |
| "Procurement planning windows" | | `schedule/planning.html` | "Order-by dates" |
| "Anticipated construction start" / ANTICIPATED/CONFIRMED | | `schedule/planning.html` | "Planned start" / "Confirmed" |
| "Internal, Subcontracted or N/A" / "N/A" | 6 / 4 | `guided/scope.html`, `guided/_choice.html` | "Is Brayman doing this work? Yes (our crew) / Yes (subcontract) / No: by others" |
| "Your role" / "contractor role" | 11 / 8 | `wizards/forms/*`, `guided/start.html` | default it; ask only if unusual |
| "Permit context class", "Pricing posture", "Execution risk", "Schedule condition", "Site condition", "Estimate stage", "Delivery model" | | `wizards/forms/np_location.html`, `projects/form.html`, `projects/edit_context.html` | hide under "Adjust project settings"; plain labels |
| "Commercial settings" / "PRICING_ASSUMPTIONS (version N)" | | `projects/detail.html` | Details › Pricing assumptions |
| "operating" (operating state, operating identity, operating standard) | 13 / 8 | `projects/detail.html` `operating_identity`, `labour_engine/*` | "Current / Closed" |
| "immutable", "superseded" | 7 / 5; 7 / 6 | `projects/detail.html`, `plan_intelligence/takeoff_package.html`, `labour_engine/mapping_detail.html` ("Source evidence (immutable)") | "Approved (cannot change)" / "Replaced"; mostly hide |
| "baseline" | 3 / 2 (+7 in copy) | `projects/detail.html` | "Contract value (signed)" |
| "artifact", "governed", "routing", "SHA" | 5 / 1, 3 / 2, 3 / 2, 3 / 2 | `projects/quickbooks_entry.html`, `projects/scope_delivery.html`, `plan_intelligence/detail.html` | hide |
| "work item" / "work plan" / "element" / "activity" | 41 / 12; 4 / 2; 7 / 3; 6 / 3 | `work_structure/*`, `schedule/item_form.html` | keep **"Work item"** as the single noun everywhere (replacing stage/element/activity/package) |
| "Guided estimate" / "Guided Wizards" / "Wizard" / "Continue Manually" | 14 / 10; 15 / 8; 9 / 5 | `projects/detail.html`, `wizards/_home_strip.html`, `_cards.html` | remove: tasks are just the way the app works |
| "LEARN · Future" | 6 / 3 | `projects/detail.html` | remove (unbuilt) |
| "synthetic" | 18 / 11 | `projects/supplier_package*.html`, `supplier/pro_desk/*` | training/test data only; never on Production copy |
| "Field Observations" vs "Capture" vs "field events" | | `projects/detail.html`, `field/today.html` | one name: "Site notes & photos" |
| "Workflow Guide" vs "Getting started" vs "Training" | 33 "Workflow" / 22 files | | Help (one entry) |

---

## 9. Top simplifications by value

1. **One attention list, with deep links into tasks.** Merge `/operations/attention`, `/company-attention` and the Home block. Add the 21 missing governed events (5.3), especially Gate 1 ready, proposal unanswered, CaliSIGN awaiting signature, subcontract commitment to approve, schedule change requests, and drafted delivery notices.
2. **A state-aware Next Step on every project.** Extend `project_setup.describe_setup` past estimating through every stage (Lead → Closed), and replace the hub's fixed "Continue setup" button.
3. **Price This Job as one screen.** Merge 7 Guided Estimating steps and 4 scope surfaces into a work-item list with an item panel. Routing, supplier price matching, "mark waiting", "use this cost" and completion are done automatically.
4. **A single Gate 1 action.** "Approve the costing", "apply pricing policy" and "Sign off/Lock" become one **Approve Estimate**, with margin and labour rate editable per project.
5. **Set Up This Project on one screen.** Default the 10 software-needs fields and retire the duplicate manual form and the Review step.
6. **Reduce the office nav from 28 to 6 primary + More + Admin.** Calculators open from the work item. Libraries and policies move under Admin.
7. **Rebuild the project hub as Overview + tabs.** 74 panels and ~42 buttons become one Next Step, two waiting lists and 8 tabs of one-line summaries.
8. **Retire the linear "Manage a Project" and supplier wizards.** Manage a Project becomes Next Step + attention-driven tasks; the supplier wizard becomes Price This Request. Remove the "Start Guided Wizard / Continue Manually" fork everywhere.
9. **Rename internal terms.** Use one noun, "Work item", for stage/element/activity/package. Hide snapshot, fingerprint, SHA, canonical, candidate, mapping, immutable, Plan Intelligence and LEARN.
10. **One help affordance per screen.** Remove the "More about this page" implementation paragraphs. Turn the dead header bell into the attention count. Move the SMS banner into attention.

---

## 10. Governed capability to preserve (checklist for the redesign)

Each capability below survives behind the tasks. Nothing is removed from the services; only surfaces change.

| Capability | Where it lives |
|---|---|
| Scope lineage | `work_scope.inherit_scope_lineage` |
| Non-destructive exclusion | guided scope responsibility |
| Labour calculation | `estimate_labour_hours`, `labour_engine` |
| Supplier/subcontract pricing | `supplier_pricing_request*`, `subcontract_quote` |
| True margin | `estimate_economics` |
| Winter settings | `winter_job` |
| Gate 1 | `estimate_approval`, immutable versions (`estimates.refuse_unlock`) |
| Gate 2 | `proposal_acceptance`, Commercial Baseline |
| Gate 3 + Early Procurement Exception | `procurement_gate` |
| Purchasing | `supplier_office`, `supplier_hub` |
| CaliSIGN | `signing*`, `calisign` |
| Scheduling/Gantt and schedule governance | `governed_schedule`, `schedule_governance` |
| Calendar | `schedule.company`, `appointments` |
| Change orders | `project_controls` |
| Actuals | `direct_cost_actuals`, `package_controls` |
| Closeout | `project_operating_lifecycle`, `final_walkthrough`, `closeout` |
| Calibration | `labour_engine`, `historical_review` |
| Document generation | the Approved Master Template Family V1, unchanged |
| Audit | event tables, `people_access_event` |
| Permissions | `access_domains`, `instance_authority` |

**Design constraints carried forward**
- Approved logos and colours.
- The Approved Master Template Family V1 and the approved Supplier Pricing Request form are not redesigned.
- A View project plan button on project screens.
- Training and the app stay in sync.
- No added AI cost.

---

## 11. Suggested next steps (for approval, not started)

1. Approve the Guided Task names (7.1) and the primary navigation (2.2).
2. Build the Task Screen and Attention Item partials and tokens (8.1). This is CSS/partials only, with no behaviour change.
3. Slice 1: unified attention + the gap items in 5.3 (service only; read-only) + Home layout.
4. Slice 2: the project Next Step engine (extend `project_setup`) + Project Overview.
5. Slice 3: Price This Job + Review This Estimate (Gate 1 single action), validated against the Linda Bushel deck and Paulusse jobs.
6. Then: Set Up This Project, Get Customer Approval, Buy What's Needed, Schedule, Change, Close.
7. Update the Training Centre lessons and Workflow Maps to the task names in each slice.

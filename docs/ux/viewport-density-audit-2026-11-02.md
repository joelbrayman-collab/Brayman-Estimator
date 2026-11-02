# CalibraytAI Viewport-First Density Audit

**Date:** 2 Nov 2026
**Branch:** `feature/viewport-density-2026-11-02` (worktree `/home/claude/vd`), from the live commit `ec80e6f1`
**Mandate:** "AIRIA-DENSITY UX CORRECTIVE RELEASE" (acceptance finding UX-DENSITY-001, Set Up This Project)
**Status:** Audit, rules and plan. Not an approval gate; the implementation followed it in the same branch.
**Measured by:** `tools/release/evidence_density.mjs` against `tests/density_page_server.py` (real migrations,
synthetic office: five customers, five projects, a priced job, an unpriced job, a subcontractor, a supplier account,
one piece of equipment, nine filed documents, a Field crew member booked today). Chromium, 100% zoom,
`deviceScaleFactor` 1. Laptop **1280 x 800** (the gate), **1280 x 720** recorded for reference, phone **390 x 844**.

**The standard.** At 1280 x 800 the *active task* of a primary screen (what the person must see and fill in, and the
one primary action) is inside the first viewport. Scrolling is for genuinely detailed information (a long document
list, an opened optional section), never the normal way to finish an ordinary Guided Task. Phones may scroll but stay
focused: Field Today shows today's work and its primary action on the first screen, and nothing scrolls sideways.

---

## 1. Baseline (ec80e6f1) at 1280 x 800, before any change

`doc` = page height, `scroll` = how far the page scrolls, `task` = bottom of the active task (its primary action and
every required input). Fits = the task ends inside 800 px.

| Screen | doc | scroll | task | Fits | Visible fields | Visible blocks |
|---|---|---|---|---|---|---|
| Home | 908 | 108 | 594 | YES | 1 | 6 |
| Attention (`/operations/attention`) | 800 | 0 | 290 | YES | 0 | 1 |
| Projects | 800 | 0 | 725 | YES | 2 | 1 |
| **Set Up This Project** (customer we have) | **2055** | **1255** | **1952** | **NO** | 36 | 8 |
| Set Up This Project (new customer) | 2055 | 1255 | 1952 | NO | 36 | 8 |
| Set Up This Project (refused, no customer name) | 2118 | 1318 | 2015 | NO | 36 | 8 |
| Project page (Task Screen) | 1510 | 710 | 296 | YES | 15 | 58 |
| **Price This Job** (priced) | 1358 | 558 | **978** | **NO** | 0 | 6 |
| **Price This Job** (to price) | 1345 | 545 | **1031** | **NO** | 0 | 7 |
| Review This Estimate | 1789 | 989 | 366 | YES (decision only) | 7 | 12 |
| Documents library | 1261 | 461 | 757 | YES | 7 | 1 |
| Project / customer / supplier / subcontractor / person documents | 800 | 0 | 418 | YES | 0 | 1 |
| Equipment | 800 | 0 | 506 | YES | 10 | 4 |
| Purchasing | 800 | 0 | 354 | YES | 0 | 2 |
| Time & Money | 800 | 0 | 490 | YES | 0 | 2 |
| Calendar | 1074 | 274 | 1003\* | NO\* | 7 | 6 |
| Field Today (phone 390 x 844) | 1847 | 1003 | **1503** | **NO** | 2 | 5 |

\* The calendar's month box sizes itself to the window; the baseline selector measured the whole workspace. Re-measured
with the box itself, it ended about 40 px below the screen because the box was sized before the page finished
loading (section 3.12).

At 1280 x 720 the Projects list (task 725) and the Documents library (757) also miss the first viewport.

**Screens needing routine scrolling at 1280 x 800 before:** Set Up This Project, Price This Job (both states),
Calendar (marginally), and Field Today on a phone: **4 of the primary screens** (5 measurements).

---

## 2. AiRIA reference inspected (read-only copy, `/home/claude/airia-ref`)

Visual and interaction reference only; no runtime dependency, no legal wording copied.

| Area | File | What it shows | Adopted as |
|---|---|---|---|
| Shell density | `templates/base.html` | Page content padding 16/28 px; top bar 2.75 rem; nav items 8 px x 16 px at 13 px | Header 64 -> 52 px; workspace top padding 16 -> 12 px, bottom 56 -> 32 px |
| Compact header | `static/css/airia_shell.css` (`--airia-compact-header-pad-y: 0.5rem`, `.top-bar-*`) | One compact bar; the matter and posture inline | Below 1440 px the company box and user name collapse to icons so the page title is never cut off |
| Guided workflow | `static/css/airia_guided.css` (`.gw-*`, `.gwf-*`) | Cards 14-20 px padding; one title, one line of explanation; 3-across task cards; review as `dt/dd` rows | Task screen padding tokens (10/14 px), one-line purpose, figures as compact `dt/dd` rows |
| Case home | `static/css/case_home.css` (`.ch-*`) | 10 px radius cards, 14/16 px padding, `auto-fit minmax(300px,1fr)` grid of panels; 13.5 px lists | `.ts-details-grid`: closed sections side by side (`minmax(300px,1fr)`) |
| Compact forms | `.gw-field` (label 4 px above input; 14 px between fields) | Label/input rhythm without big card gaps | `--label-gap` 4 px, `--field-gap-y` 10 px, `.ts-form` |
| Navigation density | `.nav-shortcut`, `.nav-section` | Secondary items visually subordinate | Kept Calibrayt's six primary destinations; no sidebar change needed |

---

## 3. Screen-by-screen audit (the 12 questions)

Questions: 1 active task - 2 must see now - 3 optional - 4 explanatory - 5 advanced - 6 history/reference -
7 Calibrayt can infer - 8 hide until requested - 9 side by side - 10 contextual instead of permanent -
11 fits? (before) - 12 why scroll.

### 3.1 Set Up This Project (`projects.create_project`, `projects/form.html`) — UX-DENSITY-001
1. Establish the project: customer, job, role, job site, plans, Create.
2. Customer choice and the customer (or a new customer's name); project name; what is being built; your role; street
   and town; plans choice; Create.
3. Client Project #, email and phone of a new customer, postal code, description, address as written.
4. The promise line; the plan choices' one-line explanations; "Brayman Project # assigned automatically".
5. Status, commercial type, permit class, the six settings, Project Lead, reason, start-the-estimate.
6. None.
7. Brayman Project #, commercial type (from what is built), all settings (company defaults), Project Lead (you),
   province and country (defaults), job site (copy from the customer).
8. New-customer fields when "A customer we have"; the customer list when "A new customer"; description; address as
   written; settings (already closed).
9. Customer choice + customer on one row; name + what is built + Client Project # on one row; the role as one row of
   choices; the five address fields on one row; the four plan choices on one row; settings four per row.
10. "Same as the customer's address" only with an existing customer; the plan explanations as tooltips on a laptop.
11. NO: Create at 1952 px (2.4 viewports).
12. Not necessary: every field was full height (label 20 px margin + 8 px + 12 px padding), fields stacked two per row,
    three radio options stacked at 44 px each, new-customer fields always shown, boxed fieldsets.

### 3.2 Price This Job (`guided.workflow`, `guided/workflow.html`)
1. Price the next work item (or go to Review when all are priced).
2. The one next step; the work list with each item's status and what it still needs.
3. Waiting calculations (when any), attention items.
4. "Open any work item, in any order…" line; the purpose line.
5. Calculators, supplier prices, line items, revisions, compare versions (in "More for this job").
6. Recent decisions.
7. The next item; totals.
8. More, Still to do, Recent decisions (already closed).
9. Work and next step on the left; progress, counts and totals on the right.
10. Totals as a compact 2 x 2 figure grid instead of four stacked rows.
11. NO: the work list ended at 978-1031 px.
12. Not necessary: one column, a full-width progress card with an unstyled `dl` (four 46 px rows), 16 px card padding
    and 14 px margins, closed sections stacked one per row.

### 3.3 Review This Estimate (`guided.pricing`, `guided/pricing.html`)
1. Approve the estimate (Gate 1) — or see what blocks approval.
2. The decision with its consequence and total; the figures it is approved on (direct cost, selling price, gross
   profit, true margin, customer total); the rates (labour rate, margin, HST, winter) that produce them.
3. The reason for an override; winter settings.
4. "What Calibrayt already knows".
5. The separate costing and pricing steps; the proposal; into the build (already closed).
6. None on screen.
7. The rates (company defaults), the figures.
8. Nothing decision-critical: the figures and rates stay visible (mandate: Ben must see enough to approve).
9. Rate, margin and HST on one row; winter on the next; reason and Save on the last; figures beside them; the
   "already knows" facts in two columns; the closed sections three across.
10. The winter explanation as the checkbox tooltip.
11. YES for the decision (366 px) but the figures needed scrolling past a 700 px tall stack of inputs (doc 1789).
12. Not necessary: each pricing input took a full row with a note below.

### 3.4 Project page (`projects/detail.html`)
1. Do the job's one next step.
2. Identity (name, number, customer, address, stage), the Next step, what Calibrayt knows, what needs you.
3. Client Project # editor, operating identity.
4. Section hints.
5. Everything in the 12 closed sections and More actions.
6. History inside sections.
7. The next step itself (app/services/project_next_step.py).
8. Already closed.
9. Closed sections three across (they were one per row).
10. The jump strip duplicated the section list; on a laptop the grid itself names every part, so the strip shows
    only where the parts stack (narrower than 900 px).
11. YES (296 px) but the page was 1510 px tall of closed boxes.
12. Not necessary: 13 closed sections at 65 px each plus a two-row strip naming the same sections.

### 3.5 Home (`dashboard.html`)
1. See what needs you; start something.
2. The top five attention items; Start something (three Guided Tasks).
3. Continue where you left off; today and coming days.
4. Task "why" lines.
5. Current work in numbers (closed).
6. —
7. —
8. Already done in ec80e6f1.
9. Today / Coming days already side by side.
10. —
11. YES (594 px).
12. Small overflow is the Today / Coming days reference below the task. Benefited from shared chrome only.

### 3.6 Attention (`/operations/attention`) and the Home list
1. Open the item that needs you. 2. The list. 3. Waiting on others (closed). 4. One purpose line. 5–8. —
9. Filters on one row. 11. YES (290 px). 12. Only when the list is long (genuine content). Shared chrome only.

### 3.7 Projects list
1. Find and open a project; start one. 2. Search, Start, the rows. 11. YES at 800 (725 px), NO at 720. 12. Only
the list length. Shared chrome (header, workspace padding, inputs) brings the first six rows inside 720 px.

### 3.8 Documents (company library, project, customer, supplier, subcontractor, person, equipment pages)
1. Find a document or upload one. 2. Search, type, filed on, status, Find; Upload; the first rows.
3. Due within, uploaded from/to. 4. The purpose line. 8. The three date filters behind "Dates" (open on their own
when one is set). 9. Filters on one row. 11. YES at 800 (757 px library), NO at 720. 12. Only the length of the
list. Context pages already fit (418 px); equipment page fits (506 px).

### 3.9 Purchasing and Time & Money landings (`task_landing.html`)
1. Open what waits on you here; reach a page of the area. 11. YES (354 / 490 px). Link tiles 56 -> 44 px.

### 3.10 Field Today (phone, `field/today.html`)
1. Enter time / capture on today's job. 2. Today's work and its primary action. 3. Quick actions (owner approved,
kept). 4. The one-time "Get a text" question (consent text). 5. More for today (closed). 6. Recent observations.
7. —. 8. The texts question moves below today's work (still asked on the screen). 9. —. 10. —.
11. NO: primary action at 1503 px on an 844 px phone. 12. Not necessary: the texts question (about 520 px) sat above
the work; the address had two empty lines from template whitespace; 52 px quick actions.

### 3.11 Calendar (`/schedule`)
Its own layout (the month box takes the height from its top to the bottom of the window). 11. Marginal: the box was
measured before the page finished loading and ended ~40 px below the screen. 12. Fixed by measuring again on `load`.
The months scroll inside their own box by design (genuinely detailed information).

### 3.12 Shared components (cause of vertical expansion)
| Component | Cause | Change |
|---|---|---|
| Global `label` / `input` (app.css, v1-refinement.css) | label margin 20 px + input margin 8 px + padding 11-12 px | inside the office workspace: 10 px / 4 px / 6 x 10 px, 38 px control height on a mouse laptop, 44 px on touch and phone |
| `.form-panel` | 22-28 px padding | 16 x 20 px |
| Header | 64 px; company and user labels squeeze the title | 52 px; labels collapse to icons below 1440 px |
| Workspace | 16 px top, 56 px bottom | 12 / 32 px |
| `.ts-context`, `.ts-next`, `.ts-state`, `.ts-attention`, `.ts-details` | 12-16 px padding, 16 px grid gap, 44 px summaries on desktop | 10 x 14 px padding tokens, 12 px gap, 38 px summaries on a mouse laptop |
| `.ts-purpose` | title and why stacked | one line where it fits; the title not repeated on a laptop when the top bar shows it |
| Closed sections | one per row | `.ts-details-grid`, one-line hints |
| Flash messages | 14 x 18 px | 8 x 16 px |
| Link hub tiles | 56 px | 44 px |

---

## 4. Reusable density and layout rules (adopted)

1. **Vertical budget at 1280 x 800:** header 52 + workspace 12 + task. The active task must end above 800 px.
2. **Tokens, not literals** (`tokens.css`): `--control-height` 38, `--control-pad-y/x` 6/10, `--label-gap` 4,
   `--field-gap-y/x` 10/14, `--stack-gap` 12, `--card-pad-y/x` 10/14, `--workspace-pad-top/bottom` 12/32.
   Touch targets stay 44 px on coarse pointers and at 720 px and below. Text never below `--text-sm`.
3. **One title.** The top bar names the screen; the task screen does not repeat it on a laptop
   (`ts.purpose(..., title_in_header=True)`); one line of purpose.
4. **Fields that belong together share a row** (`.ts-form .ts-row`); choices with short labels are one inline row
   (`.ts-inline`).
5. **Show only the branch that applies** (customer we have / new customer): the other branch is hidden, not removed,
   so the submitted form is unchanged.
6. **Optional and advanced parts are closed** (`.ts-optional`, `ts.details`) and **open on their own** when the
   screen comes back refused with something typed there or a problem in them.
7. **Closed sections sit side by side** (`.ts-details-grid`); an opened one takes the full row.
8. **Two working columns on a laptop** (`.ts-cols`): the task left, what it is decided on right; one column below
   1100 px.
9. **Decision-critical figures are never hidden** (Review This Estimate keeps the figures and rates in view).
10. **Fieldsets are light groups** (a rule and an inline legend), not boxed cards inside a card.
11. **Phones keep the semantic order** with the primary action first; one-time questions go after the day's work.

---

## 5. Implementation plan (executed in this branch)

1. Baseline walk `evidence_density.mjs` + `density_page_server.py` (measure only, `DENSITY_BASELINE=1`). Done first.
2. Shared: tokens; task-screen.css density layer (forms, cards, details grid, two columns, compact form, header,
   flash); guided-estimating.css task-screen overrides; project pricing compact rows (v1-refinement.css); field.css
   phone density.
3. Set Up This Project: TDD (`tests/test_viewport_density.py`) for the customer branch, the optional parts opening on
   refusal, then the template.
4. Price This Job: two columns, details grid. Review This Estimate: pricing rows, facts in two columns, details grid.
5. Project page: details grid; strip only below 900 px; fixed the doubly escaped "Scope &amp;amp; Estimate".
6. Documents library: date filters behind "Dates". Field Today: texts question after the work; address whitespace;
   44 px quick actions. Calendar: re-fit on `load`.
7. The density walk asserts the standard at 1280 x 800 (and records 1280 x 720 and phone), added to the release gate.
8. Existing tests and the 29 browser walks re-run; ledger section appended.

Results after implementation are in `docs/implementation/task-first-rdims-ledger.md`, section "Viewport-first
density corrective (2 Nov 2026)".

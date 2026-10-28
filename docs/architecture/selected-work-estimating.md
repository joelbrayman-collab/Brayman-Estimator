# Selected-work estimating (Approach B)

| Attribute | Value |
|---|---|
| Status | Approved by Joel, 28 Oct 2026 (Approach B). Design and implementation plan. |
| Principle | **Pick the work. Estimate the work. Everything else stays out of the way.** |
| Replaces | The contractor-facing "classify every generic construction stage" scope (v1rel9 Guided Estimating, 23 Oct 2026) for every new estimate. Existing estimates keep the stage model they were made with. |

## 1. Root cause of the clutter (current model)

`app/services/guided_estimating.start_guided_estimate` copies a whole **project-type template**
(`TEMPLATES[project_type]`, 4 to 15 generic stages, each with its parts) into `guided_estimate_stages` the moment a
guided estimate starts. Every copied row is "undecided" (`responsibility IS NULL`) and `save_scope(finalize=True)`
refuses until **every** row is Internal, Subcontracted or N/A. So:

- the scope is the template, not the work: a siding job on an "Addition / Renovation" carries 15 stages;
- N/A is the only way to say "we are not doing this", so a siding job records 11+ N/A decisions;
- `workflow_view` counts and lists N/A rows ("Excluded / N/A 11"); the wizard spends three steps (type & role,
  review the stages, Internal / Subcontracted / N/A) on the template; "Add a stage" adds more of the taxonomy;
- the manual Construction Scope page is the same template with the same rule.

Project Creation (step 5, role) calls the same `start_guided_estimate`, so every new project gets the template.

## 2. The model

```
PROJECT → ESTIMATE → SELECTED WORK SCOPE (one source of truth) → Guided or Manual → quantities / labour /
materials / subcontracts → pricing → proposal
```

**Selected work is the scope.** The scope of an estimate is exactly the work the contractor chose. Work that was
not chosen is not part of the project: no row, no decision, no N/A, no progress, no cost, no proposal line.

### Persistence: the existing tables, no migration

The scope already has one authoritative store per project, `guided_estimates` (one per project, linked to the
estimate it works on) with its rows in `guided_estimate_stages`. Its shape can represent selected work exactly,
so no parallel schema is added:

| Concept | Stored as |
|---|---|
| The project's scope (holder) | the project's one `GuidedEstimate` row (`estimate_id` = the estimate it governs) |
| Scope model | an append-only `GuidedEstimateEvent` `SCOPE_MODEL` → `SELECTED_WORK`, written when the scope is created. No such event = the legacy stage model (every scope made before this release). |
| A selected work item | one top-level `GuidedEstimateStage`: `stage_key` = the work-catalogue key (`work_siding`) or `custom_<name>` for named work |
| Responsibility | the row's `responsibility`: `INTERNAL` or `SUBCONTRACTED` (asked only for selected work) |
| Mixed responsibility | the existing split: `is_split` and two parts, `<key>.materials` and `<key>.installation`, each with its own responsibility |
| Removed work | the row stays (its history and audit events reference it); `responsibility = NA`, status `EXCLUDED`, event `WORK_REMOVED`. In the selected-work model an NA row is **not shown anywhere** — it is simply not part of the estimate. Adding the same work again reuses the row (`WORK_ADDED`). |
| Quantities, labour, materials, subcontract quotes, allowances, pricing | unchanged: the estimate's own sections and lines (one section per work item or part), scope-delivery quotes, costing snapshot, pricing, proposal |

`DATA MIGRATION REQUIRED: NO` — no table or column changes, no data rewritten. Existing scopes have no
`SCOPE_MODEL` event and keep the legacy behaviour unchanged.

### One service: `app/services/selected_work.py`

Every entry point uses it; templates and routes hold no scope logic.

- `catalogue()` — the work catalogue: categories (navigation only — choosing a category adds nothing) and work
  items (what is actually estimated), each with the calculators and costing tools that fit it.
- `ensure_scope(org, project_id, actor, estimate_id=None)` — the project's scope, created on first use in the
  selected-work model (never seeded with work).
- `work_items(guided)` — the selected work, in order.
- `add_work(guided, keys, custom_name, actor)` — adds catalogue or named work (Internal by default; the
  contractor changes it to Subcontracted in one choice). Ensures the estimate and one section per work item.
- `set_responsibility`, `split_work` (progressive disclosure: materials and installation by part).
- `removal_check(row)` / `remove_work(guided, row, actor)` — removal is refused while the work holds estimate
  data (lines, calculations, a requested quote, an allowance, a no-cost decision, a completion, notes): the
  message says what is there and that it must be removed first, the same rule the stage model used for N/A. Empty
  work is removed after confirmation; its empty section is removed; the history keeps the event.
- `progress(guided)` — done / total over selected work only.
- `convert_legacy_draft(guided, actor)` — explicit, person-triggered only (see §6).

`app/services/guided_estimating.py` keeps every costing, completion, quote, allowance, revision and proposal rule.
It learns the selected-work model in four places only: `spec_for` resolves work-catalogue keys; `start_guided_estimate`
creates selected-work scopes (legacy templates only on explicit request, for legacy fixtures);
`scope_rows`/`leaf_stages` leave removed (NA) work out in the selected-work model; `workflow_view` and
`guided_blockers` count selected work only.

## 3. Work catalogue

Built from the existing stage library (same calculators and tools), at the level a contractor names work:

| Category (navigation) | Work |
|---|---|
| Exterior | Siding · Soffit, fascia & trim · Roofing · Windows · Exterior doors · Garage door · Deck |
| Structure | Wall framing · Floor framing · Roof framing |
| Foundation & site | Demolition · Site preparation · Excavation · Footings · Foundation walls · Concrete slab · Waterproofing & drainage |
| Interior | Insulation · Drywall · Flooring · Trim & baseboard · Interior doors · Cabinets & counters · Painting · Stairs & railings |
| Mechanical & electrical | Electrical · Plumbing · HVAC |
| General | Final cleanup |
| Other | any named work ("Septic system") |

The project type (Renovation, New home, …) stays a fact about the project and orders nothing into the scope.

## 4. Journeys

**Guided** (wizard "Guided Estimating"): Select the project → **What work are we doing?** (choose work; Internal /
Subcontracted for each; split materials and installation only if wanted) → Measurements and quantities (only if
there is internal work) → Calculators for internal work (internal work only) → Request quotations / Record and
select quotations (only if there is subcontracted work) → Supplier pricing → Review costs → Internal cost →
Pricing → Proposal → Acceptance. The legacy steps "Project type and your role", "Review the construction stages"
and "Internal, Subcontracted or N/A" apply only to legacy scopes.

**Manual**: Project → Estimate (or Estimating workflow) → **Add work** → choose the work → each work item's page
(quantities, calculators, labour, materials, subcontract quote) → Internal cost → Pricing → Proposal. No wizard.

**Project Creation handoff**: step 5 keeps the contractor's role (a fact about the job) and starts the project's
scope in the selected-work model with no work in it; finishing into Guided Estimating opens **What work are we
doing?** — the one place work is chosen. No stage list is created or shown in Project Creation.

**One "Add work"**: the Guided step, the Work page (formerly Construction scope), the estimating workflow, the
project page and the estimate page all use the same selector and the same `add_work`.

**Synchronization**: there is one scope row per work item and one estimate; the wizard and the manual pages read
and write those same rows and lines. Nothing is copied, so nothing needs synchronizing.

## 5. Progress

`done / total` over selected work (a split work item counts once; it is complete when its parts are). Removed
work is not counted. One selected item = 1 of 1.

## 6. Existing estimates

- **Completed / issued / accepted (legacy)**: unchanged and read by the legacy rendering path (N/A rows still
  shown where they were decided). Nothing is converted.
- **Legacy drafts**: unchanged by the release. The Work page of a legacy draft offers an explicit, person-triggered
  **Switch this draft to selected work**: Internal and Subcontracted stages stay as the work; stages that were N/A or
  never decided leave the estimate (each decision stays in the history). Refused if an accepted proposal exists.
  Nothing is converted silently. For **Paulusse & Bonokoski** (an active legacy draft) this is the safe path after
  release, if Joel chooses it.

## 7. Plan-upload defect (28 Oct 2026)

Fixed separately on `fix/project-creation-step4-2026-10-28` (Save & Continue busy state, duplicate-PDF guard);
this branch is built on that fix and does not change it.

## 8. Implementation plan (as built, test first)

| # | Change | Files | Proven by |
|---|---|---|---|
| 1 | Work catalogue and the one scope service | `app/services/selected_work.py` | `tests/test_selected_work.py` (catalogue, add, named work, responsibility, split, remove, progress, legacy conversion) |
| 2 | New scopes start empty in the selected-work model (legacy templates only on explicit request); removed work is out of every count | `app/services/guided_estimating.py` (`start_guided_estimate(legacy_stages=False)`, `scope_rows`, `leaf_stages`, `change_responsibility`, `workflow_view`, `guided_blockers`, `spec_for`) | same, plus the legacy suites `tests/test_guided_estimating.py`, `tests/test_guided_owner_decisions.py` on the legacy fixture (`Driver.new_project(..., legacy=True)`) |
| 3 | Work page replaces the Construction Scope page for selected-work scopes; the legacy page offers the explicit switch | `app/routes/guided_estimating.py`, `app/templates/guided/work.html`, `app/templates/guided/scope.html` | tests 1–13, 17–18 |
| 4 | Guided Estimating wizard: "What work are we doing?" replaces the three legacy steps for selected-work scopes; its form is sent by Next (`continue_form` honoured by the full wizard layout) | `app/wizards/estimating.py`, `app/templates/wizards/forms/ge_work.html`, `app/templates/wizards/_run.html` | `test_wizard_and_manual_work_on_the_same_scope_and_the_same_lines`, `evidence_selected_work.mjs` |
| 5 | Project Creation keeps the role and hands over with no stages | `app/wizards/new_project.py`, `app/routes/projects.py` | `test_project_creation_hands_over_a_scope_with_no_stages`, `tests/test_wizards.py`, `tests/test_project_creation_ux.py` |
| 6 | One "Add work" on the estimate page and the project page | `app/routes/estimates.py`, `app/templates/estimates/detail.html`, `app/routes/projects.py`, `app/templates/projects/detail.html` | `test_manual_estimate_add_work_governs_that_estimate_without_the_wizard`, browser manual journey |
| 7 | Work-item pages offer Internal / Subcontracted only (no N/A) | `app/templates/guided/stage.html` | browser guided journey |
| 8 | Browser evidence | `tools/release/evidence_selected_work.mjs` (new, 10 checks, in the release gate), `tools/release/evidence_guided_estimating.mjs` (rewritten for selected work, 19 checks) | `BROWSER_EXPECTED` 279 with the separate calendar month-fit fix (`65982f0`, +4) |

No migration, no model change, no data rewritten.

## 9. Verification

- Guided: Project Creation → Guided Estimating wizard "What work are we doing?" → Siding (Internal) and Windows
  (Subcontracted) → quantities and labour, a selected quote → internal cost → wizard pricing → proposal; only that
  work anywhere and no N/A.
- Manual: project → estimate → Add work (Flooring) → costs → pricing → proposal, no wizard run.
- Cross-entry: work chosen in the wizard is on the Work page and the estimate; work added on the estimate page is in
  the wizard; empty work removed after confirmation disappears everywhere; work holding estimate lines cannot be
  removed.
- Desktop 1280 × 900 and iPhone 390 × 844 (no sideways scroll, 44 px choices).

# Feature Gate FG-025: Contractor-Facing UX Language & Terminology Standardization

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-025` |
| Feature Name | Contractor-Facing UX Language & Terminology Standardization |
| Target Milestone | **None.** FG-025 is the governing identifier. Do not assign a new M0xx number. This is a **commercialization hygiene** gate, not a new lifecycle stage. Sequence: **after [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) closes**, **before** broad external UAT / U.S. commercialization. |
| Module | **Cross-cutting UX copy.** [Projects](../modules/projects.md) owns Project Hub chrome. Owning modules retain their screens: Plan Intelligence, Estimating, Pricing Engine, Proposals, Project Controls, BUILD, MONITOR, LEARN (Future), authentication. This gate does **not** transfer record ownership. |
| Date | 2026-09-07 |
| Status | **FUTURE / RECORDED / IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / TESTED / COMMITTED / PUSHED / SLICE 2 IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT CLOSED / NOT A PRODUCT-WIDE SWEEP** (2026-09-07). Remaining FG-025 slices / surfaces are **NOT AUTHORIZED**. Do **not** treat this gate as closed. |
| Architecture | [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** (PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN) · [FG-011](FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT** (Hub reads/links; Future labeled) · [FG-012](FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** (office vs customer-facing estimate copy) · [FG-017](FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT** (visual brand, not terminology) · [FG-021](FG-021-field-web-v1-today-and-capture.md) **CLOSED** (Field Web capture copy) · [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT** · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |
| Related ADRs | **None new in this recording pass.** Visual identity remains [ADR-040](../adr/ADR-040-organization-brand-profile.md). Do **not** accept ADR-008 or ADR-010 from this gate. |
| Prerequisites | [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) is **CLOSED / OPERATIONAL FOR UAT**. Slice 1 and Slice 2 were each authorized by a bounded Joel/ChatGPT prompt (2026-09-07). Remaining slices remain **NOT AUTHORIZED**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **RECORDED.** **IMPLEMENTATION PREFLIGHT COMPLETE.** **SLICE 1 IMPLEMENTED.** **SLICE 2 IMPLEMENTED.** **NOT CLOSED.** |
| UI copy rewrite | **SLICE 1 AND SLICE 2 AUTHORIZED AND IMPLEMENTED.** Remaining surfaces **NOT AUTHORIZED.** |
| Product code | Presentation mapping `app/presentation/contractor_copy.py` + Project Hub (`detail.html`) PLAN/PRICE/CONTRACT/BUILD/MONITOR display. |
| Schema / Alembic | **None.** |
| New ADR | **None.** |

```text
FG-025:
FUTURE / RECORDED
IMPLEMENTATION PREFLIGHT COMPLETE
SLICE 1 IMPLEMENTED / TESTED / COMMITTED / PUSHED
SLICE 2 IMPLEMENTED / TESTED / COMMITTED / PUSHED
NOT CLOSED
NOT A PRODUCT-WIDE SWEEP
REMAINING FG-025 SLICES / SURFACES: NOT AUTHORIZED
FG-023: CLOSED / OPERATIONAL FOR UAT
FG-024: FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED
ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION
```

Joel/ChatGPT recorded this gate on **2026-09-07**. Preflight completed the same day. Bounded prompts authorized Slice 1 then Slice 2 the same day. The gate is **NOT CLOSED**. Remaining surfaces stay unauthorized. FG-023 remains **CLOSED**. Do **not** start Slice 3 from this document.

---

## Purpose

Perform a **product-wide sweep** of user-facing language across PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN so CalibAi presents **contractor-facing, plain-English** terminology rather than internal technical, database, governance, or developer language.

Internal model/state names may remain technical in code, tests, architecture, and governance. User-facing UI must not leak those names unless the term is already normal construction-industry language, or Joel/ChatGPT later approve a specific exception.

---

## Product rule (governing)

```text
CODE / TESTS / ARCHITECTURE / GOVERNANCE
  may keep technical enums, table names, and state keys.

CONTRACTOR-FACING AND CUSTOMER-FACING UI
  must use language a contractor or project manager would naturally use
  unless the technical term is already normal construction-industry language.

Raw internal enums, database terms, implementation-state names, and
developer phrasing must not appear on contractor-facing or customer-facing
screens without intentional product approval.
```

This rule does **not** rename commercial identities, schema columns, or MONITOR calculation keys. It governs **display copy**.

Final contractor-facing strings are **not pinned** in this recording unless already governed elsewhere. Directional examples below are **illustrative only**.

| Internal (keep in code) | Illustrative contractor-facing direction (not pinned) |
|-------------------------|--------------------------------------------------------|
| `MISSING_ACTUALS` | No actual costs entered yet |
| supersede actual | Correct this cost |
| Actual-to-Date GM | Gross Margin So Far, or another contractor-approved equivalent |
| Current Authorized Pre-Tax Revenue | Current Contract Value Before Tax, or another governed equivalent |

Lifecycle stage labels **PLAN / PRICE / CONTRACT / BUILD / MONITOR / LEARN** remain product language ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)). Do not invent a second lifecycle vocabulary.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Screens mix contractor language with internal enums and implementation-state names (especially MONITOR Hub). That will not survive broad external / U.S. commercialization. |
| 2 | Who is the user? | Future review must evaluate owner, estimator, project manager, office administrator, field user, any subcontractor-facing surface, and external customer-facing documents. Roles need not share identical wording. |
| 3 | Which module owns it? | **Cross-cutting copy standard.** Each owning module keeps its screens. Projects owns Hub chrome. No new module. No new durable record. |
| 4 | What data does it own? | **None.** Display strings only. |
| 5 | What data does it reference? | Existing screens and flashes across office, Field Web, and generated customer documents. Does not mutate commercial SoR. |
| 6 | What may it change? | **This recording:** this document and current-authority pins only. **Later implementation:** user-visible copy in templates/JS/flashes under a bounded prompt. |
| 7 | What must it not change? | FG-023 product meaning, close sequence, commercial identities, schema, migrations, MONITOR arithmetic, Field Evidence semantics, Legal Content Gate, FG-024 slices, tests’ internal state keys unless a later prompt explicitly maps display vs domain. |
| 8 | What are the acceptance criteria? | **This recording:** FG-025 exists; FUTURE / NOT IMPLEMENTATION-AUTHORIZED; inventory started; FG-023 unchanged. **Implementation acceptance:** later, after FG-023 close and a separate authorization. |
| 9 | What tests are required? | **This recording:** none. Product pytest **not re-run**. Later: Hub/Field/office copy assertions that display strings are contractor-facing while domain keys stay stable. |
| 10 | What documentation must be updated? | This gate; feature-gates README; docs README; platform-roadmap; platform-governance; current-state; session-handoff; project-state-report; chat-workflow-log; milestones; bounded FG-023/FG-024 cross-pins. |
| 11 | Is an ADR required? | **No** for this recording. A later implementation may need an ADR only if copy policy would change a frozen commercial identity or Constitution article. |
| 12 | Does it require a database migration? | **No.** |

---

## Existing authority (do not duplicate)

| Authority | What it already covers | Relation to FG-025 |
|-----------|------------------------|--------------------|
| [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) / [FG-011](FG-011-project-hub-ux.md) | Lifecycle hub; operational vs Future labels; Hub reads/links | **Extend.** Stage names stay. Hub **copy quality** is not a terminology standard. |
| [FG-012](FG-012-estimate-output-consistency.md) | Office internal breakdown vs customer-facing Proposal/PDF | **Extend.** Customer vs office distinction exists; not a product-wide lexicon. |
| [FG-013](FG-013-contractor-calibration-onboarding-historical-upload-ux.md) | One TIER_A review label (“Estimate associated with a completed project”) | **Extend.** Local label only. |
| [FG-017](FG-017-organization-brand-profile-v1.md) / [ADR-040](../adr/ADR-040-organization-brand-profile.md) | Visual brand (logo, colors, issued snapshot) | **Do not duplicate.** Brand ≠ terminology. |
| [FG-021](FG-021-field-web-v1-today-and-capture.md) | Field capture UX; some contractor-facing Save/Retry copy | **Extend.** Field strings still in sweep; do not reopen FG-021 product meaning. |
| [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) | Frozen MONITOR identities and Hub metric labels | **Extend display only after close.** Do **not** amend commercial identities in this recording. |
| [pricing-policy.md](../pricing-policy.md) | Pricing **formula** terminology for reconciliation | **Do not silently rename** governed pricing terms. Contractor display may later differ from policy names if Joel approves. |
| Constitution / architecture principles | Ownership, immutability, no invented business rules | **No product-wide UX language article exists.** |
| [FG-024](FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) | Future legal-content / contract generation | **Separate gate.** FG-025 is **not** a split of FG-024 slices. Future contract **UI** copy is in FG-025 scope; legal content remains FG-024 / Legal Content Gate. |

**Verdict:** FG-025 **extends** existing Hub, Field, and customer-document copy practice into a product-wide contractor-facing language standard. It does **not** duplicate FG-017 brand, FG-024 legal content, or FG-023 commercial arithmetic.

---

## Scope of the future sweep

Minimum surfaces (do not rewrite now):

- page titles
- section headings
- navigation / sidebar / header
- lifecycle labels (wording around PLAN → LEARN, not a second lifecycle)
- buttons and action links
- field labels, helper text, tooltips
- status chips
- empty states, warning states
- validation messages, flash messages, errors
- confirmation language
- table headings and column labels
- MONITOR metrics
- BUILD actual-cost language
- proposal / estimate language
- permit language
- authentication / account language
- future contract language (display only; Legal Content Gate unchanged)

### Surface inventory (later implementation)

| Surface | Code home (inspect later) |
|---------|---------------------------|
| Project Hub | `app/templates/projects/detail.html`, `app/services/project_hub.py` |
| Office shell / nav | `app/templates/partials/header.html`, `sidebar.html`, `app/navigation.py` |
| Auth | `app/templates/auth/login.html`, auth flashes |
| CRM / Projects lists | `app/templates/clients/`, `app/templates/projects/` |
| PLAN | `app/templates/plan_intelligence/`, permit report, location edit |
| PRICE | `app/templates/estimates/`, `labour_engine/`, `pricing_engine/`, `cost_library/`, `assemblies/`, `material_catalogue/` |
| CONTRACT | `app/templates/proposals/`, `proposal_templates/` |
| BUILD | Change Orders `app/templates/project_controls/`; Field Observations `app/templates/build/`; Field Web `app/templates/field/`, `app/static/js/field.js` |
| MONITOR | Hub `#hub-monitor` block; BUILD actuals create/correct forms |
| LEARN | Hub Future note only today |
| Historical upload | `app/templates/historical_estimates/` |
| Settings / brand | `app/templates/settings/brand_profile.html` |
| Customer documents | Proposal preview/PDF; Permit HTML/PDF; later FG-024 contract UI |
| Flashes / errors | owning `app/routes/*.py` |

This inventory is a **starting list**, not a claim of exhaustiveness.

---

## Internal-term leakage inventory (flag only — do not rewrite)

Inspected 2026-09-07. Examples of **user-visible** internal/developer phrasing. Not a complete corpus; later implementation must re-walk templates and JS.

### MONITOR / BUILD Hub (`app/templates/projects/detail.html`)

| Visible copy | Why flagged |
|--------------|-------------|
| `MISSING ACTUALS` / `MISSING CUSTOMER COMMITMENT` / `AMBIGUOUS COMMITMENT` / `MISSING ORIGINAL BASELINE` | Domain enum rendered as UI headline |
| `no ACTIVE office actual-cost entries` | Implementation-state (`ACTIVE`) in helper copy |
| `Actual Direct Cost — other_direct` | Enum `other_direct` as a label |
| `Actual-to-Date Project Gross Margin` | Internal metric name |
| `GM Variance` | Abbreviation-first, not contractor phrasing |
| `Current Authorized Pre-Tax Revenue` | Governance identity used as Hub label |
| `Provenance: source version … snapshot …` | Developer/audit vocabulary on the Hub |
| `ACTIVE actuals` / `Superseded actuals` / `SUPERSEDED` | Correction mechanics leaked as section titles |
| Button `Record correction` | Closer to contractor language — **keep as a candidate**, do not freeze |

`Record correction` on Field Event and actuals forms is already nearer the intended direction than `supersede`.

### Other office surfaces (sample)

| Surface | Visible examples |
|---------|------------------|
| Pricing Engine | `Provenance`; button `Supersede (new draft version)` |
| Labour Engine | `Provenance`; `Superseded by` ids |
| Historical estimates | `Inspect Provenance`; `Source-Cell Provenance Observations` |
| Take-off package | `Provenance: run … provider … config hash` |
| Location edit | `supersedes the current preliminary profile` in helper text |
| Permit findings | status chips `MISSING_INFORMATION` / `POTENTIAL_NON_CONFORMANCE` (To be verified as exact Hub/report labels in implementation) |

Code/tests may keep `MISSING_ACTUALS`, `assemble_monitor_v1`, `supersedes_id`. FG-025 forbids **display** of those names without approval.

---

## Role / audience

Future review must not assume one glossary for every role.

| Audience | Copy concern |
|----------|----------------|
| Owner / principal | Commercial outcome language (margin, contract value) without ledger jargon |
| Estimator | Precision retained where construction estimating already uses the term (Change Order, Direct Cost, Gross Margin) |
| Project manager | Job progress vs estimate; avoid schema names |
| Office administrator | Account/login and list screens |
| Field user | Short, action-first copy (FG-021 already started this) |
| Subcontractor-facing (if any later) | Separate review; none operational as a distinct surface today |
| External customer documents | FG-012 already splits office vs customer; FG-025 must not put Hub enum names on PDFs |

**Error / empty-state quality (future requirement):** every flagged empty, warning, and error state should say (1) what happened, (2) why it matters, (3) what to do next — in contractor language.

---

## Sequencing

```text
1. FG-023 MONITOR close
2. FG-025 contractor-facing terminology sweep
3. Broader external / U.S. commercialization and later roadmap items
```

- Does **not** reopen FG-023. Slice C remains **PASS**. FG-023 is **CLOSED / OPERATIONAL FOR UAT**. This gate remains **NOT IMPLEMENTATION-AUTHORIZED**.
- Does **not** authorize FG-024 implementation or legal-content population.
- Does **not** jump LEARN (roadmap item 14) or QuickBooks (item 16) as the next coded stream.
- **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

---

## Out of scope (this recording and later unless separately authorized)

- Product-code or template edits in this pass
- Renaming database columns, enums, or test fixtures
- Changing MONITOR arithmetic or commercial identities
- FG-023 close
- FG-024 legal content
- Visual rebrand (FG-017)
- Inventing construction business rules
- Subcontractor portal (does not exist)

---

---

## IMPLEMENTATION PREFLIGHT (2026-09-07)

**Status:** **PREFLIGHT COMPLETE.** **NOT IMPLEMENTED.** **NOT CLOSED.** **NOT IMPLEMENTATION-AUTHORIZED.**

Inspect date: 2026-09-07. Parent SHA `00c763b1a5d936eaa3b825105ffa0001b48c5ef5` (`docs: close FG-023 MONITOR V1`). Live current = heads `e3f4a5b6c7d8`. Field **39 / 39**. FG-023 **CLOSED / OPERATIONAL FOR UAT**. No product-code change in this pass. No separate architecture recon file: this gate remains the authority.

### Preflight principle

```text
INTERNAL TECHNICAL LANGUAGE MAY REMAIN INTERNAL.
USER-FACING LANGUAGE MUST BE CONTRACTOR-FACING.
Prefer a presentation-layer mapping. Do not rename model fields,
enums, or schema columns merely to change display copy.
```

Lifecycle stage names **PLAN / PRICE / CONTRACT / BUILD / MONITOR / LEARN** remain product language ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)). LEARN remains **Future**.

### C. Product-wide UI surface inventory (current)

73 office/Field HTML templates + 3 JS files + shell nav. User-facing copy is **mostly embedded in Jinja**. Flash strings originate in `app/routes/*.py`. Field live feedback is in `app/static/js/field.js`. CSS has **no** contractor copy (`content: "/"` breadcrumb only). Customer Proposal preview/PDF is a **separate audience** (FG-012).

| Surface | Files | Notes |
|---------|-------|--------|
| Shell / nav | `app/templates/base.html`, `partials/sidebar.html`, `partials/header.html`, `app/navigation.py` | Dashboard, Clients, Projects, Estimating group, Project Controls, Settings. Disabled: Purchase Orders, Job Costing, Reports, AI Assistant (**Soon**). |
| Auth | `app/templates/auth/login.html`, `app/routes/auth.py` | “Office sign in”; “organization membership credentials”. |
| Dashboard | `app/templates/dashboard.html`, `partials/dashboard_cards.html` | “Executive overview”; Recent Estimates / Proposals. |
| Clients / Projects lists | `app/templates/clients/*`, `projects/list.html`, `projects/form.html` | CRM; project status chip is stored `project.status`. |
| Project Hub | `app/templates/projects/detail.html`, `app/services/project_hub.py` | Lifecycle chips; PLAN/PRICE/CONTRACT/BUILD/MONITOR; LEARN Future. Highest leakage. |
| PLAN / location / permit | Hub PLAN panel; `projects/edit_location.html`; `projects/permit_report.html`; `plan_intelligence/*` | Permit findings render `finding.status.replace('_', ' ')` (still ALL_CAPS words). |
| PRICE estimates | `estimates/*`, `assemblies/*`, `cost_library/*`, `material_catalogue/*` | Internal breakdown leaks class names (`EstimateVersion`, `EstimatePricingSnapshot`). |
| Labour / pricing engines | `labour_engine/*`, `pricing_engine/*` | Office-specialist; raw `Provenance`, `SUPERSEDED`, `organization_id`. |
| Historical | `historical_estimates/*` | `TIER_A` chip; FG-013 mapped sentence exists for review status. |
| CONTRACT office | `proposals/*`, `proposal_templates/*` | Office detail still shows Overhead/Profit rows; customer preview omits them (FG-012). |
| BUILD office | Hub BUILD; `build/event_form.html`, `build/event_detail.html`; Change Orders `project_controls/change_orders/*` | Field observation “Superseded”; actuals “ACTIVE actuals”. |
| Field Web | `field/today.html`, `capture.html`, `projects.html`, `field.js` | Action-first; “Save original”; `SAVED` / `SAVING` / `NEEDS RETRY`. |
| MONITOR | Hub `#hub-monitor` | Raw MONITOR states and metric identities. |
| LEARN | Hub `#hub-learn` | Future placeholder only. Keep Future. |
| Settings | `settings/brand_profile.html` | Mostly contractor-clear. |
| Flashes | owning routes | Mix of contractor-clear (`Actual cost recorded.`) and technical (`Policy superseded. New DRAFT version created.`). |

### D–E. Leakage inventory and classification

Classes: **A** keep contractor · **B** keep industry · **C** rewrite technical · **D** improve awkward · **E** must not display raw · **F** customer-document separate · **G** Joel/ChatGPT decision.

| Visible copy (current) | File | Class | Notes |
|------------------------|------|-------|--------|
| Change Order, Direct Cost, Gross Margin, Allowance, Subcontract, Labour, Material, Permit | many | **A / B** | Keep. Do not “simplify” into job-costing slang. |
| PLAN / PRICE / CONTRACT / BUILD / MONITOR | Hub | **A** | Lifecycle product language. |
| LEARN · Future | Hub | **A** | Must remain Future. |
| `MISSING ACTUALS` / `MISSING CUSTOMER COMMITMENT` / `AMBIGUOUS COMMITMENT` / `MISSING ORIGINAL BASELINE` | `projects/detail.html` | **E** | Domain keys rendered as headlines. Domain keys in `monitor.py` **stay**. |
| `no ACTIVE office actual-cost entries` / `ACTIVE actuals` | Hub | **E** | Implementation-state `ACTIVE`. |
| `Actual Direct Cost — other_direct` and `<option>other_direct` | Hub | **E** | Enum as label. `labour`/`material`/`subcontract` are industry words; still capitalize for display. |
| `Actual-to-Date Project Gross Margin` | Hub | **D / G** | Accurate; abbreviation-first. |
| `GM Variance` | Hub | **D / G** | Keep meaning; wording not pinned. |
| `Current Authorized Pre-Tax Revenue` | Hub | **D / G** | Frozen FG-023 identity. Display may differ **only** if meaning is preserved. Flag: “contract value” can be read as a signed legal contract. |
| `Original Estimated GM` / `Approved/Invoiced CO Revenue Delta` | Hub | **D** | Estimator-precise; owner may want plainer labels. |
| `CO cost delta not stored` (`CO_COST_DELTA_COPY`) | `monitor.py` via Hub | **C** | Governance sentence on Hub. |
| `Provenance: source version … snapshot …` | Hub | **E** | Audit IDs. Offer a contractor “Source” line without raw table names. |
| `SUPERSEDED` chip / `Superseded actuals` | Hub | **C** | Correction history. Button `Record correction` is already nearer contractor language — **keep as candidate**. |
| Commercial Decision Gate Context / M011 helper | Hub | **C / D** | Governance milestone leak. |
| `PRELIMINARY / FOUNDATION ONLY` · `ADVISORY ONLY` · `RECHECK REQUIRED` · `AHJ` | Hub PLAN / permit report | **B / D** | Keep legal caution; drop ALL_CAPS where a sentence works. |
| `LOCATION_COMPLETE` displayed as “complete” | Hub | **A** | Already mapped. Pattern to copy. |
| Permit `MISSING_INFORMATION` → `MISSING INFORMATION` | `permit_report.html` | **E / C** | Underscore stripped; still enum English. |
| `TRUE_GROSS_MARGIN` / `COST_PLUS_MARKUP` / `COST_PLUS_MARKUP_STACK` | estimates, internal breakdown | **C / G** | Office-internal method names. Do not put on customer PDF. |
| `EstimateVersion` / `EstimatePricingSnapshot` headings | `internal_breakdown.html` | **E** | Class names on an office page. |
| `Organization {{ organization_id }}` | labour index, material catalogue, snapshots | **C** | Show company name, not `ORG-001`, unless Joel wants the code. |
| `Provenance` fields / `Supersede (new draft version)` | labour + pricing | **C** | Specialist office tools; still not contractor-facing. |
| `TIER_A` chip | historical index | **E** | FG-013 already mapped review-status sentences; evidence tier chip still raw. |
| `Inspect Provenance` / `Source-Cell Provenance Observations` | historical | **E** | Calibration reviewers may need source-cell detail — **G** whether to keep a technical sub-panel labeled “Where this number came from”. |
| Flash `Policy superseded. New DRAFT version created.` | `pricing_engine.py` | **C** | |
| Login “organization membership credentials” | `auth/login.html` | **D** | |
| Nav “Labour Engine” / “Pricing Engine” / “Historical Evidence” | `navigation.py` | **D / G** | Specialist names vs “Labour rates” / “Pricing” / “Previous estimates”. |
| Field `Save original` / `SAVED` / `SAVING` / `NEEDS RETRY` | Field templates + `field.js` | **D** | Action-first already; drop ALL_CAPS and “original” if Joel agrees. IndexedDB store names stay internal. |
| Proposal office Overhead / Profit amounts | `proposals/detail.html` | **F / G** | FG-012 already hides from customer preview/PDF. Office display is a known residual — wording vs whether to hide is **not** a casual FG-025 rewrite. |
| Customer Proposal/PDF legal-ish labels | `proposals/preview.html` | **F** | **Out of first implementation slices.** Not FG-024 legal content, but still a different audience. |
| `operational for UAT` | **not in product UI** (docs only) | — | Do not introduce into UI. |
| `ProjectDirectCostActual` / `organization_id` as code | models/services | — | **Keep internal.** Not a display string except where templates print `organization_id`. |

`ProjectDirectCostActual` does **not** appear as a Hub heading. `implementation status` / `operational for UAT` do **not** appear in templates (verified by search of product UI).

### F. Proposed contractor-facing glossary (not pinned)

Final strings require Joel/ChatGPT approval. Directional only.

| Internal term | Current user-facing | Recommended display (candidate) | Rationale | Surfaces |
|---------------|---------------------|----------------------------------|-----------|----------|
| `MISSING_ACTUALS` | MISSING ACTUALS | No actual costs entered yet | Empty state, not a fake $0.00 | Hub MONITOR |
| `MISSING_CUSTOMER_COMMITMENT` | MISSING CUSTOMER COMMITMENT | No accepted proposal yet | Contractor language | Hub |
| `AMBIGUOUS_COMMITMENT` | AMBIGUOUS COMMITMENT | More than one accepted proposal — this screen will not pick one | Preserve fail-closed meaning | Hub |
| `MISSING_ORIGINAL_BASELINE` | MISSING ORIGINAL BASELINE | An accepted proposal exists, but the original estimate cannot be used | Awkward accurate | Hub |
| `other_direct` | other_direct | Other direct cost | Enum leak | Hub forms/metrics |
| `labour` / `material` / `subcontract` | lowercase enum | Labour / Material / Subcontract | Industry terms; capitalize | Hub |
| supersede actual | SUPERSEDED / Superseded actuals | Corrected cost / Previous entries | Action already “Record correction” | Hub, BUILD |
| Provenance block | Provenance: source version… | Source of these numbers (proposal, estimate, pricing lock) — hide raw IDs unless a “details” disclosure | Audit ≠ Hub headline | Hub |
| Actual-to-Date Project Gross Margin | same | Gross margin so far | Owner-readable; **must remain** actual-to-date GM on current authorized pre-tax revenue | Hub |
| GM Variance | same | Margin change from the original estimate | Candidate; Joel may keep “GM” on estimator screens | Hub |
| Current Authorized Pre-Tax Revenue | same | Current authorized selling price before tax | **Flag:** “contract value” risks legal-contract confusion. Do not adopt “Current Contract Value” without Joel. | Hub |
| Original Estimated Direct Cost | same | Original estimated direct cost | **A** — keep | Hub |
| `CO_COST_DELTA_COPY` | CO cost delta not stored | Change Order estimated cost is not stored on the Change Order | Meaning preserved | Hub |
| Estimate / Proposal / Change Order | same | same | **A** — do not merge | all |
| Direct Cost vs Actual Cost | mixed “actual-cost” | Direct cost (estimated) vs Actual direct cost (entered) | Keep the distinction | Hub / BUILD |
| Client | Client | Client (office). Customer on generated documents | Do not rename CRM entity | CRM vs Proposal |
| Field Observation | Field observation | Field observation / note | **A** Field | BUILD / Field |
| `TIER_A` | TIER_A | Estimate associated with a completed project (already FG-013 for review status) | Map evidence-tier chips the same way | Historical |
| TRUE_GROSS_MARGIN | TRUE_GROSS_MARGIN | Target gross margin | Office PRICE only; **G** | Estimates |
| COST_PLUS_MARKUP_STACK | COST_PLUS_MARKUP_STACK | Legacy markup stack | Office PRICE only | Estimates |
| Labour Engine | Labour Engine | Labour rates | **G** | Nav |
| Pricing Engine | Pricing Engine | Pricing | **G** | Nav |
| Historical Evidence | Historical Evidence | Previous estimates | **D** | Nav |

Do **not** invent equivalence: Estimate ≠ Proposal ≠ Contract; Direct Cost ≠ Actual Cost; Field Observation ≠ Actual Cost; Permit finding ≠ AHJ approval.

### G. Role / audience

| Audience | Surface | Copy |
|----------|---------|------|
| Owner | Hub MONITOR, dashboard | Margin, authorized selling price, missing-actuals in sentences |
| Estimator | PRICE, internal breakdown, Hub metrics | May keep Gross Margin, Direct Cost, Change Order; drop class names |
| Project manager | Hub PLAN/BUILD/MONITOR | Progress vs estimate; no schema |
| Office administrator | login, lists, Settings | Plain account/list language |
| Field worker | `/field` | Short verbs. Do not import Hub GM vocabulary onto Field Web |
| External customer | Proposal preview/PDF | **F — separate review.** FG-025 office sweep must not casually retitle customer documents |

### H. Error / empty-state standard (proposed)

Every user-facing empty, warning, and error should answer:

1. What is missing / what happened
2. Why it matters
3. What to do next

Avoid stack traces, raw enums, raw status keys, database terms, unexplained governance.

Example (MONITOR missing actuals, candidate): “No actual costs have been entered yet. Margin so far cannot be shown as $0.00. Use Record actual direct cost below.”

Example (no accepted proposal): “This project has no accepted proposal yet. Original estimated figures are not treated as a committed baseline. Accept a proposal when the customer has committed.”

### I. Status / action label standard (proposed)

Prefer verbs that match user intent. Keep industry-normal nouns.

| Current | Evaluate |
|---------|----------|
| Record correction | **Keep candidate** (better than Supersede) |
| Save actual | Save actual cost |
| Supersede (new draft version) | Save as a new version |
| Reprocess / indexing flashes | Run again / Index again |
| Archive (plan document) | **Keep** Archive |
| Void (sheet/calibration) | **Keep** Void (drawing practice) |
| Capture / Save original | Capture / Save |
| Retry pending captures | Retry |
| Update Context | Update project settings |
| Sign in | **Keep** |

Chips: map enums through a display helper; never print `SUPERSEDED` / `MISSING_ACTUALS` raw.

### J. Commercial / accounting meaning (must preserve)

FG-025 changes **wording only**. Do not alter Gross Margin calculations, Direct Cost meaning, tax treatment, `EstimatePricingSnapshot` authority, Accepted Proposal authority, Change Order authority, MONITOR identities, Actual Direct Cost aggregation, or current authorized revenue logic.

**Flag before adopting “Current Contract Value Before Tax”:** that phrase can be read as a signed construction contract. The MONITOR identity is **Current Authorized Pre-Tax Revenue** = accepted-proposal pre-tax selling price + Approved/Invoiced CO revenue delta, tax excluded. If Joel wants “contract value” language, ChatGPT must confirm it does not imply FG-024 legal execution.

**Flag:** “Gross margin so far” must remain Actual-to-Date GM (current authorized pre-tax revenue vs actual direct cost to date), not a new forecast-final figure.

**Flag:** office Proposal Overhead/Profit rows are an FG-012 residual. Hiding them is **not** a terminology-only change; do not do it inside a copy sweep unless separately authorized.

### K. FG-024 / legal-content boundary

FG-025 may retitle ordinary CONTRACT **navigation** (Proposals, templates) only. Do **not** rewrite legal clauses, populate contracts/warranties, change statutory notices, alter legal approval states, implement Contract Update Engine, or change jurisdiction support. Legal Content Gate remains empty and FG-024-owned.

### L. Recommended implementation strategy

**B. Controlled slices by surface** — not one unbounded product-wide sweep.

Copy lives in Jinja, route flashes, and Field JS. MONITOR **display** tests currently assert raw strings (`MISSING ACTUALS`, `other_direct`) in `tests/test_monitor_v1_fg023.py` and `tests/test_project_hub.py`. Domain tests asserting `actuals_state == "MISSING_ACTUALS"` **must not** change.

Presentation pattern: a small display-map module (e.g. `app/presentation/contractor_copy.py`) + Jinja usage. **Do not** rename enums or `assemble_monitor_v1` keys.

Proposed slices (later authorization, one prompt each):

| Slice | Scope | Why separate |
|-------|--------|----------------|
| **1** | Hub `#hub-monitor` + actuals forms/tables | Highest leakage; test coupling; commercialization-critical |
| **2** | Hub PLAN permit labels + commercial-context heading + LEARN Future note (wording only) | Governance leak; keep LEARN Future |
| **3** | Office PRICE specialist: estimates internal breakdown, labour, pricing, historical chips, material catalogue org label | Different audience |
| **4** | Nav / dashboard / auth / Settings | Low risk, high visibility |
| **5** | Field Web ALL_CAPS + “Save original” | Already mostly contractor-facing |
| **F** | Customer Proposal/PDF | Separate review; not Slice 1 |

Schema: **not required.** If a later slice appears to need a migration to improve wording: **STOP**.

### M. Proposed file allow-list (implementation, not this pass)

**CREATE (later):** `app/presentation/contractor_copy.py` (or equivalent display maps); `tests/test_fg025_contractor_copy.py`.

**MODIFY (by slice):**

- Slice 1: `app/templates/projects/detail.html` (MONITOR/actuals only); display-map module; display assertions in `tests/test_monitor_v1_fg023.py` / `tests/test_project_hub.py` (HTML copy only). Optional: Hub-only flashes in `app/routes/build.py` if they still echo enum names.
- Slice 2: same Hub template (PLAN/LEARN/commercial-context blocks only).
- Slice 3: `estimates/internal_breakdown.html`, `estimates/detail.html`, `estimates/version_detail.html`, `labour_engine/*`, `pricing_engine/*`, `historical_estimates/*`, `material_catalogue/*`, related route flashes (`pricing_engine.py`, `labour_engine.py`, `historical_estimates` routes).
- Slice 4: `app/navigation.py`, `dashboard.html`, `auth/login.html`, `settings/brand_profile.html`.
- Slice 5: `field/*.html`, `app/static/js/field.js` (user-visible strings only).

**DO NOT TOUCH:** `migrations/`; models and enum constants; `app/services/monitor.py` calculation keys; commercial arithmetic; Proposal PDF total logic; FG-024; Observation Delete; session revocation; LEARN product; CSS except if a later slice proves a `content:` string (none today).

### N. Test plan (implementation, not this pass)

Preserve behavior: navigation, forms, validation, auth, tenant isolation, Hub, Field Web, MONITOR math, Estimate/Proposal functions.

Pin:

- Rendered UI for targeted states does **not** contain raw `MISSING_ACTUALS`, `MISSING_CUSTOMER_COMMITMENT`, `AMBIGUOUS_COMMITMENT`, `MISSING_ORIGINAL_BASELINE`, `other_direct` as labels (after Slice 1).
- Domain JSON/service still uses those keys.
- MONITOR remains operational; LEARN remains Future; `NET PROFIT` remains absent.
- Customer PDF/preview not unintentionally changed (FG-012 assertions stay).

**Focused regression bundle (proposed):**

```bash
./venv/bin/python -m pytest -q \
  tests/test_fg025_contractor_copy.py \
  tests/test_monitor_v1_fg023.py \
  tests/test_project_hub.py \
  tests/test_auth_fg018.py \
  tests/test_build_field_observation_fg020.py \
  tests/test_build_media_compatibility_fg020.py \
  tests/test_field_web_fg021.py
```

Plus estimate/proposal tests when Slice 3/F runs. **Full suite must run after each implementation slice.** Current full-suite baseline: **593 passed**. Do not claim a future count.

This preflight did **not** re-run pytest.

### O. Visual / manual UAT plan (after implementation — do not execute now)

Representative pages: Dashboard, Project Hub (PLAN/PRICE/CONTRACT/BUILD/MONITOR), Field Web Today/Capture, Settings, Estimates/Proposals (office), one customer preview. Purpose: clarity that string tests cannot judge.

**Joel should approve final contractor-facing wording before FG-025 closure.** ChatGPT reviews meaning preservation. Office UAT on a labeled project (existing `FG023-UAT-MONITOR` id 13 is valid for MONITOR copy; do not write further actuals unless a later prompt says so).

### Readiness

**B. READY WITH EXPLICIT NON-BLOCKING NOTES**

Notes: glossary candidates are **not pinned**; “contract value” wording is flagged; customer documents are Slice F / separate; specialist engine nav names are **G**; FG-012 office Overhead/Profit residual is out of a terminology-only slice.

This preflight **did not** authorize implementation. Slice 1 was authorized later the same day by a separate bounded prompt.

---

## SLICE 1 IMPLEMENTATION (2026-09-07)

**Status:** **SLICE 1 IMPLEMENTED / TESTED / COMMITTED / PUSHED.** Gate **NOT CLOSED.** Remaining slices **NOT AUTHORIZED.**

Presentation-layer mapping only. Internal MONITOR/BUILD state keys remain authoritative in services, models, and domain tests.

Pinned Hub display strings live in `app/presentation/contractor_copy.py`. Hub `#hub-monitor` and office actuals forms/tables in `app/templates/projects/detail.html` consume that map. Optional Jinja wiring: `app/shell.py` injects `contractor_copy` into template context (existing UI helper file).

Dedicated tests: `tests/test_fg025_contractor_copy.py`. HTML copy assertions updated in `tests/test_monitor_v1_fg023.py` and `tests/test_project_hub.py` only. Domain-key assertions unchanged.

Frozen Slice 1 Hub metric identities were **not** renamed. No schema, migration, live DB write, MONITOR arithmetic change, enum/model rename, Field Web rewrite, LEARN, or FG-024.

Do **not** start Slice 3 from this section.

---

## SLICE 2 IMPLEMENTATION (2026-09-07)

**Status:** **SLICE 2 IMPLEMENTED / TESTED / COMMITTED / PUSHED.** Gate **NOT CLOSED.** Remaining slices **NOT AUTHORIZED.** Not a product-wide sweep.

Presentation-layer mapping only, reusing `app/presentation/contractor_copy.py`. No competing copy system. No schema, migration, live DB write, MONITOR arithmetic change, enum/model rename, Field Web rewrite, LEARN, or FG-024.

Project Hub (`app/templates/projects/detail.html`) contractor-facing copy:

- Actual-cost history: `Corrected by`, `No previous cost corrections.`, muted `Entry reference {id}`; primary `Id`/`ID` column removed.
- Commercial heading: **Pricing assumptions** (legacy empty: `Legacy project — pricing assumptions not recorded`; missing: `No pricing assumptions recorded.`).
- PLAN permit Hub: `Preliminary / foundation only`, `Advisory only`, `Recheck required`.
- Take-off Hub labels via `sentence_label()` (snake_case not primary).

Slice 1 MONITOR mappings and frozen financial metric labels were **not** renamed.

Dedicated tests: `tests/test_fg025_contractor_copy.py` (**10**). Hub HTML copy assertions also updated in `tests/test_project_hub.py`, `tests/test_monitor_v1_fg023.py`, `tests/test_permit_foundation_fg015.py`, and `tests/test_organization_foundation.py` (legacy Hub banner only). Domain-key assertions unchanged.

Do **not** start Slice 3 from this section.

---

## Approval

| Role | State |
|------|--------|
| Joel / ChatGPT | **Recorded** 2026-09-07. Preflight **COMPLETE** 2026-09-07. **Slice 1 authorized and implemented** 2026-09-07. **Slice 2 authorized and implemented** 2026-09-07. Remaining slices **not** authorized. Gate **not** closed. |
| Cursor | Slice 2 Project Hub language + tests + docs. No Slice 3. No FG-024. No LEARN. |
| Implementation | **SLICE 2 DONE.** Remaining FG-025 surfaces **NOT AUTHORIZED** until a later bounded prompt. |

**Next governed action:** **STOP.** Return Slice 2 report to ChatGPT Architect. Do **not** start Slice 3. Do **not** start FG-024. Do **not** start LEARN. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

# Feature Gate FG-025: Contractor-Facing UX Language & Terminology Standardization

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-025` |
| Feature Name | Contractor-Facing UX Language & Terminology Standardization |
| Target Milestone | **None.** FG-025 is the governing identifier. Do not assign a new M0xx number. This is a **commercialization hygiene** gate, not a new lifecycle stage. Sequence: **after [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) closes**, **before** broad external UAT / U.S. commercialization. |
| Module | **Cross-cutting UX copy.** [Projects](../modules/projects.md) owns Project Hub chrome. Owning modules retain their screens: Plan Intelligence, Estimating, Pricing Engine, Proposals, Project Controls, BUILD, MONITOR, LEARN (Future), authentication. This gate does **not** transfer record ownership. |
| Date | 2026-09-07 |
| Status | **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** This recording is **not** Feature Gate approval for implementation. Do **not** rewrite UI from this document. |
| Architecture | [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** (PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN) · [FG-011](FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT** (Hub reads/links; Future labeled) · [FG-012](FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** (office vs customer-facing estimate copy) · [FG-017](FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT** (visual brand, not terminology) · [FG-021](FG-021-field-web-v1-today-and-capture.md) **CLOSED** (Field Web capture copy) · [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) **APPROVED / OPEN / NOT CLOSED** · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |
| Related ADRs | **None new in this recording pass.** Visual identity remains [ADR-040](../adr/ADR-040-organization-brand-profile.md). Do **not** accept ADR-008 or ADR-010 from this gate. |
| Prerequisites | Active implementation stream remains [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) **close**. This gate does **not** jump the queue. Slice C is already **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**. This recording does **not** reopen Slice C. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **RECORDED.** **NOT APPROVED FOR IMPLEMENTATION.** |
| UI copy rewrite | **NOT AUTHORIZED** |
| Product code | **None.** |
| Schema / Alembic | **None.** |
| New ADR | **None in this recording.** |

```text
FG-025:
FUTURE
RECORDED
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
NO UI REWRITE IN THIS PASS
FG-023: UNCHANGED
  APPROVED / OPEN / NOT CLOSED
  SLICE C: MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS
  NEXT: CLOSE AUTHORIZATION
FG-024: UNCHANGED FUTURE CONTRACT INTELLIGENCE GATE
ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION
```

Joel/ChatGPT recorded this gate on **2026-09-07** as durable product/governance authority only. Recording is **not** implementation approval. Do **not** draft an implementation preflight from this document until FG-023 is closed and a separate bounded prompt authorizes the sweep.

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

- Does **not** interrupt FG-023. Slice C is already **PASS**. Next governed action remains **FG-023 close authorization**.
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

## Approval

| Role | State |
|------|--------|
| Joel / ChatGPT | **Recorded** 2026-09-07 as FUTURE product/governance authority. **Not** implementation-approved. |
| Cursor | Docs recording only. No product code. No UI rewrite. |
| Implementation | **NOT AUTHORIZED** until FG-023 is closed **and** Joel/ChatGPT later approve this gate for implementation with a bounded prompt. |

**Next governed action for the platform remains FG-023 close authorization.** Do **not** start FG-025 copy rewrite from this recording.

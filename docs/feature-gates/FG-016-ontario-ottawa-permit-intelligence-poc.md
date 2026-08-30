# Feature Gate FG-016: Ontario / Ottawa Permit Intelligence POC — Governed Rules + Mike Pratt Reference

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-016` |
| Feature Name | Ontario / Ottawa Permit Intelligence POC — Governed Rules + Mike Pratt Reference |
| Target Milestone | **None.** FG-016 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Permit Intelligence** owns Pass 2 analysis, findings, and the substantive Permit & Approvals Report. **Projects** owns project-tied location, jurisdiction resolution, Permit Profile relationship, Hub presentation, and the report snapshot relationship. **Permit Rules Library** is a **platform governed source** ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). Plan Intelligence remains plan/site-plan owner (**read-through only**). |
| Date | 2026-08-30 |
| Status | **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED** |
| Architecture | [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [permit-rules-library.md](../architecture/permit-rules-library.md) · [jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) · [modules/permit-intelligence.md](../modules/permit-intelligence.md) · [modules/projects.md](../modules/projects.md) |
| Related ADRs | [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted** · [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) **Accepted** · [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted** · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-005](../adr/ADR-005-ai-takeoff-traceability.md) **Accepted** · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | [FG-015](FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. ADR-037/038/039 **Accepted**. Live current = head `e7f8a9b0c1d2`. Full suite **364 passed**. |
| Approved baseline | Gate-approval HEAD `8c70ede72e37b5b0fe0910b70c34fca5d9c733ad`. Alembic current = head `e7f8a9b0c1d2`. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **APPROVED FOR IMPLEMENTATION** |
| Implementation | **NOT STARTED.** This pass is documentation only. |
| Schema / Alembic | **Authorized later** — one bounded additive revision in the implementation prompt. **Do not create it now.** |
| Permit Rules Library | **EMPTY / NOT IMPLEMENTED** — population is **in this gate** under human review. Not populated in this governance pass. |
| Substantive Permit Intelligence / Pass 2 | **NOT IMPLEMENTED** — authorized by this gate; not started. |
| Mike Pratt project in product data | **NOT CREATED** this pass. UAT reference only until implementation UAT. |
| Live web / geocoder / external AI | **NOT AUTHORIZED** at product runtime. |

This gate makes Permit Intelligence **genuinely useful** for **one bounded jurisdiction / reference case**. It is a **POC**, not a national permit library.

Success is a **useful advisory Permit & Approvals Report**. Success is **not** PERMIT READY, PERMIT APPROVED, or ZONING COMPLIANT.

---

## Purpose

```text
PROJECT LOCATION / JURISDICTION  (FG-015)
+ PERMIT CONTEXT                 (FG-015)
+ GOVERNED ONTARIO / OTTAWA REQUIREMENTS
+ REVIEWED PROJECT / PLAN / SITE FACTS
→ DETERMINISTIC ADVISORY PERMIT ANALYSIS
→ PERMIT & APPROVALS REPORT
```

Office success: for a project whose FG-015 location resolves to **City of Ottawa**, with permit context **Additional dwelling / coach house** (or other authorized class), CalibAi can run a cited, versioned analysis against **approved** platform rules and reviewed project facts, then show an advisory report that states what was checked, what passed the governed checks performed, what requires verification, what is missing, and what additional approvals may be likely — **without claiming AHJ approval**.

Reference / UAT case: **Mike Pratt Coach House, 2562 Church Street, North Gower, Ontario**. Use the existing signed plan set and site plan as reference evidence. Do **not** seed conversational ChatGPT conclusions as product facts. Do **not** claim municipal approval. Do **not** pre-decide findings in this gate.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | FG-015 is foundation only. The Permit Rules Library is empty. There is no Pass 2 analysis, no findings, and no useful Permit & Approvals Report. Ontario/Ottawa coach-house preflight cannot be trustworthy without governed rules + reviewed facts + deterministic evaluation ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)). |
| 2 | Who is the user? | Office estimator / Joel on the **current unauthenticated office app**. Not field. Not the AHJ. Not a municipal portal. |
| 3 | Which module owns it? | **Permit Intelligence** names Pass 2 analysis. **Projects** owns project-tied facts, Hub, and report snapshot relationship. **Permit Rules Library** is platform-governed (shared; not org commercial intelligence). Plan Intelligence owns plan/site versions (read-through). |
| 4 | What data does it own? | Platform permit-rule records (cited, effective-dated, approval-stated). Project-tied permit facts (reviewed evidence, not legal conclusions). Project-tied analysis/report versions and findings. Not `Project.address`. Not commercial `PROJECT_TYPES`. Not contract/warranty templates. |
| 5 | What data does it reference? | FG-015 `ProjectLocation`, jurisdiction resolution, preliminary `PermitProfile` / permit context. Plan/site-plan identity and **reviewed** measurements/citations (Plan Intelligence; read-through). Organization (tenant). |
| 6 | What may implementation change? | Permit Intelligence / Projects models, services, routes, templates for rules library (platform, no org CRUD for ordinary office users), project-fact capture/review, analysis run, report view, Hub PLAN extension, dedicated tests, governed docs, **one** additive migration under the **implementation** prompt. Optional bounded PDF export of the same snapshot (see **PDF / document output**). |
| 7 | What must it not change? | FG-015 location/jurisdiction semantics; `Project.address`; Plan Intelligence write paths; Estimating lines/pricing; proposals/contracts; BUILD; branding / Organization Brand Profile; Change Order documents; labour/pricing engines; Material Catalogue; historical evidence; Desktop corpus; Phase D. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. |
| 9 | Tests required? | Dedicated FG-016 tests; Project Hub / FG-015 / Plan Intelligence / Estimating / Proposals / org-isolation regressions; full suite before closure. |
| 10 | Documentation? | This gate; permit-rules architecture; permit-and-approvals; jurisdiction; Projects / Permit Intelligence modules; indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; UAT reference. |
| 11 | ADR required? | **No new ADR.** Covered by ADR-037/038/039. If implementation exposes an uncovered conflict: **STOP** — do not invent an ADR inside the implementation prompt. |
| 12 | Migration? | **YES — one bounded additive revision** in the implementation prompt only. No destructive rewrite. Do not create the migration in this governance pass. |

---

## Owner

| Concern | Owner |
|---------|--------|
| Project location / FG-015 resolver | **Projects** ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)) — **reuse; do not fork** |
| Permit context class | **Projects** (FG-015 profile field; do not mutate commercial `project_type`) |
| Permit Rules Library | **Platform governed source** ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)) |
| Reviewed project / plan / site facts used in analysis | **Projects** (project-tied permit facts). Plan/site **source** remains Plan Intelligence |
| Pass 2 analysis, findings, Permit & Approvals Report snapshot | **Permit Intelligence** capability; **Projects** persists project-tied snapshots |
| Plan / site-plan versions | Plan Intelligence (read-through; **no mutation**) |
| Estimate lines / pricing | Estimating — **unchanged** ([ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md)) |
| Contract / warranty templates | Legal Content Gate — **unchanged** |
| Post-issuance permit numbers / inspections | BUILD — **not this gate** ([ADR-020](../adr/ADR-020-build-module-boundary.md)) |

Do **not** create a second jurisdiction resolver. Do **not** store legal conclusions as project facts.

---

## Jurisdiction scope and fail-closed coverage

**Bound implementation to:**

| Layer | Value |
|-------|--------|
| Country | Canada |
| Province | Ontario |
| Municipality | City of Ottawa |
| Reference area | North Gower (alias already resolves to City of Ottawa under FG-015) |

Reuse the FG-015 resolver. Do **not** hard-code Ontario/Ottawa as universal architecture.

**Coverage statement (explicit):**

```text
ONTARIO / CITY OF OTTAWA
COACH HOUSE / ADDITIONAL DWELLING
RURAL / NORTH GOWER REFERENCE CASE
```

This corpus does **not** cover: all Ottawa project types; all Ontario municipalities; all Ontario permits; Canada; U.S. jurisdictions.

When location is unresolved, or resolved jurisdiction / permit context has **no approved rule coverage**:

**RULE COVERAGE NOT AVAILABLE**

Do not invent findings outside governed coverage. Do not fall back to Ottawa rules for unmatched municipalities.

---

## Mike Pratt reference case

| Field | Value |
|-------|--------|
| Project | Mike Pratt Coach House |
| Address | 2562 Church Street, North Gower, Ontario |
| Role | **Reference / UAT evidence** for this POC |
| Plans | Existing signed plan set and site plan — reference evidence |
| Status this pass | **Not created in product data** |

The POC must be **capable** of expressing and checking, **where governed source evidence supports them**:

- coach-house / additional dwelling use
- building footprint
- building height
- setbacks
- lot / site-plan completeness
- private servicing / septic
- grading requirements
- other bounded approval requirements in the authorized rule families

Do **not** pre-decide PASS / non-conformance in this gate. Do **not** treat prior ChatGPT research as a product determination ([testing/uat-reference-cases.md](../testing/uat-reference-cases.md)).

Implementation UAT **may** create a clearly labeled Pratt reference project. This governance pass must **not**.

---

## Permit Rules Library V1

Canonical architecture: [permit-rules-library.md](../architecture/permit-rules-library.md).

Smallest library required for the POC. A rule/reference must be capable of preserving:

- jurisdiction (tied to FG-015 platform definitions)
- issuing authority
- source title
- rule category
- concise governed rule statement
- source citation / URL / document reference
- `effective_from`
- `effective_to` / superseded
- `reviewed_at`
- provenance
- applicability
- approval / review state
- active / superseded state

Do **not** overbuild a national legal-content platform. Do **not** reuse the Contract / Warranty Legal Content Gate as this library.

### Authority-source policy

Operational governed rules may use **authoritative governmental / AHJ sources only**, for example (where applicable):

- City of Ottawa
- Province of Ontario
- applicable official building / zoning / permit authority
- applicable septic / private-servicing authority

**Not** governing authority: ChatGPT, Cursor, blogs, contractor websites, search snippets, generic summaries.

Secondary sources may assist **research** but must **not** become the approved rule source.

### Ingestion / curation

```text
DEVELOPMENT / GOVERNANCE RESEARCH
→ AUTHORITATIVE SOURCE
→ HUMAN REVIEW
→ GOVERNED RULE RECORD
→ PRODUCT USE
```

V1 population is **HUMAN-REVIEWED / CURATED / CITED / VERSIONED**.

Product runtime must **not** depend on live web retrieval. No runtime scraping. No automatic regulatory ingestion. No external AI.

Developer/governance research against public authoritative sources is an **offline / development activity** only. Do not confuse it with a product capability.

### Rule approval

AI **cannot** set regulatory content to **APPROVED** ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)).

V1 states (conceptual; exact tokens are implementation detail):

| State | Meaning |
|-------|---------|
| **DRAFT** | Captured; not used in operational analysis |
| **REVIEWED** | Human reviewed; not yet approved for analysis |
| **APPROVED** | Human-approved for operational analysis |
| **SUPERSEDED** | Replaced; retained for history |

Only **APPROVED** and currently effective rules participate in a new analysis. Ordinary org office UX has **no** CRUD path that mutates platform rules (same fail-closed spirit as FG-015 jurisdiction definitions). Rule curation is a governed operator/platform path, not contractor commercial intelligence.

### Effective dating / supersession

Rules are effective-dated. If a rule is superseded, **new** analysis uses the new approved rule. **Old reports retain the rule/version they pinned.** No mutable `CURRENT_RULE` shortcut that rewrites history ([ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)).

---

## First rule families (bounded)

Authorize only families required to make the Pratt POC useful:

- coach house / additional dwelling applicability
- permitted-use prerequisites
- footprint / maximum area
- building height
- setbacks
- site-plan submission requirements (bounded)
- rural grading requirement
- private servicing / septic review requirement
- driveway / access **where directly applicable**
- permit application / document completeness (bounded)

Do **not** automatically include every Ontario Building Code requirement. Do **not** make this a full code-compliance engine.

### Building Code boundary

Permit Intelligence **may cite** limited Ontario Building Code / submission requirements **only where directly necessary** to this bounded permit-preflight use case.

Do **not** perform comprehensive: structural code review; fire-code review; energy-code review; stair/guard compliance; engineering design validation; whole-plan OBC compliance. Those remain separately governed future capabilities.

### Contract / legal boundary

Permit Rules Library remains **separate** from the [Legal Content Gate](../governance/legal-content-and-templates.md) and from any future Jurisdictional Contract & Compliance Library.

Permit findings **may later** feed contract assumptions/exclusions. Gate 2 must **not** generate legal clauses.

---

## Rule vs project fact

| Kind | Meaning |
|------|---------|
| **RULE** | What the authority requires (platform-governed, cited, effective-dated) |
| **PROJECT FACT** | What the project / plans / site evidence show (org- and project-scoped, provenance-bearing) |

The engine compares governed facts to governed rules. Do **not** store a legal conclusion as a project fact.

Project facts must preserve source/provenance (who recorded, when, from which plan/site/manual entry). Ambiguous geometry or unshown surveyed values must **not** be auto-resolved.

---

## Plan Intelligence read-through

Authorize **minimum** read-through of **reviewed** facts, with provenance, such as:

- plan-set identity / version
- site-plan identity / version
- building footprint / dimensions
- building height
- shown setback dimensions
- project type / use evidence
- presence / absence of grading information
- presence / absence of servicing information

Do **not** mutate Plan Intelligence. Do **not** authorize Phase D. Do **not** consume unreviewed mock extraction as authoritative permit facts.

Where a plan fact is ambiguous, CalibAi must support **VERIFY / HUMAN REVIEW** rather than inventing certainty. Examples: which lot line a dimension applies to; exact surveyed setback; lot area not shown; septic location not shown; grade datum ambiguity.

Omission from an architectural sheet does **not** prove absence from a full municipal permit package. Word findings carefully.

---

## Deterministic evaluation

Use deterministic evaluation where rule and project fact permit it: numeric comparison; presence/absence; known jurisdiction/applicability; required-document check.

Do **not** implement generative legal reasoning.

If the rule cannot be deterministically evaluated, surface:

**VERIFY** / **MISSING INFORMATION** / **AHJ / PROFESSIONAL CONFIRMATION REQUIRED**

(or governed equivalent). Do not invent a PASS.

---

## Finding model

Smallest durable finding model for Gate 2. Conceptual statuses:

| Status | Meaning |
|--------|---------|
| **PASS** | No issue identified against the **governed checks performed** ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). **Never** means permit approved, zoning approved, or AHJ approved. |
| **VERIFY** | Human / professional confirmation required; do not invent certainty |
| **MISSING INFORMATION** | Required fact or document not available |
| **POTENTIAL NON-CONFORMANCE** | Evidence compared to the governed rule suggests a possible non-conformance; still advisory |
| **ADDITIONAL APPROVAL LIKELY** | Bounded indication that another approval path may be required |
| **NOT APPLICABLE** | Rule does not apply to this project/context |

**MATERIAL RISK** is **severity / impact**, not a finding status. **BLOCKING** commercial commitment is **not** a hard product block in this POC (see **Commercial-commitment warning**).

Each finding must be able to identify: Project; permit analysis/report version; governing rule; project fact/evidence; plan/site citation where applicable; result/status; explanation; recommended next action; advisory authority language.

Do **not** create uncited conclusions.

---

## Analysis run and report snapshot

Authorize a bounded analysis-run / report-generation concept that **pins**:

- jurisdiction
- rule-set / version (approved rules used)
- project location snapshot
- permit context
- plan version
- site-plan version
- project facts used
- findings
- generated_at
- provenance

Do **not** rewrite prior analysis.

The Permit & Approvals Report is an **immutable governed project snapshot** ([ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)). Later plan change, site-plan change, material project-fact change, or applicable rule change → **RECHECK REQUIRED** → **new report version**. Never silently rewrite an older report.

FG-015 location / permit-context recheck remains. Gate 2 **extends** triggers to plan revision, site-plan revision, material project-fact change, and applicable rule superseded/changed. Do **not** implement background monitoring. Surface stale/recheck when known.

---

## Permit & Approvals Report UX

Authorize a useful **office report view** containing conceptually:

- PROJECT / LOCATION / JURISDICTION / PERMIT CONTEXT / PLAN-SITE BASIS
- EXECUTIVE STATUS: **ADVISORY ONLY**
- CHECKS / FINDINGS (topic; governed requirement; project evidence; result; action required; source/citation)
- MISSING INFORMATION
- RECOMMENDED NEXT ACTIONS
- DISCLAIMER / AHJ AUTHORITY

Do **not** create decorative analytics or project-health scores.

---

## PDF / document output

**Office HTML report is in-gate and required.**

**PDF snapshot export is authorized in-gate** as a print of the **same** immutable report snapshot, using a **neutral CalibAi-governed project-report layout**.

Until Organization Brand Profile exists:

- do **not** require Brand Profile
- do **not** introduce a second per-module logo system
- do **not** use the static Brayman Construction proposal asset as Permit stationery
- later Brand Profile may add contractor branding **without changing analysis truth** ([ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md))

If implementation **cannot** produce PDF without a new document stack, new storage/fonts, or a second logo system: **STOP** and split PDF as an **immediate follow-on Feature Gate**. Do not guess a new PDF engine inside this gate.

---

## Project Hub

Extend PLAN → **PERMIT & APPROVALS** only with truthful Gate 2 state, for example:

- Substantive Permit Report: available / not available
- Last analysis: timestamp (when a report exists)
- Plan/site basis: identified (when pinned)
- Findings requiring attention: **actual count** if durable findings exist (VERIFY / MISSING INFORMATION / POTENTIAL NON-CONFORMANCE / ADDITIONAL APPROVAL LIKELY — not decorative)
- Recheck required: yes / no

Keep FG-015 foundation labels truthful. No generic project-health scores. No fake PASS counts.

---

## Estimating, commercial warning, contracts, BUILD

| Boundary | Gate 2 rule |
|----------|-------------|
| Estimating | **Advisory.** May identify **POTENTIAL COST / SCOPE IMPLICATION** for later human action. **No** automatic `EstimateLineItem`, Allowance, or CostItem. |
| Commercial commitment | **Warning / acknowledgement architecture only** where a material feasibility finding remains unresolved before final customer proposal or contract. **No hard blocking** in this POC unless a later gate explicitly justifies it. No contract-generation changes. |
| Contracts | Findings may later inform assumptions/exclusions. **No** legal-clause generation. |
| BUILD | **No** permit-number / inspection / occupancy tracking. |

---

## Private servicing and site-plan completeness

For the Pratt reference case, represent private septic / well / private servicing **only where authoritative evidence supports the requirement or the project fact**.

Do **not** assume a specific system unless project/source evidence establishes it. If missing: **MISSING INFORMATION / VERIFY**.

Site-plan completeness may compare **bounded municipal submission requirements** against what is shown/known in the **reviewed** site plan (property lines/dimensions, proposed building location, setbacks, driveway/access, lot area, servicing, easements/right-of-way, grading, overhead services) — **only** requirements supported by approved sources. Word findings carefully.

---

## Schema / migration authorization

**Schema: YES** (implementation prompt). Smallest additive structures conceptually:

- permit rules / requirement records (+ citation/provenance fields)
- project permit facts (if not representable safely on existing records)
- permit analysis run / report version
- permit findings

Prefer the smallest architecture. Exact table names are an implementation detail. Do **not** create a migration in this governance pass.

**Migration: YES — one bounded additive revision** in the later implementation prompt. No destructive changes. No forced backfill of Pratt conclusions.

---

## ADR requirement

**No new ADR.** ADR-037 (location/jurisdiction), ADR-038 (authority, rules library, PASS meaning, estimating/contract boundary), and ADR-039 (snapshot immutability, recheck, branding not required for analysis) cover this gate.

If implementation exposes a genuinely new architectural decision not covered: **STOP**. Do not invent an ADR inside the implementation prompt.

---

## Acceptance criteria

1. Uses FG-015 jurisdiction foundation (no second resolver; no universal Ottawa fallback).
2. Rules are separate from the Contract / Warranty Legal Content Gate.
3. Rules are authoritative-source backed.
4. Rules preserve provenance and effective dates.
5. AI cannot approve rules.
6. No runtime scraping.
7. No external AI.
8. Bounded Ontario / Ottawa coverage is explicit.
9. Mike Pratt is reference / UAT, not a universal rule.
10. Rule vs Project Fact distinction is preserved.
11. Project facts preserve source / provenance.
12. Ambiguous facts fail to VERIFY / MISSING INFORMATION rather than invent certainty.
13. Deterministic checks where rule and fact permit.
14. Finding statuses are governed (table above).
15. PASS does not mean permit approved.
16. Findings cite rule and project evidence.
17. Analysis / report pins rule set and plan / site versions.
18. Old report versions are immutable.
19. Recheck after plan / site / material fact / applicable rule change.
20. Project Hub shows truthful report state.
21. No Phase D.
22. No automatic EstimateLineItems.
23. No contract language generation.
24. No BUILD permit operations.
25. No national rules library.
26. No municipal submission.
27. Pratt POC report is useful and advisory (not a prescribed conclusion).
28. Dedicated tests pass.
29. Relevant regressions pass.
30. Full suite passes.
31. Docs reconciled before closure.

---

## Test / UAT plan (implementation)

Synthetic / labeled records. Pratt reference project **only** as labeled UAT when implementation authorizes it. Do **not** seed ChatGPT conclusions.

- Approved rule record; DRAFT/REVIEWED rules excluded from operational analysis
- Effective dating; superseded rule retained; new analysis uses new approved rule; old report unchanged
- Jurisdiction applicability; Ottawa / North Gower coverage via FG-015 alias
- Unsupported jurisdiction → RULE COVERAGE NOT AVAILABLE
- Project-fact provenance
- Numeric deterministic check
- Missing fact; ambiguous fact → VERIFY / MISSING INFORMATION
- PASS semantics (not AHJ approval)
- VERIFY; POTENTIAL NON-CONFORMANCE; ADDITIONAL APPROVAL LIKELY; NOT APPLICABLE
- Report snapshot immutability
- Rule-change recheck; plan/site-change recheck
- Org isolation (project facts, analyses, findings fail closed)
- Project Hub truthful state
- No runtime web; no external AI
- No Estimate mutation; no contract mutation
- Pratt reference UAT (advisory report produced; conclusions not prescribed here)
- Full suite

---

## Explicit non-goals

National rules library; runtime web scrape / municipal APIs / geocoder; external or regulatory AI; AI-approved rules; ChatGPT conclusions as product facts; comprehensive OBC / fire / energy / structural engine; Phase D; automatic estimate insertion; contract-clause generation; Organization Brand Profile; Change Order documents; BUILD permit numbers / inspections; municipal submissions; hard commercial blocking; background rule monitoring; cadastral/GIS; a second jurisdiction resolver; pre-deciding Pratt PASS/fail.

---

## Implementation authorization

This document **authorizes** the bounded FG-016 product implementation, including one additive Alembic revision **in a later implementation prompt**.

**This governance pass does not implement.** Do not populate the library now. Do not create the Pratt project now. Do not enable live web lookup or external AI.

**Next governed action:** FG-016 **implementation** under a separate Cursor prompt.

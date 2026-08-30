# Feature Gate FG-015: Permit Foundation V1 — Project Location, Jurisdiction & Preliminary Permit Profile

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-015` |
| Feature Name | Permit Foundation V1 — Project Location, Jurisdiction & Preliminary Permit Profile |
| Target Milestone | **None.** FG-015 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Projects** owns project location, project-tied jurisdiction resolution, and the project Permit Profile / snapshot relationship. **Permit Intelligence** owns the future analysis capability (Pass 2 is **out of this gate**). Permit Rules Library remains [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md). |
| Date | 2026-08-30 |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Architecture | [jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) · [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [modules/projects.md](../modules/projects.md) · [modules/permit-intelligence.md](../modules/permit-intelligence.md) |
| Related ADRs | [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted** · [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) **Accepted** · [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted** · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | FG-014 **CLOSED / OPERATIONAL FOR UAT**. ADR-037/038/039 **Accepted**. Live current = head `e7f8a9b0c1d2`. |
| Approved baseline | Gate-approval HEAD `5474c47189f67645cc6a636cdfa054cf3c6660f9`. Alembic current = head `d6e7f8a9b0c1`. Full suite **345 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **CLOSED / OPERATIONAL FOR UAT** |
| Implementation | **Done in product code.** Live migration applied. Office UAT **PASSED** on port **5008**. |
| Schema / Alembic | Additive revision **`e7f8a9b0c1d2`**. Live current = graph head = **`e7f8a9b0c1d2`**. One head. |
| Permit Rules Library | **NOT IN THIS GATE** — not created, not populated |
| Live web / geocoder / external AI | **NOT AUTHORIZED** — none in this implementation |
| Mike Pratt project / permit analysis | **NOT IN THIS GATE** |

This gate establishes **trustworthy location / jurisdiction / preliminary-profile infrastructure**. It does **not** perform zoning or permit compliance analysis. It does **not** authorize the later Ontario / Ottawa Permit Rules + Mike Pratt POC.

---

## Purpose

Permit Foundation V1 creates the project spine required by later Permit Intelligence:

```text
PROJECT
→ STRUCTURED LOCATION
→ JURISDICTION
→ PRELIMINARY PERMIT PROFILE
→ PROVENANCE-READY PROJECT RECORD
```

Office success: a new project can record a civic location, show location/jurisdiction status immediately, and carry an explicitly **preliminary** Permit Profile when the foundation runs — without a hidden Permit button, without invented AHJ conclusions, and without touching existing free-text `Project.address`.

Success is **FOUNDATION READY**, not PERMIT READY and not ZONING COMPLIANT.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | `Project.address` is free text. There is no structured location, no reusable jurisdiction resolver, and no project-tied preliminary Permit Profile. Later Ontario/Ottawa analysis cannot be trustworthy without this spine ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). |
| 2 | Who is the user? | Office estimator / Joel on the **current unauthenticated office app**. Not field. Not the AHJ. |
| 3 | Which module owns it? | **Projects** owns location, project-tied resolution, and the profile/snapshot relationship. **Permit Intelligence** names the future analysis capability; Pass 2 is out of scope. Platform jurisdiction **definitions** are shared; project facts are org-scoped. |
| 4 | What data does it own? | Bounded `ProjectLocation` (1:1, parented to `projects`); project-tied preliminary Permit Profile / snapshot; project-tied resolved-jurisdiction result. Not `Project.address` replacement. Not Permit Rules Library rows. Not commercial `PROJECT_TYPES`. |
| 5 | What data does it reference? | `projects`, `organizations` (tenant). Platform jurisdiction definitions / bounded municipality aliases (shared). Current commercial context **read-through only** (not mutated; not used as permit-use ontology). Plan/site facts **not** read into findings. |
| 6 | What may implementation change? | Projects models/services/routes/templates for location + Hub PLAN presentation; Permit Profile persistence; platform jurisdiction seed; dedicated tests; governed docs; **one** additive migration under the **implementation** prompt. |
| 7 | What must it not change? | `Project.address` values; existing project validity; Plan Intelligence write paths; Estimating lines/pricing; proposals/contracts; BUILD; branding; Change Order documents; labour/pricing engines; Material Catalogue; historical evidence; Desktop corpus; live DB backfill of ambiguous addresses. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. |
| 9 | Tests required? | Dedicated FG-015 tests; Project Hub regressions; project create/isolation regressions; full suite before closure. |
| 10 | Documentation? | This gate; jurisdiction + permit architecture; Projects / Permit Intelligence modules; Project Hub presentation; indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log. |
| 11 | ADR required? | **No new ADR.** Covered by ADR-037/038/039. If implementation exposes an uncovered conflict: **STOP** — do not invent an ADR inside the implementation prompt. |
| 12 | Migration? | **YES — one bounded additive revision** in the implementation prompt only. No destructive rewrite. No forced backfill. Do not create the migration in this governance pass. |

---

## Owner

| Concern | Owner |
|---------|--------|
| Project location facts; `Project.address` preservation | **Projects** ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)) |
| Project-tied jurisdiction resolution result | **Projects** (consumes the one reusable resolver) |
| Platform jurisdiction definitions / bounded aliases | **Platform governed source** (shared; not org commercial intelligence) |
| Preliminary Permit Profile / snapshot relationship | **Projects** (project-tied). Permit Intelligence names the future analysis capability. |
| Permit Rules Library | [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) — **not this gate** |
| Plan / site-plan versions | Plan Intelligence (read-through later; **not this gate**) |
| Estimate lines / pricing | Estimating — **unchanged** |
| Post-issuance permit numbers / inspections | BUILD — **not this gate** ([ADR-020](../adr/ADR-020-build-module-boundary.md)) |

Do **not** create a second jurisdiction mechanism inside Permit Intelligence, tax, contracts, or supplier geography.

---

## Structured project location (V1)

ADR-037: Projects owns location; structured location records **parent to `projects`**; distinct from `ProjectCommercialContext`.

**V1 shape:** a bounded **ProjectLocation** record, **1:1** with `Project`, owned by Projects. Do **not** scatter civic fields as the only location model on `Project` while leaving `address` overloaded. Do **not** build cadastral/GIS.

**Preserve** existing `Project.address` (free text). Do not overwrite it from structured fields in V1. Do not parse it into structured fields.

Normal civic location (supported now):

- civic / street address
- city / municipality
- province / state
- postal / ZIP (supported; **not** required for LOCATION COMPLETE or JURISDICTION RESOLVED)
- country

Anticipate later (nullable / unused in V1 UX; no GIS):

- location kind (civic vs rural/vacant vs legal-description)
- legal description
- parcel identifier
- future civic address

Exact column names are an implementation detail. Do not add geocoder, lat/long-required, or map-provider fields in V1.

---

## Location completeness

| State | Meaning (V1 civic) |
|-------|-------------------|
| **LOCATION COMPLETE** | Street/civic address, municipality, province/state, and country are all present. |
| **LOCATION INCOMPLETE** | Any of those four is missing. A legitimate early project may be incomplete. |

Do **not** invent precision. Postal/ZIP may be stored when known; its absence does **not** by itself make location incomplete. Rural/vacant/legal-description-only records remain **LOCATION INCOMPLETE** in V1 (civic completeness is the V1 rule). Do **not** require complete location to create a `Project`.

---

## Jurisdiction Resolver V1

Reusable hierarchy ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)):

```text
Country
→ Province / State
→ Municipality / County
→ applicable AHJ(s)
```

V1 is **not** a national geocoder. Resolution is **deterministic** from stored location fields matched to **governed platform jurisdiction definitions**.

**JURISDICTION RESOLVED** only when all of the following are true:

1. Country, province/state, and municipality are present on ProjectLocation.
2. Those values match a governed platform jurisdiction node (normalized name or **bounded** municipality alias).
3. The match identifies country → province/state → municipality and the applicable AHJ recorded on that node.

Otherwise: **JURISDICTION UNRESOLVED**.

**Bounded first-jurisdiction representation (not a universal default):**

- Platform may seed Canada / Ontario / City of Ottawa as **one** governed municipality node.
- Bounded aliases **may** include `Ottawa`, `City of Ottawa`, and `North Gower` → City of Ottawa so the first municipal case can resolve **without live lookup**.
- Do **not** default every Ontario (or unmatched) project to Ottawa.
- Do **not** seed a national municipality library.
- Unmatched municipality text stays **JURISDICTION UNRESOLVED**.

`Organization.tax_jurisdiction` remains tax policy. It is **not** the resolver.

---

## No live geocoding / web lookup

This gate must **not** require Google Maps, an external geocoder, a municipal API, live web lookup, or external AI. Future automated geocoding is separately governed.

---

## Permit context class (project type for Pass 1)

Do **not** blindly reuse commercial estimating `PROJECT_TYPES` (`New Build`, `Addition`, `Renovation`, `Garage`, `Foundation`, `Commercial`, `Specialty` in `app/services/commercial_context.py`). Those values are **estimating posture** ([ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md)). They cannot represent coach house / additional dwelling and must not be treated as zoning use.

**V1 decision (within ADR-038 Pass 1; not a new ADR):** store a small **permit context class** on the Permit Profile (and collect it at project create). Do **not** mutate `ProjectCommercialContext.project_type`. Do **not** auto-map commercial type → permit context. Do **not** build a zoning-use ontology.

V1 vocabulary (conceptual; exact tokens are implementation detail):

- New dwelling
- Addition
- Renovation
- Garage / accessory structure
- Additional dwelling / coach house
- Commercial
- Other / unspecified

`Other / unspecified` is valid. Missing permit context does **not** block project creation; the profile records that it is unspecified.

If implementation would replace commercial `PROJECT_TYPES`, infer zoning use from estimating type, or invent a full use ontology: **STOP**.

---

## Preliminary Permit Profile

Project-tied Pass 1 record ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). Purpose: record foundation state, not compliance.

Must record:

- project
- organization
- project location basis (values used; completeness)
- resolved jurisdiction where available (or explicit unresolved)
- permit context class (or unspecified)
- advisory / preliminary status
- created / generated timestamp
- provenance (who/what established location; generation method = deterministic platform, not AI)
- whether plans / site plan have been reviewed (**always false / not performed in V1**)
- whether substantive permit analysis exists (**always false / not yet available in V1**)
- profile version / supersession

Must **not** contain invented zoning conclusions, setbacks, height, septic determinations, or PASS.

### Preliminary means preliminary

The V1 profile must communicate **PRELIMINARY / FOUNDATION ONLY**.

It does **not** mean: zoning compliant; permit ready; permit approved; building-code compliant; AHJ reviewed.

**PASS** is **not** shown. [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) authority boundary is binding.

---

## Snapshot / provenance foundation

**Decision:** V1 creates a **versioned project-tied Permit Profile snapshot** that is the Pass 1 instance of the snapshot family Gate 2 will extend ([ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)).

Do **not** create a second “generic report” table in V1. Do **not** create substantive findings or rule citations in V1.

Later Gate 2 adds a later version / kind (substantive report) without rewriting issued V1 rows. Location, jurisdiction, permit context, generated_at, and provenance are **pinned** on the snapshot. Later changes create a **new** version. Never rewrite historical issued profiles.

---

## Recheck / staleness foundation

A current profile becomes **STALE / RECHECK REQUIRED** (without rewriting the prior snapshot) when:

- project location values change
- permit context class changes

Plan / site-plan and governing-rule-change triggers belong to the later analysis gate. Do **not** implement rule-change monitoring in FG-015.

---

## Project creation UX

Later implementation, substantially:

```text
NEW PROJECT
  Project Name
  Customer
  Project Location (structured civic fields)
  Permit context class
  → CREATE PROJECT
```

Existing FG-007 commercial-context fields on create **remain**. Do not remove them. Label permit context **distinctly** from commercial `project_type` so the two are not aliased.

After create, **LOCATION / JURISDICTION STATUS** appears immediately (complete/incomplete; resolved/unresolved).

**Automatic profile:** creating a project **always** creates a preliminary Permit Profile that records actual foundation state (including incomplete / unresolved / unspecified context). Do **not** require a separate Permit button for the foundation. Do **not** invent jurisdiction when facts are missing.

---

## Existing projects

Existing projects remain valid. **No destructive backfill.** **No parsing** of ambiguous historical `Project.address` into structured location or Ottawa.

Until a human explicitly reviews/enters structured location:

- `Project.address` unchanged
- LOCATION INCOMPLETE
- JURISDICTION UNRESOLVED
- Permit Profile **not generated** (Hub: profile not generated)

Optional later “review location” action may create the first ProjectLocation + profile from **user-entered** structured fields, not from guessed free-text.

---

## Mike Pratt reference

Mike Pratt Coach House, 2562 Church Street, North Gower, Ontario is the **[FG-016](FG-016-ontario-ottawa-permit-intelligence-poc.md)** reference case (approved, not created in product data by FG-015).

This gate must **not**: create that project in the database; perform permit analysis; seed Pratt-specific conclusions.

Bounded jurisdiction aliases (e.g. North Gower → City of Ottawa) are **platform jurisdiction data**, not Pratt conclusions.

---

## Project Hub (PLAN)

Bounded presentation under PLAN at `/projects/<id>` ([FG-011](FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)):

**PERMIT & APPROVALS**

- Location: complete / incomplete
- Jurisdiction: resolved / unresolved
- Permit Profile: preliminary / not generated
- Plan/site analysis: not performed
- Substantive Permit Report: not yet available

Do **not** show fake finding counts. Do **not** show PASS. Do **not** imply AHJ approval. Hub **reads** Projects-owned foundation records; it does not take Permit Rules Library ownership.

---

## Tenant / org isolation

Project location and Permit Profile are **organization- and project-scoped**. Cross-org access **fails closed**. No contractor may see another contractor’s project location, permit profile, or future permit evidence.

Platform jurisdiction definitions **may** be shared (like canonical materials). Ordinary org actions must not mutate platform jurisdiction nodes.

---

## Schema / migration

| Item | Status |
|------|--------|
| SCHEMA CHANGE | **Done.** Additive `project_locations`, `jurisdiction_definitions`, `jurisdiction_aliases`, `permit_profiles` |
| MIGRATION | **`e7f8a9b0c1d2`** applied live (`d6e7f8a9b0c1` → `e7f8a9b0c1d2`). Live current = head. |
| Backfill | **NO** — existing rows stay valid; address preserved; no forced profiles |

---

## Acceptance criteria

1. Project location is a governed project fact (Projects-owned ProjectLocation parented to `projects`).
2. Existing `Project.address` is preserved.
3. Existing projects remain valid without structured location.
4. No automatic ambiguous backfill from free-text address.
5. Structured location can represent a normal Ontario civic address.
6. LOCATION INCOMPLETE is supported; projects may be created incomplete.
7. Jurisdiction may be resolved only from sufficient governed facts + platform definitions.
8. One reusable jurisdiction model/resolver foundation (not per-module forks).
9. No hard-coded universal Ottawa assumption; unmatched locations stay unresolved.
10. Preliminary Permit Profile is project-tied and org-scoped.
11. Profile is explicitly advisory / **PRELIMINARY / FOUNDATION ONLY**.
12. No zoning compliance conclusion.
13. No PASS / AHJ-approval implication.
14. No Permit Rules Library population (no Ottawa zoning, setbacks, height, coach-house, septic, or grading rules).
15. No live web / geocoder / external AI.
16. Project Hub can surface foundation state under PLAN as specified.
17. Cross-org access to location and profiles fails closed.
18. Location or permit-context-class changes can mark the current profile STALE / RECHECK REQUIRED without rewriting the prior snapshot.
19. No Plan Intelligence permit analysis; no footprint/height/setback ingest; no Plan Intelligence mutation.
20. No Phase D.
21. No estimating insertion / allowances / proposal blocking / pricing change.
22. No contract generation.
23. No Organization Brand Profile implementation; no Permit-logo settings.
24. No Change Order document-family work.
25. No BUILD permit numbers / inspections / occupancy.
26. Dedicated tests pass.
27. Relevant regressions pass (Project Hub, project CRUD/isolation, commercial context).
28. Full suite passes.
29. Docs reconciled before gate closure.

---

## Test / UAT plan (implementation)

Synthetic / labeled UAT records only. **Do not** seed Pratt conclusions or create the Mike Pratt project as governed evidence.

- Structured location create (Ontario civic example)
- LOCATION INCOMPLETE create still succeeds
- JURISDICTION RESOLVED when country + province + municipality match a governed node / bounded alias
- JURISDICTION UNRESOLVED when facts missing or municipality unmatched (including non-Ottawa Ontario text)
- Existing `Project.address` unchanged; no auto-backfill
- Project create workflow: status visible immediately; preliminary profile auto-created for **new** projects
- Existing project: profile not generated until explicit location review
- Advisory / preliminary labeling present; no zoning conclusions; no PASS
- Project Hub PLAN presentation (complete/incomplete, resolved/unresolved, preliminary/not generated, analysis not performed, report not yet available)
- Org isolation; cross-org fail closed
- STALE / RECHECK after location or permit-context-class change; prior snapshot not rewritten
- No permit-rule records; no live lookup; no Plan Intelligence mutation; no Estimate mutation
- Full suite

---

## Explicit non-goals

Permit Rules Library; Ottawa/Ontario zoning or building-code engine; live web lookup / geocoding / municipal APIs; external or regulatory AI; automatic zoning or permit conclusions; municipal submissions; Pass 2 Permit & Approvals Report; Plan Intelligence integration; Phase D; estimate insertion; contract generation; Organization Brand Profile; Change Order documents; BUILD operational permits; national jurisdiction library; cadastral/GIS; creating the Mike Pratt project; parsing historical `Project.address`.

**Recommended second Permit Gate:** [FG-016](FG-016-ontario-ottawa-permit-intelligence-poc.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED**.

---

## Implementation authorization

This document **authorized** the bounded FG-015 product implementation, including one additive Alembic revision.

**Implemented:** `ProjectLocation` 1:1; platform Canada / Ontario / City of Ottawa seed + aliases; deterministic resolver; permit context class; new-project auto location + preliminary profile; existing-project location review; versioned immutable preliminary snapshots; Project Hub PLAN foundation panel.

**Live migration + office UAT (2026-08-30):** `flask db upgrade` applied `d6e7f8a9b0c1` → `e7f8a9b0c1d2`. Fresh Flask on port **5008**. Complete / incomplete / unknown-municipality / North Gower alias / existing-project transition / explicit location review / permit-context / snapshot immutability / recheck / Hub / isolation / advisory copy **PASSED**. Dedicated FG-015 **19 passed**. Relevant regressions **338 passed**. Full suite **364 passed**. No product-code defect. No product-code change this pass.

**Not done (still out of this gate):** Permit Rules Library; Pass 2 analysis; Pratt project; Phase D; live web lookup / geocoder / external AI. Those belong to [FG-016](FG-016-ontario-ottawa-permit-intelligence-poc.md) or later gates.

**Next governed action:** [FG-016](FG-016-ontario-ottawa-permit-intelligence-poc.md) is **APPROVED FOR IMPLEMENTATION**. Do not implement FG-016 in the FG-015 close record. Do not populate permit rules until the FG-016 implementation prompt.

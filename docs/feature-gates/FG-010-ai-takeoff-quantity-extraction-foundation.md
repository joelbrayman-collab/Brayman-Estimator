# Feature Gate FG-010: AI Take-off / Quantity Extraction Foundation

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-010` |
| Feature Name | AI Take-off / Quantity Extraction Foundation |
| Target Milestone | **M012** |
| Module | Plan Intelligence |
| Date | 2026-08-29 |
| Status | **APPROVED FOR IMPLEMENTATION** — **NOT IMPLEMENTED** |
| Architecture | [ai-takeoff-quantity-extraction-foundation.md](../architecture/ai-takeoff-quantity-extraction-foundation.md) **Approved** |
| Related ADRs | [ADR-031](../adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) **Accepted** · [ADR-005](../adr/ADR-005-ai-takeoff-traceability.md) **Accepted** · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) **Accepted** · [ADR-009](../adr/ADR-009-pdf-first-versus-cad-first.md) **Accepted** · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** · [ADR-011](../adr/ADR-011-ai-confidence-threshold-policy.md) **Accepted** · [ADR-012](../adr/ADR-012-plan-document-version-ownership.md) · [ADR-026](../adr/ADR-026-scale-ownership-and-calibration-provenance.md) **Accepted** · [ADR-027](../adr/ADR-027-pdf-rendering-and-normalized-coordinate-system.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** |
| Prerequisites | M005–M010 implemented; FG-007 org isolation; FG-008 **CLOSED / OPERATIONAL FOR UAT**; FG-009 **CLOSED / OPERATIONAL FOR UAT** |
| Approved baseline | Governance approval 2026-08-29. Parent HEAD at approval: `bc37463a15dbb3a97e6250686ba5b0a4d78f1955`. Alembic current/head `a3b4c5d6e7f8`. **Implementation not started.** |

---

## Status

| Layer | State |
|-------|--------|
| Architecture | **Approved** (2026-08-29) |
| Feature Gate (this document) | **APPROVED FOR IMPLEMENTATION** |
| ADR-031 / 005 / 006 / 007 / 009 / 011 | **Accepted** |
| ADR-010 | **Proposed** (real external AI provider **not authorized**) |
| Implementation | **NOT IMPLEMENTED.** Requires a **separate** bounded implementation prompt. No product code, no migration in this governance pass. |
| Real external AI provider | **NOT AUTHORIZED** |

This gate does **not** implement OCR, CAD, multi-trade extraction, automatic estimate insertion, Labour Engine or Pricing Engine changes, BUILD/MONITOR/LEARN, QuickBooks, or contracts.

---

## Purpose and business rationale

Estimators need **defensible AI-assisted counts** from searchable architectural PDFs without letting the model silently write commercial records.

Without this foundation:

- AI detections would have nowhere durable to live except comments or logs.
- Reruns could float reviewed quantities.
- PLAN could leak into PRICE (FG-009) or labour standards (FG-008).
- Other organizations could inherit Brayman plan intelligence as if it were a platform default.

POC (narrow): **interior door opening count** on **searchable** architectural floor-plan sheets.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Need a governed extraction-run → candidate → human-review → immutable take-off package path for AI counts, with citations, without estimate/pricing mutation. |
| 2 | Who is the user? | Office estimators/reviewers on a Project’s plans. Not field. |
| 3 | Which module owns it? | **Plan Intelligence.** Not a new module. Estimating owns lines only after a later mapping gate. |
| 4 | What data does it own? | `TakeoffExtractionRun`, `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem`; additive audit event types. |
| 5 | What data does it reference? | `Organization`, `Project`, `PlanDocument`, `PlanPage`, `DrawingRevision`, `PlanSheet`. Read-only consume. |
| 6 | What may implementation change? | Additive Plan Intelligence schema/services/UI/tests/docs. |
| 7 | What must implementation not change? | Historical workbooks; Accepted proposals; FG-008 labour production/calibration; FG-009 policies/snapshots; M010 measurement math; silent estimate insert; CAD/OCR scope. |
| 8 | Acceptance criteria? | See below. |
| 9 | Tests required? | See **Test expectations**. None in this architecture pass. |
| 10 | Documentation? | This gate; take-off architecture; ADR-031; Plan Intelligence module; indexes; current-state; handoff; roadmap; chat-workflow-log. |
| 11 | ADR required? | **Yes** — ADR-031 **Accepted**. ADR-005/006/007/009/011 **Accepted** (006 does not authorize insert in M012; 011 confidence never auto-approves). ADR-010 stays **Proposed**. |
| 12 | Migration? | **Yes, later.** Additive only, when an **approved** implementation prompt authorizes it. **Not this pass.** |

---

## Scope

### In (architecture now; code later)

- Searchable PDF input boundary
- Architectural sheet eligibility
- Extraction run lifecycle
- Candidate provenance (normalized bbox)
- Human review (accept/adjust/reject/duplicate/not_applicable)
- Confidence as advisory (numeric + band)
- Immutable approved take-off package
- Org fail-closed
- Interior door count vocabulary V1

### Out

OCR; CAD; scanned plans; photo/voice AI; windows/walls/concrete/framing/MEP; automatic estimate insertion; Labour Task/rate selection; Pricing Engine writes; contracts; QuickBooks; BUILD/MONITOR/LEARN; model training; cross-org learning; autonomous approval; schedule auto-match (optional later); Phase D mapping.

---

## Dependencies (existing)

| Dependency | State |
|------------|--------|
| M005 upload | Implemented |
| M007 pages/packages/revisions/audit | Implemented |
| M009 sheets/human review | Implemented |
| M010 scale + PDF.js + normalized coords | Implemented (COUNT AI path does not require scale) |
| M011 / ADR-028 org isolation | Implemented |
| FG-008 / FG-009 | Closed / operational for UAT — **must not be modified** |

---

## Data model (intended)

See [architecture §7–8, §20, §25](../architecture/ai-takeoff-quantity-extraction-foundation.md). Additive tables; no rewrite of `plan_measurements`.

---

## Source traceability

Every candidate/package item must retain at least: `organization_id`, `project_id`, `PlanDocument`, `DrawingRevision`, `PlanPage`/`page_index`, `PlanSheet`, file identity (filename/sha256 via document), sheet number/name, normalized geometry, extraction method, provider/model/version if AI, run id, confidence, timestamps, evidence text where appropriate, reviewer, review decision, review timestamp, adjustment reason.

Citations are first-class (ADR-005).

---

## Normalized coordinates

ADR-027 `[0,1]×[0,1]` only. Same convention as `PlanMeasurement.geometry_data`.

---

## COUNT without scale (authorized correction)

**COUNT is dimensionless.** A count candidate / reviewed count must **not** require scale merely to count discrete objects.

Future FG-010 implementation **may** permit `measurement_type = count` without confirmed dimensional calibration. This applies **only** to count.

It must **not** weaken M010 rules for `linear`, `polyline`, `area`, or perimeter. Those dimensional measurements must continue to fail closed unless the governing scale/viewport calibration is valid.

Current M010 code reportedly requires confirmed non-NTS scale even for COUNT. That is a **narrow authorized correction** in the later implementation prompt. **Do not change code in this governance pass.**

---

## Real external AI provider (not authorized)

FG-010 implementation **may** build: provider-neutral extraction interface; provider/model/version fields; run/candidate/review/package persistence; a deterministic/mock/test extractor or internal development adapter.

**REAL EXTERNAL AI PROVIDER INTEGRATION IS NOT AUTHORIZED.** Do not send customer or UAT plan bytes/text to an external AI service merely because this gate is approved.

A later governed decision (ADR-010 amendment/acceptance or another artifact) must cover provider identity, data sent, retention, training/data-use, privacy/security, credentials, failure behavior, and cost/control.

---

## Lifecycles

| Object | States |
|--------|--------|
| Extraction run | `queued` → `running` → `succeeded` \| `failed` \| `cancelled` |
| Candidate | `suggested` → `accepted` \| `adjusted` \| `rejected` \| `duplicate` \| `not_applicable` |
| Package | `draft` → `approved` (immutable) → `superseded` |

No silent acceptance.

---

## Confidence

Numeric `[0.0, 1.0]` + advisory band `LOW` / `MEDIUM` / `HIGH`. **Never auto-approves.** Confidence never equals human approval. No threshold may auto-accept, auto-create an approved package, auto-insert estimate quantity, or auto-price work. Batch-approve is an explicit human command on listed candidates only — still not estimate insert (ADR-006).

---

## Duplicates and revisions

Duplicates: `canonical_candidate_id`; evidence kept; excluded from approved totals.

New drawing revision: new run; old approved package immutable. Diff automation future.

---

## Take-off package

Versioned frozen reviewed total + item snapshots + provenance. Must not float.

---

## Organization isolation

`organization_id` on all new take-off rows. Unknown org / cross-org id → fail closed. No leakage of geometry, candidates, or packages.

---

## AI authority

Propose only. Human is SoR for reviewed quantities. See architecture §6.

---

## PLAN → PRICE / Labour / Pricing

| Boundary | Rule |
|----------|------|
| Estimate mapping | **Out of this gate** (Phase D later). Human approval of a candidate/package does **not** authorize `EstimateVersion` writes (ADR-006). |
| Labour Engine | Read-none for V1. Must not alter FG-008 records. |
| Pricing Engine | Must not alter FG-009 records or create customer price. |

---

## Auditability

Append-only `PlanAuditEvent` extensions. Human actor strings until auth exists.

---

## Security / privacy

External provider handling of plan bytes/text is **not authorized** by this gate. See **Real external AI provider** above. Unauthenticated office app remains platform debt; continue actor-string convention (not equivalent to completed auth).

---

## Migration expectations

When an **implementation prompt** is issued: one additive Alembic revision. No casual generation in this governance pass. No live migrate authorization here.

---

## Tests (implementation later)

Org isolation; searchable PDF; architectural sheet; run versioning; provenance; bbox; confidence; accept/adjust/reject/duplicate; reviewer; package immutability; rerun; revision separation; count determinism; no estimate insert; no pricing/labour mutation; cross-org fail-closed; `tests/test_plan_upload.py`, `test_plan_indexing.py`, `test_sheet_intelligence.py`, `test_scale_measurement.py`; FG-008; FG-009; full suite.

**This pass:** existing suites only (no new tests).

---

## UAT (later)

Synthetic searchable architectural PDF. Do not create UAT data now. Do not casually send customer production plans to an external model.

---

## Rollback / legacy

Additive tables can be unused if rolled back before commercial dependence. Existing M005–M010 paths unchanged. Manual `PlanMeasurement` remains.

---

## Protected areas

Historical workbooks; Accepted proposals; FG-008 labour facts; FG-009 ORG-001 seed and snapshots; PlanDocument bytes/checksums; M009 sheet SoR from AI; M010 calibration fail-closed for dimensional measures.

---

## Non-goals

See **Out** plus FG-009 UI leftover-stack-percent cleanup (separate maintenance).

---

## Acceptance criteria (for a future implementation prompt)

1. Named extraction run; rerun does not mutate approved packages.
2. Interior-door candidates cited to sheet/page/norm-bbox.
3. Human accept/adjust/reject/duplicate; no silent accept.
4. Approved package immutable; deterministic reviewed total.
5. COUNT V1 works without requiring scale; M010 dimensional fail-closed unchanged.
6. Zero silent estimate/labour/pricing writes.
7. Cross-org fail-closed.
8. Provider fields vendor-agnostic.
9. Docs/tests/DoD for that implementation prompt.

---

## Blocking conditions (implementation)

Product implementation remains **blocked** until a **separate** bounded FG-010 implementation Cursor prompt is issued.

This governance pass does **not** authorize product code, migration, or real external AI provider integration.

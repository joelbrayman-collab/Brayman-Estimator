# AI Take-off / Quantity Extraction Foundation — Architecture / Readiness Report

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** — FG-010 foundation in code; Alembic current/head `b4c5d6e7f8a9` |
| Date | 2026-08-30 |
| Milestone | **M012** (foundation operational for UAT; Phase D mapping not started) |
| Feature Gate | [FG-010](../feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Module | [Plan Intelligence](../modules/plan-intelligence.md) (take-off is **not** a separate module) |
| Related ADRs | [ADR-005](../adr/ADR-005-ai-takeoff-traceability.md) **Accepted** · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) **Accepted** · [ADR-009](../adr/ADR-009-pdf-first-versus-cad-first.md) **Accepted** · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** · [ADR-011](../adr/ADR-011-ai-confidence-threshold-policy.md) **Accepted** · [ADR-012](../adr/ADR-012-plan-document-version-ownership.md) **Proposed** (revision immutability practiced in M007+) · [ADR-026](../adr/ADR-026-scale-ownership-and-calibration-provenance.md) **Accepted** · [ADR-027](../adr/ADR-027-pdf-rendering-and-normalized-coordinate-system.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** · [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** · [ADR-031](../adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) **Accepted** |
| Prerequisites | M005–M010 Plan Intelligence **implemented**; FG-007/M011 org isolation **implemented**; FG-008 Labour Engine **CLOSED / OPERATIONAL FOR UAT**; FG-009 Pricing Engine **CLOSED / OPERATIONAL FOR UAT** |
| Product code | `app/plan_intelligence/models.py` (`TakeoffExtractionRun`, `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem`); `app/plan_intelligence/takeoff.py`; `app/plan_intelligence/takeoff_extractors.py` (deterministic mock only); office routes/templates. Migration `migrations/versions/b4c5d6e7f8a9_add_ai_takeoff_foundation_fg010.py`. |

This document is **approved architecture** plus a **verified foundation implementation**. It does **not** authorize a real external AI provider or Phase D estimate mapping.

---

## 1. Purpose

Define the durable architecture for **AI-assisted quantity extraction** as a PLAN capability:

```text
SOURCE PLAN
  → EXTRACTION RUN
  → CANDIDATE ELEMENTS
  → HUMAN REVIEW
  → REVIEWED TAKE-OFF
  → APPROVED TAKE-OFF PACKAGE
```

CalibAi owns **methodology** (how candidates are proposed, cited, reviewed, versioned, and kept from floating). Each organization owns its **plans and reviewed quantities**. Brayman (`ORG-001`) is not a universal model.

This foundation must **not** silently cross into PRICE. FG-009 remains the selling-price authority. FG-008 remains labour-methodology authority.

---

## 2. Current vs intended vs future

### Current (implemented — cite code)

| Capability | Evidence |
|------------|----------|
| Project-scoped PDF upload, archive, checksum | `app/plan_intelligence/services.py`, `PlanDocument` |
| Deterministic embedded-text extraction; **no OCR** | `app/plan_intelligence/extraction.py` (`deterministic_pdf` 1.0.0) |
| Pages, processing attempts/results, search | `PlanPage`, `ProcessingAttempt`, `ProcessingResult` |
| Drawing package / revision (minimal) | `DrawingPackage`, `DrawingRevision` |
| Sheet identity, human metadata review | `PlanSheet`, `PlanSheetPage`, `PlanSheetSuggestion`; `REVIEW_STATUSES` draft/suggested/reviewed/void |
| Scale calibration + manual measurement | `PlanScaleCalibration`, `PlanMeasurement`; PDF.js 3.11.174 |
| Normalized coordinates `[0,1]×[0,1]` | ADR-027; `geometry_data` JSON; overlay in `app/static/js/sheet-measurement.js` |
| Manual measurement types | `linear`, `polyline`, `area` (+ `perimeter_value` on area), `count` (COUNT does **not** require scale) |
| Append-only plan audit | `PlanAuditEvent` via `app/plan_intelligence/audit.py` (additive take-off FKs) |
| Org isolation at project route | `_get_project_or_404` requires `organization_id == current org` |
| Take-off extraction runs / candidates / packages | `TakeoffExtractionRun`, `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem`; `app/plan_intelligence/takeoff.py` |
| Provider-neutral extractor | `app/plan_intelligence/takeoff_extractors.py` — **deterministic mock only** (`calibai-mock`) |
| Office take-off UI | `/projects/<id>/plans/takeoff` |

**Not implemented:** real external AI provider; OCR; CAD; estimate mapping from take-off (Phase D); Labour/Pricing Engine consumption of take-off packages.

### Implemented (this architecture / FG-010)

Phase **C** foundation: searchable architectural PDF → interior-door **count** candidates (mock) → human review → immutable approved take-off package. Real external AI provider **not authorized**. Live DB **not** migrated to `b4c5d6e7f8a9`.

### Future (separate gates)

OCR/scanned; CAD; multi-trade; schedule cross-check automation; Phase **D** estimate mapping; Labour Engine consumption of reviewed quantities; Pricing Engine application to mapped estimate versions.

---

## 3. Search-before-new (reuse)

| Existing | Reuse |
|----------|--------|
| `PlanDocument` / `PlanPage` / `DrawingRevision` / `PlanSheet` | Source identity. Do not duplicate. |
| ADR-027 normalized bbox | **Only** coordinate system for candidate geometry. |
| `PlanAuditEvent` | Extend with new `event_type` values and additive nullable FKs (`extraction_run_id`, `takeoff_candidate_id`, `takeoff_package_id`). Do not create a parallel audit log. |
| Sheet suggestion statuses | Pattern only (`open`/`accepted`/`rejected`). Take-off candidates need additional `adjusted` / `duplicate` / `not_applicable`. |
| Labour `LabourCalibrationCandidate` lifecycle | Pattern only. Do not store take-off in Labour Engine tables. |
| M010 `PlanMeasurement` | Remains **manual** measurement SoR. AI candidates are a **separate** entity that may *reference* the same sheet/page/norm-box. Do not overload `PlanMeasurement` as an AI candidate. |
| ProcessingAttempt/Result | Pattern for run provenance. Extraction runs are first-class take-off objects, not a reuse of PDF text-index attempts. |

**NO DUPLICATE COORDINATE MODEL.**

---

## 4. Recommended POC

| Field | Recommendation |
|-------|----------------|
| Name | Interior door opening **count** from searchable architectural PDF |
| Input | Existing uploaded `PlanDocument` with `has_text_layer=True` |
| Sheets | Architectural floor-plan `PlanSheet` (`discipline_code=ARCH` or human-confirmed architectural); **one or two sheets** per trial job |
| Element vocabulary (V1) | `INTERIOR_DOOR_OPENING` — quantity contribution typically `1` count per accepted candidate |
| Optional later | Door-schedule cross-check (not in V1 implementation) |
| Explicitly not V1 | Windows, walls, concrete, framing, roof, electrical, mechanical, multi-trade |

The element-type field is a **controlled vocabulary string**, not a door-only schema. V1 ships one value.

---

## 5. Input boundary

**In:**

- Searchable PDF already stored as `PlanDocument` (M005+)
- Architectural floor-plan sheets with page maps (M009)
- Current org’s project only

**Out unless a later gate says otherwise:**

OCR, scanned-image recognition, CAD/DWG/DXF, photo take-off, hand sketches, supplier documents, specification extraction, external web search, uploading new files solely for AI (use existing upload).

Eligibility fail-closed:

1. Unknown organization → no run
2. Project not in current org → no run
3. `has_text_layer` is false → ineligible (V1)
4. Sheet not mapped to a page → ineligible
5. Document archived → ineligible

Human may still **confirm** sheet is an architectural floor plan even if discipline is `OTHER`; AI must not silently reclassify sheet SoR (ADR-015 / M009).

---

## 6. AI authority

**AI MAY:** inspect eligible page content; propose candidates (type, location, quantity contribution); assign confidence + explanation; flag ambiguity; optionally *propose* a schedule cross-reference later.

**AI MUST NOT:** approve quantities; alter plan metadata, scale, or sheet review status; create/update estimate lines or versions; set pricing policy/GM/markup/tax/posture/risk; alter Labour Tasks, mappings, production rates, DLCR, or calibration candidates; mutate historical take-off packages or prior runs.

Human review is authoritative.

---

## 7. Extraction run (first-class)

**Required entity (intended):** `TakeoffExtractionRun`

| Field (conceptual) | Role |
|--------------------|------|
| `organization_id`, `project_id` | Fail-closed tenant + project scope |
| `drawing_revision_id` | Frozen input revision |
| Eligible `plan_sheet_id` / `plan_page` list | Explicit selection at start |
| Requested extraction type / vocabulary version | e.g. `INTERIOR_DOOR_OPENING` count |
| Method / provider / model / version / config hash | Reproducibility; provider-agnostic |
| Status | `queued` → `running` → `succeeded` \| `failed` \| `cancelled` |
| Started/finished, error summary | Provenance |
| Candidate counts | Advisory |

A later rerun is a **new run** with a new id. It must not mutate candidates belonging to another run or any **approved** take-off package.

Reuse the *idea* of `ProcessingAttempt` (append-only runs) without mixing PDF text-index attempts with quantity extraction.

---

## 8. Take-off candidate

**Required entity (intended):** `TakeoffCandidate`

| Field (conceptual) | Role |
|--------------------|------|
| ids: org, project, run, sheet, document, page_index | Traceability |
| `element_type` | Controlled vocabulary (`INTERIOR_DOOR_OPENING` in V1) |
| `quantity_contribution` | AI-proposed count (usually 1) |
| `reviewed_quantity` | Null until human accept/adjust |
| `geometry` | Normalized bbox or point(s) `[0,1]` (ADR-027) |
| `confidence_numeric`, `confidence_band` | Advisory (see §13) |
| `source_evidence` | Text snippet / explanation / method |
| `status` | See §9 |
| `canonical_candidate_id` | Duplicate pointer; evidence retained |
| `schedule_ref` | Optional; unused in V1 |
| Reviewer, decided_at, review_note | Human authority |

Candidates are **not** estimate quantities.

---

## 9. Human-review lifecycle

Reconciled with existing Plan Intelligence conventions (`draft`/`suggested`/`reviewed`/`void` on sheets; `open`/`accepted`/`rejected` on suggestions) **without** overloading those columns.

**Candidate statuses (intended):**

| Status | Meaning |
|--------|---------|
| `suggested` | AI (or later manual) proposal; not reviewed |
| `accepted` | Human accepted proposed quantity/geometry |
| `adjusted` | Human changed quantity and/or geometry; before/after in audit |
| `rejected` | Not this element / false positive; evidence kept |
| `duplicate` | Same physical opening as `canonical_candidate_id`; not counted |
| `not_applicable` | Wrong sheet/type/out of scope |

No silent `accepted`. Confidence never flips status.

**Package statuses (intended):**

| Status | Meaning |
|--------|---------|
| `draft` | Review in progress; quantities may still change |
| `approved` | Frozen reviewed total; immutable |
| `superseded` | Replaced by a later approved package for a newer revision or explicit re-approval |

Lifecycle:

```text
SOURCE PLAN (immutable PlanDocument / Revision / Sheet / Page)
  → EXTRACTION RUN (append-only)
  → CANDIDATES (suggested → human decision)
  → DRAFT TAKE-OFF PACKAGE (aggregates reviewed candidates)
  → APPROVED TAKE-OFF PACKAGE (immutable snapshot of reviewed quantities)
```

---

## 10. Four quantity layers (must stay distinct)

| Layer | Owner | Meaning |
|-------|--------|---------|
| AI candidate count | Plan Intelligence | Proposed `quantity_contribution` |
| Human-reviewed candidate count | Plan Intelligence | `reviewed_quantity` after accept/adjust |
| Approved take-off package quantity | Plan Intelligence | Sum of included reviewed candidates on an **approved** package |
| Estimate quantity | Estimating | Line quantity on `EstimateVersion` after an **explicit** Phase D map |

These are **not** automatically the same. An approved package is **evidence for estimating**, not a PRICE event.

---

## 11. PLAN → PRICE boundary (critical)

FG-009 is **operational**. AI take-off must not bypass estimating or pricing governance.

```text
Approved TakeoffPackage
    → (FUTURE Phase D) explicit human map
    → draft editable EstimateVersion lines
    → (existing) human apply Pricing Engine snapshot
    → customer-facing proposal (existing; no internal GM)
```

**FG-010 / M012 implementation: mapping is OUT OF SCOPE.**

Recommendation: **option B/C** — architecture records the mapping contract; implementation deferred to a later Feature Gate (roadmap Phase D). No optional “quick insert” in V1.

AI must not choose `CostItem`, `Assembly`, markup, waste, GM, tax, posture, or risk.

---

## 12. Assembly / CostItem / Labour / Pricing (non-goals)

| System | Boundary |
|--------|----------|
| Assembly / CostItem / EstimateSection / Line | Future explicit map only. Physical detection ≠ commercial line. |
| Labour Engine | Reviewed count may later feed Quantity × production rate. AI must not select ORG-APPROVED rates, tasks, mappings, DLCR, or calibration. FG-008 unchanged. |
| Pricing Engine | Must not set policy, GM, markup, contingency, tax, posture, risk, or overrides. After Phase D, humans may apply FG-009 to the estimate version as today. |

---

## 13. Confidence

Confidence is **advisory evidence**, never approval.

Store **both**:

- numeric in `[0.0, 1.0]`
- band `LOW` / `MEDIUM` / `HIGH` derived from documented cut-points when used for UI display (cut-points are not universal commercial policy; they must be explicit/configured and provenance-visible)

**Confidence NEVER equals human approval.** No threshold may auto-accept, auto-create an approved package, auto-insert estimate quantity, or auto-price work.

V1: no universal threshold auto-approves. ADR-011 batch-approve remains an **explicit human command** over listed candidates and still does not insert estimates (ADR-006).

Manual measurements (`PlanMeasurement`) remain outside AI thresholds (ADR-011 §6).

---

## 14. Duplicates / multi-sheet

Same opening may appear on floor plan, enlarged plan, RCP, and schedule.

AI may propose duplicates. Human may:

- mark `duplicate` and set `canonical_candidate_id`
- reject
- keep one representation as counted

Do **not** delete duplicate evidence. Approved package includes only non-duplicate accepted/adjusted candidates.

---

## 15. Drawing revisions

Align with ADR-012 / M007 practice:

- Prior **approved** take-off package remains immutable history.
- New `DrawingRevision` → new extraction run(s) referencing the new revision.
- Comparison (added/removed/changed/unchanged) is **future**; storage must allow it.
- Activating a new revision must not mutate old packages or estimates.

---

## 16. Scale

**COUNT is dimensionless.** Interior door COUNT does not require dimensional scale to derive quantity.

- A count candidate / reviewed count must **not** require a confirmed `PlanScaleCalibration` merely to count discrete objects.
- Future FG-010 implementation **may** permit `measurement_type = count` without confirmed dimensional calibration. This authorization applies **only** to count.
- Do **not** weaken M010 for `linear`, `polyline`, `area`, or perimeter: those must continue to fail closed unless the governing scale/viewport calibration is valid (non-NTS, confirmed).
- Current M010 code requires confirmed calibration even for manual `PlanMeasurement` `count`. That is a **narrow authorized correction** for the FG-010 implementation prompt. **Do not change code in this governance pass.**
- Future length/area AI extraction **must** require confirmed scale (ADR-026).

---

## 17. Provider abstraction

Do not lock schema to one vendor.

Persist: `extraction_method`, `provider`, `model_name`, `model_version`, `config_hash` (prompt/config identity).

FG-010 implementation **may** build a provider-neutral extraction interface and a deterministic/mock/test extractor (or internal development adapter).

**REAL EXTERNAL AI PROVIDER INTEGRATION IS NOT AUTHORIZED.** Do not send customer or UAT plan bytes/text to an external AI service merely because FG-010 is approved.

Before a real provider is enabled, require a separate governed decision covering: provider identity, data sent, retention, training/data-use terms, privacy/security, credential handling, failure behavior, and cost/control boundary (ADR-010 amendment/acceptance or another artifact).

---

## 18. Organization isolation

All take-off records carry `organization_id` **and** `project_id`. Project must belong to that org (ADR-028).

Direct-ID access to another org’s run/candidate/package **fail-closed**. No cross-org learning or pooling (ADR-024).

Existing plan tables lack `organization_id` columns; they remain project-scoped with route-level org checks. New take-off tables **must** include `organization_id` (do not wait to retrofit every M005 table in this gate).

---

## 19. Audit

Append-only `PlanAuditEvent` (extended) for at least:

- run create/start/complete/fail/cancel
- candidate create
- accept / adjust / reject / duplicate / not_applicable
- package draft create
- package approve
- package supersede
- revision-linked rerun (new run id)

No silent state change. Reviewer identity: human actor required where auth is absent (same pattern as FG-008/FG-009 `created_by` / `approved_by` strings) until authentication is Feature-Gated.

---

## 20. Approved take-off package

**Required entity (intended):** `TakeoffPackage`

Frozen on approve:

- org/project/revision
- source extraction run id(s)
- included candidate snapshot (id, type, reviewed quantity, bbox, citation fields)
- approved total + unit (`count`)
- reviewer, approved_at, notes/exceptions
- provenance

Later candidate edits or model reruns **must not float** an approved package (same spirit as `EstimatePricingSnapshot` / `EstimateLabourSnapshot`).

---

## 21. POC success criteria (for later implementation)

1. Existing searchable PDF selected.
2. Architectural sheet confirmed by human (M009 SoR not silently rewritten).
3. Extraction run explicitly initiated.
4. AI proposes interior-door candidates.
5. Every candidate retains page/sheet/normalized bbox provenance.
6. Reviewer can accept, adjust, reject, mark duplicate.
7. Reviewed total is deterministic from included reviewed candidates.
8. Approved package is immutable/versioned.
9. Rerun does not mutate old approved package.
10. No estimate line is silently created.
11. No Pricing Engine mutation.
12. Cross-org direct-ID fails closed.

---

## 22. UAT later (do not create data now)

Prefer a **synthetic** searchable architectural PDF in a clearly labeled UAT project, or an already-uploaded test document in development/UAT.

Do **not** casually use 3415 Roger Stevens / customer production plans for AI provider calls.

No UAT records in this architecture pass.

---

## 23. Security / privacy (later implementation)

If a provider later receives page images or extracted text (only after a **separate** provider authorization):

- org-scoped; no training on customer plans unless Joel-approved contract
- citations and quantities remain Estimator-owned (ADR-005)

**Not authorized now.** Unauthenticated office app remains platform debt (same as M009/FG-009). Actor strings are not equivalent to completed authentication.

---

## 24. FG-009 carry-forward (do not fix here)

- ORG-001 overhead/profit/contingency remain `UNSPECIFIED`
- Labour-snapshot Direct Labour Cost not in estimate basis by default
- Synthetic FG-009 UAT residue exists and is labeled
- Estimate Totals header may still show leftover stack percents when a pricing snapshot exists — **separate bounded UI maintenance**, not this gate

---

## 25. Intended additive schema (implementation later)

Additive tables under Plan Intelligence, names indicative:

- `takeoff_extraction_runs`
- `takeoff_candidates`
- `takeoff_packages`
- `takeoff_package_items` (frozen snapshot rows)

Nullable FKs on `plan_audit_events` for those ids.

**No live migration in this implementation pass.** Additive migration `b4c5d6e7f8a9` exists in the working tree and is the Alembic graph head. Live `flask db current` remains `a3b4c5d6e7f8`.

---

## 26. Test readiness

Covered in `tests/test_takeoff.py` and COUNT-without-scale tests in `tests/test_scale_measurement.py`, plus Plan Intelligence / FG-008 / FG-009 / full-suite regression.

---

## 27. Readiness

| Layer | State |
|-------|--------|
| This architecture | **Approved** (2026-08-29) |
| FG-010 | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| ADR-031 / 005 / 006 / 007 / 009 / 011 | **Accepted** |
| ADR-010 | **Proposed** — PDF.js historical FG-005 fact; remaining buy decisions deferred; **real external AI provider not authorized** |
| Product code | **Implemented** (mock extractor only; live-migrated; UAT-smoke-verified) |
| Real external AI provider | **NOT AUTHORIZED** |
| Phase D estimate mapping | **NOT STARTED** |

**Next action:** **STOP DEVELOPMENT.** 29 Aug day-end turnover is the closure of this cycle. Do not enable a real external AI provider. Do not start Phase D. Next roadmap candidate is Project Hub UX — **NOT STARTED / NOT AUTHORIZED**.

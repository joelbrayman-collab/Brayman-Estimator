# Architecture — Plan Intelligence and Automated Take-Off

| Attribute | Value |
|-----------|--------|
| Status | **Architecture documented (M004); Phase A–M010 implemented in code; M012 / FG-010 IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Updated | 2026-08-30 |
| Module | [../modules/plan-intelligence.md](../modules/plan-intelligence.md) |
| Related | [platform-roadmap.md](../platform-roadmap.md) · [document-intelligence.md](document-intelligence.md) · [ai-takeoff-quantity-extraction-foundation.md](ai-takeoff-quantity-extraction-foundation.md) · ADR-005–007, 009–016, 026–027, 031 |

**Current vs future:** Phase A PDF upload/storage, Document Intelligence indexing, sheets, and M010 scale/measurement exist under Plan Intelligence. **AI quantity extraction foundation is operational for UAT** (mock extractor; live-migrated). Real external AI provider is **not authorized**. OCR/CAD remain future. Estimating and Proposals exist separately.

**COUNT / scale (FG-010):** COUNT is dimensionless. `measurement_type = count` does not require confirmed dimensional calibration. Linear / polyline / area / perimeter continue to fail closed without valid scale.

Narrow M012 design: [ai-takeoff-quantity-extraction-foundation.md](ai-takeoff-quantity-extraction-foundation.md).

---

## 1. Strategic position

```text
Construction Plans
        ↓
AI-assisted Quantity Take-Off     ← Plan Intelligence
        ↓
Estimate Assemblies               ← Estimating (existing; not redesigned)
        ↓
Labour / Material Pricing
        ↓
Proposal                          ← Proposals (existing)
        ↓
Procurement
        ↓
Project Cost Tracking
```

Plan Intelligence **feeds** the estimate builder; it does not replace it.

---

## 2. End-to-end processing pipeline

```text
Upload
  → Document storage
  → Virus / type validation
  → Document Intelligence (Drawing Package / Revision / Sheet index / metadata / search)  ← M006 architecture
  → OCR (if required)
  → Drawing classification (discipline)
  → Revision detection / activation
  → Sheet indexing
  → Scale detection (+ human confirmation)
  → AI element recognition
  → Geometry extraction
  → Quantity calculations
  → Human review
  → Estimate assembly mapping (proposed only)
  → Estimate generation (explicit human commit into EstimateVersion)
  → Proposal generation (existing Proposals module; out of Plan Intelligence ownership)
```

Document Intelligence detail: [document-intelligence.md](document-intelligence.md). FG-003: [../feature-gates/FG-003-document-intelligence-readiness.md](../feature-gates/FG-003-document-intelligence-readiness.md).

### Stage details

#### Upload

| | |
|--|--|
| **Inputs** | User file(s); target `Project` id |
| **Outputs** | Upload job id; raw object reference |
| **Responsibilities** | Authz (project-scoped); size/type allowlist; reject executables |
| **Failure** | Reject with clear error; no partial register |
| **Audit** | Who uploaded, when, filename, checksum |

#### Document storage

| | |
|--|--|
| **Inputs** | Validated bytes; metadata |
| **Outputs** | Stored blob URI; `DrawingSet` / document version record |
| **Responsibilities** | Private storage (not public static); encryption at rest where practical |
| **Failure** | Roll back register if store fails |
| **Audit** | Storage location class; retention tag |

#### Virus / type validation

| | |
|--|--|
| **Inputs** | Stored object |
| **Outputs** | Pass/fail; content-type confirmation |
| **Responsibilities** | Malware scan when available; MIME sniffing |
| **Failure** | Quarantine; block downstream pipeline |
| **Audit** | Scan engine/version; result |

#### OCR (if required)

| | |
|--|--|
| **Inputs** | Scanned PDF pages |
| **Outputs** | Text layer / page images with OCR text |
| **Responsibilities** | Optional path; **not in first POC** |
| **Failure** | Mark page OCR-failed; continue with manual tools if allowed |
| **Audit** | OCR engine/version; confidence |

#### Drawing classification

| | |
|--|--|
| **Inputs** | Pages / sheets |
| **Outputs** | Discipline, sheet purpose, confidence |
| **Responsibilities** | Architectural / structural / civil / etc.; human override |
| **Failure** | Default to `unknown`; require human classify before AI extract |
| **Audit** | Classifier id; human override events |

#### Revision detection

| | |
|--|--|
| **Inputs** | Title block / revision table / filename conventions |
| **Outputs** | `Revision` label; links prior set if detectable |
| **Responsibilities** | Never overwrite prior revision’s take-offs |
| **Failure** | Prompt human to assign revision |
| **Audit** | Detected vs confirmed revision |

#### Sheet indexing

| | |
|--|--|
| **Inputs** | Pages |
| **Outputs** | `Sheet` records (number, name, page index) |
| **Responsibilities** | Stable sheet ids within a revision |
| **Failure** | Index as page-N until named |
| **Audit** | Index run id |

#### Scale detection

| | |
|--|--|
| **Inputs** | Sheet image/text; scale bar / title block |
| **Outputs** | Candidate scale(s); units |
| **Responsibilities** | **Human confirmation required** before quantities are estimate-eligible |
| **Failure** | Block AI quantity approval until scale confirmed |
| **Audit** | Detected scale; confirmer; timestamp |

#### AI element recognition

| | |
|--|--|
| **Inputs** | Confirmed-scale sheet; element vocabulary (narrow for POC) |
| **Outputs** | `DetectedElement` candidates + confidence |
| **Responsibilities** | Propose only; never write estimates |
| **Failure** | Empty candidate set; fall back to manual measure |
| **Audit** | Model id/version; prompt/vocab version |

#### Geometry extraction

| | |
|--|--|
| **Inputs** | Detected elements or manual tool strokes |
| **Outputs** | Regions (bbox/polygon), counts, lengths, areas in page coords |
| **Responsibilities** | Persist geometry for highlight/review |
| **Failure** | Discard invalid geometry; require re-measure |
| **Audit** | Method = AI \| manual |

#### Quantity calculations

| | |
|--|--|
| **Inputs** | Geometry + confirmed scale + method code |
| **Outputs** | `Quantity` candidates (count, LF, SF, CY, …) |
| **Responsibilities** | Deterministic math from inputs; store formula/method |
| **Failure** | Mark **dimensional** quantity invalid if scale missing. **COUNT is dimensionless** and must not require scale merely to count objects (FG-010 / ADR-031). |
| **Audit** | Inputs hash; computed value |

#### Human review

| | |
|--|--|
| **Inputs** | Candidates + highlights + confidence |
| **Outputs** | Approved / rejected / adjusted quantities; review record |
| **Responsibilities** | Mandatory before estimate mapping commit (ADR-006) |
| **Failure** | Package stays `InReview`; no estimate insert |
| **Audit** | Full review history (see §4) |

#### Estimate assembly mapping

| | |
|--|--|
| **Inputs** | Approved quantities; mapping rules → assemblies/cost items |
| **Outputs** | **Proposed** estimate line drafts (not yet persisted as authority) |
| **Responsibilities** | Plan Intelligence proposes; Estimating service commits |
| **Failure** | Unmapped items queued; no silent skip into wrong assembly |
| **Audit** | Mapping rule version; proposed lines |

#### Estimate generation

| | |
|--|--|
| **Inputs** | Explicit user “Insert into estimate version V” |
| **Outputs** | New/updated lines on editable `EstimateVersion` via Estimating APIs |
| **Responsibilities** | Respect estimate locks; never touch locked/issued versions without Estimating rules |
| **Failure** | Abort transaction; leave take-off approved state intact |
| **Audit** | Link take-off version → estimate version |

#### Proposal generation

| | |
|--|--|
| **Inputs** | Estimate version (existing flow) |
| **Outputs** | Proposal snapshot (existing Proposals module) |
| **Responsibilities** | **Out of Plan Intelligence ownership** — documented only for end-to-end clarity |
| **Failure** | Existing proposal error handling |
| **Audit** | Existing proposal audit/immutability (Accepted lock) |

---

## 3. Conceptual document model

**Not SQLAlchemy models.** Conceptual entities for future schema Feature Gates.

| Concept | Description |
|---------|-------------|
| **Project** | Existing CRM/Projects entity; scopes all plan work |
| **Drawing Set** | Uploaded plan package bound to a project |
| **Revision** | Immutable version of a drawing set (A, B, cloud#, etc.) |
| **Sheet** | One sheet/page within a revision (number, name, discipline) |
| **Viewport** | Optional cropped region / detail callout on a sheet |
| **Scale** | Sheet- or viewport-level scale + units; confirmation state |
| **Layer** | Logical layer/class for detections (doors, walls, …) — PDF may approximate |
| **Detected Element** | AI or manual instance (type, geometry ref, confidence) |
| **Measurement** | Raw measure (count/length/area) before business quantity rules |
| **Quantity** | Business quantity derived from measurement(s) |
| **Review** | Human review session/actions on candidates |
| **Approval** | Explicit accept of a quantity or take-off package |
| **Confidence** | Score + reason codes on AI outputs |
| **Correction** | Human adjustment with before/after values |
| **Audit History** | Append-only event log across the pipeline |

### Relationships (conceptual)

```text
Project
  └── DrawingSet
        └── Revision (append-only history)
              └── Sheet
                    ├── Scale (confirmed)
                    ├── Viewport?
                    └── DetectedElement → Measurement → Quantity
                                                      ├── Confidence
                                                      ├── Correction*
                                                      └── Review / Approval
```

Take-off **package version** aggregates approved quantities for a revision and is the unit mapped into an `EstimateVersion`.

---

## 4. Human review workflow

**Invariant:** The system must **never** silently insert AI-generated quantities into estimates (ADR-006).

### Confidence scoring

- Every AI candidate carries `confidence` ∈ [0,1] (or 0–100) plus reason codes.
- Below threshold (ADR-011) → cannot batch-approve; requires explicit per-item review.
- Manual measurements may be marked `confidence = human` (authoritative).

### Manual verification

- Reviewer sees sheet image with **highlighted geometry**.
- Can zoom to cited region; compare schedule if present (later).

### Approval workflow

1. Reviewer opens take-off package for a revision.
2. Accepts, adjusts, or rejects each candidate.
3. Adjustments create `Correction` records.
4. Package-level **Approve** freezes approved quantities for mapping.

### Rejection workflow

- Rejected candidates remain in history with reason.
- May be re-opened only as new candidates (no silent revive into estimate).

### Manual overrides

- Override quantity value, type, or mapping target.
- Overrides require note; fully audited.

### Review history & audit logging

Append-only events: viewed, accepted, rejected, adjusted, scale confirmed, package approved, mapping proposed, estimate insert requested/completed/failed.

---

## 5. Source traceability

Every estimate quantity that originated from Plan Intelligence should be traceable to:

| Citation field | Required |
|----------------|----------|
| Uploaded file / object id | Yes |
| Drawing set + **revision** | Yes |
| Sheet number / name | Yes |
| Page index | Yes |
| Drawing region (bbox/polygon) | Yes |
| AI confidence (+ model version) | Yes if AI-sourced |
| Reviewer identity | Yes when auth exists; else placeholder until auth Feature |
| Approval date/time | Yes |
| Manual corrections (before/after) | Yes if any |

**Architecture rule:** Citations are first-class records on the take-off quantity and copied (snapshotted) onto mapping/insert audit links—not optional comments (ADR-005).

Estimating lines should store a reference to the take-off quantity / citation bundle when created via this path, without making the estimate a live pointer that mutates when plans change.

---

## 6. Estimate mapping (feeds existing builder)

Plan Intelligence **does not redesign** Estimating. It produces approved quantities and mapping proposals; Estimating owns persistence of sections/lines.

### Mapping targets

| Take-off output | Maps toward |
|-----------------|-------------|
| Approved quantity + type | Estimate **Section** (by rule or user pick) |
| Quantity type / trade | **Assembly** and/or **Cost Item** templates |
| Assembly expansion | **Labour**, **Materials**, **Equipment** (via existing assembly items) |
| Optional factors | **Waste**, line **markup** (Estimating rules / user confirm) |
| Version-level | **Overhead**, **Profit**, **Tax** remain on `EstimateVersion` (existing) — not invented by AI |

### Insertion rules

1. Only **approved** quantities may be offered for insert.
2. User selects target editable `EstimateVersion`.
3. Estimating service creates lines (same validation as manual builder).
4. Locked/issued versions remain protected by existing Estimating locks.
5. Re-running AI never updates existing estimate lines automatically (ADR-007).

### Proposal path

After estimate lines exist, users create proposals via the **existing** Proposals module (snapshot + Accepted immutability). Plan Intelligence does not own proposals.

---

## 7. Security and storage (summary)

- Project-scoped access; secrets/env for object storage.
- No plan binaries in chat logs or git.
- Retention/deletion policy required before production (Joel).

---

## 8. Technical risks

See module doc. Highest: false quantities, wrong scale, scope creep, silent insert. Mitigations: ADR-005/006/007/009/011.

---

## 9. Phased implementation & POC

See [platform-roadmap.md](../platform-roadmap.md) Phases A–G and §10 below.

### Recommended Proof of Concept (safest / smallest)

| Field | Recommendation |
|-------|----------------|
| **Name** | Plan Intelligence POC — Interior Door Count |
| **Input** | **One searchable PDF** only |
| **Discipline** | **Architectural** floor plan (≤2 sheets) |
| **Element** | **Interior door openings — count** (one measurable element) |
| **Output** | One verified quantity with citations |
| **Human approval** | Mandatory accept before any estimate action |
| **Estimate** | Insert into **one** assembly/line on one draft `EstimateVersion` |
| **Non-goals** | OCR optimisation; CAD/DWG/IFC; supplier integrations; procurement; multi-trade AI; auto-insert; proposal changes |

**Implementation order for POC:** Phase A (upload/store/register) → minimal sheet index + manual/AI count with review → single mapping insert. Prefer manual count in first coded slice if AI model not Feature-Gated yet.

---

## 10. Related ADRs

| ADR | Topic | Status |
|-----|-------|--------|
| [ADR-005](../adr/ADR-005-ai-takeoff-traceability.md) | Source traceability / AI take-off audit | Proposed |
| [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) | Human approval required | Proposed |
| [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) | Plan vs estimate ownership | Proposed |
| [ADR-009](../adr/ADR-009-pdf-first-versus-cad-first.md) | PDF-first vs CAD-first | Proposed |
| [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) | Build vs buy | Proposed |
| [ADR-011](../adr/ADR-011-ai-confidence-threshold-policy.md) | AI confidence threshold policy | Proposed |

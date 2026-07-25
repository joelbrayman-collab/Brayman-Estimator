# Architecture — Plan Intelligence and Automated Take-Off

| Attribute | Value |
|-----------|--------|
| Status | **Future architecture** (not implemented) |
| Updated | 2026-07-25 |
| Module (proposed) | Plan Intelligence / Quantity Take-Off |
| Related | [platform-roadmap.md](../platform-roadmap.md) · [architecture.md](../architecture.md) · ADR-005–007, ADR-009–010 |

**Current vs future:** The repository today has **no** plan upload, sheet classification, take-off, OCR, CAD, or AI extraction modules. Estimating and Proposals are implemented separately. Everything below is **intended architecture** until Feature-Gated and built.

---

## Purpose

Enable a builder or developer to ingest construction plans, produce a **source-traceable quantity take-off**, map reviewed quantities into estimate assemblies/line items, and preserve auditability so AI never silently invents or overwrites commercial numbers.

Downstream consumers (existing): Estimating → Proposals → Project Controls.  
Upstream (new): Plan documents and human-reviewed take-off records.

---

## Supported source types

| Source | Near-term | Later | Notes |
|--------|-----------|-------|-------|
| Searchable PDF | **Phase A–D target** | — | Text layer available; preferred POC input |
| Scanned PDF | Deferred after POC | Phase C+ with OCR | Higher error risk; confidence scoring mandatory |
| Architectural plans | POC + Phase B–D | — | Primary discipline for first POC |
| Structural plans | Later | Phase C+ | Separate symbol vocabularies |
| Civil / site plans | Later | Phase C+ | Scales and units often differ |
| Specifications | Later | Parallel track | Quantity rules may cite spec sections |
| DWG / DXF | **Not Phase A–F** | Phase G | Requires build-vs-buy ADR-010 |

---

## Ingestion pipeline (intended)

```text
Upload → Store (encrypted at rest where practical) → Virus/type validation
  → Document register (project-scoped)
  → Page/sheet extraction
  → Classification (discipline, sheet type, revision)
  → Scale detection / confirmation
  → Geometry & symbol extraction (AI-assisted and/or manual tools)
  → Quantity candidates + confidence
  → Human review & adjustment
  → Approved take-off snapshot
  → Explicit map into EstimateVersion (never silent)
```

Ownership: a future **Plan Intelligence** module owns document, sheet, measurement, and take-off candidate records. **Estimating** owns estimate versions and line items. Insertion crosses modules only via approved service boundary (Rule 11) after human approval (ADR-006).

---

## Document and sheet classification

- Detect (or assign) discipline: architectural, structural, civil, MEP (later), unknown.
- Detect sheet purpose: floor plan, elevation, section, detail, schedule, cover, other.
- Persist classifier confidence and allow human override.
- Never delete human classification without audit.

## Revision handling

- Plans are versioned: document set revision, per-sheet revision bubbles/labels when detectable.
- New uploads create **new document versions**; prior take-offs remain readable.
- Changing a plan revision does **not** mutate an approved take-off or estimate; user must explicitly re-run or create a new take-off version (ADR-007).

## Scale detection and manual confirmation

- Attempt scale detection from title block / scale bar / known markers.
- **Human must confirm scale** before quantities are eligible for estimate insertion (Phase B+).
- Support dual units and sheet-specific scales.
- Record who confirmed scale and when.

## Geometry and symbol extraction

- Manual measurement tools first (Phase B): distance, area, count.
- AI-assisted extraction (Phase C): limited vocabulary (one trade/assembly).
- Store raw geometry references (page, bounding box / polygon in page coordinates).
- Symbol libraries are module-owned configuration, not free-form invented items.

## Quantity calculation

- Derived from confirmed scale + measurements/counts.
- Persist formula or method code (e.g. count, LF, SF, CY) with inputs.
- Waste factors applied only when mapping to estimate assemblies under Estimating rules—not silently inside take-off unless product defines take-off-level waste.

## Confidence scoring

- Every AI-generated quantity carries a confidence score and reason codes.
- Below threshold → cannot auto-approve; requires human review.
- Manual measurements may mark confidence = human-authoritative.

## Human review workflow

- Queue of candidates by sheet / assembly / confidence.
- Accept, reject, adjust quantity, adjust classification, attach notes.
- Dual control optional later for high-value packages.
- **No path** from AI candidate → estimate line without explicit approval (ADR-006).

## Source citations

Every approved quantity must cite:

- file / document version id  
- page number  
- sheet id / name if known  
- region (bounding box or measurement geometry)  
- extraction method (manual / AI model id + version)  
- reviewer identity (when auth exists) and timestamp  

Citations are first-class data, not optional comments.

## Audit history

- Append-only events: upload, classify, scale confirm, AI propose, human adjust, approve, reject, map-to-estimate, supersede.
- Distinguish AI-generated vs human-adjusted values.
- Financially significant insertion into estimates is auditable (Rule 6).

## Mapping take-off quantities to estimate assemblies

- Mapping rules link take-off item types → `Assembly` / `CostItem` / custom line templates owned by Estimating.
- Mapping produces **proposed** estimate line drafts; commit only on user action into a specific `EstimateVersion`.
- Locked / issued estimate versions remain protected by existing Estimating lock rules.

## Prevention of silent estimate changes

- Plan reprocessing never updates estimate lines automatically.
- Approved take-off versions are immutable snapshots; corrections create new take-off versions or audited adjustments per ADR-005/007.
- Align with Constitution Articles 5–6 and Rules 5–6.

## Versioning and snapshot requirements

| Record | Versioning |
|--------|------------|
| Plan document set | New version on re-upload / revision |
| Take-off package | Versioned; approve freezes package |
| Estimate | Existing `EstimateVersion` model |
| Mapping run | Snapshot of which take-off version fed which estimate version |

## Security and file storage

- Project-scoped access (auth model TBD).
- Store originals outside public static URL space; signed download only.
- Validate content type; reject executables; size limits.
- Do not log full plan binaries in chat or workflow logs.
- Retention and deletion policy required before production (Joel).
- No secrets in repo; object-storage credentials via environment.

## Technical risks

| Risk | Mitigation |
|------|------------|
| OCR / AI false quantities | Confidence + mandatory human approval |
| Wrong scale | Mandatory scale confirmation |
| Scope explosion across trades | Narrow POC; one assembly |
| CAD complexity | PDF-first (ADR-009); CAD Phase G |
| Build vs buy for viewers/CAD | ADR-010 before large spend |
| Silent overwrite | ADR-005/006/007; no auto-insert |
| Storage cost / PII in title blocks | Retention + access controls |

## Phased implementation

See [platform-roadmap.md](../platform-roadmap.md) Phases A–G. This document is the architectural authority for Plan Intelligence; the roadmap owns sequencing status labels.

## Explicit non-goals (until Feature-Gated)

- Live CAD round-trip editing  
- Fully autonomous estimate generation without review  
- Speculative AI pricing  
- Replacing Estimating or Proposals modules  

## Related ADRs

- [ADR-005](../adr/ADR-005-ai-takeoff-traceability.md) — AI take-off traceability  
- [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) — Human approval before estimate insertion  
- [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) — Plan and estimate version ownership  
- [ADR-009](../adr/ADR-009-pdf-first-versus-cad-first.md) — PDF-first vs CAD-first  
- [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) — Build vs buy  

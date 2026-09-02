# Module — BUILD

| Attribute | Value |
|-----------|--------|
| Status | **Partial Current** — Field Capture V1 **CLOSED / OPERATIONAL FOR UAT**. Change Orders remain Project Controls. Field Web **not implemented**. |
| Updated | 2026-09-01 |
| Code | `app/models/build.py`, `app/services/build.py`, `app/services/build_storage.py`, `app/services/build_rendition.py`, `app/routes/build.py`, `app/cli/build.py`, `app/templates/build/`; `/api/v1` BUILD adapter in `app/routes/api_v1.py` |
| ADR | [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** (boundary). [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Proposed**. [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **DRAFT / NOT APPROVED**. |
| CAR | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |

## Purpose

Own **field-execution records** for a Project so CalibAi can connect BUILD to the same authoritative project record used for PLAN / PRICE / CONTRACT.

Two first-class surfaces share one BUILD system of record ([ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**): **desktop / office** (review, management, confirmation — **this gate**) and **field / iPhone** (fast capture — Item 12, **not this gate**). Neither is scaffolding for the other. Office HTML calls Flask services directly. Field Web will consume Shared API → the same services.

## Owned records (FG-020)

Field Capture Event; Original Payloads (`text` / `audio` / `image`); Derived Candidates (`PROPOSED` / `CONFIRMED` / `REJECTED`); BUILD private original bytes under `instance/build_originals/`. JPEG, PNG, GIF, and HEIC/HEIF originals are preserved without transcoding. WebP is out. Later BUILD may still expand toward daily execution, crews, labour capture, and post-issuance permit operational evidence as separately gated.

## Referenced data

- `projects` (lifecycle hub — [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md))
- Change Orders (Project Controls) — **reference only**
- Plan Intelligence documents/sheets — **reference only**
- Estimating lines/tasks — **reference only**; actuals must not rewrite approved estimates ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted**, [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md))

## Prohibited responsibilities

- Owning Change Order commercial lifecycle (Project Controls)
- Owning estimates, cost library, or proposals
- Owning plan PDF binaries (Plan Intelligence)
- Silent AI write of labour/material/progress without human confirmation ([ADR-023](../adr/ADR-023-field-evidence-provenance.md))
- Transcription, voice AI, photo AI, Field Web chrome, MONITOR, Actual Direct Cost
- Owning Permit Intelligence preflight analysis ([permit-intelligence.md](permit-intelligence.md); [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). BUILD may later own **post-issuance** permit/inspection operational evidence only.

## Current implementation

**FG-020 Field Observation foundation** — models, additive revision `c1d2e3f4a5b6` (live current = head), office Project Hub **Field Observations** beside Change Orders, event create/detail/supersession, private original download, bounded `/api/v1` BUILD POSTs, `flask build propose-derived-candidate` for UAT. Confirm/reject does not write Estimate, Proposal, Change Order, Permit, take-off, or MONITOR records. Office UAT **PASSED** on port **5013**.

**Compatible Renditions (image-only increment)** — `app/services/build_rendition.py`. HEIC/HEIF Originals get an automatic JPEG at `instance/build_renditions/<org>/<project>/<event>/<original_id>/display.jpg` (`BUILD_RENDITION_ROOT`). Pillow + pillow-heif; JPEG quality 85; max long edge 2048 px; EXIF orientation applied. Failure does not roll back Original Source. JPEG/PNG/GIF stay native. Audio is unchanged. No schema. Event Detail renders the JPEG as **Photo** with an **Original** link. Hub Field Observations list is unchanged (no thumbnail redesign).

**Not implemented:** Project Closeout / archive-and-purge; Field Web / Today / iPhone Capture chrome; microphone or camera UI; transcription; audio conversion; MONITOR; auto-Change Order.

**Storage lifecycle:** Active projects may retain Original Source **plus** regenerable Compatible Renditions. After a separately governed Project Closeout, archive Original Source, verify, then purge renditions first and duplicate active originals second. Do **not** accumulate redundant copies indefinitely. FG-020 must not block that future path. Closeout is **not** this gate.

## Dependencies

- Authentication before field capture ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md); [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**). [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**. Item 12 Field Web recon **COMPLETE / NOT IMPLEMENTED** ([field-web-today-and-capture.md](../architecture/field-web-today-and-capture.md)). [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Proposed**. [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **DRAFT / NOT APPROVED**. Implementation **NOT AUTHORIZED**.

## Related

- [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**
- [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Proposed**
- [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**
- [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **DRAFT / NOT APPROVED**
- [architecture/field-web-today-and-capture.md](../architecture/field-web-today-and-capture.md) — Item 12 recon **COMPLETE / NOT IMPLEMENTED**
- [architecture/build-media-storage-lifecycle.md](../architecture/build-media-storage-lifecycle.md) (Original Source / Compatible Rendition / Closed Project Archive — HEIC/HEIF JPEG renditions **implemented**; Closeout **not implemented**)
- [modules/projects.md](projects.md) (Change Orders)
- [modules/plan-intelligence.md](plan-intelligence.md)
- [modules/monitor.md](monitor.md) (comparison layer; does not own BUILD actuals)

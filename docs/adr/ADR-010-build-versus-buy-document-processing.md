# ADR-010 — Build versus Buy for CAD and Document-Processing Components

| Field | Value |
|-------|--------|
| Title | ADR-010: Build versus Buy for CAD and Document-Processing Components |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · [supplier architecture](../architecture/supplier-catalogue-inventory-pricing.md) |

## Context

PDF rendering, OCR, CAD parsing, and measurement UX are specialized. Building everything in-house can stall the product; buying can create lock-in and data-residency issues.

## Decision

*(Proposed)*

1. Before Phase B/C implementation spend, Joel reviews a short **build-vs-buy** options memo for: PDF render/viewer, OCR (if scanned), measurement overlay, and (later) CAD.
2. Default bias for POC Phase A–B: **minimize new dependencies**; use simplest PDF storage + metadata first; add viewers/OCR only under Feature Gate.
3. No dependency may be added to `requirements.txt` without Feature Gate + this ADR acceptance for that component class.
4. Prefer vendors that allow **export of citations/coordinates** into Estimator-owned records (ADR-005).

## Alternatives Considered

- Always build — High risk of delay.
- Always buy full take-off suite — Risk of opaque quantities and weak ownership.

## Consequences

Positive: conscious spend. Negative: decision latency before Phase B.

## Module Ownership Impact

Plan Intelligence integrates adapters; Estimating remains independent.

## Data Ownership Impact

Estimator-owned DB remains system of record for quantities/citations.

## Migration Impact

None until a component is chosen.

## Testing Impact

Adapter contract tests when a buy decision ships.

## Documentation Impact

Update this ADR with the chosen option when decided.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | No dependencies or code in this documentation sprint | |

---

## 2026-08-29 reconciliation (FG-010 / M012 architecture)

| Field | Recommendation |
|-------|----------------|
| Still correct? | **Partially.** Bias to minimize lock-in remains. |
| Amendment needed? | **Record historical fact:** Mozilla **PDF.js 3.11.174** was adopted under **FG-005 / M010** (ADR-027) without this ADR being Accepted. That viewer choice should be treated as **already decided for measurement UI**. OCR, CAD, and **real external AI provider** remain open. |
| Accept before implementation? | **Do not bulk-accept.** Keep Status **Proposed**. |
| Supersede? | **No.** |

---

## 2026-08-29 governance decision (FG-010)

**Status remains Proposed.** FG-010 approval does **not** accept this ADR.

**Real external AI provider integration is not authorized.** FG-010 implementation may build a provider-neutral extraction interface, persist provider/model/version fields, and use a deterministic/mock/test extractor or internal development adapter. It must **not** send customer or UAT plan bytes/text to an external AI service.

Before a real provider is enabled, a separate governed decision is required covering: provider identity, data sent, retention, training/data-use terms, privacy/security, credential handling, failure behavior, and cost/control boundary. That may later be an amendment/acceptance of this ADR or another governance artifact.

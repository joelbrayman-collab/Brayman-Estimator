# ADR-051 — Legal Content Source Classes, Candidate-Update Lifecycle, and Slice B / Slice D Boundary

| Field | Value |
|-------|--------|
| Title | ADR-051: Legal Content Source Classes, Candidate-Update Lifecycle, and Slice B / Slice D Boundary |
| Status | **Accepted** by Joel Brayman / ChatGPT Architect, 13 Sep 2026 (source-class / candidate-update / Slice B–D boundary). Subsequent Slice B product foundation is **implemented in the repository** from a later bounded prompt. This ADR still does **not** authorize live migration, office UAT, legal drafting, live monitoring, Slice C/D, or Native Signing. |
| Date | 2026-09-13; Accepted 2026-09-13 |
| Related | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) · [fg-024-slice-b-legal-content-source-lifecycle-preflight.md](../architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md) · [ADR-050](ADR-050-north-american-legal-content-library-ownership.md) **Accepted** · [legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [ADR-037](ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted** · [ADR-038](ADR-038-permit-intelligence-authority-and-rules-library.md) **Accepted** · [ADR-002](ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-010](ADR-010-build-versus-buy-document-processing.md) **Proposed** |

This ADR is the **source-class, candidate-update, and Slice B / Slice D boundary** for FG-024. It does **not** replace [ADR-050](ADR-050-north-american-legal-content-library-ownership.md) (library ownership and fail-closed selection). It does **not** reopen Slice A.

---

## Context

Slice A is **CLOSED / OPERATIONAL FOR UAT**: empty North American library, ADR-037-backed selection, coded fail-closed. The Legal Content Gate remains **empty**.

Without this ADR, a later implementer could:

- treat a retrieved statute or web page as APPROVED legal content;
- let AI mark candidates APPROVED or ACTIVE because a source changed;
- auto-deactivate an ACTIVE package merely because a candidate exists;
- put continuous web monitoring into Slice B;
- reuse Permit Rules as contract-update sources;
- treat Family 05 or org brand copy as jurisdiction legal authority;
- collapse Native Signing into the update engine.

[FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) already records the Update Engine flow and assigns live monitoring to Slice D. [v1-completion-register.md](../v1-completion-register.md) §9.2 makes Slice B V1 **manual/counsel-driven** and recommends Slice D live watchers **POST-V1**. Source-class authority and ACTIVE-package behaviour during candidate review are **not** fully inside ADR-050.

Constitution Article 8 requires an ADR for this ownership and invariant set.

---

## Decision

**Accepted.** Architecture only. Do **not** treat acceptance as Slice B product authorization. A later bounded Cursor prompt is required.

### 1. Slice B owns the source / update lifecycle; Slice D owns live monitoring

Slice B: source registration; manual ingestion; snapshot custody; candidate creation; impact-assessment records; human/counsel review routing; provenance for supersession.

Slice D: automated/live source watchers; stale-jurisdiction alerts; unsigned-document impact alerts.

Slice A continues to own persistence, selection, and fail-closed lookup. Slice C owns generation and frozen project snapshots. Native Signing remains a separate process track.

### 2. Four source classes; none silently become APPROVED

| Class | May be recorded | May become APPROVED legal content |
|-------|-----------------|-----------------------------------|
| A. Official primary source | Yes, as evidence | **No**, not by recording or retrieval |
| B. Counsel-supplied source / interpretation | Yes | **Only** after governed human/counsel approval of a **content version** |
| C. Organization-supplied commercial content | Yes, as commercial overlay evidence | **No** as jurisdiction legal authority |
| D. Secondary / informational source | Yes, as review material | **No** |

Do not inventory Ontario or U.S. instruments in this ADR.

### 3. AI may assist candidates; AI must not approve or activate

AI may later identify differences, summarize, map evidence, flag affected objects, and propose **PROPOSED** candidates.

AI must **not**: mark APPROVED or ACTIVE; issue legal advice as system authority; silently rewrite approved clauses; activate because a source changed; replace counsel; convert Class D into Class A; bypass the Legal Content Gate; mutate issued or signed contracts.

A real external AI provider remains unauthorized while [ADR-010](ADR-010-build-versus-buy-document-processing.md) is **Proposed**.

### 4. Preserve `APPROVED` ≠ `ACTIVE`

Counsel/human APPROVED authorizes a **content version**. Platform ACTIVE is a separate human activation under effective-date rules. Unresolved effective-date conflict → FAIL CLOSED (ADR-050).

### 5. Candidate creation does not auto-SUPERSEDE

Creating a PROPOSED candidate, or setting support status `UPDATE_PENDING_REVIEW`, must **not** by itself SUPERSEDE or deactivate an ACTIVE package.

### 6. ACTIVE-package usability during candidate review — deferred

**Explicitly deferred** by Joel Brayman / ChatGPT Architect on 13 Sep 2026 (Slice B governance reconciliation). Acceptance of this ADR does **not** choose generation option B, A, C, or D.

Existing fragments remain in force: `UPDATE_PENDING_REVIEW` implies an approved package still exists; unresolved effective-date conflict FAIL CLOSED; issued/signed snapshots stay immutable. Later Slice B product must **not** auto-SUPERSEDE or auto-deactivate ACTIVE merely because a candidate exists.

Whether generation from an ACTIVE package stays allowed while a candidate is in review and the package remains inside its effective window is a later Joel decision, required before Slice C / generation UX. It does **not** block Slice B architecture.

### 7. Acceptance does not authorize product implementation

Accepting this ADR does **not** by itself authorize product code, schema, migration, legal drafting, live monitoring, or Native Signing. A later bounded Cursor prompt is required.

---

## Alternatives Considered

- **No new ADR; implement Slice B from FG-024 + ADR-050** — Rejected for product start: source-class authority and update-vs-activation invariants are new durable rules (Article 8).
- **Put live web monitoring in Slice B** — Rejected: FG-024 Slice D; V1 register recommends POST-V1.
- **Treat official primary sources as auto-APPROVED** — Rejected: Legal Content Gate; AI/tools cannot independently APPROVE.
- **Reuse `permit_rules` as contract-update sources** — Rejected: ADR-038 / ADR-050 domain split.
- **Auto-deactivate ACTIVE when any candidate appears** — Rejected as an automatic rule: contradicts `UPDATE_PENDING_REVIEW`. Human/effective-date withdrawal remains the open decision in §6.

---

## Consequences

**Positive:** Slice B/D boundary frozen; source classes cannot silently become legal authority; AI approval/activation forbidden; Slice A fail-closed preserved.

**Negative:** Slice B product still cannot start until Joel issues a bounded implementation prompt. ACTIVE-during-review generation policy remains **deferred** (not option B). Ontario content remains BLOCKED on counsel (06D).

**Subsequent status (2026-09-13, Slice B product foundation):** A later bounded Cursor prompt implemented the source / snapshot / candidate / review foundation in the repository (Alembic **`c2d3e4f5a6b7`**). Live migration **not** run. Office UAT **not** started. Slice B **not closed**. §6 remains **deferred**. Legal Content Gate remains **empty**.

**Subsequent status (2026-09-13, Slice B live migrate + bounded office UAT):** Live `flask db upgrade` **PASS**. Live current **`c2d3e4f5a6b7 (head)`**. Bounded office UAT **PASS**. Slice B **CLOSED / OPERATIONAL FOR UAT**. §6 remains **deferred**. Legal Content Gate remains **empty**. Evidence [fg024-slice-b-live-migrate-bounded-uat-record.md](../testing/fg024-slice-b-live-migrate-bounded-uat-record.md). This ADR is **not** reopened.

**Subsequent status (2026-09-13, Slice C preflight):** Slice C generation / snapshot architecture frozen in [fg-024-slice-c-contract-generation-snapshot-preflight.md](../architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md). Product **NOT AUTHORIZED**. §6 remains **deferred** and is **not** resolved here. Pending-candidate generation stays unimplemented / fail-closed. New ADR **not** required.

## Module Ownership Impact

CONTRACT / FG-024 Slice B would own source, snapshot, candidate, and review-event records (later). Legal Content Gate retains APPROVED. Slice A retains selection/fail-closed. Slice D later owns watchers. Permit Intelligence unchanged. Native Signing unchanged.

## Data Ownership Impact

Source and candidate records are **platform-governed legal-process evidence**, not org commercial intelligence. They must not be pooled as another contractor’s legal templates. Generated project contracts remain Slice C / org-scoped.

## Migration Impact

**Deferred at acceptance.** Subsequent Slice B product created additive revision **`c2d3e4f5a6b7`** (`down_revision` **`b1c2d3e4f5a6`**). Subsequent live `flask db upgrade` **applied** 2026-09-13. Live current = repository head **`c2d3e4f5a6b7 (head)`**.

## Testing Impact

Subsequent empty-candidate product tests prove: no AI APPROVED/ACTIVE; candidate is not legal authority; candidate does not auto-SUPERSEDE or deactivate ACTIVE; empty library still BLOCK; no legal seed; no live monitoring.

## Documentation Impact

[fg-024-slice-b-legal-content-source-lifecycle-preflight.md](../architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md); [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); this ADR index.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman / ChatGPT Architect | 2026-09-13 |
| ChatGPT review | Slice B documentation preflight; existing-governance reconciliation / Accept | 2026-09-13 |
| Cursor implementation note | Drafted **Proposed** 2026-09-13 from ADR-000. **Accepted** 2026-09-13 documentation-only. Subsequent bounded product prompt implemented repository foundation 2026-09-13. §6 generation-while-pending remains **deferred**. Live migrate **not** authorized. |

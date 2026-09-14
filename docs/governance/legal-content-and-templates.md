# Legal Content and Template Governance

| Attribute | Value |
|-----------|--------|
| Status | **Governing** |
| Updated | 2026-09-13 |
| Implementation | Template registers remain **empty**. Slice A library persistence + selection engine **CLOSED / OPERATIONAL FOR UAT** (live / empty). Slice B source/update foundation **CLOSED / OPERATIONAL FOR UAT** (live). Slice C generation / snapshot **CLOSED / OPERATIONAL FOR UAT** (engine live / synthetic-UAT proven / no real jurisdictional content). [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. Legal-change monitoring remains **FUTURE**. [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **OVERALL OPEN / PARTIAL**. |

## Purpose

Govern construction contract language, statutory/consumer wording, warranty obligations, and legal templates. Ontario remains the **first expected** Canadian jurisdiction package and the historical register home. The Estimator may **not** invent or silently alter legal obligations.

**North American scope (future):** Canada (provinces and territories) and the United States (states) are the commercial destinations. Population is incremental. Architecture must not require redesign per jurisdiction. See [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md). This document remains the Legal Content Gate. FG-024 does **not** replace it.

## Legal Content Gate

| Rule | Detail |
|------|--------|
| Governed provenance | Ontario contract clauses, statutory/consumer wording, warranty language, and legal templates require **separately governed template provenance and approval** |
| AI / tool generation | AI or tool generation **cannot independently** set legal content to **APPROVED** |
| Human approval | Legal templates reach production use only after explicit governed approval |
| No silent edits | Approved template versions are superseded — not silently overwritten |

**August 2026 scope:** Record governance only. **Do not draft substantive Ontario contract language** in documentation or implementation tasks unless Joel explicitly authorizes template authoring under separate legal review.

## Ontario construction contract register (governed — empty until approved)

| Field | Policy |
|-------|--------|
| Template identity | Versioned register entry (ID, title, jurisdiction, effective date) |
| Source | Approved legal/commercial source — not ad hoc AI output |
| Approval state | Follows contract/warranty progression ([project-document-package.md](../architecture/project-document-package.md)) |
| Estimate linkage | Generated only from **APPROVED** estimate with provenance preserved |
| Attachment | Applicable warranty document attached as schedule |

**Register status:** No production templates registered in repository as of 2026-08-25. Future entries live in this governance track (implementation TBD).

**Subsequent status (2026-09-03):** Recovered Allen Jacques document **05** (`Ontario Construction Contract COMMERCIAL_DRAFT`) is an **approved presentation reference** only. It does **not** populate this register, does **not** authorize production contract use, customer execution, or Native Signing. See [approved-document-presentation-reference-baseline.md](../architecture/approved-document-presentation-reference-baseline.md).

**Subsequent status (2026-09-04):** Approved presentation **source custody CLOSED**. Durable exact ZIP is outside Git. That custody closure does **not** populate this register, does **not** approve Document 05 legal content, and does **not** authorize production contract use, customer execution, or Native Signing.

**Subsequent status (2026-09-04, FG-022 implementation):** [FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) extracted a project-neutral **presentation / commercial-draft reference** for family 05. That extraction does **not** populate this register, does **not** approve contract or warranty language, and does **not** authorize execution or Native Signing. Family 05 remains **COMMERCIAL DRAFT — NOT FOR EXECUTION**.

**Subsequent status (2026-09-04, FG-022 closure):** Joel recorded presentation-master approval for Families 01–07. [FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) is **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Family 05 is an **APPROVED REUSABLE PRESENTATION MASTER** only. This closure does **not** populate this register, does **not** approve contract or warranty language, and does **not** authorize execution or Native Signing. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED / NOT FOR EXECUTION / NOT FOR SIGNATURE**.

**Subsequent status (2026-09-07, FG-024 recorded):** [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) records the future North American CONTRACT-stage legal-content library, update engine, frozen generation snapshot, and change-monitoring capability. Status: **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. This recording does **not** populate this register, does **not** approve any legal language, does **not** authorize Ontario or U.S. content drafting, and does **not** interrupt [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md). AI still cannot independently set legal content to **APPROVED**. Fail closed if no counsel-approved jurisdiction package exists. No generic North American fallback.

**Subsequent status (2026-09-12, FG-024 Slice A preflight):** Architecture preflight **COMPLETE**. [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) drafted **Proposed**. This does **not** populate this register, does **not** approve any legal language, does **not** mark Family 05 legally approved, and does **not** authorize Slice A product code. Fail closed remains mandatory. No generic North American fallback.

**Subsequent status (2026-09-13):** [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted** by Joel Brayman / ChatGPT Architect (architecture / fail-closed ownership only). Slice A architecture prerequisite **satisfied**. This does **not** populate this register, does **not** approve any legal language, does **not** mark Family 05 legally approved, and does **not** authorize Slice A product code. Fail closed remains mandatory. No generic North American fallback.

**Subsequent status (2026-09-13, Slice A product):** Empty-library tables and coded fail-closed selection exist in the repository (`legal_content_jurisdiction_packages`, `legal_content_objects`, `app/services/legal_content.py`). Alembic **`b1c2d3e4f5a6`** not applied live. This **still does not** populate this register, approve any legal language, or mark Family 05 legally approved. Ontario project + empty library → **BLOCK**. No generic North American fallback.

**Subsequent status (2026-09-13, Slice B architecture):** Existing-governance reconciliation **validated** the Slice B source/update preflight. [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** (architecture only). Slice B **PREFLIGHT COMPLETE / PRODUCT NOT AUTHORIZED / NOT IMPLEMENTED**. This **still does not** populate this register. Generation-while-`UPDATE_PENDING_REVIEW` **deferred**.

**Subsequent status (2026-09-13, Slice B product foundation):** Source / snapshot / candidate / review tables and service exist in the repository (`legal_content_sources`, `legal_content_source_snapshots`, `legal_content_candidate_changes`, `legal_content_candidate_impacts`, `legal_content_review_events`, `app/services/legal_content_update.py`). Alembic **`c2d3e4f5a6b7`** not applied live. This **still does not** populate this register, approve any legal language, or mark Family 05 legally approved. AI still cannot independently set legal content to **APPROVED** or **ACTIVE**. No live monitoring. No contract generation.

**Subsequent status (2026-09-13, Slice B live migrate + bounded office UAT):** Alembic **`c2d3e4f5a6b7` applied live**. Slice B **CLOSED / OPERATIONAL FOR UAT**. Labeled synthetic UAT source/snapshot/candidate rows exist as update-engine evidence only. This **still does not** populate this register or approve any legal language. Live library packages/objects remain **0**. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**.

**Subsequent status (2026-09-13, Slice C preflight):** [fg-024-slice-c-contract-generation-snapshot-preflight.md](../architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md) **PREFLIGHT COMPLETE**. Product **NOT AUTHORIZED / NOT IMPLEMENTED**. This **still does not** populate this register, approve Family 05 legally, or authorize generation. Empty library remains FAIL CLOSED. ADR-051 §6 remains **deferred**.

**Subsequent status (2026-09-13, Slice C product foundation):** Generation + immutable snapshot exist in the repository (`project_generated_contracts`, `project_contract_snapshots`, `project_contract_snapshot_objects`, `app/services/contract_generation.py`). Alembic **`d3e4f5a6b7c8`** not applied live at that commit. This **still does not** populate this register, approve any legal language, or mark Family 05 legally approved. Synthetic tests only. Empty library remains FAIL CLOSED. ADR-051 §6 remains **deferred**.

**Subsequent status (2026-09-13, Slice C live migrate + bounded office UAT):** Alembic **`d3e4f5a6b7c8` applied live**. Slice C **CLOSED / OPERATIONAL FOR UAT**. Labeled synthetic generated-contract rows exist as engine evidence only (`CTR-2026-0001`, `CTR-2026-0002`). This **still does not** populate this register or approve any legal language. Live library packages/objects remain **0**. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. No real customer contract. ADR-051 §6 remains **deferred**.

## Warranty template register (governed — empty until approved)

Warranty language is **governed content**.

| Rule | Detail |
|------|--------|
| Templates required | Approved/versioned warranty templates must exist **before production use** |
| No invention | The Estimator may not invent or silently alter warranty obligations |
| Contract package | Applicable warranty document **must** attach to the Ontario construction contract package |
| Versioning | Supersede prior approved versions explicitly |

**Register status:** No production warranty templates registered in repository as of 2026-08-25.

## Not this gate — Permit Intelligence / Permit Rules Library

**Status:** Permit Rules Library is a **separate** governed source from this Legal Content Gate. Architecture **Accepted**: [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md). Canonical V1 pin: [permit-rules-library.md](../architecture/permit-rules-library.md). [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT** populated a bounded Ontario / Ottawa coach-house corpus. This gate still does **not** own municipal/provincial zoning or permit rules.

This Legal Content Gate governs **construction contract and warranty templates** (Ontario first; later North American packages under FG-024). It does **not** own municipal/provincial/state zoning, permit, servicing, or AHJ requirement sources. The Permit Rules Library is a **separate** governed source. Permit authority and contract legal-content authority remain independent even when they share Project jurisdiction identity ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)).

[FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) and this Legal Content Gate do **not** authorize:

- jurisdictional rules-library population (that belongs to [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) implementation, not this Legal Content Gate)
- live regulatory AI
- in-product web lookup
- automatic permit approval conclusions
- municipal submissions
- treating permit findings as contract clauses

Do not treat ChatGPT or other tool research as an authoritative permit determination. Preliminary research on the Mike Pratt Coach House reference case is **not** governed legal content. AI cannot mark regulatory content approved.

## Contract and warranty progression states

Shared lifecycle states (see [project-document-package.md](../architecture/project-document-package.md)):

PROPOSED → APPROVED → GENERATED → VERIFIED → SENT FOR SIGNATURE → SIGNED → SUPERSEDED

Generation alone does not mean final or sent.

## Open decisions (Joel / legal)

1. Template storage location and format (repository vs controlled document store)
2. Approval authority for legal template versions
3. Ontario-specific statutory clause set and update process
4. E-signature provider boundary (Future). **Subsequent status (2026-09-01):** Native Signing reconnaissance is **complete** ([contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md)). Recommendation **NATIVE V1**. Counsel process-review specification **PREPARED** ([native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md)) — **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL**. **Development may proceed under separate governance. Production activation / real customer use is blocked pending counsel process approval.** This Legal Content Gate for Contract/Warranty **templates** is **unchanged** and remains in force. Native signing must never bypass approved Contract/Warranty templates or human approval before send. Change Orders are the intended first signing use case. Contract signing remains later and behind this gate.

## Related

- [feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) — North American library / update engine / frozen snapshot / monitoring (**RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / OVERALL OPEN / PARTIAL**; Slice D **NOT AUTHORIZED**)
- [architecture/fg-024-slice-a-legal-content-library-preflight.md](../architecture/fg-024-slice-a-legal-content-library-preflight.md) — Slice A engine freeze; empty library; fail-closed
- [architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md](../architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md) — Slice C generation / snapshot freeze; **PREFLIGHT COMPLETE**; subsequent product **CLOSED / OPERATIONAL FOR UAT**
- [adr/ADR-050-north-american-legal-content-library-ownership.md](../adr/ADR-050-north-american-legal-content-library-ownership.md) — **Accepted** 13 Sep 2026 (library ownership / fail-closed)
- [adr/ADR-051-legal-content-source-and-update-lifecycle.md](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) — **Accepted** 13 Sep 2026 (source classes / candidate-update / Slice B–D boundary; architecture only)
- [legal/native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md) — signing **process** draft for counsel; **not** template approval
- [architecture/project-document-package.md](../architecture/project-document-package.md)
- [architecture/permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) — **FUTURE / NOT IMPLEMENTED**; not this Legal Content Gate
- [platform-governance.md](../platform-governance.md)
- [platform-constitution.md](../platform-constitution.md) — Articles 5, 8, 9

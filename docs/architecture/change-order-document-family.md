# Architecture pin — Change Order document family

| Attribute | Value |
|-----------|--------|
| Status | **FUTURE / NOT IMPLEMENTED** — requirement pin only |
| Date | 2026-08-30 |
| Product | The Estimator / CalibAi |
| Canonical record | This document |
| Related | [organization-brand-profile.md](organization-brand-profile.md) · [project-document-package.md](project-document-package.md) · [modules/projects.md](../modules/projects.md) · [ADR-020](../adr/ADR-020-build-module-boundary.md) · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) |

**Current vs future:** Existing Change Order architecture remains the **authoritative Change Order business record** (`change_orders` / `change_order_items` in [`app/project_controls/`](../../app/project_controls/)). Office list/detail and a live PDF renderer exist today ([`app/project_controls/pdf.py`](../../app/project_controls/pdf.py)). That PDF is **not** the future governed document family described below: it uses a hardcoded Brayman static logo, is office-desktop only, and does not provide Brand Profile snapshot, client email, or field UX. **Do not create a second Change Order entity.** The Permit & Approvals Report is a **core project document**, not a Change Order ([ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)). Nothing below is implemented. This pin does **not** reopen [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) (**CLOSED / OPERATIONAL FOR UAT**). Next governed action is **STOP** (Permit Intelligence architecture Accepted / not implemented) — not this pin.

---

## Purpose

Future CalibAi must provide a standard governed **CHANGE ORDER DOCUMENT** generated from the **existing** Change Order record.

Change Order becomes a **STANDARD PROJECT TRANSACTION DOCUMENT FAMILY**.

A project may contain many:

```text
CO-000001
CO-000002
CO-000003
…
```

Do **not** treat Change Order as one single static project document. Do **not** force Change Order into a numbered “Document #7” of the core package.

---

## This pin does not authorize

- Change Order schema changes
- Change Order PDF renderer rewrite
- email service / automatic sending
- electronic signatures
- Organization Brand Profile schema or logo storage
- document-template engine changes
- new durable fields
- new Change Order statuses merely for document generation
- auth / field-native apps
- Permit Intelligence
- Phase D
- supplier onboarding / BMR / Winchester
- ADR-008 acceptance
- BUILD expansion
- MONITOR / LEARN
- Feature Gate
- ADR
- migration

A later repository-first architecture assessment must govern:

```text
EXISTING CHANGE ORDER
→ DOCUMENT SNAPSHOT
→ EMAIL DELIVERY
→ ACCEPTANCE EVIDENCE
```

This pin does not make that decision.

---

## Authoritative record vs generated document

| Layer | Rule |
|-------|------|
| Business record | Existing `ChangeOrder` / items remain the commercial source of truth |
| Generated document | Snapshot of that record for customer communication |
| Forbidden | A second Change Order entity or a PDF that becomes a competing commercial source of truth |

Preserve the existing lifecycle (`Draft`, `Pending Approval`, `Approved`, `Rejected`, `Invoiced`, `Cancelled` in `CHANGE_ORDER_STATUSES`). Do **not** invent new statuses merely for document generation.

---

## Core package vs transaction-document families

Record this distinction:

| Kind | Role |
|------|------|
| **Core project document / package outputs** | The four-output package in [project-document-package.md](project-document-package.md) (internal breakdown, customer estimate/Proposal, QuickBooks, Ontario contract). Plus additional pinned documents such as the Permit & Approvals Report. |
| **Project transaction document families** | Repeating per-project transactions. Change Orders belong here because a project may have many. |

Future Project Documents UX should be capable of showing both **CORE DOCUMENTS** and **TRANSACTION DOCUMENTS** without creating duplicate authoritative records.

---

## Field / desktop UX (future)

Future UX should allow contractor staff from **desktop**, **tablet**, and **phone / field device** to open a project and choose substantially:

```text
CHANGE ORDERS
→ NEW CHANGE ORDER
```

CalibAi should pre-fill governed facts already known, potentially including:

- organization branding
- contractor / company information
- customer
- project
- project address
- Change Order number
- date
- governing Proposal / Contract reference
- applicable tax treatment
- existing project / commercial references where appropriate

The contractor should need to provide only the smallest project-specific delta.

Potential user inputs (do **not** create durable fields in this pin):

- change description
- reason
- selling price / commercial delta
- schedule impact where applicable
- supporting notes
- attachments / photos where later authorized

Current office Change Order UX is **not** this field/desktop family. Do not implement native field clients under this pin ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md) remains direction only).

---

## Preview and generate

Future workflow should support:

```text
CREATE / EDIT DRAFT
→ PREVIEW CHANGE ORDER
→ GENERATE GOVERNED PDF / DOCUMENT
→ SEND TO CLIENT
```

The generated document must be a **snapshot** of the authoritative Change Order record. It must not become a second commercial source of truth.

---

## Direct client email (future)

Future Change Order UX should support **EMAIL TO CLIENT** directly from CalibAi after **explicit user action**.

Record a requirement for future audit / provenance such as:

- sender / user
- recipient
- Change Order identity
- exact document / version sent
- sent timestamp
- subject
- delivery / message reference where available

Do **not** implement email integration under this pin. Do **not** send messages automatically.

---

## Acceptance / immutability

Preserve existing Change Order lifecycle and governance.

Future accepted / authorized Change Order documents must preserve immutable commercial history consistent with existing Proposal / Change Order governance.

Do **not** silently rewrite accepted Change Orders when:

- organization branding changes
- Estimate changes
- Proposal changes
- pricing policy changes
- document templates change

Brand-at-issue preservation is defined on [organization-brand-profile.md](organization-brand-profile.md). Commercial immutability remains with the existing Change Order record and Proposal Accepted rules ([ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)). BUILD references Change Orders; it does not own them ([ADR-020](../adr/ADR-020-build-module-boundary.md)).

---

## Related current code (do not change under this pin)

- [`app/project_controls/models.py`](../../app/project_controls/models.py)
- [`app/project_controls/services.py`](../../app/project_controls/services.py)
- [`app/project_controls/routes.py`](../../app/project_controls/routes.py)
- [`app/project_controls/pdf.py`](../../app/project_controls/pdf.py)
- [`tests/test_change_orders.py`](../../tests/test_change_orders.py)

---

## Related

- [organization-brand-profile.md](organization-brand-profile.md)
- [project-document-package.md](project-document-package.md)
- [modules/projects.md](../modules/projects.md)
- [ADR-020](../adr/ADR-020-build-module-boundary.md)
- [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)
- [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) — approved Change Order deltas are part of the composed MONITOR baseline; MONITOR is **not implemented**

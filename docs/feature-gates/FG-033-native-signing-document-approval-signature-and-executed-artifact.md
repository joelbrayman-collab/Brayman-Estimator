# Feature Gate FG-033: Native Signing — Document Approval, Customer Signature, Countersignature, Executed Artifact, and Audit

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-033` |
| Feature Name | Native Signing — Document Approval, Customer Signature, Countersignature, Executed Artifact, and Audit |
| Target Milestone | **V1-07.** Not a 12th major V1 package. Does **not** rescore V1. |
| Module | **Signing Service** owns signing requests, frozen signable artifacts, participants, consent versions, signing events, and later executed artifacts. Change Orders remain Project Controls. Generated contracts remain FG-024 / CONTRACT. Native Signing is an **overlay**. |
| Date | 2026-09-14 |
| Status | **OPEN / PARTIAL.** SIGN-A **IMPLEMENTED**. SIGN-B/C/D/E **NOT STARTED**. Production / real-customer signing **BLOCKED** pending Ontario counsel process approval. |
| Architecture | [contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md) **ARCHITECTURE RECONNAISSANCE COMPLETE**. [native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md) **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL**. [change-order-document-family.md](../architecture/change-order-document-family.md) **FUTURE / NOT IMPLEMENTED** (V1 signing freezes the current ReportLab CO PDF). [FG-024](FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **OVERALL OPEN / PARTIAL**. [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted**. [ADR-004](../adr/ADR-004-proposal-acceptance-workflow.md) **Proposed** (Proposal e-sign out of this gate). |
| Related ADRs | No new ADR in SIGN-A. Existing Native Signing recon + counsel spec govern process. [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) / [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** (contract legal content remains separate). |
| Prerequisites | TECH-A/B/C/D **PASS**. Frozen generated-contract DOCX custody live. Change Order business record live. FG-018 office Users / membership. Counsel process review **not** a development hold. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / PARTIAL** |
| SIGN-A | **IMPLEMENTED** — freeze + request engine + audit through APPROVED_FOR_SIGNATURE |
| SIGN-B | **NOT STARTED** |
| SIGN-C | **NOT STARTED** |
| SIGN-D | **NOT STARTED** |
| SIGN-E | **NOT STARTED** |
| Schema / Alembic | Additive **`b7c8d9e0f1a2`** revises **`a6b7c8d9e0f1`**. |
| Production Native Signing | **NOT COMPLETE** |
| V1 scoring | **NOT RESCORED** (**60% / 4 of 11**) |

```text
FG-033:
OPEN / PARTIAL
SIGN-A IMPLEMENTED
SIGN-B / SIGN-C / SIGN-D / SIGN-E NOT STARTED
NO PUBLIC /sign ROUTE
NO CUSTOMER TOKEN
NO EXECUTED PDF
NO TRANSACTIONAL EMAIL
NO LIBREOFFICE CONVERSION
PRODUCTION / REAL CUSTOMER USE BLOCKED PENDING COUNSEL PROCESS APPROVAL
COUNSEL: DEFERRED FOR V1 TECHNICAL DEVELOPMENT
MANDATORY PRE-PRODUCTION GATE
NOT A LEGAL APPROVAL
NOT A COUNSEL PASS
V1 NOT RESCORED
```

---

## Purpose

Provide one complete Native Signing capability: take an immutable governed document through approval-for-signature, secure invitation, customer iPhone ceremony, consent, signature, optional countersignature, executed-artifact custody, and append-only audit.

Change Orders are the first overlay. Generated contracts use the same engine later, remaining production-blocked until Ontario PRODUCTION legal content and counsel process approval.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Brayman internally approved Change Orders and generated contracts can be mistaken for customer-authorized / executed documents. There is no governed signing request, freeze, invitation, ceremony, or executed artifact. |
| 2 | Who is the user? | Office: any **ACTIVE** organization member (no RBAC). Customer: invited signer via secure link (SIGN-B); **no** CalibraytAI account. Not AI. Not a public generate-anyway control. |
| 3 | Which module owns it? | Signing Service (`app/services/signing.py`, `app/models/signing.py`). Overlay only. Does not own Change Order commercial records or generated-contract commercial identity. |
| 4 | What data does it own? | `signing_requests`, `signing_participants`, `signing_events`, `signing_frozen_artifacts`, `signing_consent_versions`, later executed artifacts (SIGN-C). Private `instance/signing_artifacts/`. |
| 5 | What data does it reference? | Organization, User / UserMembership, Client, Project, `ChangeOrder`, `GeneratedProjectContract` / `ProjectContractSnapshot`, Family 05 master SHA, TECH-C DOCX custody. |
| 6 | What may it change? | Signing-owned tables, frozen signing-artifact bytes, SIGN-A CLI, later customer `/sign` (SIGN-B), executed PDF (SIGN-C). May freeze a **copy** of the current CO PDF. Must **not** mutate CO statuses or generated-contract `GENERATED` constraint. |
| 7 | What must it not change? | `CHANGE_ORDER_STATUSES`; EST-2026-0019; PRODUCTION Ontario legal packages; Family 05 master; FG-024 Slice D; Proposal e-sign (ADR-004); Time / MONITOR / LEARN; inventing RBAC; DocuSign/Adobe as source of truth. |
| 8 | What are the acceptance criteria? | Complete workstream: immutable artifact; human APPROVED_FOR_SIGNATURE; secure invite; consent; signature; countersign path; executed custody; audit; CO + synthetic contract E2E; iPhone UAT; production contract signing remains fail-closed. SIGN-A subset: freeze + CREATED → APPROVED_FOR_SIGNATURE + audit only. |
| 9 | What tests are required? | Dedicated SIGN-A identity/tenancy/freeze/approval/AI-block/audit tests; migration upgrade/downgrade; TECH-A/B/C/D and Change Order regressions; full suite. |
| 10 | What documentation must be updated? | This gate; feature-gates README; modules; architecture; current-state; session-handoff; chat-workflow-log; milestones; project-state-report; v1-completion-register (no rescore); Native Signing recon subsequent status. |
| 11 | Does it require an ADR? | **No new ADR for SIGN-A.** Existing recon already recommends NATIVE V1. Schema follows additive org-scoped immutable-artifact pattern. |
| 12 | Does it require a database migration? | **Yes.** One additive SIGN-A revision **`b7c8d9e0f1a2`**. |

---

## Product decisions (Joel / Architect, 14 Sep 2026)

| Decision | V1 rule |
|----------|--------|
| Change Order source | Freeze **current** governed ReportLab PDF once at request creation / APPROVED_FOR_SIGNATURE path. Do **not** wait for the future CO document family. |
| Countersign | Change Order default **`countersign_required = true`**. Flag is explicit. Legal necessity remains a counsel question. |
| Invitation expiry | Default **7 days** (SIGN-B uses this pin). |
| UAT delivery | Office copyable URL is allowed for technical UAT (SIGN-B). Transactional email is required before the **normal real-customer send** workflow is complete. |
| Signature evidence | Technically retain completion **IP** and **basic user-agent** (SIGN-B/C). Counsel still unanswered for production policy. |
| Family 05 PDF | **SIGN-E only:** retained DOCX → pinned LibreOffice/soffice **once** → retain PDF. No ReportLab Family 05 substitute. Missing converter **BLOCK**. |
| Office authorization | Any **ACTIVE** organization member may perform permitted V1 office signing actions. Do **not** invent RBAC. |
| Customer account | **Not required.** |
| Authority | `SYNTHETIC_UAT` vs `PRODUCTION`. Synthetic EXECUTED is technical proof only. |

---

## Complete workstream slices

Later slices are **not** authorized merely because this Feature Gate exists.

### SIGN-A — Freeze + request engine + audit

**Status: IMPLEMENTED (this prompt).**

Office-only. Frozen signable artifact. `SIGN-YYYY-NNNN` identity. Participants foundation. Consent-version foundation. CREATED → APPROVED_FOR_SIGNATURE. HUMAN only. AI/AUTOMATION **BLOCK**. Append-only `REQUEST_CREATED` / `APPROVED_FOR_SIGNATURE`. Tenant isolation.

**STOP:** no `/sign` route, no token, no customer UI, no countersignature, no executed PDF, no email, no iPhone UAT.

### SIGN-B — Secure invitation + customer iPhone ceremony

Secure token (hash-at-rest), public `/sign/*` exemption, review frozen PDF, placeholder consent, SIGN & ACCEPT, CSRF, rate limit, office copyable URL. **NOT STARTED.**

### SIGN-C — Countersign + executed PDF + custody

Office countersign; executed PDF + SHA; downloads; VOID/EXPIRE/DECLINE/RESEND. **NOT STARTED.**

### SIGN-D — Change Order E2E + synthetic / real-iPhone UAT

Hub labels UNSIGNED / AWAITING / SIGNED / EXECUTED. Synthetic CO only. Real iPhone UAT. EST-2026-0019 protected. **NOT STARTED.**

### SIGN-E — Contract attachment + DOCX→PDF + synthetic contract UAT

LibreOffice convert-once. PRODUCTION contract send **BLOCK** without ACTIVE PRODUCTION package + counsel process activation. **NOT STARTED.**

---

## Lifecycle (complete workstream)

```text
CREATED → APPROVED_FOR_SIGNATURE → SENT → SIGNED → EXECUTED
                                    ↘ VOIDED | EXPIRED | DECLINED
```

VIEWED and COUNTERSIGNED are **events**, not statuses. SIGN-A services exercise **CREATED → APPROVED_FOR_SIGNATURE** only.

---

## Counsel / production boundary

```text
NATIVE SIGNING DEVELOPMENT: MAY PROCEED UNDER THIS GATE (bounded slices).
NATIVE SIGNING PRODUCTION ACTIVATION / REAL CUSTOMER USE:
BLOCKED PENDING ONTARIO COUNSEL APPROVAL OF THE SIGNING PROCESS.
NOT A LEGAL APPROVAL.
NOT A COUNSEL PASS.
```

No counsel-review status field is required in SIGN-A development workflow.

---

## Out of this gate / this slice

- Public customer signing (SIGN-B)
- Executed PDF (SIGN-C)
- Time / Project Performance / MONITOR / LEARN
- FG-024 Slice D
- Ontario PRODUCTION legal population
- V1 rescore
- Proposal e-signature
- DocuSign / Adobe as source of truth

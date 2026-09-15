# Feature Gate FG-033: Native Signing — Document Approval, Customer Signature, Countersignature, Executed Artifact, and Audit

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-033` |
| Feature Name | Native Signing — Document Approval, Customer Signature, Countersignature, Executed Artifact, and Audit |
| Target Milestone | **V1-07.** Not a 12th major V1 package. Does **not** rescore V1. |
| Module | **Signing Service** owns signing requests, frozen signable artifacts, participants, consent versions, signing events, and later executed artifacts. Change Orders remain Project Controls. Generated contracts remain FG-024 / CONTRACT. Native Signing is an **overlay**. |
| Date | 2026-09-15 |
| Status | **OPEN / PARTIAL.** SIGN-A **IMPLEMENTED**. SIGN-B **IMPLEMENTED**. SIGN-C **IMPLEMENTED**. SIGN-D **IMPLEMENTED** (automated product / E2E). SIGN-E **NOT STARTED**. Real iPhone UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT** — **NOT CLAIMED AS PASS**. Production / real-customer Native Signing **NOT COMPLETE**. No external-review dependency in the development workflow. |
| Architecture | [contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md) **ARCHITECTURE RECONNAISSANCE COMPLETE**. [native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md) **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL**. [change-order-document-family.md](../architecture/change-order-document-family.md) **FUTURE / NOT IMPLEMENTED** (V1 signing freezes the current ReportLab CO PDF). [FG-024](FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **OVERALL OPEN / PARTIAL**. [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted**. [ADR-004](../adr/ADR-004-proposal-acceptance-workflow.md) **Proposed** (Proposal e-sign out of this gate). |
| Related ADRs | No new ADR in SIGN-A, SIGN-B, SIGN-C, or SIGN-D. Existing Native Signing recon remains architecture. [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) / [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** (contract legal content remains separate). |
| Prerequisites | TECH-A/B/C/D **PASS**. Frozen generated-contract DOCX custody live. Change Order business record live. FG-018 office Users / membership. Development proceeds on product/software requirements. Do **not** add legal-review gates or approval states. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / PARTIAL** |
| SIGN-A | **IMPLEMENTED** — freeze + request engine + audit through APPROVED_FOR_SIGNATURE |
| SIGN-B | **IMPLEMENTED** — secure invitation + public `/sign` + iPhone-first customer ceremony through SIGNED |
| SIGN-C | **IMPLEMENTED** — countersign + executed PDF custody + VOID/EXPIRE/DECLINE/RESEND |
| SIGN-D | **IMPLEMENTED** — Change Order E2E + office/Hub + automated mobile UX. Real iPhone UAT **DEFERRED** (not PASS) |
| SIGN-E | **NOT STARTED** |
| Schema / Alembic | Additive SIGN-A **`b7c8d9e0f1a2`**. Additive SIGN-B **`c8d9e0f1a2b3`**. Additive SIGN-C **`d9e0f1a2b3c4`** revises **`c8d9e0f1a2b3`**. Live current **equals** repository head. |
| Production Native Signing | **NOT COMPLETE** |
| V1 scoring | **NOT RESCORED** (**60% / 4 of 11**) |

```text
FG-033:
OPEN / PARTIAL
SIGN-A IMPLEMENTED
SIGN-B IMPLEMENTED
SIGN-C IMPLEMENTED
SIGN-D IMPLEMENTED (AUTOMATED)
SIGN-E NOT STARTED
REAL IPHONE UAT DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT
NOT CLAIMED AS PASS
PUBLIC /sign ROUTE NARROWLY EXEMPTED
TOKEN HASH-AT-REST
NO CUSTOMER ACCOUNT
EXECUTED PDF IN PRIVATE CUSTODY
NO TRANSACTIONAL EMAIL
NO LIBREOFFICE CONVERSION
NO EXTERNAL-REVIEW DEPENDENCY
NOT A LEGAL APPROVAL
NOT EXTERNALLY REVIEWED
V1 NOT RESCORED
```

---

## Purpose

Provide one complete Native Signing capability: take an immutable governed document through approval-for-signature, secure invitation, customer iPhone ceremony, consent, signature, optional countersignature, executed-artifact custody, and append-only audit.

Change Orders are the first overlay. Generated contracts use the same engine later, remaining production-incomplete until Ontario PRODUCTION legal content and remaining SIGN slices.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Brayman internally approved Change Orders and generated contracts can be mistaken for customer-authorized / executed documents. There is no governed signing request, freeze, invitation, ceremony, or executed artifact. |
| 2 | Who is the user? | Office: any **ACTIVE** organization member (no RBAC). Customer: invited signer via secure link (SIGN-B); **no** CalibraytAI account. Not AI. Not a public generate-anyway control. |
| 3 | Which module owns it? | Signing Service (`app/services/signing.py`, `app/models/signing.py`). Overlay only. Does not own Change Order commercial records or generated-contract commercial identity. |
| 4 | What data does it own? | `signing_requests`, `signing_participants`, `signing_events`, `signing_frozen_artifacts`, `signing_consent_versions`, `signing_token_access_attempts` (SIGN-B), `signing_executed_artifacts` (SIGN-C). Private `instance/signing_artifacts/`. |
| 5 | What data does it reference? | Organization, User / UserMembership, Client, Project, `ChangeOrder`, `GeneratedProjectContract` / `ProjectContractSnapshot`, Family 05 master SHA, TECH-C DOCX custody. |
| 6 | What may it change? | Signing-owned tables, frozen and executed signing-artifact bytes, SIGN-A/B/C CLI, public `/sign` (SIGN-B/C), office `/signing-requests/<id>/executed`. May freeze a **copy** of the current CO PDF. Must **not** mutate CO statuses or generated-contract `GENERATED` constraint. |
| 7 | What must it not change? | `CHANGE_ORDER_STATUSES`; EST-2026-0019; PRODUCTION Ontario legal packages; Family 05 master; FG-024 Slice D; Proposal e-sign (ADR-004); Time / MONITOR / LEARN; inventing RBAC; DocuSign/Adobe as source of truth. |
| 8 | What are the acceptance criteria? | Complete workstream: immutable artifact; human APPROVED_FOR_SIGNATURE; secure invite; consent; signature; countersign path; executed custody; audit; CO + synthetic contract E2E; iPhone UAT; production contract signing remains fail-closed. SIGN-A subset: freeze + CREATED → APPROVED_FOR_SIGNATURE + audit. SIGN-B subset: invitation + public ceremony through SIGNED. SIGN-C subset: countersign / no-countersign execute + executed PDF custody + VOID/EXPIRE/DECLINE/RESEND. SIGN-D subset: Change Order E2E + office/Hub + automated mobile UX. Real iPhone UAT is **deferred** (Joel / Architect 15 Sep 2026) and is **not** claimed as PASS. |
| 9 | What tests are required? | Dedicated SIGN-A, SIGN-B, SIGN-C, and SIGN-D identity/tenancy/token/ceremony/custody/mobile-UX tests; migration upgrade/downgrade; TECH-A/B/C/D and Change Order regressions; full suite. |
| 10 | What documentation must be updated? | This gate; feature-gates README; modules; architecture; current-state; session-handoff; chat-workflow-log; milestones; project-state-report; v1-completion-register (no rescore); Native Signing recon subsequent status. |
| 11 | Does it require an ADR? | **No new ADR for SIGN-A, SIGN-B, SIGN-C, or SIGN-D.** Existing recon already recommends NATIVE V1. Schema follows additive org-scoped immutable-artifact pattern. |
| 12 | Does it require a database migration? | **Yes.** SIGN-A **`b7c8d9e0f1a2`**. SIGN-B additive **`c8d9e0f1a2b3`**. SIGN-C additive **`d9e0f1a2b3c4`**. |

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

**Status: IMPLEMENTED (this prompt).**

Secure token (hash-at-rest), public `/sign/*` exemption, review frozen PDF, placeholder consent, typed-name SIGN & ACCEPT, CSRF, rate limit, office copyable URL. No customer account. Stops at SIGNED. Countersign and EXECUTED remain SIGN-C. Real iPhone close remains SIGN-D. Transactional email is outside SIGN-B close.

### SIGN-C — Countersign + executed PDF + custody

**Status: IMPLEMENTED (this prompt).**

Office HUMAN countersign for SIGNED + `countersign_required=true` (any ACTIVE org member; AI/AUTOMATION BLOCK). No-countersign path assembles EXECUTED without a second ceremony. Executed PDF = immutable pre-sign PDF + completion/audit page (pypdf). Distinct private artifact. SHA-256 of retained bytes. SIGNED → EXECUTED only after custody succeeds. VOID / EXPIRE / DECLINE / RESEND. Customer completed-link executed download. Smallest office `/signing-requests/<id>/executed`. Token unusable for SIGN & ACCEPT after EXECUTED/VOIDED/EXPIRED/DECLINED. RESEND rotates the SENT token.

**STOP:** no SIGN-D Hub polish, no real iPhone UAT close, no transactional email, no LibreOffice / SIGN-E.

### SIGN-D — Change Order E2E + automated product validation

**Status: IMPLEMENTED (this prompt). Automated product / E2E validation COMPLETE.**

Hub labels UNSIGNED / AWAITING SIGNATURE / SIGNED / EXECUTED. Office Send for Signature. Customer mobile ceremony (name-first copy). Countersign + no-countersign EXECUTED. Lifecycle fail-closed. Tenant isolation. Synthetic CO only. EST-2026-0019 protected.

```text
REAL IPHONE UAT:
DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT.
NOT CLAIMED AS PASS.
```

A later real-device defect is normal governed corrective work. It does **not** reopen SIGN-D unless a defect is actually found.

**STOP:** no SIGN-E, no LibreOffice, no transactional email, no V1 rescore.

### SIGN-E — Contract attachment + DOCX→PDF + synthetic contract UAT

LibreOffice convert-once. PRODUCTION contract send **BLOCK** without ACTIVE PRODUCTION package. **NOT STARTED.**

---

## Lifecycle (complete workstream)

```text
CREATED → APPROVED_FOR_SIGNATURE → SENT → SIGNED → EXECUTED
                                    ↘ VOIDED | EXPIRED | DECLINED
```

VIEWED and COUNTERSIGNED are **events**, not statuses. SIGN-B services exercise **CREATED → APPROVED_FOR_SIGNATURE → SENT → SIGNED**. SIGN-C services exercise **SIGNED → EXECUTED** (with or without COUNTERSIGNED) plus VOIDED / EXPIRED / DECLINED / RESENT.

---

## Production boundary

```text
NATIVE SIGNING DEVELOPMENT: MAY PROCEED UNDER THIS GATE (bounded slices).
NO EXTERNAL-REVIEW DEPENDENCY IN THE DEVELOPMENT WORKFLOW.
DO NOT ADD LEGAL-REVIEW GATES OR APPROVAL STATES.
DO NOT REPRESENT ANYTHING AS EXTERNALLY REVIEWED UNLESS IT ACTUALLY IS.
NATIVE SIGNING PRODUCTION / REAL CUSTOMER USE: NOT COMPLETE
UNTIL REMAINING SLICES AND PRODUCT REQUIREMENTS ARE SATISFIED.
NOT A LEGAL APPROVAL.
```

No counsel-review status field is required in the SIGN-A/SIGN-B development workflow.

---

## Out of this slice (SIGN-B)

- Countersignature / executed PDF (SIGN-C)
- Real iPhone UAT close (SIGN-D)
- Contract PDF conversion (SIGN-E)
- Time / Project Performance / MONITOR / LEARN
- FG-024 Slice D
- Ontario PRODUCTION legal population
- V1 rescore
- Proposal e-signature
- DocuSign / Adobe as source of truth

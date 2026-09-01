# Architecture reconnaissance — Contract, e-signature, and signed Change Orders

| Attribute | Value |
|-----------|--------|
| Status | **ARCHITECTURE RECONNAISSANCE COMPLETE / NOT IMPLEMENTED.** Recommendation **NATIVE V1**. Counsel process-review specification **PREPARED**. **Development may proceed under separate governance. Production activation / real customer use is blocked pending Ontario counsel approval of the signing process.** No Native Signing Feature Gate in this pass. No ADR. No product code. |
| Date | 2026-08-31 (recon); **2026-09-01** (counsel specification prepared) |
| Product | The Estimator / CalibAi |
| Canonical architecture | This document |
| Counsel-facing process spec | [native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md) — **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL / NOT IMPLEMENTED** |
| Related | [change-order-document-family.md](change-order-document-family.md) · [project-document-package.md](project-document-package.md) · [legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [ADR-004](../adr/ADR-004-proposal-acceptance-workflow.md) **Proposed** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [modules/projects.md](../modules/projects.md) · [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted** |

This reconnaissance is **complete** as architecture. The counsel-facing signing-process specification is **prepared**. Neither document authorizes implementation, a Feature Gate, an ADR, a migration, email, a signing UI, DocuSign, Adobe Acrobat Sign, or Ontario contract/warranty template authoring.

Commercial-execution architecture may proceed **in parallel** with BUILD / Field Web governance. Counsel review of the Native Signing **process** is **not** a general development hold.

```text
NATIVE SIGNING DEVELOPMENT:
MAY PROCEED UNDER SEPARATE GOVERNANCE

NATIVE SIGNING PRODUCTION ACTIVATION / REAL CUSTOMER USE:
BLOCKED PENDING ONTARIO COUNSEL APPROVAL OF THE SIGNING PROCESS
```

Separately governed Native Signing architecture, Feature Gate drafting, implementation, testing, and non-production UAT may proceed when Joel authorizes that track. Do **not** enable real customer / commercial signing until counsel decisions are reconciled and approved. The Legal Content Gate for Ontario Contract / Warranty templates remains **separate** and in force.

Field Web remains separately governed. Parallel does **not** mean this document authorizes signing product code.

**Delta (2026-08-31):** Joel requires CalibAi to evaluate whether electronic signing can be implemented **natively** inside CalibAi rather than requiring a DocuSign or Adobe Acrobat Sign subscription. A third-party provider is **not** assumed.

---

## Purpose

Establish architecture for **commercial authorization** of frozen customer documents:

- signed **Change Orders** (strongest early use case)
- signed **Ontario Contract + Warranty** packages (later; Legal Content Gate still owns templates)

Objectives:

- simple customer experience
- strong commercial authorization
- reliable signed Change Orders and Contracts
- no unnecessary recurring third-party subscription
- provider independence
- defensible document/signing provenance

---

## Governed principle

```text
A SIGNING PROVIDER IS NOT THE COMMERCIAL SOURCE OF TRUTH.
```

CalibAi owns:

| Concern | Owner |
|---------|--------|
| Exact document / package version | CalibAi (document snapshot bytes + SHA) |
| Commercial record | Existing owning module (`ChangeOrder`; future contract package record) |
| Document status | CalibAi |
| Signing request | CalibAi Signing Service |
| Signed completion status | CalibAi Signing Service |
| Signed artifact | CalibAi private custody |
| Project association | `projects` |
| Provenance | CalibAi Signing Record |

The signing **mechanism** (native ceremony, or a later DocuSign/Adobe adapter) only establishes **customer intent / authorization** against that exact frozen document.

Do **not** create a second Change Order entity. Do **not** let a PDF or a vendor envelope become a competing commercial record.

---

## Current vs intended

| Layer | Current (code) | Intended (this recon) |
|-------|----------------|------------------------|
| Change Order business record | `change_orders` / `change_order_items` in `app/project_controls/` | Unchanged authority |
| Office CO statuses | `Draft`, `Pending Approval`, `Approved`, `Rejected`, `Invoiced`, `Cancelled` | **Keep.** Do not replace with a vendor envelope status |
| CO PDF | Live renderer `app/project_controls/pdf.py` (office; hardcoded logo) | Future **frozen snapshot** PDF before any send-for-signature ([change-order-document-family.md](change-order-document-family.md)) |
| Email | **Not implemented** | Transactional mail for signing links only (future gate) |
| E-signature | **Not implemented** | Signing Service + Native adapter as V1 candidate |
| Ontario Contract + Warranty | **Not implemented**; register empty | Same Signing Service after Legal Content Gate template approval |
| Proposal e-sign | ADR-004 **Proposed**; out of this recon | Do not expand this recon onto Proposal acceptance |

---

## Three architecture choices (not selected as product yet)

Evaluate **A, B, and C**. Do not implement any.

### A. CalibAi Native Signing

CalibAi conducts the signing ceremony on a CalibAi HTTPS page against a CalibAi-frozen PDF. CalibAi stores the Signing Record and artifacts. A transactional mail provider delivers the link. No DocuSign/Adobe subscription is required for V1.

### B. DocuSign adapter

CalibAi still freezes the document and owns the commercial record. CalibAi calls DocuSign (or equivalent TSP) to collect the signature, then **imports** completion status + signed artifact. Vendor is a mechanism, not the source of truth.

### C. Adobe Acrobat Sign adapter

Same as B with Adobe Acrobat Sign as the mechanism.

**Rule:** even if A is chosen for V1, B and C remain **future adapters** behind the same Signing Service. Do **not** couple Change Order / Contract business logic to the native web UI.

Recommended abstraction (do **not** over-engineer unused adapters in a first gate):

```text
SigningService
  ├── NativeSigningAdapter     [V1 candidate]
  ├── DocuSignAdapter          [future]
  └── AdobeSignAdapter         [future]
```

A first Feature Gate may implement `SigningService` + `NativeSigningAdapter` only. Adapter interfaces exist so a later gate can add B/C without rewriting CO/Contract ownership.

---

## Native signing ceremony (conceptual V1)

Minimum defensible flow. **Not implemented.**

1. Brayman generates / finalizes a governed Change Order or Contract PDF snapshot.
2. Authenticated Brayman user explicitly **Approves for Signature**.
3. CalibAi freezes exact document bytes/version. Record SHA-256 of the **pre-sign** PDF.
4. CalibAi creates a secure cryptographically random signing request (store **hash** of the token, not the token).
5. Customer receives a unique signing link at a **governed recipient email**.
6. Link has bounded expiry and may be revoked / voided.
7. Customer opens the **exact frozen document**.
8. Customer can review and download the document **before** signing.
9. CalibAi displays explicit electronic-signature **consent / intent** language (versioned text).
10. Customer identifies / confirms signer (typed legal name matching the invitation, with an explicit mismatch warning — product rule later).
11. Customer may optionally apply a typed or drawn **graphical** signature as presentation only.
12. Customer explicitly presses **SIGN & ACCEPT**.
13. CalibAi records completion (Signing Record immutable after complete).
14. CalibAi generates / preserves the completed signed document and audit record.
15. The signing link **cannot** be reused to alter the completed transaction (idempotent; further SIGN → fail closed).

A regenerated or modified PDF **must not** inherit a prior signature.

```text
DOCUMENT CHANGE AFTER SEND
→ VOID / SUPERSEDE the signing request
→ new frozen bytes
→ new signing request
```

---

## Document integrity (must bind one frozen document)

Record at minimum:

| Field | Role |
|-------|------|
| source document / record ID | Existing CO id or future contract-package id |
| source version | Snapshot / document version identity |
| SHA-256 of exact **pre-sign** PDF/package | Tamper detection of what was offered |
| generated_at | When the frozen bytes were produced |
| approved_by | Authenticated Brayman user who Approved for Signature |
| sent_by | Authenticated sender (may equal approved_by) |
| signer name (invited) | Who was asked to sign |
| signer email | Governed recipient |
| signing_request_id | CalibAi identity |
| signed_at UTC | Completion instant |
| SHA-256 of **completed** document | Tamper detection of the signed artifact |
| signing state | See Signing Record |
| consent text version | Exact language shown |

Do **not** copy a completed signature onto a later regeneration.

---

## Signer assurance recommendation

**Recommended V1 assurance** for Brayman residential / construction commercial transactions (Change Orders first):

| Control | V1 |
|---------|----|
| Unique high-entropy signing link | **MUST** |
| Governed recipient email | **MUST** |
| Bounded expiry | **MUST** |
| One-time completion | **MUST** |
| Signer name confirmation | **MUST** |
| Explicit intent to sign (SIGN & ACCEPT + consent text) | **MUST** |
| HTTPS for the ceremony | **MUST** (production) |
| SMS / MFA | **NOT** in V1 |
| Identity-document verification | **NOT** in V1 |
| Biometrics | **NOT** in V1 |

**Rationale:** This is a **simple electronic signature** ceremony: the invited inbox, the unique secret link, the frozen document, the named person, and an explicit act of acceptance. That matches typical Brayman Change Order authorization (homeowner / client authorizing a priced change) without turning CalibAi into an identity-proofing product.

Do **not** automatically add SMS, MFA, ID scan, or biometrics because commercial TSPs offer them. Add a second factor only if **Ontario counsel** says this transaction class requires it.

**To be verified by counsel:** whether any Brayman document class (for example some consumer home-renovation contracts, or documents with statutory form requirements) is an **exception** that cannot use this assurance level or cannot use electronic form at all.

---

## Signature representation recommendation

Do **not** confuse a **graphical** signature with the authoritative signing event.

The system record tying **person + intent + exact document + completion** is the legal/commercial event.

| Option | V1 role |
|--------|---------|
| A. Drawn signature image | Optional presentation; **not** the authority |
| B. Typed / adopted signature | Optional presentation (typed name rendered in a signature font) |
| C. Explicit click-to-sign plus typed name | **Recommended V1 authority** |
| D. Other | Qualified/advanced certificates, IDV — **not V1** |

**Recommended simplest customer-friendly V1:** **C**.

The customer:

1. reviews/downloads the frozen PDF
2. confirms their name
3. accepts versioned consent/intent language
4. presses **SIGN & ACCEPT**

A drawn or typed glyph may be **embedded on the completion page / PDF signature block** for human familiarity. It is a **rendition of the event**, not a substitute for the Signing Record.

---

## Signing Record (durable)

Intended fields. Apply **data minimization**. Do **not** collect unnecessary personal information.

| Field | Include in V1? |
|-------|----------------|
| `signing_request_id` | Yes |
| Organization | Yes (`organization_id`) |
| Project | Yes |
| Document family (`CHANGE_ORDER` / later `CONTRACT_PACKAGE`) | Yes |
| Source record id | Yes |
| Source document version | Yes |
| Pre-sign document SHA-256 | Yes |
| Recipient name | Yes |
| Recipient email | Yes |
| request `created_at` | Yes |
| `sent_at` | Yes |
| `opened_at` | Optional; useful; not required for validity |
| consent accepted_at | Yes (may equal `signed_at`) |
| `signed_at` | Yes |
| signer-entered name | Yes |
| signature representation reference (optional image/object id) | Optional |
| IP address of signing completion | **Yes, completion event only** — proportionate audit, not tracking |
| user-agent of signing completion | **Yes, completion event only** |
| status | Yes |
| `voided_at` / `voided_by` | Yes |
| completed-document SHA-256 | Yes |
| audit-certificate / consent-text version | Yes |
| Device fingerprint | **No** |
| Geolocation | **No** |
| Biometrics | **No** |
| Identity documents | **No** |

Statuses (signing request, **not** a replacement of `CHANGE_ORDER_STATUSES`):

```text
CREATED → APPROVED_FOR_SIGNATURE → SENT → OPENED? → SIGNED
                                    ↘ EXPIRED
                                    ↘ VOIDED
```

After `SIGNED`, the record is immutable except for authorized void metadata that cannot resurrect the token.

---

## Privacy / data minimization

CalibAi needs only enough to prove:

- who was invited
- which exact document they were shown
- that they consented and completed
- when, from which network/user-agent at completion

PIPEDA-style minimization: do **not** copy TSP “forensic” packs (continuous location, device graphs, ID selfies) into V1.

Office users already exist under [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md). Customers signing are **not** office Users in V1. They are signing-request recipients. Do **not** invent customer login, RBAC, or org-switcher to support native signing.

---

## Signed PDF / completion certificate

Preserve **three** artifacts separately:

```text
PRE-SIGN PDF          (frozen bytes offered)
FINAL SIGNED PDF      (pre-sign + signature block / completion page)
SIGNING RECORD        (authoritative event)
```

Conceptual composition of the final PDF:

```text
ORIGINAL FROZEN PDF
+ signature representation / completion block
+ CalibAi signing certificate / audit page
→ FINAL SIGNED PDF
```

**PDF cryptographic signing (PAdES / PKCS#7 certificates) for V1:** **not required by this architecture** if application-level SHA-256 of pre-sign and completed PDFs plus an immutable Signing Record are retained, and the completed PDF embeds the request id + hashes.

**Legal counsel determination required:** whether Ontario / consumer / construction practice for Brayman documents requires a cryptographically signed PDF (certificate-based) rather than application-level hashing. This recon does **not** claim cryptographic PDF signatures are unnecessary in law. It claims they are **not a product prerequisite** to design Native V1.

If counsel requires certificate-based PDF signatures, options later: add a certificate-signing increment to Native, **or** use a TSP adapter for that document class only.

---

## Email dependency

Native signing needs **delivery**, not a signing vendor.

Minimum capability:

| Message | Purpose |
|---------|---------|
| Send signing link | Invite |
| Resend | Same request, new send timestamp; same token policy (or rotated token — later FG) |
| Signed confirmation | To customer and/or office |
| Completed document | Link (authenticated) or attachment |

**Recommendation:** use a **transactional mail provider** (organization-owned credentials). Do **not** build CalibAi SMTP infrastructure in V1.

Email is **not** a reason to choose DocuSign. DocuSign’s value is a mature signing ceremony and vendor audit pack — not mail itself.

Do **not** implement mail in this recon.

---

## Security (Native V1 MUST list)

| Control | V1 |
|---------|----|
| Cryptographically random signing tokens | **MUST** |
| Hashed token storage (never store the raw token at rest) | **MUST** |
| Token expiry | **MUST** |
| One-time completion | **MUST** |
| Revoke / void | **MUST** |
| CSRF on the SIGN & ACCEPT POST | **MUST** |
| Rate limiting on token presentation | **MUST** |
| Replay protection / idempotent SIGN | **MUST** |
| HTTPS | **MUST** in production |
| No token leakage in logs, URLs in office UI, or analytics | **MUST** |
| Signed-file access control (org/project, like other private custody) | **MUST** |
| Tamper detection via SHA-256 of both PDFs | **MUST** |
| Backups include Signing Records + both PDFs | **MUST** |
| Cross-org 404 fail-closed | **MUST** (same pattern as FG-018/FG-019) |

---

## Change Order native-signing fit

**Yes — strongest early use case.** Native signing can overlay the **existing** Change Order:

```text
CHANGE ORDER (existing record)
→ READY FOR SIGNATURE     (frozen PDF + Approve for Signature)
→ SENT
→ VIEWED                  (optional opened_at)
→ SIGNED
→ EFFECTIVE               (product rule: office commercial approval + customer SIGNED)
```

Attach the exact signed PDF to the **existing** Change Order. Do **not** create a replacement entity.

Existing office statuses remain (`Draft` / `Pending Approval` / `Approved` / …). Do **not** modify that status model in this recon. Customer signing is a **separate** Signing Request machine.

```text
BRAYMAN APPROVED
is NOT the same as
CUSTOMER SIGNED.
```

Do **not** collapse them. Do **not** invent an unsigned-work bypass (work must not proceed as if signed because an office user Approved the commercial record).

The future product must clearly distinguish these Hub/presentation labels, derived from the signing request (not new `CHANGE_ORDER_STATUSES`):

| Hub label | Meaning |
|-----------|---------|
| **UNSIGNED** | No completed signing request for the current frozen document |
| **AWAITING SIGNATURE** | Request SENT or OPENED, not SIGNED, not VOIDED/EXPIRED |
| **SIGNED** | Completed signing request; signed PDF attached |

This recon does **not** rewrite Hub UX. A later Feature Gate must keep Change Orders clearly separate from BUILD Field Observations.

Prerequisite (already pinned, still **not implemented**): governed CO **document snapshot** distinct from today’s live `pdf.py` renderer ([change-order-document-family.md](change-order-document-family.md)). You cannot lawfully bind a signature to a PDF that is regenerated from live fields on each download.

---

## Contract native-signing fit

**Yes, later, same Signing Service.**

Ontario Contract + Warranty may use the same ceremony **after**:

- Legal Content Gate template **APPROVED**
- generated from an **APPROVED** estimate ([project-document-package.md](project-document-package.md) output 4)
- verified against that estimate/version

Native signing does **not** make the Ontario Contract legally ready.

Native signing **must never** bypass:

- an **approved** Ontario Contract template
- an **approved** Warranty
- **human approval before send**
- [legal-content-and-templates.md](../governance/legal-content-and-templates.md)

Do **not** author contract/warranty text. Do **not** mark legal templates APPROVED. Contract/warranty legal-template approval remains a **separate** gate from signing-process review.

---

## Native vs DocuSign / Adobe (qualitative)

Vendor list prices are **not** recorded here. A separate authorized public-web / provider research pass is required if Joel wants dollar comparison.

| Concern | Native V1 | Third-party V1 (B or C) |
|---------|-----------|-------------------------|
| Development effort | Higher in CalibAi (ceremony, tokens, PDF completion page, mail) | Lower ceremony; higher integration (API, webhooks, envelope mapping, failure modes) |
| Security ownership | CalibAi owns token + artifact security | Shared: vendor + CalibAi still must freeze docs and import artifacts correctly |
| Mail | Still required (transactional provider) | Vendor often sends mail; CalibAi still needs status sync |
| Operating cost | Mail + hosting; no per-envelope signing SaaS | Recurring subscription / envelope fees (**amounts To be verified**) |
| Maintenance | Ceremony + PDF + mail + audit | Vendor API churn, webhook auth, envelope/version drift |
| Customer simplicity | Stay on CalibAi-branded page; no second product login | Familiar TSP UX; hand-off off-site |
| CalibAi integration | Direct: same Project, same CO, same SHA | Must map vendor envelope ↔ CalibAi source version without losing SoR |
| Provider independence | High | Vendor lock-in for the ceremony; SoR can still stay in CalibAi if designed correctly |
| Mature audit pack | CalibAi-designed; counsel must accept | Vendor certificate packs are familiar to some counterparties/lenders |

**Architecture conclusion:** a third-party TSP is **optional**, not required, if Native V1 plus counsel review of the **process** is accepted.

---

## Legal-review gate (signing PROCESS)

Do **not** claim native signing is legally sufficient for every Brayman document without counsel review.

This is review of the **signing process**, not approval of contract/warranty **templates**.

**Subsequent status (2026-09-01):** Counsel-facing specification **PREPARED** at [native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md). **DRAFT FOR ONTARIO COUNSEL REVIEW.** **NOT LEGAL APPROVAL.** **NOT IMPLEMENTED.** Change Orders are the intended first use case. Contract signing remains later and behind the Legal Content Gate.

Give counsel that document. Do not treat it as approval.

Counsel should consider, without this document pretending to be legal advice:

- Ontario *Electronic Commerce Act, 2000* (electronic signatures; reliability / association with the document)
- Privacy (PIPEDA / applicable provincial rules) and data minimization
- *Consumer Protection Act, 2002* home-renovation / cooling-off issues where they apply
- *Construction Act* or other statutory form requirements, if any, for specific instruments

**Flag:** whether application-level hashing is sufficient vs certificate-based PDF signatures is a **counsel determination**.

---

## Recommendation

```text
NATIVE V1
subject to Ontario counsel review of the signing PROCESS
before any Feature Gate implementation
```

Not **THIRD-PARTY V1**. Not **FURTHER RESEARCH REQUIRED** for product architecture.

Optional later research (not blocking this recon):

- current DocuSign / Adobe envelope pricing (authorized public-web pass)
- whether any lender, insurer, or AHJ counterparties will reject a CalibAi-native audit pack

Preserve DocuSign / Adobe as **future adapters**.

---

## Explicit non-goals of this recon

- Implementation, Feature Gate, ADR, migration
- Field Web, MONITOR, BUILD expansion, Project Closeout
- Proposal e-signature (ADR-004 remains Proposed; out of scope)
- Authoring Ontario contract/warranty templates
- Accepting ADR-008 or ADR-010
- Customer accounts, tokens/API keys, RBAC, org-switcher, SaaS billing
- SMS, MFA, IDV, biometrics
- Building SMTP
- Replacing `ChangeOrder` or inventing a second CO entity

---

## Related current code (do not change under this recon)

- [`app/project_controls/models.py`](../../app/project_controls/models.py)
- [`app/project_controls/pdf.py`](../../app/project_controls/pdf.py)
- [`app/project_controls/services.py`](../../app/project_controls/services.py)
- [`app/project_controls/routes.py`](../../app/project_controls/routes.py)

---

## Related

- [change-order-document-family.md](change-order-document-family.md)
- [project-document-package.md](project-document-package.md)
- [legal/native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md) — **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL / NOT IMPLEMENTED**
- [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md)
- [organization-brand-profile.md](organization-brand-profile.md)
- [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)
- [ADR-004](../adr/ADR-004-proposal-acceptance-workflow.md) **Proposed**
- [ADR-020](../adr/ADR-020-build-module-boundary.md)
- [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md)

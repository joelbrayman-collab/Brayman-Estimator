# BRAYMAN CONSTRUCTION INC.
# CALIBAI NATIVE ELECTRONIC SIGNING
# CHANGE ORDER PROCESS — COUNSEL REVIEW SPECIFICATION

| Attribute | Value |
|-----------|--------|
| Status | **DRAFT FOR ONTARIO COUNSEL REVIEW.** **NOT LEGAL APPROVAL.** **NOT IMPLEMENTED.** |
| Date | 2026-09-01 |
| Company | Brayman Construction Inc. |
| Product | CalibAi (The Estimator) |
| Scope | Proposed **electronic signing process** for **Change Orders** (V1) |
| Canonical architecture (internal) | [contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md) |
| Legal Content Gate (templates) | [legal-content-and-templates.md](../governance/legal-content-and-templates.md) — **separate**; this document does **not** approve Contract or Warranty text |

---

## Status for counsel

This specification is a **proposed process** for legal review.

It is **not**:

- legal advice
- counsel approval
- software implementation
- a Feature Gate
- approval of Ontario construction contract or warranty templates

Counsel is asked to determine whether this process is appropriate for Brayman’s Ontario **Change Orders**, and to identify required changes.

Counsel is **not** asked to design CalibAi, redesign the Change Order workflow, review the whole platform, select DocuSign or Adobe Acrobat Sign, draft the construction contract, or review BUILD.

---

## 1. Commercial problem

Brayman has experienced commercial risk where Change Order work proceeded without clear **signed customer authorization**.

CalibAi’s objective is to make this distinction unmistakable:

```text
BRAYMAN INTERNALLY APPROVED
is not
CUSTOMER SIGNED / AUTHORIZED
```

The future product should reduce the chance that unsigned Change Order work is mistaken for customer-authorized work.

There is **no** proposed “unsigned work emergency bypass.” Any exception policy would require a later separate decision by Joel Brayman and would not be invented here.

---

## 2. What is being signed

The existing **Change Order** remains the commercial Change Order.

Signing does **not** create a second Change Order. It overlays customer authorization onto the existing record.

Internal office lifecycle (today: Draft, Pending Approval, Approved, Rejected, Invoiced, Cancelled) remains a **Brayman operational** status.

Customer signature is a **separate** authorization state.

Future product labels for customer-signature state (not a replacement of the internal lifecycle):

| Label | Meaning |
|-------|---------|
| **UNSIGNED** | No completed customer signature on the current frozen Change Order document |
| **AWAITING SIGNATURE** | A signing request has been sent and is not completed, expired, voided, or declined |
| **SIGNED** | Customer completed the signing ceremony against that exact frozen document |

```text
BRAYMAN APPROVED ≠ CUSTOMER SIGNED.
```

Work must not proceed as if the customer authorized the Change Order merely because Brayman internally approved it.

---

## 3. Proposed customer signing ceremony (for review)

This is the proposed V1 process. Counsel has **not** approved it.

1. Brayman prepares the Change Order (scope, price, items).
2. Brayman completes internal review/approval.
3. CalibAi generates and **freezes** the exact Change Order PDF that will be signed.
4. A SHA-256 hash of those exact pre-sign PDF bytes is recorded.
5. An authenticated Brayman user explicitly chooses **SEND FOR SIGNATURE**.
6. CalibAi creates a cryptographically random signing request (secret token).
7. Only the **hash** of the token is stored (the secret itself is not kept at rest).
8. The request is associated with: organization, project, Change Order, frozen document, recipient name, recipient email.
9. The customer receives a unique signing link at a **governed recipient email**.
10. The link expires after a governed period.
11. The link may be revoked/voided before completion.
12. The customer opens the **exact frozen** Change Order.
13. The customer can review and download it **before** signing.
14. CalibAi displays **counsel-approved** electronic-signature consent / intention text (versioned; wording not invented here).
15. The customer confirms the signer name.
16. The customer explicitly activates **SIGN & ACCEPT**.
17. The typed/adopted signer name is recorded.
18. An optional visual “signature” glyph may appear for familiarity. It is **not** the authoritative signing event.
19. CalibAi records successful completion.
20. The signing request becomes completed / terminal.
21. A completed signed PDF is generated and preserved.
22. A Signing Record is preserved.
23. The customer cannot reuse the link to alter the completed transaction.

---

## 4. Exact document binding

The signature is tied to **one exact document**, not to “the Change Order as later edited.”

Recorded with the signing event:

- Change Order identity
- frozen snapshot / version identity
- SHA-256 of the **pre-sign** PDF
- recipient name and email
- signing-request identity
- consent-text version
- completion timestamp
- SHA-256 of the **final signed** PDF

If Change Order content changes after send:

```text
VOID / SUPERSEDE the signing request
→ freeze a new document
→ new SHA-256
→ new signing request
```

A signature must **never** silently transfer to changed commercial terms.

---

## 5. Signer identification (proposed V1)

Proposed:

- request sent only to a governed customer email
- unique high-entropy signing URL
- bounded expiry
- signer confirms name
- explicit SIGN & ACCEPT
- one-time completion

**Not** proposed for V1 unless counsel requires it:

- SMS one-time passcode
- multi-factor authentication
- government identity documents
- biometrics
- geolocation
- identity-document upload

**Question for counsel:** Is this assurance appropriate for Brayman Change Orders? If not, what additional assurance is required?

---

## 6. Consent / intent (functional requirement only)

CalibAi will **not** invent final legal wording. AI cannot mark consent language **APPROVED**.

Before SIGN & ACCEPT, the customer must explicitly acknowledge, in counsel-approved words, that:

**A.** they have reviewed, or had access to, the Change Order;

**B.** they intend to sign electronically;

**C.** their electronic action constitutes their signature / acceptance of the **identified** Change Order.

**Question for counsel:** Please provide or approve the exact wording. CalibAi will store that text as a **versioned** consent record and display that version at signing.

---

## 7. What “counts” as the signature

Proposed V1 representation:

```text
explicit SIGN & ACCEPT
+ typed / adopted signer name
```

An optional drawn or styled glyph may be shown so the completed PDF looks familiar.

The graphical image is **not** intended to be the sole authoritative record.

The authoritative commercial signing event is the durable record tying:

- the signer
- their intent
- the exact document
- the exact document hash
- the completion action
- the timestamp
- the signing request

**Question for counsel:** Is this acceptable for Brayman Change Orders?

---

## 8. Proposed Signing Record (minimum)

| Item | Proposed |
|------|----------|
| Organization | Yes |
| Project | Yes |
| Change Order | Yes |
| Signing request identity | Yes |
| Frozen document identity / version | Yes |
| Pre-sign PDF SHA-256 | Yes |
| Recipient name | Yes |
| Recipient email | Yes |
| Request created time | Yes |
| Sent time | Yes |
| Opened time | Optional, if recorded |
| Consent text version | Yes |
| Signer-confirmed name | Yes |
| Signed time (UTC) | Yes |
| Completion IP address | **May** be retained — see §9 |
| Basic user-agent | **May** be retained — see §9 |
| Signing status | Yes |
| Void / decline / expiry metadata | Yes |
| Final signed PDF SHA-256 | Yes |
| Authenticated Brayman user who approved / sent | Yes |

**Not** proposed as routine collection:

- geolocation
- device fingerprinting
- biometrics
- government ID

**Question for counsel:** Is any additional record necessary?

---

## 9. Privacy — IP address and user-agent

Proposed architecture: completion **IP address** and **basic user-agent** **may** be retained as signing provenance. No invasive device fingerprinting.

Counsel is asked:

**A.** Is retaining completion IP advisable or necessary?

**B.** Is basic user-agent advisable or necessary?

**C.** Are there specific disclosure or privacy requirements Brayman should follow?

Answers will be recorded later as governed policy. This specification does **not** decide them.

---

## 10. Completed documents

Three artifacts would be preserved separately. The pre-sign PDF is **not** overwritten.

1. **Pre-sign frozen Change Order PDF**
2. **Final signed Change Order PDF**
3. **Signing / completion record**

The final PDF may include:

- the original frozen Change Order content
- a signing / completion block
- signer name
- signed timestamp
- CalibAi signing-request reference
- a completion / audit page

Final legal wording on that page is **not** authored here.

---

## 11. Document integrity — hashing vs cryptographic PDF signing

Proposed Native V1 uses:

```text
application-level SHA-256
+ immutable CalibAi Signing Record
+ immutable pre-sign PDF
+ immutable final signed PDF
```

It does **not** presently require:

- PAdES
- a certificate-based PDF digital signature
- a PKI signing certificate

**Question for counsel (do not treat as answered):**

Is this application-level integrity / audit model appropriate for Brayman Change Orders?

Or should completed PDFs use cryptographic PDF signing / certificate-based validation?

---

## 12. When a Change Order is “effective”

Proposed product rule: **Brayman internal approval does not establish customer authorization.**

**Question for counsel:** Should customer completion of this ceremony normally make the Change Order **EFFECTIVE / CUSTOMER AUTHORIZED**?

Are any other legally recognized customer-authorization paths required to be represented?

No exception path is invented here.

---

## 13. Decline, void, expiry, resend, supersede

Proposed signing-request outcomes:

- awaiting signature
- signed / completed
- expired
- voided
- declined (if the customer explicitly declines)

**Question for counsel:** What customer notice or record, if any, is required for voiding, expiry, decline, resend, or superseding a previously sent Change Order?

---

## 14. Correcting a signed Change Order

Proposed rule: a **signed** Change Order is **not edited in place**.

If commercial terms must change:

- preserve the signed Change Order
- create a new / superseding commercial record as governed
- obtain new customer authorization where required

Signed history is not mutated.

**Question for counsel:** Please confirm or modify this rule, including what is required when a **sent but unsigned** Change Order must be corrected.

---

## 15. Customer copy

**Question for counsel:** Upon signing, must the customer receive a completed copy automatically?

Is an email attachment preferable or required? Is a secure download link sufficient? Should both be offered? Is any access period required?

Mail is **not** implemented in this governance step.

---

## 16. Record retention

**Question for counsel:** Does Ontario law or practice impose a minimum retention period for:

- the signed Change Order
- the pre-sign Change Order
- the signing / audit record
- the consent version
- related communications

No retention period is invented here. Future project closeout / archive must preserve whatever counsel requires.

---

## 17. Wet-ink / non-electronic exceptions

**Question for counsel:** Are there Brayman Change Order circumstances where electronic signing should **not** be used, or where another form or signing method is required?

Do not generalize beyond counsel’s answer.

---

## 18. Later use for construction contracts

The same signing **ceremony** is intended later for Ontario Contract + Warranty packages.

Contract and warranty **templates** remain behind a separate Legal Content Gate. Native signing must never bypass:

- an approved Ontario Contract template
- an approved Warranty
- human approval before send
- legal-content governance

Native signing does **not** make the Ontario Contract legally ready.

**Question for counsel:** Once the underlying contract form has been **separately** approved, would this same signing ceremony also be suitable for Brayman construction contracts?

Template approval remains separate from process approval.

---

## 19. Counsel decision list

Please answer **YES / NO / MODIFY** (or supply wording / period where asked).

| # | Question | Counsel |
|---|---------|---------|
| 1 | Is the proposed native electronic-signing ceremony appropriate for Brayman Ontario Change Orders? | |
| 2 | Is governed-email + high-entropy expiring link + signer-name confirmation sufficient signer assurance? | |
| 3 | Is explicit SIGN & ACCEPT + typed/adopted name sufficient signature representation? | |
| 4 | What exact electronic-consent / intent wording should be approved? | |
| 5 | Should completion IP be retained? | |
| 6 | Should basic user-agent be retained? | |
| 7 | Is SHA-256 + immutable Signing Record sufficient, or should completed PDFs use PAdES / certificate-based cryptographic signing? | |
| 8 | Should customer signature normally establish Change Order EFFECTIVE / CUSTOMER AUTHORIZED status? | |
| 9 | Are any alternative authorization paths required? | |
| 10 | What is required when a sent or signed Change Order must be corrected or superseded? | |
| 11 | What completed-document copy must be provided to the customer? | |
| 12 | What retention period applies? | |
| 13 | Are there any wet-ink / non-electronic exceptions? | |
| 14 | Can this same signing ceremony later be used for Brayman construction contracts after separate template approval? | |
| 15 | Are there any Ontario construction / consumer-law requirements missing from the proposed process? | |

---

## 20. What this document does not decide

- DocuSign or Adobe Acrobat Sign as a vendor (architecture may keep them as a later fallback; they are not required by this V1 proposal)
- Ontario Contract or Warranty template language
- Software design, database schema, or a Feature Gate
- BUILD / field capture
- Any unsigned-work exception policy

---

## Related (internal; not required for counsel)

- [architecture/contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md)
- [architecture/change-order-document-family.md](../architecture/change-order-document-family.md)
- [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md)
- [adr/ADR-002-accepted-proposal-immutability.md](../adr/ADR-002-accepted-proposal-immutability.md)

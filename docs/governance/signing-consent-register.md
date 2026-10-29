# Signing consent register

The electronic-signature consent versions CalibraytAI pins to signing requests, and who approved each. A consent
version is created once and never edited; changed wording is a new version with its own approval. The wording
below is copied from the code that holds it and must stay identical to it.

| Version | Authority | Used for | Signers | Status |
|---|---|---|---|---|
| `CONSENT-SUPPLIER-V1-001` | PRODUCTION | Supplier purchase orders and supplier delivery changes (FG-041) for real (non-demo) suppliers | Contractor/office signer and supplier/store signer, each signed in | **APPROVED — 29 OCTOBER 2026 (Joel Brayman)** |
| `CONSENT-BRAYMAN-V1-001` | PRODUCTION | Brayman V1 generated contracts (client signing) | Client (secure link, no account) | In use since 16 Oct 2026 (WF-04, internal V1 acceptance). Not broadened by the supplier approval. |
| `CONSENT-SYNTHETIC-UAT-001` | SYNTHETIC_UAT | Synthetic/test requests: demo suppliers, and office-sent change orders (see PP-1) | Test signers | Test only. Not affected by the supplier approval. |

## CONSENT-SUPPLIER-V1-001 — APPROVED — 29 OCTOBER 2026

Source: `app/services/supplier_signing.py`, `CONSENT_SUPPLIER_V1_CODE` / `CONSENT_SUPPLIER_V1_BODY`.

Approved wording, exactly as written (unchanged; no new version created):

> By ticking the box, typing your full name and selecting the sign button, you sign this document electronically for
> the business you represent, and you confirm you are authorized to do so. Your typed name and that selection are your
> signature. You can open the document before you sign, and both businesses can download the signed copy with its
> signing record afterwards. If you do not want to sign electronically, do not continue and contact the other business
> directly.

Approval (Joel Brayman, 29 Oct 2026, in the CaliSIGN supplier consent review):

- Applies to the existing supplier CaliSIGN implementation reviewed in the approval package (branch
  `feature/calisign-native-esignature-2026-10-28` at `692cbb85`, on PR #13's FG-041 work): Purchase Orders, Delivery
  Changes, the contractor/office signer and the supplier/store signer.
- Joel specifically accepted the statements on: consent to electronic signing; signing for the business represented;
  the signer's confirmation of authority; attribution of the typed name plus the signing action as the electronic
  signature; availability of the document before signing; availability of the signed copy and signing record
  afterwards; opting out by not proceeding and contacting the other business.
- Shown as reviewed: the "Adopt your signature" box in the Supplier Hub and on the office forms; the tick box "I agree
  to sign electronically", unticked by default; typed full name with script preview; the sign buttons (Sign & Confirm
  Order, Sign & Accept [date], Sign & Propose This Time, Sign & Send for E-Signature, Sign & Send the Change); refusal
  without the tick records nothing.
- Synthetic (demo) suppliers keep the synthetic prefix and pin `CONSENT-SYNTHETIC-UAT-001`; not affected.

This approval does **not** authorize: production or Training deployment; running PR #13's supplier migration
(`a4d5e6f7a8b9`) in Production; merging unrelated feature work; sending real supplier signing requests. Those remain
separate decisions for Joel.

## Pre-production follow-ups (recorded 29 Oct 2026; separate from the consent approval)

These do not change the approved wording. Each must be resolved or explicitly dispositioned before CaliSIGN is
recommended for production.

**PP-1 — Client Change Order consent.** Office-sent change orders
(`office_send_change_order_for_signature`, `app/services/signing.py`) pin `CONSENT-SYNTHETIC-UAT-001` ("NOT FOR
SIGNATURE") with authority `SYNTHETIC_UAT`, so a real client change order is not signed under an approved production
consent. Do not substitute the supplier consent; do not silently broaden `CONSENT-BRAYMAN-V1-001` (its wording names
"this contract"). Determine the governed solution (for example a change-order production consent version for Joel's
approval) during CaliSIGN release preparation.

**PP-2 — IP / proxy evidence hardening.** Supplier signatures record the first `X-Forwarded-For` entry
(`signature_from_form`, `app/services/supplier_signing.py`), which the sender can supply; client signatures record
`request.remote_addr` (`app/routes/sign.py`), which on Render may be the proxy rather than the signer. The app has no
trusted-proxy configuration. Keep IP evidence; determine the correct trusted-proxy approach for the hosted
architecture before production release.

# Signing consent register

The electronic-signature consent versions CalibraytAI pins to signing requests, and who approved each. A consent
version is created once and never edited; changed wording is a new version with its own approval. The wording
below is copied from the code that holds it and must stay identical to it.

| Version | Authority | Used for | Signers | Status |
|---|---|---|---|---|
| `CONSENT-SUPPLIER-V1-001` | PRODUCTION | Supplier purchase orders and supplier delivery changes (FG-041) for real (non-demo) suppliers | Contractor/office signer and supplier/store signer, each signed in | **APPROVED — 29 OCTOBER 2026 (Joel Brayman)** |
| `CONSENT-BRAYMAN-CHANGE-ORDER-V1-001` | PRODUCTION | Client change orders sent from the office (FG-033 SIGN-D), from the 29 Oct 2026 CaliSIGN release | Client (secure link, no account); Brayman countersigns | **In use from release — 29 Oct 2026** (Joel authorized: the contract consent with only the document named changed) |
| `CONSENT-BRAYMAN-V1-001` | PRODUCTION | Brayman V1 generated contracts (client signing) | Client (secure link, no account) | In use since 16 Oct 2026 (WF-04, internal V1 acceptance). Not broadened by the supplier approval. |
| `CONSENT-SYNTHETIC-UAT-001` | SYNTHETIC_UAT | Synthetic/test requests: demo suppliers; change orders sent on the training site (`TRAINING_ENVIRONMENT`); engine tests | Test signers | Test only. No longer used for office change orders (PP-1). |

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

**PP-1 — Client Change Order consent. RESOLVED 29 Oct 2026** — see `CONSENT-BRAYMAN-CHANGE-ORDER-V1-001` below.
Office-sent change orders had pinned `CONSENT-SYNTHETIC-UAT-001` ("NOT FOR SIGNATURE") with authority `SYNTHETIC_UAT`
since SIGN-D (15 Sep 2026, scoped then as synthetic UAT; never completed for production when contracts went to
production on 16 Oct). `CONSENT-BRAYMAN-V1-001` names "this contract", so it was not broadened.

**PP-2 — IP / proxy evidence hardening. RESOLVED 29 Oct 2026** (`app/services/client_ip.py`). Before: supplier signatures record the first `X-Forwarded-For` entry
(`signature_from_form`, `app/services/supplier_signing.py`), which the sender can supply; client signatures record
`request.remote_addr` (`app/routes/sign.py`), which on Render may be the proxy rather than the signer. The app has no
trusted-proxy configuration. After: both record `request_client_ip()`. On Render (it sets `RENDER=true`) every public
request passes through Cloudflare, which sets `CF-Connecting-IP` to the address that connected to it and refuses a
request that supplies that header itself; the app records that address when it is a valid IP. `X-Forwarded-For` is
never trusted (Render appends to it without resetting it). Without the header (local, tests, the training site), or
if it is malformed, the socket address is recorded, as before. `CLIENT_IP_HEADER` can name another header for
another host. Sources: Render, "How Render handles DDoS attacks" (all inbound traffic passes through Cloudflare);
Render's header-test demo (spoofed `CF-Connecting-IP` is refused by Cloudflare; `X-Forwarded-For` keeps a fake
leftmost value). IP evidence means: the public address Cloudflare saw connecting, which may be a carrier, office or
VPN gateway rather than the signer's own device.

## CONSENT-BRAYMAN-CHANGE-ORDER-V1-001 — PRODUCTION — 29 OCTOBER 2026

Source: `app/services/signing.py`, `CONSENT_BRAYMAN_CHANGE_ORDER_V1_CODE` / `CONSENT_BRAYMAN_CHANGE_ORDER_V1_BODY`.

Joel's release authorization (29 Oct 2026): wording substantively parallel to the approved contract consent that only
changes the document reference is an implementation/governance completion. This wording is
`CONSENT-BRAYMAN-V1-001` with "contract" replaced by "change order" and nothing else changed (a test enforces it):

> By ticking the box, typing your full name and selecting Sign & Accept, you agree to sign this change order
> electronically. Your typed name and that selection are your signature on this change order. Before you sign you
> can open the full change order above and keep a copy. After you sign you can download the signed change order with
> its signing record. If you do not want to sign electronically, do not continue and contact Brayman Construction.

Scope: client change orders sent from the office (status Approved), the client signing through the secure CaliSIGN
link; Brayman countersigns by default. The training site keeps `CONSENT-SYNTHETIC-UAT-001`. Earlier change-order
signing records keep the consent they pinned (synthetic), unchanged.

Shared note (both client consents): "After you sign you can download …" — the signing link offers the completed
document once every signature is in place (after Brayman's countersignature when required) and while the link is
still valid (7 days by default); after that the office provides the copy (the completion email says so).

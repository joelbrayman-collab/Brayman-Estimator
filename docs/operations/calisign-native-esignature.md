# CaliSIGN native e-signature (28 Oct 2026)

**Status:** built on branch `feature/calisign-native-esignature-2026-10-28`, stacked on the FG-041 reconcile branch
(PR #13). **NOT MERGED. NOT DEPLOYED.** No migration of its own. Supplier signing still depends on PR #13's
migration (`a4d5e6f7a8b9`). Its consent `CONSENT-SUPPLIER-V1-001` was **approved by Joel on 29 Oct 2026**, exactly as
written ([signing consent register](../governance/signing-consent-register.md)).

CaliSIGN is the name and look of CalibraytAI's existing native signing. It is not a new engine. The FG-033 engine
(SIGN-A to SIGN-E) signs client contracts and change orders; FG-041 signs supplier purchase orders and delivery
changes. CaliSIGN changes how that work is launched, shown and emailed. The identity is the approved one
(`docs/branding/calisign/README.md`).

## What the office sees

| Document | Where | Action | Signing sequence | Final state |
|---|---|---|---|---|
| Contract | Project → Contract (after it is generated) | **Send for E-Signature** | Office sends → client signs at the CaliSIGN link → office countersigns (default) | Executed; **Download Executed Copy** |
| Change Order | Change order page (status Approved) | **Send for E-Signature** | Same as the contract | Executed; **Download Executed Copy** |
| Purchase order | Supplier requests → approved quote | **Sign & Send for E-Signature** | Office signs on placing → store signs in the Supplier Hub (**Sign & Confirm Order**) | Executed when both have signed; signed copy (PDF) both sides |
| Delivery change | Delivery panel (office or Hub) | **Sign & Send the Change** | Requester signs on asking → the other side signs on **Sign & Accept** | Executed; signed change (PDF). Decline needs no signature; counter or withdraw voids |

Draft or unapproved records show no send action.

### The CaliSIGN panel on a contract or change order

One panel on the record shows the status chip, the signer, expiry, countersignature, signed copy and email
delivery, then the next action only:

- **Not sent for signature** → the compact *Review & send* card, already filled in from the accepted proposal or
  the project's client (document, project, client, signer name, signer email, days valid, countersign). Check it,
  then **Send for E-Signature**.
- **Awaiting Signature** → **Resend Invitation** (a new link; the old link stops), Void.
- **Viewed** → the signer opened the link (a real `VIEWED` event).
- **Awaiting Your Signature** → the client has signed; **Countersign & Execute**.
- **Executed** → **Download Executed Copy**.
- Voided, Expired, Declined are shown as they are recorded.

*View Signing Status* lists the real signing events (created, approved, sent, opened, consent, signed, countersigned,
executed, …) with who and when. Nothing is inferred: every label comes from `SigningRequest.status` and its
`SigningEvent` rows (`app/services/calisign.py`).

## What the client sees

1. **Email** (existing transactional email, `SIGNING_INVITATION` / `SIGNING_RESEND` / `SIGNING_COMPLETE`): an HTML
   CaliSIGN message with a text version, the document, project and sender, the button **Review and Sign Document**
   and "No CalibraytAI account is needed". No new mail service. The link is never logged (`invitation_url` stays a
   secret variable).
2. **Signing page** `/sign/<link>`, one responsive page:
   - desktop (≥1024 px): the frozen PDF on the left, the signing panel on the right;
   - phone: one column, a **Review the document** button opens the PDF;
   - steps: 1 Review Document · 2 Consent to Sign · 3 Adopt Signature · 4 Sign & Accept · 5 Confirmation.
   - consent uses the stored consent version's wording, not ticked in advance;
   - the typed full name shows as a script signature: "This is how your name will appear as your electronic
     signature." No drawing, no font menu. The stored signature is the typed text; the script is only how it is
     shown. The script font (Dancing Script, SIL OFL) is served by the app, not a third party;
   - **Sign & Accept** posts once (the button locks; the server refuses a second signature anyway).
3. **Document Signed Successfully.** If the contractor still countersigns, the page says so: signed is not executed.
   Once executed, the same link offers the completed document.

Error pages say what happened and that nothing was signed: invalid link, expired, already signed, closed
(withdrawn/declined/expired request), document could not be prepared, not open for signing, too many tries.

## What the store sees

Stores sign in the Supplier Hub, signed in (FG-041). They get a CaliSIGN email (`SIGNING_SUPPLIER_INVITATION`)
for a new purchase order and for a delivery change the contractor asks for: the contractor, the project reference
the store already has (never the job name), the document, and **Review and Sign Document** pointing to the Hub. In the Hub
the "Adopt your signature" box shows the consent wording, the tick box (not ticked) and the typed name with its
script preview; chips show Awaiting Your Signature / Awaiting Signature / Executed.

## SMS

Supplier order notices already go by text where the store user has agreed to texts (existing
`app/services/text_messages`). Client signing has no text message: clients are not users and have no texting
consent on record. **Client SMS invitations are future work** and need a consent decision first.

## Evidence

- Focused tests: `tests/test_calisign_esignature_client.py`, `tests/test_calisign_esignature_supplier.py`
  (revised brief items 1–34; 35 is the existing signing suites, unchanged in what they prove).
- Browser walk: `tools/release/evidence_calisign.mjs` on `tests/calisign_page_server.py` (temporary database,
  synthetic data, mail captured locally). Contract and change order to Executed, purchase order and delivery change
  to Executed, at 1600, 1280×800 and 390 px.

  ```
  EVIDENCE_REPO=$PWD EVIDENCE_SHOTS=/tmp/calisign-shots node --test --test-concurrency=1 tools/release/evidence_calisign.mjs
  ```

  Chromium without Chrome's PDF viewer draws the document frame blank; Chrome on the Mac draws it. The walk also
  renders page 1 of the exact bytes the frame was served (`03b-supplement-…`).

## Approval gates

- PR #13 (FG-041) supplier migration: not applied anywhere hosted; production apply needs Joel's authorization.
- `CONSENT-SUPPLIER-V1-001`: **APPROVED — 29 OCTOBER 2026** (Joel). Wording unchanged; no new version.
- Production deploy: Joel's Mac release gate. The consent approval does not authorize deployment, the production
  migration or real supplier signing requests.

## Release readiness: PR #13 → PR #16 (opened 29 Oct 2026)

Nothing here is deployed. Each item must be resolved or explicitly dispositioned before production is recommended.

| # | Item | Status |
|---|---|---|
| 1 | Supplier migration readiness (`a4d5e6f7a8b9` on `q4c7l2n8t3a6`; `migration_check.py --altered-checks`; release gate wiring) | **Next** |
| 2 | Supplier consent `CONSENT-SUPPLIER-V1-001` | **Complete** — approved 29 Oct 2026 |
| 3 | Client Change Order production consent (PP-1 in the consent register) | Open — needs a governed solution and Joel's approval |
| 4 | Trusted IP / proxy evidence (PP-2 in the consent register) | Open — technical hardening |
| 5 | Migration rollback / recovery | Open |
| 6 | Final tests and the Mac release gate on the exact commit | Open |
| 7 | Deployment order (merge #13, then #16; backup; migration; deploy; post-checks) | Open — Joel authorizes |

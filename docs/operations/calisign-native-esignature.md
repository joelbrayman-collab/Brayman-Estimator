# CaliSIGN native e-signature (28 Oct 2026)

**Status:** built on branch `feature/calisign-native-esignature-2026-10-28`, stacked on the FG-041 reconcile branch
(PR #13). **NOT MERGED. NOT DEPLOYED.** No migration of its own. Supplier signing still depends on PR #13's
migration (`a4d5e6f7a8b9`) and on `CONSENT-SUPPLIER-V1-001`, which is **not approved**.

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

*Signing history* lists the real signing events (created, approved, sent, opened, consent, signed, countersigned,
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
for a new purchase order and for a delivery change the contractor asks for, pointing them to the Hub. In the Hub
the "Adopt your signature" box shows the consent wording, the tick box (not ticked) and the typed name with its
script preview; chips show Awaiting Your Signature / Awaiting Signature / Executed.

## SMS

Supplier order notices already go by text where the store user has agreed to texts (existing
`app/services/text_messages`). Client signing has no text message: clients are not users and have no texting
consent on record. **Client SMS invitations are future work** and need a consent decision first.

## Evidence

- Focused tests: `tests/test_calisign_esignature_client.py`, `tests/test_calisign_esignature_supplier.py`
  (brief items 1–33; 34 is the existing signing suites, unchanged in what they prove).
- Browser walk: `tools/release/evidence_calisign.mjs` on `tests/calisign_page_server.py` (temporary database,
  synthetic data, mail captured locally). Contract and change order to Executed, purchase order and delivery change
  to Executed, at 1600, 1280×800 and 390 px.

  ```
  EVIDENCE_REPO=$PWD EVIDENCE_SHOTS=/tmp/calisign-shots node --test --test-concurrency=1 tools/release/evidence_calisign.mjs
  ```

  Chromium without Chrome's PDF viewer draws the document frame blank; Chrome on the Mac draws it. The walk also
  renders page 1 of the exact bytes the frame was served (`03b-supplement-…`).

## Approval gates (unchanged by CaliSIGN)

- PR #13 (FG-041) supplier migration: not applied anywhere hosted.
- `CONSENT-SUPPLIER-V1-001`: not approved. Real suppliers cannot sign until it is.
- Production deploy: Joel's Mac release gate.

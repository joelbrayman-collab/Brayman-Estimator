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
| 1 | Supplier migration readiness (`a4d5e6f7a8b9` on `q4c7l2n8t3a6`) | **Verified 29 Oct 2026** (below); release-gate wiring corrected (`d7c3e389`) |
| 2 | Supplier consent `CONSENT-SUPPLIER-V1-001` | **Complete** — approved 29 Oct 2026 |
| 3 | Client Change Order production consent (PP-1) | **Resolved** — `CONSENT-BRAYMAN-CHANGE-ORDER-V1-001`, the contract consent with only the document named changed (consent register) |
| 4 | Trusted IP / proxy evidence (PP-2) | **Resolved** — `app/services/client_ip.py`: Cloudflare's `CF-Connecting-IP` on Render; `X-Forwarded-For` never trusted (consent register, PP-2) |
| 5 | Migration rollback / recovery | **Planned** — procedure below, with the old code proven on a migrated database |
| 6 | Final tests and the Mac release gate on the exact commit | Open until the gate passes on the Mac |
| 7 | Deployment order | **Planned** — sequence below; production deployment pending the gate |

## Supplier migration verification — 29 Oct 2026 (readiness item 1)

Disposable SQLite files only (production is SQLite on the Render instance); nothing hosted was read or changed.

- **Start:** `main` `817bf451`; PR #13 open/draft at `43694c53`; PR #16 open at `bba5a9bb`; migration
  `a4d5e6f7a8b9` (down revision `q4c7l2n8t3a6`) is byte-identical to FG-041's commit `705d2ad2` and is the only
  migration difference from `main`.
- **Database:** built by Alembic from the migration history to `q4c7l2n8t3a6` (218 tables), then legitimate
  pre-migration records through the app's own services: an executed client change-order signing, a signed contract
  awaiting countersignature, a quoted and approved concrete request (135 rows; 2 signing requests, 4 participants,
  12 events, 2 frozen and 1 executed artifact).
- **Up:** succeeded. Exactly three check constraints changed:
  `ck_signing_frozen_artifacts_document_family` and `ck_signing_requests_document_family` (+ `SUPPLIER_ORDER`,
  `SUPPLIER_DELIVERY_CHANGE`), `ck_signing_participants_role` (+ `CONTRACTOR`, `SUPPLIER`). No table, column, type,
  default, nullability, index, foreign key or other check changed; no row changed, deleted or inserted (row
  fingerprint of all 218 tables identical: `fceef76e28b461b3` before, after up, after down). The three tables are
  rebuilt, so SQLite stores their CREATE text with clauses in a different order; structure is identical.
- **Constraints:** after up, the four new values are accepted and the old values still accepted; `PURCHASE_ORDER`,
  `BYSTANDER`, lower-case variants and empty strings are still rejected. After down, the new values are rejected again.
- **Down (no supplier rows):** succeeded; checks, structure and every row back to the baseline. Round trip
  up → down → up: same structure and rows.
- **Down with supplier rows:** after one real purchase order was placed (1 request, 1 frozen artifact, 2
  participants, 4 events), the downgrade **refuses** ("Supplier signing records exist … Restore the pre-migration
  backup instead.") and leaves the database at `a4d5e6f7a8b9`, unchanged.
- **Code before migration:** the supplier-signing code on an unmigrated database cannot place an order (check
  constraint refuses the supplier frozen artifact; the order is rolled back, nothing saved). Deploy and migration must
  follow each other closely; this window belongs to readiness item 7 (deployment order).
- **Checker:** `migration_check.py rehearse --new-tables none --altered-checks <the three>` → `MIGRATION_REHEARSAL=ok`,
  three `ALTERED_CHECK` lines, "every row identical; schema identical except the named check constraints". Without
  declaring them, or naming a different check, it fails. With `--altered-tables` it also passes but checks less
  (any schema change of those tables, indexes included, would be accepted).
- **Release gate (corrected `d7c3e389`):** before, the gate and `release_migrate.sh` could pass only
  `--altered-tables`. Now both carry `--altered-checks`. Release arguments for this migration:
  `--migration-to a4d5e6f7a8b9 --new-tables none --altered-checks ck_signing_frozen_artifacts_document_family,ck_signing_requests_document_family,ck_signing_participants_role`.
- **Rollback truth:** schema rollback is possible only before any supplier signing record exists. After real supplier
  use, a downgrade is refused by design; the options are to keep the widened checks and redeploy older code (the
  older code runs with the wider checks), or restore the pre-migration backup (losing everything written since).
  Which to use, and any archival, is readiness item 5.

## Release sequence (established mechanism, CaliSIGN release)

Live before the release: `30d47b8` (deploy `dep-dbgeh86gekts73a54c60`), database revision `q4c7l2n8t3a6`. The
candidate fast-forwards `main`; Render deploys `main` (auto-deploy off).

1. **Mac release gate** (`tools/release/release_gate.sh`, Joel's Mac): clean clone at the candidate; complete
   regression with no skip; release browser checks in Chrome (now including `evidence_calisign.mjs`); a fresh hosted
   backup copied to the Mac and verified; the migration rehearsed on a copy of that backup in strict mode
   (`--migration-to a4d5e6f7a8b9 --new-tables none --altered-checks ck_signing_frozen_artifacts_document_family,ck_signing_requests_document_family,ck_signing_participants_role`);
   stops at READY_FOR_PUSH.
2. **Push and deploy** (Claude): `main` fast-forwarded to the candidate; Render deploy triggered for that commit.
3. **Migration** (`release_migrate.sh`, Joel's Mac): waits until the instance runs the candidate; takes the instance's
   own online pre-migration backup and copies it to the Mac; applies the migration with the same strict checks.
4. **Post-release check** (`postrelease_check.sh`): live revision, rows, integrity, pages.

**The window between 2 and 3.** The new code on the old schema cannot record a supplier signature: placing a
supplier purchase order, or signing a delivery change, is refused (nothing is saved; the user sees an error).
Everything else, including client contract and change-order signing, works. `release_migrate.sh` starts the moment
the instance reports the new commit (it polls every 30 s), so the window is the few minutes of the deploy. Release at
a quiet hour.

## Recovery (incident procedure)

Recovery points: the gate's fresh hosted backup (on the Mac) and the instance's pre-migration backup
(`instance/backups/pre-migrate-<label>-<UTC>.db`, also copied to the Mac). Restoring a backup always needs Joel.

| Situation | What to do | Why it is safe |
|---|---|---|
| The deploy fails or the new code misbehaves **before** the migration | Redeploy `30d47b8` (deploy `dep-dbgeh86gekts73a54c60`, same settings). Do not run the migration. | Nothing in the database changed. |
| The migration stops (`MIGRATE` not ok) | Leave the app running; read `$OUT-migrate.txt`. If the revision is still `q4c7l2n8t3a6`, nothing changed: redeploy `30d47b8` and investigate. If the database is partly changed, Joel restores the pre-migration backup, then redeploy `30d47b8`. | SQLite migration DDL is not transactional; the backup was taken and verified immediately before. |
| A problem **after** the migration, no supplier signing yet | Redeploy `30d47b8`. Keep the widened checks (no downgrade needed). | Verified 29 Oct 2026: the live code `30d47b8` signs-in, opens projects, supplier requests, deliveries and change orders, and sends, signs and countersigns a change order on a database at `a4d5e6f7a8b9`. |
| A problem **after** supplier signing has started | Redeploy `30d47b8` and/or forward-fix. **Do not downgrade**: it refuses once supplier signing records exist, by design. The supplier records stay in the database untouched; the old code does not read them. | Same verification, run with a supplier signing record present. |
| Catastrophic damage to the database | Joel restores the pre-migration backup and redeploys `30d47b8`. Everything written after the backup is lost, so this is the last resort. | Backup verified (integrity, revision, SHA-256) at the time it was taken. |

No step deletes data automatically; there is no automated rollback.

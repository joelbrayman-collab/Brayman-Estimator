# Paulusse (3 Kingfisher): Estimate Builder REV2 technically accepted, development hold

**Status:** REV2 TECHNICALLY ACCEPTED / DEVELOPMENT HOLD / AWAITING BEN FEEDBACK. Recorded on 2026-10-30 on Joel Brayman's instruction.

No product code was changed and nothing was deployed. No further Paulusse development is authorized until Ben responds.

## Accepted candidate

- **File:** `PAULUSSE_3_KINGFISHER_ESTIMATE_BUILDER_SCOPE_REV2_2026-10-30.pdf`
  - SHA-256: `65d8726af14ee83fb52f65daf9779bac070b71f1e1d45b95e76e1acdbc6ea332`
  - Size: 7,541,972 bytes, 10 pages, legal landscape throughout.
- **Supersedes:** REV2 replaces `…_SCOPE_REV_2026-10-30` for all future Paulusse work. Historical versions are kept and are never silently overwritten.
- **Change rule:** REV2 is not altered while Ben's feedback is awaited, unless a critical defect is found.
- **Not part of this record:** the PDF and its generator scripts are working files held outside Git. They are not committed here.

## Validation completed

**pdf.js (Firefox's built-in PDF viewer)**
- full functional suite
- each scope package excluded on its own
- every package excluded at once
- labour rate
- target gross margin
- regression of the original editable fields
- propagation to the customer Detailed Estimate
- propagation to the customer Proposal
- propagation of the responsible party
- quantity preservation
- restoration of the canonical baseline

**Adobe Acrobat Reader**
- dynamic show and hide of the responsibility selector
- recalculation
- save, close and reopen persistence
- propagation to the customer documents
- inspection of print output

## Canonical all-included baseline

| Item | Value |
|---|---|
| Labour hours | 272 |
| Direct labour | $20,400.00 |
| Materials | $17,997.32 |
| Equipment | $850.00 |
| Other | $700.00 |
| Total direct cost | $39,947.32 |
| Selling price | $46,996.85 |
| Gross profit | $7,049.53 |
| HST | $6,109.59 |
| Customer total | $53,106.44 |

## Scope UX accepted for this candidate

The scope section is headed **BRAYMAN SCOPE OF WORK** and asks one question per selectable work package: **is Brayman doing this work?**

- **Checked:** Brayman includes the work.
- **Unchecked:** the work is excluded from Brayman's scope, and a responsible-party selector appears with three choices:
  - By Others (the default)
  - By Lockwood
  - By Owner / Client
- **General conditions:** calculated automatically and not offered as a selectable package. They stay in the price while any Brayman package is included.

## Architectural evidence (input to the Dynamic Estimate Builder; not authorization)

**Construction requirement is separate from contractual responsibility.** Excluding work does not delete:

- takeoff quantity
- construction intelligence
- labour requirement
- material requirement

Excluding work only changes whether Brayman is commercially responsible for it.

The Paulusse prototype demonstrated this dependency chain:

1. Drawings / takeoff
2. Work package
3. Brayman included / excluded
4. Responsible party
5. Material, labour and equipment cost participation
6. Direct cost
7. Selling price
8. Customer Detailed Estimate
9. Customer Proposal

See also [governance/estimate-approval-and-commercial-gates.md](../governance/estimate-approval-and-commercial-gates.md) for the customer-facing scope clarity rule and the future work-package fields (commercial status, responsible party, delivery method).

## Adobe Reader characteristic

Adobe Reader may ask the user to save changes after they open the interactive PDF, even when they made no edits. This happens because the calculated fields recalculate when the file opens. On an unchanged file, choosing **Don't Save** is safe.

This is a characteristic of the current interactive-PDF implementation. REV2 is not to be modified only to remove it. The eventual Calibrayt workflow must not depend on the interactive PDF being the system of record.

## Ben's current review

Ben's existing package (`PAULUSSE_3_KINGFISHER_ESTIMATE_BUILDER_2026-10-30`) is untouched, and nothing has been sent to replace it.

When Ben responds:

1. Capture his requested changes exactly.
2. Compare his returned or reviewed package against the version originally sent to him.
3. Separate his changes into:
   - scope
   - quantity
   - supplier / pricing
   - labour
   - commercial
   - wording / presentation
4. Reconcile those changes into REV2.
5. Re-run the affected calculations and the regression tests (pdf.js and Adobe Reader).
6. Produce the next review or final candidate.
7. Do not silently overwrite historical versions.

## After Paulusse is finalized

Resume the Calibrayt architecture exercise in the agreed order:

1. Identify the governed Calibrayt project stages.
2. Record, save and document those stages.
3. Define the exact output and package contents at each stage.
4. Reconcile those requirements against existing Calibrayt functionality.
5. Identify genuine gaps.
6. Implement only the gaps that are approved.

The Paulusse Estimate Builder and its scope-control behaviour are evidence for that exercise. They do not authorize implementing it.

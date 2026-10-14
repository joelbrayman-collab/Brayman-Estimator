# Deck Takeoff — pool-deck material takeoff and supplier price return

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTED / TESTED — not accepted, not committed, not deployed; catalogue migration prepared, not applied** |
| Updated | 2026-10-13 |
| Rule | `pool_deck_takeoff` version `1` |
| Code | `app/services/deck_takeoff/`, `app/routes/deck_takeoff.py`, `app/templates/projects/deck_takeoff*.html` |
| Approved page | `render_supplier_response_request` in `app/services/brayman_supplier_estimate.py` (the 7 Oct 2026 page with the supplier's response boxes) |
| Acceptance case | Synthetic copy of Linda Bushel J1 (`tests/fixtures/construction_model/linda_j1_takeoff_fixture.py`). The real project was not read or changed. |

**Brayman calculates. The supplier prices. CalibraytAI connects the two.**

## One authority

The J1 mathematics in `docs/estimating-cases/2026/linda-bushel-pool-deck/takeoff/issue_j1.py` now lives in `app/services/deck_takeoff/` as the single platform authority. The case script stays as the historical generator of the 1 Oct 2026 issue. It is not called and was not changed.

| Calculation | Module |
|---|---|
| Curved deck area, side intersection, open pool edge, joist lengths, header chords | `geometry.py` |
| Board courses split at the pool apex, curve cuts measured at the long edge, ripped rows, corner remainder, lower deck, treads | `geometry.py` |
| Stock-length allocation with kerf; offcut and waste; refusal of a cut longer than any stock | `stock.py` |
| Guard and stair-rail chains, junctions, fascia runs, panel bays and posts | `railing.py` |
| Structural cuts, beams split at splice piers, blocking by bay, stringers, posts, stitch bolts, bearings, piers, connectors | `takeoff.py` |
| Manufacturer and installer facts (no defaults) | `product_facts.py` |
| Supplier request rows and issued manifest | `supplier_request.py` |
| Response import, matching, validation, evidence recording | `intake.py` |
| Write-once file custody (facts versions, issued requests, responses) | `storage.py` |

Existing engines are not changed: Concrete 1.0.0, Stair, 8-inch ICF, Wall Framing slices 1–2, Employment vs Entrepreneurship, `construction_measurement`, `unit_conversion`, and the estimate confirmation gates.

## Inputs

The takeoff reads the project's current stored construction model revision. Named dimensions, the first stair result, joist / stringer / beam / post / header members, pier supports, and two top-level records: `structural_specification` (the retained framing, recorded from the governing issue) and `finish_specification`. A missing fact refuses the takeoff and is listed. Nothing is filled.

Product facts are entered by Brayman as numbered versions. Every earlier version is kept.

## Statuses

Every line carries `CALCULATED`, `PRODUCT_DEPENDENT`, `FIELD_VERIFICATION_REQUIRED`, or `ENGINEERING_REQUIRED`, with each open fact and who can close it. A purchasing quantity is final only when the line is `CALCULATED`. The purchasing schedule is complete only when every requested line is final.

## Supplier request and return

1. Brayman downloads the request for one supplier account. The request identity and each line's key and signature are stored and written into hidden read-only fields.
2. **Form 2 (current, 14 Oct 2026, Joel's decision):** the supplier fills three boxes per material — SKU, unit cost, discount %. The Total column is printed "Calculated by Brayman"; it is not a field. Substitutions go under General notes as the original line number and the replacement SKU (the replacement is priced on that line). A line named in the notes is held as `SUBSTITUTION_REVIEW` and is never recorded from that response; any general notes block recording until a person ticks that they reviewed them (recorded as `notes_reviewed_by`). Price validity is still required. Rounding (approved 14 Oct): net unit cost to the cent, then × quantity. A PDF returned with blank totals (viewer did not run the scripts) imports normally; the server is the calculation authority. **Form 1 (historical):** requests issued earlier keep their stored PDF and their eight boxes (product / SKU, confirmed, unit price, discount, net price, availability, lead time, substitution notes). The manifest's `response_form` says which; a manifest without it is form 1. A form-2 request has its own request identity, so the same takeoff can be reissued on form 2.
3. Brayman imports the returned PDF, or types the answers in. Lines are matched by request, key, and signature. Another project's response is refused.
4. Recording appends supplier price evidence (and, for form 1 only, availability evidence) through the existing supplier catalogue services, only for lines whose material has a canonical identity in the catalogue. Earlier evidence stays.
5. Brayman approves or rejects a contractor cost through the existing `record_contractor_cost_approval` gate.

No step creates an estimate line, a costing snapshot, or a customer price.

## Catalogue identities (ADR-057, Proposed)

Revision `u1b2c3d4e5f6` adds `DECKING`, `FASCIA`, `RAILING`, `GATE`, `FOUNDATION`, `CONNECTOR`, `FASTENER`, and the unit `PKG`. Each purchasing line maps to a deterministic identity (`catalogue.py`), for example `CAL-PT-2X12-8`, `CAL-DECK-CAPCOMP-20`, `CAL-GATE-AL-BLACK-42IN`. An identity is created only when a person records supplier evidence for the line. A line whose identity needs a missing fact keeps its price on the response record. The migration is prepared and rehearsed, not applied: [../operations/takeoff-catalogue-migration-rollback.md](../operations/takeoff-catalogue-migration-rollback.md).

## Live form calculations

**Form 2 (no viewer dependency, 14 Oct 2026):** the PDF carries no JavaScript and no total fields, so any viewer that saves form fields works; Adobe Acrobat Reader is not required. CalibraytAI is the sole calculation authority: on import, net unit cost = round_to_cent(unit cost × (1 − discount / 100)) (half up), line total = quantity × net, **Recordable Quoted Total** (Joel, 14 Oct 2026) = sum of the line totals of complete, eligible lines only: valid SKU, valid unit cost, explicit discount (0% counts), a FINAL QUANTITY purchasing quantity, a purchasing unit, no unresolved substitution, matching request and line identity. Every other quoted line is listed as a partial or excluded quotation with its reason; its arithmetic value, if any, is shown separately as a provisional value and never added. It is not an approved cost; Brayman's cost approval is unchanged. The same rule runs on PDF import and hand entry (the hand-entry page previews it in the browser; the server recalculates). Historical form-1 requests get no form-2 totals. A blank discount is not zero and gives no total; 0 is a real zero discount; a quantity marked TBD has no total. Any total typed into a tampered PDF is ignored. If a returned PDF has no SKU, unit cost or discount on any line (for example a viewer that did not save the typed values), nothing is stored: the office sees a warning and the hand-entry page opens. Verified with files saved by Apple Preview (macOS 26.5.2) and by pdf.js 4.10.38 (Firefox's PDF engine); both kept every typed value and all 27 line identities (tests/fixtures/supplier_forms/).

**Form 1:** the supplier request PDF calculates in the form: the net price fills in once a unit price and a discount are entered, each line total is net × Brayman's quantity, and a read-only Total adds the line totals. A typed net is kept when either input is blank; a blank discount is never taken as zero. Adobe Acrobat Reader runs these calculations; Apple Preview does not. Import re-checks every figure. The hand-entry page runs the same arithmetic in the browser.

## Request labels

Every row is labelled `FINAL QUANTITY`, `CALCULATED — FIELD VERIFICATION BEFORE ORDERING`, `PRODUCT-DEPENDENT — NOT READY TO ORDER`, or `ENGINEERING-DEPENDENT — NOT READY TO ORDER`.

## Cutting policy

`cutting.offcut_reuse` is Brayman's decision: `within_use` keeps each use (joists, header, blocks, lower joists; upper, lower, treads) on its own sticks, as J1 did; `across_uses` lets offcuts serve other cuts of the same material. Until it is chosen the engine packs within each use and flags the line. See [../testing/deck-takeoff-j1-reconciliation.md](../testing/deck-takeoff-j1-reconciliation.md).

## J1 mapping

`tools/linda_j1_construction_model.py` maps the J1 generator into a construction model revision as a dry run, recording the generator and drawing SHA-256. Saving it to Linda's real project needs Joel's authorization.

## Known limits

- Identities for finish materials are created from recorded evidence, not from a reviewed seed list (ADR-057).
- The run rule supports a stair centred on the upper deck and a lower deck as wide as the stair.
- No structural adequacy, pier capacity, guard attachment, or pool-enclosure compliance is inferred.

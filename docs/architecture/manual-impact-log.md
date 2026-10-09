# CalibraytAI User Guide — Manual Impact log

| Attribute | Value |
|-----------|--------|
| Status | **FRAMEWORK / IMPACT CAPTURE.** Not the User Guide. D1 Hub Help, D3 office Help, D4 Field Help, and D5 Voice-with-Help are **IMPLEMENTED**; this log remains Manual Impact only. |
| Updated | 2026-10-09 |
| Governing record | [interactive-help-voice-and-user-manual-future-record.md](interactive-help-voice-and-user-manual-future-record.md) **OPEN / PARTIAL** — D1 Hub Help **IMPLEMENTED**; D3 office Help **IMPLEMENTED**; D4 Field Help **IMPLEMENTED**; D5 Voice-with-Help **IMPLEMENTED IN WORKING TREE**; User Guide **NOT IMPLEMENTED** |
| Framework | [calibraytai-v1-user-guide-framework.md](calibraytai-v1-user-guide-framework.md) **MANUAL FRAMEWORK: START NOW.** **Manual Audience Law** controlling. |
| Policy | **Append-only.** Newest entry first under Entries. Do not rewrite historical entries except to correct factual error (note the correction). |

This file is **not** the professional CALIBRAYTAI V1 USER GUIDE. It is a lightweight close-time capture so later Manual authoring has contractor-facing impact notes from the actual product.

Do **not** write final Manual prose here.
Do **not** capture screenshots against unfinished surfaces.
Do **not** implement Voice / office/Field Help / finished Manual from this file.

**Final authoring sequence** remains: remaining functional V1 → Contractor Language + UX E2E Audit → one User Help Content authority → User Guide from the finished product → procedure cross-check → final desktop/iPhone screenshots → Help → Voice → internal E2E → task-based UAT package → **give the completed Guide to Kevin and Ben (and already-recorded Ben’s father-in-law) BEFORE platform access** → allow Guide review → then platform access and realistic task-based UAT without coaching.

Kevin / Ben platform access: **NOT YET**.

V1 **not rescored** from this file.

---

## When to add an entry

Add one entry at each **material feature / slice close** that creates or changes a contractor-facing capability.

Do not backfill earlier slices from this recording. Capture begins with current development (SCH-C).

## Template (copy)

```markdown
### MANUAL IMPACT — <SLICE> (YYYY-MM-DD)

| Field | Content |
|-------|---------|
| Slice | |
| Product status at capture | |
| 1. What new contractor capability exists? | |
| 2. When would the contractor use it? | |
| 3. What workflow will the final Manual need to teach? | |
| 4. What contractor-facing terms must be used? | |
| 5. What screenshots / Print examples will eventually be needed? | |
| 6. What warnings / validation distinctions need explanation? | |
| 7. Desktop / iPhone / Print relevance | |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |
```

---

## Entries

### MANUAL IMPACT — Enter construction information (2026-10-09)

| Field | Content |
|-------|---------|
| Slice | The project page can save deck construction information as the next project-owned revision. |
| Product status at capture | Implemented and tested on isolated data. Not deployed. Official V1 remains **65% / 4 of 11**. Checklist step 8 stays open. |
| 1. What new contractor capability exists? | From the project, the contractor can enter the deck facts already known, see a blank length as missing, save revision 1, reopen it, correct it, and save the next revision. |
| 2. When would the contractor use it? | When the project does not yet have a construction model, or when a model saved from this page needs a correction, before using Add from calculation. |
| 3. What workflow will the final Manual need to teach? | Open the project, choose Enter construction information, enter the drawing status, measurement system, level, members, and supports, save, then open Add from calculation for a group that has no missing fact. |
| 4. What contractor-facing terms must be used? | Enter construction information. Update construction information. Drawing status. Measurement system. Level. Elevation. Member role. Member size. Length. Known count. Missing facts. Model revision. Save construction information. Save a new revision. Add from calculation. |
| 5. What screenshots / Print examples will eventually be needed? | The project action, the entry page with one complete member and one member missing a length, and the saved revision. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | A saved model is not a calculation-ready group. A blank length stays missing and cannot be offered. This page does not add an estimate line or a price. A model that already contains facts this page does not edit cannot be replaced here. |
| 7. Desktop / iPhone / Print relevance | Office project page on desktop. Not a Field or iPhone change. Print is unchanged because this page does not create an estimate line. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Stored member count from a project model (2026-10-09)

| Field | Content |
|-------|---------|
| Slice | Add from calculation can offer one stored member group from the project’s current construction-model revision. |
| Product status at capture | Implemented and tested on isolated data. Not deployed. Official V1 remains **65% / 4 of 11**. Checklist step 8 stays open. |
| 1. What new contractor capability exists? | On an estimate, the contractor can see the stored member groups for the project’s current model and send one complete group to the existing calculation review. Confirming that review adds one ordinary estimate line for the stored count. |
| 2. When would the contractor use it? | After a construction model has been saved on the project, while building the estimate, and only for a group whose required facts are already stored. |
| 3. What workflow will the final Manual need to teach? | Open the estimate, open Add from calculation, read the role, size, count, missing facts, and model revision, offer one eligible group, then confirm the line. A later model revision does not change a line already confirmed. |
| 4. What contractor-facing terms must be used? | Member role. Member size. Known count. Missing facts. Model revision. Add to estimate. |
| 5. What screenshots / Print examples will eventually be needed? | The Add from calculation page with one eligible group and one group that has a missing fact, then the estimate line after confirmation. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | A member count is not a material takeoff. No length, stock length, waste, labour, or price is invented. A missing fact cannot be offered. Offering the same group again does not add a second line. |
| 7. Desktop / iPhone / Print relevance | Office estimate page on desktop. Not a Field or iPhone change. The printed customer estimate is unchanged until a line is confirmed. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Construction intelligence (2026-10-08)

| Field | Content |
|-------|---------|
| Slice | Stored area, sheet size, coverage, and service counts become quantities. The cost path stays separate. |
| Product status at capture | Implemented and tested on scratch data. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | A known wall or roof rectangle can become a square-foot quantity, and a named sheet size can become an exact sheet count. A stored fixture count can go to a subcontractor with the price still blank. |
| 2. When would the contractor use it? | When the plan already stores the length and width, the sheet size or coverage, or the fixture, device, or equipment count. |
| 3. What workflow will the final Manual need to teach? | Read the square feet first. Read sheets or bundles only when the product size is stored. Send plumbing, electrical, and HVAC as a quote with the count visible and the allowance blank. |
| 4. What contractor-facing terms must be used? | Area. Sheet. Coverage. Fixture count. Quote. Allowance. Unresolved. |
| 5. What screenshots / Print examples will eventually be needed? | A supplier request with an exact OSB sheet count, and a separate subcontract request with a fixture count and a blank allowance. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | Pitch is not applied. Openings are not deducted. A missing sheet size does not become a sheet count. A subcontract count is not a material order. |
| 7. Desktop / iPhone / Print relevance | Office quantity result, the printed supplier request, and the printed subcontract request. Not a Field or iPhone change. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Governed footing volume (2026-10-08)

| Field | Content |
|-------|---------|
| Slice | A footing with stored length, width, and thickness becomes a concrete volume. |
| Product status at capture | Implemented and tested on scratch data. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | A complete footing can be requested as concrete in cubic metres. The cubic yards stay in the note. An incomplete footing stays marked unresolved. |
| 2. When would the contractor use it? | When the footing length, width, and thickness are already stored, on the same pass as a slab or an ICF wall. |
| 3. What workflow will the final Manual need to teach? | Read each footing separately. Leave a missing thickness unresolved. Confirm the concrete price is per cubic metre. Leave mix design and labour hours open. |
| 4. What contractor-facing terms must be used? | Footing. Concrete. Cubic yards. Cubic metres. Unresolved. |
| 5. What screenshots / Print examples will eventually be needed? | A supplier request with a complete footing in cubic metres and an unresolved footing beside it. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | A pier or footing location is not a footing size. No waste or truck count is added. Two footings are not combined. |
| 7. Desktop / iPhone / Print relevance | Office quantity result and the printed supplier request. Not a Field or iPhone change. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Canonical concrete material (2026-10-08)

| Field | Content |
|-------|---------|
| Slice | One concrete material identity so a known concrete volume can be requested. |
| Product status at capture | Implemented and tested on scratch data. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | A dimensioned slab can become a concrete requirement in cubic metres. The cubic yards stay in the note. The same concrete identity can be used for ICF concrete. |
| 2. When would the contractor use it? | When asking a supplier to price concrete for a slab whose length, width, and thickness are already stored. |
| 3. What workflow will the final Manual need to teach? | Read the cubic yards. Read the cubic metres. Send the request with product, SKU, and price blank. Approve the supplier price per cubic metre before it reaches the estimate. |
| 4. What contractor-facing terms must be used? | Concrete. Cubic yards. Cubic metres. |
| 5. What screenshots / Print examples will eventually be needed? | A supplier request that shows concrete at 2.832 m³ and keeps the cubic yards in the note. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | The requirement is 2.8317 cubic metres. The request shows 2.832. Neither number is a truck count. The concrete identity is not a mix design or a supplier product. |
| 7. Desktop / iPhone / Print relevance | Office material catalogue, the supplier request, and the estimate. Not a Field or iPhone change. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Next coherent quantity batch (2026-10-08)

| Field | Content |
|-------|---------|
| Slice | Use stored member counts, support locations, and a fully dimensioned slab in the common quantity result. |
| Product status at capture | Implemented and tested on scratch data. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | A stored stair member can be counted. A stored pier location can be seen without becoming an order. A slab with length, width, and thickness can be requested in cubic metres. A riser count stays a stair fact. |
| 2. When would the contractor use it? | On the first quantity pass, when the construction model already stores those members or the slab dimensions are already entered. |
| 3. What workflow will the final Manual need to teach? | Read the known counts. Leave a pier as locations until the pier itself is known. Read the slab in cubic metres and keep the cubic yards. Leave roofing, windows, and a footing volume marked unresolved. |
| 4. What contractor-facing terms must be used? | Member count. Locations. Cubic yards. Cubic metres. Unresolved. Quote or allowance. |
| 5. What screenshots / Print examples will eventually be needed? | A supplier request that shows a stair member count, a slab in cubic metres, and an unresolved roofing line. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | A riser count is not a lumber order. A pier location count is not a pier order. A slab has no concrete catalogue identity yet. A footing still has no volume. No waste or labour rate is added. |
| 7. Desktop / iPhone / Print relevance | Office quantity result and the printed supplier request. Not a Field or iPhone change. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Construction unit and purchasing unit (2026-10-08)

| Field | Content |
|-------|---------|
| Slice | Keep the construction measurement and show the purchasing quantity when a conversion exists. |
| Product status at capture | Implemented and tested on scratch data. Official V1 remains **65% / 4 of 11**. Not deployed. |
| 1. What new contractor capability exists? | A concrete volume calculated in cubic yards can be requested and costed in cubic metres. The yard quantity stays visible. A sheet area with no sheet size stays unresolved. |
| 2. When would the contractor use it? | When a supplier orders concrete in cubic metres and the plan was measured in feet and inches. |
| 3. What workflow will the final Manual need to teach? | Read the construction volume. Read the purchasing quantity. Confirm the supplier price is per cubic metre. Leave an unknown package size unresolved. |
| 4. What contractor-facing terms must be used? | Construction quantity. Purchasing quantity. Cubic yards. Cubic metres. Unresolved. |
| 5. What screenshots / Print examples will eventually be needed? | A supplier request that shows 45.307 m³ and the construction volume 59.259 yd³. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | The two quantities are different numbers. The request does not add waste or a truck count. An unknown sheet size does not become a sheet count. |
| 7. Desktop / iPhone / Print relevance | Office estimate and the printed supplier request. Not a Field or iPhone change. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Common estimating quantity contract (2026-10-08)

| Field | Content |
|-------|---------|
| Slice | One quantity result for a plan that can contain more than one scope. |
| Product status at capture | Implemented and tested on scratch data. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | A plan can produce member counts and an ICF form count together, mark unresolved scopes, and keep plumbing, electrical, and HVAC as quotes or allowances. |
| 2. When would the contractor use it? | While reviewing the first quantity pass for a project that is more than one trade. |
| 3. What workflow will the final Manual need to teach? | Review the known counts. Leave unresolved scopes marked. Send the material request. Treat plumbing, electrical, and HVAC as quotes or allowances. |
| 4. What contractor-facing terms must be used? | Member count. Form count. Concrete volume. Unresolved. Quote or allowance. |
| 5. What screenshots / Print examples will eventually be needed? | A supplier request that includes a known count and an unresolved scope, with subcontract trades absent from that sheet. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | A missing rule does not stop the known quantities. A member count is not a purchase quantity. A concrete volume is not a truck count. Labour hours wait for a production assumption. |
| 7. Desktop / iPhone / Print relevance | Office estimate and the printed supplier request. Not a Field or iPhone change. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Foundation vertical slice (2026-10-08)

| Field | Content |
|-------|---------|
| Slice | Foundation quantities on the existing estimate path. |
| Product status at capture | Implemented and tested on scratch data. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | An ICF wall with a net area and corner counts can produce a standard-form count, a concrete volume, and a supplier request. The form count can become an estimate line after a contractor-confirmed price. |
| 2. When would the contractor use it? | While estimating an ICF foundation, before asking a supplier for a form price. |
| 3. What workflow will the final Manual need to teach? | Enter the wall area and both corner counts. Review the form count and the concrete volume separately. Leave reinforcement, membrane coverage, footings, and slabs marked until those facts or rules exist. Approve the form price before it reaches the estimate. |
| 4. What contractor-facing terms must be used? | Net wall area. Corner count. Form count. Concrete volume. Unresolved. |
| 5. What screenshots / Print examples will eventually be needed? | The supplier request with the form count, the concrete volume, and one unresolved wall. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | A form count is not a package. A concrete volume is not a truck count. Labour hours wait for a contractor production assumption. |
| 7. Desktop / iPhone / Print relevance | Office estimate and the printed supplier request. Not a Field or iPhone change. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Deck and framing vertical slice (2026-10-08)

| Field | Content |
|-------|---------|
| Slice | First deck and framing quantity handoff into the existing estimate chain. |
| Product status at capture | Implemented and tested on scratch data. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | A stored deck member count can become a material requirement, a supplier request line, and an estimate line. A missing length stays marked and the other members continue. |
| 2. When would the contractor use it? | While turning a deck model into an internal estimate, before asking a supplier for a price. |
| 3. What workflow will the final Manual need to teach? | Confirm the member facts, review the count, send the supplier request, approve the contractor cost, and keep the line. Leave labour hours blank until a production assumption is confirmed. |
| 4. What contractor-facing terms must be used? | Member count. Supplied length. Unresolved. Contractor-confirmed price. Framing. |
| 5. What screenshots / Print examples will eventually be needed? | The supplier request with one known count and one unresolved member. Do not capture a screenshot in this slice. |
| 6. What warnings / validation distinctions need explanation? | A member count is not a purchase quantity. No stock length or waste is added. Labour hours wait for a contractor production assumption. |
| 7. Desktop / iPhone / Print relevance | Office estimate and the printed supplier request. Not a Field or iPhone change. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Brayman V1 interim contract presentation (2026-10-07)

| Field | Content |
|-------|---------|
| Slice | Contract presentation for the existing Ontario interim package. |
| Product status at capture | Implemented and tested on scratch data. Not deployed. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | Open contract shows the Brayman V1 interim contract, with the parties, project, amount, package, version, effective date, and signature lines. |
| 2. When would the contractor use it? | After Review contract generates the contract. |
| 3. What workflow will the final Manual need to teach? | Generate, open the contract, and read it as generated. A signature is a later step. |
| 4. What contractor-facing terms must be used? | Brayman V1 Interim Contract. Contract / Agreement. Generated. Owner. Contractor. |
| 5. What screenshots / Print examples will eventually be needed? | The opened contract. Do not capture it as a draft or as counsel-approved. |
| 6. What warnings / validation distinctions need explanation? | The contract says it is generated and not signed. It says external counsel has not reviewed the package. |
| 7. Desktop / iPhone / Print relevance | Desktop review. The contract opens as a PDF. |
| Do not | Call it a draft, a presentation master, or counsel-approved. Send a signing link from generation. |

### MANUAL IMPACT — Brayman V1 interim Ontario contract (2026-10-07)

| Field | Content |
|-------|---------|
| Slice | Ontario contract path. Existing contract engine. |
| Product status at capture | Implemented and tested on scratch data. Not deployed. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | An Ontario project can use the active Brayman V1 interim contract package and generate a contract for review. |
| 2. When would the contractor use it? | After the estimate is issued and locked and the proposal is issued or accepted. |
| 3. What workflow will the final Manual need to teach? | Open the project, read the package, version, effective date, and status, open Review contract, generate, and read the snapshot. |
| 4. What contractor-facing terms must be used? | Ontario. Brayman V1 Interim Contract. Version. Effective date. Status Active. Contract snapshot. Generated — not signed. |
| 5. What screenshots / Print examples will eventually be needed? | The project Contract section and the Review contract page after generation. Do not capture them as counsel-approved. |
| 6. What warnings / validation distinctions need explanation? | Generating does not sign the contract and does not send a signing link. Counsel approved appears only when that approval exists. No active package, an unresolved location, or missing contract data still blocks generation. |
| 7. Desktop / iPhone / Print relevance | Desktop review. The generated file can be downloaded. It is not a signed contract. |
| Do not | Call the package counsel-approved. Bypass the block. Send a signing link from generation. |

### MANUAL IMPACT — V1-10 operating pack (2026-10-07)

| Field | Content |
|-------|---------|
| Slice | V1-10 operator and recovery pack. Documentation only. |
| Product status at capture | Written. Not a product change. Not deployed. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | A written Mac-office guide, a one-page first day, and a backup sheet Joel runs. |
| 2. When would the contractor use it? | Before the first real project is typed in, and when the office misbehaves. |
| 3. What workflow will the final Manual need to teach? | Sign in on the Mac office, start a project, price, leave the contract blocked, capture field notes, and call Joel. |
| 4. What contractor-facing terms must be used? | Office sign in. Approve all costing. CONSTRUCTION ESTIMATE. Production contract unavailable. Supplier Estimate Request. |
| 5. What screenshots / Print examples will eventually be needed? | None in this pack. The pages are the print. |
| 6. What warnings / validation distinctions need explanation? | Family 05 is not a contract. The website is not the Mac office. The supplier does not approve cost. |
| 7. Desktop / iPhone / Print relevance | Desktop office. Field capture is described. The first-day sheet and the backup sheet print on their own. |
| Do not | Final Manual prose in this log. A rescore. A deploy. |

### MANUAL IMPACT — Supplier estimate request from the supplier review (2026-10-07)

| Field | Content |
|-------|---------|
| Slice | Supplier Package review download. |
| Product status at capture | **IMPLEMENTED / TESTED** in the working tree. Not committed. Not deployed. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | From a project's supplier review, download the Brayman supplier estimate request for that job and that supplier. |
| 2. When would the contractor use it? | When the project has material requirements and a supplier is selected. |
| 3. What workflow will the final Manual need to teach? | Open the supplier review. Choose the supplier. Download Supplier Estimate Request. The supplier fills price and code. |
| 4. What contractor-facing terms must be used? | Supplier Estimate Request. The project name and address. Qty. Unit price. Line price. Code. |
| 5. What screenshots / Print examples will eventually be needed? | The supplier review with the download, and the resulting page for a job other than Bushel. |
| 6. What warnings / validation distinctions need explanation? | A stored SKU or price is not printed on the request. The supplier fills those boxes. |
| 7. Desktop / iPhone / Print relevance | Office download, then print or email. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Supplier estimate request on the Brayman page (2026-10-07)

| Field | Content |
|-------|---------|
| Slice | Checklist step 8. Linda Bushel supplier estimate request. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | A one-page Brayman Construction sheet Darcy can price. It matches the approved cost-request documents. |
| 2. When would the contractor use it? | When asking BMR Winchester for a price before the purchase quantities are complete. |
| 3. What workflow will the final Manual need to teach? | Send the sheet. Darcy fills unit price, line price, BMR code, and a note. Brayman still confirms any quantity marked TBD. |
| 4. What contractor-facing terms must be used? | Supplier estimate request. Qty. Unit price. Line price. BMR code. TBD. A blank is not zero. |
| 5. What screenshots / Print examples will eventually be needed? | This sheet beside the approved Geleynse cost request. |
| 6. What warnings / validation distinctions need explanation? | TBD is not a purchase quantity and not zero. No price or SKU is filled in by Brayman. |
| 7. Desktop / iPhone / Print relevance | Print and email. No new screen. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Bushel supplier pricing request (2026-10-07)

| Field | Content |
|-------|---------|
| Slice | Checklist step 8. Manual supplier pricing request for Linda Bushel. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. No migration. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | A fillable PDF Darcy can complete for BMR Winchester. It shows what is known, what is TBD, what BMR must price, and what Brayman must still confirm. |
| 2. When would the contractor use it? | Before a supplier price exists, when the project is still incomplete. |
| 3. What workflow will the final Manual need to teach? | Send the PDF. Darcy fills product, SKU, availability, and contractor price. Brayman answers the separate project questions. Brayman later approves cost. |
| 4. What contractor-facing terms must be used? | Known count. Purchase quantity. TBD. Public / list price. Contractor price. Brayman information required. |
| 5. What screenshots / Print examples will eventually be needed? | The five-page Bushel request, after the wording is stable. |
| 6. What warnings / validation distinctions need explanation? | A member count is not a purchase quantity. A public price is not the contractor price. Darcy does not answer Brayman's questions and does not approve Brayman's cost. |
| 7. Desktop / iPhone / Print relevance | Print and email PDF. No new screen. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Bushel governed member fact completion (2026-10-06)

| Field | Content |
|-------|---------|
| Slice | Checklist step 8. Bushel proving model and the canonical material seed. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. No migration. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | The governed tread name "Two 5/4 x 6 boards per tread" is a supplier-neutral canonical identity, `CAL-LUM-5-4X6`. The readiness read can name it. It still has no quantity, stock length, supplier product, or price. |
| 2. When would the contractor use it? | When reading what Bushel already decided, before asking a supplier for a product and a price. |
| 3. What workflow will the final Manual need to teach? | A known material name is not a purchase quantity. Missing member size and length stay missing and do not hide the known name. |
| 4. What contractor-facing terms must be used? | Known project fact. Complete purchase requirement. Canonical material. Contractor input. Supplier product. Supplier pricing. |
| 5. What screenshots / Print examples will eventually be needed? | None yet. This slice does not add a screen or a supplier request. |
| 6. What warnings / validation distinctions need explanation? | 29 Sep lumber sizes are not member facts. "Two boards per tread" is not a counted purchase. The Veranda kit is named and is not in the lumber catalogue. |
| 7. Desktop / iPhone / Print relevance | No new desktop, iPhone, or print surface. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Costing review contractor-cost provenance (2026-10-06)

| Field | Content |
|-------|---------|
| Slice | Checklist step 8. Existing costing review. Frozen contractor-cost citation. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. No migration. Official V1 remains **65% / 4 of 11**. |
| 1. What new contractor capability exists? | An approved costing review can show why a frozen cost is there: the supplier, product, SKU, price class, evidence, and Brayman's approval, with the amount frozen on that snapshot. |
| 2. When would the contractor use it? | When reviewing an estimate version whose costing already froze an approved contractor cost. |
| 3. What workflow will the final Manual need to teach? | Open the estimate version. Read Frozen snapshot provenance. The supplier names where the price came from. Brayman is the approver. A later supplier price does not replace the frozen amount. |
| 4. What contractor-facing terms must be used? | Source: approved contractor cost. Supplier. Product. SKU. Price class. Evidence. Approval. Approved by. Effective dates. Frozen amount. |
| 5. What screenshots / Print examples will eventually be needed? | The existing Costing review section with one approved contractor cost and one ordinary custom line. Not captured here as a finished example. |
| 6. What warnings / validation distinctions need explanation? | A library cost, assembly, custom line, allowance, or override does not show supplier provenance. A public list price is not an approved contractor cost. Viewing the review does not change the estimate. |
| 7. Desktop / iPhone / Print relevance | Office desktop estimate version. No new page. No print sheet was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — ICF wall work-element binding (2026-10-04)

| Field | Content |
|-------|---------|
| Slice | Checklist step 8. First work-element binding. Baseline `ICF` → `icf_wall`. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. Migration `n4a5b6c7d8e9` is not applied to the Mac primary or the hosted database. |
| 1. What new contractor capability exists? | Continue setup can open the existing ICF wall calculation when the confirmed work is ICF wall and Our crew, and the project already has one estimate. |
| 2. When would the contractor use it? | After confirming ICF wall as Our crew, when the estimate exists and the wall measurements are still to be entered. |
| 3. What workflow will the final Manual need to teach? | Confirm ICF wall as Our crew. Open the existing ICF wall page. Enter the measured wall. Review the result. Confirm the quantity on the existing estimate gate. Site, foundation, and structure do not open a calculation. Subcontracted ICF wall does not open a crew calculation. |
| 4. What contractor-facing terms must be used? | ICF wall. Our crew. Subcontractor. A governed ICF wall calculation is available. Open ICF wall calculation. |
| 5. What screenshots / Print examples will eventually be needed? | Continue setup for Our-crew ICF wall, and the existing ICF wall quantities page. Not captured here as a finished example. |
| 6. What warnings / validation distinctions need explanation? | Choosing ICF wall does not calculate a quantity. The wall page does not add an estimate line. Foundation is not ICF wall. A subcontracted package requires no crew calculation. |
| 7. Desktop / iPhone / Print relevance | Office desktop Continue setup and the existing ICF wall page. No print sheet was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Bearing annotation (2026-10-03)

| Field | Content |
|-------|---------|
| Slice | Construction Model slice 18. Bearing annotation. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. The drawing set stays **OPEN / NOT COMPLETE**. The generic fixture set is still not a crew set. |
| 1. What new contractor capability exists? | The bearing length sits beside the joint, with the members and the relationship it names. The contact line stays on the post and the beam. |
| 2. When would the contractor use it? | When reading the post-and-beam detail, the section, and the stair seats. |
| 3. What workflow will the final Manual need to teach? | The words can move on the sheet. The contact does not move. Several equal bearings share one note and still name each relationship. |
| 4. What contractor-facing terms must be used? | Bearing. Bears on. Geometry not supplied. |
| 5. What screenshots / Print examples will eventually be needed? | An 11×17 post-and-beam detail with the bearing note in the margin and the contact visible. Not captured here as a finished example. |
| 6. What warnings / validation distinctions need explanation? | A leader is omitted when it would cross an unrelated member. A connector without a shape still says geometry not supplied. |
| 7. Desktop / iPhone / Print relevance | Print on 11×17. No screen was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Construction model blocking (2026-10-03)

| Field | Content |
|-------|---------|
| Slice | Construction Model slice 17. Blocking. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. The drawing set stays **OPEN / NOT COMPLETE**. The generic fixture set is still not a crew set. |
| 1. What new contractor capability exists? | Blocking is a member on the framing plan, on the section that cuts it, and in the member schedule, with the joist or rim it is fastened to. |
| 2. When would the contractor use it? | When laying out solid blocking on the two beam lines of this deck. |
| 3. What workflow will the final Manual need to teach? | Blocking appears only when it was supplied. The section shows the row the cut hits. A missing piece is not filled in. |
| 4. What contractor-facing terms must be used? | Blocking. Fastened to. 2x8. Geometry not supplied. |
| 5. What screenshots / Print examples will eventually be needed? | An 11×17 framing plan with the blocking on the beam lines, and section A with the front row between the joists. Not captured here as a finished example. |
| 6. What warnings / validation distinctions need explanation? | A ledger is not drawn for this freestanding deck. A connector without a shape still says geometry not supplied. |
| 7. Desktop / iPhone / Print relevance | Print on 11×17. No screen was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Construction drawing annotation layout (2026-10-03)

| Field | Content |
|-------|---------|
| Slice | Construction Model slice 16. Drawing annotation layout. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. The drawing set stays **OPEN / NOT COMPLETE**. The generic fixture set is still not a crew set. |
| 1. What new contractor capability exists? | Connector notes sit beside the members instead of on top of them. A plate still shows its shape. A connector without a shape still says geometry not supplied. |
| 2. When would the contractor use it? | When reading the framing plan, the elevations, the section, and the post-and-beam detail. |
| 3. What workflow will the final Manual need to teach? | The note can move on the sheet. The member does not move. If the connector shape was not supplied, the sheet says so and does not draw one. |
| 4. What contractor-facing terms must be used? | Geometry supplied. Geometry not supplied. Pier depth. Baluster spacing. You need to provide this information. |
| 5. What screenshots / Print examples will eventually be needed? | An 11×17 framing plan with the connector note in the margin, and a post-and-beam detail with the plate note beside the plate. Not captured here as a finished example. |
| 6. What warnings / validation distinctions need explanation? | A leader is omitted when every route would cut through another member. The note stays. Geometry not supplied is not a finished connector. |
| 7. Desktop / iPhone / Print relevance | Print on 11×17. No screen was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Complete generic construction drawing fixture (2026-10-02)

| Field | Content |
|-------|---------|
| Slice | Construction Model slice 15. Complete generic fixture data and a stair riser-count field. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. The drawing set stays **OPEN / NOT COMPLETE**. The generic fixture set is still not a crew set. |
| 1. What new contractor capability exists? | A stair sheet can print a riser count that was supplied with the stair. A foundation plan can print front-to-back pier spacing. A side elevation can print guard height. A section can print the height from grade to the decking. A guard detail can name a latch without drawing one. |
| 2. When would the contractor use it? | When reading the generic deck set: the foundation plan, the framing plan, the side elevation, the stair, section A, the guard detail, and the schedule. |
| 3. What workflow will the final Manual need to teach? | The count, the bearings, and the dimensions come from the construction model. If a connector was named and no shape was supplied, the sheet says geometry not supplied. A dimension that has no clear place on the sheet stays on the schedule. |
| 4. What contractor-facing terms must be used? | Riser count. Pier spacing. Guard height. Section height. Stair opening. Geometry not supplied. Fixture data. You need to provide this information. |
| 5. What screenshots / Print examples will eventually be needed? | An 11×17 foundation plan with the pier spacing, a side elevation with the guard height, a section with the section height, and a guard detail that says geometry not supplied. Not captured here as a finished example. |
| 6. What warnings / validation distinctions need explanation? | The drawing does not calculate the riser count. A latch name is not a hinge. Pier depth and baluster spacing on the schedule are not the same as a dimension on the elevation. The schedule is not an estimate. |
| 7. Desktop / iPhone / Print relevance | Print on 11×17. No screen was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Governed connector geometry (2026-10-02)

| Field | Content |
|-------|---------|
| Slice | Construction Model slice 14. Governed connector geometry. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. The drawing set stays **OPEN / NOT COMPLETE**. The generic fixture set is still not a crew set. |
| 1. What new contractor capability exists? | A connection detail can show a plate, a thickness, a bolt diameter, and fastener locations when those were supplied. A connector name with a fastener and a quantity stays a note. |
| 2. When would the contractor use it? | When reading a post-and-beam detail, a section through that connection, or the connection schedule. |
| 3. What workflow will the final Manual need to teach? | The connector shape comes from the construction model and stays on the relationship it serves. If the geometry was not supplied, the sheet says geometry not supplied. It does not draw a typical connector. |
| 4. What contractor-facing terms must be used? | Geometry supplied. Geometry not supplied. Plate. Bolt. You need to provide this information. |
| 5. What screenshots / Print examples will eventually be needed? | An 11×17 post-and-beam detail with the supplied plate, and a stringer detail that says geometry not supplied. Not captured here as a finished example. |
| 6. What warnings / validation distinctions need explanation? | Fastener quantity does not place bolts. A product name does not become a shape. Uncertainty on the connector stays uncertainty. The schedule is not an estimate. |
| 7. Desktop / iPhone / Print relevance | Print on 11×17. No screen was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Drawing references and schedule presentation (2026-10-02)

| Field | Content |
|-------|---------|
| Slice | Construction Model slice 13. Drawing references and schedule / callout presentation. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. The drawing set stays **OPEN / NOT COMPLETE**. The generic fixture set is still not a crew set. |
| 1. What new contractor capability exists? | A plan can show a section cut and a detail reference that name the sheet they go to. Grouped members can share one callout that still names those members. The schedule columns line up, and a relationship names one bearing. A sheet that is missing a required connection is marked NOT ISSUED. The set includes a drawing index. |
| 2. When would the contractor use it? | When reading a deck plan set: the plans, the elevations, the schedules, and the index. |
| 3. What workflow will the final Manual need to teach? | The marks and the schedule come from the construction model and the sheet set. A missing connection stays missing. NOT ISSUED means that sheet is not a finished detail. The schedule does not price the work. |
| 4. What contractor-facing terms must be used? | See sheet. Detail. Section. Member schedule. Bearing supplied. Bearing not supplied. Not issued. You need to provide this information. |
| 5. What screenshots / Print examples will eventually be needed? | An 11×17 framing plan with a section cut and a detail bubble, a schedule page, an index, and a detail marked NOT ISSUED. Not captured here as a finished example. |
| 6. What warnings / validation distinctions need explanation? | A callout that cannot be given a clear leader is not given a crossing leader. A missing bearing is named for that pair. A missing connection is not invented. Generated sheets and unresolved sheets are marked differently. |
| 7. Desktop / iPhone / Print relevance | Print on 11×17. No screen was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Construction relationships and bearing (2026-10-02)

| Field | Content |
|-------|---------|
| Slice | Construction Model slice 11. Construction relationships and connection geometry. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. The drawing set stays **OPEN / NOT COMPLETE**. The stringer/tread and post/beam details on the generic fixture show the supplied bearing. The whole set is not a crew set. |
| 1. What new contractor capability exists? | A drawing can show a supplied bearing between two members, such as a stringer and a tread or a post and a beam. A connection stays a note when only the connector name and fasteners were supplied. |
| 2. When would the contractor use it? | When reading a stair, a post-and-beam detail, a section, or a relationship line on the construction schedule. |
| 3. What workflow will the final Manual need to teach? | The bearing comes from the construction model. If the stated bearing does not sit on both members, the drawing is refused. A missing bearing or a missing connector shape is named. It is not drawn as a guess. |
| 4. What contractor-facing terms must be used? | Bears on. Supports. Bearing. Connection. You need to provide this information. |
| 5. What screenshots / Print examples will eventually be needed? | An 11×17 stair with the seats, a stringer-and-tread detail, and a post-and-beam detail. Not captured here as a finished example. |
| 6. What warnings / validation distinctions need explanation? | A relationship is stored only when it is supplied. Members that happen to be near each other are not joined. A product name does not become a connector shape. Uncertainty on a relationship stays uncertainty. The schedule is not an estimate. |
| 7. Desktop / iPhone / Print relevance | Print on 11×17. No screen was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — Construction details and schedules (2026-10-02)

| Field | Content |
|-------|---------|
| Slice | Construction Model slice 10. Buildable details and construction schedules. |
| Product status at capture | **IMPLEMENTED / TESTED**. Not deployed. The drawing set stays **OPEN / NOT COMPLETE**. Visual acceptance is not passed. |
| 1. What new contractor capability exists? | A supplied member section, including a sloped board, can be drawn. Equivalent boards group on a construction schedule with a quantity and a length. Connections that are in the model appear on a hardware schedule. |
| 2. When would the contractor use it? | When reading a deck plan set: the stair, the post and beam, the section, and the schedules. |
| 3. What workflow will the final Manual need to teach? | The drawing comes from the construction model. A missing section size or a missing connection is named. The schedule counts like members. It does not price them. |
| 4. What contractor-facing terms must be used? | Member schedule. Connection schedule. Material schedule. Detail. Section. You need to provide this information. |
| 5. What screenshots / Print examples will eventually be needed? | An 11×17 stair, a post-and-beam detail, a section, and a grouped schedule. Not captured here as a finished example. The fixture set is not a crew set. |
| 6. What warnings / validation distinctions need explanation? | A missing profile is named and is not replaced with a generic shape. A missing connection is named. Different lengths are not averaged. The schedule is not an estimate. |
| 7. Desktop / iPhone / Print relevance | Print on 11×17. No screen was added. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — ICF wall quantities (2026-10-01)

| Field | Content |
|-------|---------|
| Slice | Estimate path for 8-inch ICF form count and concrete. |
| Product status at capture | **CLOSED — LIVE VERIFIED**. Product SHA `ff9d6791c4bb16ef50d42a9ca71af2a1d6bc051b`. Deploy `dep-dav9uk97lnhs73bj35pg`. |
| 1. What new contractor capability exists? | From Add from calculation, ICF wall quantities accepts the measured wall and shows form count and concrete. Review opens the existing confirmation. Nothing is added until that confirmation. |
| 2. When would the contractor use it? | When an estimate needs 8-inch ICF forms and concrete from a net wall area and corner counts. |
| 3. What workflow will the final Manual need to teach? | Open the estimate’s Add from calculation, choose ICF wall quantities, enter the manufacturer, area, and corners, calculate, then review and confirm only the quantities that have a company cost. |
| 4. What contractor-facing terms must be used? | ICF wall quantities. Net wall area. Enter 0 when the wall has none. Labour-hour allowance. Review on this estimate. |
| 5. What screenshots / Print examples will eventually be needed? | The input page and the review that still says nothing is added. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | Corner counts are required, including zero. A corner the profile does not describe is not calculated. Labour hours are an allowance and are not priced. Package quantity is not invented. |
| 7. Desktop / iPhone / Print relevance | Checked in the office shell on a temporary local database. The known 11px overflow at 390px was not repaired. No print sheet was created. |
| Do not | Final Manual prose. Unstable screenshots. A public ICF calculator. A second labour rate. |

### MANUAL IMPACT — Live acceptance walk (2026-10-01)

| Field | Content |
|-------|---------|
| Slice | Start Project, Guided Project Setup, and Plan Generation live acceptance. |
| Product status at capture | **CLOSED — LIVE VERIFIED** on deploy `dep-dav6kt8jo6nc73fpglg0`. |
| 1. What new contractor capability exists? | Start New Project opens Continue setup. Continue setup names the next existing page. Build Drawings can make a dimensioned-plan candidate, and Use adds it as a project drawing. |
| 2. When would the contractor use it? | When opening a job, filling the first missing fact, or making a dimensioned plan from entered members. |
| 3. What workflow will the final Manual need to teach? | Start the project, complete location, choose whether drawings are required, upload or build a drawing, confirm scope, then open or create the estimate. A generated sheet is not a project drawing until Use. A calculated quantity is not an estimate line until it is confirmed. |
| 4. What contractor-facing terms must be used? | Start New Project. Continue setup. Build Drawings. Use. Return to setup. Choose an estimate. |
| 5. What screenshots / Print examples will eventually be needed? | Continue setup, the drawing choice, Build Drawings, and the estimate handoff on a desktop and a phone. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | An unsupported drawing type is refused. An incomplete sheet is refused. A candidate is not a current drawing. Several estimates are not chosen automatically. |
| 7. Desktop / iPhone / Print relevance | Checked at 1280, 520, and 390. The known 11px office-shell overflow at 390px remains. No print sheet was created. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — SNP-6 (2026-10-01)

| Field | Content |
|-------|---------|
| Slice | SNP-6. Continue setup into the ordinary estimate. |
| Product status at capture | GUIDED PROJECT SETUP **IMPLEMENTED**. ESTIMATE HANDOFF **IMPLEMENTED**. MAPPER HANDOFF **VERIFIED / PRESERVED**. This slice **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Not deployed. |
| 1. What new contractor capability exists? | Continue setup opens the estimate when there is one, the project's estimate list when there are several, and Create estimate when there is none. |
| 2. When would the contractor use it? | After the client, location, drawings, and scope are in place, and the next fact is the estimate. |
| 3. What workflow will the final Manual need to teach? | From Continue setup, open the estimate, choose one from the project list, or create one and come back. A calculated quantity is added only after the contractor chooses a company cost or reusable work and confirms it. |
| 4. What contractor-facing terms must be used? | Continue to the estimate. Choose an estimate. Create estimate. Add to estimate. |
| 5. What screenshots / Print examples will eventually be needed? | Continue setup for one estimate, several estimates, and no estimate, on a desktop and on a phone. The existing calculation review after a quantity is added. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | Continue setup does not price the job and does not pick an estimate when several exist. A loaded calculation does not add a line until it is confirmed. |
| 7. Desktop / iPhone / Print relevance | Desktop and phone-width Continue setup. The estimate and the mapper keep their own layout. No print sheet is created. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — SNP-4 (2026-10-01)

| Field | Content |
|-------|---------|
| Slice | SNP-4. Return from Scope to Continue setup. |
| Product status at capture | GUIDED PROJECT SETUP **IMPLEMENTED**. This slice **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Not deployed. |
| 1. What new contractor capability exists? | On Scope of work, Return to setup opens Continue setup for the same project. |
| 2. When would the contractor use it? | After adding work, or after looking at scope and leaving it unchanged, while setting up a project. |
| 3. What workflow will the final Manual need to teach? | From Continue setup, open Scope of work. Add the work and say Our crew or Subcontractor, or leave it unchanged. Return to setup. Continue setup then shows the current next action. Opening Scope directly still adds work on that page. |
| 4. What contractor-facing terms must be used? | Return to setup. Scope of work. Our crew. Subcontractor. Add work. |
| 5. What screenshots / Print examples will eventually be needed? | Scope of work on a desktop and on a phone, with Return to setup visible. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | Adding work does not price it and does not leave Scope by itself. Return to setup reads the project again. It does not skip a missing fact. |
| 7. Desktop / iPhone / Print relevance | Desktop and phone-width Scope of work. No print sheet is created. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — SNP-2 (2026-10-01)

| Field | Content |
|-------|---------|
| Slice | SNP-2. Guided Project Setup resume. |
| Product status at capture | START NEW PROJECT **IMPLEMENTED**. This slice **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Not deployed. |
| 1. What new contractor capability exists? | After starting a project, or from Continue setup on a project, the office shows what is ready, what is still needed, and one next action that opens the existing page. |
| 2. When would the contractor use it? | When starting a job, or when coming back to a job that is not ready to price. |
| 3. What workflow will the final Manual need to teach? | Start New Project still uses the existing project form. Saving opens Continue setup. The next action opens the existing client, location, drawings, scope, or estimate page. After that work, Continue setup reads the job again. Leaving and coming back does the same. More than one estimate asks the contractor to choose. |
| 4. What contractor-facing terms must be used? | Continue setup. What's ready. What's still needed. Next action. Correct the client. Review location. Choose about drawings. Open drawings. Open scope of work. Open the estimate. Choose an estimate. Create the estimate. |
| 5. What screenshots / Print examples will eventually be needed? | Continue setup on a desktop and on a phone, with the next action visible. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | The page does not complete the job. It opens the existing page. It does not pick one estimate when several exist. A client from another company is not shown. |
| 7. Desktop / iPhone / Print relevance | Desktop and phone-width Continue setup. No print sheet is created. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — PGE-6 (2026-10-01)

| Field | Content |
|-------|---------|
| Slice | PGE-6. Project drawing requirement. |
| Product status at capture | Plan Generation Engine **IN PRODUCTIZATION**. This slice **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Not deployed. |
| 1. What new contractor capability exists? | On the project page, the contractor can say drawings are required or drawings are not required. |
| 2. When would the contractor use it? | When a project has no current drawing and the office has not yet said whether drawings are needed. |
| 3. What workflow will the final Manual need to teach? | Open the project. If a drawing decision is required, choose Drawings are required or Drawings are not required. Required with no drawing opens the existing drawings page, where Upload PDF and Build Drawings already exist. A project that already has a current drawing does not have to answer that question. Changing the choice later does not remove the drawing. |
| 4. What contractor-facing terms must be used? | Drawing decision required. Drawings are required. Drawings are not required. Current drawing. Open drawings. |
| 5. What screenshots / Print examples will eventually be needed? | The project drawings panel on a desktop and on a phone, for a decision still required, for not required, and for a project that already has a current drawing. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | The choice is not made for the contractor. Not required does not create a drawing. An archived drawing does not count as a current drawing. |
| 7. Desktop / iPhone / Print relevance | Desktop and phone-width project page. No print sheet is created by the choice. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — PGE-5 (2026-10-01)

| Field | Content |
|-------|---------|
| Slice | PGE-5. Build Drawings on the existing project plans page. |
| Product status at capture | Plan Generation Engine **IN PRODUCTIZATION**. This slice **IMPLEMENTED / TESTED / CLOSED AS A SLICE** for `dimensioned_plan`. Not deployed. |
| 1. What new contractor capability exists? | On a project’s drawings page, Build Drawings can make a dimensioned-plan candidate. The contractor reviews it and uses it when it should become a project drawing. |
| 2. When would the contractor use it? | When the project needs a dimensioned plan and the members, sheet size, scale, and origin are known. |
| 3. What workflow will the final Manual need to teach? | Drawings → Build Drawings → enter the sheet facts and members → Generate → review the candidate → Use. Upload PDF stays the path for a drawing the contractor already has. |
| 4. What contractor-facing terms must be used? | Current drawings. Build Drawings. Candidate. Generate. Review candidate. Use. Uploaded. Generated. |
| 5. What screenshots / Print examples will eventually be needed? | The drawings page on a desktop and on a phone, showing Current drawings and Build Drawings, a candidate before Use, and the same sheet after Use. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | Generate does not add a project drawing. A missing measurement system, sheet size, scale, origin, or member list is explained and nothing is generated. This project has no placed members to copy. |
| 7. Desktop / iPhone / Print relevance | Desktop and phone-width drawings page. The candidate PDF is the print sheet. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — PLAT-LOGO-01 (2026-09-30)

| Field | Content |
|-------|---------|
| Slice | PLAT-LOGO-01. Approved office logo. |
| Product status at capture | Development freeze ACTIVE. Platform stabilization CLOSED. This logo CLOSED in git. Factual correction 30 Sep 2026: it is now live at deploy `dep-daulf9u0tbcc73bomdgg`. |
| 1. What new contractor capability exists? | The office sidebar shows the approved dark CalibraytAI mark. |
| 2. When would the contractor use it? | Whenever the office sidebar is open, including Home, Projects, Clients, and What we pay. |
| 3. What workflow will the final Manual need to teach? | None. The mark identifies the office. It does not change a task. |
| 4. What contractor-facing terms must be used? | CalibraytAI. The company name under the mark stays the company name. |
| 5. What screenshots / Print examples will eventually be needed? | Office sidebar on a desktop and on a phone, after this commit is the live office. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | None. Customer documents still use Brand Profile. |
| 7. Desktop / iPhone / Print relevance | Desktop office and the phone-width office drawer. Not Print. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — PLAT-UX-01 (2026-09-30)

| Field | Content |
|-------|---------|
| Slice | PLAT-UX-01. What we pay categories on a narrow screen. |
| Product status at capture | Development freeze ACTIVE. Platform stabilization IN PROGRESS. This defect CLOSED. |
| 1. What new contractor capability exists? | On a phone, the cost categories stay on the What we pay page instead of pushing the page sideways. |
| 2. When would the contractor use it? | When choosing All, Labour, Material, Equipment, Subcontract, Allowance, or Other on a narrow screen. |
| 3. What workflow will the final Manual need to teach? | Costs & pricing → What we pay → choose a category. The names did not change. |
| 4. What contractor-facing terms must be used? | What we pay. Labour. Material. Equipment. Subcontract. Allowance. Other. |
| 5. What screenshots / Print examples will eventually be needed? | What we pay on a phone, with the categories on more than one line. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | None. A category still only filters the list. |
| 7. Desktop / iPhone / Print relevance | Phone-width office browser, and the same page on a desktop where the categories stay on one line. Not Print. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — PLAT-CLIENT-01 (2026-09-30)

| Field | Content |
|-------|---------|
| Slice | PLAT-CLIENT-01. Open and correct an existing Client. |
| Product status at capture | Development freeze ACTIVE. Platform stabilization IN PROGRESS. This defect CLOSED. |
| 1. What new contractor capability exists? | From Clients, open an existing Client by the name and correct the same information used when the Client was added. |
| 2. When would the contractor use it? | When a Client name, company, email, phone, address, or note was entered wrong and the job should stay on that Client. |
| 3. What workflow will the final Manual need to teach? | Clients → click the Client name → correct the field → Save Client → the list shows the correction. |
| 4. What contractor-facing terms must be used? | Client. Clients. Save Client. |
| 5. What screenshots / Print examples will eventually be needed? | Clients list with the name as the way in, and the Client form with stored values. Not captured here. |
| 6. What warnings / validation distinctions need explanation? | Client name is required. Clearing the name does not save. |
| 7. Desktop / iPhone / Print relevance | Desktop and phone-width office browser. Not Print. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — DRAWINGS AND SCOPE (2026-09-27)

| Field | Content |
|-------|---------|
| Slice | Drawings list and Scope of work, after Joel’s first walk. |
| Product status at capture | Presentation corrected in git. Joel has not re-walked the live pages. |
| 1. What new contractor capability exists? | The project opens Drawings, which are the uploaded PDFs. Scope asks what work needs to be done and whether our crew or a subcontractor is doing it. |
| 2. When would the contractor use it? | After opening a project, before building the estimate. |
| 3. What workflow will the final Manual need to teach? | Open the project. Open Drawings. Open Scope of work. Choose the work. Choose Our crew or Subcontractor. |
| 4. What contractor-facing terms must be used? | Drawings. Scope of work. What work needs to be done? Who is doing it? Our crew. Subcontractor. |
| 5. What screenshots / Print examples will eventually be needed? | Drawings with the test files labeled. Scope with one crew item and one subcontractor item. Capture after Joel accepts the live pages. |
| 6. What warnings / validation distinctions need explanation? | Adding work does not price it or send anything. The two FG-010 files are test drawings. Sheet lists and the door-count trial are not on this page. |
| 7. Desktop / iPhone / Print relevance | Desktop office. The same two questions fit a later phone view. No print. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — ESTIMATING PATH LIVE ALIGNMENT (2026-09-27)

| Field | Content |
|-------|---------|
| Slice | Project, plans, and Scope of work as the way an estimate starts. |
| Product status at capture | Estimate version no longer offers Add from calculation. Scope of work is the project step. Hosted office follows the deploy of this slice. |
| 1. What new contractor capability exists? | From a project, open the plans, then open Scope of work and say who is doing each piece of work. The estimate page no longer asks the contractor to add from a calculation. |
| 2. When would the contractor use it? | After plans are on the project, before building the estimate. |
| 3. What workflow will the final Manual need to teach? | Open the project. Open Plan documents. Open Scope of work. Add the work. Choose Our crew or Subcontractor. |
| 4. What contractor-facing terms must be used? | Plan documents. Scope of work. What work? Who is doing it? Our crew. Subcontractor. |
| 5. What screenshots / Print examples will eventually be needed? | Project heading with Plan documents and Scope of work. Scope of work with one crew item and one subcontractor item. An estimate version without a calculation action. Capture after Joel has seen the live page. |
| 6. What warnings / validation distinctions need explanation? | Confirming scope does not price the work, create an estimate line, or send a quote. |
| 7. Desktop / iPhone / Print relevance | Desktop office. iPhone not required. No print. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — SCOPE OF WORK (2026-09-26)

| Field | Content |
|-------|---------|
| Slice | Scope of work, on a project. |
| Product status at capture | Implemented and tested in git. Not on the hosted office. Not on the Mac primary schema. |
| 1. What new contractor capability exists? | On a project, name the work and say whether our crew or a subcontractor will do it. A plan already on the project can be attached. Nothing is priced from this page. |
| 2. When would the contractor use it? | After plans are on the project, and before building the estimate. |
| 3. What workflow will the final Manual need to teach? | Open the project, open the plans, open Scope of work, add each piece of work, and choose who is doing it. |
| 4. What contractor-facing terms must be used? | Scope of work. What work? Who is doing it? Our crew. Subcontractor. Plan documents. Add project work. Confirmed. |
| 5. What screenshots / Print examples will eventually be needed? | Project with the Scope of work action. Scope of work with one crew item and one subcontractor item. Do not capture until the page is on the office Joel uses. |
| 6. What warnings / validation distinctions need explanation? | Work must already exist in the work catalog. A plan from another project cannot be used. Removing work from scope keeps the record. This page does not create the estimate. |
| 7. Desktop / iPhone / Print relevance | Desktop office. iPhone not required for this foundation. No print. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — ADD FROM CALCULATION ENTRY (2026-09-26)

| Field | Content |
|-------|---------|
| Slice | Add from calculation, on an estimate version. |
| Product status at capture | Entry copy corrected after Joel stopped, confused, before any mapping. Human review of the correction is not done. |
| 1. What new contractor capability exists? | The estimate explains that a calculation works out quantities and that only confirmed quantities are added. It does not ask the contractor to paste a file. |
| 2. When would the contractor use it? | When they want calculated quantities on an estimate, once a calculation can be run from that page. |
| 3. What workflow will the final Manual need to teach? | Open the estimate. Add from calculation. Read what the step is for. When a calculation is available, run it, review the quantities, choose the company item, and confirm. |
| 4. What contractor-facing terms must be used? | Add from calculation. What was calculated. Add to this estimate. Add as. Still to match. Calculation details. |
| 5. What screenshots / Print examples will eventually be needed? | The explained entry page, one confirmed quantity, and one quantity still to match. Do not capture them until Joel accepts the look. |
| 6. What warnings / validation distinctions need explanation? | No calculation can be run from the estimate until a real one exists. A quantity with no company item can be left waiting. That wait is not a failure. |
| 7. Desktop / iPhone / Print relevance | Desktop office. Not a customer document. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — CALCULATION RESULT MAPPING LIVE FOR UAT (2026-09-26)

| Field | Content |
|-------|---------|
| Slice | Add from calculation, on an estimate version. |
| Product status at capture | Live on the hosted validation office. Ready for Joel to try. Human UAT is not done. Mac primary was not migrated. |
| 1. What new contractor capability exists? | From an unlocked estimate version, load a calculation file, see each quantity, and add one confirmed quantity to a company cost. |
| 2. When would the contractor use it? | After a calculation file exists and they want a confirmed quantity on an estimate. |
| 3. What workflow will the final Manual need to teach? | Open an unlocked draft. Add from calculation. Paste the calculation file. Review each quantity. Add one. Leave another unresolved. Open the calculation record. |
| 4. What contractor-facing terms must be used? | Add from calculation. Calculation result. Unresolved. Add to estimate. Calculation record. |
| 5. What screenshots / Print examples will eventually be needed? | The review list, one added line with waste at zero, and one unresolved quantity. Do not capture them until Joel accepts the look. |
| 6. What warnings / validation distinctions need explanation? | The sample file is a mapper test, not an approved formula. A quantity whose unit has no company item stays unresolved. The estimate line does not add waste again. |
| 7. Desktop / iPhone / Print relevance | Desktop office. Not a customer document. Not one of the seven workflow document families. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — CALCULATION RESULT MAPPING (2026-09-26)

| Field | Content |
|-------|---------|
| Slice | Add from calculation, on an estimate version. |
| Product status at capture | Implemented and tested. Not on the hosted office. Migration `j0e1f2a3b4c5` is not live-migrated. |
| 1. What new contractor capability exists? | From an estimate version, load a calculation, see each quantity, and add a confirmed quantity to a company cost item or reusable work. |
| 2. When would the contractor use it? | After a calculation exists and they want those quantities on an estimate. |
| 3. What workflow will the final Manual need to teach? | Open the estimate. Add from calculation. Review each quantity. Choose a matching item. Add to estimate. Leave unmatched quantities unresolved. |
| 4. What contractor-facing terms must be used? | Add from calculation. Calculation result. Unresolved. Reusable work. Labour mapping needs a labour rule. |
| 5. What screenshots / Print examples will eventually be needed? | The review list on an unlocked estimate, one added quantity, and one unresolved quantity. Do not capture them until the hosted migration exists. |
| 6. What warnings / validation distinctions need explanation? | A bad calculation file is refused. Units that are not the same measure are refused. Nothing is converted. Waste on the estimate line is not added again. A locked estimate cannot take a new quantity. |
| 7. Desktop / iPhone / Print relevance | Desktop office. Not a customer document. Not one of the seven workflow document families. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — UAT 3 COSTS AND PRICING (2026-09-26)

| Field | Content |
|-------|---------|
| Slice | Costs & pricing. What we pay. Reusable work. How we price. |
| Product status at capture | IMPLEMENTED / TESTED. Labour rates were not redesigned. Estimate-specific margin was not added. |
| 1. What new contractor capability exists? | The contractor can open Costs & pricing and see the unit costs used in estimates, groups of those costs used again, and how the company turns cost into the customer price. |
| 2. When would the contractor use it? | When checking or updating the costs and the company pricing method before building an estimate. |
| 3. What workflow will the final Manual need to teach? | Open Costs & pricing. Open What we pay and choose a category. Open a row to change a cost. Open Reusable work for a repeated group of costs. Open How we price to see the company method. A labour cost here is a unit cost, not the hourly rate screen. |
| 4. What contractor-facing terms must be used? | Costs & pricing. What we pay. Reusable work. How we price. Gross Margin Pricing. Company default. Subcontract. |
| 5. What screenshots / Print examples will eventually be needed? | The Costs & pricing list, What we pay, Reusable work, and How we price. Do not capture them until Joel accepts the look. |
| 6. What warnings / validation distinctions need explanation? | A material name identifies the product. It is not the price. The starting markup on a cost is not the company method for the customer price. Supplier pricing is not connected. |
| 7. Desktop / iPhone / Print relevance | Desktop office. Print is unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — UAT 3 WORKFLOW DOCUMENTS (2026-09-26)

| Field | Content |
|-------|---------|
| Slice | Workflow documents on a project, from the seven-family register. |
| Product status at capture | IMPLEMENTED / TESTED. Missing document generators were not built. |
| 1. What new contractor capability exists? | A project has a Workflow documents list. It shows each paper the job can use, whether it is internal or for the customer, and whether it can be opened. |
| 2. When would the contractor use it? | When they want to see which documents belong to a job, open the office cost breakdown, or open the QuickBooks entry sheet. |
| 3. What workflow will the final Manual need to teach? | From the project, open Workflow documents. Open a row only when it has a current view. Leave a row that says not yet available. Read the contract row as a draft that is not for signature. |
| 4. What contractor-facing terms must be used? | Workflow documents. Internal working documents. Customer documents. Current office view. Current office entry. Not yet available. Commercial draft. Not for execution. Not for signature. |
| 5. What screenshots / Print examples will eventually be needed? | The workflow documents list on a project, including the contract warning. Do not capture them until Joel accepts the look. |
| 6. What warnings / validation distinctions need explanation? | The Ontario construction contract row is a commercial draft. It is not a contract to sign or use. The office breakdown and the QuickBooks sheet are current working views, not finished customer documents. |
| 7. Desktop / iPhone / Print relevance | Desktop office, from the project. Print is unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — UAT 3 SHARED POLISH FOUNDATION (2026-09-26)

| Field | Content |
|-------|---------|
| Slice | Shared office presentation. Clients list. Crews list. Brand leaves the daily menu. |
| Product status at capture | IMPLEMENTED / TESTED. Documents, costs, labour, commercial settings, subcontractors, and RFQ are not in this slice. |
| 1. What new contractor capability exists? | Clients and Crews use the same calm header and list as Home and Projects. Brand profile opens from the company name at the upper right. |
| 2. When would the contractor use it? | When adding a client, reviewing crews, or changing the name and logo used on customer documents. |
| 3. What workflow will the final Manual need to teach? | Open Clients or Crews from the menu. Use the one action at the top of the page. Open Brand profile from the company name, not from the side menu. |
| 4. What contractor-facing terms must be used? | Clients. Crews. Company profile. Brand profile. Active. Retired. |
| 5. What screenshots / Print examples will eventually be needed? | Clients list, Crews list, and the upper-right company control. Do not capture them until Joel accepts the look. |
| 6. What warnings / validation distinctions need explanation? | Brand profile still only changes customer-document identity. It does not change prices or access. |
| 7. Desktop / iPhone / Print relevance | Desktop office. The header company control should remain readable on a narrow screen. Print is unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — UAT 2 WAVES A AND B (2026-09-26)

| Field | Content |
|-------|---------|
| Slice | Home, Company Calendar, and company-first navigation |
| Product status at capture | IMPLEMENTED / TESTED. Presentation only. No new calculation or permission. |
| 1. What new contractor capability exists? | The office names the company and opens the month calendar from Home. No new business capability. |
| 2. When would the contractor use it? | Opening the office, checking counts, and looking at the month of work. |
| 3. What workflow will the final Manual need to teach? | Home lists current work and starts a project. Company Calendar is the month, the day, work waiting for dates, and this period. Projects stays in the menu. Estimates and proposals are opened from Home or from a project. Costs & pricing is what the company pays, reusable work, and how a cost becomes a price. Past jobs are reference, not current estimates. |
| 4. What contractor-facing terms must be used? | Company Calendar. Costs & pricing. What we pay. Reusable work. How we price. Past jobs. Templates. Attention. Crews. Brand. Work catalog. |
| 5. What screenshots / Print examples will eventually be needed? | Home and Company Calendar after Joel’s visual pass. Not captured now. |
| 6. What warnings / validation distinctions need explanation? | Past jobs are not current estimates. The month is not back on Home. Crews are company setup used when assigning dated work. The sidebar mark is still the Brayman logo. |
| 7. Desktop / iPhone / Print relevance | Desktop office. Field, iPhone, and Print were not changed. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — UAT 1 OFFICE PRESENTATION (2026-09-26)

| Field | Content |
|-------|---------|
| Slice | UAT 1 office presentation cleanup |
| Product status at capture | IMPLEMENTED / TESTED. Presentation only. No new calculation or permission. |
| 1. What new contractor capability exists? | The office is easier to scan. No new business capability. |
| 2. When would the contractor use it? | Opening the office, choosing a project, and opening an estimate. |
| 3. What workflow will the final Manual need to teach? | Home shows where work stands and starts a project. The calendar is on Schedule. A project row opens the project. Project stage is the project's own stage. Estimate work happens on the estimate page. Archive is on that page. Assemblies remain under Cost library. |
| 4. What contractor-facing terms must be used? | Home. Projects. Estimates. Proposals. Schedule. Cost library. Assemblies. Project stage. Estimate Stage stays on the project, separate from Project stage. |
| 5. What screenshots / Print examples will eventually be needed? | Home, Projects list, one Project, Estimates list, one Estimate. Not captured now. |
| 6. What warnings / validation distinctions need explanation? | Project stage is not Estimate Stage. The sidebar mark is still the Brayman logo until the approved dark CalibraytAI mark is installed. |
| 7. Desktop / iPhone / Print relevance | Desktop office. Field, iPhone, and Print were not changed. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |

### MANUAL IMPACT — PKG-F07 EXTRA WORK APPROVED INTERNAL DIRECT COST (2026-09-24)

| Field | Content |
|-------|---------|
| Slice | PKG-F07 Extra Work Approved Internal Direct Cost capture + MONITOR truth |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** Parent pin SHA **`246fd5e424da27fc7f0551b24c7491c9bc285d33`**. User Guide remains outstanding. |
| 1. What new contractor capability exists? | When Extra Work becomes Approved, the contractor can enter Approved Internal Direct Cost — the estimated direct cost to perform that extra work. MONITOR then uses that stored cost, not customer sell value, on the authorized estimated-cost side. |
| 2. When would the contractor use it? | When approving extra-work Change Orders, when linking extra work to an already-approved Change Order, and when reviewing project estimated vs actual direct cost on the Hub MONITOR panel. |
| 3. What workflow will the final Manual need to teach? | Open the Extra Work Change Order. Set status to Approved. Enter Approved Internal Direct Cost or leave blank if not captured. If the amount was wrong, reverse approval, confirm/re-enter the amount, and approve again. Linking extra work to an already-approved Change Order asks for the same amount. |
| 4. What contractor-facing terms must be used? | Approved Internal Direct Cost. Extra work. Not captured. Actual Direct Cost. Do not call customer sell, subtotal, markup, or Change Order total the internal direct cost. |
| 5. What screenshots / Print examples will eventually be needed? | Change Order status form with Approved Internal Direct Cost. Hub MONITOR Approved Internal Direct Cost vs Actual Direct Cost, including Not captured. Not from this working tree. |
| 6. What warnings / validation distinctions need explanation? | Blank means Not captured, not $0.00. Zero is a real captured estimate. Negative amounts fail and do not approve. The amount cannot be casually edited after approval. Reversing approval keeps the stored amount but MONITOR ignores it until re-approved. |
| 7. Desktop / iPhone / Print relevance | Office Change Order and Project Hub MONITOR. Field unchanged. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Start F15 or T16. Live-upgrade. Teach sell value as internal cost. |

### MANUAL IMPACT — FG-039 EMPLOYMENT VS ENTREPRENEURSHIP DECISION TOOL (2026-09-24)

| Field | Content |
|-------|---------|
| Slice | FG-039 Employment vs Entrepreneurship Decision Tool |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** Parent pin SHA **`3b193949eabd326bbce33043b2b60a1a290c7c6f`**. User Guide remains outstanding. |
| 1. What new contractor capability exists? | A shareable CalibraytAI calculator that compares employment economic value with entrepreneurship economics, transition cash, owner hours, downside cases, and what has to be true. The user can download a Results PDF of the current scenario. It does not tell the user which path to take. |
| 2. When would the contractor use it? | When comparing a job with running a business, considering leaving employment, or reviewing the economics of self-employment. Download the PDF to keep a point-in-time record. |
| 3. What workflow will the final Manual need to teach? | Open the tool. Enter Today, Business, Market, and Costs. Review Results. Optionally name the scenario. Download Results PDF. Start over / new scenario resets the form on purpose. The user decides. |
| 4. What contractor-facing terms must be used? | Employment economic value. Entrepreneurship economic value. Difference. Cash required to make the transition. Cash available to owner before personal income tax. Total owner hours. What has to be true. Download results PDF. Start over / new scenario. Do not say winner, recommended, score, or risk rating. |
| 5. What screenshots / Print examples will eventually be needed? | Today step. Results hierarchy. What Has to Be True. Downside cases. Results PDF cover and core results. Not from this working tree. |
| 6. What warnings / validation distinctions need explanation? | Empty or invalid numbers are treated as zero. Existing assets cannot create a negative cash-to-start-up figure. A negative difference is a real result, not an error. Starting trade profiles are assumptions only. Download PDF does not save the scenario in the system. Start over clears the current entries. |
| 7. Desktop / iPhone / Print relevance | Public branded page and office Plan link. Field unchanged. Results PDF is the print/retain record. |
| Do not | Final Manual prose. Unstable screenshots. Claim the tool chooses employment or entrepreneurship. Start F07 or F15. |

### MANUAL IMPACT — PKG-F14 ORGANIZATION-SCOPED NUMBERING (2026-09-24)

| Field | Content |
|-------|---------|
| Slice | PKG-F14 organization-scoped Estimate / Proposal / Change Order numbering |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED / FULL SUITE NOT GREEN.** HEAD **`4024180592df3e2689a2ee40e5ec83f572c34ccb`**. Live S16 migration **NOT APPLIED**. User Guide remains outstanding. |
| 1. What new contractor capability exists? | Each company has its own Estimate, Proposal, and Change Order number sequence. A second company can use the same human-facing number. A duplicate number inside one company is refused. |
| 2. When would the contractor use it? | When creating or editing an Estimate or Proposal, or when creating a Change Order (including Extra Work → Change Order), especially if more than one company will use the platform. |
| 3. What workflow will the final Manual need to teach? | New Estimate / Proposal / Change Order numbers are next for this company only. Another company’s documents do not consume this company’s numbers. Do not reuse a number already used in this company. |
| 4. What contractor-facing terms must be used? | Company. Estimate number. Proposal number. Change Order number. Do not say organization_id, unique constraint, generator, or TOCTOU. |
| 5. What screenshots / Print examples will eventually be needed? | New Estimate suggested number. Duplicate-number refusal on Estimate and Proposal. New Change Order number. Not from this working tree. |
| 6. What warnings / validation distinctions need explanation? | The same Estimate or Proposal number may exist in another company. A duplicate number inside one company is refused. Change Order collisions are refused by the database unique rule for that company. |
| 7. Desktop / iPhone / Print relevance | Office Estimate, Proposal, and Change Order forms. Field unchanged. Print number formats unchanged (`EST-YYYY-NNNN`, `PROP-YYYY-NNNN`, `CO-NNNNNN`). |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Start F07 or F15. Live-upgrade. Teach numbers as globally unique. |

### MANUAL IMPACT — PKG-S16 SCHEMA FOUNDATION (2026-09-23)

| Field | Content |
|-------|---------|
| Slice | PKG-S16 Rule 16 consolidated schema / migration (R14 / R07 / R12 / R24) |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED / NOT LIVE-MIGRATED.** Additive **`h8c9d0e1f2a3`**. Live Alembic remains **`g7b8c9d0e1f2`**. User Guide remains outstanding. |
| 1. What new contractor capability exists? | None yet. This is persistence foundation only. Estimate / Proposal / Change Order numbers can later be unique per company, but the app still suggests the next number globally. Approved extra-work cost is not captured on Approve. Person wage history is not shown. |
| 2. When would the contractor use it? | Not yet. Later F14 when creating documents in a second company. Later F07 when Approving extra work. Later People work when wage changes are recorded. |
| 3. What workflow will the final Manual need to teach? | Do not teach S16 itself. Later teach that each company has its own Estimate / Proposal / Change Order numbers, that extra-work internal cost is captured on Approve, and that Person wage history exists. |
| 4. What contractor-facing terms must be used? | Company. Estimate number. Proposal number. Change Order number. Extra work. Approved internal cost. Person. Hourly wage. Do not say organization_id, unique constraint, CHECK, or Alembic. |
| 5. What screenshots / Print examples will eventually be needed? | None from S16. Later F14 numbering, F07 Approve extra work, and People wage history. |
| 6. What warnings / validation distinctions need explanation? | Later: the same Estimate number may exist in another company. A duplicate number inside one company is refused. Extra-work approved internal cost is not the customer sell amount. |
| 7. Desktop / iPhone / Print relevance | No contractor-facing screen change in S16. Office forms, Field, and Print are unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Start F14, F07, or F15. Live-upgrade. Teach wage history as if it is written today. |

### MANUAL IMPACT — PKG-F09 PROJECT-CHILD CONTEXT (2026-09-23)

| Field | Content |
|-------|---------|
| Slice | PKG-F09 / R09 Project-child context / wrong-Project prevention |
| Product status at capture | **COMMITTED / PUSHED / SHA-PINNED / CLOSED** at product SHA **`e445e641789efd71b44d456b202b560649879c37`**. User Guide remains outstanding. |
| 1. What new contractor capability exists? | Opening New Change Order or New Estimate from a Project Hub stays on that Project. Global New Change Order no longer silently picks the first Project. An existing Change Order cannot be moved to another Project. |
| 2. When would the contractor use it? | When creating a Change Order, Estimate, Time entry, or Schedule item from a Project, or when creating a Change Order from the company-wide list. |
| 3. What workflow will the final Manual need to teach? | From a Project, New stays on that Project and Cancel/Back return to that Project. From the company-wide list, the contractor must choose the Project before a Change Order or Estimate can be created. Extra Work still cannot become a Change Order for a different Project. |
| 4. What contractor-facing terms must be used? | Project. Change Order. Estimate. Extra Work. Time. Schedule. Do not say projects[0], operating Project bind, or reparent. |
| 5. What screenshots / Print examples will eventually be needed? | Project Hub New Change Order and New Estimate. Global New Change Order with Choose a project. The message when no Project is chosen. |
| 6. What warnings / validation distinctions need explanation? | A Change Order cannot be created until a Project is chosen. Extra Work from another Project cannot be turned into this Project’s Change Order. An existing Change Order cannot be moved to another Project. |
| 7. Desktop / iPhone / Print relevance | Office Project Hub and office Change Order / Estimate / Time / Schedule forms. Field Project confirm (R02) unchanged. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Start S16. Change Estimate edit Project selection. Redesign Hub visual / left-nav. |

### MANUAL IMPACT — PKG-F08 SCOPE ORIGIN AFTER TIME (2026-09-23)

| Field | Content |
|-------|---------|
| Slice | PKG-F08 / R08 live origin immutability after Time |
| Product status at capture | **COMMITTED / PUSHED / SHA-PINNED / CLOSED** at product SHA **`94928ab58de232be4e26a129626279f5270a6ef1`**. User Guide remains outstanding. |
| 1. What new contractor capability exists? | None new for ordinary office work. Extra Work that already has time recorded against it cannot later be treated as original work, and original work that already has time recorded against it cannot later be reviewed into Extra Work. |
| 2. When would the contractor use it? | When office tries Record as original work or Review as extra work after time has already been entered on that work. |
| 3. What workflow will the final Manual need to teach? | Extra Work can be recorded as original work only before time is entered. After time exists, that classification stays. Time already entered keeps the origin it had when it was submitted. |
| 4. What contractor-facing terms must be used? | Extra Work. Original work. Change Order work. Time. Do not say scope_origin, EXTRA_WORK, or operational-use boundary. |
| 5. What screenshots / Print examples will eventually be needed? | Project work Extra Work row with Record as original work. The error after time already exists. |
| 6. What warnings / validation distinctions need explanation? | The work can no longer be reclassified because time has already been recorded against it. Creating Extra Work, seeding original work, and linking Extra Work to a Change Order are different actions. |
| 7. Desktop / iPhone / Print relevance | Office Project work. Field Extra Work create unchanged. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Start F09 Project-child context. Change Change Order numbering (F14). |

### MANUAL IMPACT — PKG-T03C EXTRA WORK → CHANGE ORDER (2026-09-23)

| Field | Content |
|-------|---------|
| Slice | PKG-T03C / R03C Extra Work → Change Order atomicity |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** User Guide remains outstanding. |
| 1. What new contractor capability exists? | None new for ordinary office work. Creating a Change Order from Extra Work now either completes both steps together or does neither. |
| 2. When would the contractor use it? | When turning Extra Work into a Change Order from Project work or from the new Change Order form with Extra Work selected. |
| 3. What workflow will the final Manual need to teach? | Extra Work is recorded first. Creating a Change Order from that Extra Work is one action. If it fails, no leftover Change Order is left to clean up. Linking Extra Work to an already-existing Change Order remains a separate action. |
| 4. What contractor-facing terms must be used? | Extra Work. Change Order. Do not say PATH 1, commit=False, or orphan CO. |
| 5. What screenshots / Print examples will eventually be needed? | Project work Extra Work → create Change Order. Office new Change Order form. |
| 6. What warnings / validation distinctions need explanation? | If creating a Change Order from Extra Work cannot finish, the Extra Work stays Extra Work and no Change Order is left behind. Linking Extra Work to a Change Order that already exists is a different action. |
| 7. Desktop / iPhone / Print relevance | Office Change Orders and Project work. Field Extra Work create unchanged. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Redesign scope-origin (F08). Change Change Order numbering (F14). |

### MANUAL IMPACT — PKG-F06 PUBLIC WALKTHROUGH GET EXPIRY (2026-09-23)

| Field | Content |
|-------|---------|
| Slice | PKG-F06 / R06 public Walkthrough GET expiry read-only |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** User Guide remains outstanding. |
| 1. What new contractor capability exists? | None new for office work. A client Walkthrough link that has passed its expiry time is no longer usable, and opening that link does not itself change the invitation record to Expired. |
| 2. When would the contractor use it? | When a client opens or tries to submit a Final Walkthrough link after its expiry time, or when office Closes a Project that still has an unused invitation. |
| 3. What workflow will the final Manual need to teach? | Send the Walkthrough invitation as today. After the expiry time, the client sees that the link is not available. Closing the Project still ends unused invitations. Opening an expired link does not create a new office status of Expired. |
| 4. What contractor-facing terms must be used? | Final Walkthrough. Invitation. Link. Expired. Close. Do not say OPEN→EXPIRED, GET side effect, or expires_at. |
| 5. What screenshots / Print examples will eventually be needed? | Public Walkthrough unavailable page for an expired link. Office Walkthrough after Close. |
| 6. What warnings / validation distinctions need explanation? | The link is not available because the expiry time passed, not because the client opened it. Closing the Project still ends an unused invitation even if that expiry time already passed. |
| 7. Desktop / iPhone / Print relevance | Public Walkthrough page. Office Close. Field unchanged. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Wholesale C08 copy sweep. Remove access-attempt recording. |

### MANUAL IMPACT — PKG-L05 PROJECT CLOSE / WALKTHROUGH REVOCATION / OPEN PUNCH CONFIRMATION (2026-09-23)

| Field | Content |
|-------|---------|
| Slice | PKG-L05 Project Close — Walkthrough revocation + open Punch confirmation |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** User Guide remains outstanding. |
| 1. What new contractor capability exists? | Closing a Project now ends unused Final Walkthrough invitations so the old link cannot be used. If Punch List items are still open, Close still works, but the office must confirm that those items will stay open. |
| 2. When would the contractor use it? | When the Instance Owner or System Administrator Closes a Project that had a client Walkthrough invitation still unused, or that still has open Punch List items. |
| 3. What workflow will the final Manual need to teach? | Close as today. If Punch List items are open, read the warning, see the count, and confirm Close anyway. After Close, the old Walkthrough link is no longer usable. After Reopen, send a new invitation if the client should respond again. |
| 4. What contractor-facing terms must be used? | Close. Reopen. Punch List. Final Walkthrough. Invitation. Open. Send a new invitation. Do not say REVOKED, TOCTOU, or transaction. |
| 5. What screenshots / Print examples will eventually be needed? | Close confirmation with open Punch warning and count. Project Hub Walkthrough after Close / after Reopen, showing that a new invitation is required. |
| 6. What warnings / validation distinctions need explanation? | Closing does not complete or delete open Punch List items. Missing confirmation does not Close. An unused invitation is no longer usable after Close. Reopen does not bring the old link back. |
| 7. Desktop / iPhone / Print relevance | Office Close confirmation and Project Hub Walkthrough. Public Walkthrough link fail-closed. Field unchanged. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Wholesale C08 copy sweep. Change Close authorization. |

### MANUAL IMPACT — PKG-T13 / R13 INTEGRITYERROR → CONTRACTOR DOMAIN ERROR (2026-09-23)

| Field | Content |
|-------|---------|
| Slice | PKG-T13 / R13 expected integrity collision → contractor domain error |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** User Guide remains outstanding. |
| 1. What new contractor capability exists? | None new. Saving a schedule that is already current, assigning a person or crew already on those dates, adding a work order that already exists, building a work plan that is already built, or saving a crew name that already exists still does the same contractor work. If another save won first, the later person is told that in ordinary product language. |
| 2. When would the contractor use it? | When two people save the same Schedule item, assignment, or work order; when they rebuild a work plan that is already built; or when they save a crew name that already exists. |
| 3. What workflow will the final Manual need to teach? | Same Schedule / work-plan / crew workflows. If the later save cannot complete, open the current dates or list again. Do not treat a database error page as the product. |
| 4. What contractor-facing terms must be used? | Schedule. Work item. Activity. Assignment. Work order. Work plan. Crew. Already scheduled. Already assigned. Already exists. Already built. Do not say IntegrityError, unique constraint, or SQLite. |
| 5. What screenshots / Print examples will eventually be needed? | Company Schedule after a rejected duplicate save. Crew settings after a rejected duplicate name. Project work after a rejected second seed. |
| 6. What warnings / validation distinctions need explanation? | “That work item is already scheduled. Edit the current dates.” “That activity is already scheduled. Edit the current dates.” “That person is already assigned to these dates.” “That crew is already assigned to these dates.” “That work order already exists.” “This project's work plan is already built.” “A crew with that name already exists. Rename the retired crew first.” Those messages now also cover a save that lost to another completed save. A broken database is not described as a duplicate. |
| 7. Desktop / iPhone / Print relevance | Office Schedule, Project work, and Crew settings. Field Schedule POSTs unchanged. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Invent a duplicate-Time rule. Decide commercial document numbering. |

### MANUAL IMPACT — PKG-T10 / R10 TIME CONCURRENT TRANSITION (2026-09-22)

| Field | Content |
|-------|---------|
| Slice | PKG-T10 / R10 Time concurrent status transition |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** User Guide remains outstanding. |
| 1. What new contractor capability exists? | None new. Approve, Return, Send again, and approved Time correction still do the same contractor work. Two people can no longer both finish a conflicting change on the same Time row. |
| 2. When would the contractor use it? | When office Approves or Returns submitted Time, when a worker Sends again after a Return, or when office corrects approved Time. |
| 3. What workflow will the final Manual need to teach? | Same Time review workflow. If the Time is no longer waiting for that action, the later person is told it cannot be done that way. They should open the Time again. |
| 4. What contractor-facing terms must be used? | Time. Submitted. Returned. Approved. Send. Send again. Correct. Do not say concurrent, rowcount, or UPDATE. |
| 5. What screenshots / Print examples will eventually be needed? | Office Time detail after Approve. Office Time detail after Return. Field Send again after Return. |
| 6. What warnings / validation distinctions need explanation? | “Only submitted time can be approved.” “Only submitted time can be returned.” “Only returned time can be corrected and sent again.” “Only approved time can be corrected this way.” Those messages now also cover a Time that another person already moved. |
| 7. Desktop / iPhone / Print relevance | Office Time review and Field Time Send again. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. Invent a duplicate-Time rule. |

### MANUAL IMPACT — PKG-T02 / R02 FIELD PROJECT CONTEXT (2026-09-22)

| Field | Content |
|-------|---------|
| Slice | PKG-T02 / R02 Field Project operating context |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** User Guide remains outstanding. |
| 1. What new contractor capability exists? | None new. Field now keeps the current job as a current (ACTIVE) job only. Opening Time for a current job still does not ask for a second confirm. A Closed job cannot become the current Field job. |
| 2. When would the contractor use it? | On Field Today, Time, Extra work, Capture, and Projects, whenever they choose or switch the job they are standing on. |
| 3. What workflow will the final Manual need to teach? | Open Time from Today for a current job and work immediately. Switching to another current job’s Time makes that job current. A Closed job is labeled Closed and is not operated from Field. After a job is Closed, Today no longer treats it as the current job. |
| 4. What contractor-facing terms must be used? | Today. Time. Extra work. Capture. Confirm Project. Current. Closed. Project. Do not say session key, operating_state, or confirm authority. |
| 5. What screenshots / Print examples will eventually be needed? | Field Today with a current job. Field Time after Today→Time with the Project name visible. Field Time or confirm surface showing Closed. |
| 6. What warnings / validation distinctions need explanation? | Closed jobs are not operated from Field. That is now true for the confirmed Field job. New Time or Extra work on a Closed job still fails closed. Help copy was not rewritten. |
| 7. Desktop / iPhone / Print relevance | Field / iPhone. Office Close law unchanged. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim whole-system Rule 16 PASS. |

### MANUAL IMPACT — VISUAL-2 PROJECTS V2 REGISTER (2026-09-21)

| Field | Content |
|-------|---------|
| Slice | VISUAL-2 Projects V2 register presentation |
| Product status at capture | **COMMITTED IN THIS SLICE.** Structure accepted. User Guide remains outstanding. |
| 1. What new contractor capability exists? | None new. The Projects list is a calmer register: name, then client and location, then stage, then Open. Current and Closed show how many Projects are in each. |
| 2. When would the contractor use it? | After clicking Projects, to scan current or closed work and open a Project. |
| 3. What workflow will the final Manual need to teach? | Same as the first Projects visual: Current vs Closed is operating state, not CRM status. Start New Project is unchanged. Closed Projects stay reachable. |
| 4. What contractor-facing terms must be used? | Projects. Current. Closed. Start New Project. Open. Client. Location. |
| 5. What screenshots / Print examples will eventually be needed? | Desktop Current and Closed registers after Joel accepts the live visual. |
| 6. What warnings / validation distinctions need explanation? | Counts are operating-state counts. Stage on the row is CRM status. No attention badges. |
| 7. Desktop / iPhone / Print relevance | Desktop office Projects only. Field Projects unchanged. Print unchanged. |
| Do not | Final Manual prose. Claim Hub redesigned. Claim UAT Project names were cleaned up. |

### MANUAL IMPACT — VISUAL-2 OFFICE PROJECTS LIST (2026-09-21)

| Field | Content |
|-------|---------|
| Slice | VISUAL-2 office Projects list presentation (working tree / not committed) |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** Home V2.2 remains the desktop reference. User Guide remains outstanding. |
| 1. What new contractor capability exists? | None new. The existing Projects list is easier to scan: Project name first, Current or Closed, and + Start New Project in the same language as Home. |
| 2. When would the contractor use it? | After clicking Projects in the left navigation, to find a current or closed Project and open it, or to start a new Project. |
| 3. What workflow will the final Manual need to teach? | Projects is the list of work, not the Project Hub. Current vs Closed is operating state, not CRM status. Closed Projects stay reachable. Start New Project still uses the existing form. |
| 4. What contractor-facing terms must be used? | Projects. Current. Closed. Start New Project. Client. Location. Do not say database, archive, or deleted for Closed. |
| 5. What screenshots / Print examples will eventually be needed? | Desktop Projects Current list and Closed list after Joel accepts the live visual, not this working tree. |
| 6. What warnings / validation distinctions need explanation? | Current / Closed is not CRM Project status. Closed does not mean financially complete, LEARN complete, or deleted. Company Attention is not shown on this list. |
| 7. Desktop / iPhone / Print relevance | Desktop office Projects only. Field Projects unchanged. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim attention scores. Claim Hub was redesigned. Claim Field Projects changed. |

### MANUAL IMPACT — HOME V2.2 DESKTOP PLANNING PRESENTATION (2026-09-21)

| Field | Content |
|-------|---------|
| Slice | Home V2.2 live desktop presentation (working tree / not committed) |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED.** Office `/` is the contractor planning desk. Isolated prototype remains provenance. User Guide remains outstanding. |
| 1. What new contractor capability exists? | Opening Office home now shows a large month calendar of scheduled work, a Start New Project action, truthful work counts, work waiting for dates, and the selected day's scheduled work. |
| 2. When would the contractor use it? | First thing in the office: plan the week, see what occupies a day, start a new Project, or open Company Attention when authorized. |
| 3. What workflow will the final Manual need to teach? | Home is the planning desk, not a scorecard. Click a day to see that day's work. Start New Project uses the existing Project form. Counts are live work counts, not money. Capacity, payday, holidays, and drag-to-reschedule are not available yet. |
| 4. What contractor-facing terms must be used? | Office home. Start New Project. Current projects. Estimates outstanding. Proposals outstanding. Open change orders. Need attention. Not scheduled yet. Day. |
| 5. What screenshots / Print examples will eventually be needed? | Desktop Home with a real occupied month and an empty month. Capture after Joel accepts the live visual, not this working tree. |
| 6. What warnings / validation distinctions need explanation? | Home does not invent money, capacity, payday, holidays, or ready-to-schedule. Closed Projects stay off this calendar. Company Attention still requires Company / Management. Help/Voice are the same as other office screens. |
| 7. Desktop / iPhone / Print relevance | Desktop Home only. Field Month is unchanged. Print unchanged. |
| Do not | Final Manual prose. Claim payday/holiday tints exist. Claim capacity percentages. Claim Financials. Claim drag-and-drop reschedule. Claim Field Month changed. |

### MANUAL IMPACT — FG-038 PA-B SYSTEM ADMINISTRATOR FOUNDATION (2026-09-19)

| Field | Content |
|-------|---------|
| Slice | FG-038 PA-B System Administrator authority foundation |
| Product status at capture | **IMPLEMENTED IN WORKING TREE / NOT LIVE.** No People & Access UI. No live Sys Admin. Owner unchanged. Close/Reopen can accept a Sys Admin only after a later live appointment. User Guide remains outstanding. |
| 1. What new contractor capability exists? | None on a live screen. This slice stores later System Administrator authority. Settings still has no People & Access page. |
| 2. When would the contractor use it? | Not yet. Later, after People & Access UI and a live appointment, the Owner designates a System Administrator. |
| 3. What workflow will the final Manual need to teach? | Later: only the Instance Owner appoints a System Administrator. A System Administrator cannot appoint another. A System Administrator cannot remove or replace the Instance Owner. Close/Reopen remains Owner or System Administrator, not ordinary company management. |
| 4. What contractor-facing terms must be used? | Instance Owner. System Administrator. People & Access (future). Do not say Platform Owner. |
| 5. What screenshots / Print examples will eventually be needed? | None from this slice. Capture People & Access after that UI exists. |
| 6. What warnings / validation distinctions need explanation? | Domain B (Company / Management) is not System Administrator. Inactive people are not administrators. History of appointment and removal is kept. |
| 7. Desktop / iPhone / Print relevance | No current screen change. Print unchanged. |
| Do not | Final Manual prose. Claim People & Access exists. Claim a live System Administrator exists. Claim Completion Sign-Off exists. |

### MANUAL IMPACT — D5 VOICE WITH HELP (2026-09-19)

| Field | Content |
|-------|---------|
| Slice | D5 Voice with Help |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED.** Product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. Same Help authority as D1–D4. Typed and spoken questions share `answer_help_question()`. Browser speech only. No provider. No schema. Voice does not change the job. User Guide remains outstanding. |
| 1. What new contractor capability exists? | After opening Help, the contractor can type a question or tap Ask by speaking. Help answers from the current screen. The answer is shown as text. Speak answer is optional where the browser can speak. |
| 2. When would the contractor use it? | When the static Help is not enough and they want to ask what this screen is, what they can do, why something is blocked, or what is next. |
| 3. What workflow will the final Manual need to teach? | Open Help. Read it, or type/ask by speaking. Help explains. It does not close a Project, approve Time, or add Punch List items. If the microphone is not available, type instead. |
| 4. What contractor-facing terms must be used? | Help. Ask about this screen. Ask by speaking. Speak answer. Stop speaking. |
| 5. What screenshots / Print examples will eventually be needed? | Office Help with the question box open. Field Help with Ask by speaking. An example typed answer. Capture after later SHA, not this working tree. |
| 6. What warnings / validation distinctions need explanation? | Microphone is requested only when Ask by speaking is used. Help does not change the job. Field Company today is not Company Attention. This is not general construction advice. |
| 7. Desktop / iPhone / Print relevance | Office desktop and Field iPhone both use the same Help question path. Print unchanged. |
| Do not | Final Manual prose. Claim Voice is a chatbot or action engine. Claim LEARN is live. Claim People & Access exists. Claim Completion Sign-Off exists. Claim a new Help knowledge base exists. |

### MANUAL IMPACT — D4 FIELD HELP (2026-09-19)

| Field | Content |
|-------|---------|
| Slice | D4 Field Help |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED.** Product SHA **`e7c3fb35a1b1c4519c387a71eb8f7e81a6cc1169`**. Same Help authority as D1/D3. Native expandable Help on high-value Field screens. LEARN remains Future. Informational only. No schema. No Voice. Contextual Help coverage complete for Hub / Office / Field. Voice and User Guide remain outstanding. |
| 1. What new contractor capability exists? | On Field Today, This week, This month, Company today, Projects, Capture, Time, My time, and Extra work, the contractor can open Help and read what the screen is, what to do there, and what normally follows. |
| 2. When would the contractor use it? | When first using a Field screen on iPhone, or when unsure what the screen is for or what to do next. |
| 3. What workflow will the final Manual need to teach? | Open Help on the Field screen being used. Help stays collapsed until opened. Help does not save work, change dates, or capture media. Company today is a schedule view and is not Company Attention. |
| 4. What contractor-facing terms must be used? | Help. Today. This week. This month. Company today. Projects. Capture. Time. My time. Extra work. |
| 5. What screenshots / Print examples will eventually be needed? | Field Today Help open on a narrow iPhone viewport. Company today Help. Capture Help. Time Help. Capture after Field restart onto this working tree / later SHA. |
| 6. What warnings / validation distinctions need explanation? | Company today does not change dates. Closed jobs are not operated from Field. Time records hours only. Capture saves observations to the confirmed Project. |
| 7. Desktop / iPhone / Print relevance | iPhone Field first. Office Help unchanged. Print unchanged. |
| Do not | Final Manual prose. Claim Voice exists. Claim LEARN is live. Claim People & Access exists. Claim Completion Sign-Off exists. Claim Company Attention exists in Field. |

### MANUAL IMPACT — D3 OFFICE HELP (2026-09-19)

| Field | Content |
|-------|---------|
| Slice | D3 office Help |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED.** Product SHA **`61f86789ae4e755fb39b3d65cbfee6a481ab15e8`**. Same Help authority as D1. Native expandable Help on high-value office screens. LEARN remains Future. Informational only. No schema. No Voice. Help product overall **PARTIAL**. |
| 1. What new contractor capability exists? | On Dashboard, Clients, Projects Current/Closed, Schedule, Company Attention, Estimates, Previous estimates, Cost library, Settings/Brand Profile, Permit report, Job location, Time, and Change Orders, the contractor can open Help and read what the screen is, what to do there, and what normally follows. |
| 2. When would the contractor use it? | When first using an office screen, or when unsure what the screen is for or what to do next. |
| 3. What workflow will the final Manual need to teach? | Open Help on the office screen being used. Treat LEARN as Future. Help does not save work. Company Attention Help appears only with Company/Management access. Punch List and Final Walkthrough Help remain on the Project Hub BUILD section. |
| 4. What contractor-facing terms must be used? | Help. What is this? What should I do here? What happens next? Previous estimates. Cost library. Gross Margin Pricing. Municipality or permit office. Job location. Current vs Closed. Company Attention. Brand Profile. |
| 5. What screenshots / Print examples will eventually be needed? | Dashboard Help open. Projects Current vs Closed Help. Company Attention Help. Previous estimates Help. Permit report Help. Capture after office restart onto this working tree / later SHA. |
| 6. What warnings / validation distinctions need explanation? | Permit report is not municipal approval. Closed Projects must be reopened before new operational work. Previous estimates are evidence, not a current estimate. Cost library is not an estimate. Client records are not Final Walkthrough access. Punch List completion does not complete a Change Order. |
| 7. Desktop / iPhone / Print relevance | Office desktop and narrow office/mobile-browser width. Field Help not added. Print unchanged. |
| Do not | Final Manual prose. Claim Voice exists. Claim Field Help exists. Claim LEARN is live. Claim People & Access exists. Claim Completion Sign-Off exists. |

### MANUAL IMPACT — D2 BOUNDED CONTRACTOR-LANGUAGE RESIDUALS (2026-09-19)

| Field | Content |
|-------|---------|
| Slice | D2 bounded contractor-language residuals |
| Product status at capture | **IMPLEMENTED.** Presentation/language/navigation only. D1 Help unchanged. Help product overall **PARTIAL**. |
| 1. What new contractor capability exists? | The Project Hub PRICE list, previous-estimate screens, permit screens, header Settings, and cost library now use ordinary construction/business wording. |
| 2. When would the contractor use it? | Whenever opening those existing screens. No new workflow. |
| 3. What workflow will the final Manual need to teach? | Header gear opens Settings. Cost library holds reusable unit costs. Previous estimates are uploaded past jobs, not live pricing. Permit report is advisory, not municipal approval. Hub PRICE shows whether pricing was recorded, not the internal method key. |
| 4. What contractor-facing terms must be used? | Gross Margin Pricing. Pricing recorded. Labour rates recorded. Previous estimates. Cost library. Settings. Advisory only. Municipality or permit office. Job location. |
| 5. What screenshots / Print examples will eventually be needed? | Hub PRICE table. Header Settings gear. Previous estimates list. Cost library. Permit report banner. Capture after office restart onto this SHA. |
| 6. What warnings / validation distinctions need explanation? | Recorded pricing is not a recalculation. A passing permit check is not a permit. Previous estimates are evidence, not the live cost model. |
| 7. Desktop / iPhone / Print relevance | Office desktop. Permit PDF banner updated. Field unchanged. |
| Do not | Final Manual prose. Claim Voice exists. Claim office/Field Help exists. Claim LEARN is live. Claim FG-025 closed. |

### MANUAL IMPACT — D1 PROJECT HUB CONTEXTUAL HELP (2026-09-19)

| Field | Content |
|-------|---------|
| Slice | D1 Project Hub contextual Help |
| Product status at capture | **IMPLEMENTED.** Static Help content authority. Native expandable Help on Project Hub PLAN / PRICE / CONTRACT / BUILD / MONITOR. LEARN remains Future. Informational only. No schema. No Voice. Help product overall **PARTIAL**. |
| 1. What new contractor capability exists? | On the Project Hub, the contractor can open Help beside each lifecycle area and read what the area is, what to do there, and what normally follows. |
| 2. When would the contractor use it? | When first using a Project, or when unsure which Hub area to work in next. |
| 3. What workflow will the final Manual need to teach? | Open a Project. Use Help on PLAN, PRICE, CONTRACT, BUILD, and MONITOR. Treat LEARN as Future. Help does not save work. |
| 4. What contractor-facing terms must be used? | Help. What is this? What should I do here? What happens next? PLAN. PRICE. CONTRACT. BUILD. MONITOR. LEARN · Future. Permit report is not municipal approval. Client comments are not the Punch List until accepted. Monitor is not a profit figure. |
| 5. What screenshots / Print examples will eventually be needed? | Hub with Help closed. One Help panel open on PLAN. LEARN Future Help. Capture after office restart onto this SHA. |
| 6. What warnings / validation distinctions need explanation? | Opening Help does not change the job. Production contract generation is not available. LEARN does not recommend or calibrate. |
| 7. Desktop / iPhone / Print relevance | Office desktop Project Hub. Not Field. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim Voice exists. Claim office/Field Help exists. Claim LEARN is live. |

### MANUAL IMPACT — CORE CLOSE C2 CLIENT FINAL WALKTHROUGH (2026-09-19)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE C2 Client Final Walkthrough |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH CLIENT DATA.** Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Additive **`e5f6a7b8c9d0` applied live**. No live invitations. |
| 1. What new contractor capability exists? | On an ACTIVE Project Hub, authorized Project users can Invite Client to Final Walkthrough, copy a secure no-login link, see client response state, and review each client-submitted item. Actions: Add to Punch List (after choosing Original Scope / Change Order / Other), Already Addressed, or Discuss / Not Part of Current Work. |
| 2. When would the contractor use it? | Near Project completion, to give the client a simple chance to say what still needs attention. Client comments are not the Punch List until the contractor accepts them. |
| 3. What workflow will the final Manual need to teach? | Open Project Hub Client Final Walkthrough. Invite. Copy the link and send it outside the product if email is not configured. Review each item. Add accepted items to Punch List with a work source. Manage those items on the existing Punch List. Closed Projects show history only. |
| 4. What contractor-facing terms must be used? | Final Walkthrough. Invite Client to Final Walkthrough. Client input awaiting review. Add to Punch List. Already Addressed. Discuss / Not Part of Current Work. Everything looks complete — I have nothing to add. Not Punch List for the client-facing form. |
| 5. What screenshots / Print examples will eventually be needed? | Hub not-sent / sent / awaiting review / nothing-to-add. Copyable invite link. Client phone form. Capture after live migrate / UAT. |
| 6. What warnings / validation distinctions need explanation? | Client response is not Completion Sign-Off. Nothing-to-add does not close the Punch List. Pending client input does not block Close. Closed Project blocks new invitations until Reopen. |
| 7. Desktop / iPhone / Print relevance | Office desktop Hub invite/review. Client form is mobile-first in the browser. No Field chrome. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim Completion Sign-Off exists. Claim email/SMS delivery is live. Claim live invitations happened. |

### MANUAL IMPACT — CORE CLOSE C1 CONTRACTOR PUNCH LIST (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE C1 Contractor Punch List |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH MUTATING DATA.** Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Additive **`d4e5f6a7b8c9` applied live**. Live Punch List items **0**. |
| 1. What new contractor capability exists? | On an ACTIVE Project Hub, authorized Project users can add Punch List items describing unfinished physical work, associate them with Original Scope or an existing Change Order or Other closeout work, mark them Complete, and Reopen if the work is not actually done. Summary states open/complete counts, Punch List complete, or Nothing is on the Punch List. |
| 2. When would the contractor use it? | When physical work still needs to be completed before later Completion Sign-Off. Not for Change Order paperwork, invoices, or client communication history. |
| 3. What workflow will the final Manual need to teach? | Open Project Hub BUILD Punch List. Add an item with a plain description and work source. Mark Complete when the physical work is done. Reopen if it was marked complete too soon. Closed Projects show Punch List history only. |
| 4. What contractor-facing terms must be used? | Punch List. Open. Complete. Add Punch List Item. Mark Complete. Reopen. Original Scope. Change Order. Other closeout work. Punch List complete. Nothing is on the Punch List. |
| 5. What screenshots / Print examples will eventually be needed? | Active Hub Punch List empty, with open items, and complete. Add form. Closed Hub history view. Capture after live migrate / UAT. |
| 6. What warnings / validation distinctions need explanation? | Closed Project blocks Punch List changes until Reopen Project. Completing a Punch List item does not complete the Change Order. Client comments later are not Punch List items until the contractor accepts them. Zero items is not a fake “no deficiencies” row. |
| 7. Desktop / iPhone / Print relevance | Office desktop/tablet Hub only. No Field Punch List. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim Client Final Walkthrough exists. Claim Completion Sign-Off exists. Claim live migrate happened. |

### MANUAL IMPACT — CORE CLOSE CLOSE/REOPEN OPTION A (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE Close/Reopen Option A |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed.** Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. No live Close. All live Projects remain ACTIVE. Authorization is Instance Owner / future System Administrator. `COMPANY_MANAGEMENT` is not Close/Reopen authority. |
| 1. What new contractor capability exists? | Authorized Instance Owner can **Close Project** and **Reopen Project** from the Project Hub after a dedicated confirmation page. Hub shows lifecycle identity **Current** or **Closed**. Closed Hub hides **New Change Order**. Projects list **Current \| Closed** already existed from Slice B and now actually receives Closed Projects after Close. |
| 2. When would the contractor use it? | When a Project should leave current operating work, or when a Closed Project must return to current operating work. Not after Punch List / Completion Sign-Off (those products do not exist yet). |
| 3. What workflow will the final Manual need to teach? | Open the Project Hub. Confirm Close. Find the Project under Closed. Open it historically. Reopen from the Closed Hub when new work is required. Ordinary users do not see Close/Reopen. |
| 4. What contractor-facing terms must be used? | Current. Closed. Close Project. Reopen Project. This Project is closed. This Project is current. This Project is already closed. This Project is already current. Not Archive. |
| 5. What screenshots / Print examples will eventually be needed? | Active Hub Close action. Close confirmation. Closed Hub identity and Reopen. Closed Hub without New Change Order. Projects Current vs Closed after a real Close. Capture after live Close/Reopen UAT exists. |
| 6. What warnings / validation distinctions need explanation? | Repeat Close or Reopen fails visibly. Close does not rewrite history. Closed blocks new work. Existing Time / Change Order paperwork can still finish. Incomplete physical work is Punch List later, not this slice. |
| 7. Desktop / iPhone / Print relevance | Desktop Hub and confirmation pages. Field already hides closed current work from Slice B. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim Punch List exists. Claim Completion Sign-Off exists. Claim live Close was executed. |

### MANUAL IMPACT — CORE CLOSE SLICE B (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE Slice B current-operating consumers + CLOSED guards |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION.** Product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**. No live Close. All live Projects remain ACTIVE. Close/Reopen UI does not exist. |
| 1. What new contractor capability exists? | Projects list **Current \| Closed** (default Current). CLOSED Projects stay reachable from Closed and from the Project Hub. New work on a closed Project is refused with: “This Project is closed. Reopen it before adding new work.” |
| 2. When would the contractor use it? | After a Project is Closed (not yet possible from the product). Until then Current looks like today’s Projects list. |
| 3. What workflow will the final Manual need to teach? | Find a closed Project under Closed. Open the Hub historically. Do not add new Time, Schedule, Extra Work, Change Orders, or Field capture until Reopen exists. Finish existing Time / Change Order paperwork. |
| 4. What contractor-facing terms must be used? | Current. Closed. This Project is closed. Reopen it before adding new work. Not Archive. |
| 5. What screenshots / Print examples will eventually be needed? | Projects Current vs Closed. Closed Project Hub. The closed-Project error. Capture after Close/Reopen exists. |
| 6. What warnings / validation distinctions need explanation? | Closed blocks new work. Existing submitted Time can still be approved or returned. Returned Time can be corrected and sent again. Existing Change Order status can still move; new lines and rewritten Draft scope cannot. Incomplete physical work is Punch List later, not this slice. |
| 7. Desktop / iPhone / Print relevance | Desktop Projects Current \| Closed. Field picker/Today/Week/Month hide closed current work. iPhone Field capture/extra work fail closed if the selected Project is closed. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim Close/Reopen exists. Claim Punch List exists. |

### MANUAL IMPACT — CORE CLOSE SLICE A LIVE MIGRATION (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE Slice A live migration |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED.** Product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. Live Alembic **`b2c3d4e5f6a7 (head)`**. All existing Projects **ACTIVE**. Event rows **0**. No Close UI. No Punch List. No Completion Sign-Off. No contractor-facing lifecycle change. |
| 1. What new contractor capability exists? | None now. Schema is live. Close remains unimplemented. |
| 2. When would the contractor use it? | Not yet. Later Close / Punch List / Completion Sign-Off surfaces. |
| 3. What workflow will the final Manual need to teach? | Same as the owner freeze. |
| 4. What contractor-facing terms must be used? | Close Project. Reopen Project. Punch List. Project Completion Sign-Off. Current operating work. |
| 5. What screenshots / Print examples will eventually be needed? | None now. |
| 6. What warnings / validation distinctions need explanation? | Open Punch List blocks Completion Sign-Off. Incomplete physical work is Punch List work. NEW Change Order after Close requires Reopen. |
| 7. Desktop / iPhone / Print relevance | None now. |
| Do not | Final Manual prose. Unstable screenshots. Claim Close exists. Claim Punch List exists. |

### MANUAL IMPACT — CORE CLOSE SLICE A (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE Slice A foundation |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED.** Product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. No Close UI. No Punch List. No Completion Sign-Off. No contractor-facing lifecycle change. |
| 1. What new contractor capability exists? | None now. Foundation only. |
| 2. When would the contractor use it? | Not yet. Later Close / Punch List / Completion Sign-Off surfaces. |
| 3. What workflow will the final Manual need to teach? | Same as the owner freeze: current vs historical work; Punch List before Completion Sign-Off; physical work vs administrative Change Order completion. |
| 4. What contractor-facing terms must be used? | Close Project. Reopen Project. Punch List. Project Completion Sign-Off. Current operating work. Do **not** treat Change Order status as physical completion. |
| 5. What screenshots / Print examples will eventually be needed? | None now. Capture later against finished Close / Punch List / Completion Sign-Off surfaces. |
| 6. What warnings / validation distinctions need explanation? | Open Punch List blocks Completion Sign-Off. Incomplete physical work on Original Scope or an existing Change Order is Punch List work, not administrative completion. NEW Change Order after Close requires Reopen. |
| 7. Desktop / iPhone / Print relevance | None now. |
| Do not | Final Manual prose. Unstable screenshots. Claim Close exists. Claim Punch List exists. |

### MANUAL IMPACT — CORE CLOSE OWNER FREEZE (2026-09-18)


| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE / Project lifecycle owner freeze |
| Product status at capture | **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** Canonical [core-close-project-lifecycle-product-direction.md](core-close-project-lifecycle-product-direction.md). No Close UI. No Punch List. No Completion Sign-Off. |
| 1. What new contractor capability exists? | None now. Direction recorded: Projects can later leave current operating work without deleting history. Punch List then Project Completion Sign-Off then Close Project. |
| 2. When would the contractor use it? | After work is substantially complete: walkthrough, Punch List, customer/contractor Completion Sign-Off, then Instance Owner / Sys Admin Close. Reopen if the Project must return to current work. |
| 3. What workflow will the final Manual need to teach? | What is current operating work vs historical Project? Who may Close/Reopen? Why Punch List must be complete before Completion Sign-Off can be signed. Why Close can still proceed with a strong warning if the customer has not signed. Why history remains. |
| 4. What contractor-facing terms must be used? | Close Project. Reopen Project. Punch List. Project Completion Sign-Off. Current operating work. Historical Project. Do **not** use: archive (as a third operating state), delete Project, release, waiver, LEARN Closeout, paid in full as a Close rule. |
| 5. What screenshots / Print examples will eventually be needed? | None now. Capture later against the finished Close / Punch List / Completion Sign-Off surfaces. |
| 6. What warnings / validation distinctions need explanation? | Open Punch List blocks Completion Sign-Off signature eligibility. Missing executed Completion Sign-Off warns on Close and does not hard-block Close. Other pending Time/CO warnings inform. Close does not rewrite history. |
| 7. Desktop / iPhone / Print relevance | Completion Sign-Off is intended for desktop/tablet review and generated PDF. Field Punch List is **not frozen**. Print later. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim Close exists. Claim Punch List exists. Claim LEARN Closeout exists. Claim ARCHIVED operating state. |

### MANUAL IMPACT — PERF-C LIVE UAT / SEAL (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 PERF-C Company Attention live UAT / seal |
| Product status at capture | **CURRENT** — PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED**. Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. Evidence [testing/fg035-perf-c-live-uat-record.md](../testing/fg035-perf-c-live-uat-record.md). |
| 1. What new contractor capability exists? | Joel can open office Company Attention and see where the business needs attention across the company’s Projects. Another office user without Company / Management permission cannot. Field does not show Company Attention. |
| 2. When would the contractor use it? | Opening the office to ask: Where does my business need attention? Then following Review to the existing Project destination. |
| 3. What workflow will the final Manual need to teach? | What is Company Attention? Why can Joel see it and AUTH-B cannot? Why is it not in Field? What does each Needs Attention item mean (reuse PERF-B language)? Why leftover test Projects can currently appear in the list until a later Project lifecycle exists. |
| 4. What contractor-facing terms must be used? | Company Attention. Where does my business need attention? Nothing needs attention right now. Extra work needs review. Labour getting close. Labour allowance used. Labour over allowance. Scheduled finish passed. Scheduled work has no approved Time. Do **not** use: Home Office, scorecard, health, risk, severity, RBAC, Active/Archived. |
| 5. What screenshots / Print examples will eventually be needed? | Quiet positive. Several Projects. One Project with several items. Capture later against finished Manual sequencing. Do **not** treat current UAT-vessel occupancy as the customer screenshot set. |
| 6. What warnings / validation distinctions need explanation? | Company Attention does **not** stop work. It does **not** acknowledge or resolve items. Project access does **not** give Company Attention. Company Attention does **not** give Sensitive Financial. Field Company Today is a different screen. Historical / test Projects may currently appear because Company Attention is organization-wide. |
| 7. Desktop / iPhone / Print relevance | Office / management desktop first. Adaptive office layout. Field unchanged. Print later. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim Home Office. Claim Sensitive Financial. Claim People & Access. Claim FG-035 closed. Invent Active/Archived filtering. |

### MANUAL IMPACT — PERF-C (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 PERF-C Company Attention |
| Product status at capture | **CURRENT** — PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-UATed**. Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. Not live-UATed. |
| 1. What new contractor capability exists? | Office Company Attention lists where the business needs attention across the company’s Projects, or says nothing needs attention right now. It is not Field Company Today. It is not Home Office. |
| 2. When would the contractor use it? | Opening the office to ask: Where does my business need attention? Then following the existing Project review link for that item. |
| 3. What workflow will the final Manual need to teach? | What is Company Attention? Why can Joel see it and another office user cannot? Why is it not in Field? What does each Needs Attention item mean (reuse PERF-B language)? What happens when nothing needs attention? |
| 4. What contractor-facing terms must be used? | Company Attention. Where does my business need attention? Nothing needs attention right now. Extra work needs review. Labour getting close. Labour allowance used. Labour over allowance. Scheduled finish passed. Scheduled work has no approved Time. Do **not** use: Home Office, scorecard, health, risk, severity, RBAC. |
| 5. What screenshots / Print examples will eventually be needed? | Quiet positive. One Project with several items. Several Projects. Do **not** capture now. Surface is uncommitted and not live-UATed. |
| 6. What warnings / validation distinctions need explanation? | Company Attention does **not** stop work. It does **not** acknowledge or resolve items. Project access does **not** give Company Attention. Company Attention does **not** give Sensitive Financial. Field Company Today is a different screen. |
| 7. Desktop / iPhone / Print relevance | Office / management desktop first. Adaptive layout. Field unchanged. Print later. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim live UAT. Claim Home Office. Claim Sensitive Financial. Claim People & Access. |

### MANUAL IMPACT — FG-037 (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-037 Company / Management access-domain authorization |
| Product status at capture | **CURRENT** — FG-037 **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION**. Product SHA **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`**. No Company Attention screen. |
| 1. What new contractor capability exists? | Company / Management information is now a separate permission. Joel Brayman (Membership 1) has it. Other current users do not, unless Joel later grants them. |
| 2. When would the contractor use it? | Later, when Company Attention / company screens exist. Today there is no Company screen. The permission is already stored so those screens can be added later without giving every office user company access. |
| 3. What workflow will the final Manual need to teach? | Who can see company / management information? Why can Joel see it and another office user cannot? Why does Field still not show Company Attention? How is permission granted later (not a Settings Members screen today)? |
| 4. What contractor-facing terms must be used? | Company / Management. Project / Operational. Do **not** use: RBAC, role, admin, manager permission, Sensitive Financial (not implemented). |
| 5. What screenshots / Print examples will eventually be needed? | None now. Capture Company Attention later when PERF-C exists. Do **not** screenshot Field as if Company Attention lives there. |
| 6. What warnings / validation distinctions need explanation? | Having Project access does **not** give Company / Management access. Having Company / Management access does **not** give Sensitive Financial access. Ben is intended to have the same company permission later, after a real Ben account exists. |
| 7. Desktop / iPhone / Print relevance | Office / management only. Field unchanged. Print later. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim PERF-C exists. Claim Sensitive Financial exists. Claim Ben already has access. |

### MANUAL IMPACT — PERF-B (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 PERF-B Project Needs Attention |
| Product status at capture | **CURRENT** — PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. Project **50**. Product SHA **`dcde4adfe4a475932b7f144b0220b2b60e4bd75c`**. |
| 1. What new contractor capability exists? | On the Project Labour section, Needs Attention lists factual things to look at, or says nothing needs attention right now. It sits above Allowed / Used / Remaining. |
| 2. When would the contractor use it? | Opening a Project and asking whether anything about this job needs a look. Checking labour getting close, extra work, a scheduled finish that has already passed, scheduled work with no approved Time, or a schedule warning. |
| 3. What workflow will the final Manual need to teach? | What does Needs Attention mean? Does Needs Attention stop me from working? Why does Labour getting close appear? What does Labour allowance used mean? What does Labour over allowance mean? Why does Extra Work need review? What does Scheduled finish passed mean? Why does CalibraytAI say scheduled work has no approved Time? |
| 4. What contractor-facing terms must be used? | Needs attention. Extra work needs review. Labour getting close. Labour allowance used. Labour over allowance. Scheduled finish passed. Scheduled work has no approved Time. Nothing needs attention right now. Do **not** use: threshold breach, attention DTO, risk, severity, scope lineage, schedule conflict algorithm. |
| 5. What screenshots / Print examples will eventually be needed? | Quiet positive state. Labour getting close. Labour over allowance. Extra work needs review. Scheduled finish passed. Scheduled work has no approved Time. Schedule warning. Do **not** capture now. Final Manual later. |
| 6. What warnings / validation distinctions need explanation? | Needs Attention does **not** stop Time, Schedule, Change Orders, or Project work. It is information only. Waiting for approval is not its own Needs Attention item. Labour getting close means Used has reached 80% of Allowed; it is not a verdict that the job is going badly. Labour allowance used means Used equals Allowed. Labour over allowance means Used is more than Allowed. Extra work needs review while extra work still has used or waiting hours and is not yet authorized. Scheduled finish passed means the scheduled end date is before today; it does not mean the work is late or incomplete. Scheduled work has no approved Time means the scheduled start is before today and that scheduled work still has no approved Time; it does not mean the work has not started. |
| 7. Desktop / iPhone / Print relevance | Desktop / office Project Hub Labour. Field is unchanged. Print later. Bounded synthetic live UAT **PASS** on Project **50**. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim FG-035 closed. PERF-C. |

### MANUAL IMPACT — PERF-A (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 PERF-A Project Hub Labour Allowed · Used · Remaining |
| Product status at capture | **SUPERSEDED AS CURRENT** for newest Manual Impact by PERF-B. PERF-A product remains **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**. Project **49**. |
| 1. What new contractor capability exists? | On the Project page, after Time and before MONITOR, a Labour section shows how many hours are Allowed, Used, and Remaining (or Over by). It also shows hours Waiting for approval. Extra work is listed separately while it is still extra work. After a Change Order authorizes that extra work, those hours move into Authorized labour. |
| 2. When would the contractor use it? | Checking how a job is doing on labour. Asking how many hours are left. Seeing whether extra work time is sitting outside the authorized allowance. Checking labour again after extra work is authorized. |
| 3. What workflow will the final Manual need to teach? | How many labour hours do we have left? What is Used? What is Waiting for approval? What does Over by mean? Why is Extra Work shown separately? What happens after Extra Work is authorized? What does Allowance not available mean? |
| 4. What contractor-facing terms must be used? | Labour. Allowed. Used. Remaining. Waiting for approval. Over by. Extra work. Allowance not available. Needs review. Do **not** use: current_authorized_hours, scope_origin, hours_delta, DTO, performance engine, variance denominator. |
| 5. What screenshots / Print examples will eventually be needed? | Project Labour with Allowed / Used / Remaining. Over by example. Extra work with Needs review. Same job after Extra Work is authorized (Extra Work gone; hours in Authorized). Allowance not available. Do **not** capture now. Final Manual later. |
| 6. What warnings / validation distinctions need explanation? | Over by and Needs review are information only. They do not stop Time, Schedule, Change Orders, or Project work. Waiting for approval does not reduce Remaining. Used is approved hours only. Extra work stays separate until that work is authorized; then it is no longer Extra Work on Labour. Time Extra work hours can still show frozen extra-work time until Time’s own summary catches up — that is Time, not Labour. Allowance not available means there is no governed allowance to compare against, not that Allowed is zero. Allowed zero is a known allowance. |
| 7. Desktop / iPhone / Print relevance | Desktop / office Project Hub. Field is unchanged. Print later. Bounded synthetic live UAT **PASS** on Project **49**. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim FG-035 closed. PERF-B Needs Attention. |

### MANUAL IMPACT — SCH-D PHYSICAL IPHONE UAT PASS (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Today / Week / Month + schedule-assisted Time + job-site Directions |
| Product status at capture | **SUPERSEDED AS CURRENT** for newest Manual Impact by PERF-A. SCH-D Field product remains **PHYSICAL IPHONE UAT PASS**. G1–G6 **PHYSICAL PASS**. Directions + native iOS return **PHYSICAL PASS**. |
| 1. What new contractor capability exists? | See today’s work, this week, this month, and company today. See the job-site address. Tap Directions to open the phone’s maps. Enter Time from scheduled work, or choose the work actually done. Native iPhone return brings the worker back to CalibraytAI. |
| 2. When would the contractor use it? | Opening Field in the morning. Driving to the job. Checking what others are doing today. Entering hours. Looking at the month calendar. |
| 3. What workflow will the final Manual need to teach? | What am I doing today? What is coming this week? What is coming this month? How do I see what the company is doing today? What does Assigned to me mean? What does Crew work mean? How do I enter Time from today’s work? What if I have more than one scheduled job? What if the work I did was not scheduled? What does a Schedule warning mean? How do I get directions to today’s job? How do I return to CalibraytAI after opening Directions? How do I add CalibraytAI to my iPhone Home Screen? After opening Directions, use the iPhone’s native return-to-Safari control to return to CalibraytAI. |
| 4. What contractor-facing terms must be used? | Today. This week. This month. Company today. My work. Assigned to me. Crew work. Address. Directions. Enter time. Scheduled today. Working somewhere else? Choose different work. This is information only. Do **not** use: maps.apple.com, daddr, deep link, URL scheme, GPS, overlay, WorkScheduleItem. |
| 5. What screenshots / Print examples will eventually be needed? | Today with address + Directions. Company Today. This Week grouped by day/Project. Month calendar. Time from scheduled work. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | Schedule warnings are information only and do not block Time. Missing job-site address omits Directions; that is not a blocking warning. Time does not change Schedule. |
| 7. Desktop / iPhone / Print relevance | iPhone Field is the accepted physical surface. Desktop plans dates. Print later. Home Screen is an iPhone install topic, not a CalibraytAI navigation feature. |
| Do not | Final Manual prose. Unstable screenshots. Embedded maps. Custom return button. PERF. Claim FG-035 closed. |

### MANUAL IMPACT — SCH-D JOB-SITE LOCATION / DIRECTIONS UAT CORRECTION (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D job-site location + Directions physical UAT correction |
| Product status at capture | **SUPERSEDED AS CURRENT** by SCH-D PHYSICAL IPHONE UAT PASS. G2/G3/G4 later **PHYSICAL PASS**. |
| 1. What new contractor capability exists? | Scheduled Field work shows the job-site address. Directions hands that destination to the phone’s maps app. |
| 2. When would the contractor use it? | Opening Today, Company today, or This week to see where the job is, then tapping Directions to get there. |
| 3. What workflow will the final Manual need to teach? | How do I get directions to today’s job? See the job address. Tap Directions. Use the phone’s navigation. |
| 4. What contractor-facing terms must be used? | Address. Directions. Today. Company today. This week. Do **not** use: maps.apple.com, daddr, geocode, URI, GPS. |
| 5. What screenshots / Print examples will eventually be needed? | Today work with address + Directions. Company Today. This Week grouped by day/Project. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | If a Project has no address, Directions is not shown. That is not a blocking warning. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Today / Company Today / Week. Month calendar layout preserved. Time unchanged. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim G2/G3/G4 physical PASS. Embedded maps. GPS. PERF. |

### MANUAL IMPACT — SCH-D ADDRESS / DIRECTIONS / MONTH CALENDAR (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Project address, Directions, Month calendar + day detail |
| Product status at capture | **SUPERSEDED AS CURRENT** by SCH-D JOB-SITE LOCATION / DIRECTIONS UAT CORRECTION. G5 Month **PHYSICAL PASS**. G1/G6 later PASS. |
| 1. What new contractor capability exists? | Field shows the Project/job-site address with the work. Directions sends that address to the phone’s mapping app. This Month is a calendar; tap a day to see that day’s work below. |
| 2. When would the contractor use it? | Opening Today / Company Today / This Week to see where the job is. Tapping Directions to get there. Opening This Month to see when work is happening, then tapping a day. |
| 3. What workflow will the final Manual need to teach? | Where is today’s job? How do I get directions to the job? How do I see where I’m working this week? How do I use the Month calendar? How do I tap a day to see its work? |
| 4. What contractor-facing terms must be used? | Project. Address. Directions. Today. Company today. This week. This month. Previous month. Next month. No scheduled work for this day. Do **not** use: maps.apple.com, daddr, geocode, URI, GPS, navigation provider. |
| 5. What screenshots / Print examples will eventually be needed? | Today with address + Directions. Company Today grouped. Week with address once per Project. Month calendar + selected-day detail. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | If a Project has no address, Directions is not shown. Directions does not track the worker. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Today / Company Today / Week / Month. Desktop office Project Address remains the source. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim Month or Directions physical PASS. Embedded maps. GPS tracking. Landscape work. PERF. |

### MANUAL IMPACT — SCH-D UX #5 (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Time Date, Field landscape, Back to Today |
| Status | **SUPERSEDED AS CURRENT** by SCH-D ADDRESS / DIRECTIONS / MONTH CALENDAR. Date **PHYSICAL PASS**. Portrait **PASS**. Enter Time speed **QUICK**. F4 Back to Today **PHYSICAL PASS / IMMEDIATE**. |
| 1. What new contractor capability exists? | One Date control with no blank extra box. Today and Time use the wide landscape Field shell. Back to Today should feel like other Field pages. Native calendar chrome on Date is not shown. |
| 2. When would the contractor use it? | Entering Time. Rotating the phone. Returning from Time to Today. |
| 3. What workflow will the final Manual need to teach? | Open Time. Choose Date. Rotate for landscape. Back to Today. |
| 4. What contractor-facing terms must be used? | Date. Time. Today. Back to Today. Do **not** use: calendar-picker-indicator, IndexedDB, media query. |
| 5. What screenshots / Print examples will eventually be needed? | Time Date. Today landscape. Time landscape. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | Unchanged. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Today / Time. Desktop office unchanged. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim UX #5 physical PASS. PERF. |

### MANUAL IMPACT — SCH-D UX #4 (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Time Date containment + landscape width + Field action responsiveness |
| Status | **SUPERSEDED AS CURRENT** by SCH-D UX #5. Portrait and Enter Time speed remain physical PASS. |
| 1. What new contractor capability exists? | Time Date stays inside the Time card. Field uses the wider landscape viewport. Enter Time / Today / This Week / This Month / Company Today should feel prompt on the phone (Google Fonts no longer block Field pages). |
| 2. When would the contractor use it? | Opening Field, rotating to landscape, tapping Enter Time. |
| 3. What workflow will the final Manual need to teach? | Open Time. Date stays in the card. Rotate for a wider Field layout. Identity remains **My Work — Joel**. |
| 4. What contractor-facing terms must be used? | My Work — Joel. Date. Time. Today. Enter Time. Do **not** use: overflow, media query, viewport, IndexedDB, webfont. |
| 5. What screenshots / Print examples will eventually be needed? | Time Date inside the card. Landscape using the width. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | Unchanged. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Time / Today / Week / Month. Desktop office layout unchanged. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim UX #4 physical PASS. PERF. Record “landscape is slow.” |

### MANUAL IMPACT — SCH-D UX #3 (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Today / Time physical UX #3 (identity + Date + landscape) |
| Status | **SUPERSEDED AS CURRENT** by SCH-D UX #4. **My Work — Joel** remains a physical PASS. |
| 1. What new contractor capability exists? | Today heading **My Work — Joel** (first name). Time Date label and control are sibling fields. Landscape again uses the FG-021 two-column Field layout. |
| 2. When would the contractor use it? | Opening Today to see whose work is shown. Entering Time on iPhone in portrait or landscape. |
| 3. What workflow will the final Manual need to teach? | Open Today. Confirm **My Work — first name**. Enter Time. Rotate the phone for landscape. Schedule remains the plan. |
| 4. What contractor-facing terms must be used? | My Work — Joel. Date. Today. Time. Do **not** use: overlay, User id, overflow-x, media query. |
| 5. What screenshots / Print examples will eventually be needed? | Today **My Work — Joel**. Time Date aligned. Landscape two-column Field. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | Unchanged. Warnings remain information only. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Today / Time. Desktop Schedule unchanged. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim UX #3 physical PASS. PERF. |

### MANUAL IMPACT — SCH-D UX #2 (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Today / Time presentation (physical UAT UX #2) |
| Status | **SUPERSEDED AS CURRENT** by SCH-D UX #3 above for Today identity / Time Date / landscape. Scheduled Time remains **PHYSICAL PASS**. |
| CONTRACTOR CAPABILITY | See weekday and natural date on Today. My work does not repeat the worker’s own name. On Time: **Scheduled today** then **Working somewhere else?** / **Choose different work** to record actual work that was not the plan. |
| WHEN USED | When a worker opens Field, and when Ben sends them to another job without changing the Schedule first. |
| FINAL MANUAL WORKFLOW TO TEACH | Open Today. Read the weekday and date. Read My work. Enter time from scheduled work, or tap **Working somewhere else?** / **Choose different work** and pick the work actually done. Schedule stays as planned. |
| CONTRACTOR-FACING TERMS | Today. Wednesday / natural month day. My work. Scheduled today. Working somewhere else? Choose different work. Send time. Do **not** use: overlay, ad-hoc assignment record, RBAC. |
| WARNINGS / VALIDATION | Warnings remain information only. Time does not update Schedule. Unscheduled valid work remains choosable. |
| DESKTOP | Schedule planning unchanged. |
| IPHONE | YES — Field Today / Time. Scheduled Time physical PASS. Overall physical UAT **not closed**. |
| PRINT | Future relevance; do not implement. |
| SCREENSHOTS NEEDED LATER | Today weekday/date. Time Scheduled today + Choose different work. Do **not** capture now. |
| EVERYDAY TASKS | What if Ben sends me to another job? What if the work I actually did was not on my Schedule? Answer: Choose the work you actually performed when entering Time. |
| HELP / VOICE | Future topics: What if Ben sends me to another job? What if the work I actually did was not on my Schedule? |
| Do not | Final Manual prose. Unstable screenshots. PERF/LEARN planned-versus-actual. Auto-updating Schedule from Time. |

### MANUAL IMPACT — SCH-D (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Today / Week / Month + schedule-assisted Time |
| Status | **SUPERSEDED AS CURRENT** by SCH-D UX #2 above for Time/Today presentation. SCH-D product remains **IMPLEMENTED / TESTED.** Scheduled Time later recorded **PHYSICAL PASS**. |
| CONTRACTOR CAPABILITY | See **My work** for today, this week, and the next few weeks. Open **Company today** to see what the company has scheduled today. On Time, use **Scheduled today** as a suggestion, then still choose the work and hours. |
| WHEN USED | When a worker opens Field to see what they are supposed to do, or when an owner/manager wants a read-only look at company work today. |
| FINAL MANUAL WORKFLOW TO TEACH | Open Field **Today**. Read **My work**. Use **This week** / **This month**. Optionally open **Company today**. Tap **Enter time**. On Time, use **Scheduled today** or choose other work. Warnings do not stop Time. Dates are planned on desktop, not on the phone. |
| CONTRACTOR-FACING TERMS | Today. This week. This month. Company today. My work. Assigned to me. Crew work. Not assigned. Enter time. Scheduled today. You can use this scheduled work, or choose other work. Choose the work you actually did. This is information only. You can keep working. What the company has scheduled today. This does not change dates. Do **not** use: RBAC, overlay, projection, DAG, WorkScheduleItem. |
| WARNINGS / VALIDATION | **Warning:** informational only; does not block Time. **Validation:** Field does not edit Schedule. Time still requires confirmed work and hours. |
| DESKTOP | Plans dates and assignments. Company Schedule / Hub unchanged. |
| IPHONE | YES — Field views. Physical iPhone UAT **NOT CLAIMED**. |
| PRINT | Future relevance; do not implement. |
| SCREENSHOTS NEEDED LATER | Field Today / Week / Month. Company today. Time Scheduled today. Do **not** capture now. Physical iPhone screenshots wait for later authorized UAT. |
| EVERYDAY TASKS | What am I supposed to do today? What does the company have scheduled today? How do I enter time against scheduled work? |
| HELP / VOICE | Future topics only. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Field Schedule editing. Company-wide Unassigned on ordinary worker Today / Week / Month. Automatic Time. Physical iPhone PASS. |

### MANUAL IMPACT — SCH-C (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-C Lightweight Element dependencies + sequence warnings |
| Status | **SUPERSEDED AS CURRENT** by SCH-D capture below. SCH-C product remains **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.** Additive **`f9b0c1d2e3f4`**. Live current = repository head. Live UAT on Project **47** confirmed this contractor copy. No workflow/copy change from UAT. |
| CONTRACTOR CAPABILITY | Set which major work should come before other work. Under **Work order**, say which work **comes after** other work. This does not move dates by itself. |
| WHEN USED | When planning the order of major Project work. |
| FINAL MANUAL WORKFLOW TO TEACH | Add a **Comes after** / **Must follow** relationship. Remove it. Understand a **Schedule warning** when work is scheduled before prior work is finished. Understand a **Schedule warning** when work is scheduled but the prior work does not have dates yet. Optionally **Change dates** or **Review this project**. **Leave dates as they are**, or ignore the warning and continue. |
| CONTRACTOR-FACING TERMS | Work order. Comes after. Must follow. Add work order. Prior work. Schedule warning. Scheduled before prior work is finished. Scheduled, but the prior work does not have dates yet. Leave dates as they are. Change dates. Review this project. This is information only. You can continue without changing anything. Do **not** use: DAG, edge, node, graph, ProjectWorkDependency, dependency_id. |
| WARNINGS / VALIDATION | **Warning:** informational only; does not block work. **Validation:** an invalid relationship or a loop cannot be saved. |
| DESKTOP | YES — Company Schedule and Project Hub Schedule. |
| IPHONE | SCH-D / future. |
| PRINT | Future relevance; do not implement. |
| SCREENSHOTS NEEDED LATER | Work-order / sequence controls. Sequence warning. Project Schedule / Hub context. Do **not** capture now. |
| EVERYDAY TASKS | How do I tell CalibraytAI what work comes first? What does this Schedule warning mean? How do I move work after reviewing a warning? |
| HELP / VOICE | Future topics only. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Automatic date movement. |

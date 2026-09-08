# Feature Gate FG-026: PLAN → PRICE Phase D — Takeoff-to-Estimate Mapping V1

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-026` |
| Feature Name | PLAN → PRICE Phase D — Takeoff-to-Estimate Mapping V1 |
| Target Milestone | **None.** FG-026 is the governing identifier. Do not assign a new M0xx number. Roadmap Phase D (reviewed quantities → estimate assemblies) is the sequence home. This is **not** Item 14 LEARN and **not** Item 15 / [FG-024](FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md). |
| Module | **PLAN proposes. PRICE / Estimating commits.** Plan Intelligence remains owner of take-off evidence. Estimating remains owner of `EstimateVersion`, `EstimateLineItem`, insertion, and frozen estimate-side provenance. No new module. |
| Date | 2026-09-08 |
| Status | **FUTURE / RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** This recording is **not** Feature Gate approval for implementation. |
| Architecture | [ai-takeoff-quantity-extraction-foundation.md](../architecture/ai-takeoff-quantity-extraction-foundation.md) · [plan-intelligence-and-automated-takeoff.md](../architecture/plan-intelligence-and-automated-takeoff.md) · [fg-026-takeoff-to-estimate-mapping-preflight.md](../architecture/fg-026-takeoff-to-estimate-mapping-preflight.md) **PREFLIGHT COMPLETE** · [ADR-005](../adr/ADR-005-ai-takeoff-traceability.md) **Accepted** · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) **Accepted** · [ADR-011](../adr/ADR-011-ai-confidence-threshold-policy.md) **Accepted** · [ADR-031](../adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) **Accepted** · [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) **Accepted** · [FG-010](FG-010-ai-takeoff-quantity-extraction-foundation.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-012](FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-014](FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT** · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |
| Related ADRs | **None new in this recording / preflight pass.** Implementation stays within accepted ADR-005 / 006 / 007 / 011 / 031 / 035. Do **not** accept ADR-008 or ADR-010 from this gate. |
| Prerequisites | [FG-010](FG-010-ai-takeoff-quantity-extraction-foundation.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue identity **exists** ([FG-014](FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md)). [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED**. [FG-025](FG-025-contractor-facing-ux-language-and-terminology-standardization.md) remaining surfaces **NOT AUTHORIZED** and are **not** this gate. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **RECORDED.** **ARCHITECTURE PREFLIGHT COMPLETE.** **NOT APPROVED FOR IMPLEMENTATION.** |
| Product code | **None.** |
| Schema / Alembic | **None in this pass.** A later implementation prompt **would require** an additive migration for Estimating-owned insertion/citation records. Do **not** create that migration from this recording. |
| MaterialRequirement | **OUT OF V1.** ADR-035 remains architecture direction only. |
| Labour snapshot from take-off | **OUT OF V1.** |
| Pricing Engine apply | **OUT OF V1.** Existing FG-009 remains a separate human action after lines exist. |

```text
FG-026:
FUTURE
RECORDED
ARCHITECTURE PREFLIGHT COMPLETE
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
PLAN PROPOSES / ESTIMATING COMMITS
PACKAGE APPROVAL DOES NOT INSERT
NO NEW ADR IN THIS PASS
LATER IMPLEMENTATION WOULD REQUIRE ADDITIVE MIGRATION
ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION
```

Joel/ChatGPT recorded this gate on **2026-09-08** as durable product/governance authority plus architecture preflight. Recording is **not** implementation approval. Do **not** implement from this document.

---

## Purpose

Define the smallest architecture-compliant bridge from an **APPROVED** `TakeoffPackage` to **explicit human-authorized** insertion of governed commercial lines into an **existing editable Draft** `EstimateVersion` on the **same Project**.

This gate must **not** duplicate Plan Intelligence, Estimating, Material Catalogue, Labour Engine, Pricing Engine, or historical-ingestion ownership.

---

## Ownership (pinned)

| Concern | Owner |
|---------|--------|
| `TakeoffExtractionRun`, `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem`, approved quantity/citation evidence | **Plan Intelligence** |
| `Estimate`, `EstimateVersion`, `EstimateSection`, `EstimateLineItem` | **Estimating** |
| Commercial insertion commit | **Estimating** |
| Insertion audit + frozen estimate-side provenance / citation snapshots | **Estimating** |
| Canonical material identity | **Material Catalogue** (read-only consume; no MaterialRequirement in V1) |
| Labour tasks / production rates / labour snapshots | **Labour Engine** (unchanged; out of V1) |
| Pricing policy / snapshots | **Pricing Engine** (unchanged; out of V1) |

**PLAN proposes. Estimating commits.** Package approval does **not** insert estimate lines ([ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md)). Confidence never authorizes insert ([ADR-011](../adr/ADR-011-ai-confidence-threshold-policy.md)).

---

## Four quantity layers (must stay distinct)

| Layer | Owner | V1 role |
|-------|--------|---------|
| AI candidate quantity | Plan Intelligence | Evidence only |
| Human-reviewed candidate quantity | Plan Intelligence | Evidence only |
| Approved package quantity | Plan Intelligence | **Suggested** estimate quantity; never silent line quantity |
| Estimate-line quantity | Estimating | Set only after explicit user confirmation |

No silent unit conversion. No generic `count` → `ea` rule is authorized. The user must explicitly confirm estimate quantity **and** target commercial unit.

---

## V1 mapping contract

1. Source must be an **APPROVED** `TakeoffPackage` (not draft, not superseded).
2. Mapping unit is **one commercial line per selected package element grouping**. V1 grouping = all frozen items on that package (`TakeoffPackage.element_type` is already single-valued). A mapped line **may cite multiple** `TakeoffPackageItem` rows.
3. Target must be an **existing** organization-owned **Assembly** or **CostItem**, selected explicitly by a human. Preferred normal target for `INTERIOR_DOOR_OPENING` is Assembly **where a suitable governed Assembly already exists**. FG-026 must **not** create an Assembly or CostItem to satisfy mapping. If no suitable target exists, mapping **cannot proceed**.
4. Destination must be an **existing editable Draft** `EstimateVersion` on the **same Project**. Do **not** auto-create `Estimate`, `EstimateVersion`, `Project`, or `Proposal`. If none exists, UI directs the user to the existing estimating workflow.
5. User must select an **existing** `EstimateSection` on that Draft. If none exists, fail closed and direct to the existing estimate builder.
6. Insert uses existing Estimating builder ownership (`add_assembly_line` / `add_cost_item_line` calculation and catalog-copy behaviour) inside **one** transaction with provenance writes. Current builder functions commit internally; a later implementation must **not** call them as-is if that would commit the line before provenance persists.
7. Estimate-side records freeze insertion provenance. The estimate must **not** float with later PLAN reruns, drawing revisions, or package supersession.
8. Source `TakeoffPackage` remains unchanged.

---

## Intended V1 user flow

1. User opens an APPROVED TakeoffPackage (`/projects/<id>/plans/takeoff/packages/<package_id>`).
2. User chooses **Map to estimate** (or governed equivalent).
3. System displays the package element group and frozen source evidence.
4. User selects an EXISTING Assembly or CostItem.
5. System suggests the approved package quantity (and package unit as suggestion only).
6. User explicitly confirms estimate quantity and target unit.
7. User selects an EXISTING editable Draft EstimateVersion on the SAME Project, and an EXISTING section on that version.
8. System previews the proposed commercial line and source citations.
9. User explicitly chooses **Insert into estimate**.
10. Estimating creates the line.
11. Estimating records frozen insertion/citation provenance.
12. Source TakeoffPackage remains unchanged.
13. Destination EstimateVersion remains governed by existing editability rules.
14. Pricing remains a separate later human FG-009 action.

No silent insertion.

---

## Fail-closed rules

Mapping/insert **must not proceed** when:

- package is not `approved`
- package project ≠ destination estimate project
- organization mismatch
- destination `EstimateVersion` is not status `Draft`, or is locked, or is in `AUTO_LOCK_VERSION_STATUSES`
- no existing section is selected
- target Assembly/CostItem does not exist, is inactive, or is not in the current org
- user has not explicitly selected the target
- user has not explicitly confirmed quantity and unit
- provenance cannot be persisted
- source package/item identity cannot be reconstructed
- a V1 duplicate insertion already exists for the same package + element grouping + destination version
- required schema/migration is unresolved (this recording: unresolved because not implemented)

**No partial silent commercial insert.** If insertion fails: source package unchanged; destination must not retain a partial line or partial audit row. Single DB transaction; rollback on any failure.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Approved take-off packages exist (FG-010) and editable estimate lines exist (Estimating), but there is no governed human-approved bridge. Without it, estimators cannot move reviewed PLAN quantities into PRICE without informal re-entry, and silent insert would violate ADR-006. |
| 2 | Who is the user? | Office estimator/reviewer on a Project. Not Field Web. Not MONITOR. Not customers. |
| 3 | Which module owns it? | **Estimating** owns insertion, lines, and estimate-side provenance. **Plan Intelligence** owns take-off evidence and proposes the map. No new module. |
| 4 | What data does it own? | **Future, not created:** Estimating-owned `TakeoffEstimateInsertion` and `TakeoffEstimateInsertionCitation` (names in preflight). This recording owns no schema. |
| 5 | What data does it reference? | `TakeoffPackage` / `TakeoffPackageItem` (Plan Intelligence); `Estimate` / `EstimateVersion` / `EstimateSection` / `EstimateLineItem`; `Assembly` / `CostItem`; `Organization` / `Project` / `User` actor snapshot. Not CanonicalMaterial as insert target. Not `PlanMeasurement`. Not Labour snapshots. |
| 6 | What may it change? | **This recording:** documentation and discoverability pins. **Later implementation:** only what a later approved Cursor prompt allows — additive Estimating provenance tables, mapping UI on the existing take-off package page, Estimating insert service. |
| 7 | What must it not change? | Take-off models/immutability; Estimate builder commercial math; FG-009 policies/snapshots; FG-008 labour standards or labour-in-basis default; Material Catalogue identity; historical workbooks; Accepted proposals; Field Events/Originals; MONITOR arithmetic; FG-025 remaining surfaces; FG-024; LEARN. |
| 8 | What are the acceptance criteria? | **This recording:** FG-026 exists; preflight exists; NOT IMPLEMENTATION-AUTHORIZED; ownership and fail-closed rules pinned. **Later implementation:** explicit human insert only; four quantity layers preserved; provenance reconstructable; package unchanged; locked versions untouched; dedicated tests pass. |
| 9 | What tests are required? | **None** for this docs-only recording. Later implementation requires dedicated tests (see preflight). |
| 10 | What documentation must be updated? | This gate; preflight; feature-gates README; docs README; current-state; session-handoff; project-state-report; milestones; chat-workflow-log; roadmap Phase D pin; Plan Intelligence and Estimating module docs; architecture.md; CAR-001 subsequent status; platform-governance pin. |
| 11 | Does it require an ADR? | **No in this pass.** Insertion-audit ownership stays with Estimating (ADR-006 / ADR-007). Frozen citation snapshot on insert is ADR-005. Many items per line is cardinality, not an ownership transfer. If a later prompt moved insertion audit into Plan Intelligence, **STOP** and require a new ADR. |
| 12 | Does it require a database migration? | **No in this recording.** **Yes** for a later implementation prompt: additive Estimating provenance tables only. Do **not** generate Alembic from this pass. |

---

## Explicitly out of scope

Real external AI; OCR; CAD; multi-trade extraction; supplier integration; SKU mapping; MaterialRequirement; Assembly explosion; pack rounding; mapping-UI waste-factor editing; automatic labour snapshot; automatic pricing apply; historical workbook auto-mapping; LEARN; FG-024; Observation Delete; remaining FG-025 terminology work; QuickBooks; contract generation; Native Signing; new permit work; new Field work; auto-create Estimate / EstimateVersion / Project / Proposal; AI-created Assembly or CostItem; `PlanMeasurement` mapping; putting `takeoff_package_id` alone on `EstimateLineItem` as the provenance SoR.

---

## UAT design (later; do not create data now)

Live fact (not a defect): approved `TakeoffPackage` **id 1** is on **project 3**; project 3 currently has **no** estimate.

Later bounded UAT, after implementation authorization:

**A.** Create a labeled synthetic Draft estimate **on project 3** using the existing estimating workflow (including at least one section).

**B.** Create an explicitly human-authored labeled UAT Assembly (preferred) or CostItem as the commercial target. Do **not** use AI to create the target. Do **not** treat `FG014-UAT-ASM` (framing lumber UAT) as an interior-door Assembly.

Do **not** write live DB data in this governance pass.

---

## Implementation authorization

**ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

This gate does **not** authorize product code, schema, migration, live DB writes, or UAT data creation. A later bounded Joel/ChatGPT Cursor prompt is required before implementation.

---

## Related

- [fg-026-takeoff-to-estimate-mapping-preflight.md](../architecture/fg-026-takeoff-to-estimate-mapping-preflight.md)
- [FG-010](FG-010-ai-takeoff-quantity-extraction-foundation.md)
- [modules/plan-intelligence.md](../modules/plan-intelligence.md)
- [modules/estimating.md](../modules/estimating.md)

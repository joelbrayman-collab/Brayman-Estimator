# Platform Vision — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **Joel-approved CalibAi direction** (2026-08-28); repository product name remains The Estimator |
| Updated | 2026-08-28 |
| Approval | CalibAi vision and lifecycle: Joel Brayman via CAR-001. Repository/product rename is a **separate** future approval. |
| Record | [CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md) |

## CalibAi

CalibAi is a **construction intelligence platform** connecting **PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN** through **one authoritative project record**.

**Positioning:** Construction intelligence. Calibrated.

**Learning principle:** Every project makes the next project smarter.

CalibAi provides complementary **office** and **field** experiences over the same authoritative project record, the same business rules, and the same service layer. Field/iPhone use is a first-class product requirement ([ADR-022](adr/ADR-022-field-client-and-shared-api.md)).

The existing `Project` entity remains the lifecycle hub ([ADR-019](adr/ADR-019-calibai-lifecycle-and-project-hub.md)). CalibAi extends this repository’s implemented commercial core; it does not rename the repository in CAR-001.

## What The Estimator is (current product in this repository)

The Estimator is a **construction estimating and commercial operations platform** for Brayman (working title: Brayman Estimator). It is the **current office commercial core** of CalibAi: client relationship and project leads through structured estimating, client proposals, and project controls—with a path toward **plan-intelligent quantity take-off**, **supplier-priced procurement**, job costing, field capture, monitoring, and historical intelligence.

It is intended to be **attorney-quality in discipline** (documented, auditable, recoverable) while serving **construction business users**: estimators, project managers, principals, office staff, and (CalibAi) field crews using the same project record.

## Problems it is intended to solve

- Fragmented spreadsheets and tribal knowledge for cost libraries and assemblies
- Estimates that cannot be versioned or locked once issued
- Proposals that drift when the underlying estimate changes
- Weak handoff from winning work into project controls (change orders, later purchasing/job cost)
- Loss of institutional memory about *why* a number was bid
- Manual, non-traceable take-off from PDF plans
- Disconnect between supplier catalogue pricing and historical estimate/proposal numbers

## Intended users

- Estimators and estimating managers
- Project managers / project controls staff
- Company principals reviewing proposals and change orders
- Office / CRM operators maintaining clients and projects
- Field crews and supervisors (CalibAi field experience — first-class; not implemented)
- (Future) Take-off reviewers validating AI/manual quantities
- (Future) Purchasing staff preparing supplier POs
- (Future) Supplier-channel launch/reference partners (not exclusive; [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md))

## Long-term platform direction

CAR-001 records the approved CalibAi sequencing direction on [platform-roadmap.md](platform-roadmap.md). The lists below remain the existing commercial/operations path. They are **not** a claim that later stages exist in code.

### Foundational commercial path (partially current)

1. CRM
2. Estimating
3. Proposal Engine
4. Proposal Acceptance
5. Project Creation
6. Project Management / Controls

### Differentiating operations path (future architecture)

7. **Plan Intelligence** (PDF-first upload, classification, scale)
8. **Automated Quantity Take-Off** with **human review and source traceability**
9. Map reviewed quantities into estimate assemblies
10. **Supplier catalogue** and price-file management
11. **Live supplier inventory/pricing** integrations
12. **Procurement / PO preparation**
13. Scheduling, job costing, invoicing, historical intelligence

See [architecture.md](architecture.md) for **current** vs intended vs future, [platform-roadmap.md](platform-roadmap.md) for pillars and Phases A–G, and domain architecture under [architecture/](architecture/).

## Governance boundaries (without a further approved decision)

Without Joel approval and an ADR where required, the platform does not expand into a general ERP, a full accounting system (QuickBooks remains external unless integration is approved), or a CAD-first drafting tool (PDF-first take-off is the proposed path — ADR-009).

AI does not silently invent prices, scopes, quantities, or contracts. Historical estimates, proposals, take-offs, and financial records are versioned or superseded, not silently overwritten.

CalibAi office and field experiences are **complementary**. The product is an office-and-field construction intelligence platform, not a field-only app.

## Related documents

- [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- [architecture-principles.md](architecture-principles.md)
- [platform-roadmap.md](platform-roadmap.md)
- [architecture/plan-intelligence-and-automated-takeoff.md](architecture/plan-intelligence-and-automated-takeoff.md)
- [architecture/supplier-catalogue-inventory-pricing.md](architecture/supplier-catalogue-inventory-pricing.md)
- [architecture/supplier-channel-and-launch-partner.md](architecture/supplier-channel-and-launch-partner.md)
- [adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md)
- [modules/](modules/)

# Platform Vision — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Provisional product vision |
| Updated | 2026-07-25 |
| Approval | Requires ongoing Joel confirmation |

## What The Estimator is

The Estimator is a **construction estimating and commercial operations platform** for Brayman (working title: Brayman Estimator). It helps contractors move from client relationship and project leads through structured estimating, client proposals, and into project controls—with a long-term path toward **plan-intelligent quantity take-off**, **supplier-priced procurement**, job costing, and historical estimating intelligence.

It is intended to be **attorney-quality in discipline** (documented, auditable, recoverable) while serving **construction business users**: estimators, project managers, principals, and office staff.

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
- (Future) Take-off reviewers validating AI/manual quantities
- (Future) Purchasing staff preparing supplier POs

## Long-term platform direction (provisional)

This sequence is **provisional** and must be confirmed against Joel’s priorities. It is **not** a claim that later stages exist in code.

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

## What it is not (without an approved architectural decision)

Without Joel approval and an ADR where required, The Estimator is **not**:

- A general ERP replacement
- A full accounting system (QuickBooks remains external unless integration is approved)
- A field-only mobile product
- An AI system that silently invents prices, scopes, quantities, or contracts
- A platform that silently overwrites historical estimates, proposals, take-offs, or financial records
- A CAD-first drafting tool (PDF-first take-off is the proposed path — ADR-009)

## Related documents

- [architecture-principles.md](architecture-principles.md)
- [platform-roadmap.md](platform-roadmap.md)
- [architecture/plan-intelligence-and-automated-takeoff.md](architecture/plan-intelligence-and-automated-takeoff.md)
- [architecture/supplier-catalogue-inventory-pricing.md](architecture/supplier-catalogue-inventory-pricing.md)
- [modules/](modules/)

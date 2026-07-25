# Platform Vision — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Provisional product vision |
| Updated | 2026-07-25 |
| Approval | Requires ongoing Joel confirmation |

## What The Estimator is

The Estimator is a **construction estimating and commercial operations platform** for Brayman (working title: Brayman Estimator). It helps contractors move from client relationship and project leads through structured estimating, client proposals, and into project controls—with a long-term path toward job costing and historical estimating intelligence.

It is intended to be **attorney-quality in discipline** (documented, auditable, recoverable) while serving **construction business users**: estimators, project managers, principals, and office staff.

## Problems it is intended to solve

- Fragmented spreadsheets and tribal knowledge for cost libraries and assemblies
- Estimates that cannot be versioned or locked once issued
- Proposals that drift when the underlying estimate changes
- Weak handoff from winning work into project controls (change orders, later purchasing/job cost)
- Loss of institutional memory about *why* a number was bid

## Intended users

- Estimators and estimating managers
- Project managers / project controls staff
- Company principals reviewing proposals and change orders
- Office / CRM operators maintaining clients and projects

## Long-term platform direction (provisional sequence)

This sequence is **provisional** and must be confirmed against Joel’s priorities and the live repository. It is **not** a commitment that all stages are implemented.

1. CRM  
2. Estimating  
3. Proposal Engine  
4. Proposal Acceptance  
5. Project Creation  
6. Project Management  
7. Scheduling  
8. Purchasing  
9. Job Costing  
10. Invoicing  
11. Historical Estimating Intelligence  

See [architecture.md](architecture.md) for what exists **today** versus this intended path, and [platform-roadmap.md](platform-roadmap.md) for status labels.

## What it is not (without an approved architectural decision)

Without Joel approval and an ADR where required, The Estimator is **not**:

- A general ERP replacement
- A full accounting system (QuickBooks remains external unless integration is approved)
- A field-only mobile product
- An AI system that silently invents prices, scopes, or contracts
- A platform that silently overwrites historical estimates, proposals, or financial records

## Related documents

- [architecture-principles.md](architecture-principles.md)
- [platform-roadmap.md](platform-roadmap.md)
- [modules/](modules/)

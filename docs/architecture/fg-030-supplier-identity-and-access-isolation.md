# FG-030 — Supplier Identity, Authentication, and Access Isolation

| Attribute | Value |
|-----------|--------|
| Status | **ARCHITECTURE RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** |
| Date | 2026-09-09 |
| Gate | [FG-030](../feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) |
| ADR | [ADR-047](../adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only) |
| Does not authorize | Product code · schema · migration · live DB · website publish · live BMR · ADR-008 · FG-030 implementation · FG-028 Slice 3 install |

This is the architecture pin for supplier named-user access. It is **not** an implementation preflight that authorizes Cursor to write application code.

---

## Current (evidenced)

| Surface | Evidence |
|---------|----------|
| Contractor named-user login | `User`, `UserMembership`, Flask-Login; [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| Tenant | `Organization` only ([ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md)) |
| Supplier records | `Supplier`, `SupplierLocation`, `ContractorSupplierAccount`, products, evidence, maps, `SupplierPackage` ([FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**; migration **`b6c7d8e9f0a1` applied live**) |
| Supplier-facing artifact | Issued package HTML + PDF from **contractor office** |
| Supplier portal login | **Does not exist** |
| Marketing website | **External / not this repository** |

FG-029 Feature Gate answer 2 remains true for that gate: Darcy / BMR Winchester receive HTML/PDF. Not a supplier portal login **in FG-029**.

---

## Intended V1 (not implemented)

```text
WEBSITE (EXTERNAL) OPTIONAL LINK
        ↓
APPLICATION UNIVERSAL LOGIN  (email + password)
        ↓
PRINCIPAL CLASS RESOLUTION  (exactly one)
        ↓
    CONTRACTOR → existing office / Field surfaces
    SUPPLIER   → supplier workspace only
```

### Principal classes

| Class | Binding | Lands on |
|-------|---------|----------|
| `CONTRACTOR` | Active `UserMembership` → `Organization` | Existing office (and Field where already authorized) |
| `SUPPLIER` | Active SupplierUserMembership → `Supplier` (+ optional `SupplierLocation`) | Supplier workspace |

V1: a User must not have both bindings active. Dual membership **fails closed**. Dual-hat is later.

### Membership

- Contractor membership: unchanged FG-018 `UserMembership`.
- Supplier membership: new Supplier Catalogue record User ↔ Supplier, optional location scope.
- Supplier users **must not** receive contractor `UserMembership`.
- `Supplier` is **not** an `Organization`.

### Sharing

Contractor grants visibility to an **issued Supplier Package** for that package's supplier.

Not granted by share:

- Project Hub
- estimates, costing, pricing, labour, MONITOR, LEARN
- other packages, other projects, other suppliers
- unrestricted relationship **A** “see everything”

Relationship **A** (`ContractorSupplierAccount`) is procurement account identity, not an ACL.

### Isolation matrix

| Viewer | May see |
|--------|---------|
| Supplier A named-user | Own membership supplier; shared issued packages for A; A's SKU/price/availability only if a later slice authorizes self-catalogue — **never** B's catalogue or packages |
| Supplier B named-user | Symmetric; never A's data |
| Contractor office (ORG-001) | Own projects; FG-029 office mapping; relationship **A** evidence for **their** accounts; never another contractor org |
| Supplier session | **Never** `EstimateLineItem` costs, FG-027 snapshots, FG-009 snapshots, GM, customer selling price |

Fail closed. Missing share = no access. Cross-supplier list endpoints must not exist for supplier sessions.

### Workspace

Supplier navigation is a **separate shell**. Do not hide contractor nav items and call that isolation.

V1 supplier workspace minimum (when implemented): authenticate; list/view **shared issued** packages; download/view the same frozen HTML/PDF facts FG-029 already freezes. Optional later: own-catalogue read. Not in this recording's implementation (there is none).

### Login gateway

One application login URL. Website may link to it. Website implementation/publish is **out of this pin**.

### Unchanged

PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN. Inform-only supplier price. ADR-008 Proposed. No live order. No marketplace.

---

## Implementation notes (for a later prompt — not authorization)

When Joel/ChatGPT authorize implementation, expected additive work includes:

- `SupplierUserMembership` (name may vary)
- `SupplierPackageShare` (name may vary)
- principal-class resolution on session
- supplier blueprint/workspace
- fail-closed query scoping
- bootstrap of a labeled DEMO supplier user **only** if that later prompt authorizes it
- dedicated isolation tests

Do **not** create those objects from this document.

---

## V1 register

This capability is **Joel-directed V1 identity/isolation architecture**. It is **not** a 12th major package. It does **not** change V1-03 completion factor. It does **not** mark BMR DEMO READY. FG-029 HTML/PDF remains the current supplier-facing path until FG-030 is separately implemented.

---

## Stop conditions

Do not implement from this pin.

Do not live-migrate FG-029 from this pin.

Do not install FG-028 Slice 3 from this pin.

Do not publish the marketing website from this pin.

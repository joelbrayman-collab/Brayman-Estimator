# ADR-047 — Supplier Identity, Authentication, and Access Isolation

| Field | Value |
|-------|--------|
| Title | ADR-047: Supplier Named-User Login, Membership, Sharing, and Cross-Supplier Isolation |
| Status | **Accepted** (architecture / governance only). [FG-030](../feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) is **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. |
| Date | 2026-09-09 |
| Related | [FG-030](../feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) · [fg-030-supplier-identity-and-access-isolation.md](../architecture/fg-030-supplier-identity-and-access-isolation.md) · [ADR-041](ADR-041-user-membership-and-office-authentication.md) **Accepted** · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** · [ADR-046](ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** · [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [ADR-008](ADR-008-supplier-price-snapshotting.md) **Proposed** |

This ADR authorizes the **identity and isolation boundary** for supplier-facing access. It does **not** authorize product code, schema, migration, live database writes, website publish, live BMR integration, or acceptance of [ADR-008](ADR-008-supplier-price-snapshotting.md).

---

## Context

CalibraytAI V1 now has a contractor-office supplier workflow: thin `MaterialRequirement` → human mapping → inform-only evidence → frozen Supplier Package HTML/PDF ([FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**, [ADR-046](ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md)).

FG-029 users are the **contractor office estimator**. Darcy / BMR Winchester **receive** an HTML/PDF package. That gate explicitly does **not** include a supplier portal login.

Office authentication today ([ADR-041](ADR-041-user-membership-and-office-authentication.md), [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md)) binds a durable `User` to a contractor `Organization` via `UserMembership`. `Supplier` is **not** a CalibraytAI tenant ([ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md), [ADR-046](ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) Decision S).

Joel directed (2026-09-09) that CalibraytAI V1 must **define and govern**:

- supplier named-user login
- Supplier / SupplierLocation membership
- contractor-to-supplier project/package sharing
- supplier-specific authorization
- strict cross-supplier data isolation
- protection of contractor-private costing/margins
- supplier pricing/SKU/availability privacy
- supplier workspace/navigation
- universal website → application login gateway
- contractor vs supplier post-login routing

Hard product rules:

- No supplier may see another supplier's commercial data or work product.
- No supplier receives unrestricted contractor-office access.

Without this ADR, a later supplier login could be implemented as ORG-001 membership, as a second Actor entity, as office RBAC, or as a shared Project Hub — all of which would leak contractor margins or cross-supplier catalogues.

---

## Decision

**Accepted as architecture.** Do **not** treat acceptance as product implementation.

### 1. One durable User; two principal classes

V1 keeps **one** durable `User` ([ADR-041](ADR-041-user-membership-and-office-authentication.md) Decision 1). Do **not** create a separate Actor / SupplierUser entity.

Every authenticated session has exactly one **principal class**:

| Principal class | Meaning |
|-----------------|---------|
| `CONTRACTOR` | Active `UserMembership` to a contractor `Organization` |
| `SUPPLIER` | Active supplier membership to a `Supplier` (optional `SupplierLocation` scope) |

Login identifier remains **email + password**. Display name remains the human-readable snapshot.

### 2. Organization remains the only contractor tenant

`Organization` remains the only tenant / legal-commercial root ([ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md)).

`Supplier` / `SupplierLocation` remain **dealer identity**, not tenants. Do **not** create dummy Organizations for dealers. Do **not** grant supplier users `UserMembership` to ORG-001 or any contractor organization.

### 3. Supplier membership is not contractor membership

Contractor authorization continues to use `UserMembership` (User ↔ Organization).

Supplier authorization uses a **separate** membership binding (User ↔ Supplier, with optional SupplierLocation scope). Exact table name is implementation reconnaissance. Architecture name: **SupplierUserMembership**.

Supplier Catalogue owns supplier membership records. The identity/`User` table remains the FG-018 identity layer.

### 4. V1: one principal class per User

A User must not hold **both** an active contractor `UserMembership` and an active supplier membership in V1.

If both exist, authentication/authorization **fails closed**. Dual-hat (same person as contractor and supplier) is a **later governed decision**. Do not invent a switcher.

### 5. This is not office RBAC

Keep [ADR-041](ADR-041-user-membership-and-office-authentication.md) Decision 4: V1 contractor office does **not** gain estimator/admin/reviewer roles from this ADR.

Contractor vs supplier is a **principal class and workspace**, analogous to office vs Field as surfaces — not a permissions matrix.

Supplier-specific authorization in V1 is:

| Concept | V1 rule |
|---------|---------|
| Authentication | Active logged-in User |
| Supplier authorization | Active SupplierUserMembership for that Supplier (and location if scoped) |
| Share authorization | Explicit contractor-granted share of a specific Supplier Package (see Decision 7) |
| Audit provenance | Logged-in User identity + human-readable snapshot |

Do **not** implement enterprise supplier RBAC, SLA roles, or national IdP from this ADR ([ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md) Decision 6: do not overbuild Winchester).

### 6. Cross-supplier isolation (fail closed)

No supplier may read, list, or infer another supplier's:

- products / SKUs
- living or frozen price evidence
- availability evidence
- mappings
- Supplier Packages or package lines
- supplier memberships
- contractor–supplier accounts that are not theirs
- work product produced for another supplier

Queries and routes **fail closed** on the session's `supplier_id` (and location scope when present). Absence of a share is **not** access.

### 7. Contractor-to-supplier sharing is explicit and bounded

The V1 shareable unit is an **issued Supplier Package** (FG-029 frozen artifact), not the contractor Project Hub and not the estimate.

A contractor organization may grant a supplier named-user (via that user's Supplier membership) visibility to **that package's supplier-visible fields only**.

Sharing does **not**:

- grant office HTML routes
- grant Field Web
- grant estimate / costing / pricing / labour / MONITOR / LEARN access
- grant other projects' packages
- grant other suppliers' packages
- convert relationship **A** (contractor–supplier account) into automatic all-project visibility

Relationship **A** remains procurement account identity. **Share** is a separate explicit grant. Relationship **B** (channel partnership) remains out of this ADR.

Exact share-record shape is implementation reconnaissance. Architecture name: **SupplierPackageShare** (or equivalent). Contractor creates/revokes shares. Issued package freeze ([ADR-046](ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) Decision I) is unchanged: living evidence must not float an issued package.

### 8. Contractor-private commercial data is never supplier-visible

Supplier workspace and supplier-facing APIs **must not** expose:

- `EstimateLineItem` working/library/override cost
- `EstimateCostingSnapshot` / lines
- `EstimatePricingSnapshot` / selling price / gross margin
- labour rates, production standards, or calibration
- customer Proposal / contract commercial terms
- MONITOR actuals vs estimate
- Brand Profile internals beyond what an issued package already shows as contractor identity on the supplier-facing artifact

FG-027 and FG-009 remain contractor-private. Inform-only supplier price on a **shared issued package** may be visible to that package's supplier because it is **that supplier's** evidence, not contractor margin.

### 9. Supplier commercial privacy

Supplier A's SKU, price, and availability are **A's** commercial data.

- Supplier B must not see them.
- A contractor organization may see Supplier A's evidence **only** through relationship **A** + that contractor's own office workflow (existing FG-029 office path), never through a supplier session.
- Do not publish a cross-supplier catalogue to any supplier session.

### 10. Supplier workspace and navigation

Supplier sessions land in a **supplier workspace**, not the contractor office shell.

V1 supplier navigation is bounded to supplier-authorized surfaces (shared packages; later, only explicitly authorized supplier-self catalogue views for their own Supplier). Do **not** reuse contractor nav with items hidden. Hidden nav is not isolation.

Contractor sessions remain the existing office / Field surfaces. Post-login routing is by principal class.

### 11. Universal application login gateway

The **application** exposes one login entry (existing office `/login` is the current contractor gateway). After this gate is implemented, that entry becomes the **universal application login**: same email/password form; post-login routing by principal class.

The **marketing website** remains an **external** surface ([ADR-045](ADR-045-calibraytai-product-identity-and-former-name-preservation.md) Decision J). This ADR authorizes the website to **link** to the application login URL. It does **not** authorize website implementation, publish, CMS, or deploy from this repository.

### 12. Unchanged commercial and integration boundaries

- [ADR-008](ADR-008-supplier-price-snapshotting.md) remains **Proposed**.
- Supplier price remains **INFORM ONLY** for FG-029 ([ADR-046](ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) J–M).
- No live BMR API, EDI, or submitted purchase order.
- No marketplace.
- PLAN / FG-026 / FG-027 / Pricing ownership unchanged.
- FG-029 remains the contractor-office package workflow. This ADR does **not** reopen or close FG-029.

---

## Alternatives Considered

- **Grant supplier users `UserMembership` to ORG-001** — Rejected: unrestricted contractor-office access; leaks costing/margins.
- **Treat Supplier as a second Organization tenant** — Rejected: conflates dealer identity with contractor legal-commercial root ([ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md)).
- **Separate SupplierUser entity** — Rejected: violates one durable User ([ADR-041](ADR-041-user-membership-and-office-authentication.md)).
- **Office RBAC roles (estimator vs supplier)** — Rejected: mixes surfaces into a permissions matrix; ADR-041 forbids V1 office RBAC.
- **Automatic visibility of all project packages once relationship A exists** — Rejected: unrestricted project sharing.
- **Supplier sees the Project Hub PRICE workspace** — Rejected: Hub includes costing/pricing links.
- **Implement login in this recording** — Rejected: architecture only.
- **Make FG-029 incomplete until a portal exists** — Rejected: FG-029 supplier-facing artifact is HTML/PDF; portal is a separate gate.

## Consequences

**Positive:** Named supplier users can later enter a bounded workspace; cross-supplier and contractor-margin isolation are fail-closed before code exists; website can point at one login without becoming an app.

**Negative:** Dual-hat users are deferred. FG-029 live DEMO UAT still uses HTML/PDF delivery until FG-030 is implemented. Extra membership/share records will require a later additive migration.

## Module Ownership Impact

| Concern | Owner |
|---------|--------|
| Durable `User` / password / contractor `UserMembership` / session | Existing identity layer (FG-018) |
| Principal-class resolution and post-login routing | Identity layer + supplier workspace routes |
| `SupplierUserMembership` | **Supplier Catalogue** |
| `SupplierPackageShare` (or equivalent) | **Supplier Catalogue** |
| Issued Supplier Package freeze / HTML/PDF | **Supplier Catalogue** (FG-029; unchanged) |
| Contractor costing / pricing / estimates | **Estimating** / Pricing Engine (unchanged; not supplier-visible) |
| Marketing website | **External** (not this repository) |

## Data Ownership Impact

None in the live database from this ADR. Future owned records (not created here): SupplierUserMembership; SupplierPackageShare (or equivalent); optional principal-class / last-login surface snapshot as implementation reconnaissance justifies.

## Migration Impact

**Deferred.** Do not create an Alembic revision from this ADR. Live current remains whatever FG-029 live-migrate later applies; this recording does **not** migrate.

## Testing Impact

When later implemented: dedicated isolation tests (cross-supplier 404/403; contractor-private records absent from supplier session; share revocation; dual-membership fail closed; contractor session cannot use supplier routes and vice versa). Not run in this recording.

## Documentation Impact

[FG-030](../feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md); architecture pin; current-state; session-handoff; feature-gate and ADR indexes; V1 register **status text only** (do **not** rescore; do **not** add a 12th major package). Subsequent status on [ADR-041](ADR-041-user-membership-and-office-authentication.md) and [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md).

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman (V1 supplier identity / isolation direction) | 2026-09-09 |
| ChatGPT review | Define-and-govern brief into Cursor | 2026-09-09 |
| Cursor implementation note | Docs/ADR/FG/architecture only. No product code. No migration. ADR-008 **not** accepted. | 2026-09-09 |

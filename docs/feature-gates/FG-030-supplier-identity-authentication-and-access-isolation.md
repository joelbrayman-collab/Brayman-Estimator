# Feature Gate FG-030: Supplier Identity, Authentication, and Access Isolation

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-030` |
| Feature Name | Supplier Identity, Authentication, and Access Isolation |
| Target Milestone | **None.** FG-030 is the governing identifier. Do **not** assign a new M0xx number. Do **not** add a 12th V1 major package. Do **not** rescore [v1-completion-register.md](../v1-completion-register.md) from this recording. |
| Module | **Supplier Catalogue** owns supplier membership and package-share records. Existing FG-018 identity layer owns durable `User`, password, session, and contractor `UserMembership`. Estimating / Pricing / PLAN do **not** gain supplier-session readers. Marketing website remains **external**. |
| Date | 2026-09-09 |
| Status | **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** [ADR-047](../adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). |
| Architecture | [fg-030-supplier-identity-and-access-isolation.md](../architecture/fg-030-supplier-identity-and-access-isolation.md) · [ADR-047](../adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** · [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** · [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** · [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-029](FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| Related ADRs | **[ADR-047](../adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) Accepted** (architecture). Do **not** accept ADR-008 or ADR-010 from this gate. |
| Prerequisites | FG-018 **CLOSED / OPERATIONAL FOR UAT**. FG-029 contractor-office package workflow **CLOSED / OPERATIONAL FOR UAT**. This gate does **not** implement supplier login from FG-029 close. FG-028 Slice 3 installation remains **not** this gate. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **RECORDED.** **NOT APPROVED FOR IMPLEMENTATION.** |
| Named-user supplier login | **NOT AUTHORIZED** |
| Supplier / location membership | **NOT AUTHORIZED** |
| Package sharing | **NOT AUTHORIZED** |
| Supplier workspace / routing | **NOT AUTHORIZED** |
| Schema / Alembic | **None.** Do not create a migration from this recording. |
| Product code | **None.** |
| Website publish | **Not this gate.** External surface may later **link** to application login. |

```text
FG-030:
RECORDED
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
ADR-047 ACCEPTED (ARCHITECTURE ONLY)
NO SCHEMA
NO LIVE DB MUTATION
NO WEBSITE PUBLISH
FG-029 UNCHANGED (NOT A SUPPLIER PORTAL IN THAT GATE)
ADR-008 REMAINS PROPOSED
V1 REMAINS 45% / 2 OF 11
DO NOT ADD A 12TH MAJOR PACKAGE
DO NOT LIVE-MIGRATE FG-029 FROM THIS GATE
DO NOT INSTALL FG-028 SLICE 3 FROM THIS GATE
```

Joel directed this isolation architecture on **2026-09-09**. Recording is **not** implementation approval.

**Subsequent status (2026-09-09 FG-029 close — not authorized by this gate):** [FG-029](FG-029-bmr-supplier-workflow-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Live current = head **`b6c7d8e9f0a1`**. V1 is **55% / 3 of 11**. V1-03 **COMPLETE**. FG-030 remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Do **not** treat FG-029 contractor-office tenancy as FG-030 supplier-portal isolation.

---

## Purpose

Govern how a **named supplier user** authenticates into CalibraytAI and what they may see:

1. login as a durable User (not a second Actor type);
2. belong to a Supplier and optional SupplierLocation;
3. receive only contractor-granted package shares;
4. never see another supplier's commercial data or work product;
5. never receive unrestricted contractor-office access;
6. never see contractor-private costing, margins, or selling price;
7. keep their own SKU / price / availability private from other suppliers;
8. land in a supplier workspace, not the contractor office shell;
9. enter through one application login that a website may link to;
10. route after login by contractor vs supplier principal class.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | FG-029 can produce a frozen supplier package, but there is no governed supplier login, membership, sharing, or isolation model. Without it, a later portal would likely reuse ORG-001 membership or the Project Hub and leak margins or cross-supplier catalogues. |
| 2 | Who is the user? | Named supplier users (example: BMR Winchester / Darcy as **SUPPLIER** principal). Contractor office users remain **CONTRACTOR** principal (FG-018). Not Field Web. Not a marketplace shopper. |
| 3 | Which module owns it? | Supplier Catalogue owns supplier membership and package shares. FG-018 identity layer owns `User`, password, session, contractor `UserMembership`. Estimating does not expose costing to supplier sessions. |
| 4 | What data does it own? | Future: SupplierUserMembership; SupplierPackageShare (or equivalent). Not CanonicalMaterial. Not MaterialRequirement. Not estimate/costing/pricing snapshots. |
| 5 | What data does it reference? | `User`; `Supplier`; `SupplierLocation`; issued `SupplierPackage`; contractor `Organization` only as the sharing grantor identity — not as supplier tenant membership. |
| 6 | What may it change? | Later implementation may add membership/share tables, supplier workspace routes, and post-login routing. This recording changes **docs/governance only**. |
| 7 | What must it not change? | FG-029 product behaviour; live DB; FG-018 contractor membership semantics; Organization as sole tenant; PLAN/FG-026; FG-027 costing; FG-009 Pricing; ADR-008 status; V1 45% / 2 of 11; website source; FG-028 Slice 3 install; live BMR; PO submit. |
| 8 | What are the acceptance criteria? | Architecture recorded; isolation rules explicit; FG-029 remains HTML/PDF supplier artifact until a later implementation prompt; no code/migration from this gate. Later implementation (separate prompt): fail-closed isolation tests PASS. |
| 9 | What tests are required? | None in this recording. Later: cross-supplier isolation; contractor-private absence; share grant/revoke; dual-membership fail closed; principal routing. |
| 10 | What documentation must be updated? | ADR-047; this gate; architecture pin; current-state; session-handoff; indexes; V1 register status text only. |
| 11 | Does it require an ADR? | **Yes — ADR-047.** |
| 12 | Does it require a database migration? | **Not in this recording.** Later implementation will require an additive migration (not created here). |

---

## Hard isolation rules

```text
NO SUPPLIER SEES ANOTHER SUPPLIER'S COMMERCIAL DATA OR WORK PRODUCT.
NO SUPPLIER RECEIVES UNRESTRICTED CONTRACTOR-OFFICE ACCESS.
CONTRACTOR COSTING / MARGINS / SELLING PRICE ARE NEVER SUPPLIER-VISIBLE.
SUPPLIER SKU / PRICE / AVAILABILITY ARE PRIVATE TO THAT SUPPLIER
(except the contractor office that holds relationship A for its own workflow).
SHARE UNIT = ISSUED SUPPLIER PACKAGE, NOT THE PROJECT HUB.
```

---

## Relationship to FG-029

[FG-029](FG-029-bmr-supplier-workflow-v1.md) remains: contractor office creates/reviews requirements and mappings; Darcy / BMR Winchester **receive HTML/PDF**. **Not a supplier portal login in FG-029.**

FG-030 is the **later** named-user workspace. Do **not** mark FG-029 incomplete for lacking login. Do **not** implement FG-030 during FG-029 live-migrate / UAT.

---

## Non-goals

Live BMR API · EDI · submitted PO · ADR-008 acceptance · marketplace · relationship **B** / Darcy channel economics · office RBAC matrix · dual-hat users · treating Supplier as Organization · dummy tenant orgs for dealers · website CMS/publish · FG-028 Slice 3 install · FG-024 · remaining FG-025 · LEARN · Field Web for suppliers · invitations/SSO/IdP · enterprise supplier roles/SLAs

---

## Current vs intended vs future

| Layer | State |
|-------|--------|
| **Current** | FG-018 contractor named-user login. FG-029 office mapping + package HTML/PDF (not live-migrated). No supplier membership. No supplier workspace. |
| **Intended (this gate, not implemented)** | Supplier named-user + membership + package share + isolated workspace + universal app login routing. |
| **Future** | Dual-hat; SSO; supplier self-admin; live BMR; apply-supplier-cost. |

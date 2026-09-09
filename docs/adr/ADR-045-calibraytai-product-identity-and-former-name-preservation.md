# ADR-045 — CalibraytAI Product Identity and Former-Name Preservation

| Field | Value |
|-------|--------|
| Title | ADR-045: CalibraytAI Product Identity and Former-Name Preservation |
| Status | **Accepted** |
| Date | 2026-09-09 |
| Related | [product-identity.md](../governance/product-identity.md) · [FG-028](../feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) · [platform-vision.md](../platform-vision.md) · [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [ADR-040](ADR-040-organization-brand-profile.md) |

This ADR authorizes the **product-identity** decision. Visible-string and current-authority documentation changes are executed under [FG-028](../feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md). This ADR does **not** authorize a schema migration, live database rewrite, repository rename, logo installation, marketing-website change, V1-03, FG-024 implementation, or ADR-008.

---

## Context

Joel selected **CalibraytAI** as the permanent product name. The former product name is **CalibAi**.

Repository reconnaissance (2026-09-08) showed four coexisting identities:

1. Repository / working title: **The Estimator** / **Brayman-Estimator**
2. Office chrome: **Brayman Construction Platform**
3. Platform product (Field title/alt, Permit advisory/PDF title, current vision/governance): **CalibAi**
4. Tenant ORG-001: **Brayman Construction Inc.** / **Brayman Construction** / Organization Brand Profile

A blind global string replacement would rewrite historical truth, break Field IndexedDB compatibility, conflate product with tenant letterhead, and churn Alembic history.

CAR-001’s “product rename not authorized” referred to the **repository / The Estimator** working title, not to this later governed CalibAi → CalibraytAI identity transition.

---

## Decision

A. **CalibraytAI** is the current product identity. Canonical spelling: `CalibraytAI`.

B. **CalibAi** is the former product identity. Historical references remain valid historical truth. Do **not** globally rewrite history.

C. Authoritative alias home: [product-identity.md](../governance/product-identity.md).

D. Technical identifiers may retain `calibai` / `CALIBAI` / `CalibAi` where compatibility, provenance, or historical stability requires (Field IndexedDB keys, `calibai-mock`, `CALIBAI-AI`, `CALIBAI_BASELINE` token, tempfile prefixes, ADR-019 / CAR-001 filenames, historical Desktop paths).

E. Product identity does **not** replace ORG-001 tenant identity or Organization Brand Profile.

F. Product identity does **not** replace **Brayman Construction Platform** office chrome in this gate.

G. Frozen database evidence is **not** rewritten merely for branding (`permit_findings.advisory_language`, historical workbook paths, takeoff provider values, audit/provenance strings).

H. Historical Alembic files are immutable (no rename; no comment rewrite).

I. Repository name remains **Brayman-Estimator** unless separately governed.

J. Marketing website is a **separate external surface**.

K. Visual logo replacement requires a Joel-approved CalibraytAI lettering asset (same emblem, colours, layout; lettering only). Until supplied, Field may keep the Brayman Construction PNG while textual title/alt is CalibraytAI.

L. Permit **generator** current title/advisory uses CalibraytAI. Stored finding advisory snapshots stay unchanged. Re-render uses the live constant (existing FG-016 behaviour).

---

## Alternatives Considered

- **Global replace CalibAi → CalibraytAI** — Rejected: rewrites history; breaks identifiers; conflates tenant branding.
- **Rename office chrome to CalibraytAI in this gate** — Rejected: office chrome is Brayman Construction Platform; tenant/product split must hold.
- **Schema or data migration for branding** — Rejected: no table/model rename; no live UPDATE.
- **Rename ADR-019 / CAR-001 files** — Rejected: historical filenames.

## Consequences

**Positive:** Current user-facing product text and current governance name CalibraytAI; former name is durable; history and identifiers preserved; tenant branding protected.

**Negative:** Field header image remains a Brayman Construction PNG until Slice 3. Remaining CalibAi hits in historical docs are intentional. Permit HTML/PDF re-render of old analyses will show the new live advisory constant while stored finding rows keep the former wording.

## Module Ownership Impact

None. No module gains or loses record ownership. Product identity is a platform-level naming concern, not a new module.

## Data Ownership Impact

None. No new records. Frozen permit findings, historical paths, and provenance strings remain owned by their existing modules.

## Migration Impact

**None.**

## Testing Impact

Dedicated FG-028 tests for Field title/alt, Project Hub aria-label, Permit PDF title/advisory, tenant neutrality, office chrome preservation, and identifier preservation. Update FG-016 / FG-017 assertions that required the former visible product string.

## Documentation Impact

[product-identity.md](../governance/product-identity.md); [FG-028](../feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md); current-authority vision, V1 register product field, AGENTS, Cursor rules, continuity protocol, roadmap, current-state, session-handoff; future-facing FG-024 / supplier-channel / Native Signing product references. Do not rewrite closed Feature Gate narratives or chat-workflow-log history.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-09-09 |
| ChatGPT review | Authorized implementation prompt | 2026-09-09 |
| Cursor implementation note | Slices 1–2 under FG-028; Slice 3 held | 2026-09-09 |
| Cursor subsequent status | Slice 3 **INSTALLED / TESTED / VERIFIED.** Runtime `calibraytai-logo-v2.png` on Field header (light background). FG-028 **CLOSED / OPERATIONAL FOR UAT**. Tenant office/login/Brand Profile logos unchanged. | 2026-09-09 |

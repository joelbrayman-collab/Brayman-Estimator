# FG-024 Slice A — North American Legal Content Library preflight

| Attribute | Value |
|-----------|--------|
| Status | **PREFLIGHT COMPLETE.** Subsequent Slice A product **CLOSED / OPERATIONAL FOR UAT** (live-migrated 2026-09-13). This preflight remains the architecture freeze; it does **not** authorize Slices B–D. |
| Date | 2026-09-12 |
| Gate | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) Slice A only |
| ADR | [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted** — required **before product code**. Acceptance does **not** authorize Slice A product. |
| Alembic | Live current **`b1c2d3e4f5a6 (head)`**. Repository head **`b1c2d3e4f5a6`**. One graph head. Applied live 2026-09-13. |
| Product | CalibraytAI (formerly CalibAi) |
| Tenant | Brayman Construction Inc. / ORG-001 |
| Parent recon | 12 Sep 2026 V1-04 / V1-06 reconnaissance on SHA `3200112d627d6c6d8173daf72194f8409ac84b11` |

```text
FG-024 SLICE A PREFLIGHT:
COMPLETE
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
ADR-050 ACCEPTED / ARCHITECTURE ONLY
NO SCHEMA FILE
NO LEGAL DRAFTING
NO GENERIC NORTH AMERICAN FALLBACK
ONTARIO = FIRST PACKAGE / NOT PRODUCT SCOPE
V1 SCORES UNCHANGED
V1-04 REMAINS PARTIAL / OUTPUT 4 NOT IMPLEMENTED
V1-06 REMAINS PARTIAL / 0.25
```

This document freezes Slice A **engine architecture** for a later bounded product prompt. It does **not** authorize that prompt.

**Subsequent status (2026-09-13):** [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted** by Joel Brayman / ChatGPT Architect (architecture / fail-closed ownership only). Slice A architecture prerequisite **satisfied**. Product implementation remains **NOT AUTHORIZED / NOT IMPLEMENTED**. Do **not** rescore V1.

**Subsequent status (2026-09-13, Slice A product):** Empty-library persistence, ADR-037-backed selection, and coded fail-closed are **implemented in the repository**. Alembic **`b1c2d3e4f5a6`**. Live migration **not** run. Legal Content Gate remains **empty**. V1 score **unchanged**. Do **not** begin Slice B/C/D.

**Subsequent status (2026-09-13, Slice A live migrate + UAT):** Slice A **CLOSED / OPERATIONAL FOR UAT**. Live current **`b1c2d3e4f5a6 (head)`**. Library **empty**. Evidence [fg024-slice-a-live-migrate-bounded-uat-record.md](../testing/fg024-slice-a-live-migrate-bounded-uat-record.md).

**Out of this preflight:** Slice B update engine product; Slice C generation; Slice D live monitoring; Ontario/U.S. legal population; Family 05 legal approval; Native Signing product; V1-04 product work; V1 rescore.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | ADR-037 / FG-015 jurisdiction **identity** implemented (`CA` → `CA-ON` → `CA-ON-OTTAWA` seeded). Legal Content Gate **empty**. Family 05 **COMMERCIAL_DRAFT** presentation master outside Git. No `legal_content` models in `app/`. No contract generation. Fail-closed for contracts is **by absence**. Outputs 1–3 exist. Output 4 does not. |
| **Intended (Slice A later product)** | Empty North American library persistence + package selection from the existing resolver + coded fail-closed when no ACTIVE counsel-approved package. Still **no** legal population. Still **no** executable contract. |
| **Future (other FG-024 slices / V1-06)** | Slice B maintains the library. Slice C generates and freezes. 06D Ontario counsel approval. V1-07 signing. 06J extra jurisdictions POST-V1. Slice D live source monitoring recommended POST-V1 (register §13 #3). |

---

## 2. Library objects and version / supersession states

Platform-governed objects (conceptual; **not created**):

| Object | Role |
|--------|------|
| Jurisdiction package | Bind a resolver node (country / province-territory-state, later municipality only if a later gate requires it) to a counsel-reviewable contract/warranty set |
| Content object | Versioned clause, warranty, notice, disclosure, prescribed form, or other counsel-approved legal content |
| Provenance record | Source authority, retrieval date, publication date, effective dates |
| Support status | SUPPORTED / LIMITED / UPDATE PENDING REVIEW / NOT YET SUPPORTED |

### Library package / content-object states

```text
PROPOSED → COUNSEL REVIEW → APPROVED → ACTIVE → SUPERSEDED
```

| State | Meaning | May generate a contract? |
|-------|---------|--------------------------|
| PROPOSED | Candidate exists; not counsel-approved | **No** |
| COUNSEL REVIEW | Routed for human/counsel review | **No** |
| APPROVED | Counsel/human authorized that **content version** | **No** until ACTIVE under effective-date rules |
| ACTIVE | Platform-activated for generation | **Yes**, only for that jurisdiction package |
| SUPERSEDED | Replaced; retained for provenance | **No** (historical issued snapshots remain frozen) |

`APPROVED` ≠ `ACTIVE`. Unresolved effective-date conflict → FAIL CLOSED.

These library states are **not** the generated-document instance states:

```text
PROPOSED → APPROVED → GENERATED → VERIFIED → SENT FOR SIGNATURE → SIGNED → SUPERSEDED
```

Instance states belong to Slice C / Native Signing. Slice A does not generate instances.

AI may later assist with candidates. AI **must not** mark APPROVED, activate unapproved content, or rewrite issued/signed contracts.

---

## 3. Project jurisdiction → package selection

Reuse existing identity only ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md); [jurisdiction-resolution.md](jurisdiction-resolution.md); `app/services/jurisdiction.py`).

```text
PROJECT LOCATION
→ COUNTRY
→ PROVINCE / STATE
→ MUNICIPALITY / COUNTY (identity only)
→ MATCH ACTIVE COUNSEL-APPROVED JURISDICTION PACKAGE
→ ELSE FAIL CLOSED
```

Selection rules for a later product slice:

1. Resolve ProjectLocation to a governed jurisdiction node.
2. If identity is **UNRESOLVED**, fail closed (no guessed Ontario/Ottawa fallback).
3. Select the package whose jurisdiction node matches the resolved identity (province/state first; more specific municipal package only if one exists and is ACTIVE).
4. Require library state **ACTIVE** and effective-date coverage for the generation date.
5. Organization commercial content (Brand Profile / FG-017) may overlay **only where lawful** and must not conflict with jurisdiction authority.
6. Do **not** consult `Organization.tax_jurisdiction` as AHJ or contract jurisdiction.
7. Do **not** treat Permit Rules findings as the selected contract package.

Seeded V1 identity nodes remain `CA` / `CA-ON` / `CA-ON-OTTAWA`. That does **not** populate an Ontario legal package.

---

## 4. Fail-closed matrix

Intended product principle (already in FG-024 and the Legal Content Gate):

CalibraytAI must not generate or present an apparently approved contract for a jurisdiction / family / version that lacks the required approved legal-content authority.

| Condition | Result | Fallback allowed? |
|-----------|--------|-------------------|
| Jurisdiction identity UNRESOLVED | **BLOCK** | No |
| Jurisdiction identity resolved; no package row | **BLOCK** (`NOT YET SUPPORTED`) | No |
| Package exists but PROPOSED or COUNSEL REVIEW only | **BLOCK** | No |
| Package APPROVED but not ACTIVE | **BLOCK** | No |
| Package SUPERSEDED with no ACTIVE replacement | **BLOCK** | No |
| Package expired / outside effective-date window | **BLOCK** | No |
| Unresolved effective-date conflict | **BLOCK** | No |
| Required counsel review incomplete | **BLOCK** | No |
| LIMITED coverage presented as fully supported | **BLOCK** (must not market as fully supported) | No |
| Generic “North American” template | **Prohibited** | — |
| Substitute another province/state package | **Prohibited** | — |
| Use Family 05 as executable contract | **Prohibited** | — |
| Use Permit Rules as contract clauses | **Prohibited** | — |
| AI marks content APPROVED or ACTIVE | **Prohibited** | — |
| Draft presentation master viewed **outside** product generation, with NOT FOR EXECUTION labels | Allowed as FG-022 presentation only | Must not be issued as approved |
| Draft templates issued / sent for signature as approved contracts | **Prohibited** | — |

**Today (Current):** the same outcomes occur because **no generator exists**. That is fail-closed by absence, not a coded CONTRACT path.

---

## 5. Ownership table

| Concern | Owner | Slice A role |
|---------|--------|--------------|
| Legal Content Gate approval (`APPROVED`) | [legal-content-and-templates.md](../governance/legal-content-and-templates.md) | Preserved. AI cannot approve. |
| North American library engine / packages / versions | **CONTRACT** / FG-024 Slice A | Future persistence + selection + fail-closed |
| Four-output package completeness | V1-04 register | Tracks output 4; does **not** own the engine |
| Output 4 generation + freeze | V1-06 / FG-024 Slice C | **Out of Slice A** |
| Estimate / internal breakdown | Estimating / FG-012 | Referenced commercial source later; not owned |
| Customer estimate / Proposal | Proposals / FG-012 | Referenced commercial source later; not owned |
| QuickBooks-ready pair | Estimating / FG-032 | Unchanged. Do not rescore under V1-04. |
| Permit Rules | Permit Intelligence / ADR-038 / FG-016 | Independent content. Not contract clauses. |
| Jurisdiction identity | Projects / ADR-037 / FG-015 | Referenced. Do not duplicate. |
| Presentation masters | FG-022 | Visual only. Family 05 remains COMMERCIAL_DRAFT. |
| Brand overlay | FG-017 / ADR-040 | Lawful commercial presentation only |
| Native Signing process | V1-07 | Separate. Not template legal text. |
| Change Order document family | FUTURE pin | Not output 4 |

---

## 6. Schema recommendation

**Later Slice A product: YES (additive).** **This pass: no file. No `flask db upgrade`. No live DB mutation.**

Proposed names only (do not create):

### `legal_content_jurisdiction_packages`

Platform-governed. Not org commercial intelligence.

Suggested columns: id; jurisdiction_definition_id (FK to existing platform jurisdiction nodes); country_code; province_or_state_code; support_status; library_state (`PROPOSED` / `COUNSEL_REVIEW` / `APPROVED` / `ACTIVE` / `SUPERSEDED`); effective_from; effective_to; counsel_approved_at; counsel_approved_by (human identifier, not AI); activated_at; superseded_by_id; provenance JSON/text; created_at.

Unique: at most one **ACTIVE** package per jurisdiction node.

### `legal_content_objects`

Versioned content inside a package: kind (contract provision, warranty, notice, disclosure, prescribed form, other); version_number; library_state; source citation; body **unpopulated in Slice A product**; hashes later at generation time.

### What Slice A product must **not** add

- generated contract snapshot tables (Slice C);
- update-engine candidate tables (Slice B);
- legal-source watcher tables (Slice D);
- Ontario/U.S. seed legal language;
- reuse of `permit_rules` rows as contract clauses.

If a later product prompt requires schema, that prompt must include **Joel-approved migration**. Do not generate Alembic casually.

---

## 7. ADR decision

| Decision | Value |
|----------|--------|
| Required? | **REQUIRED BEFORE PRODUCT CODE** |
| This pass | [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) drafted **Proposed** from [ADR-000-template.md](../adr/ADR-000-template.md) |
| Accept now? | **No** (preflight 2026-09-12). **Accepted** 2026-09-13 architecture only. |
| Implement from Accepted? | **No** |

FG-024 Q11 deferred library schema / package ownership. This preflight supplies that ADR as Proposed. Joel **Accepted** ADR-050 on **13 Sep 2026**. Slice A product code still requires a later bounded implementation prompt.

---

## 8. Out of Slice A

- Legal drafting; Ontario or U.S. statutory language; Construction Act / Tarion / HCRA / Consumer Protection drafting
- Marking Family 05 legally approved
- Contract generation, issue, PDF/DOCX product rendering, freeze snapshots
- Native Signing
- Slice B live or batch source monitoring
- Slice D alerts
- Website publish; HostPapa
- V1 rescore; rebuilding outputs 1–3
- Second contract system; second resolver; generic NA fallback

---

## 9. Smallest later product slice (not authorized)

**Empty library + fail-closed. No executable contract output.**

A later Joel-authorized prompt could implement:

1. Additive empty library tables (after ADR-050 **Accepted** and an approved migration).
2. Selection service: ProjectLocation → resolver → package lookup.
3. Deterministic BLOCK with a contractor-facing reason when no ACTIVE package exists (including today’s empty Ontario case).
4. Tests: unresolved jurisdiction BLOCK; resolved Ontario with empty library BLOCK; Family 05 not consulted; Permit Rules not consulted; no generic fallback; org isolation if any org-scoped preview is added (default: no generation UI).
5. Optional Hub CONTRACT panel: **Contract package not available** / fail-closed. Must not look like an approved contract.

That slice would advance 06A / 06B selection / 06G **implementation** without 06D, 06E, or 06F. It would **not** complete V1-04. It would **not** flip BMR DEMO READY by pretending Family 05 is approved.

Do **not** begin that slice from this document.

---

## 10. V1 scoring (unchanged)

| Package | Status | Factor | Contribution |
|---------|--------|--------|--------------|
| V1-04 | PARTIAL | 0.50 | 4.0 |
| V1-06 | PARTIAL | 0.25 | 4.0 |
| Readiness | **60% / 4 of 11** | — | — |

Do **not** rescore because a preflight now exists. 06A remains **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** until product exists.

---

## 11. Prohibited scope (this pass)

Application code · models · routes · services · templates · CSS/JS · tests altered for new behaviour · Alembic revision · live DB mutation · legal-content population · Family 05 legal-status change · Native Signing product · V1-04 product · accepting ADR-050 · accepting ADR-008 or ADR-010 · website · HostPapa · rescore V1

**Subsequent (2026-09-13):** [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. The 2026-09-12 preflight prohibition on accepting ADR-050 is closed. Slice A **product** remains prohibited until a bounded implementation prompt.

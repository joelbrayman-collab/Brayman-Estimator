# Feature Gate FG-022: Reusable Approved Document Template Family V1 — Project-Neutral Extraction

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-022` |
| Feature Name | Reusable Approved Document Template Family V1 — Project-Neutral Extraction |
| Target Milestone | **None.** FG-022 is the governing identifier. Do **not** assign a new M0xx number. Do **not** assign FG-022 to Field Web, Native Signing, FG-012 product renderers, or Legal Content Gate population. |
| Owning domain | **Approved Document Presentation / Project Document Package** ([approved-document-presentation-reference-baseline.md](../architecture/approved-document-presentation-reference-baseline.md); [project-document-package.md](../architecture/project-document-package.md)). This is **not** a new product code module. |
| Date | 2026-09-04 |
| Status | **CLOSED / APPROVED REUSABLE MASTER FAMILY V1** (2026-09-04). Extraction **complete**. Source / zero-residue / visual verification **PASS**. Joel presentation-master approval **COMPLETE**. Durable custody **COMPLETE**. Product implementation **NONE**. Database migration **NONE**. Legal Content Gate **UNCHANGED / EMPTY**. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. Immutable source **unchanged**. |
| Architecture | [approved-document-presentation-reference-baseline.md](../architecture/approved-document-presentation-reference-baseline.md) · [project-document-package.md](../architecture/project-document-package.md) · [testing/allen-jacques-garage-presentation-baseline-manifest.md](../testing/allen-jacques-garage-presentation-baseline-manifest.md) · [testing/reusable-approved-document-template-family-v1-register.md](../testing/reusable-approved-document-template-family-v1-register.md) · [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [organization-brand-profile.md](../architecture/organization-brand-profile.md) · [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted** |
| Related ADRs | [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted** (bytes outside Git; SHA-256 identity in Git). [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted** (Brand Profile remains separate). **No new ADR.** |
| Prerequisites | Approved presentation source custody **CLOSED**. Source ZIP SHA-256 `26f5e579c01651f2e304a76fbed1de7ab54ba144055937c2a1fc6871ebe5e874`. 17/17 members verified. This implementation prompt authorized 2026-09-04. |
| Approved baseline | Docs + durable derived masters outside Git. Product-changing tests remain dedicated FG-021 **19** / focused **147** / full **557**. Alembic current = head **`d2e3f4a5b6c7`**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **CLOSED / APPROVED REUSABLE MASTER FAMILY V1** |
| Extraction | **COMPLETE** — seven DOCX masters + seven verification PDFs |
| Source verification | **PASS** |
| Zero-residue verification | **PASS** |
| Visual verification | **PASS** |
| Joel presentation-master approval | **COMPLETE** (2026-09-04) |
| Durable custody | **COMPLETE** — `Reusable Master Template Family V1/` |
| Immutable presentation source | **UNCHANGED** — durable custody **CLOSED** |
| Legal Content Gate | **UNCHANGED / EMPTY** — not populated by this gate |
| FG-012 product renderers | **UNCHANGED** |
| FG-017 Brand Profile raster | **UNCHANGED** — unresolved vs recovered header |
| FG-021 Field Web | **UNCHANGED** — **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** / **NOT CLOSED** |
| Schema / Alembic | **NONE** — live current remains **`d2e3f4a5b6c7`** |
| Product implementation | **NONE** |
| Database migration | **NONE** |
| New ADR | **None** |
| New product module | **None** |

This gate is a **separately governed parallel document-template track**. It does **not** alter [FG-021](FG-021-field-web-v1-today-and-capture.md) or roadmap item 12. Implementation landed 2026-09-04. Joel presentation-master approval recorded 2026-09-04. The gate is **CLOSED**.

**Subsequent status (2026-09-06):** [FG-021](FG-021-field-web-v1-today-and-capture.md) is independently **CLOSED** with the explicit SESSION-EXPIRY deferred exception. FG-022 remains **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. The FG-021 row above is the 2026-09-04 at-close snapshot.

### Governing template authority after closure

```text
IMMUTABLE SOURCE / PROVENANCE AUTHORITY
  = Allen Jacques Presentation Baseline - 2026-09-03

REUSABLE PRESENTATION AUTHORITY
  = Reusable Master Template Family V1
    /Users/joelbrayman/Documents/CalibAi/Approved Document Templates/
    Reusable Master Template Family V1/

For future Brayman manual project-document generation:
  PROJECT DATA AUTHORITY  = current governed Project / Estimate / Pricing records
  PRESENTATION AUTHORITY  = APPROVED REUSABLE MASTER FAMILY V1
```

Do **not** use Allen Jacques project data. Do **not** use the Allen Jacques project documents as working templates when the approved reusable masters are available. The Allen Jacques package remains immutable provenance/reference.

Family 05 presentation-master approval does **not** equal legal-template approval. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED / NOT FOR EXECUTION / NOT FOR SIGNATURE**.

---

## Purpose and business rationale

The governed Allen Jacques presentation family is safely preserved as an immutable **PRESENTATION / DOCUMENT DESIGN** baseline. The working source still contains Allen Jacques project-specific information.

CalibAi needs a durable, reusable, **PROJECT-NEUTRAL** Brayman/CalibAi master family so future estimates do not depend on copying an old customer’s project documents.

The derived master family must:

- preserve the approved presentation exactly (**NO REDESIGN**)
- remove all Allen Jacques project-specific content
- retain provenance to the immutable source
- retain internal / customer / legal classifications
- be durably stored and versioned
- be independently hash-identifiable
- never become an independent source of project or financial truth
- never imply legal approval that does not exist

```text
IMMUTABLE APPROVED PRESENTATION SOURCE (provenance)
  → APPROVED REUSABLE MASTER FAMILY V1 (this gate, CLOSED)
    ≠ PRODUCT HTML/REPORTLAB RENDERERS (FG-012)
    ≠ ORGANIZATION BRAND PROFILE RASTER (FG-017)
    ≠ LEGAL CONTENT GATE / EXECUTABLE CONTRACT (empty)
    ≠ PROGRAMMATIC DOCUMENT TEMPLATE ENGINE (future, out of scope)
```

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Future work still depends on copying Allen Jacques project documents. CalibAi needs project-neutral reusable visual masters that keep the approved presentation and drop that project’s facts. |
| 2 | Who is the user? | Joel / office estimator using governed presentation masters for later document work. Not the customer. Not Field Web. Not a signing workflow. |
| 3 | Which module owns it? | **Approved Document Presentation / Project Document Package** owns reusable presentation masters, master-family identity, master version, presentation structure, provenance, document classification, and approved presentation geometry/style. **Not** a new `app/` module. Estimating / Pricing own costs, labour, pricing, margin, tax, and estimate totals. **Projects** owns Client / Project / Site facts. **Organization Brand Profile** owns governed organization branding facts. **Legal Content Gate** owns approved contract/warranty language. |
| 4 | What data does it own? | Derived reusable DOCX visual masters (bytes outside Git), Git identity/provenance register, classification, version, source-baseline SHA, extraction date, approval-lifecycle state. **Not** estimate lines, prices, or legal-clause registers. |
| 5 | What data does it reference? | Immutable source ZIP SHA-256 `26f5e579c01651f2e304a76fbed1de7ab54ba144055937c2a1fc6871ebe5e874`; seven presentation families 01–07; shared `styles.xml` SHA `760005ab7de5676d3d702b2484b60c7960b2b09be48eb0e7a2756ddea328973e`; recovered header raster SHA `0949c20891bb38a651403ca4e1965b3938a471bb68ec82773df80f3d5c50d4d2`. Does **not** own FG-012 renderer output or FG-017 logo bytes. |
| 6 | What may implementation change? | Derived masters in a **separate** durable directory; Git identity register rows/hashes; visual-verification notes; governed docs. **Only after a separate extraction implementation prompt.** Neutral field labels such as Client / Project / Site / Date are allowed. |
| 7 | What must it not change? | Immutable source ZIP / DOCX / PDF; `app/`; `tests/`; Alembic; database; FG-012 HTML/ReportLab; Proposal rendering; Internal Breakdown rendering; FG-017 logo substitution; FG-021; Legal Content Gate registers; Native Signing; MONITOR; LEARN; Phase D; supplier; QuickBooks API; a new programmatic templating syntax; fake customer data. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. Extraction, verification, Joel presentation-master approval, and durable custody **met**. Gate **CLOSED**. Family 05 legal content **not** approved. |
| 9 | Tests required? | SHA identity of derived masters; zero-residue scan; visual inspection of every extracted master. Automated product pytest is **not** the acceptance path. Do **not** rerun the full suite merely because this gate exists. |
| 10 | Documentation? | This gate; feature-gate index; presentation baseline pin; project-document-package ownership row; empty V1 register; legal-content subsequent status; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log. |
| 11 | ADR required? | **No.** Existing project-document, custody ([ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md)), Brand Profile ([ADR-040](../adr/ADR-040-organization-brand-profile.md)), and Legal Content Gate boundaries are sufficient. **STOP** if implementation would need a new product document module, a second commercial source of truth, Legal Content Gate population, FG-012 visual-parity claim, FG-017 raster substitution, or a programmatic template engine. |
| 12 | Migration? | **No.** If a schema change appears required, **STOP**. Do not create a migration. |

---

## Ownership boundary

| Concern | Owner | Does **not** own |
|---------|--------|------------------|
| Reusable presentation masters, family identity, version, structure, provenance, classification, approved geometry/style | **Approved Document Presentation / Project Document Package** | Project facts; costs; legal-clause approval |
| Costs, labour, pricing, margin, tax, estimate totals | **Estimating / Pricing** | Presentation masters |
| Client, Project, Site, project-specific facts | **Projects** | Presentation masters |
| Governed organization branding facts | **Organization Brand Profile** ([FG-017](FG-017-organization-brand-profile-v1.md)) | Recovered presentation header raster as Brand Profile identity |
| Approved contract / warranty language | **Legal Content Gate** | Presentation-only Document 05 treatment |

No master template may become a hidden second source of truth. Project and financial values come from governed estimate/project records, not from copied master cells.

This gate does **not** create `docs/modules/` product-module ownership. Presentation custody already lives on architecture pins, not in `app/`.

---

## Immutable source (do not modify)

| Field | Value |
|-------|--------|
| Filename | `Allen_Jacques_Garage_FINAL_116778_Internal_and_Customer_2026-08-31.zip` |
| SHA-256 | `26f5e579c01651f2e304a76fbed1de7ab54ba144055937c2a1fc6871ebe5e874` |
| Status | **RECOVERED / SHA VERIFIED / 17/17 MEMBERS VERIFIED / DURABLE CUSTODY CLOSED** |
| Durable directory | `/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/Allen Jacques Presentation Baseline - 2026-09-03/` |
| Role | Immutable approved **PRESENTATION / DOCUMENT DESIGN** baseline |

Do **not** extract into, rewrite, or replace files in the immutable-source directory. Do **not** treat derived masters as the source.

---

## Seven reusable master families

| # | Family | Classification |
|---|--------|----------------|
| 01 | Labour Calculation Detail | **INTERNAL** |
| 02 | Internal Detailed Cost Breakdown | **INTERNAL** |
| 03 | Customer Facing Estimate | **CUSTOMER-FACING** |
| 04 | QuickBooks Estimate Entry | **INTERNAL ENTRY REFERENCE**. **Not** customer-facing. **Not** QuickBooks API. |
| 05 | Ontario Construction Contract | **PROJECT-NEUTRAL PRESENTATION / COMMERCIAL-DRAFT REFERENCE**. **APPROVED REUSABLE PRESENTATION MASTER**. **COMMERCIAL_DRAFT**. **NOT LEGALLY APPROVED**. **NOT FOR EXECUTION**. **NOT FOR SIGNATURE**. |
| 06 | Door / Window / Skylight Schedule | **CUSTOMER-FACING** |
| 07 | Client Construction Proposal | **CUSTOMER-FACING** |

Source-quote PDFs in the recovered ZIP remain **PROJECT SOURCE MATERIAL**. They are **not** reusable masters.

---

## Document 05 — hard legal boundary

The Legal Content Gate is **EMPTY**.

FG-022 **must not** create an approved Ontario Construction Contract template.

Reusable V1 treatment for family 05:

```text
PROJECT-NEUTRAL PRESENTATION / COMMERCIAL-DRAFT REFERENCE
COMMERCIAL DRAFT — NOT FOR EXECUTION
```

Presentation approval does **not** equal legal approval. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED** after this presentation-master approval.

Do **not**:

- populate the Legal Content Gate
- approve contract clauses
- approve warranty language
- authorize execution
- authorize Native Signing

---

## Frozen presentation characteristics

From the [manifest](../testing/allen-jacques-garage-presentation-baseline-manifest.md). Implementation must preserve them. **NO REDESIGN.**

| Characteristic | Frozen value |
|----------------|--------------|
| Page | Letter 8.5 × 11 in |
| Margins | approximately 0.55 in top/bottom; approximately 0.65 in left/right |
| Header/footer | approximately 0.5 in |
| Typography | Aptos-based body styles |
| Structure | ALL-CAPS primary titles; identity block where applicable; table presentation; heading hierarchy; spacing; header/footer organization |
| Shared `word/styles.xml` SHA-256 | `760005ab7de5676d3d702b2484b60c7960b2b09be48eb0e7a2756ddea328973e` |
| Recovered presentation header raster SHA-256 | `0949c20891bb38a651403ca4e1965b3938a471bb68ec82773df80f3d5c50d4d2` |

---

## Master source format

**DOCX-based reusable master files.**

The approved source presentation is a Word / `python-docx` family. Do **not** invent a new renderer. Do **not** translate the presentation into HTML or ReportLab for convenience.

PDF may be produced during implementation for visual verification. PDF is **not** the editable master source.

---

## Project-neutral extraction rule

Future implementation must remove **all** Allen Jacques project-specific information.

Audit at minimum for:

- Allen
- Jacques
- 3415 Roger Stevens
- North Gower
- 116778
- August 31, 2026

and all project-specific names, addresses, project IDs, dates, prices, costs, quantities, hours, supplier values, subcontract values, scope, allowances, exclusions, door/window/skylight information, source-quote information, and project notes.

**Acceptance requirement:**

```text
ZERO ALLEN JACQUES PROJECT-SPECIFIC CONTENT
IN REUSABLE MASTER FILES.
```

Neutral field labels/placeholders for Client / Project / Site / Date are allowed. Do **not** use fake customer data. Do **not** establish a full programmatic templating syntax unless separately required.

FG-022 distinguishes:

| Kind | This gate |
|------|-----------|
| **Reusable visual master** | **Complete** — **APPROVED REUSABLE MASTER FAMILY V1** |
| **Future programmatic document template engine** | **Out of scope** |

---

## Derived-master custody and versioning

Root (already established):

`/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/`

| Store | Path | Role |
|-------|------|------|
| Immutable source | `Allen Jacques Presentation Baseline - 2026-09-03/` | Exact original ZIP only. Do **not** use as the derived working directory. |
| Derived V1 masters | `Reusable Master Template Family V1/` | Extracted DOCX masters + verification PDFs (2026-09-04). |

Each future master must record in Git:

- family number
- filename
- classification
- version
- source baseline (ZIP SHA-256)
- extraction date
- approval state
- SHA-256 of the derived file
- legal-content status where applicable (family 05: **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**)

Binary DOCX/PDF files remain **outside Git** unless separate governance changes the binary-custody rule. Git records identity and provenance in [reusable-approved-document-template-family-v1-register.md](../testing/reusable-approved-document-template-family-v1-register.md).

---

## Approval lifecycle

An extracted master does **not** automatically become approved.

```text
EXTRACTED
  → SOURCE-VERIFIED
  → ZERO-RESIDUE VERIFIED
  → VISUALLY VERIFIED
  → JOEL APPROVED
  → APPROVED REUSABLE MASTER
```

Family 05 retains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED** even after presentation-master approval.

---

## Visual acceptance

The implementation pass must render and inspect **every** extracted master.

Verify: page geometry, letterhead, header, footer, typography, tables, heading hierarchy, spacing, wrapping, page breaks, blank pages, orphan headings, clipping, overlap, font substitution, neutral placeholder presentation, and classification labels.

Acceptance target:

```text
PROJECT-NEUTRAL
+
VISUALLY FAITHFUL TO APPROVED PRESENTATION
```

not:

```text
REDESIGNED
```

---

## Acceptance criteria

1. Immutable source ZIP SHA-256 unchanged.
2. Derived masters live only under `Reusable Master Template Family V1/` — not in the immutable-source directory.
3. Seven families 01–07 extracted as DOCX visual masters (PDF optional for inspection).
4. Zero Allen Jacques project-specific residue.
5. Frozen presentation characteristics preserved (no redesign).
6. Classifications retained, including Document 04 **INTERNAL ENTRY REFERENCE** and Document 05 **COMMERCIAL DRAFT — NOT FOR EXECUTION**.
7. Git identity register complete (SHA-256 per master).
8. Visual inspection of every master **PASS**.
9. Joel presentation-master approval recorded per family.
10. Legal Content Gate still **empty**. FG-012 / FG-017 / FG-021 unchanged.

**Met** 2026-09-04. Joel presentation-master approval recorded. Gate **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Family 05 legal content remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. Legal Content Gate remains **empty**.

---

## FG-012 relationship

[FG-012](FG-012-estimate-output-consistency.md) product renderers remain unchanged. They are materially visually different from the approved recovered Word family.

Do **not**:

- modify FG-012
- modify Proposal rendering
- modify Internal Breakdown rendering
- claim visual parity
- change `app/` code

Product-renderer reconciliation is **future separately governed work**.

---

## FG-017 relationship

FG-017 raster SHA-256 `948f96e08827f18d77b47538f65c8b98b45caaf9c981adccba0189976948efe9` and the recovered approved presentation header raster SHA-256 `0949c20891bb38a651403ca4e1965b3938a471bb68ec82773df80f3d5c50d4d2` are **different byte identities**.

Do **not** silently substitute FG-017 branding into the master extraction.

For V1:

```text
THE APPROVED RECOVERED PRESENTATION IS THE IMMUTABLE SOURCE / PROVENANCE AUTHORITY.
THE APPROVED REUSABLE MASTER FAMILY V1 IS THE REUSABLE PRESENTATION AUTHORITY.
```

Do **not** silently substitute FG-017 branding into the approved reusable masters.

Broader Brand Profile raster reconciliation remains **unresolved future work**.

---

## FG-021 / roadmap relationship

[FG-021](FG-021-field-web-v1-today-and-capture.md) was **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** / **NOT CLOSED** at FG-022 close (2026-09-04). **Subsequent status (2026-09-06):** FG-021 is independently **CLOSED** subject to the explicit SESSION-EXPIRY deferred exception. FG-022 does **not** reopen FG-021.

Roadmap item 12 is unchanged by this gate. This gate is **not** item 13 MONITOR and does **not** authorize MONITOR, LEARN, Native Signing, or QuickBooks.

---

## Out of scope

Historical implementation-pass constraints (2026-09-04 extraction) forbade closing the gate or assigning JOEL APPROVED until a separate Joel/ChatGPT approval. That approval was recorded 2026-09-04 and **supersedes** the extraction-pass prohibition on closure.

Still out of scope after closure:

- Populating Legal Content Gate
- Creating or approving legal content (contract clauses, warranty, statutory, consumer-protection)
- Changing FG-012, FG-017, or FG-021
- Continuing iPhone UAT
- Closing FG-021
- Observation Delete
- Native Signing
- MONITOR / LEARN
- Phase D
- Supplier work
- QuickBooks API
- Programmatic template engine
- Regenerating master bytes
- Treating Family 05 as an approved Ontario construction contract, production contract template, legally approved document, or ready-for-signature instrument

---

## Related

- [approved-document-presentation-reference-baseline.md](../architecture/approved-document-presentation-reference-baseline.md)
- [testing/allen-jacques-garage-presentation-baseline-manifest.md](../testing/allen-jacques-garage-presentation-baseline-manifest.md)
- [testing/reusable-approved-document-template-family-v1-register.md](../testing/reusable-approved-document-template-family-v1-register.md)
- [project-document-package.md](../architecture/project-document-package.md)
- [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md)
- [FG-012-estimate-output-consistency.md](FG-012-estimate-output-consistency.md)
- [FG-017-organization-brand-profile-v1.md](FG-017-organization-brand-profile-v1.md)
- [FG-021-field-web-v1-today-and-capture.md](FG-021-field-web-v1-today-and-capture.md)

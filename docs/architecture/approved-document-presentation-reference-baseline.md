# Approved Document Presentation Reference Baseline

| Attribute | Value |
|-----------|--------|
| Status | **APPROVED PRESENTATION / DOCUMENT DESIGN BASELINE** (2026-09-03). **SOURCE CUSTODY CLOSED** (2026-09-04). [FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **APPROVED / IMPLEMENTATION NOT STARTED**. Extraction **not** performed. **Not** Legal Content Gate approval. **Not** product implementation. |
| Date | 2026-09-03 (presentation approval); **2026-09-04** (durable source custody) |
| Product | The Estimator / CalibAi |
| Canonical record | This document |
| Manifest | [testing/allen-jacques-garage-presentation-baseline-manifest.md](../testing/allen-jacques-garage-presentation-baseline-manifest.md) |
| Related | [project-document-package.md](project-document-package.md) · [testing/uat-reference-cases.md](../testing/uat-reference-cases.md) · [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [organization-brand-profile.md](organization-brand-profile.md) · [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) · [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) · [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) · [FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) |

## Purpose

Close the artifact-custody gap for the recovered Allen Jacques garage document package. Joel confirmed that package was **the first project using the approved document presentation / template family**.

This pin records **presentation / document-design approval** of that family, using the recovered project files as the **reference baseline**.

It does **not**:

- convert those files into reusable templates
- approve Ontario contract/warranty legal language
- change FG-012 HTML/PDF renderers
- replace the FG-017 Brand Profile logo
- authorize Native Signing or customer execution of document 05

## What was recovered

**Category D generated project package** (not a `.dotx` / generator):

`Allen_Jacques_Garage_FINAL_116778_Internal_and_Customer_2026-08-31.zip`

SHA-256: `26f5e579c01651f2e304a76fbed1de7ab54ba144055937c2a1fc6871ebe5e874`

**Durable custody** (closed 2026-09-04): `/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/Allen Jacques Presentation Baseline - 2026-09-03/` — exact original ZIP only. Recovered Desktop copy remains leave-in-place provenance. See **Custody** below.

First project: Allen Jacques / Detached Garage / 3415 Roger Stevens Road, North Gower. Dated 2026-08-31. Quote basis `$116,778.00 + HST` appears in customer documents and is **project-specific**, not a template value.

Seven presentation families (DOCX + PDF pairs) plus three **source-quote PDFs** (project source material, not presentation templates). Exact names and hashes: the [manifest](../testing/allen-jacques-garage-presentation-baseline-manifest.md).

## Classification

Joel/ChatGPT (2026-09-03): this package is the **first project using the Joel-approved document presentation family**. Documents **01–07** are therefore **APPROVED PRESENTATION REFERENCES**.

**Approved by that classification:** visual design, page geometry, typography, header/footer presentation, section hierarchy, table presentation, spacing, and document-family visual identity.

**Not approved merely by that classification:** Allen Jacques project data, prices, quantities, dates, scope, allowances, exclusions, source-quote contents, legal language, or commercial terms from that specific project.

| Family | Presentation | Functional classification | Legal content |
|--------|--------------|---------------------------|---------------|
| 01 Labour Calculation Detail | **APPROVED PRESENTATION REFERENCE** | Internal | N/A (internal commercial) |
| 02 Internal Detailed Cost Breakdown | **APPROVED PRESENTATION REFERENCE** | Internal | N/A (internal commercial) |
| 03 Customer Facing Estimate | **APPROVED PRESENTATION REFERENCE** | Customer-facing | N/A |
| 04 QuickBooks Estimate Entry | **APPROVED PRESENTATION REFERENCE** | **INTERNAL ENTRY REFERENCE.** Recovered ZIP folder `CUSTOMER-FACING - FINAL BUILD ONLY` is **provenance only** and does **not** override the document’s own designation. **Not** a customer deliverable. | N/A |
| 05 Ontario Construction Contract COMMERCIAL_DRAFT | **APPROVED PRESENTATION REFERENCE** | Customer-facing folder (provenance); **not** a production contract | **COMMERCIAL_DRAFT / NOT APPROVED**. Legal Content Gate **empty**. Not for signature. Not Native Signing. |
| 06 Door Window Skylight Schedule FINAL | **APPROVED PRESENTATION REFERENCE** | Customer-facing | N/A |
| 07 Client Construction Proposal | **APPROVED PRESENTATION REFERENCE** | Customer-facing | N/A |

Source quotes: **PROJECT SOURCE MATERIAL**. Do not promote into the presentation family.

## Presentation family (forensic)

Verified 2026-09-03, read-only, original ZIP unmodified:

- Creator: `python-docx`; saved in Microsoft Macintosh Word (`Normal.dotm`)
- Letter 8.5×11 in; margins top/bottom 0.55 in, left/right 0.65 in; header/footer 0.5 in
- Shared `word/styles.xml` SHA-256: `760005ab7de5676d3d702b2484b60c7960b2b09be48eb0e7a2756ddea328973e` (all seven DOCX)
- Shared header PNG SHA-256: `0949c20891bb38a651403ca4e1965b3938a471bb68ec82773df80f3d5c50d4d2` — PNG 2048×819, 92001 bytes, gold house-gable mark on black (wide letterhead crop)
- Header/footer **structure** shared (logo + company line + document-specific label); **XML bytes** differ per document because labels/footers carry project and document titles
- Body titles are ALL-CAPS document names; identity block Client / Project / Site / Date; tables for commercial lines
- Body fonts in styles: Aptos (and Courier / theme majors)

These files are **not** reusable templates until a later governed extraction removes Allen Jacques / address / prices / quantities / dates / scope.

## Custody (do not invent)

Repository binary policy for customer/project bytes is already [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md): **bytes outside Git**; **SHA-256 identity in Git**. Plan PDFs, brand logos, and Field originals use gitignored `instance/` stores — **wrong custody** for this presentation baseline (those roots are product runtime, not a document-design register). Do **not** commit DOCX/PDF/ZIP binaries to Git.

**Custody status: CLOSED** (verified 2026-09-04). The approved source bytes no longer depend solely on Desktop.

| Layer | Location |
|-------|----------|
| **Immutable source ZIP (durable byte store)** | `/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/Allen Jacques Presentation Baseline - 2026-09-03/Allen_Jacques_Garage_FINAL_116778_Internal_and_Customer_2026-08-31.zip` |
| ChatGPT Library logical collection (established 2026-09-04) | `/CalibAi/Approved Document Templates/Allen Jacques Presentation Baseline - 2026-09-03/` — collection name only; **not** a Cursor-writable filesystem. Governed bytes are the Documents store above. |
| Recovered Desktop provenance copy | `/Users/joelbrayman/Desktop/Allen_Jacques_Garage_FINAL_116778_Internal_and_Customer_2026-08-31.zip` — **leave in place**; do **not** delete; **not** sole custody |
| Identity | This pin + [manifest](../testing/allen-jacques-garage-presentation-baseline-manifest.md) in Git |
| UAT project pin | [testing/uat-reference-cases.md](../testing/uat-reference-cases.md) |

**Verification (2026-09-04):** source ZIP SHA-256 `26f5e579c01651f2e304a76fbed1de7ab54ba144055937c2a1fc6871ebe5e874` matched the governed hash. All **17** ZIP members matched the [manifest](../testing/allen-jacques-garage-presentation-baseline-manifest.md), including DOCX/PDF identities for families **01–07**. Durable copy SHA-256 matched. Original ZIP unmodified. No extraction. No redesign.

The durable store holds the **exact original ZIP** only. Do **not** treat extracted members, regenerated files, or project-neutral derivatives as the immutable source.

## FG-012 / FG-017

**FG-012** HTML/ReportLab renderers (`app/templates/estimates/internal_breakdown.html`, `app/templates/proposals/preview.html`, `app/services/proposal_pdf.py`) are **current product renderers**. They are **materially different** from this recovered Word/`python-docx` letterhead family. Do **not** claim they visually match. Do **not** substitute them for this baseline. Future CalibAi document-generation governance must reconcile product renderers with this approved presentation baseline.

**FG-017** governed static/logo SHA-256: `948f96e08827f18d77b47538f65c8b98b45caaf9c981adccba0189976948efe9` (80007 bytes). Recovered approved presentation raster: `0949c20891bb38a651403ca4e1965b3938a471bb68ec82773df80f3d5c50d4d2`. **Different bytes.** Do **not** silently replace either file. Do **not** resolve the Brand Profile raster question from this pin.

For reconstruction/reproduction of the approved presentation family, **the recovered presentation itself remains the reference**. A later separately governed branding decision may determine whether FG-017 should adopt or derive from that raster.

## Separate estimate-generation handoff (status)

The separate estimate-generation conversation may now use this recovered package as the **APPROVED PRESENTATION REFERENCE**, subject to:

- current estimate/workbook = **project-data authority**
- recovered Allen Jacques documents = **presentation authority**
- no Allen Jacques project-specific value may survive
- no redesign
- no generic FG-012 visual substitution
- Document 04 = **INTERNAL ENTRY REFERENCE** (not a customer deliverable)
- Document 05 legal content remains **COMMERCIAL_DRAFT / NOT APPROVED**
- source-quote PDFs are **not** templates
- reusable template extraction has **not** yet occurred ([FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **APPROVED / IMPLEMENTATION NOT STARTED**)

Do **not** generate that estimate from this pin.

## Future reusable-template extraction ([FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md))

[FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) is **APPROVED / IMPLEMENTATION NOT STARTED**. It authorizes a later extraction of reusable presentation source that **keeps** page geometry, typography, header/footer structure, table styling, spacing, section hierarchy, and visual identity, and **removes** Allen Jacques, site address, project numbers, prices, quantities, dates, project-specific scope/allowances/exclusions, and source-quote content.

Derived masters must live under a **separate** durable directory (`Reusable Master Template Family V1/`), not in this immutable-source directory. Identity register: [testing/reusable-approved-document-template-family-v1-register.md](../testing/reusable-approved-document-template-family-v1-register.md) (**empty** until extraction).

This pin does **not** perform extraction. Do **not** extract without a separate implementation prompt.

## Related

- [testing/allen-jacques-garage-presentation-baseline-manifest.md](../testing/allen-jacques-garage-presentation-baseline-manifest.md)
- [testing/reusable-approved-document-template-family-v1-register.md](../testing/reusable-approved-document-template-family-v1-register.md)
- [feature-gates/FG-022-reusable-approved-document-template-family-v1.md](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md)
- [testing/uat-reference-cases.md](../testing/uat-reference-cases.md)
- [project-document-package.md](project-document-package.md)
- [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md)

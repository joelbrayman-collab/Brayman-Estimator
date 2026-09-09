# Product Identity — CalibraytAI

| Attribute | Value |
|-----------|--------|
| Status | **GOVERNING** |
| Updated | 2026-09-09 |
| Authority | [ADR-045](../adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted** · [FG-028](../feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) |
| Does not amend | [platform-constitution.md](../platform-constitution.md) Articles 1–12 |

This is the authoritative **current vs former product-name** record. It does **not** rename the repository, office chrome, or tenant Brand Profile.

---

## Canonical names

| Role | Name | Rule |
|------|------|------|
| **CURRENT PRODUCT** | **CalibraytAI** | Permanent selected product name. Canonical spelling: `CalibraytAI`. |
| **FORMER PRODUCT NAME** | **CalibAi** | Name used before this governed product-identity transition. |
| Repository / working title | The Estimator / Brayman-Estimator | **PRESERVE.** Separate from product identity. |
| Office chrome | Brayman Construction Platform | **PRESERVE** under [FG-028](../feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md). |
| Tenant ORG-001 | Brayman Construction Inc. / Brayman Construction / Organization Brand Profile | **PRESERVE.** Not the product. |

## Durable rule

CalibraytAI is the current product name.

CalibAi is the former product name used before the governed product-identity transition.

Historical references to CalibAi remain valid historical truth.

## Effective transition

| Field | Value |
|-------|--------|
| Decision | Joel selected CalibraytAI on 2026-09-08; implementation authorized 2026-09-09 |
| Feature Gate | [FG-028](../feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) |
| ADR | [ADR-045](../adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) |
| Product commit SHA | *Pinned after the Slices 1–2 commit.* |
| Schema / Alembic | **None.** Live current remains heads `a5b6c7d8e9f0`. |

## Historical rule

Do **not** rewrite chat-workflow-log entries, milestone records, closed Feature Gate / UAT evidence, dated ADR or CAR decision bodies, Alembic comments, frozen database provenance, or historical filesystem paths merely to insert CalibraytAI.

A later **Subsequent status** line may record current identity without altering the original adopted text.

## Technical identifier rule

Compatibility, provenance, and historically embedded identifiers may retain `CalibAi` / `calibai` / `CALIBAI`, including:

- Field IndexedDB / localStorage: `calibai-field-v1`, `calibai-field-last-project-id`, `calibai-field-project-id`
- Takeoff provider `calibai-mock`
- Actor token `CALIBAI-AI`
- Resolution-source token `CALIBAI_BASELINE` (user-facing copy remains “Platform baseline”)
- tempfile prefixes `calibai-brand-logos-`, `calibai-build-originals-`, `calibai-build-renditions-`
- ADR-019 and CAR-001 **filenames**
- Desktop corpus path `~/Desktop/CalibAi Historical Estimates`

## Tenant rule

Brayman Construction identity is separate. Do **not** replace `Brayman Construction`, `Brayman Construction Inc.`, or Organization Brand Profile fields with CalibraytAI.

## Office chrome rule

`Brayman Construction Platform` remains the office shell / login / sidebar product string under this gate. This transition does **not** retitle office chrome as CalibraytAI.

## Generated documents

| Surface | Rule |
|---------|------|
| Permit HTML/PDF **generator** | Current product title and live advisory constant: **CalibraytAI**. Tenant-neutral (no Brand Profile, no Brayman logo). |
| Stored `permit_findings.advisory_language` | **Frozen.** Do not UPDATE for branding. |
| Proposal / Change Order | Tenant / Brand Profile / `Brayman Construction Platform` **unchanged**. |

## Visual asset (Slice 3 — held)

Joel will supply an approved CalibraytAI lettering asset. Design retained: same emblem, colours, layout; **only** lettering CalibAi → CalibraytAI.

Until that asset is installed, Field **text** is CalibraytAI while the header/favicon may continue to use `app/static/branding/brayman-construction-logo.png`. That is a **temporary known identity/asset conflation**, not a Brand Profile change.

## Website

**WEBSITE PRODUCT-IDENTITY TRANSITION: EXTERNAL / PENDING SEPARATE JOEL-CHATGPT PASS.**

Marketing website source is outside this repository. This document does **not** authorize website implementation, publish, or deploy.

## Related

- [platform-vision.md](../platform-vision.md)
- [platform-constitution.md](../platform-constitution.md)
- [v1-completion-register.md](../v1-completion-register.md)

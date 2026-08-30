# Permit Rules Library — Ontario / Ottawa coach-house source inventory (FG-016)

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTED** in repository seed / **LIVE MIGRATION PENDING** |
| Date | 2026-08-30 |
| Coverage | Ontario / City of Ottawa / Additional dwelling/coach house / North Gower reference |
| Canonical seed | `app/models/permit_intelligence.py` (`PERMIT_RULE_SEED`) |
| Migration | `f8a9b0c1d2e3` (graph head; **not** applied to live development/UAT) |
| Reviewer | `FG-016-GOVERNANCE-SEED` (deterministic development/governance review; **not** AI approval) |
| Effective from | 2026-03-11 (City of Ottawa dual-compliance date for applications deemed complete on or after that day) |

This inventory is the durable answer to: **what source, what authority, what effective date, what rule record, who reviewed it, and why it applies to this coverage.**

Research-time official PDFs and City pages were used to **create** these governed records. Product runtime does **not** fetch the web.

Secondary sources (blogs, contractor sites, 2017 “How to plan your COACH HOUSE IN OTTAWA” PDF citing obsolete s.142) are **not** governing.

---

## Dual-compliance note (applies to numeric zoning checks)

City of Ottawa: building-permit applications deemed complete on **11 March 2026** or after must comply with **both** Zoning By-law **2008-250** and Zoning By-law **2026-50**, applying the **most restrictive** provisions.

Parcel zone, transect, and Area D membership are **not** proven by the North Gower alias. Numeric footprint / height / setback checks therefore **VERIFY** unless a conservative ceiling is clearly exceeded.

---

## Operational APPROVED rules

| Code | Category | Authority | Official source | Effective from | Record | Reviewed by | Why this coverage |
|------|----------|-----------|-----------------|----------------|--------|-------------|-------------------|
| OTT-CH-001 | permit_application_completeness | City of Ottawa Building Code Services | [Adding a coach house — Do I need a building permit?](https://ottawa.ca/en/planning-development-and-construction/building-and-renovating/do-i-need-building-permit/adding-coach-house-additional-dwelling-units-accessory-structure) | 2026-03-11 | `permit_rules` code `OTT-CH-001` v1 | FG-016-GOVERNANCE-SEED | Coach house always requires a building permit in Ottawa. |
| OTT-CH-002 | coach_house_applicability | City of Ottawa | [Zoning By-law 2008-250 s.133(2)](https://documents.ottawa.ca/sites/default/files/zoning_bylaw_part5_section133_en.pdf); By-law 2026-50 s.701 | 2026-03-11 | `OTT-CH-002` v1 | FG-016-GOVERNANCE-SEED | Same-lot requirement is in both cited instruments. |
| OTT-CH-003 | permitted_use_prerequisites | City of Ottawa | [New Zoning By-law 2026-50](https://ottawa.ca/en/planning-development-and-construction/maps-and-zoning/new-zoning-law-2026-50) | 2026-03-11 | `OTT-CH-003` v1 | FG-016-GOVERNANCE-SEED | Dual-compliance always requires AHJ confirmation of the governing numeric standard. |
| OTT-CH-004 | private_servicing | City of Ottawa | 2008-250 s.133(3)(c)–(d) PDF above | 2026-03-11 | `OTT-CH-004` v1 | FG-016-GOVERNANCE-SEED | Private-service unit cap and Area D 0.4 ha test; Area D is not assumed from North Gower. |
| OTT-CH-005 | footprint_maximum_area | City of Ottawa | 2008-250 s.133(10); 2026-50 s.701 size | 2026-03-11 | `OTT-CH-005` v1 | FG-016-GOVERNANCE-SEED | 95 m² is the cited Area D / AG-RU ceiling. Over 95 m² is potential non-conformance; otherwise VERIFY. |
| OTT-CH-006 | building_height | City of Ottawa | 2008-250 s.133(8); 2026-50 s.701 height | 2026-03-11 | `OTT-CH-006` v1 | FG-016-GOVERNANCE-SEED | 6.1 m garage exception is the conservative ceiling. Over 6.1 m is potential non-conformance; otherwise VERIFY. |
| OTT-CH-007 | setbacks | City of Ottawa | 2008-250 s.133(9); 2026-50 s.701 setbacks | 2026-03-11 | `OTT-CH-007` v1 | FG-016-GOVERNANCE-SEED | Below 0.6 m is potential non-conformance; otherwise VERIFY. Lot-line identity is not invented. |
| OTT-CH-008 | private_servicing_septic_review | City of Ottawa / RVCA Ottawa Septic System Office | [Septic systems — Do I need a building permit?](https://ottawa.ca/en/planning-development-and-construction/building-and-renovating/do-i-need-building-permit/septic-systems) | 2026-03-11 | `OTT-CH-008` v1 | FG-016-GOVERNANCE-SEED | OSSO/RVCA review anywhere in Ottawa for septic works; not assumed from North Gower without servicing facts. |
| OTT-CH-009 | rural_grading | City of Ottawa | [Preparing your plans — Grading Plan](https://ottawa.ca/en/planning-development-and-construction/building-and-renovating/planning-your-project/preparing-your-plans) | 2026-03-11 | `OTT-CH-009` v1 | FG-016-GOVERNANCE-SEED | Accessory > 55 m² or within 1.2 m of a property line requires a grading plan. |
| OTT-CH-010 | site_plan_submission | City of Ottawa | [ADU submissions — Part 9 residential](https://ottawa.ca/en/planning-development-and-construction/building-and-renovating/planning-your-project/building-permit-application-submission-requirements-part-9-residential/additional-dwelling-unit-adu-submissions) | 2026-03-11 | `OTT-CH-010` v1 | FG-016-GOVERNANCE-SEED | Bounded site-plan completeness against reviewed evidence only. |

---

## What was not populated

Not every FG-016 candidate family was seeded. Driveway/access as a standalone zoning rule, comprehensive OBC structural/fire/energy review, and GIS zone lookup were left out because official support was either incomplete for deterministic evaluation or belongs to full Building Code Intelligence.

---

## Related

- [permit-rules-library.md](permit-rules-library.md)
- [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md)
- [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)

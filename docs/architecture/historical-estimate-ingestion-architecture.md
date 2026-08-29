# Historical Estimate Ingestion Architecture & Source Audit (Phase A)

| Attribute | Value |
|---|---|
| Document Type | Architectural Research & Ingestion Design Specification |
| Milestone / Program | Historical Estimate Ingestion — Phase A (Source Audit & Architecture) |
| Authoritative Context | `platform-constitution.md`, `architecture-principles.md`, `pricing-policy.md`, `ADR-024`, `ADR-025` |
| Status | **PHASE A COMPLETE · PHASE B IMPLEMENTED & VERIFIED** (FG-006; migration `e1b2c3d4e5f6`; 170 total tests passed, 11 dedicated historical ingestion tests) |
| Date | 2026-08-28 |

---

## 1. Executive Summary & Audit Baseline

A read-only forensic audit was conducted on the 20 historical Brayman estimating workbooks located in the external source collection directory (`~/Desktop/CalibAi Historical Estimates`).

### Key Findings:
1. **Total Source Count:** 20 workbooks (16 `.xlsm` macro-enabled OpenXML workbooks, 4 `.xlsx` standard OpenXML workbooks).
2. **Source Integrity:** All 20 files are 100% valid, uncorrupted OpenXML zip archives. SHA-256 hashes have been calculated and sealed in `docs/architecture/historical-estimates-source-manifest.md`.
3. **Template Families:** The 20 workbooks fall into **5 distinct template families** (detailed in Section 3).
4. **Prevalent Commercial Lineage:** 16 of the 20 workbooks (`.xlsm`) share a common heritage: they are built upon an older commercial template containing 10 hidden legacy financial sheets (`Data Input Smart City`, `Battery Cost`, `Debt P&I`, etc.) with over 7,000 broken formula cells (`#REF!`) in the hidden layers. However, the visible Brayman estimating sheets (`COST DATA`, `House TES`, `Worksheet FOUNDATION`, `Worksheet GARAGE SLAB`, `Esiimate`, `ICF Contract`) are active, self-contained, and mathematically functional.
5. **Pricing Methodology Discovery:**
   - **Markup vs Gross Margin:** Historical Brayman workbooks uniformly calculate "Margin" using **Cost-Plus Markup** (`Margin = Direct Cost * 0.15`, `Selling Price = Direct Cost + Margin`), **not** true gross margin (`Selling Price = Direct Cost / (1 - Margin)`).
   - **Margin Rates:** Range from 10.0% to 15.0% across different jobs (15% on slabs/renos, 10%–12.5% on large ICF packages).
   - **Labour Rates:** Historically ranged from $50.00/hr (older/sub-tier), $60.00/hr, $62.50/hr, to $65.00/hr.
6. **Data Quality & Contradiction Risk:** As evidenced in the Allen Jacques workbook (`HIST-EST-0002`), customer-facing presentation sheets (`Esiimate`, `ICF Contract`) frequently contain stale copy-paste residue from previous projects (e.g., date headers or estimate codes referencing older clients like "Gorman" or "BROWN Storage") while the calculation sheet contains project-specific quantities.

---

## 2. Workbook Structure & Content Profiling

### Structural Statistics Across the 20 Workbooks

| Template Family | Workbook Count | Format | Sheet Count (Vis / Total) | Approx Cells / File | Formulas / File | Merged Cells / File |
|---|---|---|---|---|---|---|
| **Family A: Slab-on-Grade / TES** | 9 | .xlsm | 3 visible / 14 total | 56,800 | 7,160 | ~96 |
| **Family B: Standard ICF Foundation** | 5 | .xlsm | 5 visible / 16 total | 59,100 | 7,320 | ~104 |
| **Family C: Extended Multi-Trade ICF** | 1 | .xlsm | 11 visible / 22 total | 61,421 | 7,447 | 170 |
| **Family D: Comprehensive Build Package** | 1 | .xlsm | 6 visible / 17 total | 58,643 | 7,531 | 89 |
| **Family E: Ad-hoc / Standalone Flat Sheet** | 4 | .xlsx | 1 to 2 visible / 1 to 2 total | 40 to 337 | 5 to 122 | 0 |
| **TOTAL POPULATION** | **20** | **16 .xlsm / 4 .xlsx** | — | — | — | — |

### Content Pattern Breakdown

| Category | Typical Sheet Name(s) | Structure & Content Evidence | Extraction Confidence |
|---|---|---|---|
| **Project Identity** | `COST DATA`, `House TES`, `Worksheet FOUNDATION`, `Sheet1` | Client name, site address, email, phone, project name. Formatted in fixed cell coordinates (e.g., `COST DATA!C2:C11`). | **High** (with residue cross-check) |
| **Rate & Margin Config** | `COST DATA`, `Sheet1` | Global parameters: Labour Rate ($60-$65), Margin % (10%-15%), HST (13%). Fixed cells `COST DATA!C10:C17`. | **High** |
| **Materials Catalogue** | `COST DATA` (top rows 15–50) | Item description, unit cost per unit (e.g., 2x4x10, Rebar, Concrete 20/25/32 MPA, Logix blocks). | **High** |
| **Takeoff & Quantities** | `House TES`, `Worksheet FOUNDATION`, `Worksheet GARAGE SLAB` | Parametric dimension inputs (Length, Width, Height/Depth) driving calculated material counts and labour hours. | **High** |
| **Labour Activities** | `House TES`, `Worksheet FOUNDATION`, `BC Internal Work` | Crew tasks (Forming, Pouring, Finishing, Stripping) with Crew Size (People), Duration (Days), calculated Hours (`People * Days * 8`), and Extended Labour Cost. | **High** |
| **Subcontractors** | `SUB-TRADES`, `Worksheet FOUNDATION` | Direct trade quotes (Plumbing, Electrical, Drywall, HVAC, Stairs, Windows). | **Medium-High** |
| **Allowances / Placeholders** | `SUB-TRADES`, `Foundation` | Rounded lump sums, unconfirmed supplier numbers. | **Medium** |
| **Commercial Totals** | `House TES`, `Worksheet FOUNDATION`, `SUMMARY`, `Esiimate` | Direct cost subtotal, markup addition, selling price before tax, HST (13%), total invoice amount. | **High** |
| **Actual Performance** | `Alberton Garage Cost`, `Serge copy` | Actual hours/costs vs estimate (very rare in standard templates; most files represent pre-contract estimates). | **Low prevalence** (requires explicit detection) |

---

## 3. Template Family Analysis

```
                       ┌──────────────────────────────────────────────┐
                       │   Historical Brayman Workbook Population     │
                       │               (20 Workbooks)                 │
                       └──────────────────────┬───────────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         │                                    │                                    │
┌────────┴─────────┐                 ┌────────┴─────────┐                 ┌────────┴─────────┐
│ Family A: SLAB   │                 │ Family B: ICF    │                 │ Family E: Ad-Hoc │
│ (9 workbooks)    │                 │ (5 workbooks)    │                 │ (4 workbooks)    │
│ - COST DATA      │                 │ - COST DATA      │                 │ - Simple sheets  │
│ - House TES /    │                 │ - Worksheet FDN  │                 │ - Direct line    │
│   Worksheet SLAB │                 │ - ICF Estimate   │                 │   calculations   │
│ - Esiimate       │                 │ - ICF Contract   │                 │ - Fast/custom    │
└──────────────────┘                 │ - Estimate D&W   │                 └──────────────────┘
                                     └────────┬─────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                             │
              ┌────────┴─────────┐                          ┌────────┴─────────┐
              │ Family C: Ext ICF│                          │ Family D: Build  │
              │ (1 workbook)     │                          │ (1 workbook)     │
              │ - Steele Manotick│                          │ - Mike Pratt     │
              │ - Sub-floor Calcs│                          │ - Multi-trade    │
              │ - Invoices 1 & 2 │                          │ - SUMMARY master │
              └──────────────────┘                          └──────────────────┘
```

### Family Profiles:
1. **Family A (Slab-on-Grade / Thickened Edge Slab) — 9 Workbooks:**
   - **Workbooks:** `HIST-EST-0002` (Allen Jacques), `HIST-EST-0004` (Bradley Construction), `HIST-EST-0005` (Brian Alberton), `HIST-EST-0009` (GATE Pads Kingston), `HIST-EST-0010` (Gerry Cardinal), `HIST-EST-0012` (Lamb Thickened Edge Slab), `HIST-EST-0015` (NG Slab Repair), `HIST-EST-0016` (Patrick Pearce), `HIST-EST-0017` (Richard Gorman).
   - **Structure:** 3 visible sheets (`COST DATA`, `House TES` or `Worksheet GARAGE SLAB` / `Worksheet Slab`, `Esiimate` / `Invoice SLABS`).
   - **Calculation Pattern:** Single continuous table combining material formulas, pump rental, and crew labour hours, rolled into Sub-Total, Markup, and Total.
   - **Extraction Difficulty:** **Low-Medium** (highly standardized layout).

2. **Family B (Standard ICF Foundation) — 5 Workbooks:**
   - **Workbooks:** `HIST-EST-0003` (Bob Milne), `HIST-EST-0007` (Chris Graham), `HIST-EST-0011` (Jacob Brown), `HIST-EST-0018` (Ryan Dunwoodie), `HIST-EST-0019` (Sasha - ICF).
   - **Structure:** 5 visible sheets (`COST DATA`, `Worksheet FOUNDATION`, `ICF Estimate`, `ICF Contract`, `Estimate D&W`).
   - **Calculation Pattern:** Multi-stage breakdown on `Worksheet FOUNDATION` (Footings, ICF Walls, Basement Floor, Garage Slab, Veranda), each with its own material and labour subtotal and margin.
   - **Extraction Difficulty:** **Medium** (stage-by-stage rollup).

3. **Family C (Extended Multi-Trade ICF) — 1 Workbook:**
   - **Workbooks:** `HIST-EST-0013` (Michelle Steele Manotick ICF V2).
   - **Structure:** 11 visible sheets (`COST DATA`, `Worksheet FOUNDATION`, `Sub-floor Calcs`, `ICF Estimate`, `ICF Contract`, `Sub-Floor INVOICE#1/#2`, `Invoice #1 Roof Truss`, `Estimate Roof Truss 2`, `Estimate Floor Joists-Trusses`, `Estimate D&W`).
   - **Calculation Pattern:** Foundation + Framing + Trusses + Windows across discrete trade sheets.
   - **Extraction Difficulty:** **High** (multi-sheet cross-references).

4. **Family D (Comprehensive Build Package) — 1 Workbook:**
   - **Workbooks:** `HIST-EST-0014` (Mike Pratt FULL ICF 2 V2).
   - **Structure:** 6 visible sheets (`SUMMARY`, `Cost Data`, `Foundation`, `BC Internal Work`, `SUB-TRADES`, `ICF Contract`).
   - **Calculation Pattern:** Master `SUMMARY` rollup sheet referencing dedicated division sheets (`Foundation`, `BC Internal Work` framing/finishing, and `SUB-TRADES` MEP/drywall/cabinetry).
   - **Extraction Difficulty:** **High** (complex inter-sheet dependencies).

5. **Family E (Ad-Hoc / Standalone Flat Sheets) — 4 Workbooks:**
   - **Workbooks:** `HIST-EST-0001` (Alberton Garage Cost), `HIST-EST-0006` (Brown Floor Replacement), `HIST-EST-0008` (Copy of Julia Harish RENO), `HIST-EST-0020` (Serge copy).
   - **Structure:** 1 or 2 visible sheets (`Sheet1`, `Sheet2`). All 4 are standard `.xlsx` files without legacy hidden sheet residue.
   - **Calculation Pattern:** Flat tabular lists of materials and labour hours with bottom-line markup calculation.
   - **Extraction Difficulty:** **Low** (flat structure, but varies per workbook).

*Family Sum Verification:* $9 + 5 + 1 + 1 + 4 = 20$ workbooks.

---

## 4. Pricing-Method Detection & Governing Policy Gap

### Historical Reality vs Governing Policy

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                PRICING FORMULA DISCOVERY                               │
├───────────────────────────────────────────┬────────────────────────────────────────────┤
│ Historical Brayman Workbooks (Audited)    │ Governed CalibAi Policy (pricing-policy.md)│
├───────────────────────────────────────────┼────────────────────────────────────────────┤
│ Formula: COST-PLUS MARKUP                 │ Formula: TRUE GROSS MARGIN                 │
│                                           │                                            │
│ Margin Amount = Direct Cost * 0.15        │ Gross Margin = 15%                         │
│ Selling Price = Direct Cost + Margin      │ Selling Price = Direct Cost / (1 - 0.15)   │
│ Selling Price = Direct Cost * 1.15        │ Selling Price = Direct Cost / 0.85         │
│                                           │ Selling Price = Direct Cost * 1.17647      │
│ Effective Margin on Revenue = 13.04%      │ Effective Margin on Revenue = 15.00%       │
└───────────────────────────────────────────┴────────────────────────────────────────────┘
```

### Pricing Method Classification Rules for Ingestion
Every ingested historical estimate must record its explicit pricing mathematical rule:
- `MARKUP_SIMPLE`: `Selling Price = Direct Cost * (1 + markup_pct)` (Found in 100% of audited workbooks where margin is parameterized).
- `TRUE_GROSS_MARGIN`: `Selling Price = Direct Cost / (1 - margin_pct)` (Governing Brayman policy in `pricing-policy.md`; not found in historical sheets).
- `CATEGORY_TIERED_MARKUP`: Different markups applied per division (e.g., Materials @ 15%, Subcontractors @ 10%).
- `FIXED_LUMP_SUM_OVERRIDE`: Selling price entered manually with no formula.

---

## 5. Cell-Level Provenance & Lineage Model

To maintain strict construction-grade auditability, no historical figure may be stored as an unanchored scalar. Every extracted commercial fact must retain its complete source path:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         CELL-LEVEL PROVENANCE TRACE                              │
├──────────────────────┬───────────────────────────────────────────────────────────┤
│ Source Workbook ID   │ HIST-EST-0002                                             │
│ Source File Name     │ Allen Jacques - TES copy.xlsm                             │
│ Source SHA-256       │ e20bf7aa7288d4f126636599bb558918220ed3dfdb036db26966dfa... │
│ Sheet Name           │ House TES                                                 │
│ Cell Coordinate      │ H45                                                       │
│ Raw Formula          │ =SUM(H14:H44)                                             │
│ Evaluated Value      │ 30976.00                                                  │
│ Extraction Rule      │ rule_slab_direct_cost_subtotal_v1                         │
│ Normalized Target    │ estimate_totals.direct_cost_subtotal                      │
│ Extraction Timestamp │ 2026-08-28T13:45:00Z                                      │
└──────────────────────┴───────────────────────────────────────────────────────────┘
```

---

## 6. Data Quality & Contradiction Model

The ingestion architecture implements a strict **Evidence & Observation** pattern rather than guessing or silently correcting inconsistencies.

### Governed Data Quality Flags:
1. `CONSISTENT`: Extracted value matches cross-sheet references and mathematical sum.
2. `POSSIBLE_TEMPLATE_RESIDUE`: Presentation header/client text differs from calculation sheet parameters (e.g., `Esiimate!F2` says `BC(EST)Gorman` but `COST DATA!C3` says `Allen Jacques`).
3. `CONTRADICTORY`: Calculation sheet total does not equal customer estimate sheet total.
4. `FORMULA_ERROR`: Cell contains `#REF!`, `#VALUE!`, `#DIV/0!`, etc.
5. `BROKEN_EXTERNAL_LINK`: Cell references an external workbook path not accessible.
6. `MANUAL_OVERRIDE`: Cell contains hard-coded numeric constant where a formula was expected by template standard.
7. `MISSING`: Expected field in template family is blank or unpopulated.
8. `REVIEW_REQUIRED`: Discrepancy threshold exceeded; human estimator must decide authoritative value.

---

## 7. Historical Evidence Hierarchy & Organization-Neutral Terminology

Per `ADR-024` and `platform-vision.md`, historical estimates are **commercial evidence**, not automatic pricing truth. Furthermore, the engine operates on **organization-neutral source classifications**:

```
                    ┌─────────────────────────────────────────────────┐
                    │    HISTORICAL PRICING EVIDENCE HIERARCHY        │
                    │               (Highest to Lowest)               │
                    └────────────────────────┬────────────────────────┘
                                             │
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      │                                      │                                      │
┌─────┴────────────────────────┐ ┌───────────┴────────────────┐ ┌───────────────────┴─────┐
│ 1. ORG-ACTUAL                │ │ 2. ORG-APPROVED            │ │ 3. ORG-HISTORICAL       │
│ - Invoiced actual costs      │ │ - Calibrated company rate  │ │ - Contracted / Quoted   │
│ - Actual labour hours log    │ │ - Review-approved for use  │ │   historical estimate   │
│ - Actual supplier invoices   │ │ - Organization-owned       │ │ - Evidence, not truth   │
└──────────────────────────────┘ └────────────────────────────┘ └─────────────────────────┘
                                             │
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      │                                      │                                      │
┌─────┴────────────────────────┐ ┌───────────┴────────────────┐ ┌───────────────────┴─────┐
│ 4. CURRENT QUOTE             │ │ 5. BASELINE / BENCHMARK    │ │ 6. PROVISIONAL / MANUAL │
│ - Current supplier quote     │ │ - Published industry rate  │ │ - Research baseline     │
│ - Active sub bid             │ │ - Manufacturer guidance    │ │ - User override+reason  │
└──────────────────────────────┘ └────────────────────────────┘ └─────────────────────────┘
```

---

## 8. Organization-Neutral Lineage & Canonical Schema (Design Only — No Implementation)

### Governing Architectural Principle:
> **CALIBAI OWNS THE ENGINE AND METHODOLOGY.**  
> **EACH CUSTOMER ORGANIZATION OWNS ITS COMMERCIAL INTELLIGENCE.**

Brayman Construction is the first development and UAT organization. Brayman's historical workbook folder is UAT evidence for `Organization: Brayman Construction Inc.`. It must **not** define universal CalibAi defaults.

### Canonical Ingestion & Calibration Lineage:
$$\text{Organization} \longrightarrow \text{Source Workbook} \longrightarrow \text{Historical Estimate} \longrightarrow \text{Estimate Version} \longrightarrow \text{Source Observation} \longrightarrow \text{Normalized Commercial Data} \longrightarrow \text{Evidence Class} \longrightarrow \text{Calibration Candidate} \longrightarrow \text{Review Decision} \longrightarrow \text{Organization Calibration Model}$$

### Canonical Relational Model:
The normalized relational model separates **immutable raw source observations** from **curated estimate entities**, with strict **Organization ownership** on every commercial entity:

```
                       ┌────────────────────────────────┐
                       │          Organization          │
                       │ ------------------------------ │
                       │ organization_id (PK)           │
                       │ legal_name, display_name       │
                       │ default_pricing_policy         │
                       └───────────────┬────────────────┘
                                       │ 1:N
                       ┌───────────────┴────────────────┐
                       │      SourceWorkbookManifest    │
                       │ ------------------------------ │
                       │ source_id (PK: HIST-EST-0001)  │
                       │ organization_id (FK)           │
                       │ filename, sha256_hash, size    │
                       │ template_family, source_tier   │
                       └───────────────┬────────────────┘
                                       │ 1:N
                       ┌───────────────┴────────────────┐
                       │     SourceCellObservation      │
                       │ ------------------------------ │
                       │ id, source_id (FK), sheet_name │
                       │ cell_ref, raw_formula          │
                       │ evaluated_val, data_type       │
                       │ data_quality_flag, notes       │
                       └───────────────┬────────────────┘
                                       │ 1:1 Lineage
                       ┌───────────────┴────────────────┐
                       │     NormalizedHistoricalEst    │
                       │ ------------------------------ │
                       │ id, organization_id (FK)       │
                       │ source_id (FK), project_name   │
                       │ client_name, estimate_date     │
                       │ status_tier, pricing_method    │
                       │ margin_rate, direct_cost       │
                       │ sell_price, hst, total_price   │
                       └───────┬──────────────┬─────────┘
                               │ 1:N          │ 1:N
        ┌──────────────────────┴──────┐      ┌┴─────────────────────────┐
        │   HistoricalCostLineItem    │      │   HistoricalLabourItem   │
        │ --------------------------- │      │ ------------------------ │
        │ id, estimate_id (FK)        │      │ id, estimate_id (FK)     │
        │ division, cost_category     │      │ task_name, crew_size     │
        │ item_description, qty, unit │      │ duration_days, hours     │
        │ unit_cost, extended_cost    │      │ base_rate, extended_cost │
        │ provenance_obs_id (FK)      │      │ provenance_obs_id (FK)   │
        └─────────────────────────────┘      └──────────────────────────┘
```

---

## 9. Security & Protected Repository Boundary

### Governed Security Invariants:
1. **Raw Workbooks Remain External:** Raw customer workbooks located in `~/Desktop/CalibAi Historical Estimates` must **never** be copied into or committed to the Git repository.
2. **Git Contents Restricted to Metadata:** The Git repository may contain:
   - Schema designs and architectural specifications.
   - Source provenance manifests (filenames, hashes, metadata).
   - Anonymized, controlled unit-test fixtures.
   - Ingestion algorithm code.
3. **Future Production Storage Boundary:** When Phase B implements database persistence, ingested historical estimates must reside in protected database tables subject to strict workspace and tenant isolation, with role-based access control prohibiting unauthorized export of customer pricing history.
4. **Cross-Organization Benchmarking:** Not authorized. CalibAi may not pool customer data across organizations without explicit governance, legal review, and customer authorization.

---

## 10. Pilot Extraction Results

Five representative workbooks were extracted read-only during the Phase A audit:

| Source ID | Workbook Filename | Client / Project Identified | Direct Cost | Pricing Method | Margin Applied | Selling Price | HST | Total Commercial Amount | Provenance Anchor |
|---|---|---|---|---|---|---|---|---|---|
| `HIST-EST-0002` | Allen Jacques - TES copy.xlsm | Allen Jacques / 3415 Roger Stevens | $30,976.00 | Cost-Plus Markup | 15.0% ($4,646.40) | $35,622.40 | $4,630.91 | $40,253.31 | `House TES!H45:H49` |
| `HIST-EST-0003` | Bob Milne copy.xlsm | Bob Milne / 1082 Boucher Cres | $124,520.08 | Cost-Plus Markup (Multi-stage) | 12.0% ($16,187.61) | $140,707.69 | $18,291.99 | $158,999.68 | `Worksheet FOUNDATION!I147:I149` |
| `HIST-EST-0008` | Copy of Julia Harish RENO.xlsx | Julia Harish / Reno | $85,152.40 | Cost-Plus Markup | 15.0% ($12,772.86) | $97,925.26 | $12,730.28 | $110,655.54 | `Sheet1!C58:C63` |
| `HIST-EST-0014` | Mike Pratt FULL ICF 2 V2 copy 2.xlsm | Mike Pratt / 2562 Church St | $534,436.10 (Direct Scopes) | Category Tiered Markup | 12.5% GC Work ($60,492.01) + 5% Contingency ($25,896.80) | $620,824.91 | $80,707.24 | $701,532.15 | `SUMMARY!C10:C37` |
| `HIST-EST-0001` | Alberton Garage Cost copy.xlsx | Alberton Garage | $33,146.74 | Cost-Plus Markup | 15.0% ($4,972.01) | $38,118.75 | $4,955.44 | $43,074.19 | `Sheet1!G11:I11` |

*Extraction Verification & Reconciliation Note:*
- `HIST-EST-0008` (Julia Harish): Direct Cost is $85,152.40 (`Sheet1!C58`), 15% Margin is $12,772.86 (`Sheet1!C59`), and 5% Contingency is $4,257.62 (`Sheet1!C60`). The pre-tax selling price is $97,925.26 (`C58 + C59`), HST 13% is $12,730.28, and Total is $110,655.54. Contingency ($4,257.62) is retained as an internal reserve (`CONTINGENCY_NOT_INCLUDED_IN_SELL_PRICE`) and does not roll into the customer selling price.
- `HIST-EST-0014` (Mike Pratt): In Phase A pilot notes, this was recorded as $547,405.80 direct cost / $73,419.11 markup under an unverified manual audit interpretation. In Phase B deterministic ingestion, the exact cell formulas on the `SUMMARY` sheet govern:
  * Trade scope lines (`SUMMARY!C10:C34`): $534,436.10 (`direct_cost_total`)
  * GC Work / Markup at 12.5% (`SUMMARY!C35` = `SUM(C9:C32)*B35`): $60,492.01 (`markup_total`)
  * Change Order / Contingency at 5.0% (`SUMMARY!C36` = `SUM(C10:C33)*B36`): $25,896.80 (`contingency_total`, included in pre-tax selling price via `SUMMARY!C37`)
  * Selling Price Before Tax (`SUMMARY!C37` = `SUM(C10:C36)`): $620,824.91 (`selling_price_before_tax`)
  * HST 13%: $80,707.24 (`tax_amount`)
  * Grand Total: $701,532.15 (`total_price`)
All commercial layers are stored with distinct source-cell provenance, guaranteeing that contingency is not conflated with markup. Phase A's $547,405.80 / $73,419.11 values are documented as manual / unresolved historical audit figures superseded by deterministic OpenXML extraction.

---

## 11. Phase B Prerequisite & Implementation Status

### Historical Blocking Condition & Satisfaction:
The prerequisite conditions for `FG-006 — Historical Estimate Ingestion Engine (Phase B — Deterministic Ingestion & Database Persistence)` were **SATISFIED** upon completion and verification of **Milestone 011 / FG-007 (Organization Foundation & Project Commercial Context)** under ADR-028:
1. Canonical `Organization` entity and multi-tenant data ownership rules were implemented and verified.
2. Tenant isolation requirements were defined and enforced via `get_current_organization_id()`.
3. Calibration-model ownership boundaries were established.
4. Rate-resolution hierarchy and commercial context provenance were formalized.

### Phase B Implementation:
Following satisfaction of prerequisites, **FG-006 Phase B was implemented, verified, committed, and pushed** on `main` at `690d755d9901e04eb783198f4b89071fbeaf472a`:
- Additive database migration: `e1b2c3d4e5f6`
- 20 / 20 historical workbooks ingested into `ORG-001` with 20/20 exact SHA-256 integrity verification
- Pure Python OpenXML reader executing zero macros
- Template Families A–E classified and normalized with cell-level provenance
- Full test baseline: 170 passed (11 dedicated historical ingestion tests)
- Subsequent systems: Labour Engine Phase B **IMPLEMENTED / VERIFIED / LIVE-MIGRATED** ([FG-008](../feature-gates/FG-008-labour-engine-phase-b.md); Alembic `f2c3d4e5f6a7`); Organization-Calibrated Pricing Engine remains **BLOCKED / NOT STARTED**.

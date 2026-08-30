# CalibAi / Brayman Estimator — Organization & Calibration Architecture (Phase A)

| Attribute | Value |
|---|---|
| Document Type | Architectural Specification & Data Governance Standard |
| Program / Milestone | CalibAi Organization & Calibration Architecture — Phase A |
| Governing Authority | `platform-constitution.md` (Articles 1–12), `architecture-principles.md`, `platform-governance.md`, `pricing-policy.md`, `CAR-001`, `ADR-019`, `ADR-024`, `ADR-025` |
| Status | **ARCHITECTURAL SPECIFICATION & GOVERNANCE RECORD** (Phase A Complete — No Application Code / No Schema Migrations) |
| Date | 2026-08-28 |
| Development Tenant | Organization 001 — Brayman Construction Inc. |
| Related future pin | [organization-brand-profile.md](organization-brand-profile.md) **FUTURE / NOT IMPLEMENTED** — not this document's `branding_config` JSON; that column is **not implemented** |

---

## 1. Executive Summary & Core Governing Principle

This document establishes the **organization-aware commercial architecture** required before CalibAi can implement organization-specific pricing, labour calibration, historical estimate ingestion (Phase B), or commercial learning and calibration.

### The Governing Principle

> **CALIBAI OWNS THE ENGINE AND METHODOLOGY.**  
> **EACH CUSTOMER ORGANIZATION OWNS ITS COMMERCIAL INTELLIGENCE.**  
> **BRAYMAN CONSTRUCTION IS THE FIRST DEVELOPMENT / UAT ORGANIZATION. IT IS NOT THE UNIVERSAL CALIBAI PRICING MODEL.**

Under this foundational architecture:
1. **CalibAi Platform:** Provides the algorithmic engine, measurement and sheet classification pipelines, coordinate transformations, deterministic extraction parsers, estimation mathematical solvers, lifecycle state machines, audit infrastructure, and standard industry baseline libraries.
2. **Customer Organization (Tenant):** Owns its commercial data, direct labour wage rates, burden multipliers, crew productivity curves, material discounts, subcontractor bid history, margin preferences, risk tolerances, customer proposals, and project actuals.
3. **UAT Baseline:** Brayman Construction Inc. serves as **Organization 001 (`ORG-001`)**—the primary real-world development and user acceptance testing organization. Brayman's commercial practices (e.g., $65/hr direct labour rate, 15% true gross margin policy, historical ICF and slab estimating methods) constitute Brayman's calibrated commercial intelligence, not hard-coded platform defaults.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       CALIBAI PLATFORM ENGINE                                          │
│  - Document / Sheet Intelligence Pipeline       - Scale Calibration & Coordinate Geometry              │
│  - Deterministic Ingestion Parser               - Rate & Policy Resolution Cascade Engine              │
│  - Estimation Mathematical Solvers              - Multi-Tenant Isolation & Audit Trail Infrastructure  │
│  - Standard Industry Baseline Reference Library - State Machine & Review Governance Engine             │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │ Ingests, Calibrates & Isolates
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CUSTOMER COMMERCIAL INTELLIGENCE                                       │
│                                                                                                        │
│  ┌──────────────────────────────────────────────┐    ┌──────────────────────────────────────────────┐  │
│  │     ORGANIZATION 001: BRAYMAN CONSTRUCTION   │    │          ORGANIZATION 002: CUSTOMER X        │  │
│  │ -------------------------------------------- │    │ -------------------------------------------- │  │
│  │ - Direct Labour Rate: $65.00/hr (CAD)        │    │ - Direct Labour Rate: $72.50/hr (CAD)        │  │
│  │ - Pricing Policy: 15% True Gross Margin      │    │ - Pricing Policy: 18% Tiered Markup          │  │
│  │ - 20 Historical Workbooks (ICF, Slab, Build) │    │ - Historical Workbooks (Timber Frame, Fitout)│  │
│  │ - Calibrated ICF & Concrete Productivity     │    │ - Calibrated Framing Productivity            │  │
│  │ - Ontario Construction Contract Templates    │    │ - Custom Contract & Warranty Templates       │  │
│  └──────────────────────────────────────────────┘    └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Three-Tier Commercial Architecture

To prevent vendor lock-in, eliminate hardcoded assumptions, and enable seamless multi-tenant productization, commercial intelligence is divided into three distinct tiers:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: CALIBAI CORE (Universal Engine & Platform Code)                                                │
│ - Pure execution algorithms (geometry, coordinate mapping, math solvers, ingestion rules).             │
│ - Platform data models, audit mechanisms, state machine lifecycles.                                    │
│ - Zero customer-specific rates, names, margins, or cost data.                                          │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │ Fallback / Starter Reference
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 2: CALIBAI BASELINE LIBRARY (Reference / Starter Data)                                            │
│ - Published regional wage statistics and open construction benchmark production rates.                 │
│ - Standard CSI MasterFormat / UniFormat classification dictionaries.                                   │
│ - Starter assembly templates (e.g., generic 8" ICF wall recipe, standard 4" slab-on-grade).            │
│ - Read-only starter baseline provided by CalibAi; cannot overwrite customer actuals.                   │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │ Calibrated / Overridden By
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 3: ORGANIZATION CALIBRATION MODEL (Customer Commercial Intelligence)                              │
│ - Calibrated crew production outputs derived from actual project performance.                          │
│ - Organization-approved labour rates, burden multipliers, and equipment rates.                         │
│ - Ingested historical estimates and quotation histories.                                               │
│ - Commercial margin targets, risk contingency policies, and approved contract templates.               │
│ - 100% confidential and isolated to the owning Organization.                                           │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Architectural Distinctions:
1. **CalibAi Core:** Contains no hardcoded dollar rates, margin percentages, or trade names. The engine operates on mathematical representations of cost structures, formulas, and constraints.
2. **CalibAi Baseline Library:** Ships as a seeded, immutable reference catalogue. When a new customer organization onboard, it can clone baseline recipes into its private organization library. Baseline items are tagged with source class `BASELINE`.
3. **Organization Calibration Model:** The living commercial brain of each contractor. As an organization executes projects and logs timecards, change orders, and supplier invoices, the CalibAi LEARN pipeline proposes calibration updates to the organization's private calibration model.

---

## 3. Canonical Organization Entity Specification (Conceptual Data Model)

The `Organization` entity is the top-level commercial and administrative container. All business entities, projects, documents, cost items, historical workbooks, and user memberships belong to exactly one Organization.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       ENTITY: Organization                                             │
├────────────────────────────────┬─────────────────┬─────────────────────────────────────────────────────┤
│ Field                          │ Type            │ Description & Governance Invariants                 │
├────────────────────────────────┼─────────────────┼─────────────────────────────────────────────────────┤
│ `id`                           │ UUID / String   │ Canonical immutable Organization PK (e.g. `ORG-001`)│
│ `legal_name`                   │ String(255)     │ Registered legal entity name (e.g. Brayman Con...)  │
│ `trade_name`                   │ String(255)     │ DBA / Public trade name                             │
│ `corporate_identifier`         │ String(100)     │ Business number / Tax registration number           │
│ `jurisdiction`                 │ String(100)     │ Primary legal jurisdiction (e.g. Ontario, Canada)   │
│ `primary_currency`             │ String(3)       │ ISO-4217 Currency Code (default: `CAD`)             │
│ `status`                       │ String(50)      │ `active`, `suspended`, `archived`                   │
│ `default_labour_rate`          │ Numeric(10,2)   │ Default base direct labour cost per man-hour        │
│ `default_pricing_policy_type`  │ String(50)      │ `TRUE_GROSS_MARGIN`, `COST_PLUS_MARKUP`, `TIERED`   │
│ `default_target_margin`        │ Numeric(5,4)    │ Default commercial margin fraction (e.g. `0.1500`)  │
│ `default_tax_rate`             │ Numeric(5,4)    │ Default sales tax fraction (e.g. `0.1300` for HST)  │
│ `active_calibration_model_id`  │ UUID / String   │ Pointer to currently active Calibration Model       │
│ `branding_config`              │ JSON            │ **Intended / not implemented.** Future branding is pinned on [organization-brand-profile.md](organization-brand-profile.md). Do not implement this JSON from that pin. |
│ `integration_config`           │ JSON            │ QuickBooks tenant ID, cloud storage paths           │
│ `created_at`                   │ DateTime        │ UTC creation timestamp                              │
│ `updated_at`                   │ DateTime        │ UTC update timestamp                                │
└────────────────────────────────┴─────────────────┴─────────────────────────────────────────────────────┘
```

### Relational Entity Graph:
- `Organization` 1 : N `UserMembership` (Users scoped to Organization with RBAC roles)
- `Organization` 1 : N `Project` (All drawings, sheets, measurements, estimates belong to Org)
- `Organization` 1 : N `SourceWorkbookManifest` (Historical workbooks belong to Org)
- `Organization` 1 : N `NormalizedHistoricalEstimate` (Ingested commercial data belongs to Org)
- `Organization` 1 : N `OrganizationCalibrationModel` (Versioned calibration intelligence)
- `Organization` 1 : N `CostItem` / `Assembly` (Private organization **costing** catalogue — not CalibAi material identity; see [material-catalogue-architecture.md](material-catalogue-architecture.md))
- `Organization` 1 : N `ProposalTemplate` (Private contract / proposal document formats)

---

## 4. Data Ownership Matrix

Every entity in the CalibAi platform is explicitly categorized across three ownership classifications:

| Entity Category | Specific Entity / Record | Ownership Classification | Multi-Tenant Partitioning Rule |
|---|---|---|---|
| **Platform Infrastructure** | Engine Algorithms, Math Solvers | **Global Platform** | Stateless code, immutable across tenants |
| **Reference Data** | Baseline Cost Items, Starter Assemblies | **Global Baseline** | Read-only global catalog; cloned on override |
| **Reference Data** | Standard Classification Dictionaries | **Global Baseline** | Standard MasterFormat / UniFormat codes |
| **Organization Identity** | `Organization`, `UserMembership` | **Organization-Owned** | Strict tenant partition |
| **Project Master** | `Project`, `Client` | **Organization-Owned** | Filtered by `organization_id` on all queries |
| **Plan Intelligence** | `DrawingPackage`, `DrawingRevision` | **Organization-Owned** | Scoped through `Project.organization_id` |
| **Plan Intelligence** | `PlanDocument`, `PlanPage` | **Organization-Owned** | Binary storage and database rows org-isolated |
| **Plan Intelligence** | `PlanSheet`, `PlanSheetPage` | **Organization-Owned** | Scoped through `DrawingRevision` / `Project` |
| **Plan Intelligence** | `PlanScaleCalibration`, `PlanMeasurement` | **Organization-Owned** | Scoped through `PlanSheet` / `Project` |
| **Plan Intelligence** | `ProcessingAttempt`, `ProcessingResult` | **Organization-Owned** | Raw extraction payloads confidential to Org |
| **Commercial Estimating** | `Estimate`, `EstimateVersion` | **Organization-Owned** | Commercial figures 100% confidential to Org |
| **Commercial Estimating** | `EstimateSection`, `EstimateLineItem` | **Organization-Owned** | Direct costs and pricing private to Org |
| **Commercial Estimating** | `Proposal`, `ProposalLineItem` | **Organization-Owned** | Customer pricing and terms private to Org |
| **Project Controls** | `ChangeOrder`, `ChangeOrderItem` | **Organization-Owned** | Contract revisions private to Org |
| **Cost Intelligence** | `CostItem`, `Assembly`, `AssemblyItem` | **Organization-Owned** (Current: M011 `organization_id`) | Org costing catalogue. CalibAi Material Catalogue is **separate platform vocabulary** ([material-catalogue-architecture.md](material-catalogue-architecture.md); Intended, not implemented). Do not treat CostItem as canonical material identity. |
| **Historical Ingestion** | `SourceWorkbookManifest` | **Organization-Owned** | Ingested workbook files/manifests private to Org |
| **Historical Ingestion** | `SourceCellObservation` | **Organization-Owned** | Cell-level traces private to Org |
| **Historical Ingestion** | `NormalizedHistoricalEstimate` | **Organization-Owned** | Ingested project history private to Org |
| **Calibration Intelligence**| `OrganizationCalibrationModel` | **Organization-Owned** | Production rates and curves private to Org |
| **Legal & Branding** | `ProposalTemplate`, Contract Templates | **Baseline w/ Org Override** | Standard legal shells customized per Org |
| **Audit Infrastructure** | `PlanAuditEvent`, System Audit Trails | **Organization-Owned** | Audit logs partitioned by `organization_id` |

---

## 5. Organization-Neutral Source Terminology & Evidence Hierarchy

To maintain rigorous construction auditability across all organizations, all cost items, productivity factors, unit prices, and commercial assumptions must carry an explicit **Evidence Classification**. 

Historical records and platform defaults are **evidence**, not automatic truth.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                HISTORICAL PRICING EVIDENCE HIERARCHY                                   │
│                                       (Highest to Lowest Authority)                                    │
├──────────────────────┬─────────────────────────────────────────────────────────┬───────────────────────┤
│ Evidence Class       │ Definition & Source Lineage                             │ Commercial Authority  │
├──────────────────────┼─────────────────────────────────────────────────────────┼───────────────────────┤
│ **1. ORG-ACTUAL**    │ Verified historical project actuals, timecards, vendor  │ **Empirical Truth**   │
│                      │ invoices, job cost accounting records for this Org.     │ (Strongest Calibration│
│                      │ Serves as calibration evidence; does not alter pricing. │  Evidence)            │
├──────────────────────┼─────────────────────────────────────────────────────────┼───────────────────────┤
│ **2. ORG-APPROVED**  │ Active Chief Estimator / Executive approved company     │ **Authorized Standard│
│                      │ standard rate or calibrated productivity curve.         │ (Active Baseline)     │
├──────────────────────┼─────────────────────────────────────────────────────────┼───────────────────────┤
│ **3. CURRENT**       │ Active project-specific vendor quote, supplier bid,     │ **Live Market Rate**  │
│                      │ or binding subcontractor proposal for quoted inputs.    │ (Project-Specific)    │
├──────────────────────┼─────────────────────────────────────────────────────────┼───────────────────────┤
│ **4. ORG-HISTORICAL**│ Ingested historical estimates, past bids, legacy        │ **Historical Evidence │
│                      │ workbook data. (Evidence of past intent, not actuals).  │ (Requires Review)     │
├──────────────────────┼─────────────────────────────────────────────────────────┼───────────────────────┤
│ **5. BASELINE**      │ CalibAi global reference library, regional statistics,  │ **Fallback Starter**  │
│                      │ published trade standards, manufacturer datasheets.     │ (Flagged as Generic)  │
├──────────────────────┼─────────────────────────────────────────────────────────┼───────────────────────┤
│ **6. PROVISIONAL**   │ Heuristic default, suggested production rate, or        │ **Provisional Draft** │
│                      │ unverified import prior to human estimator review.      │ (Unverified)          │
├──────────────────────┼─────────────────────────────────────────────────────────┼───────────────────────┤
│ **7. MANUAL**        │ Ad-hoc estimator override on a specific estimate line.  │ **Human Discretion**  │
│                      │ Requires reason documentation if variance is extreme.   │ (Audited Override)    │
└──────────────────────┴─────────────────────────────────────────────────────────┴───────────────────────┘
```

### Governing Evidence & Calibration Principles:
1. **Operating Standard:** `ORG-APPROVED` is the active organization-authorized operating rate or policy used automatically for estimates.
2. **Calibration Evidence Role:** `ORG-ACTUAL` completed-job performance is the strongest empirical calibration evidence, but does **not** silently replace an `ORG-APPROVED` rate.
3. **Candidate Generation & Human Approval:** Actual performance may evaluate sufficient comparable empirical evidence and generate a `PROPOSED` calibration candidate. Governed human/executive approval is strictly required before that candidate becomes `ORG-APPROVED`.
4. **No AI Auto-Approval:** AI or automated analytical methods cannot independently set or activate an `ORG-APPROVED` standard.

---

## 6. Organization Calibration Lifecycle

The Organization Calibration Model governs how commercial intelligence matures within a customer organization over time.

```
   ┌───────────────────────┐
   │ 1. INITIAL_EMPTY      │ ──► Organization created; zero private commercial data.
   └───────────┬───────────┘
               │ Initialize with Starter Baseline
               ▼
   ┌───────────────────────┐
   │ 2. BASELINE_INITIALIZED│ ──► Standard CalibAi baseline cloned; rates flagged BASELINE.
   └───────────┬───────────┘
               │ Ingest Historical Workbooks (Phase B)
               ▼
   ┌───────────────────────┐
   │ 3. INGESTION_ACCUMULATING ─► Historical estimates parsed; observations tagged ORG-HISTORICAL.
   └───────────┬───────────┘
               │ Calibration Engine Analyzes Patterns
               ▼
   ┌───────────────────────┐
   │ 4. CALIBRATION_PROPOSED│ ──► Statistical / Analytical engine proposes calibrated crew curves & rates.
   └───────────┬───────────┘
               │ Human Estimator / Executive Review Gate
               ▼
   ┌───────────────────────┐
   │ 5. HUMAN_REVIEW       │ ──► Chief Estimator reviews, adjusts, and signs off.
   └───────────┬───────────┘
               │ Explicit Approval & Activation
               ▼
   ┌───────────────────────┐
   │ 6. ACTIVE_CALIBRATED  │ ──► Current authoritative calibration model for new estimates.
   └───────────┬───────────┘
               │ Superseded by newer calibrated version
               ▼
   ┌───────────────────────┐
   │ 7. SUPERSEDED / ARCHIVE│ ──► Immutable historical snapshot preserved for past project audits.
   └───────────────────────┘
```

### Review Gate Rules:
1. **No Silent Activation:** Statistical or analytical evaluation of historical workbooks or project actuals generates a `CALIBRATION_PROPOSED` model. It **never** moves to `ACTIVE_CALIBRATED` without an explicit human review and approval action.
2. **Audit Attribution:** Every transition from `HUMAN_REVIEW` to `ACTIVE_CALIBRATED` logs the approving user ID, timestamp, variance notes, and calibration parameter delta.

---

## 7. Calibration Model Versioning & Historical Immutability

To guarantee that past estimates and contracts remain mathematically reproducible:

1. **Semantic Versioning:** Calibration models are versioned sequentially within each organization (e.g., `ORG-001-CAL-v1.0.0`, `ORG-001-CAL-v1.1.0`, `ORG-001-CAL-v2.0.0`).
2. **Estimate Snapshot Pinning:** When an `EstimateVersion` is created, it records a foreign key to the `calibration_model_version_id` active at that exact moment.
3. **Historical Immutability Invariant:** Once a calibration model version is referenced by any finalized or accepted estimate version, that calibration model becomes **100% byte-for-byte immutable**. Subsequent adjustments to organization rates or productivity curves spawn a new calibration version (`v1.1.0`), leaving `v1.0.0` untouched.

---

## 8. Rate & Policy Resolution Model

When the CalibAi Estimating Engine resolves the unit cost, labour productivity factor, or margin percentage for any estimate line item, it follows the canonical operating resolution cascade:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CANONICAL RATE RESOLUTION CASCADE                                    │
│                                         (Operating Precedence)                                         │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Applicable ORG-APPROVED Rate / Policy                                                               │
│    - Active organization-authorized operating rate, production curve, or Commercial Gate factor.       │
│    - Evidence Class: ORG-APPROVED. Used automatically for production estimating.                       │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. Applicable CURRENT Supplier / Subcontract Quote                                                    │
│    - Direct live quote where the required input is a current quoted cost item.                         │
│    - Evidence Class: CURRENT. Project-specific live market input.                                      │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. ORG-ACTUAL Calibration Candidate Generation                                                        │
│    - If no approved organization rate exists, evaluate sufficient comparable ORG-ACTUAL empirical      │
│      evidence and generate a PROPOSED calibration candidate for human review (never auto-activated).   │
│    - Evidence Class: ORG-ACTUAL (Calibration Candidate).                                               │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. ORG-HISTORICAL Comparable Evidence                                                                 │
│    - Comparable historical estimate or legacy workbook observation for review.                         │
│    - Evidence Class: ORG-HISTORICAL.                                                                   │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. BASELINE / PUBLISHED / MANUFACTURER Reference Library                                               │
│    - Standard regional benchmark, manufacturer guidance, or generic recipe.                            │
│    - Evidence Class: BASELINE. System displays visual warning badge: "Using Generic Baseline Rate".     │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 6. PROVISIONAL / REVIEW REQUIRED                                                                      │
│    - Unverified heuristic fallback requiring explicit human review and determination.                  │
│    - Evidence Class: PROVISIONAL.                                                                      │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 7. MANUAL with Required Reason                                                                         │
│    - Estimator explicit line-item override. Preempts automated resolution. Mandates reason note if     │
│      variance exceeds organization policy threshold (> 25%).                                           │
│    - Evidence Class: MANUAL.                                                                           │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Rate Isolation Invariant:
At no point may Organization B's private rate or actual data be used to price Organization A's estimate. All resolution cascades operate exclusively within the tenant partition of the estimating Organization.

---

## 9. Project Creation Commercial Decision Gate

Every project created in CalibAi must pass through the **Commercial Decision Gate**. This gate captures the commercial, logistical, and environmental context that governs how the calibration engine prices the job:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              PROJECT COMMERCIAL DECISION GATE PROFILE                                  │
├─────────────────────────┬──────────────────────────────────────────────────────────────────────────────┤
│ Decision Gate Parameter │ Allowed Values / Profiles                                                    │
├─────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ **1. Project Type**     │ `RESIDENTIAL_DETACHED`, `ICF_FOUNDATION`, `SLAB_ON_GRADE`, `CUSTOM_BUILD`,    │
│                         │ `COMMERCIAL_FITOUT`, `STRUCTURAL_RENOVATION`, `MULTI_UNIT_RESIDENTIAL`       │
├─────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ **2. Pricing Posture**  │ `AGGRESSIVE_BID` (Low margin / competitive market share capture)             │
│                         │ `STANDARD_COMPETITIVE` (Target corporate margin, e.g. 15%)                   │
│                         │ `PREMIUM_NEGOTIATED` (Value-based, specialized expertise, high margin)       │
│                         │ `DEFENSIVE_DEMAND` (High-capacity, high margin to throttle volume)           │
├─────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ **3. Execution Risk**   │ `LOW_STANDARD` (Known scope, familiar site, standard conditions)            │
│                         │ `MODERATE_CONSTRAINED` (Tight tolerances, limited staging, technical specs)  │
│                         │ `HIGH_SEVERE_RISK` (Extreme site difficulty, unknown soils, weather risk)   │
├─────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ **4. Schedule Condition**│ `STANDARD_PACE` (Normal working hours, standard lead times)                  │
│                         │ `ACCELERATED_OVERTIME` (Compressed schedule requiring premium overtime)     │
│                         │ `SEASONAL_WINTER_BUILD` (Cold weather curing, ground thaw, heating costs)   │
│                         │ `FIXED_HARD_DEADLINE` (Liquidated damages risk / hard occupancy date)       │
├─────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ **5. Site Condition**   │ `CLEAR_LEVEL_ACCESS` (Direct road access, ample staging, standard ground)    │
│                         │ `TIGHT_URBAN_STAGING` (No street storage, crane permits, restricted access)  │
│                         │ `POOR_SOILS_ROCK` (Bedrock blasting, engineered fill, dewatering required)  │
│                         │ `REMOTE_EXTENDED_TRAVEL` (Extended crew transit, lodging allowances)         │
├─────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ **6. Estimate Stage**   │ `CLASS_5_CONCEPTUAL` (+/- 35% accuracy; rough order of magnitude)            │
│                         │ `CLASS_4_SCHEMATIC` (+/- 20% accuracy; preliminary budget)                   │
│                         │ `CLASS_3_DESIGN_DEV` (+/- 15% accuracy; semi-detailed takeoff)               │
│                         │ `CLASS_2_BID_TENDER` (+/- 10% accuracy; comprehensive plan measurement)      │
│                         │ `CLASS_1_BINDING_CONTRACT` (+/- 5% accuracy; firm fixed price baseline)      │
├─────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ **7. Delivery Model**   │ `STIPULATED_SUM_FIXED` (Lump sum fixed price)                                │
│                         │ `GUARANTEED_MAX_PRICE` (Cost-plus with GMP cap and shared savings)           │
│                         │ `TIME_AND_MATERIALS` (Hourly labour billing + actual material cost-plus)     │
│                         │ `UNIT_PRICE_CONTRACT` (Fixed price per unit of measurement, e.g. $/sq ft)    │
└─────────────────────────┴──────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Project Decision Provenance & Audit Trail

To prevent commercial drift and ambiguity:

1. **Snapshot on Versioning:** The Project Commercial Profile is locked at the creation of each `EstimateVersion`. If an estimator changes the Pricing Posture from `STANDARD_COMPETITIVE` to `AGGRESSIVE_BID`, the change does not alter past estimate versions; it spawns a new `EstimateVersion` with full provenance.
3. **Pre-M011 Legacy Project Invariant:** Projects created prior to the introduction of the Commercial Decision Gate (Milestone 011) do not have historical records for these commercial decisions. In migration and backfill, all pre-M011 projects receive an explicit `Legacy / Unknown` context (`is_legacy_unknown = True`) across all seven decision parameters. CalibAi must **never** infer or manufacture historical Pricing Posture, Execution Risk, Schedule, Site Condition, Estimate Stage, Delivery Model, or Project Type from pre-M011 records. Future calibration and learning engines must explicitly treat legacy unrecorded context as unrecorded/unknown.

---

## 11. Reason Requirement for Exceptional Commercial Settings

To enforce commercial discipline without removing estimator agency, CalibAi mandates structured **Human Justifications** for exceptional commercial configurations:

### Mandatory Justification Triggers:
1. **Extreme Low Margin:** Target gross margin configured below the organization safety floor (e.g., $< 8.0\%$ when corporate target is $15.0\%$).
2. **Extreme High Margin:** Target gross margin configured above the ceiling (e.g., $> 30.0\%$).
3. **Severe Execution Risk with Zero Contingency:** Marking Execution Risk as `HIGH_SEVERE_RISK` while setting line contingency to $0.00$.
4. **Large Productivity Variance:** Overriding a calibrated crew productivity curve by more than $\pm 25\%$ on a major division item.

### Governance Behavior:
When a trigger condition is met, the system displays a mandatory prompt: *"Exceptional commercial setting detected. Please record the commercial justification before finalizing this estimate version."* The justification note is permanently bound to the `EstimateVersion` and displayed in the **Internal Detailed Cost Breakdown**.

---

## 12. Pricing Posture Policy: Separating Economics from Strategy

A core architectural tenet of CalibAi is the strict decoupling of **Direct Cost Economics** from **Commercial Pricing Strategy**:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 COMMERCIAL PRICING DECOUPLING                                          │
├─────────────────────────────────────────────────┬──────────────────────────────────────────────────────┤
│ DIRECT COST ECONOMICS (Physical Reality)        │ COMMERCIAL PRICING STRATEGY (Market Strategy)        │
├─────────────────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ - Physical quantities from calibrated drawings. │ - Pricing Posture (Aggressive vs Premium).           │
│ - Crew productivity hours based on actual data. │ - Target Gross Margin percentage (e.g. 15%).         │
│ - Direct wage rates ($65/hr) + true burden.     │ - Commercial risk contingency buffer.                │
│ - True supplier material quotes & sub bids.     │ - Strategic discount or market-entry allowance.      │
├─────────────────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ **INVARIANT:** Pricing Posture NEVER alters     │ **INVARIANT:** Selling price is derived purely by    │
│ physical quantities, crew hours, or wage costs. │ applying commercial strategy on top of direct cost.  │
└─────────────────────────────────────────────────┴──────────────────────────────────────────────────────┘
```

### Architectural Protection:
An estimator must **never** achieve an "aggressive bid" by arbitrarily reducing the crew hours required to pour concrete if the physics of the job require those hours. Instead, the physical direct cost remains true ($100,000 direct cost), and the Pricing Posture adjusts the commercial margin (e.g., reducing margin from 15% to 10%), making the cost-of-work transparent and auditable.

---

## 13. Execution Risk Policy: Delivery Uncertainty vs Profit Preference

Execution Risk represents **expected delivery cost uncertainty** (the physical risk that bad weather, difficult soils, or complex geometry will consume more labor and materials). It is completely distinct from commercial profit margin.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                ESTIMATE COST BUILDUP ARCHITECTURE                            │
│                                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 1. BASE DIRECT COST                                                                  │   │
│   │    - Direct Materials + Direct Labour ($65/hr) + Subcontractors + Equipment          │   │
│   └──────────────────────────────────────────┬───────────────────────────────────────────┘   │
│                                              │ Plus                                          │
│                                              ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 2. EXECUTION RISK CONTINGENCY (Direct Cost Buffer)                                   │   │
│   │    - Soil uncertainty allowance, winter weather heating, crane delay buffer          │   │
│   │    - Calculated based on Execution Risk & Site Condition settings                    │   │
│   └──────────────────────────────────────────┬───────────────────────────────────────────┘   │
│                                              │ Equals                                        │
│                                              ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 3. TOTAL DIRECT ESTIMATED COST = Base Direct Cost + Execution Risk Contingency       │   │
│   └──────────────────────────────────────────┬───────────────────────────────────────────┘   │
│                                              │ Multiplied by Commercial Margin Formula       │
│                                              ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 4. PRE-TAX SELLING PRICE = Total Direct Cost / (1 - Target Gross Margin)             │   │
│   └──────────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Historical Learning of Project Context (LEARN Module)

CalibAi analytics and calibration methods may correlate organization-specific project context against realized commercial and operational outcomes (via timecards and invoices logged in BUILD and MONITOR), stratifying variance by the **Project Commercial Decision Profile**:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               CONTEXT-AWARE COMMERCIAL LEARNING                                        │
│                                                                                                        │
│   [Actual Job Performance Data] ──► [Stratify by Project Decision Profile]                            │
│                                     │                                                                  │
│                                     ├── Profile A: ICF Foundation + Standard Pace + Clear Site         │
│                                     │   └── Observed Productivity: 0.18 hrs / sq ft (Variance: -2%)    │
│                                     │                                                                  │
│                                     └── Profile B: ICF Foundation + Winter Build + Rock/Poor Soils     │
│                                         └── Observed Productivity: 0.26 hrs / sq ft (Variance: +44%)   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Learning Safety Boundary (ADR-024 Enforcement):
CalibAi analytical and calibration pipelines will **never** silently update baseline rates or blur distinct project contexts into a single noisy average. Architecture permits statistical analysis, deterministic methods, machine learning, or future approved methods, but does **not** mandate machine learning at the architectural layer. The LEARN engine surfaces context-specific recommendations (e.g., *"When estimating ICF in Winter conditions, actual historical data indicates a +35% labor adjustment is warranted"*), requiring explicit human estimator sign-off to update the organization calibration profile.

---

## 15. Multi-Tenant Data Isolation & Security Architecture

CalibAi enforces strict logical and physical data isolation across all customer organizations:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     MULTI-TENANT ISOLATION MODEL                                       │
├──────────────────────┬─────────────────────────────────────────────────────────────────────────────────┤
│ Isolation Boundary   │ Enforced Architecture & Isolation Standard                                      │
├──────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
│ **Database Queries** │ Every query against tenant entities MUST include `WHERE organization_id = :oid`.│
│                      │ Repository layers enforce mandatory organization parameterization.             │
├──────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
│ **Storage Partition**│ Blob / PDF storage paths are partitioned: `/storage/org_{org_id}/proj_{proj_id}/`│
│                      │ Pre-signed download URLs validate session tenant identity before serving bytes. │
├──────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
│ **AI Contexts**      │ AI take-off and suggestion prompts NEVER include cross-organization context.    │
│                      │ Ingestion extractions run in isolated, tenant-scoped execution boundaries.      │
├──────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
│ **Export Pipelines** │ QuickBooks and accounting exports authenticate exclusively against the specific │
│                      │ organization's integration profile.                                             │
└──────────────────────┴─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Cross-Organization Benchmarking (Status: NOT AUTHORIZED)

### Policy Invariant:
> **STATUS: STRICTLY NOT AUTHORIZED.**

1. CalibAi will **never** pool, aggregate, anonymize, or share customer commercial data, unit costs, labour productivity metrics, win/loss rates, or customer lists across organizations without explicit, affirmative multi-party legal agreements and architectural review.
2. Calibration models and analytical models trained on Organization A's historical workbooks and actuals belong exclusively to Organization A.
3. If industry-wide benchmarking is ever proposed in future years, it requires an approved ADR, Legal Content Gate sign-off, and opt-in customer consent.

---

## 17. Historical Ingestion Reconciliation (Phase A / Phase B Mapping)

The 20 historical Brayman estimating workbooks audited in Phase A (`docs/architecture/historical-estimate-ingestion-architecture.md`) are reconciled into the Organization Calibration Architecture as follows.

**Subsequent custody (2026-08-30 — [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) Accepted; [FG-013](../feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) implemented, live migration pending):** This 20-workbook ORG-001 Desktop corpus is the **legacy controlled corpus**. Do **not** move, recopy, delete, rewrite, or path-mutate it to conform to productized storage. Office uploads use a **separate** app-managed custody path (`instance/historical_uploads/…`). FG-013 ends at reviewed **ORG-HISTORICAL** evidence and must **not** auto-create calibration candidates or ORG-APPROVED standards. TIER_A historical estimate review means an estimate associated with a completed project; it is **not** `ORG-ACTUAL`.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              HISTORICAL WORKBOOK INGESTION LINEAGE                                     │
│                                                                                                        │
│  [20 External Workbooks] (SHA-256 Verified in Manifest)                                                │
│         │                                                                                              │
│         ▼                                                                                              │
│  [SourceWorkbookManifest] (Bound to organization_id = 'ORG-001' / Brayman Construction Inc.)           │
│         │                                                                                              │
│         ▼                                                                                              │
│  [SourceCellObservation] (Cell-level provenance: Sheet, Coordinate, Formula, Evaluated Value)          │
│         │                                                                                              │
│         ▼                                                                                              │
│  [NormalizedHistoricalEstimate] (Tagged with Evidence Class: ORG-HISTORICAL)                          │
│         │                                                                                              │
│         ▼                                                                                              │
│  [Calibration Proposal Engine] (Aggregates historical ICF, slab, and finish productivity)             │
│         │                                                                                              │
│         ▼                                                                                              │
│  [Human Review Gate] (Chief Estimator Joel Brayman reviews proposed rates)                             │
│         │                                                                                              │
│         ▼                                                                                              │
│  [Organization Calibration Model v1.0] (Active Calibrated Intelligence for Brayman Construction Inc.)  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 18. Labour Engine Reconciliation

The future CalibAi Labour Engine (Phase B) integrates seamlessly with the Organization Calibration Model:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 LABOUR ENGINE EXECUTION PIPELINE                                       │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. QUANTITY INPUT                                                                                      │
│    - Physical quantity derived from calibrated plan measurement (e.g. 1,450 sq ft of 8" ICF Wall).     │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. PRODUCTIVITY RESOLUTION                                                                             │
│    - Base productivity curve retrieved from Active Org Calibration Model (e.g. 0.08 hrs/sq ft).        │
│    - Multipliers applied from Project Commercial Profile (e.g. +15% for Tight Urban Staging).          │
│    - Calculated Total Crew Hours = 1,450 * (0.08 * 1.15) = 133.4 Man-Hours.                           │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. RATE APPLICATION                                                                                    │
│    - Direct Labour Cost = 133.4 Man-Hours * $65.00/hr (Org 001 Approved Base Rate) = $8,671.00.       │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. COMMERCIAL LINE GENERATION                                                                          │
│    - Emits structured EstimateLineItem with complete provenance: Quantity, Production Rate, Base Rate, │
│      Evidence Classification (`ORG-APPROVED`), and Calculation Formula.                                │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Constraint (FG-008 / ADR-029, 2026-08-29):** Automatic commercial-profile multipliers on labour hours (including the `+15%` Tight Urban Staging example in step 2 above) are **not authorized**. Project conditions may select a matching ORG-APPROVED production standard or require an explicit documented adjustment. Pricing Posture and Execution Risk must not silently scale true hours. See [labour-engine-phase-b-architecture.md](labour-engine-phase-b-architecture.md).

---

## 19. Pricing Policy & Formula Reconciliation

This architecture explicitly reconciles the governing product pricing policy with historical workbook practices and legacy application calculation code:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  PRICING FORMULA RECONCILIATION                                        │
├────────────────────────────┬─────────────────────────────┬─────────────────────────────────────────────┤
│ Domain / Context           │ Mathematical Formula        │ Status & Architectural Alignment            │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────────────────────┤
│ **Governed Policy**        │ $P = \frac{C_{\text{dir}}}{1 - M}$  │ **Governing Standard** in `pricing-policy.md`│
│ (`pricing-policy.md`)      │ At 15%: $P = \frac{C_{\text{dir}}}{0.85}$ │ Required for all new CalibAi estimate outputs│
├────────────────────────────┼─────────────────────────────┼─────────────────────────────────────────────┤
│ **Historical Workbooks**   │ $P = C_{\text{dir}} \times (1 + M)$ │ **Historical Evidence Class** (`ORG-HISTORICAL`)│
│ (20 Audited Workbooks)     │ Margin = $C_{\text{dir}} \times 0.15$ │ Ingestion engine records exact formula type │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────────────────────┤
│ **Legacy Builder Code**    │ Line Markup +               │ **Discrepancy Recorded in ADR-025**         │
│ (`app/models/estimate.py`) │ Version Overhead + Profit   │ Will be migrated to true Gross Margin in    │
│                            │                             │ future Pricing Engine Feature Gate          │
└────────────────────────────┴─────────────────────────────┴─────────────────────────────────────────────┘
```

---

## 20. Organization Branding & Document Package Ownership

The Organization owns all visual, legal, and commercial presentation assets across the **Four Core Document Outputs** (`docs/architecture/project-document-package.md`):

1. **Internal Detailed Cost Breakdown:** Emits internal organization entity headers, confidential labor rates, supplier costs, and margin analysis. Strictly internal to the owning organization.
2. **Customer-Facing Estimate:** Emits organization logo, trade branding, customer-facing line items, exclusions, and payment terms. Suppresses direct costs and internal margins.
3. **QuickBooks Estimate Representation:** Formatted according to the organization's specific chart-of-accounts and item mapping.
4. **Ontario Construction Contract & Warranty Package:** Populates registered legal entity name, corporate registration number, contractor business address, project address, and governed Ontario warranty schedules.

---

## 21. Integration Ownership & Boundary Scoping

All third-party system integrations are strictly partitioned per Organization:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  INTEGRATION BOUNDARY ARCHITECTURE                                     │
├──────────────────────────┬─────────────────────────────────────────────────────────────────────────────┤
│ Integration Target       │ Organization-Scoped Architecture Standard                                   │
├──────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ **QuickBooks Online**    │ 1:1 OAuth realm ID binding per Organization. No cross-tenant access.        │
│ **Supplier Catalogues**  │ Organization-specific account numbers and negotiated discount tiers.        │
│ **Cloud Document Storage**│ Customer-owned AWS S3 / Azure Blob buckets or tenant-isolated prefix keys. │
│ **E-Signature Service**  │ Organization-owned template keys and API integration tokens.               │
└──────────────────────────┴─────────────────────────────────────────────────────────────────────────────┘
```

---

## 22. Reference Profile: UAT Organization 001 — Brayman Construction Inc.

To ground all testing and verification in verified real-world operations, `Organization: ORG-001` is formally defined:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              UAT ORGANIZATION 001 REFERENCE SPECIFICATION                              │
├─────────────────────────────┬──────────────────────────────────────────────────────────────────────────┤
│ Attribute                   │ Authoritative Specification Value                                        │
├─────────────────────────────┼──────────────────────────────────────────────────────────────────────────┤
│ **Organization ID**         │ `ORG-001`                                                                │
│ **Legal Corporate Name**    │ Brayman Construction Inc.                                                │
│ **Trade / Operating Name**  │ Brayman Construction                                                     │
│ **Head Office Address**     │ 411 St. John Street, Merrickville, Ontario K0G 1N0                       │
│ **Primary Jurisdiction**    │ Ontario, Canada                                                          │
│ **Primary Currency**        │ `CAD` ($)                                                                │
│ **Default Labour Rate**     │ **$65.00 CAD per direct man-hour** (`pricing-policy.md`)                 │
│ **Default Pricing Policy**  │ **True Gross Margin @ 15.0%** ($P = \frac{C_{\text{dir}}}{0.85}$)        │
│ **Default Tax Treatment**   │ **13.0% HST** (Ontario Harmonized Sales Tax)                             │
│ **Historical Sources**      │ 20 Workbooks (Manifest: `historical-estimates-source-manifest.md`)       │
│ **Primary Work Types**      │ ICF Foundations, Slab-on-Grade / TES, Custom Residential, Renovations    │
│ **UAT Reference Project**   │ 3415 Roger Stevens Road, North Gower, ON (Detached Garage)               │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 23. Read-Only Existing Application Impact Audit

A comprehensive code audit of the entire existing codebase was conducted to confirm the current single-tenant baseline and design the zero-downtime additive migration path for Phase B:

### Existing Models Audited:
1. `app/models/project.py` (`Project`): Currently single-tenant; holds `client_id`, `name`, `status`, `address`. Lacks `organization_id`.
2. `app/models/client.py` (`Client`): Currently single-tenant; holds `name`, `email`, `phone`. Lacks `organization_id`.
3. `app/models/cost_item.py` (`CostItem`): Currently single-tenant catalogue. Lacks `organization_id`.
4. `app/models/assembly.py` (`Assembly`, `AssemblyItem`): Currently single-tenant recipe container. Lacks `organization_id`.
5. `app/models/estimate.py` (`Estimate`, `EstimateVersion`, `EstimateSection`, `EstimateLineItem`): Currently single-tenant estimating tree. Lacks `organization_id`.
6. `app/models/proposal.py` (`ProposalTemplate`, `Proposal`, `ProposalSection`, `ProposalLineItem`): Currently single-tenant proposal builder. Lacks `organization_id`.
7. `app/project_controls/models.py` (`ChangeOrder`, `ChangeOrderItem`): Scoped to `project_id`.
8. `app/plan_intelligence/models.py` (`DrawingPackage`, `DrawingRevision`, `PlanDocument`, `PlanPage`, `ProcessingAttempt`, `ProcessingResult`, `PlanAuditEvent`, `PlanSheet`, `PlanSheetPage`, `PlanSheetSuggestion`, `PlanScaleCalibration`, `PlanMeasurement`): All scoped directly or indirectly to `project_id`.

### Existing Routes Audited:
1. `app/routes/main.py` (`main` blueprint)
2. `app/routes/clients.py` (`clients` blueprint)
3. `app/routes/projects.py` (`projects` blueprint)
4. `app/routes/cost_library.py` (`cost_library` blueprint)
5. `app/routes/assemblies.py` (`assemblies` blueprint)
6. `app/routes/estimates.py` (`estimates` blueprint)
7. `app/routes/proposals.py` (`proposals` blueprint)
8. `app/routes/proposal_templates.py` (`proposal_templates` blueprint)
9. `app/project_controls/routes.py` (`project_controls` blueprint)
10. `app/plan_intelligence/routes.py` (`plan_intelligence` blueprint)

### Impact Findings:
- **Zero Runtime Impact in Phase A:** Phase A changes zero application code, introduces zero schema migrations, and alters zero routes.
- **Additive Evolution for Phase B:** When organization multi-tenancy is implemented in future Feature-Gated milestones, an additive schema migration will introduce the `organizations` table and add nullable `organization_id` foreign keys with a default data backfill migration assigning all existing records to `ORG-001` (Brayman Construction Inc.).

---

## 24. Implementation Status & Next Steps

### Governed Implementation Status:
- **Phase A Architecture:** Reviewed and Approved (2026-08-28).
- **Milestone 011 / FG-007 (Organization Foundation & Project Commercial Context):** Implemented and verified on `main` (`cb38d93`, migration `d0a1b2c3d4e5`).
- **FG-006 (Historical Estimate Ingestion Engine — Phase B):** Implemented and verified on `main` (`690d755`, migration `e1b2c3d4e5f6`).

### Governed Next Step:
- **FG-008** Labour Engine Phase B — **IMPLEMENTED / VERIFIED / LIVE-MIGRATED** (2026-08-29; Alembic `f2c3d4e5f6a7`). Foundation operational for UAT.
- **Next candidate:** [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) Organization-Calibrated Pricing Engine — **APPROVED FOR IMPLEMENTATION** (not implemented). Architecture: [organization-calibrated-pricing-engine-architecture.md](organization-calibrated-pricing-engine-architecture.md).
- **Blocked / Not Started (code):** Organization-Calibrated Pricing Engine implementation, ML-based commercial learning, cross-org benchmarking.

---

## 25. Related Documents

- [`platform-constitution.md`](../platform-constitution.md) — Highest-order platform law (Articles 1–12)
- [`platform-governance.md`](../platform-governance.md) — Feature Gate and decision authority
- [`pricing-policy.md`](../pricing-policy.md) — Governed pricing policy ($65/hr direct; 15% true gross margin)
- [`historical-estimates-source-manifest.md`](historical-estimates-source-manifest.md) — Provenance manifest of 20 historical workbooks
- [`historical-estimate-ingestion-architecture.md`](historical-estimate-ingestion-architecture.md) — Historical workbook audit & ingestion specification
- [`project-document-package.md`](project-document-package.md) — Authoritative estimate record & four core outputs
- [`quickbooks-integration.md`](quickbooks-integration.md) — QuickBooks export pipeline boundary
- [`CAR-001-calibai-product-architecture-reconciliation.md`](CAR-001-calibai-product-architecture-reconciliation.md) — CalibAi lifecycle reconciliation
- [labour-engine-phase-b-architecture.md](labour-engine-phase-b-architecture.md) — Labour Engine Phase B architecture (FG-008 IMPLEMENTED / VERIFIED / LIVE-MIGRATED; Alembic `f2c3d4e5f6a7`)
- [organization-calibrated-pricing-engine-architecture.md](organization-calibrated-pricing-engine-architecture.md) — Pricing Engine architecture (FG-009 **APPROVED FOR IMPLEMENTATION**, not implemented)
- [`testing/uat-reference-cases.md`](../testing/uat-reference-cases.md) — 3415 Roger Stevens Road UAT reference case

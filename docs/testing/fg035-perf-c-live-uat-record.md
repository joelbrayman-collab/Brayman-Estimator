# FG-035 PERF-C live UAT record (existing occupancy)

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-17 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Alembic | Live current = repository head **`a0b1c2d3e4f5 (head)`**. **No PERF-C migration.** |
| Freeze | [architecture/fg-035-perf-c-product-definition.md](../architecture/fg-035-perf-c-product-definition.md) |
| Architect disposition | **PERF-C LIVE UAT: PASS.** Existing-occupancy coverage **SUFFICIENT**. Additional synthetic UAT vessel **NOT REQUIRED**. Product correction **NONE REQUIRED**. |

## Scope

Prove sealed Company Attention against **existing** live ORG-001 occupancy. **READ-ONLY.** Do **not** create Projects. Do **not** mutate Projects **45–50**, Project **27**, EST-2026-0019, Estimate **28**, Version **34**, or any other live Project. Do **not** implement filtering, lifecycle, Home Office, Field Company Attention, People & Access, or Sensitive Financial. V1 **not rescored**.

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH-A/B/C/D IMPLEMENTED
PERF-A SEALED
PERF-B SEALED
PERF-C IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED
NO PERF-C FILTERING
NO PROJECT LIFECYCLE IMPLEMENTATION
CLOSE / LEARN / QB-T NOT AUTHORIZED
NO SCHEMA
V1 NOT RESCORED
```

## Git / Alembic

| Field | Value |
|-------|--------|
| HEAD / `origin/main` at UAT inspect | **`d6febfcac0687584f631987205282a8202fa99ef`** (`docs: pin FG-035 PERF-C SHA`) |
| Product PERF-C SHA | **`22fd30cd774fcf155ae69d7dcf99a44123d91409`** (`feat: implement FG-035 PERF-C company attention`) |
| Divergence at UAT inspect | **0 0** |
| Working tree at UAT inspect | **CLEAN** |
| Live current | **`a0b1c2d3e4f5 (head)`** unchanged |
| PERF alert tables | **none** (no attention/alert persistence) |
| Live `COMPANY_MANAGEMENT` grant count | **1** (unchanged) |

## Protected occupancy — unchanged

| Record | Identity / state |
|--------|------------------|
| Max project id | **50** |
| Project 27 | `40x80 Thickened-Edge Concrete Slab` |
| Estimate 28 | EST-2026-0019 Draft · Project **27** |
| Version 34 | version_number **1** · Draft · unlocked · subtotal **49872.94** · total **56356.42** |
| Projects 45–50 | existing FG-035 synthetic UAT vessels preserved |
| Live grants | **1** — Membership **1** / Joel Brayman / `COMPANY_MANAGEMENT` |
| Database mutation | **NONE** |
| Live UAT data created | **NONE** |

## Architect-accepted evidence

| Check | Result |
|-------|--------|
| Authorized viewer | Joel Brayman · Membership **1** · `COMPANY_MANAGEMENT` effective **YES** · `/company-attention` HTTP **200** |
| Ungrant deny | AUTH-B Membership **5** · `COMPANY_MANAGEMENT` effective **NO** · `/company-attention` HTTP **403** |
| Unauthenticated | login redirect **PASS** |
| Office nav (Joel) | Company Attention **present** after Schedule |
| Office nav (ungrant) | Company Attention **absent** |
| Field nav | Company Attention **absent** |
| Heading | exactly `Where does my business need attention?` |
| Organization assembly | **49** Projects considered |
| Projects with attention | **6** — **50**, **49**, **48**, **46**, **45**, **44** (newest-first) |
| Total facts | **27** |
| Unsupported fact types | **0** |
| Duplicate facts | **0** |
| EXTRA_WORK_NEEDS_REVIEW | **2** |
| LABOUR_GETTING_CLOSE | **1** |
| LABOUR_ALLOWANCE_USED | **0** (absent live; dedicated tests already cover) |
| LABOUR_OVER_ALLOWANCE | **1** |
| SCHEDULED_FINISH_PASSED | **9** |
| SCHEDULED_WORK_HAS_NO_APPROVED_TIME | **12** |
| SEQUENCE | **2** |
| Field firewall | **PASS** |
| Financial firewall | **PASS** |
| Mutation firewall | **PASS** (Review/navigation only) |
| Navigation destinations | **PASS** for available live types: Extra Work → Change Orders; labour → `#hub-labour`; finish / no-approved-Time / SEQUENCE → `#hub-schedule` |
| Performance | assembly ~**178–239 ms**; Joel page ~**266 ms**; no material issue |
| Coverage | **SUFFICIENT EXISTING OCCUPANCY** |
| Additional synthetic vessel | **NOT REQUIRED** |
| Product correction | **NONE REQUIRED** |

## Project-scope observation (not a PERF-C defect)

All **27** current live Company Attention facts came from existing synthetic/UAT Projects **50**, **49**, **48**, **46**, **45**, **44**. Project **48** produced **15 of 27** facts. Synthetic/UAT occupancy currently dominates the live Company Attention view.

Architect disposition:

- **NOT** a PERF-C fact-authority failure.
- **NOT** a PERF-C authorization failure.
- **NOT** a PERF-C performance failure.
- **NOT** a reason to invent PERF-C-specific filtering.

Record as:

```text
PROJECT LIFECYCLE / ACTIVE-ARCHIVED SCOPE
FUTURE GOVERNED PRODUCT DECISION
```

A later Project lifecycle may distinguish current/active operating work from completed/closed/archived/historical work, and separately accommodate governed test/UAT history. That decision is **not** defined here. Do **not** implement Active/Archived filtering, UAT-vessel filtering, or commercial-only filtering on Company Attention. PERF-C remains **organization-wide** under existing Project authority. Existing synthetic/UAT Projects are **preserved**.

## Firewalls preserved

People & Access **NOT IMPLEMENTED**. Sensitive Financial **NOT IMPLEMENTED**. Home Office **NOT IMPLEMENTED**. Field Company Attention **NOT IMPLEMENTED**. No additional live grants. No new PERF-C facts. No persistence. No migration.

## Scorecard

Governed V1 Readiness **65% / 4 of 11** (not rescored). Functional V1 Build **79% / 22 of 28** (not rescored). PERF-C is now **eligible** for subsequent Functional V1 Build score reconciliation. Architect reconciles after this seal.

## Stop

```text
PERF-C LIVE UAT: PASS
EXISTING-OCCUPANCY COVERAGE: SUFFICIENT
ADDITIONAL SYNTHETIC UAT VESSEL: NOT REQUIRED
PRODUCT CORRECTION: NONE REQUIRED
PERF-C: SEALED
FG-035: OPEN / PARTIAL
NO FILTERING IMPLEMENTED
NO LIVE DATA MUTATION
V1 NOT RESCORED
RETURN TO CHATGPT ARCHITECT
```

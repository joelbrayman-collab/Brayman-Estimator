# Brayman ICF Estimator V1 — Design Specification

**Date:** 26 September 2026  
**Product:** CalibraytAI  
**Classification:** Brayman Construction confidential — internal platform capability  
**Status:** Design approved in principle; implementation not authorized by this document

**Subsequent status (2026-10-09 manufacturer evidence):** Profile version 1 now holds unselected product records for the published standard and corner forms of Fox Blocks, Logix, Nudura, and BuildBlock, and for BuildLock as its own family. Logix 6.25 stays 6.25. No observation is a calculation factor. The 8-inch units and the quantity engine are unchanged. Fox 8-inch corner and corbel disagreements stay unresolved. This note does not add a core dropdown or a new calculable core.

**Subsequent status (2026-10-08 Fox product records):** Fox Blocks profile version 1 now keeps five product records beside the calculation units. The records store FOX-EC890, FOX-EC890CB, the series-page 8-inch corner, FOX-BL800, and the series-page 8-inch corbel, each with its own published measurements. Every observation is unselected. The 8-inch calculation units are unchanged, including the 0.145 cubic yard corner volume. The disagreements stay unresolved. A later selection must name the product record and the observation. This note does not select a factor, add a core dropdown, or change the quantity engine.

**Subsequent status (2026-10-08 contract identity):** Contract V1 accepts an exact positive decimal core token, including 6.25. The 8-inch quantity engine is unchanged. This note does not authorize a core dropdown or a quantity for a core whose facts are missing.

**Subsequent status (2026-10-08):** Product direction now requires manufacturer-specific core selection on the one ICF engine. A listed core calculates only from that core’s own verified facts. Logix 6.25 inches is not 6 inches. The body of this specification is unchanged. This note does not authorize implementation, a core dropdown, or a Contract V1 edit. Pinned Contract V1 still cannot store 6.25.

## 1. Purpose

Brayman ICF Estimator V1 will replace the ICF spreadsheet estimating work Joel currently performs for Ben. It will turn reviewed plan geometry or manual measurements into a complete, priced Brayman ICF estimate and preserve the evidence required to improve future estimates.

Success means Ben can select a project, provide or select the plans, confirm a short set of clearly presented choices, review CalibraytAI's proposed take-off, and generate both an internal cost breakdown and a customer-facing estimate quickly.

## 2. Access and product boundary

- Available only inside the authenticated CalibraytAI platform.
- Restricted to authorized Brayman Construction users in V1.
- Not displayed, linked, indexed or routed from the public CalibraytAI website.
- Manufacturer rules, Brayman production rates, costs, margins and historical evidence remain private.
- No public or downloadable standalone ICF calculator.
- This is part of the existing CalibraytAI estimating workflow, not a second estimating system.

## 3. Primary workflow

### Stage 1 — Project and plans

- Select an existing project or create one.
- Use plans already attached to the project or upload plans.
- Permit manual entry when plans are unavailable or unsuitable.
- Record the source plan and version used.

### Stage 2 — ICF setup

Required selections:

- Scope:
  - Foundation
  - Foundation + Main Floor
  - Foundation + All Floors
- Manufacturer:
  - StyroRail
  - Logix
  - Nudura
  - Fox Blocks
- Core size, default 8 inches.
- Concrete specification, default 25 MPa ICF mix.
- Foundation waterproofing.
- Brick/stone ledge requirement.

Normal Brayman defaults:

- StyroRail
- 8-inch core
- 25 MPa ICF mix
- RESISTO ICF Foundation Membrane
- Simpson Strong-Tie ICFVL ledger connectors at 16 inches on centre
- Anchor bolts at 36 inches on centre
- 10-foot 2×4 bottom plates with a 50% reusable-material allowance

### Stage 3 — Review plan take-off

CalibraytAI proposes, by floor:

- ICF wall segments, lengths and heights
- openings
- inside and outside corners
- brick/stone ledges
- gables and walls extending to rafters
- suspended-floor ledger connection lengths

The proposed geometry must be confirmed or corrected before final calculation.

### Stage 4 — Review materials

Show calculated and order quantities, packaging, waste and reuse allowances for all applicable materials.

### Stage 5 — Review labour and costs

Show labour tasks and hours, evidence source, materials, equipment, transportation, direct cost, true gross-margin price and HST.

### Stage 6 — Create estimate

- Save the reviewed versioned calculation.
- Add it directly to the project estimate.
- Produce an internal breakdown.
- Produce a customer-facing estimate.
- Preserve assumptions, overrides, plan version and approvals.

## 4. Architecture

### 4.1 Plan interpretation adapter

The plan-reading workflow proposes normalized ICF geometry. It does not own calculation rules. Manual measurements produce the same normalized geometry structure.

### 4.2 Manufacturer profiles

Manufacturer-specific facts are versioned data profiles, not duplicated calculator code. Each profile may define:

- product identifiers and available core sizes
- block dimensions and wall coverage
- standard, corner, brick-ledge and specialty units
- internal ties, webs, clips and connectors
- concrete-volume factors
- membrane defaults
- manufacturer reinforcement guidance
- packaging and order rounding

Initial rules:

| ICF system | Default membrane | Reinforcement default |
|---|---|---|
| StyroRail | RESISTO ICF Foundation Membrane | Approved manufacturer guidance when no engineered schedule is supplied |
| Logix | RESISTO ICF Foundation Membrane | Approved manufacturer guidance when no engineered schedule is supplied |
| Nudura | NUDURA waterproofing membrane | Approved manufacturer guidance when no engineered schedule is supplied |
| Fox Blocks | RESISTO ICF Foundation Membrane | Project schedule required until an approved default is established |

Core size remains consistent through the selected building scope in V1.

### 4.3 Universal ICF engine

The engine consumes reviewed geometry plus a manufacturer-profile version. It calculates quantities independently of prices.

Required results include:

- gross and net wall areas by floor
- standard, corner, brick-ledge and specialty blocks/forms
- concrete by wall section and total
- vertical and horizontal rebar
- lintel rebar and stirrups where applicable
- internal ties, clips and connectors
- Simpson Strong-Tie ICFVL components by floor at a visible default of 16 inches on centre
- anchor bolts at a visible default of 36 inches on centre
- individual anchor bolts and boxes, using a working default of 50 per box until supplier packaging is confirmed
- waterproofing membrane and order units
- window and door bucks
- 2×10 ledger material
- two bottom 2×4 runs, inside and outside, using 10-foot boards and a 50% purchase allowance because boards are reused
- visible waste and order rounding

Brick-ledge units replace the affected standard units and must not be added as duplicate wall coverage.

### 4.4 Pricing and estimate adapter

The adapter maps versioned quantities to the Brayman Cost Library and applicable supplier evidence. It adds labour, equipment, transportation, allowances, true gross margin and HST without altering the underlying quantity result.

Repricing must create a new priced result while preserving the original calculation and price evidence.

## 5. Detailed take-off scope

### Core calculated items

- ICF blocks/forms by type
- 25 MPa ICF concrete
- 10M and 15M rebar, plus other engineered sizes
- lintel reinforcement and stirrups
- internal ties, zip ties, clips and connectors
- Tapcons where applicable
- waterproofing membrane
- anchor bolts
- Simpson ICFVL components
- pressure-treated opening bucks
- 2×4×10 reusable bottom plates
- 2×10 ledger material
- brick/stone ledges

### Selectable related project items

- weeping tile
- pump truck
- stone slinger
- compactor
- Sonotubes
- conventional forms
- insulation
- wire mesh
- parging
- transportation
- other explicit project allowances

These options must be visible and deliberately included or excluded.

Plumbwall bracing is reusable site equipment and is not included as a consumed material quantity in V1.

## 6. Reinforcement and structural controls

- Engineered project requirements take precedence.
- Logix, Nudura and StyroRail may provide visible defaults based on approved manufacturer sources when no engineered schedule exists.
- Fox Blocks requires a project schedule until an approved default is established.
- The source of every rebar and connector schedule is displayed.
- Structural overrides require a reason and remain attached to the estimate record.
- Manufacturer documents and product profiles must be versioned and source-attributed.

## 7. Brayman labour model

Historical Brayman projects are the primary evidence. Manufacturer studies and external research are reasonableness checks only.

Labour is calculated by activity:

- layout and preparation
- block placement
- reinforcement and openings
- concrete placement
- stripping and cleanup
- waterproofing
- upper-floor and full-height complexity
- project-specific additions

The model must retain context including manufacturer, core size, scope, wall height, floors, openings, corners, ledges, reinforcement complexity, crew, season, access, pumping conditions and project size.

Initial accessible evidence includes the Mike Pratt source workbook, signed plans, labour benchmarking report, Michelle Steele/Kilby full-height ICF proposal and related Brayman estimates. The Mike Pratt record contains 200 original ICF hours for approximately 1,680 square feet of gross wall area, with a protected planning range of 220–240 hours. That record is evidence, not a universal rate.

## 8. Outputs

### Internal Brayman output

- plan and calculation versions
- scope and geometry by floor
- opening deductions
- detailed calculation and purchase quantities
- package rounding, waste and reuse allowances
- labour by activity and evidence source
- costs, equipment and transportation
- direct cost
- true gross-margin price
- HST and customer total
- assumptions, warnings, exclusions and overrides

### Customer-facing output

- clear ICF scope and included floors
- wall system and core size
- foundation and wall construction
- reinforcement
- waterproofing
- openings and ledges
- concrete placement
- included equipment and services
- price before HST, HST and total

Do not expose internal unit costs, production rates, margins, formulas, historical comparisons or internal allowances.

## 9. Review gates and warnings

Finalization requires confirmation of:

- scope
- manufacturer and core size
- source plan version
- geometry and openings
- brick/stone ledges
- rebar source
- waterproofing system
- optional items and exclusions
- labour allowance
- cost date and pricing status

Flag missing or unusual conditions, including incomplete geometry, unsupported products, absent reinforcement sources, missing Cost Library mappings, stale prices, manual overrides, unusual productivity and material totals outside comparable historical ranges.

An unresolved item may remain visibly budgetary when the authorized user records that status and reason.

## 10. Learning loop

Every completed project must be capable of improving the next estimate.

Capture and compare:

- estimated versus actual material quantities
- waste and returns
- estimated versus actual labour by activity
- planned versus actual equipment time
- estimated versus actual supplier cost
- expected versus actual duration
- expected versus achieved margin
- recorded causes of significant differences

Learning must remain contextual. Evidence from a foundation-only StyroRail job must not silently alter a full-height Logix model.

At project closeout, CalibraytAI produces:

- original estimate
- actual result
- material and labour variances
- explanatory project conditions
- suggested production-rate changes
- confidence and supporting-project count

Joel or Ben may approve a suggested rate for future use. Approval creates a new version of the Brayman production model. Original estimates, actuals and prior rates remain immutable.

This realizes the CalibraytAI lifecycle:

**PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN**

## 11. Mobile and desktop presentation

- Mobile uses one guided stage per screen, large controls and persistent Save and Continue.
- Desktop uses the same stages and may show the plan and take-off side by side.
- Defaults minimize typing but remain visible.
- Complex internal formulas are not exposed in the primary workflow.
- The user can inspect detail before finalization.

## 12. Testing and acceptance

Before release:

- verify all manufacturer-profile data against approved primary documentation
- create deterministic fixtures for each manufacturer and supported core size
- reconcile component quantities to totals
- validate Metric and Imperial equivalence
- compare engine results against known Brayman workbooks and plans
- test foundation-only, foundation-plus-main-floor and full-height cases
- test openings, corners, ledges, gables and multiple floors
- test packaging and rounding
- test engineered rebar precedence and overrides
- test labour evidence and pricing provenance
- test tenant and role restrictions
- test internal versus customer-output confidentiality
- test mobile and desktop workflows
- confirm no public route or public-site exposure

## 13. Exclusions from V1

- access by non-Brayman organizations
- public website calculator
- automatic ordering or purchase-order submission
- silent modification of engineered requirements
- unsupported manufacturer assumptions
- unrestricted autonomous changes to approved Brayman production rates

## 14. Implementation handoff

Implementation belongs in the authoritative CalibraytAI platform repository. The public Website source must not implement or expose this estimator. Before implementation, the platform workstream must inventory existing plan-ingestion, estimate, Cost Library, supplier-evidence, project, tenancy, role, calculation-contract and learning/calibration components, then produce an implementation plan that reuses those governed capabilities.
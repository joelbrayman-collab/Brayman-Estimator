# Project Element authority — future record

| Attribute | Value |
|-----------|--------|
| Status | **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT A PREFLIGHT / NOT IMPLEMENTED** |
| Updated | 2026-09-14 |
| Authority | Joel Brayman / ChatGPT Architect product-direction record during FG-024 TECH-C. Does **not** authorize schema, product code, or a Feature Gate. |
| Later work | After the current CONTRACT workstream, ChatGPT Architect will perform a bounded architecture preflight covering Project Element identity, baseline / organization / project-specific libraries, Activity, Time Entry (mobile-first / iPhone-primary), actual approval, Project Performance Profile, MONITOR variance, LEARN, QuickBooks-ready time export, organization/platform authority boundaries, and real iPhone UAT. |

This file records a **future** Time / Project Performance / MONITOR / LEARN direction only. It is **not** an ADR, not a Feature Gate, and not a preflight. TECH-C did **not** implement any of it. The 14 Sep 2026 Joel / Architect notes restated: (1) one CalibraytAI platform / multiple organization configurations; (2) Time Entry is primarily a field / iPhone experience and must be designed mobile-first. Those restatements did **not** change TECH-C scope and did **not** authorize implementation.

```text
ONE CALIBRAYTAI PLATFORM.
MULTIPLE ORGANIZATION CONFIGURATIONS.
THE SYSTEM OWNS THE INVARIANT ARCHITECTURE.
THE ORGANIZATION OWNS ITS GOVERNED CONFIGURATION.
NOT AUTHORIZED. NOT IMPLEMENTED.
```

## Core principle

CalibraytAI is one supported product. Contractor customization must not create different product architectures, tenant-specific codebases, custom schemas, custom workflow engines, or incompatible semantics.

- **Platform / system** owns invariant model, identity rules, lifecycle, relationships, permissions framework, APIs, reporting/learning semantics, schema/code, and upgrades.
- **Organization** owns governed configuration/data inside that common architecture.
- Organization-defined elements are **configuration data**, not custom product code.
- Organizations must not create custom executable logic merely by defining an element.

## Recorded conceptual model (names not decided)

Future architecture should investigate a governed three-level model:

**BASELINE → ORGANIZATION → PROJECT**

Conceptual flow:

**PROJECT → PROJECT ELEMENT → ACTIVITY → ACTUAL / TIME → MONITOR → LEARN**

Future project-related time remains:

**PROJECT → PROJECT ELEMENT → ACTIVITY → HOURS**

Project-related approved time must not become trusted ORG-ACTUAL / LEARN evidence without governed Project + Element + Activity attribution. Field workers should select from the elements applicable to that project without needing to know whether an element originated as baseline, organization, project-specific, or PLAN/PRICE-derived mapping.

Exact model names, tables, and roles are **not** authorized or decided here.

## Authority classes to investigate later

Use repository-consistent authority terminology. Do **not** implement these states from this record.

| Layer | Recorded intent |
|-------|-----------------|
| CalibraytAI BASELINE | Platform-provided reusable framework/default element/activity templates. Not automatically organization estimating standards. Changes are **platform product** decisions. A contractor cannot promote an organization element directly into the global baseline. |
| ORGANIZATION Element Library | Tenant-governed configuration: create / review / approve / activate-inactivate / map / version-supersede under later rules. Organization A’s elements do not create elements for organization B. |
| PROJECT-SPECIFIC | Governed identity for one project (estimating, time, actual-cost, MONITOR, LEARN evidence) without automatically entering the Organization Element Library. |
| PROJECT → ORGANIZATION promotion | Explicit organization approval required. LEARN may recommend; LEARN cannot approve. Exact role/permission is later work. |
| ORGANIZATION → PLATFORM promotion | No direct tenant-to-global promotion. Any baseline addition is a separate platform product/release decision. |
| ORG learning boundary | Brayman actuals → Brayman LEARN → human review → Brayman ORG-APPROVED. Do not silently transfer labour, cost, rates, pricing, or commercial intelligence across organizations. Cross-org benchmarking/pooling needs separate product, legal, privacy, consent, and governance treatment. |

Examples in the originating notes (`THICKENED-EDGE SLAB`, `EXISTING HERITAGE STONE FOUNDATION RESTORATION`, excavation/forming/reinforcing/placement splits) are **examples only**. Do **not** create those elements from this record.

## Supportability / subscription

All subscribers should continue to share common schema, application code, workflows, permission framework, API behavior, reporting engine, learning framework, and upgrade path. Avoid tenant-specific forks unless a future separately governed extension architecture explicitly permits them.

## Mobile-first Time Entry UX (non-negotiable; not implemented)

TIME ENTRY IS PRIMARILY A FIELD / iPHONE EXPERIENCE. It must be designed **mobile-first**. Do **not** design a desktop timesheet and later compress it onto a phone.

```text
MAXIMUM INTELLIGENCE BEHIND THE SCREEN.
MINIMUM EFFORT IN THE FIELD.
NOT AUTHORIZED. NOT IMPLEMENTED.
```

### Primary field flow (conceptual)

**TIME → PROJECT → PROJECT ELEMENT → ACTIVITY → HOURS → OPTIONAL NOTE → SUBMIT**

Project-related time retains the governed identity requirement **PROJECT → ELEMENT → ACTIVITY**. The field UX must make that requirement **fast**, not optional.

### Field design principles

Prioritize iPhone usability, one-handed use where practical, large touch targets, clear typography, minimal clutter/typing/scrolling, obvious current selection, fast numeric hours entry, simple correction before approval, clear save/submit confirmation, and reliable construction-site operation.

Avoid spreadsheet-style grids, tiny dropdowns, desktop tables compressed onto mobile, long forms, unnecessary metadata entry, uncontrolled free-text classification, and exposing system/learning complexity to workers.

### Intelligent selection

Once Project is selected, show only governed Elements applicable to that Project where practical. Once Element is selected, show applicable governed Activities where practical. The worker must not need to understand baseline vs organization vs project-specific origin, estimate mappings, performance metadata, LEARN classifications, or accounting mappings. The platform resolves that context behind the field interaction.

### Speed / recent context (convenience only)

Later UX may investigate active/recent Projects first, recent Element/Activity, repeat previous entry pattern, sensible date default, and today’s running total. These must **not** bypass required Project + Element + Activity attribution. Do **not** automatically submit inferred time.

### Today view (design deferred)

The field user should quickly see today’s submitted work (conceptual example: TODAY — 7.5 HOURS with project / element / activity / hours rows) so they can spot missing time, wrong project, wrong element, wrong activity, or wrong hours before approval. Exact layout is deferred.

### Complexity stays behind the UI

Workers enter only what they genuinely know/need to provide. CalibraytAI should automatically attach/reference governed context (project identity, element/activity identity/version, estimate relationship, relevant project-performance metadata, organization context, later cost/accounting mapping) where architecture supports it. Do not ask workers to re-enter metadata the system already knows.

### Approval (separate from field submit)

**SUBMITTED TIME → HUMAN REVIEW / APPROVAL → TRUSTED ACTUAL**

Only governed approved time should become authoritative ORG-ACTUAL evidence for MONITOR, performance analysis, LEARN/calibration, and QuickBooks-ready approved-time handoff. Exact approval UX/roles are deferred.

### Real iPhone UAT

The future Time workstream cannot close solely on desktop/browser unit tests. Real iPhone UAT is required before the complete Time capability closes, including project/element/activity selection, hours, optional note, submit, confirmation, today view, correction/edit, practical touch usability, readable layout, no horizontal-scroll dependence, and continuity after normal mobile navigation. Use existing Field Web UAT lessons/process where applicable.

### Complete future workstream (not this note’s authorization)

CONFIGURATION → PLAN/PRICE MAPPING → MOBILE TIME ENTRY → APPROVAL → ACTUALS → MONITOR → PROJECT PERFORMANCE → LEARN → HUMAN CALIBRATION → FUTURE ESTIMATING IMPROVEMENT → QUICKBOOKS-READY HANDOFF → REAL iPHONE / END-TO-END UAT

## Later preflight must first identify

WHAT ALREADY EXISTS in PLAN / PRICE / BUILD (scope, assembly, quantity, and related identities) · WHAT CAN BE REFERENCED · WHAT NEEDS A NEW IDENTITY

before any schema is authorized.

## Not authorized from this record

Baseline element library · Organization Element Library · project-specific elements · promotion workflow · activity taxonomy · Time UI / mobile Time page · Today view · time approval · actual labour · time entry · project-performance metadata · MONITOR expansion · LEARN · cross-org learning · QuickBooks time export · TECH-D · Native Signing.

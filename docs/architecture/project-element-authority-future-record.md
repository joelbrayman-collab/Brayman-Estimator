# Project Element authority — future record

| Attribute | Value |
|-----------|--------|
| Status | **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT A PREFLIGHT / NOT IMPLEMENTED** |
| Updated | 2026-09-14 |
| Authority | Joel Brayman / ChatGPT Architect product-direction record during FG-024 TECH-C. Does **not** authorize schema, product code, or a Feature Gate. |
| Later work | After the current CONTRACT workstream, ChatGPT Architect will perform a bounded architecture preflight covering Project Element identity, baseline / organization / project-specific libraries, Activity, Time Entry, actual approval, Project Performance Profile, MONITOR variance, LEARN, QuickBooks-ready time export, and organization/platform authority boundaries. |

This file records a **future** Time / Project Performance / MONITOR / LEARN direction only. It is **not** an ADR, not a Feature Gate, and not a preflight. TECH-C did **not** implement any of it. The 14 Sep 2026 Joel / Architect note restated the same direction (one CalibraytAI platform; multiple organization configurations; system owns invariant architecture; organization owns governed configuration). That restatement did **not** change TECH-C scope and did **not** authorize implementation.

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

## Later preflight must first identify

WHAT ALREADY EXISTS in PLAN / PRICE / BUILD (scope, assembly, quantity, and related identities) · WHAT CAN BE REFERENCED · WHAT NEEDS A NEW IDENTITY

before any schema is authorized.

## Not authorized from this record

Baseline element library · Organization Element Library · project-specific elements · promotion workflow · activity taxonomy · time entry · project-performance metadata · MONITOR expansion · LEARN · cross-org learning · QuickBooks time export · TECH-D · Native Signing.

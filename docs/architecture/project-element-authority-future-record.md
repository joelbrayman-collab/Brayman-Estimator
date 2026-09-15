# Project Element authority — future record

| Attribute | Value |
|-----------|--------|
| Status | **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT A PREFLIGHT / NOT IMPLEMENTED** |
| Updated | 2026-09-15 |
| Authority | Joel Brayman / ChatGPT Architect product-direction record during FG-024 TECH-C, with a **15 Sep 2026 visual Schedule addendum** recorded during FG-034 MAIL-B. Does **not** authorize schema, product code, or a Feature Gate. |
| Later work | After the current CONTRACT workstream, ChatGPT Architect will perform a bounded architecture preflight covering Project Element identity, baseline / organization / project-specific libraries, Activity, Time Entry (mobile-first / iPhone-primary), **visual Dynamic Project / Crew Scheduling**, actual approval, Project Performance Profile, MONITOR variance, LEARN, QuickBooks-ready time export, organization/platform authority boundaries, and real iPhone UAT. |

This file records a **future** Time / Project Performance / MONITOR / LEARN / **visual Schedule** direction only. It is **not** an ADR, not a Feature Gate, and not a preflight. TECH-C did **not** implement any of it. The 14 Sep 2026 Joel / Architect notes restated: (1) one CalibraytAI platform / multiple organization configurations; (2) Time Entry is primarily a field / iPhone experience and must be designed mobile-first. The **15 Sep 2026 visual calendar addendum** further defines future Dynamic Project / Crew Scheduling. Those restatements did **not** change FG-034 MAIL-B scope and did **not** authorize Schedule implementation.

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

## Visual Dynamic Project / Crew Scheduling (15 Sep 2026 addendum; not implemented)

Joel further defined the future V1 Dynamic Scheduling product during FG-034 MAIL-B. This is **product direction only**. It does **not** authorize a Feature Gate, schema, calendar UI, drag/drop, or iPhone Schedule screens.

```text
FUTURE VISUAL SCHEDULE.
PAPER MONTH CALENDAR ADVANTAGE PRESERVED.
FIVE-SECOND NEXT-MONTH UNDERSTANDING.
NOT AUTHORIZED. NOT IMPLEMENTED.
DO NOT IMPLEMENT FROM THIS ADDENDUM.
```

### Objective

Contractors use a paper month calendar because it gives immediate visual awareness of approximately the next month of work. CalibraytAI must preserve that advantage: highly visual, immediately understandable, interactive, dynamic, contractor-first. Digitizing calendar entries is not the product. The visual method must become **better** without becoming harder to understand.

### Five-second rule

A contractor should understand the next month of company workload within approximately **five seconds** of opening Schedule:

WHAT IS HAPPENING NOW? · WHAT IS NEXT? · WHAT IS COMING? · WHERE ARE WE BUSY? · WHERE ARE THERE CONFLICTS? · WHAT WORK IS NOT YET SCHEDULED?

If normal use requires opening multiple dialogs or interpreting technical scheduling terminology merely to understand the next month, the design has failed.

### Desktop default — month / forward view

Desktop is the **primary planning environment**. Later architecture/preflight must strongly evaluate **MONTH** as the default Schedule view: approximately **4–6 weeks** of company work at once, conceptually a highly intelligent digital wall calendar. Projects appear as large, legible visual bars/blocks across scheduled dates so overlap, duration, and upcoming work are visible without opening each project.

### Default detail level

Do not overload the default company calendar. Default company Schedule prioritizes **Projects + major milestones / major work phases**. Do not show every Activity for every Project simultaneously. Project Elements, Activities, crew assignments, dependencies, and performance information are **progressively disclosed** when a Project is selected/expanded. Preserve at-a-glance understanding.

### Desktop interaction

Later design should evaluate **direct manipulation** as the primary planning interaction: drag Project to move dates; drag edge to extend/shorten duration; drag Element to adjust a phase. Click/edit forms remain an accessible alternative. Dragging cannot be the only editing mechanism.

### Dynamic conflict intelligence

Schedule changes should identify conflicts in plain contractor language (examples: worker double-booked, crew double-booked, dependent work too early, project overlap, work outside expected sequence). Example: “Ben is scheduled on both Speakeasy and Smith Garage Wednesday.” Possible actions to evaluate later: KEEP SCHEDULE / MOVE OTHER WORK / REVIEW CONFLICT. Exact UX is deferred. Do **not** automatically move work without contractor confirmation.

### At-a-glance company pulse

Evaluate a compact secondary summary (ACTIVE JOBS / STARTING SOON / SCHEDULE CONFLICTS / UNSCHEDULED WORK). It must remain visually secondary to the calendar. Do not turn Schedule into a KPI dashboard.

### iPhone — same data, simpler representation

iPhone/mobile must provide a useful Schedule experience. Do **not** shrink the desktop planning board onto the phone. Same scheduling engine and records; different responsive presentation. Strongly evaluate **TODAY / WEEK / MONTH**.

- **TODAY:** Where am I working? What am I doing? Who am I working with? What is next? Large contractor-facing cards/rows.
- **WEEK:** Compact visual of active/upcoming work: current jobs, jobs starting, assignments, major phases, schedule changes — without desktop-style editing complexity.
- **MONTH is required to be evaluated as a core mobile view.** Joel wants someone like Ben to pull out an iPhone and quickly visualize approximately the next month. Preserve the paper-calendar mental model, simplified for the screen: visual, readable, navigational, read-mostly. Answer: what happens next week, when this project finishes, when the next starts, how busy we are three weeks from now. Tap a Project for detail. Do not show every Element/Activity label simultaneously.

Desktop Month is the full planning surface (interactive, drag/drop, resize, crew visibility, conflict management, project expansion). iPhone Month is a simplified visual overview with tap-for-detail and only limited/simple adjustment where later architecture proves useful. TODAY/WEEK on iPhone may carry more operational assignment detail. **No data fork.**

### Time / MONITOR / LEARN connection

Schedule remains connected to future Time Entry. A scheduled assignment may **suggest** Project / Element / Activity when a field worker records time; the worker confirms attribution. **SCHEDULE DOES NOT CREATE ACTUAL TIME.**

Preserve the already-recorded chain: estimated duration/labour → scheduled duration → actual time/duration → MONITOR → LEARN → better future estimate and better future schedule. Later recommendations of typical actual durations require **human acceptance**. Do not silently rewrite schedules or estimating standards.

### Future UAT principle

The future Scheduling workstream must include a simple contractor usability test: show Schedule without explaining it. Ask what is happening this week, what is coming next, and what the next month looks like. The contractor should answer quickly from the visual presentation. If substantial explanation is required, Schedule UX is not complete. Desktop and iPhone representations must both be tested.

## Later preflight must first identify

WHAT ALREADY EXISTS in PLAN / PRICE / BUILD (scope, assembly, quantity, and related identities) · WHAT CAN BE REFERENCED · WHAT NEEDS A NEW IDENTITY

before any schema is authorized.

## Not authorized from this record

Baseline element library · Organization Element Library · project-specific elements · promotion workflow · activity taxonomy · Time UI / mobile Time page · Today view · time approval · actual labour · time entry · **Schedule UI / visual calendar / drag-drop / iPhone TODAY-WEEK-MONTH Schedule** · project-performance metadata · MONITOR expansion · LEARN · cross-org learning · QuickBooks time export · TECH-D · Native Signing.

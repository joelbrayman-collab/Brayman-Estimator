# Project Element authority — future record

| Attribute | Value |
|-----------|--------|
| Status | **FUTURE / RECORDED / COMPLETE FOR PRODUCT-DIRECTION RECORDING.** Subsequent **2026-09-15:** [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**; [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**; TAX/WBS **IMPLEMENTED**; SCOPE **IMPLEMENTED**; TIME **IMPLEMENTED**. SCH architecture **PREFLIGHT COMPLETE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED** ([fg-035-sch-dynamic-scheduling-preflight.md](fg-035-sch-dynamic-scheduling-preflight.md)). SCH / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. Sibling PRE-UAT record [interactive-help-voice-and-user-manual-future-record.md](interactive-help-voice-and-user-manual-future-record.md) **does not interrupt this loop**. Historical body below is not rewritten. |
| Updated | 2026-09-15 |
| Authority | Joel Brayman / ChatGPT Architect. Origin: FG-024 TECH-C. **15 Sep 2026 complete product-direction consolidation** recorded after FG-034 MAIL-B **PASS**. Does **not** authorize schema, product code, a Feature Gate, or AUTH-D. |
| Later work | After FG-034 and the current CONTRACT workstream, ChatGPT Architect will perform a bounded architecture preflight covering the **one closed operational / learning loop**: Project Types / Elements / Activities; visual Dynamic Project / Crew Scheduling; field Time Entry; time approval; labour actuals; labour-budget and schedule alerts; Project Performance; MONITOR forecasting; Change Order / Extra Work lineage; Closeout data quality; LEARN evidence quality; estimate and schedule calibration; QuickBooks-ready approved time; and the mandatory platform-wide Contractor Language + UX E2E Audit before Brayman/Ben real-world UAT. |

This file is the **single consolidated future record** for that loop. It is **not** an ADR, not a Feature Gate, and not a preflight. Nothing in this file is implemented. The 15 Sep 2026 visual-calendar addendum is retained below and is **subsumed** by the complete loop, not a second product.

**Actual governed baseline at this recording (do not reconstruct AUTH slices):** starting HEAD / `origin/main` **`e641e19709d0a9b093cc7774943a23af95284339`** (docs-only §72 remainder / §§73–104). Product MAIL-B **`6dfc2e940456cf9c292c700e07840fac5d871df4`**. FG-034 **OPEN / PARTIAL**. MAIL-A / AUTH-A / AUTH-B / AUTH-C / MAIL-B **IMPLEMENTED / PASS**. AUTH-D **NOT STARTED**. FG-033 **CLOSED / OPERATIONAL FOR UAT**. V1 **not rescored** (**60% / 4 of 11**). Alembic **`f2a3b4c5d6e7 (head)`**.

The 15 Sep 2026 product-direction recording is now **complete** through §105. Visual-calendar direction and the complete Time / Schedule / Performance / MONITOR / LEARN / Change Order / Extra Work / Closeout / language-audit direction are **one** future workstream, not competing products. This file is product-direction / future-architecture **input**. It is **not** implementation authorization, a Feature Gate, an ADR, schema/migration authorization, a V1 rescore, or proof that any future feature is implemented. Next product workstream remains **FG-034 AUTH-D**, which this record does **not** authorize.

```text
ONE CLOSED OPERATIONAL / LEARNING LOOP.
NOT SEPARATE UNRELATED FEATURES.
NOT AUTHORIZED. NOT IMPLEMENTED.
DO NOT IMPLEMENT FROM THIS RECORD.
DO NOT BEGIN AUTH-D FROM THIS RECORD.
```

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

## Complete closed operational / learning loop (15 Sep 2026; not implemented)

Do **not** design Time, Schedule, Performance, MONITOR, and LEARN as unrelated features. They are one loop:

WHAT WE ESTIMATED → WHAT WE SCHEDULED → WHO WE ASSIGNED → WHAT WORK WAS ACTUALLY PERFORMED → WHAT TIME WAS LOGGED → WHAT TIME WAS APPROVED → HOW THE PROJECT ACTUALLY PROGRESSED → WHERE LABOUR / SCHEDULE VARIED → WHY IT VARIED → WHAT IT DID TO PROJECT PERFORMANCE → WHAT CALIBRAYTAI LEARNED → WHAT CALIBRAYTAI RECOMMENDS NEXT TIME → HUMAN ACCEPTS OR REJECTS.

The loop must improve **future estimates** and **future schedules**. LEARN recommends. Humans decide. Never silently rewrite estimates, schedules, or estimating standards.

### Governed work hierarchy

Every meaningful unit of work must resolve through:

**ORGANIZATION → PROJECT → PROJECT ELEMENT → ACTIVITY**

Later architecture must also support/inherit where relevant: Project Type; project attributes / performance drivers; Estimate / Estimate Version; estimated labour; scheduled work; worker / crew; scope origin; Change Order; actual approved labour; actual duration; production quantity / rate; Closeout review; LEARNING evidence quality.

Do **not** hard-code the architecture around Thickened Edge Slabs. TES is one example. The model must support a broad range of contractor Project Types, Elements, and Activities.

### Contractor configuration / SaaS integrity

Contractors must be able to add Elements / Activities that matter to how they operate. Do **not** fork CalibraytAI per contractor.

**ONE PLATFORM · ONE CODEBASE · ONE UPGRADE PATH** with governed organization-level configuration:

**CALIBRAYTAI BASELINE → ORGANIZATION EXTENSIONS → PROJECT-SPECIFIC USE**

Later architecture must determine governance for Project Types, Elements, Activities, performance attributes, production-rate bases, crew structures, and schedule conventions without creating incompatible contractor-specific products.

### Field Time Entry

Used primarily on iPhone. Fast, clean, touch-first, low friction. Every **approved** labour hour must resolve to **PROJECT → ELEMENT → ACTIVITY**. The worker should not manually enter information CalibraytAI can safely derive. Support worker, date, hours, Project, Element, Activity, plus only the minimum additional context genuinely required.

Attribution is mandatory because the same actual labour evidence must feed payroll / QuickBooks, project actuals, MONITOR, labour-budget alerts, schedule performance, forecasting, Closeout, LEARN, future estimating, and future scheduling. **Do not create duplicate labour-entry systems.** Workers enter time once.

**SCHEDULED TIME IS NOT ACTUAL TIME.** Never fabricate actual labour from scheduled work. A scheduled assignment may **suggest** Project / Element / Activity; the worker confirms.

### Time approval

Distinguish **FIELD SUBMITTED TIME** from **APPROVED ACTUAL LABOUR**. Approved time is the authoritative labour actual for MONITOR, forecasting, LEARN, and QuickBooks / payroll handoff. Do not treat unapproved field entries as final labour actuals. Exact approval workflow is deferred to later preflight.

### Dynamic Project / Crew Scheduling (required V1 capability; not implemented)

Do **not** build a generic calendar. Build a **contractor production schedule** using the **same** Project / Element / Activity structure as Time / MONITOR / LEARN. No calendar-only taxonomy.

See the visual Schedule section above for the paper month-calendar, five-second rule, desktop 4–6 week month, default Projects + major phases, drag/drop plus forms, conflict intelligence, company vs Project Hub Schedule (same data, no fork), and iPhone TODAY / WEEK / MONTH.

Additional scheduling rules from the 15 Sep 2026 complete record:

- Scheduling must be easy to change on the fly (weather, customer delay, material delay, inspection delay, crew availability, earlier completion, extended work, Change Order). Preserve enough schedule-change history for MONITOR, LEARN, and operational accountability without excessive event noise.
- Assignment to **individual workers and/or crews** (Ben, Matt, Ben + Matt, Concrete Crew, Unassigned). Do not require every contractor to formally use crews.
- **Lightweight dependencies** (example: Excavation → Forms → Reinforcing → Pour → Strip). If upstream work moves: identify affected downstream work, warn, offer adjustment. Do **not** build Primavera / Microsoft Project complexity unless later architecture demonstrates it is necessary.
- One organization **SCHEDULE** surface is the primary office planning view. Each Project Hub **Schedule** is a Project-filtered view of the **same** records.

### Estimate vs actual labour

At Project, Element, and useful Activity levels, later architecture must determine: estimated labour hours; actual approved labour hours; labour hours remaining; labour variance; percent of labour allowance consumed. Example: Forms estimated 40 hrs, actual 43 hrs, variance +3 hrs.

The visual Schedule should show meaningful labour variance without becoming an analytics dashboard (example: Speakeasy — Forms 43 / 40 hrs, 3 hrs over). The contractor should quickly understand ON TRACK / APPROACHING ALLOWANCE / OVER ESTIMATE / PROJECTED OVERRUN. Exact visual treatment is deferred.

### Labour and schedule alerts

The contractor must receive meaningful alerts when labour or schedule performance moves outside governed thresholds. Examples to evaluate: approaching labour allowance; labour allowance exceeded; projected labour overrun; schedule duration exceeded; unplanned work accumulating; crew / schedule conflict; material project forecast change.

Alerts must be threshold / event based, deduplicated, acknowledgeable, and contractor-facing. Do not create noisy per-hour notifications. Later architecture should evaluate defaults such as 80% and 100% of estimated labour consumed, plus predictive thresholds. Exact defaults deferred. Allow organization configuration where sensible.

**One governed performance/alert engine** must feed Schedule, Project Hub, MONITOR, and Needs Attention. Do not create competing warning calculations.

### Needs Attention

Evaluate one contractor-facing **NEEDS ATTENTION** summary (labour overrun, projected overrun, schedule delay, crew conflict, unplanned work, extra work without Change Order, unsigned Change Order, other meaningful exceptions). Do not create competing notification systems.

### Progress vs labour consumption

Raw labour consumption alone is not sufficient for predictive warning. Evaluate work progress vs labour allowance consumed (example: 80% of labour allowance used, 55% of work complete → projected overrun). Do not burden field workers with constant percentage entry. Evaluate simple progress states such as NOT STARTED / IN PROGRESS / SUBSTANTIALLY COMPLETE / COMPLETE, and determine whether any percentage model is genuinely useful.

### Project forecasting and gross margin

MONITOR should eventually forecast final labour (example: estimated 420 hrs, actual to date 286 hrs, projected final 468 hrs, projected overrun 48 hrs). Use deterministic / project-performance logic before unnecessary AI. Do not claim prediction precision beyond the evidence.

Where existing pricing/cost architecture supports it, approved labour actuals should update **internal** projected project financial performance (estimated gross margin vs current forecast gross margin). Do **not** change governed estimate pricing. Do **not** expose internal margin to customers. This records future MONITOR expansion; it does **not** reopen [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md).

### Production rates and crew / Project Type performance

LEARN should preserve meaningful labour hours / unit where appropriate (hours per linear foot, square metre, cubic metre, tonne, fixture). Do not hard-code construction units globally. Production-rate basis belongs to the governed work taxonomy / organization configuration.

Preserve enough worker/crew context to learn whether crew configuration affects production (effective crew size, typical duration, what to schedule next time). Objective: **operational learning**. Do **not** create employee rankings or surveillance scoring.

Actual labour plus cost/revenue architecture should eventually help answer which Project Types perform well, which Elements repeatedly run over, where estimating is consistently inaccurate, and which work creates margin pressure. Internal organization intelligence only.

### Estimate and schedule calibration

LEARN should compare new estimates with comparable historical evidence (example: you estimated 64 forming hours; comparable completed projects average 71; suggested 70–72). Possible later actions: USE SUGGESTION / KEEP MY ESTIMATE / REVIEW COMPARABLE PROJECTS.

The same evidence should improve future scheduling (example: scheduled forming 2 days; comparable actual 2.7; suggested 3 days). Human accepts or rejects. Do **not** silently alter future schedules or estimates.

## Change Order scope lineage through Closeout / LEARN data quality (15 Sep 2026 continuation; not implemented)

This section supersedes the PURPOSE-list placeholder. Existing Change Order **records** remain authoritative. The Change Order **document family** remains [change-order-document-family.md](change-order-document-family.md) **FUTURE / NOT IMPLEMENTED**. Exact internal names are deferred. Exact Extra Work contractor-facing terminology is deferred to the later Contractor Language + UX E2E Audit.

```text
ORIGINAL SCOPE IS IMMUTABLE HISTORICAL EVIDENCE.
CHANGE ORDERS MODIFY THE CURRENT AUTHORIZED PROJECT.
THEY DO NOT REWRITE THE ORIGINAL ESTIMATE.
NOT AUTHORIZED. NOT IMPLEMENTED.
```

### Scope origin invariant

Change Order work must never disappear into original Project scope in a way that corrupts performance evidence. Every relevant Element, Activity, scheduled work, Time Entry, actual, performance record, and learning record must retain sufficient **SCOPE ORIGIN**.

Later architecture must conceptually distinguish:

- **ORIGINAL**
- **CHANGE_ORDER** (retain the specific Change Order identity)
- **PENDING_CHANGE / EXTRA_WORK**

### New Element created by Change Order

If a Change Order introduces genuinely new work, that work becomes legitimate Project work but permanently retains source scope **CHANGE ORDER** and the specific Change Order identity. Example: CO-003 Exterior Equipment Pad may introduce Equipment Pad → Excavation / Forms / Rebar / Pour. Field workers should normally choose Project → Element → Activity; CalibraytAI should **inherit** Change Order lineage automatically. Do not make workers repeatedly select a Change Order when the selected work item already determines lineage.

### Change Order modifies an existing Element

If original Forms is 40 estimated hours and CO-004 adds 12 additional forming hours, **do not** rewrite the original Forms estimate from 40 to 52. Preserve:

- ORIGINAL FORMS: 40 estimated hours
- CO-004 ADDITIONAL FORMS: 12 estimated hours
- CURRENT AUTHORIZED FORMS: 52 estimated hours

Actual labour must be capable of attribution to ORIGINAL FORMS vs CO-004 ADDITIONAL FORMS even if both roll up visually under FORMS.

### Three performance views

Future MONITOR must support truthful separation, not one collapsed variance:

1. **ORIGINAL CONTRACT PERFORMANCE** — original estimated labour vs actual approved labour attributable to original scope.
2. **CHANGE ORDER PERFORMANCE** — Change Order estimated additions/reductions vs actual approved labour attributable to those changes.
3. **CURRENT AUTHORIZED PROJECT PERFORMANCE** — original scope + authorized Change Orders vs total actual approved labour.

### LEARNING integrity — original vs change

LEARN must not interpret customer-directed scope growth as failure of the original estimate. Example: original Forms 40 estimated / 39 actual; CO additional Forms 12 estimated / 14 actual; current authorized 52; current actual 53. Correct: original 1 hour under; Change Order 2 hours over; current project 1 hour over. Incorrect: “original estimate was 13 hours over.” Future architecture must prevent the incorrect interpretation.

### Change Order reductions / removed scope

Change Orders may remove work. Example: original Decorative Concrete 24 estimated hours; CO-006 removes Decorative Concrete (−24 authorized hours); current authorized 0 hours. Do **not** delete the original Element / estimate evidence. Preserve original scope, authorized reduction, and current authorized scope. LEARN must understand **WORK WAS REMOVED**, not that the original estimate never existed.

### Extra Work — field reality and field rule

A customer may tell a worker to move a drain and add another; the worker may do the work and record hours against an existing Drainage / Plumbing Element. No software can reliably know in every case that those hours resulted from changed scope. Do **not** pretend CalibraytAI can eliminate this human-behaviour problem. The solution must combine simple field capture + training/discipline + variance detection + Closeout review + LEARNING data quality.

Field operating rule: **if you are doing work that was not part of what you were originally sent to do, record it as Extra Work.** Field workers are **not** responsible for contractual entitlement, formal Change Order requirement, pricing, commercial approval, or final scope classification. Their responsibility is to flag: this is different / extra work.

### iPhone Extra Work UX

Future iPhone Time Entry must make Extra Work capture extremely easy. Strongly evaluate a prominent **+ EXTRA WORK** action. Example: Project Speakeasy → Extra Work → description “Move drain and add second drain” → hours. Do not require the field worker to create a formal Change Order, create taxonomy, price the work, understand scope-lineage architecture, or answer multiple administrative questions. Correct attribution must be easier than burying the hours in a vaguely related existing category.

### Training / discipline

Software cannot replace field discipline. Future Brayman / contractor rollout must include: **do not bury extra work in the original job.** If the customer asks to add, remove, move, or change something outside the work you were sent to perform: use Extra Work. This is an operational adoption requirement. Do not respond to the human-discipline problem by making Time Entry administratively heavy.

### Pending Change / Extra Work

Real work may begin before a formal Change Order exists. Future architecture must support a governed temporary attribution conceptually equivalent to PENDING CHANGE or EXTRA WORK. Time recorded here must **not** be falsely attributed to original scope.

### Needs Attention — Extra Work without a Change Order

When approved labour accumulates against Extra Work / Pending Change and no formal Change Order is linked, CalibraytAI should alert: extra work is accumulating without a Change Order. Potential later actions: CREATE CHANGE ORDER / LINK TO EXISTING CHANGE ORDER / RETURN TO ORIGINAL SCOPE. Exact copy/UX deferred. Do **not** automatically create a Change Order. The contractor decides.

### Linking / reclassification

When pending extra work is later associated with a formal Change Order, preserve history. Do **not** destructively rewrite the record as though the CO had existed before the work occurred. Retain evidence that time was originally recorded as Extra Work / Pending Change, then linked/reclassified to a specific Change Order, by actor, at timestamp. Current reporting may then attribute the labour to the formal Change Order. Historical provenance remains intact.

### Misattributed Extra Work and variance as second defence

The harder case is extra work recorded against an existing ORIGINAL Element. CalibraytAI cannot know this with certainty at entry time. Do **not** automatically reclassify unusual labour as Extra Work. MONITOR detects meaningful unexplained variance. Closeout gives the contractor an opportunity to explain/reclassify it. LEARN must remain cautious until the variance is understood.

Example: Drainage estimated 16 hrs, actual 24 hrs, comparable historical range 15–18 hrs. CalibraytAI must **not** automatically conclude that future Drainage estimates should be 24 hours. Identify **MATERIAL / UNEXPLAINED VARIANCE** for contractor attention. Exact thresholds deferred.

### Project Closeout — data-quality gate

Project Closeout becomes the final data-quality checkpoint before Project performance becomes trusted LEARN evidence. At Closeout, show **material exceptions**. Do **not** require review of every normal line item. Example: Forms 4 hrs over; Drainage 8 hrs over; Concrete 2 hrs under; CO-003 3 hrs over.

For material unexplained variance, evaluate contractor-simple explanations conceptually such as: EXTRA WORK / SCOPE CHANGE · ORIGINAL WORK TOOK LONGER · OTHER KNOWN REASON · NOT SURE. Exact wording deferred to the language audit. Do not expose statistical/technical terminology.

If the contractor determines at Closeout that labour originally recorded against original scope was actually Extra Work, allow governed reclassification/linking. Preserve original Time Entry, original attribution, review/reclassification actor, timestamp, new current attribution, and Change Order linkage where applicable. Do not erase the historical fact that the worker originally recorded the time differently.

### LEARN data confidence and protection

Not every completed Project should contribute equally to LEARN. Evaluate a simple internal evidence-quality model, conceptually **CLEAN / REVIEWED / UNRESOLVED** (exact names deferred):

- **CLEAN:** scope attribution is consistent and no material unexplained variance remains.
- **REVIEWED:** material variance was reviewed/explained by the contractor.
- **UNRESOLVED:** material variance remains unexplained.

A large unexplained labour overrun must **not** automatically become a new estimating or scheduling standard. LEARN should preferentially use CLEAN + REVIEWED comparable evidence. UNRESOLVED evidence should be treated cautiously and may be excluded or down-weighted from calibration recommendations according to later architecture. Human acceptance remains mandatory before organization standards change.

A Project should not enter the trusted LEARN corpus merely because its status becomes complete. Conceptual flow: PROJECT WORK COMPLETE → PERFORMANCE REVIEW → MATERIAL EXCEPTIONS RESOLVED / CLASSIFIED → PERFORMANCE EVIDENCE QUALITY ESTABLISHED → LEARN ELIGIBILITY. Keep this lightweight. Only meaningful exceptions should require contractor attention.

### Change Order → Schedule

Authorized Change Orders may affect labour, duration, sequence, crew assignment, and project finish date. When a CO adds work, Scheduling should identify potential impact (example: CO-005 adds 32 estimated labour hours; current planned finish Oct 16; potential revised finish Oct 20). CalibraytAI may recommend UPDATE SCHEDULE / KEEP CURRENT SCHEDULE / REVIEW IMPACT. Do **not** silently move work.

If a CO creates a new Element, it may appear as new scheduled work. If a CO modifies an existing Element, additional work may extend that Element or appear as separately attributable scheduled work. The underlying schedule must retain scope lineage. The default Month calendar must **not** become visually overloaded with CO technical detail. Detailed lineage should be available through Project/work expansion.

Labour alerts must understand the scope layer. Example: original Forms 40 estimated / 39 actual; CO-004 Forms 12 estimated / 14 actual. Do **not** alert “ORIGINAL FORMS 13 HOURS OVER.” Correct current information may include: original Forms on track; CO-004 additional Forms 2 hours over; current authorized Forms 1 hour over overall.

### Change Order commercial performance and LEARNING

Where existing pricing/cost architecture permits, future MONITOR / Closeout should distinguish original contract performance from Change Order performance (original estimating accuracy, CO estimating accuracy, small-change setup/mobilization effects, margin pressure from changed work, schedule impact of changes). Keep internal commercial performance off customer-facing surfaces.

Change Orders should become useful learning evidence in their own right: whether COs consistently consume more labour than estimated; which kinds of changes run over; whether small changes carry disproportionate setup/mobilization labour; how much schedule extension particular changes actually create; whether future CO labour estimates should include learned adjustments. Human decides whether recommendations become organization standards.

Where measurable quantities exist, preserve production-rate evidence for both original-scope work and Change-Order work. Do not exclude Change Order labour from learning. Where context matters, LEARN should be able to distinguish whether production rates differ between planned original work and later changed work.

### QuickBooks / payroll lineage

Approved labour exported toward QuickBooks / payroll must preserve internal CalibraytAI evidence: Project, Element, Activity, Scope Origin, Change Order where applicable, even if the external system cannot represent every dimension directly. Export must not destroy CalibraytAI’s learning/performance evidence.

### Project Closeout summary and management signal

Project Closeout must eventually summarize: original scope; authorized Change Orders; pending / unresolved Extra Work; original labour performance; Change Order labour performance; current total project performance; schedule performance / effects; material variance explanations; LEARNING evidence quality. A Project should not silently close into trusted LEARN evidence with material unresolved Pending Change / unexplained labour. Exact close-block vs warning policy is deferred.

Over time CalibraytAI may provide organization-level operational insight such as: projects with unresolved labour variance; extra work captured before formal CO; recurring extra-work attribution problems; material exceptions requiring Closeout review. This exists to improve operational discipline. Do **not** create employee ranking / punitive surveillance.

### Three-layer data quality control

1. **FIELD DISCIPLINE** — make Extra Work easy to capture.
2. **CALIBRAYTAI MONITORING** — detect meaningful abnormal/unexplained labour and schedule variance.
3. **CLOSEOUT REVIEW** — contractor resolves/classifies material exceptions before LEARN treats the evidence as trusted historical performance.

### Scope lineage belongs to the work structure

Do **not** solve Change Order integrity merely by tagging timesheets. Scope lineage belongs at the **work structure** level. Element / Activity / scheduled work should carry or inherit scope origin. Time Entry then inherits that lineage wherever possible. This preserves evidence through ESTIMATE → SCHEDULE → TIME → ACTUALS → MONITOR → CLOSEOUT → LEARN.

## LEARN comparability, calibration, alerts, and field simplicity (15 Sep 2026 final continuation; not implemented)

This section records the remainder of §72 plus §§73–86. It does **not** reopen FG-023 or FG-025. It does **not** authorize implementation.

```text
LEARN RECOMMENDS. HUMAN DECIDES.
COMPARE LIKE WORK WITH LIKE WORK.
ONE GOVERNED ALERT / PERFORMANCE ENGINE.
FIELD TIME ENTRY STAYS SIMPLE.
NOT AUTHORIZED. NOT IMPLEMENTED.
```

### Comparable performance

LEARN must compare genuinely comparable work. Do not compare Projects merely because they share a broad label. Later architecture must determine how comparable evidence is selected using appropriate combinations of Project Type, Element, Activity, quantity / production basis, relevant Project attributes, scope origin, crew context where meaningful, and other governed performance drivers. Purpose: **like work with like work**. Do not hard-code TES-only comparability.

### Organization-specific learning

CalibraytAI should learn how the specific contractor actually performs work. Brayman historical performance should inform Brayman recommendations. The future SaaS architecture must maintain organization boundaries. Do not allow one contractor's actual labour/performance data to silently rewrite another contractor's standards. Any future cross-organization benchmarking would require separate governance and is **not** authorized by this record.

### LEARN recommendation model

LEARN recommends. Human decides. Potential recommendation targets include estimated labour, production rate, scheduled duration, crew assumptions, and other governed organization standards. Example: current estimate 64 forming hours; comparable reviewed evidence average 71 hours; suggested 70–72 hours. The contractor may USE SUGGESTION / KEEP CURRENT ESTIMATE / REVIEW COMPARABLE WORK. Exact UX deferred. Never silently rewrite an Estimate.

### Schedule learning

The same historical evidence should improve future schedules. Example: planned forming duration 2 days; comparable actual duration 2.7 days; suggested 3 days. The contractor decides whether to apply the recommendation. Do not silently move or lengthen scheduled work.

### Calibration provenance

If a contractor accepts a LEARN recommendation that changes an organization standard, preserve sufficient provenance: what standard changed, prior value, new value, recommendation/evidence basis, actor, timestamp. Do not silently overwrite organizational calibration. Later architecture must determine whether this belongs in existing calibration/history structures or requires a bounded new model.

### LEARN evidence quality and eligibility

The conceptual evidence-quality states CLEAN / REVIEWED / UNRESOLVED must influence LEARN eligibility. Later architecture must determine which evidence is eligible, which is down-weighted, which is excluded from recommendations, and how resolved/reclassified variance changes evidence quality. Do not treat all completed Projects as equally trustworthy.

### One governed alert / performance engine

Do not independently calculate the same condition in Schedule, Project Hub, MONITOR, and Needs Attention. The underlying condition should be calculated once and presented appropriately on multiple surfaces. Examples: approaching labour allowance; labour allowance exceeded; projected overrun; schedule overrun; crew conflict; unplanned Extra Work; unlinked Change Order work; material forecast change.

The contractor should be alerted when a meaningful threshold/event occurs. Later architecture must determine V1 delivery mechanisms. At minimum evaluate in-platform Needs Attention, Project Hub, and Schedule visual state, and where later notification infrastructure supports it appropriately, transactional notification. Do not create alert spam. Alerts should be meaningful, deduplicated, acknowledgeable, and escalated only when the condition materially changes or crosses another threshold.

Labour-budget example: Speakeasy Forms estimated 40 hrs, approved actual 32 hrs → 80% consumed may identify APPROACHING LABOUR ALLOWANCE. If actual becomes 43 hrs, identify LABOUR ALLOWANCE EXCEEDED / 3 HRS OVER. If the work is Change Order scope, the alert must retain that lineage. Do not attribute CO overrun to original scope.

### Progress / forecasting

Future MONITOR must determine the simplest useful progress model for forecasting. Do not force field workers to continuously estimate percent complete. Strongly evaluate simple contractor-owned progress signals/milestones. Objective: determine when labour consumption is materially ahead of work progress, providing earlier warning than waiting for estimated hours to be fully consumed.

### Project Performance Profile

At appropriate Project lifecycle points, CalibraytAI should maintain a governed Project Performance Profile sufficient to summarize: original estimated labour; current authorized labour; approved actual labour; original scope variance; Change Order variance; pending/unresolved Extra Work; scheduled duration; actual duration; schedule variance; crew context; production rates where meaningful; forecast; Closeout explanations; evidence quality. Exact model/storage design is deferred. Do not duplicate authoritative data unnecessarily.

### QuickBooks / payroll readiness

Approved field time should be capable of becoming the authoritative labour record for later QuickBooks/payroll handoff. Workers should not have to enter the same hours again. Preserve internally: worker, date, hours, Project, Element, Activity, Scope Origin, Change Order where applicable, even if the external accounting system cannot represent all dimensions. Export state must be distinguishable from approval state. Conceptually evaluate SUBMITTED / APPROVED / READY FOR EXPORT / EXPORTED. Exact lifecycle deferred.

### Time Entry / Schedule relationship

Scheduled assignment may make Time Entry faster. Example: Ben is scheduled today on Speakeasy → Forms → Layout; when Ben records time, CalibraytAI may suggest those values; Ben confirms. Schedule does not create actual time. A worker must still record/confirm actual hours worked.

### Field simplicity

The intelligence in this future record must **not** make field Time Entry complicated. Most analytics and lineage should be derived/inherited. Field worker experience should remain approximately: WHAT PROJECT? WHAT WORK? HOW MUCH TIME? plus EXTRA WORK when necessary. Do not expose scope origin codes, learning states, estimate versions, Change Order internals, production-rate calculations, or forecast algorithms to ordinary field workers.

## Future UAT principles (not implemented)

These are later workstream acceptance principles. They do **not** authorize implementation or begin Brayman/Ben UAT.

**Scheduling:** show Schedule without explanation. Ask: what is happening this week? what is coming next? what does the next month look like? The contractor should answer quickly from the visual presentation. Desktop and iPhone representations must both be evaluated. If substantial explanation is required, Schedule UX is not complete.

**Time / Extra Work:** field UAT must prove that a worker can quickly record normal Project / Element / Activity time and record Extra Work without understanding Change Order accounting or LEARN architecture. Correct behaviour should be easier than incorrect attribution.

**MONITOR:** contractor UAT must prove that Ben can quickly identify what is on track, what is approaching labour allowance, what is over, what is forecast to overrun, what is delayed, what Extra Work needs attention, and what Change Order work is affecting performance, without interpreting technical analytics.

**LEARN:** recommendations must be understandable, evidence-based, explainable, and optional. Ben should understand what CalibraytAI recommends, why, which comparable work supports it, and what happens if he accepts it. LEARN must not silently alter standards.

## Complete future workstream sequencing

Current recorded sequence (not current authorization):

1. Finish FG-034 (AUTH-D remains).
2. Architect complete Time / Schedule / Project Performance / MONITOR / LEARN workstream.
3. Implement that complete workstream in bounded governed slices.
4. Complete BUILD / Closeout integration required by the loop.
5. Complete remaining V1 functionality / runtime hardening.
6. Platform-wide Contractor Language + UX E2E Audit.
7. Brayman / Ben real-world UAT (desktop; iPhone/mobile; deferred physical-device checks; real operational workflow).
8. Correct — correct defects discovered during real-world UAT; preserve governed scope; retest affected functionality; do not treat UAT defects as an excuse for unrelated scope expansion.
9. Complete final E2E regression — after UAT corrections, run the complete governed automated suite; re-exercise critical E2E workflows affected by corrections; confirm desktop, mobile/responsive, office, field, customer-facing, document-output, security, tenant isolation, artifact custody, and data integrity remain coherent. Physical-device checks performed during Brayman / Ben real-world UAT should be recorded truthfully. Do not claim tests that were not actually performed.
10. Complete final V1 governance / completion audit — one bounded final audit against actual V1 completion authority: what is COMPLETE, what remains PARTIAL, what is deferred beyond V1, what is operational for production/UAT, what gates can truthfully close, what documentation requires final reconciliation. Do not rely on stale historical completion percentages. Use owning Feature Gates / ADRs / current-state authority.
11. Rescore V1 — only at this final governed stage, rescore against the actual completion register. Do not preserve historical **60% / 4 of 11** merely because it was previously pinned. Score from actual completed evidence. Every COMPLETE package must satisfy its owning completion criteria. Do not inflate completion because code exists. This record does **not** rescore V1 now.
12. Final production readiness review — before declaring V1 ready, verify the platform can actually be handed to Brayman / Ben for normal use. At minimum confirm the final state of PLAN, PRICE, CONTRACT, BUILD, MONITOR, LEARN, Dynamic Scheduling, Time Entry, Time Approval, Change Orders, Extra Work, Closeout, Native Signing, Account Recovery, Transactional Email, runtime dependencies, backup/recovery, desktop UX, iPhone/mobile UX, customer-facing workflows, generated documents, QuickBooks-ready handoff where included in V1, contractor-language audit, and real-world UAT findings. Do not introduce new product scope during this review. Identify genuine blockers only.
13. V1 close — if and only if governed completion evidence supports it, declare CalibraytAI V1 production ready using repository-native closure terminology. Record final V1 score, closed/open/deferred gates, known post-V1 items, real-world UAT result, production/runtime requirements, final live pin, and final test evidence. If a genuine V1 blocker remains, do **not** declare V1 complete; identify the blocker and return to the appropriate governed workstream.

Do not begin implementation of the loop until the future preflight has resolved the entire loop coherently. This recording exercise is **closed**. Next product workstream remains FG-034 AUTH-D, which this record does **not** authorize.

## Platform-wide Contractor Language + UX E2E Audit (mandatory later; not implemented)

Joel established this as a **mandatory V1 closure workstream** before Brayman / Ben real-world UAT. It was first authorized for **recording only** during FG-034 AUTH-B and is consolidated here. It is **not** a new Feature Gate. It does **not** reopen or close [FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md). It does **not** authorize another FG-025 slice. Exact copy is **not** authorized by this record.

```text
CONTRACTOR LANGUAGE + UX E2E AUDIT.
MANDATORY BEFORE BRAYMAN / BEN REAL-WORLD UAT.
NOT AUTHORIZED. NOT IMPLEMENTED.
DO NOT BEGIN FROM THIS RECORD.
```

**Timing:** after remaining V1 functionality is substantially complete and **before** Brayman / Ben real-world UAT. Exact sequence: **Complete future workstream sequencing** above (steps 1–13 complete).

**Objective:** every normal user-facing surface is simple, straightforward, contractor-facing, consistent, and non-technical across desktop, iPhone/mobile, customer-facing surfaces, and generated documents. No normal user should need to understand CalibraytAI’s technical architecture to operate CalibraytAI.

**Illustrative inventory** (the later audit must discover the complete live surface list): login; Forgot Password / Account Recovery; office navigation; Project Hub; PLAN; PRICE; estimates; Construction Estimate; CONTRACT; contracts; Native Signing; Change Orders; BUILD; Field Web; Time Entry; Time Approval; Schedule; Project Schedule; Company Schedule; MONITOR; LEARN; Closeout; suppliers; uploads; historical data; QuickBooks handoff; settings; organization configuration; Project Types / Elements / Activities; performance configuration; empty / loading / warning / error / success / confirmation states; buttons; status badges; tooltips; customer signing pages; PDFs / generated customer documents.

**Jargon:** internal engineering terms must not leak into ordinary contractor UX without a genuine contractor-facing reason. Inspect/remove from ordinary UX unless context requires otherwise: `authority_class`, snapshot, artifact, hash, candidate, selector, gate, feature gate, event, epoch, runtime, schema, migration, synthetic, provenance, object/record identity, Alembic, technical status/error codes. These may remain internally. Do not mechanically replace words. Translate system state into contractor meaning.

**Contractor test for every screen:** Where am I? What is happening? What do I need to do? What happens next? Prefer action language (Create Estimate, Send for Signature, Record Time, Add Extra Work, Approve Time, Add Change Order, View Contract, Close Project) over implementation-oriented operations.

**Terminology dictionary:** later audit must establish and enforce one vocabulary (examples: Project, Customer, Construction Estimate, Contract, Change Order, Project Element, Activity, Time, Actual, Schedule, Estimate, Monitor, Learn). One concept must not acquire different names merely by moving between modules. Internal model names do not control customer-facing terminology.

**Status language:** internal lifecycle values may remain precise internally; contractor presentation should explain practical state (example: internal `APPROVED_FOR_SIGNATURE` may present as Ready to Send if accurate). Do not change underlying lifecycle semantics merely to improve copy. Use presentation mapping.

**Errors / warnings:** every user-facing failure should answer what happened and what to do next. Do not expose raw technical exception codes as the primary message. Fail-closed behavior must remain fail-closed. Plain language must not weaken security or governance.

**Desktop + iPhone:** one E2E audit, one product vocabulary. Responsive presentation may shorten supporting copy; meaning must stay consistent.

**Customer vs office:** customers must not see internal office terminology merely because the same model powers both surfaces. Native Signing is an important example: same engine, different appropriate presentation.

**Documents:** review Construction Estimate, Contract, Change Order, executed/signing completion, and other V1 customer outputs as part of the same language standard. Do not alter governed commercial/legal document bodies merely as a copy-edit without owning-feature authority.

**Workflow simplicity:** the audit may identify UX complexity, not merely prose (too many statuses, unclear primary action, duplicate actions, hidden next step, excessive explanation, technical diagnostics dominating useful information, desktop workflow compressed badly onto mobile). Material workflow redesign remains separately governed. Do not silently redesign architecture during a language audit.

**Automated protection:** later implementation should add bounded regression where valuable (protected contractor-facing titles, prohibited technical terms on normal customer surfaces, terminology mappings, desktop/mobile presence of primary actions, customer/office presentation separation). Do not create brittle tests for every sentence.

**Close criteria:** cannot close from a file grep alone. Required: complete user-facing surface inventory; prose, terminology, action/button, status, and error/warning review; desktop, responsive/mobile, customer-facing, and document-output walkthroughs; automated regression; complete E2E workflow walkthrough. Final question: could a competent contractor use this platform without needing to understand how CalibraytAI is engineered? Required answer: **YES**.

**Recorded sequence (not current authorization):** see **Complete future workstream sequencing** above (steps 1–13 complete).

## Later preflight must first identify

WHAT ALREADY EXISTS in PLAN / PRICE / BUILD (scope, assembly, quantity, and related identities) · WHAT CAN BE REFERENCED · WHAT NEEDS A NEW IDENTITY

before any schema is authorized.

When FG-034 is complete and ChatGPT Architect authorizes the future Time / Schedule / Performance / MONITOR / LEARN preflight, that preflight must resolve E2E:

- Project Type authority
- Element authority
- Activity authority
- contractor extension points
- project performance attributes
- frozen Estimate relationships
- original scope immutability
- current authorized scope
- scope origin
- CO-added Elements
- CO modification of existing Elements
- CO reductions/removals
- Extra Work / Pending Change
- linking/reclassification history
- Time inheritance
- Time approval
- worker/crew assignment
- dynamic visual Schedule
- desktop Month planning board
- iPhone Today / Week / Month
- schedule history
- lightweight dependencies
- conflict detection
- labour budget alerts
- schedule alerts
- progress vs labour
- forecasting
- gross-margin forecast
- original vs CO performance
- production rates
- Closeout performance review
- LEARN evidence-quality classification
- LEARN eligibility after Closeout
- comparable-project / comparable-work selection
- organization-specific learning evidence
- production-rate evidence
- crew-context evidence
- original-scope vs Change-Order learning separation
- unresolved-variance treatment
- estimate calibration recommendations
- schedule-duration calibration recommendations
- human accept / reject of recommendations
- calibration provenance/history
- approved-time QuickBooks/payroll readiness
- preservation of Project / Element / Activity / Scope lineage through export
- one governed alert/performance engine
- Needs Attention integration
- Project Hub integration
- Company Schedule integration
- Project Schedule integration
- desktop Month / 4–6 week planning board
- iPhone Today
- iPhone Week
- iPhone Month
- responsive desktop/mobile functional relationship
- complete Project Closeout → LEARN handoff
- complete E2E desktop/mobile UAT
- contractor adoption / field-training requirements
- data-quality protection against misattributed Extra Work

Do not begin implementation until that preflight has resolved the entire loop coherently.

## Not authorized from this record

Baseline element library · Organization Element Library · project-specific elements · promotion workflow · activity taxonomy · Time UI / mobile Time page · Today view · time approval · actual labour · time entry · **Schedule UI / visual calendar / drag-drop / iPhone TODAY-WEEK-MONTH Schedule** · crew assignment product · conflict engine · labour-budget alerts · Needs Attention · MONITOR forecast expansion · LEARN · estimate/schedule calibration · Change Order scope lineage product · Extra Work / Pending Change product · Extra Work iPhone action · Closeout performance review · LEARN evidence-quality states · Contractor Language + UX E2E Audit implementation · cross-org learning · QuickBooks time export · AUTH-D · a new Feature Gate · ADR from this record · V1 rescore from this record · TECH-D reopen · Native Signing reopen.

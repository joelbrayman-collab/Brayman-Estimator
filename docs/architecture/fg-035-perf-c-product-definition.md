# FG-035 PERF-C — Company Attention product definition / owner-decision freeze

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED.** Freeze body below remains the owner-decision contract. |
| Date | 2026-09-17 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Parent | PERF-B **SEALED** ([fg-035-perf-b-implementation-preflight.md](fg-035-perf-b-implementation-preflight.md)). Product PERF-B **`dcde4adfe4a475932b7f144b0220b2b60e4bd75c`**. Pin **`1b80d244e3efb0c65d3a02dd247d923dfd95166c`**. PERF-A **SEALED** ([fg-035-perf-a-implementation-preflight.md](fg-035-perf-a-implementation-preflight.md)). |
| Desktop sibling | [v1-desktop-contractor-experience-product-direction.md](v1-desktop-contractor-experience-product-direction.md) **RECORDED / NOT IMPLEMENTED**. Home Office is a **later, broader** contractor operating experience. It is **not** Company Attention. |
| Authorization seam | Separate freeze [company-management-access-domain-seam.md](company-management-access-domain-seam.md) **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. PERF-C must **not** ship until that seam is separately implemented and proven. |
| Schema | **NONE.** No attention table. No acknowledgement / resolution / escalation state. If implementation analysis later concludes persistence is required: **STOP AND RETURN TO ARCHITECT**. |
| Baseline | HEAD / `origin/main` **`1b80d244e3efb0c65d3a02dd247d923dfd95166c`**. Alembic **`f9b0c1d2e3f4 (head)`**. |
| V1 | **NOT RESCORED** (**60% / 4 of 11**). PERF-C definition alone is **not** a scoring event. |

**Subsequent status (2026-09-18 CORE CLOSE owner freeze):** [core-close-project-lifecycle-product-direction.md](core-close-project-lifecycle-product-direction.md) **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. V1 operating lifecycle is **ACTIVE / CLOSED** (no ARCHIVED third state). PERF-C may later consume shared current-operating-Project authority **without** reopening sealed fact types. Do **not** invent a PERF-C-only filter. This freeze remains the PERF-C owner-decision contract and is **not rewritten**.

**Subsequent status (2026-09-17 PERF-C LIVE UAT / SEAL):** PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED**. Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. Architect disposition: live UAT **PASS**; existing-occupancy coverage **SUFFICIENT**; additional synthetic vessel **NOT REQUIRED**; product correction **NONE REQUIRED**. Evidence [testing/fg035-perf-c-live-uat-record.md](../testing/fg035-perf-c-live-uat-record.md). Organization-wide Project-scope observation is **VALID** and is **not** a PERF-C defect; recorded as **PROJECT LIFECYCLE / ACTIVE-ARCHIVED SCOPE / FUTURE GOVERNED PRODUCT DECISION**. **Subsequent (2026-09-18):** that future decision is now frozen as CORE CLOSE **ACTIVE / CLOSED**; this historical seal sentence is **not rewritten**. No filtering implemented. No live data mutation. PERF-A / PERF-B remain **SEALED**. FG-037 remains **CLOSED**. FG-035 remains **OPEN / PARTIAL**. Official V1 **65% / 4 of 11** (not rescored). Secondary Functional V1 Build **79% / 22 of 28** (not rescored; PERF-C now **eligible** for later Functional Build reconciliation). This freeze remains the owner-decision contract.

**Subsequent status (2026-09-17 PERF-C Slice A COMMIT / PUSH / SHA-PIN):** PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-UATed**. Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. Office `/company-attention`. Requires `COMPANY_MANAGEMENT`. No schema. No live UAT data. Dedicated **13 passed**. Focused **115 passed**. Full suite **1226 passed**, 4366 warnings, **610.51s**, exit **0**. PERF-A / PERF-B remain **SEALED**. FG-037 remains **CLOSED**. Official V1 **65% / 4 of 11** (not rescored). Secondary Functional V1 Build **79% / 22 of 28** (not rescored). This freeze remains the owner-decision contract.

**Subsequent status (2026-09-17 PERF-C Slice A implementation):** PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-UATed**. Service `app/services/company_attention.py`. Office `/company-attention`. Requires `COMPANY_MANAGEMENT`. No schema. No live UAT data. Dedicated **13 passed**. Focused **115 passed**. Full suite **1226 passed**, 4366 warnings, **610.51s**, exit **0**. PERF-A / PERF-B remain **SEALED**. FG-037 remains **CLOSED**. Official V1 **65% / 4 of 11** (not rescored). Secondary Functional V1 Build **79% / 22 of 28** (not rescored).

**Subsequent status (2026-09-17 People & Access freeze):** [people-and-access-product-direction.md](people-and-access-product-direction.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Future contractor-facing administration of Domain B grants. PERF-C remains **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Subsequent [FG-037](../feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION**. This freeze is **not rewritten**. Do **not** implement Company Attention from that record.

```text
FG-035 PERF-C:
DEFINED
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
NO SCHEMA
NO MIGRATION
NO NEW ADR
NO NEW FEATURE GATE
V1 NOT RESCORED
PERF-A SEALED
PERF-B SEALED
NO HOME OFFICE
NO FIELD COMPANY ATTENTION
NO JOB-TITLE RBAC
COMPANY/MANAGEMENT SEAM DEFINED / NOT IMPLEMENTATION-AUTHORIZED
NO FINANCIAL PERMISSIONS
NO BANK / CASH / PAYROLL
NO MONITOR MONEY
NO CLOSE
NO LEARN
NO QB-T
```

This file is the frozen PERF-C **owner-decision** contract. It is **not** an implementation preflight. Do **not** implement Company Attention, Home Office, Field Company Attention, permission architecture, financial permissions, MONITOR money changes, CLOSE, LEARN, or QB-T from this file.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | PERF-A labour and PERF-B Project Needs Attention on Hub `#hub-labour`. Derived DTO from `assemble_project_performance` / `assemble_project_attention` in `app/services/project_performance.py`. Items already carry `project_id`. No company aggregation. No Company Attention surface. |
| **Intended (this freeze)** | Owner decisions in §§2–16 **ACCEPTED**. Company Attention is defined as the company/business-level attention layer. Initial factual scope is sealed PERF-B Project attention facts, organization-wide. Dedicated office/management **Company Attention** surface is defined, **not implemented**. **Not implementation-authorized.** |
| **Future (not this freeze)** | Implementation preflight (separate prompt). Home Office. Tomorrow readiness. Review + Notify Team. Week Ahead. Company/Management seam **implementation** (separate governed slice; freeze [company-management-access-domain-seam.md](company-management-access-domain-seam.md)). Sensitive-financial facts / redaction. Bank / cash / payroll. CLOSE. LEARN. QB-T. Unresolved items in §17. |

---

## 2. Frozen owner decisions

| ID | Decision | Freeze |
|----|----------|--------|
| 1 | Contractor question | **ACCEPTED.** Exact question: **Where does my business need attention?** Business-level attention. Initial governed factual scope remains bounded by authorities actually implemented and approved. Do **not** manufacture new business-attention authorities merely because the question is broader. |
| 2 | Purpose | **ACCEPTED.** Company/business-level attention layer. Initial PERF-C consumes governed Project attention facts already established by sealed PERF-B. **Not** a new risk engine. PERF-A remains Project labour-performance authority. PERF-B remains Project Needs Attention authority. |
| 3 | Surface | **ACCEPTED.** Dedicated contractor-facing **Company Attention** office/management surface. Do **not** make Schedule the owner. Do **not** equate Company Attention with Home Office. Later Home Office **may consume** Company Attention and other governed facts. This freeze does **not** design layout, navigation chrome, or URL. |
| 4 | Initial fact authority | **ACCEPTED.** Consume **only** sealed PERF-B attention fact types via the existing structured attention DTO seam, including `project_id`. Do **not** reopen PERF-A or PERF-B. |
| 5 | Derived / read-only | **ACCEPTED.** Derived read-only. No persisted PERF-C attention authority. No attention table. No acknowledgement / resolution / escalation state. No migration. If persistence later appears necessary: **STOP AND RETURN TO ARCHITECT.** |
| 6 | Field App | **ACCEPTED.** **NO COMPANY ATTENTION IN THE FIELD APP.** Explicit product decision. Field remains the governed operational worker experience. Do **not** add a Company Attention screen, section, card, or navigation destination to Field as part of PERF-C. Field-originating governed facts may still contribute through existing SCOPE / TIME / SCHEDULE / PERF authorities. This firewall concerns the **application surface**, not the origin of underlying facts. Do **not** alter sealed SCH-D Field behaviour. |
| 7 | Identity vs surface | **ACCEPTED.** Permissions follow the authenticated user and the contractor’s explicit authorization — **not** the device being used. Application surfaces remain intentionally bounded. A contractor/manager (for example Ben) may have permission to access Company Attention through the office/management CalibraytAI experience, including on a mobile device. That permission does **not** cause Company Attention to appear inside the Field App. Do **not** implement responsive/mobile office behaviour from this file. Record the distinction only. |
| 8 | Permission domains | **ACCEPTED as owner law.** Explicit contractor-controlled boundaries between **A. PROJECT / OPERATIONAL**; **B. COMPANY / MANAGEMENT**; **C. SENSITIVE FINANCIAL**. Minimum seam freeze: [company-management-access-domain-seam.md](company-management-access-domain-seam.md) (**DEFINED / NOT IMPLEMENTATION-AUTHORIZED**). Do **not** implement job-title RBAC. Do **not** implement the seam or schema from this PERF-C file. |
| 9 | Contractor controls permissions | **ACCEPTED.** The contractor / company owner controls who may access company and sensitive business information. Do **not** assume a generic title (admin, manager, supervisor, employee) automatically confers access to every information category. Do **not** design that architecture here. |
| 10 | Project / Company / Financial firewall | **ACCEPTED.** **PROJECT / OPERATIONAL ACCESS DOES NOT AUTOMATICALLY CONFER COMPANY ATTENTION ACCESS.** **COMPANY ATTENTION ACCESS DOES NOT AUTOMATICALLY CONFER ACCESS TO SENSITIVE FINANCIAL INFORMATION.** **SENSITIVE FINANCIAL ACCESS REQUIRES SEPARATELY GOVERNED, CONTRACTOR-CONTROLLED AUTHORIZATION.** A user may eventually have Project access without Company Attention; Company Attention without sensitive financial detail; sensitive financial access only when separately authorized. Exact future matrix remains separately governed. |
| 11 | Sensitive-information warning | **ACCEPTED as future principle.** When future functionality allows the contractor to grant access to sensitive financial/business information, CalibraytAI must clearly warn that the permission exposes sensitive information (bank accounts, balances, cash flow, payroll-sensitive information). The warning informs. The contractor decides. Preserve WARNINGS INFORM. HUMANS DECIDE. Do **not** implement this warning now. |
| 12 | Attention fact vs underlying information | **ACCEPTED as future-facing principle.** An attention fact and permission to view the underlying sensitive information are **not** necessarily the same authority. Future Company Attention may eventually consume governed sensitive business-attention facts. If so, presentation must respect contractor-controlled permissions. Company Attention must **not** become an accidental route around sensitive-information permissions. Exact future redaction / visibility model remains unresolved and separately governed. Do **not** design it here. |
| 13 | Current financial boundary | **ACCEPTED.** Initial PERF-C adds **no** financial-attention facts. Initial PERF-C remains based on sealed PERF-B Project attention facts. MONITOR remains current money authority. The broader question is intentionally capable of supporting future governed attention sources. That future direction is **not** current implementation authority. |
| 14 | Quiet positive | **ACCEPTED.** When there are no current attention facts: **Nothing needs attention right now.** No synthetic health score, grade, risk score, or mandatory severity classification. |
| 15 | Operating scope | **ACCEPTED.** Initial PERF-C scope is **organization-wide**. Preserve the future operating-scope seam. Do **not** implement Division, Operating Unit, scope selector, new RBAC, or cross-organization visibility. Organization tenancy remains hard. |
| 16 | Firewalls | **ACCEPTED.** PERF-C does **not** currently implement Home Office, Tomorrow readiness, Review + Notify Team, Week Ahead, Field Company Attention, bank integration, cash flow, payroll, financial permissions, MONITOR expansion, CLOSE, LEARN, QB-T, Division / Operating Unit, acknowledgement workflow, or resolution workflow. |

---

## 3. Contractor questions (keep separate)

| Product | Question |
|---------|----------|
| PERF-A | How are we doing on labour **for this Project**? |
| PERF-B | Is there something about **this Project** I should look at? |
| **PERF-C** | **Where does my business need attention?** |
| Home Office (later, not PERF-C) | What is most useful to this contractor **right now**? |

PERF-C is a **business-level** attention concept. Its **initial** governed factual scope remains bounded by authorities actually implemented and approved (sealed PERF-B). Do **not** manufacture new business-attention authorities merely because the contractor question is broader.

Home Office remains a later, broader contractor operating experience that may consume Company Attention and other governed facts. Do **not** equate the two.

PERF-C must **not** become an AI risk engine, prediction engine, persisted alert system, red/yellow/green health score, progress engine, forecast engine, or blocking workflow.

No opaque score. No severity number. No AI judgment. No persisted alert rows.

---

## 4. Fact authority — consume sealed PERF-B only

PERF-A remains Project labour-performance authority ([fg-035-perf-a-implementation-preflight.md](fg-035-perf-a-implementation-preflight.md)).

PERF-B remains Project Needs Attention authority ([fg-035-perf-b-implementation-preflight.md](fg-035-perf-b-implementation-preflight.md)).

PERF-C **consumes** those governed Project attention facts at business/company level. It does **not** recalculate labour 80%/100%/over, Extra Work lineage, scheduled finish, no-approved-Time, or SEQUENCE.

Consume the existing structured attention output (`attention.items` / `attention.positive` / `attention.positive_title`), including `project_id` on every item.

Sealed PERF-B fact types (initial PERF-C set; do **not** extend in this freeze):

| Key | Contractor title |
|-----|------------------|
| `EXTRA_WORK_NEEDS_REVIEW` | Extra work needs review |
| `LABOUR_GETTING_CLOSE` | Labour getting close |
| `LABOUR_ALLOWANCE_USED` | Labour allowance used |
| `LABOUR_OVER_ALLOWANCE` | Labour over allowance |
| `SCHEDULED_FINISH_PASSED` | Scheduled finish passed |
| `SCHEDULED_WORK_HAS_NO_APPROVED_TIME` | Scheduled work has no approved Time |
| `SEQUENCE` | existing SCH SEQUENCE copy |

Quiet company state when there are no current attention facts: **Nothing needs attention right now.**

Do **not** add in this freeze:

- new severity models
- new risk scoring
- unsigned Change Order alerts
- new Schedule warning types
- crew-overlap promotion
- USER-conflict promotion
- unassigned-upcoming-work facts
- new financial calculations
- MONITOR money facts
- cash/payroll facts

`PREDECESSOR_UNSCHEDULED` remains Schedule-only. Unassigned upcoming work remains **not** a PERF-B fact and is **not** a PERF-C fact.

MONITOR remains current money authority. `assemble_monitor_v1` must **not** import PERF.

Initial PERF-C adds **no** financial-attention facts. Initial PERF-C remains based on sealed PERF-B Project attention facts.

The broader contractor question **Where does my business need attention?** is intentionally extensible for future **governed** business-attention sources. That future extensibility is **not** implementation authority.

---

## 5. Company Attention surface boundary

Dedicated contractor-facing **Company Attention** office/management surface.

- Do **not** implement that surface from this file.
- Do **not** make Schedule / `/schedule` the owner of Company Attention.
- Do **not** equate Company Attention with Home Office.
- Do **not** add Company Attention to the Field App.

Later Home Office may consume Company Attention facts. That does **not** merge Home Office into PERF-C.

Navigation from an attention item to the relevant Project / existing surface may exist later. Navigation does **not** acknowledge, resolve, mutate work, move Schedule, create Time, create Change Orders, or change SCOPE. Warnings remain informational.

---

## 6. Field App firewall

```text
NO COMPANY ATTENTION IN THE FIELD APP.
```

Field remains the governed operational worker experience.

Do **not** add a Company Attention screen, section, card, or navigation destination to Field as part of PERF-C.

Field-originating governed facts may still contribute through existing SCOPE / TIME / SCHEDULE / PERF authorities. This firewall concerns the **application surface**, not the origin of the underlying facts.

Do **not** alter sealed SCH-D Field behaviour.

---

## 7. Identity vs application surface

```text
PERMISSIONS FOLLOW THE AUTHENTICATED USER AND THE CONTRACTOR'S
EXPLICIT AUTHORIZATION — NOT THE DEVICE BEING USED.

APPLICATION SURFACES REMAIN INTENTIONALLY BOUNDED.
```

A contractor/manager such as Ben may have permission to access Company Attention through the appropriate office/management CalibraytAI experience, including when using a mobile device.

That permission does **not** cause Company Attention to appear inside the Field App.

Do **not** implement responsive/mobile office behaviour from this file. Record the distinction only.

---

## 8. Permission domains — owner law; seam freeze is separate

Explicit contractor-controlled permission boundaries exist between at least these conceptual information domains. The **minimum Company / Management seam** is frozen in [company-management-access-domain-seam.md](company-management-access-domain-seam.md) (**DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**). Do **not** implement that seam from this PERF-C file.

| Domain | Examples (illustrative, not a matrix) |
|--------|----------------------------------------|
| **A. PROJECT / OPERATIONAL** | Projects; Project work; Schedule; labour; Time; Project attention |
| **B. COMPANY / MANAGEMENT** | Company Attention; cross-Project management information; broader company operating information |
| **C. SENSITIVE FINANCIAL** | bank-account information; bank balances; cash position; company cash flow; payroll-sensitive information; other sensitive financial/business information |

These are product/security permission domains, **not** job titles.

Do **not** implement job-title RBAC, the access-domain grant model, or schema from this PERF-C file. Domain C remains future. The exact future Sensitive Financial matrix remains separately governed.

---

## 9. Contractor controls permissions

```text
THE CONTRACTOR / COMPANY OWNER CONTROLS WHO MAY ACCESS COMPANY AND
SENSITIVE BUSINESS INFORMATION.
```

Do **not** assume that a generic title such as admin, manager, supervisor, or employee automatically confers access to every information category.

Future governed permission architecture must allow the contractor to determine appropriate access.

Do **not** design that architecture here.

---

## 10. Project / Company / Financial firewall

```text
PROJECT / OPERATIONAL ACCESS DOES NOT AUTOMATICALLY CONFER COMPANY
ATTENTION ACCESS.

COMPANY ATTENTION ACCESS DOES NOT AUTOMATICALLY CONFER ACCESS TO
SENSITIVE FINANCIAL INFORMATION.

SENSITIVE FINANCIAL ACCESS REQUIRES SEPARATELY GOVERNED,
CONTRACTOR-CONTROLLED AUTHORIZATION.
```

A user may eventually have:

- Project access without Company Attention
- Company Attention without sensitive financial detail
- sensitive financial access only when separately authorized

The exact future Sensitive Financial matrix remains separately governed. Domain B seam: [company-management-access-domain-seam.md](company-management-access-domain-seam.md).

---

## 11. Sensitive-information warning principle

When future functionality allows the contractor to grant access to sensitive financial/business information, CalibraytAI must clearly warn the contractor that the permission being granted exposes sensitive information.

Examples include bank accounts, balances, cash flow, and payroll-sensitive information.

This warning informs the contractor. The contractor decides.

Preserve:

```text
WARNINGS INFORM.
HUMANS DECIDE.
```

Do **not** implement this warning now.

---

## 12. Attention fact vs underlying information

```text
AN ATTENTION FACT AND PERMISSION TO VIEW THE UNDERLYING SENSITIVE
INFORMATION ARE NOT NECESSARILY THE SAME AUTHORITY.
```

Future Company Attention may eventually consume governed sensitive business-attention facts. If so, presentation must respect the user’s contractor-controlled permissions.

Company Attention must **not** become an accidental route around sensitive-information permissions.

The exact future redaction / visibility model remains unresolved and separately governed. Do **not** design it here.

---

## 13. Platform law (preserve exactly)

```text
WARNINGS INFORM.
HUMANS DECIDE.

VALIDATION PROTECTS DATA INTEGRITY.
WARNINGS NEVER CONTROL FUNCTIONALITY.

PROJECT → ELEMENT → optional ACTIVITY

LabourTask = PRICE
Project Work = BUILD
Change Order = commercial Source of Record
SCOPE = current work authorization
TIME = actual labour
SCHEDULE = WHEN and WHO
PERF = derived consumer
MONITOR = money
LEARN = separately governed

Schedule never creates Time.
PERF must not mutate SCOPE, TIME, or SCHEDULE.
PERF-A and PERF-B remain SEALED.
```

Every PERF-C attention fact is **informational only**. It must never block Time, Schedule, Change Orders, Project work, or another workflow. No mandatory acknowledgement. No required resolution.

---

## 14. Explicit exclusions

| Surface / program | Freeze |
|-------------------|--------|
| Home Office | **Not PERF-C.** Later, broader operating experience. May later consume Company Attention and other governed facts. |
| Tomorrow / Review + Notify / Week Ahead | Desktop later. Not PERF-C. |
| Field Company Attention | **Forbidden.** No Company Attention screen/section/card/nav in the Field App. |
| Bank integration / cash flow / payroll | Not PERF-C. Not current financial-attention facts. |
| Financial permissions / job-title RBAC | Sensitive Financial remains future. Job-title RBAC remains forbidden. Company/Management seam **DEFINED / NOT IMPLEMENTATION-AUTHORIZED** ([company-management-access-domain-seam.md](company-management-access-domain-seam.md)). |
| MONITOR money | Money remains MONITOR. Initial PERF-C adds **no** financial-attention facts. |
| CLOSE / LEARN | Separately governed. Not PERF-C. |
| QB-T | Not PERF-C. |
| Field / SCH-D | Do not modify accepted SCH-D. |
| Schedule product | Schedule remains WHEN/WHO. Do not make `/schedule` the owner of Company Attention. |
| Division / Operating Unit / scope selector | Not this freeze. Organization-wide V1. Future scoping seam preserved only. |
| Acknowledgement / resolution workflow | Not PERF-C. Derived / read-only. |
| PERF-A / PERF-B | **SEALED.** Do not reopen to make company aggregation easier. |

---

## 15. Unresolved future permission architecture

Do **not** solve the following in this freeze:

- the Sensitive Financial matrix (domain C)
- job-title RBAC schema or role catalog
- title-to-permission mapping
- implementing the Company/Management seam from this PERF-C file (that freeze is separate and also not implementation-authorized)
- mobile office/management Company Attention chrome (identity vs Field surface is recorded only)
- redaction / visibility model when an attention fact points at sensitive underlying information
- the future warning UX for granting sensitive-financial permission
- future financial-attention fact types under the broader contractor question

Also do **not** assign the following to PERF-C merely because older or future records mention them near PERF:

- “three MONITOR views”
- Original / CO / Current labour views
- explicit progress
- Forecast Finish
- Field owner performance view
- unassigned upcoming work
- acknowledgeable alerts

---

## 16. Relationship

```text
PERF-A  = this Project labour numbers                 SEALED
PERF-B  = this Project look-at facts                  SEALED
PERF-C  = business-level attention layer              DEFINED / NOT IMPLEMENTATION-AUTHORIZED
          initial facts = sealed PERF-B only
Home Office = later Desktop briefing                  RECORDED / NOT IMPLEMENTED
MONITOR = money
CLOSE   = Closeout / LEARN evidence quality           NOT AUTHORIZED
LEARN   = recommendations / calibration               NOT AUTHORIZED
QB-T    = approved-time export readiness              NOT AUTHORIZED
```

---

## 17. What this freeze does not authorize

Do **not** from this file:

- implement Company Attention or any PERF-C product
- edit `app/`, tests, templates, routes, services, or models
- create a migration
- implement Home Office, Tomorrow, Review + Notify Team, Week Ahead
- implement Field Company Attention
- implement permission architecture, job-title RBAC, the Company/Management seam, or financial permissions
- implement bank integration, cash flow, payroll, or MONITOR expansion
- implement CLOSE, LEARN, or QB-T
- reopen PERF-A or PERF-B
- rescore V1
- write an implementation prompt as if this file authorized it

A later **implementation preflight** is a separate governed prompt. This file is not that preflight.

---

## 18. Stop

```text
OWNER DECISIONS 1–16 ACCEPTED.
CONTRACTOR QUESTION:
WHERE DOES MY BUSINESS NEED ATTENTION?
PERF-C DEFINED / NOT IMPLEMENTATION-AUTHORIZED.
DO NOT IMPLEMENT PERF-C FROM THIS FILE.
DO NOT IMPLEMENT HOME OFFICE.
DO NOT PUT COMPANY ATTENTION IN THE FIELD APP.
DO NOT IMPLEMENT JOB-TITLE RBAC, THE COMPANY/MANAGEMENT SEAM, OR FINANCIAL PERMISSIONS.
DO NOT REOPEN PERF-A OR PERF-B.
RETURN TO CHATGPT ARCHITECT.
```

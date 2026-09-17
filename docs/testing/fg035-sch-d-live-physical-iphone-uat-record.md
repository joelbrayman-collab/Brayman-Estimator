# FG-035 SCH-D live + physical iPhone UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-16 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / NOT PUSHED.** Landscape remains **FAIL / unresolved / out of this close**. |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Alembic | Unchanged. Live current = repository head **`f9b0c1d2e3f4 (head)`**. No SCH-D migration. |

## Scope

Prove Field Today / Week / Month + schedule-assisted Time against the **same** Schedule rows as Company / Hub. Worker My work = USER or Crew membership on date D. Company Today is secondary read-only awareness. TIME remains authoritative. No Field Schedule POSTs. No iPhone Schedule editing. Physical iPhone UAT is **Joel-operated**. V1 **not rescored**.

**Project address + Directions is a V1 Field requirement** because Ben UAT will include real-world use and Brayman Field workers / “the boys” will participate. Accepted physical path: worker opens Today, sees the Project, sees the job-site address, taps Directions, phone navigation opens with the destination, then returns to CalibraytAI using native iOS.

## Final physical close (17 Sep 2026)

Joel physically tested and accepted the current SCH-D Field experience. Cursor did **not** operate the iPhone.

### A. Server-side live UAT

**PASS** (prior engineering / live synthetic vessel Project **48**). No SCH-D migration. Same SCH-A/B/C Schedule authority. Schedule-assisted Time remains a suggestion. TIME remains actual-work authority.

### B. Physical iPhone UAT performed by Joel (portrait)

| Check | Result | Joel reaction (only if supplied) |
|-------|--------|----------------------------------|
| G1 Today | **PHYSICAL PASS** | — |
| G2 Today job-site address + Directions | **PHYSICAL PASS** | “love it” |
| G3 Company Today job-site address + Directions | **PHYSICAL PASS** | “love it” |
| G4 This Week location + Directions | **PHYSICAL PASS** | — |
| G5 This Month | **PHYSICAL PASS** | “love this new layout!” |
| G6 Time | **PHYSICAL PASS** | — |

**SCH-D PHYSICAL IPHONE UAT: PASS.** Do not make Joel repeat these gates.

### C. Schedule-assisted Time physical test

**PASS.** Durable submitted row remains `labour_time_entries` **id 6** (Project **48**, user **1**, work_date **2026-09-16**, activity **9** Place concrete, **6.00** hours, **SUBMITTED**). History event **SUBMITTED** (id **13**) at **2026-09-16 18:09:44**. Schedule did **not** create that row. No further Time was submitted this close.

### D. Job-site address / Directions physical test

**PASS** on Today, Company Today, and This Week after the bounded location correction. Synthetic Project **48** address `48 Synthetic UAT Job-Site Road, North Gower, ON`. Directions hands the destination to native phone maps. No embedded maps. No GPS. No CalibraytAI navigation engine.

### E. Native Maps return physical test

**PASS.** Path: CalibraytAI → Directions → iPhone maps / navigation → native top-left Safari return → CalibraytAI. Joel confirmed the native iPhone return function worked well. **Architect product decision:** no CalibraytAI return-navigation feature is required. Native iOS behavior is accepted.

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH-B IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH-C IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH-D IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / NOT COMMITTED / NOT PUSHED
G1–G6 PHYSICAL PASS
DIRECTIONS + NATIVE RETURN PHYSICAL PASS
SCH OVERALL OPEN / PARTIAL
PERF NOT AUTHORIZED
CLOSE NOT AUTHORIZED
LEARN NOT AUTHORIZED
QB-T NOT AUTHORIZED
WARNING LAW INFORMATIONAL / NON-BLOCKING
MANUAL FRAMEWORK ACTIVE / SCH-D JOB-SITE LOCATION DIRECTIONS MANUAL IMPACT CURRENT
ONE LOOP
ONE PLATFORM / ONE CODEBASE
PROJECT ADDRESS + DIRECTIONS V1 FIELD REQUIREMENT
V1 NOT RESCORED
```

### 17 Sep 2026 portrait physical results + correction

| Check | Result |
|-------|--------|
| F1 Company Today | **PHYSICAL PASS** + Address/Directions V1 enhancement applied. Not a Directions physical PASS. |
| F2 This Week | **PHYSICAL PASS** + Address/Directions V1 enhancement applied. Not a Directions physical PASS. |
| F3 This Month | **PHYSICAL FAIL** / too busy / “no one will use it.” Approved replacement: calendar + tap day + day detail. Applied. **Not a Month physical PASS.** |
| F4 Time → Back to Today | **PHYSICAL PASS / IMMEDIATE.** Preserve. |

**Address authority:** existing `projects.address` (`Project.address`) and civic `ProjectLocation` when street exists. Projects owns both. Field does not duplicate. No migration. `Project.address` is not parsed into location.

**Project 48 live address:** `48 Synthetic UAT Job-Site Road, North Gower, ON` (bounded synthetic `Project.address` only; no `ProjectLocation` row). Displayed as:

48 Synthetic UAT Job-Site Road
North Gower, ON

### 17 Sep 2026 Joel G-series physical results

Historical G2/G3/G4 first pass **FAIL** (no job-site address on live Project 48). Bounded correction applied. Final retest:

| Check | Result |
|-------|--------|
| G1 Today | **PHYSICAL PASS.** |
| G2 Today cards | First **FAIL** (no job-site address). After correction **PHYSICAL PASS.** Joel: “love it”. |
| G3 Company Today | First **FAIL** (no job-site address). After correction **PHYSICAL PASS.** Joel: “love it”. |
| G4 This Week | First **FAIL** (job locations required). After correction **PHYSICAL PASS.** |
| G5 This Month | **PHYSICAL PASS** — Joel: “love this new layout!” Do not redesign. |
| G6 Time | **PHYSICAL PASS.** No additional Time submitted this close. |
| Directions → native maps → native Safari return | **PHYSICAL PASS.** No CalibraytAI return-navigation feature. |

**SCH-D PHYSICAL IPHONE UAT: PASS.** Do not repeat G1–G6. Landscape remains out of this close.

**HTTPS restart (17 Sep 2026, after job-site location / Directions correction):** terminated Python **83080**. Replacement wrapper **85906**, Python **85913**, `--with-threads`, start **2026-09-17 08:21:48** local. Localhost `/login` **200** **40 ms**. `.local` `/login` **200** **12 ms**. Concurrency: held TLS while `/login` **200** **4 ms**. URL `https://Joels-MacBook-Air.local:5443/field/today`.

## Git / Alembic

| Field | Value |
|--------|--------|
| Committed HEAD / `origin/main` | **`398db63ba9612c18915959556d49e01ddc9f1ea0`** (`docs: pin FG-035 SCH-C SHA`) at UAT start |
| Product SCH-D SHA | **`59d36b8f0b3a86eb41aee03890cb432d0fc58e52`** (`feat: implement FG-035 SCH-D field schedule`) |
| Product SCH-C | **`c57e23c55260b44fc88cadfe2fc40924aa58dde7`** |
| Working tree at UAT | Reviewed SCH-D product + tests + UAT/governance (committed in the product SHA) |
| Live current | **`f9b0c1d2e3f4 (head)`** |
| Repository head | **`f9b0c1d2e3f4 (head)`** |
| Migration this UAT | **None** |

## Backup

| Field | Value |
|--------|--------|
| Path | `instance/brayman_estimator-backup-before-fg035-sch-d-uat-20260916-110645.db` (gitignored; not staged) |
| Backup size | **3,141,632** |
| Source DB size at backup | **3,141,632** |
| Backup exists | **yes** |
| Backup Alembic | **`f9b0c1d2e3f4`** |

Earlier backups were not overwritten.

## Protected occupancy — before and after vessel create

| Record | Identity / state |
|--------|------------------|
| Project 45 | `FG035-UAT SCH-A SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · items **4** unchanged |
| Project 46 | `FG035-UAT SCH-B SYNTHETIC — NOT A CUSTOMER` · ORG-001 · items **6** unchanged |
| Project 47 | `FG035-UAT SCH-C SYNTHETIC — NOT A CUSTOMER` · ORG-001 · items **3** unchanged |
| Estimate 28 | EST-2026-0019 Draft · Project **27** |
| Version 34 | version_number **1** · Draft · `is_locked` **0** · subtotal **49872.94** · total **56356.42** |
| Schedule rows on Project 27 | **0** |
| PRODUCTION packages | **0** |
| Global LabourTimeEntry before physical Time | **5** |

Projects **45 / 46 / 47 / 27** were not mutated.

## App date

Field Today uses `date.today()`. Live app date for this UAT: **2026-09-16 Wednesday**.

| Window | Bounds |
|--------|--------|
| Today | 2026-09-16 |
| This week | Monday **2026-09-14** → Sunday **2026-09-20** |
| This month | **2026-09-16** → **2026-10-27** (`today` → `today+41`) |

## Synthetic UAT vessel

Not Joel’s production commercial occupancy. Not EST-2026-0019. Not projects **45**, **46**, or **47**.

| Field | Value |
|--------|--------|
| Project | **id 48** `FG035-UAT SCH-D SYNTHETIC — NOT A CUSTOMER` |
| Organization | **ORG-001** |
| Status | Estimating |
| Client | **id 43** `FG035 SCH-D UAT Client — NOT A CUSTOMER` |

Id **48** was assigned by normal SQLite sequencing. It was not forced.

### People / Crew

| id | Role |
|----|------|
| User **1** | Joel Brayman — physical iPhone operator / My work |
| User **12** | FG035 SCH-B Worker A — another worker (existing; not mutated beyond this vessel’s assignment) |
| Crew **3** | `FG035-UAT SCH-D Field Crew` ACTIVE |
| Membership **3** | Joel on Crew **3** **2026-09-16 → 2026-09-17** inclusive |

### Work / Schedule

| Item | Element / Activity | Window | Assignment | Role |
|------|--------------------|--------|------------|------|
| **14** | Layout **19** | 2026-09-14 → 2026-09-14 | USER Joel | This week before Today |
| **15** | Foundation **20** (Element-only) | 2026-09-16 | USER Joel | Element-only + SEQUENCE warning |
| **16** | Pour **21** | 2026-09-16 | USER Joel | Parent Element item |
| **17** | Pour **21** / Place concrete **9** | 2026-09-16 | USER Joel | Activity-level + two jobs today |
| **18** | Walls **22** | 2026-09-16 → 2026-09-19 | Crew **3** | Crew work; membership only 16–17 |
| **19** | Roofing **23** | 2026-09-16 | USER **12** | Another worker; hidden from Joel My work |
| **20** | Sitework **24** | 2026-09-16 | Unassigned | Company Today only |
| **21** | Excavation **25** | 2026-09-18 → 2026-09-20 | USER Joel | Prior work scheduled after Foundation |
| **22** | Interior **26** | 2026-10-06 → 2026-10-08 | USER Joel | This month forward awareness |

Dependency **4**: Excavation **25** → Foundation **20** (Foundation comes after Excavation).

Unscheduled Time path: Extra Work activity **10** `Cleanup not on schedule` on element **27** `Cleanup`. Not scheduled.

## SERVER-SIDE LIVE UAT

Authenticated Field session as user **1** against the live development/UAT DB. No physical iPhone taps in this section.

### Projection

| Check | Result |
|--------|--------|
| Joel Today | Foundation (Assigned to me), Pour, Pour — Place concrete, Walls (Crew work) |
| Joel Today hides Roofing | **PASS** |
| Joel Today hides Sitework Unassigned | **PASS** |
| Worker 12 Today | Roofing only |
| Company Today vessel | includes Sitework **Not assigned** and Roofing Worker A |
| This week | Mon Layout; Wed Today; Thu Walls; Fri–Sun Excavation. Walls **not** Fri/Sat despite the Crew bar |
| This month | week-grouped; Interior **2026-10-06 → 2026-10-08** |
| SEQUENCE warning on Foundation | informational; KEEP/MOVE/REVIEW not shown |
| suggest_time_attribution today | Foundation activity_id **None**; Pour element-only; Pour Place concrete activity **9**; Walls |
| suggest Friday | Excavation only (Crew membership ended 17th) |
| Time choices still include Cleanup | **PASS** |
| Suggest does not insert Time | count remained **5** |

### HTTP

| Route | Result |
|--------|--------|
| GET `/field/today` | **200** My work + Capture home |
| GET `/field/week` | **200** 2026-09-14 → 2026-09-20 |
| GET `/field/month` | **200** Interior present |
| GET `/field/company-today` | **200** Sitework Not assigned; no Change dates / Assign |
| GET `/field/schedule/today` | **302** `/field/today` |
| GET `/field/projects/48/time` | **200** Scheduled today + two-jobs help + Cleanup choosable; hours not prefilled |
| POST `/field/week` | **405** |
| POST `/field/month` | **405** |
| POST `/field/company-today` | **405** |

Company Today also shows other org items overlapping today (SCH-A Project **45** unassigned windows). That is company-wide awareness, not a SCH-D vessel defect. Physical script tells Joel which names belong to Project **48**.

## HTTPS Field environment

Established FG-021 method: Flask `--cert`/`--key`, host `0.0.0.0`, port **5443**, `--no-reload`.

| Field | Value |
|--------|--------|
| Process | Cursor Terminal **779935** · Flask wrapper PID **97891** · Python listen **97898** · started **2026-09-16 16:56:46 EDT** · **running** |
| Listen | `*:5443` |
| Login GET | **200** `https://127.0.0.1:5443/login` |
| Field Today unauthenticated | **302** `/login?next=%2Ffield/today` |
| Process vs product mtimes | Flask **16:56:46** is after latest corrected product mtimes (`field/base.html` **16:52:21**, `field.js` / `field.css` **16:52:27**) |
| Current LAN | **192.168.2.88** |
| Cert SAN | DNS `Joels-MacBook-Air.local` · IP **192.168.134.223** (historical FG-021) |
| Cert/IP note | Current LAN **does not** match the leaf IP SAN. Prefer `https://Joels-MacBook-Air.local:5443`. LAN IP URL may show a Safari name warning. Same trusted FG-021 CA. Cert was **not** regenerated this pass. |

Do **not** treat a URL response as physical iPhone PASS.

## PHYSICAL IPHONE UAT PERFORMED BY JOEL

Cursor did not tap the iPhone. Do **not** treat this section as overall PASS.

### PHYSICAL IPHONE TEST 1 / TEST 5 — JOEL RETEST AFTER TIME-ENTRY CORRECTION

**SCHEDULED TIME: PHYSICAL PASS.** Joel entered/submitted Time after the Time-entry correction. Schedule → Time handoff works physically. Worker still controls Hours.

Overall physical UAT **NOT CLOSED.** Additional contractor-facing / mobile findings remain.

| Test | Surface | Joel result |
|------|---------|-------------|
| 1 | Today | **PARTIAL.** Capture/Time usable. Remaining: weekday orientation missing; My work repeats authenticated user name; Time date control shifted right on iPhone. |
| 2 | Company today | **STOPPED.** Wait for UX #2 retest A–E. |
| 3 | This week | **STOPPED.** Week day picker wishlist parked. |
| 4 | This month | **STOPPED.** Month-name / project-rollup wishlist parked. |
| 5 | Scheduled Time | **PHYSICAL PASS.** Time submitted. Hours controlled by worker. |
| 6 | Multiple jobs | **STOPPED.** |
| 7 | Unscheduled actual Time | **STOPPED pending UX #2.** Ad-hoc reassignment must be obvious. Cleanup already exists on Project **48**. |
| 8 | Background / foreground continuity | **STOPPED.** |

### Root cause

Reproduced against live Project **48** / user 1, no `field_confirmed_project_id`:

| Path | URL | Method | Status | Result |
|------|-----|--------|--------|--------|
| A Today card Enter time | `GET /field/projects/48/time` | GET | **302** `/field/projects/48` | Confirm Project. No Hours. No Send time. |
| A2 confirmed Project 45 | `GET /field/projects/48/time` | GET | **302** `/field/projects/48` | Same gate. |
| B Confirm and Time | `POST /field/projects/48` `next=time` then `GET /field/projects/48/time` | POST/GET | **302** then **200** | Hours empty, Send time, Scheduled today, Pour / Place concrete, Cleanup choosable. |

`time_entry` required the FG-021 confirmed Field project. Schedule Enter time therefore became a **Time gate**. That violates SCH-D law: Schedule suggests; worker confirms; Time records actual work.

`submit_time()`, `list_time_work_choices()`, CSRF, SCOPE lineage, and the Time form were **not** the failing authority. Path B proved the form works once the gate is bypassed.

### Correction

`app/routes/field.py` `time_entry`: opening `/field/projects/<id>/time` **sets** the confirmed project and renders Time. Capture and Extra work still require confirm. `submit_time()` unchanged. Suggestions still do not insert Time.

Today presentation (bounded, after Time fix):

- Natural Field dates (`app/presentation/field_format.py`); no ISO on schedule cards
- One materially identical warning per card
- Project label strips the ` — …` suffix; full name remains in `title`
- Today nav uses an inline calendar SVG (no new icon library). Heading **Today — Wednesday**

### Server proof after correction (not physical PASS)

Dedicated `tests/test_enter_time_from_today_does_not_require_project_confirm` fails on the 302 and passes after the fix. Hours empty. Unscheduled Cleanup remains choosable. Element-only suggestion keeps empty `activity_id`. Multiple Scheduled today choices remain buttons. Warning facts remain informational.

### Time FAIL — superseded as current product path

The Confirm Project redirect from Time is **removed**. Joel physically submitted scheduled Time after that correction. Test 5 is **PHYSICAL PASS**. Do **not** mark overall physical UAT PASS.

### UX #2 additional findings (Joel, after Scheduled Time PASS)

| Finding | Evidence |
|---------|---------|
| Weekday orientation | Today did not clearly state the weekday. App date for this UAT is **2026-09-16 Wednesday**. Product must derive weekday from that same date. |
| My work copy | “Assigned to Joel Brayman” wasted mobile space for the authenticated user. |
| Time date alignment | Date control shifted right on physical iPhone relative to the form. |
| Ad-hoc work | If Ben sends a worker to another job, Time must record actual work without waiting for Schedule to change. Path must be obvious. |

### UX #2 correction (not physical PASS)

- Today shows dynamically derived **weekday** + natural date (`Wednesday` / `September 16` from `date.today()`).
- Worker My work omits the authenticated user’s own name; other people / Crew remain; Company Today still shows assignment names.
- Time date uses the Field form system: hidden inputs do not occupy the landscape grid; date control is full-width left-aligned.
- Time presents **Scheduled today** then **Working somewhere else?** / **Choose different work**, which reveals the existing TIME pickers. Cleanup remains choosable. Time POST does not add Schedule rows. No warning gate.

Joel must physically retest A–E. Do **not** mark overall physical UAT PASS.

### UX #2 PHYSICAL TEST A — JOEL (after UX #2)

**FAIL / CORRECTION REQUIRED.**

PASS:

- My Work itself is understandable
- existing Field functions remain accessible
- Extra Work remains accessible
- Schedule-assisted Time functional path remains **PHYSICAL PASS** (do not repeat)

FAIL:

| Finding | Joel physical result |
|---------|---------|
| Personal identity cue | Missing. Today must show **My Work — Joel** from first name. Do not repeat the name on every card. |
| Time Date alignment | Date control under Date **still** misaligned on physical iPhone. UX #2 CSS did not solve it. |
| Landscape / horizontal | **REGRESSED / NO LONGER WORKS.** Useful landscape orientation and scrolling is a **FAIL**. Do **not** record horizontal scrolling as fixed. Do **not** treat “remove accidental portrait overflow” as disabling useful landscape. |

Company Today / Week / Month physical retest remains **STOPPED** until A1–A4 are accepted.

### Chrome crash incident (2026-09-16, Mac desktop)

**AiRIA pytest / not CalibraytAI / no SCH-D product consequence.** Hung `pytest` in `/Users/joelbrayman/Desktop/Discovery-Search-deposition-contradiction` repeatedly launched headless Google Chrome.app. CalibraytAI HTTPS **5443** was not the parent. No CalibraytAI product change from that incident. Diagnostic closed. Do not repeat.

### UX #3 correction (not physical PASS)

Root causes (inspected, not guessed):

| Item | Cause | Correction |
|------|--------|------------|
| Identity | Today used generic **My work** with no first-name cue. | Section heading `My Work — {first token of display_name}` via `field_my_work_heading`. Cards still omit the authenticated user’s own name. |
| Time Date | Nested `input[type=date]` inside `<label>`; UX #2 `min-width: 0` / `max-width: 100%` on all `.field-input`; `text-align` does not move `::-webkit-datetime-edit`. | Sibling Date label + input in `.field-time-date`. Restore HEAD input sizing. WebKit datetime-edit left / 100%. Hidden CSRF `display: none`. |
| Landscape | Useful prior Field landscape is FG-021 `@media (orientation: landscape)` two-column panel/form + `field-main { max-width: none }` (SHA `057ff15` LANDSCAPE TOLERANCE PASS). There is **no** week-strip horizontal scroller in git. UX #2 stacked Time fields with `grid-column: 1 / -1` and shrink rules. | Restored FG-021 first landscape block. Time other-work uses `display: contents` so Work item / Work remain two-column grid children. **No** `overflow-x: hidden` on html/body. Portrait nav still `flex-wrap: wrap`. |

Do **not** claim UX #3 physical PASS. Joel retests **A1–A4** only.

### UX #3 PHYSICAL RETEST A1–A4 — JOEL

Physical iPhone screenshots control. No screenshot files stored (unstable Field surface).

| Check | Result |
|-------|---------|
| A1 My Work identity | **PASS.** **My Work — Joel** accepted. Preserve. |
| A2 Time Date | **FAIL.** Date control showing `Sep 16, 2026` extends beyond the **right** Time card boundary. Containment defect. |
| A3 Portrait | Improved; Date containment still a defect. Not closed. |
| A4 Landscape layout | **FAIL.** App remains a narrow portrait-like column; most of the landscape viewport is unused. |
| Field action performance | **FAIL / DIAGNOSIS REQUIRED** (Joel clarification 16 Sep 2026). Do **not** record “landscape mode is slow.” CalibraytAI Field is noticeably slow during some user actions / navigation on the physical iPhone, especially **ENTER TIME** plus other Field actions. Landscape layout remains a **separate** FAIL. |

Do **not** characterize landscape as PASS.
Do **not** record landscape-only slowness.

### UX #4 correction (not physical PASS)

**Date containment rule chain (screenshot-grounded):**

1. `.field-input { width: 100%; padding: 12px; border: 2px }` with `* { box-sizing: border-box }`
2. `.field-time-date { width: 100% }` as a landscape grid item (`grid-column: 1 / -1`) with default `min-width: auto`
3. iOS Safari `input[type=date]` intrinsic min-content for `Sep 16, 2026` plus calendar affordance
4. UX #3 `::-webkit-datetime-edit { width: 100% }` made the inner edit fill the input; the native control is extra, so WebKit grew the input past the card

Correction: `min-width: 0` and `max-width: 100%` on `.field-time-date` and its date input only. Time panel/form `min-width: 0`. WebKit datetime-edit + fields-wrapper `min-width: 0` / `max-width: 100%`. **No** `overflow-x: hidden`. **No** negative margin.

**Landscape unused width:** default `.field-main { max-width: 42rem }` (`672px`) with `margin: 0 auto`. FG-021 `max-width: none` lived only in `@media (orientation: landscape)`. Physical screenshot shows that query did **not** produce a wide Field shell. Correction: `@media (min-width: 36rem)` sets `.field-main { max-width: none; width: 100% }` (iPhone portrait ~390px does not match; iPhone landscape does). Two-column packing also matches `(min-width: 36rem) and (max-height: 32rem)`. Not a desktop planner. Not whole-page horizontal scrolling.

**Field action performance — measure first (16 Sep 2026):**

Enter Time from a Today card is an ordinary `<a href="/field/projects/<id>/time">`. No Field JS click intercept. GET confirms the project, then `list_time_work_choices` + `recent_worker_activities` + `suggest_time_attribution` (which calls `assemble_field_schedule`). No redirect chain on the scheduled Enter Time GET.

Live UAT DB (user 1, Project 48, 2026-09-16), GET-only:

| Path | Flask HTTPS TTFB (localhost, after TLS reuse) | Queries | Notes |
|------|--------------------------------------------------|---------|-------|
| `/field/today` | first **296 ms** (TLS 30 ms); later comparable to Week | 34 | Schedule + projects |
| `/field/week` | **16 ms** | 49 | |
| `/field/month` | **23 ms** | 95 | Month window |
| `/field/company-today` | **12 ms** | 35 | |
| `/field/projects/48/time` | **20 ms** then **12 ms** | 43 | Enter Time |
| Google Fonts CSS (`fonts.googleapis.com`, Mac) | **135 ms** | n/a | Render-blocking in Field `<head>` |
| IBM Plex font file (`fonts.gstatic.com`, Mac) | **152 ms**, 205 KB | n/a | Additional after CSS |
| Field header logo `calibraytai-logo-v2.png` | **5 ms** localhost | 0 | **439 328** bytes; contributing if uncached |

`assemble_field_schedule` Today **14 ms** / 26 queries. `suggest_time_attribution` **5 ms** / 27 queries. SCH-D added those onto Time GET versus pre-SCH-D choices+recent (~13 queries). That increment is **not** the noticeable iPhone delay.

**Bottleneck:** **SERVER IS FAST / IPHONE STILL FEELS SLOW.** Flask Enter Time **12–20 ms**. Render-blocking Google Fonts on every Field document was slower than Flask on the Mac and blocks first paint. `field.js` `init()` also opened IndexedDB on Time / Week / Month / Company Today even with no Capture form.

Correction (bounded Field client path; **not** PERF; **not** Schedule redesign):

1. Remove Google Fonts `<link>` from `app/templates/field/base.html`. Field CSS keeps Helvetica Neue / Arial fallback (native on iPhone).
2. Open IndexedDB only when `.field-capture` or `#field-retry-panel` is present (Today / Capture). Enter Time / Week / Month / Company Today skip idle IDB. Logout still opens IDB on submit.
3. Do **not** speculative-optimize `assemble_field_schedule`.

Header logo size remains a contributing client cost; branding asset **not** changed this pass.

Do **not** claim UX #4 physical PASS.

### UX #4 PHYSICAL RETEST B1–B5 — JOEL

| Check | Result |
|-------|---------|
| B1 Date | **FAIL.** No material change. Date control remains wrong. **Top-right box is blank.** Otherwise portrait Time fits. |
| B2 Portrait | **PASS.** Preserve. |
| B3 Landscape | **FAIL** on **Time** and **Today**. Broader than one card/control. Field shell issue. |
| B4 Enter Time | **PASS / QUICK.** Do not continue treating Enter Time as a general performance defect. |
| B5 Navigation | **PARTIAL.** Other Field pages **QUICK**. **Time → Back to Today ≈ 2–3 seconds.** |

Do **not** claim UX #4 physical PASS.

### UX #5 correction (not physical PASS)

**Date blank top-right box:** Not a second Field HTML control. Time form has one `input#field-time-date` (label + input siblings in `.field-time-date`; no empty wrapper/column). The blank box is Safari’s native calendar button (`::-webkit-calendar-picker-indicator`) inside that single input. Prior UX CSS never removed native chrome, so physical Date did not change. On iPhone the whole field already opens the picker; the indicator has no contractor purpose. Native chrome is removed (`appearance: none` on the Date input; indicator collapsed). One Date label, one Date control, full card width. No clipping. No negative margin.

**Landscape Today + Time:** Shared cause: FG-021 Capture two-column grid was applied to **every** `.field-panel`. Today and Time are not Capture. Correction: two-column grid only on `.field-panel.field-capture`. `.field-main { max-width: none }` remains for landscape / `min-width: 36rem`. Portrait default (no 2-col, 42rem until 36rem) preserved. Field CSS/JS cache-busted `v=schd-ux5b`.

**Back to Today:** `href="/field/today"` ordinary GET. No JS intercept. No redirect. Flask Today **~22 ms** — same as direct Today. Unique cost: Today always contains `#field-retry-panel`, so UX #4 still opened IndexedDB on every Today load. Week/Month/Company/Time skip IDB. Time → Today was the path that hit it. Correction: open IDB on Capture always; on Today only if `localStorage calibai-field-has-pending=1`, and then after timeout. No Schedule redesign.

Do **not** claim UX #5 physical PASS. Joel retests **C1–C5** only. Do **not** submit another Time entry.

### UX #5 PHYSICAL RETEST C1–C5 — JOEL

| Check | Result |
|-------|---------|
| C1 Date | **PHYSICAL PASS / FIXED.** Preserve. |
| C2 Portrait | **PHYSICAL PASS.** Preserve. |
| C3 Today landscape | **PHYSICAL FAIL.** Landscape did not work. Joel reports **the entire app crashed.** |
| App stability during C3 | **FAIL.** Entire app crashed. |
| C4 Time landscape | **NOT TESTED.** Do not infer. |
| C5 Back to Today | **NOT TESTED.** Do not infer. |

**C3 crash diagnostic (16 Sep 2026, after evidence capture, no product patch):**

HTTPS Python **2556** remained running from **17:46:06 EDT** (state **S**, no traceback, no restart). Last iPhone (`192.168.2.160`) requests: `/field/today` **200** at **17:48:32**, then `/field/projects/48/time` **200** at **17:48:48**, plus static **200/304**. **No further HTTP** after 17:48:48. **No 4xx. No 5xx. No redirect loop.** Rotation does not create a Field request. `field.js` has **no** `resize` / `orientationchange` / `visualViewport` / `matchMedia` / `ResizeObserver` listeners. iPhone Safari/WebKit crash logs were **not available** on this Mac (no MobileDevice crash folder; no Safari/WebKit DiagnosticReports in the C3 window; Mac unified log sample empty). Classification: **not a Flask server crash**. Client WebKit crash vs tab reload vs Safari termination: **UNKNOWN** without device logs. **No landscape CSS/JS patch this pass.** Do **not** rotate the phone again until Architect review.

Do **not** claim UX #5 physical PASS.

**CURRENT UX #5 TIME PAGE — PHYSICAL FAIL / BLANK SCREEN (after C3):**

Joel reproduced multiple times on the physical iPhone:

1. On Field
2. Tap Time
3. Screen goes blank and stays blank
4. Browser Back returns to the previous page

**Diagnostic (no product patch):** HTTPS Python **2556** still healthy from **17:46:06 EDT**. The **only** iPhone Time GET on this process is **17:48:48** `GET /field/projects/48/time` **200** (that load is the C1 Date **PHYSICAL PASS**). After the C3 crash, Flask logged **zero** further Time (or any) requests. No 3xx/4xx/5xx. No Traceback. Authenticated Project 48 Time HTML is currently **200**, **7846** bytes, form/Date/Scheduled today/Back to Today/`v=schd-ux5b` present. Date `appearance: none` was already on the C1 PASS load; it is **not** demonstrated as the cause of the later blanks. Classification: **client navigation failure after C3 WebKit/Safari termination**, not a Flask Time-route failure. Historical earlier-build Schedule-assisted Time PASS remains prior-build evidence. This same UX #5 process rendered Time successfully **before** C3.

Do **not** claim current-build Time physical PASS after C3.

**Live screenshot 18:00 EDT:** Joel is on Field **Today** (Foundation **Enter time**, Pour conflict card, Safari tab `k-air.local`). Flask still has **no** Time GET after **17:48:48**. Taps on Enter time in this session are **not** fetching `/field/projects/48/time` from the Mac.

Do **not** claim current-build Time physical PASS after C3.

**FRESH SAFARI TAB TEST (portrait, ~18:11 EDT):**

| Field | Result |
|-------|--------|
| Orientation | PORTRAIT |
| Navigation | New Safari tab. Manual `https://Joels-MacBook-Air.local:5443/field/today` |
| Result | **BLANK SCREEN** |
| Not | Old tab. Not Back. Not Time tap. Not landscape. |

**Damaged-tab-only hypothesis: INSUFFICIENT AFTER FRESH-TAB FAILURE.**

Fresh `/field/today` **did not complete HTTP** on Flask **2556**. No new Werkzeug line after **17:48:48**. HTTPS process still listening, but **not healthy for new HTTP**: localhost `GET /login` **timed out 3s**; TLS handshake to 127.0.0.1:5443 hung. One **ESTABLISHED** TCP `192.168.2.88:5443 → 192.168.2.160:61619` (same iPhone as 17:48). Cert SAN `DNS:Joels-MacBook-Air.local` (LAN `192.168.2.88`; historical IP SAN `192.168.134.223` unused here). `.local` resolves on Mac to `127.0.0.1` and `192.168.2.88`. **No product patch.** Flask single-thread blocked; HTTP never logged.

Do **not** claim current Today PASS.

### UAT HARNESS RECOVERY (16/17 Sep 2026)

**PRODUCT vs HARNESS**

| Item | Status |
|------|--------|
| C1 DATE | **PHYSICAL PASS** |
| C2 PORTRAIT | **PHYSICAL PASS** |
| C3 LANDSCAPE | **FAIL / client incident / unresolved** |
| POST-C3 Time blanks + fresh `/field/today` blank | **NOT VALID AS PRODUCT-RENDER FAILURE** |
| Reason | HTTPS UAT Python **2556** could not complete **any** new HTTP, including localhost `/login` timeout 3s. Stuck ESTABLISHED `192.168.2.160:61619`. Time HTML independently **200** in test client. |

**UAT HARNESS ROOT CAUSE:** single-thread development server blocked by stuck iPhone TCP connection.

**Recovery:** terminated **2556**. Restarted same SCH-D working-tree product: `flask run ... --no-debugger --no-reload --with-threads`. Replacement Python **78027**, wrapper **78018**, start **2026-09-17 00:25:54** local. Localhost `/login` **200** in **32 ms**. `.local` `/login` **200** in **4 ms**. Authenticated test-client `/field/today` **200**. Concurrency: held TLS connection 3s while `/login` completed **200** in **12 ms**. **No product CSS/JS/Today/Time change.**

Do **not** mark landscape PASS.

Joel sanity check only: **E1** portrait Today fresh load. **E2** portrait Time tap once. Do **not** rotate. Do **not** submit Time. Do **not** test landscape/Week/Month/Company Today yet.

## Post-physical tests

Authoritative post-physical automated regression after Joel physical PASS. Cursor Terminal.

| Bundle | Result |
|--------|--------|
| Dedicated SCH-D `./venv/bin/python -m pytest -q tests/test_work_schedule_field_fg035.py` | **21 passed**, 44 warnings, **15.53s**, exit **0** |
| TIME + Field `./venv/bin/python -m pytest -q tests/test_work_time_fg035.py tests/test_field_web_fg021.py tests/test_work_schedule_field_fg035.py` | **49 passed**, 190 warnings, **28.96s**, exit **0** |
| SCH-A/B/C `./venv/bin/python -m pytest -q tests/test_work_schedule_fg035.py tests/test_work_schedule_assignment_fg035.py tests/test_work_schedule_dependency_fg035.py` | **36 passed**, 89 warnings, **14.91s**, exit **0** |
| Focused TAX/WBS+SCOPE+TIME+SCH-A/B/C/D+Hub/Field/MONITOR | **156 passed**, 584 warnings, **83.01s**, exit **0** |
| Full suite `./venv/bin/python -m pytest -q` | **1140 passed**, 3749 warnings, **665.58s**, exit **0**. Authoritative post-physical full suite. |

## Manual Impact

**MANUAL IMPACT — SCH-D PHYSICAL IPHONE UAT PASS** is **CURRENT** in [architecture/manual-impact-log.md](../architecture/manual-impact-log.md). Includes Directions and native iOS return.

## Status at this STOP

SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / NOT COMMITTED / NOT PUSHED**. Synthetic Project **48** address `48 Synthetic UAT Job-Site Road, North Gower, ON`. V1 **60% / 4 of 11**. No migration. PERF **NOT AUTHORIZED**.

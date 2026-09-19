# CalibraytAI User Guide — Manual Impact log

| Attribute | Value |
|-----------|--------|
| Status | **FRAMEWORK / IMPACT CAPTURE.** Not the User Guide. Not Interactive Help. Not Voice. **NOT IMPLEMENTATION-AUTHORIZED.** |
| Updated | 2026-09-18 |
| Governing record | [interactive-help-voice-and-user-manual-future-record.md](interactive-help-voice-and-user-manual-future-record.md) **FUTURE / RECORDED / MANDATORY PRE-UAT V1 / NOT IMPLEMENTATION-AUTHORIZED** |
| Framework | [calibraytai-v1-user-guide-framework.md](calibraytai-v1-user-guide-framework.md) **MANUAL FRAMEWORK: START NOW.** **Manual Audience Law** controlling. |
| Policy | **Append-only.** Newest entry first under Entries. Do not rewrite historical entries except to correct factual error (note the correction). |

This file is **not** the professional CALIBRAYTAI V1 USER GUIDE. It is a lightweight close-time capture so later Manual authoring has contractor-facing impact notes from the actual product.

Do **not** write final Manual prose here.
Do **not** capture screenshots against unfinished surfaces.
Do **not** implement Help / Voice / Manual from this file.

**Final authoring sequence** remains: remaining functional V1 → Contractor Language + UX E2E Audit → one User Help Content authority → User Guide from the finished product → procedure cross-check → final desktop/iPhone screenshots → Help → Voice → internal E2E → task-based UAT package → **give the completed Guide to Kevin and Ben (and already-recorded Ben’s father-in-law) BEFORE platform access** → allow Guide review → then platform access and realistic task-based UAT without coaching.

Kevin / Ben platform access: **NOT YET**.

V1 **not rescored** from this file.

---

## When to add an entry

Add one entry at each **material feature / slice close** that creates or changes a contractor-facing capability.

Do not backfill earlier slices from this recording. Capture begins with current development (SCH-C).

## Template (copy)

```markdown
### MANUAL IMPACT — <SLICE> (YYYY-MM-DD)

| Field | Content |
|-------|---------|
| Slice | |
| Product status at capture | |
| 1. What new contractor capability exists? | |
| 2. When would the contractor use it? | |
| 3. What workflow will the final Manual need to teach? | |
| 4. What contractor-facing terms must be used? | |
| 5. What screenshots / Print examples will eventually be needed? | |
| 6. What warnings / validation distinctions need explanation? | |
| 7. Desktop / iPhone / Print relevance | |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |
```

---

## Entries

### MANUAL IMPACT — CORE CLOSE C1 CONTRACTOR PUNCH LIST (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE C1 Contractor Punch List |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED.** Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Additive **`d4e5f6a7b8c9`**. Live Hub cannot show Punch List until live migrate. No live Punch List rows. |
| 1. What new contractor capability exists? | On an ACTIVE Project Hub, authorized Project users can add Punch List items describing unfinished physical work, associate them with Original Scope or an existing Change Order or Other closeout work, mark them Complete, and Reopen if the work is not actually done. Summary states open/complete counts, Punch List complete, or Nothing is on the Punch List. |
| 2. When would the contractor use it? | When physical work still needs to be completed before later Completion Sign-Off. Not for Change Order paperwork, invoices, or client communication history. |
| 3. What workflow will the final Manual need to teach? | Open Project Hub BUILD Punch List. Add an item with a plain description and work source. Mark Complete when the physical work is done. Reopen if it was marked complete too soon. Closed Projects show Punch List history only. |
| 4. What contractor-facing terms must be used? | Punch List. Open. Complete. Add Punch List Item. Mark Complete. Reopen. Original Scope. Change Order. Other closeout work. Punch List complete. Nothing is on the Punch List. |
| 5. What screenshots / Print examples will eventually be needed? | Active Hub Punch List empty, with open items, and complete. Add form. Closed Hub history view. Capture after live migrate / UAT. |
| 6. What warnings / validation distinctions need explanation? | Closed Project blocks Punch List changes until Reopen Project. Completing a Punch List item does not complete the Change Order. Client comments later are not Punch List items until the contractor accepts them. Zero items is not a fake “no deficiencies” row. |
| 7. Desktop / iPhone / Print relevance | Office desktop/tablet Hub only. No Field Punch List. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim Client Final Walkthrough exists. Claim Completion Sign-Off exists. Claim live migrate happened. |

### MANUAL IMPACT — CORE CLOSE CLOSE/REOPEN OPTION A (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE Close/Reopen Option A |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed.** Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. No live Close. All live Projects remain ACTIVE. Authorization is Instance Owner / future System Administrator. `COMPANY_MANAGEMENT` is not Close/Reopen authority. |
| 1. What new contractor capability exists? | Authorized Instance Owner can **Close Project** and **Reopen Project** from the Project Hub after a dedicated confirmation page. Hub shows lifecycle identity **Current** or **Closed**. Closed Hub hides **New Change Order**. Projects list **Current \| Closed** already existed from Slice B and now actually receives Closed Projects after Close. |
| 2. When would the contractor use it? | When a Project should leave current operating work, or when a Closed Project must return to current operating work. Not after Punch List / Completion Sign-Off (those products do not exist yet). |
| 3. What workflow will the final Manual need to teach? | Open the Project Hub. Confirm Close. Find the Project under Closed. Open it historically. Reopen from the Closed Hub when new work is required. Ordinary users do not see Close/Reopen. |
| 4. What contractor-facing terms must be used? | Current. Closed. Close Project. Reopen Project. This Project is closed. This Project is current. This Project is already closed. This Project is already current. Not Archive. |
| 5. What screenshots / Print examples will eventually be needed? | Active Hub Close action. Close confirmation. Closed Hub identity and Reopen. Closed Hub without New Change Order. Projects Current vs Closed after a real Close. Capture after live Close/Reopen UAT exists. |
| 6. What warnings / validation distinctions need explanation? | Repeat Close or Reopen fails visibly. Close does not rewrite history. Closed blocks new work. Existing Time / Change Order paperwork can still finish. Incomplete physical work is Punch List later, not this slice. |
| 7. Desktop / iPhone / Print relevance | Desktop Hub and confirmation pages. Field already hides closed current work from Slice B. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim Punch List exists. Claim Completion Sign-Off exists. Claim live Close was executed. |

### MANUAL IMPACT — CORE CLOSE SLICE B (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE Slice B current-operating consumers + CLOSED guards |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION.** Product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**. No live Close. All live Projects remain ACTIVE. Close/Reopen UI does not exist. |
| 1. What new contractor capability exists? | Projects list **Current \| Closed** (default Current). CLOSED Projects stay reachable from Closed and from the Project Hub. New work on a closed Project is refused with: “This Project is closed. Reopen it before adding new work.” |
| 2. When would the contractor use it? | After a Project is Closed (not yet possible from the product). Until then Current looks like today’s Projects list. |
| 3. What workflow will the final Manual need to teach? | Find a closed Project under Closed. Open the Hub historically. Do not add new Time, Schedule, Extra Work, Change Orders, or Field capture until Reopen exists. Finish existing Time / Change Order paperwork. |
| 4. What contractor-facing terms must be used? | Current. Closed. This Project is closed. Reopen it before adding new work. Not Archive. |
| 5. What screenshots / Print examples will eventually be needed? | Projects Current vs Closed. Closed Project Hub. The closed-Project error. Capture after Close/Reopen exists. |
| 6. What warnings / validation distinctions need explanation? | Closed blocks new work. Existing submitted Time can still be approved or returned. Returned Time can be corrected and sent again. Existing Change Order status can still move; new lines and rewritten Draft scope cannot. Incomplete physical work is Punch List later, not this slice. |
| 7. Desktop / iPhone / Print relevance | Desktop Projects Current \| Closed. Field picker/Today/Week/Month hide closed current work. iPhone Field capture/extra work fail closed if the selected Project is closed. Print unchanged. |
| Do not | Final Manual prose. Unstable screenshots. Claim Close/Reopen exists. Claim Punch List exists. |

### MANUAL IMPACT — CORE CLOSE SLICE A LIVE MIGRATION (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE Slice A live migration |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED.** Product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. Live Alembic **`b2c3d4e5f6a7 (head)`**. All existing Projects **ACTIVE**. Event rows **0**. No Close UI. No Punch List. No Completion Sign-Off. No contractor-facing lifecycle change. |
| 1. What new contractor capability exists? | None now. Schema is live. Close remains unimplemented. |
| 2. When would the contractor use it? | Not yet. Later Close / Punch List / Completion Sign-Off surfaces. |
| 3. What workflow will the final Manual need to teach? | Same as the owner freeze. |
| 4. What contractor-facing terms must be used? | Close Project. Reopen Project. Punch List. Project Completion Sign-Off. Current operating work. |
| 5. What screenshots / Print examples will eventually be needed? | None now. |
| 6. What warnings / validation distinctions need explanation? | Open Punch List blocks Completion Sign-Off. Incomplete physical work is Punch List work. NEW Change Order after Close requires Reopen. |
| 7. Desktop / iPhone / Print relevance | None now. |
| Do not | Final Manual prose. Unstable screenshots. Claim Close exists. Claim Punch List exists. |

### MANUAL IMPACT — CORE CLOSE SLICE A (2026-09-18)

| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE Slice A foundation |
| Product status at capture | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED.** Product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. No Close UI. No Punch List. No Completion Sign-Off. No contractor-facing lifecycle change. |
| 1. What new contractor capability exists? | None now. Foundation only. |
| 2. When would the contractor use it? | Not yet. Later Close / Punch List / Completion Sign-Off surfaces. |
| 3. What workflow will the final Manual need to teach? | Same as the owner freeze: current vs historical work; Punch List before Completion Sign-Off; physical work vs administrative Change Order completion. |
| 4. What contractor-facing terms must be used? | Close Project. Reopen Project. Punch List. Project Completion Sign-Off. Current operating work. Do **not** treat Change Order status as physical completion. |
| 5. What screenshots / Print examples will eventually be needed? | None now. Capture later against finished Close / Punch List / Completion Sign-Off surfaces. |
| 6. What warnings / validation distinctions need explanation? | Open Punch List blocks Completion Sign-Off. Incomplete physical work on Original Scope or an existing Change Order is Punch List work, not administrative completion. NEW Change Order after Close requires Reopen. |
| 7. Desktop / iPhone / Print relevance | None now. |
| Do not | Final Manual prose. Unstable screenshots. Claim Close exists. Claim Punch List exists. |

### MANUAL IMPACT — CORE CLOSE OWNER FREEZE (2026-09-18)


| Field | Content |
|-------|---------|
| Slice | FG-035 CORE CLOSE / Project lifecycle owner freeze |
| Product status at capture | **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** Canonical [core-close-project-lifecycle-product-direction.md](core-close-project-lifecycle-product-direction.md). No Close UI. No Punch List. No Completion Sign-Off. |
| 1. What new contractor capability exists? | None now. Direction recorded: Projects can later leave current operating work without deleting history. Punch List then Project Completion Sign-Off then Close Project. |
| 2. When would the contractor use it? | After work is substantially complete: walkthrough, Punch List, customer/contractor Completion Sign-Off, then Instance Owner / Sys Admin Close. Reopen if the Project must return to current work. |
| 3. What workflow will the final Manual need to teach? | What is current operating work vs historical Project? Who may Close/Reopen? Why Punch List must be complete before Completion Sign-Off can be signed. Why Close can still proceed with a strong warning if the customer has not signed. Why history remains. |
| 4. What contractor-facing terms must be used? | Close Project. Reopen Project. Punch List. Project Completion Sign-Off. Current operating work. Historical Project. Do **not** use: archive (as a third operating state), delete Project, release, waiver, LEARN Closeout, paid in full as a Close rule. |
| 5. What screenshots / Print examples will eventually be needed? | None now. Capture later against the finished Close / Punch List / Completion Sign-Off surfaces. |
| 6. What warnings / validation distinctions need explanation? | Open Punch List blocks Completion Sign-Off signature eligibility. Missing executed Completion Sign-Off warns on Close and does not hard-block Close. Other pending Time/CO warnings inform. Close does not rewrite history. |
| 7. Desktop / iPhone / Print relevance | Completion Sign-Off is intended for desktop/tablet review and generated PDF. Field Punch List is **not frozen**. Print later. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim Close exists. Claim Punch List exists. Claim LEARN Closeout exists. Claim ARCHIVED operating state. |

### MANUAL IMPACT — PERF-C LIVE UAT / SEAL (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 PERF-C Company Attention live UAT / seal |
| Product status at capture | **CURRENT** — PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED**. Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. Evidence [testing/fg035-perf-c-live-uat-record.md](../testing/fg035-perf-c-live-uat-record.md). |
| 1. What new contractor capability exists? | Joel can open office Company Attention and see where the business needs attention across the company’s Projects. Another office user without Company / Management permission cannot. Field does not show Company Attention. |
| 2. When would the contractor use it? | Opening the office to ask: Where does my business need attention? Then following Review to the existing Project destination. |
| 3. What workflow will the final Manual need to teach? | What is Company Attention? Why can Joel see it and AUTH-B cannot? Why is it not in Field? What does each Needs Attention item mean (reuse PERF-B language)? Why leftover test Projects can currently appear in the list until a later Project lifecycle exists. |
| 4. What contractor-facing terms must be used? | Company Attention. Where does my business need attention? Nothing needs attention right now. Extra work needs review. Labour getting close. Labour allowance used. Labour over allowance. Scheduled finish passed. Scheduled work has no approved Time. Do **not** use: Home Office, scorecard, health, risk, severity, RBAC, Active/Archived. |
| 5. What screenshots / Print examples will eventually be needed? | Quiet positive. Several Projects. One Project with several items. Capture later against finished Manual sequencing. Do **not** treat current UAT-vessel occupancy as the customer screenshot set. |
| 6. What warnings / validation distinctions need explanation? | Company Attention does **not** stop work. It does **not** acknowledge or resolve items. Project access does **not** give Company Attention. Company Attention does **not** give Sensitive Financial. Field Company Today is a different screen. Historical / test Projects may currently appear because Company Attention is organization-wide. |
| 7. Desktop / iPhone / Print relevance | Office / management desktop first. Adaptive office layout. Field unchanged. Print later. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim Home Office. Claim Sensitive Financial. Claim People & Access. Claim FG-035 closed. Invent Active/Archived filtering. |

### MANUAL IMPACT — PERF-C (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 PERF-C Company Attention |
| Product status at capture | **CURRENT** — PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-UATed**. Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. Not live-UATed. |
| 1. What new contractor capability exists? | Office Company Attention lists where the business needs attention across the company’s Projects, or says nothing needs attention right now. It is not Field Company Today. It is not Home Office. |
| 2. When would the contractor use it? | Opening the office to ask: Where does my business need attention? Then following the existing Project review link for that item. |
| 3. What workflow will the final Manual need to teach? | What is Company Attention? Why can Joel see it and another office user cannot? Why is it not in Field? What does each Needs Attention item mean (reuse PERF-B language)? What happens when nothing needs attention? |
| 4. What contractor-facing terms must be used? | Company Attention. Where does my business need attention? Nothing needs attention right now. Extra work needs review. Labour getting close. Labour allowance used. Labour over allowance. Scheduled finish passed. Scheduled work has no approved Time. Do **not** use: Home Office, scorecard, health, risk, severity, RBAC. |
| 5. What screenshots / Print examples will eventually be needed? | Quiet positive. One Project with several items. Several Projects. Do **not** capture now. Surface is uncommitted and not live-UATed. |
| 6. What warnings / validation distinctions need explanation? | Company Attention does **not** stop work. It does **not** acknowledge or resolve items. Project access does **not** give Company Attention. Company Attention does **not** give Sensitive Financial. Field Company Today is a different screen. |
| 7. Desktop / iPhone / Print relevance | Office / management desktop first. Adaptive layout. Field unchanged. Print later. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim live UAT. Claim Home Office. Claim Sensitive Financial. Claim People & Access. |

### MANUAL IMPACT — FG-037 (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-037 Company / Management access-domain authorization |
| Product status at capture | **CURRENT** — FG-037 **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION**. Product SHA **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`**. No Company Attention screen. |
| 1. What new contractor capability exists? | Company / Management information is now a separate permission. Joel Brayman (Membership 1) has it. Other current users do not, unless Joel later grants them. |
| 2. When would the contractor use it? | Later, when Company Attention / company screens exist. Today there is no Company screen. The permission is already stored so those screens can be added later without giving every office user company access. |
| 3. What workflow will the final Manual need to teach? | Who can see company / management information? Why can Joel see it and another office user cannot? Why does Field still not show Company Attention? How is permission granted later (not a Settings Members screen today)? |
| 4. What contractor-facing terms must be used? | Company / Management. Project / Operational. Do **not** use: RBAC, role, admin, manager permission, Sensitive Financial (not implemented). |
| 5. What screenshots / Print examples will eventually be needed? | None now. Capture Company Attention later when PERF-C exists. Do **not** screenshot Field as if Company Attention lives there. |
| 6. What warnings / validation distinctions need explanation? | Having Project access does **not** give Company / Management access. Having Company / Management access does **not** give Sensitive Financial access. Ben is intended to have the same company permission later, after a real Ben account exists. |
| 7. Desktop / iPhone / Print relevance | Office / management only. Field unchanged. Print later. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim PERF-C exists. Claim Sensitive Financial exists. Claim Ben already has access. |

### MANUAL IMPACT — PERF-B (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 PERF-B Project Needs Attention |
| Product status at capture | **CURRENT** — PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. Project **50**. Product SHA **`dcde4adfe4a475932b7f144b0220b2b60e4bd75c`**. |
| 1. What new contractor capability exists? | On the Project Labour section, Needs Attention lists factual things to look at, or says nothing needs attention right now. It sits above Allowed / Used / Remaining. |
| 2. When would the contractor use it? | Opening a Project and asking whether anything about this job needs a look. Checking labour getting close, extra work, a scheduled finish that has already passed, scheduled work with no approved Time, or a schedule warning. |
| 3. What workflow will the final Manual need to teach? | What does Needs Attention mean? Does Needs Attention stop me from working? Why does Labour getting close appear? What does Labour allowance used mean? What does Labour over allowance mean? Why does Extra Work need review? What does Scheduled finish passed mean? Why does CalibraytAI say scheduled work has no approved Time? |
| 4. What contractor-facing terms must be used? | Needs attention. Extra work needs review. Labour getting close. Labour allowance used. Labour over allowance. Scheduled finish passed. Scheduled work has no approved Time. Nothing needs attention right now. Do **not** use: threshold breach, attention DTO, risk, severity, scope lineage, schedule conflict algorithm. |
| 5. What screenshots / Print examples will eventually be needed? | Quiet positive state. Labour getting close. Labour over allowance. Extra work needs review. Scheduled finish passed. Scheduled work has no approved Time. Schedule warning. Do **not** capture now. Final Manual later. |
| 6. What warnings / validation distinctions need explanation? | Needs Attention does **not** stop Time, Schedule, Change Orders, or Project work. It is information only. Waiting for approval is not its own Needs Attention item. Labour getting close means Used has reached 80% of Allowed; it is not a verdict that the job is going badly. Labour allowance used means Used equals Allowed. Labour over allowance means Used is more than Allowed. Extra work needs review while extra work still has used or waiting hours and is not yet authorized. Scheduled finish passed means the scheduled end date is before today; it does not mean the work is late or incomplete. Scheduled work has no approved Time means the scheduled start is before today and that scheduled work still has no approved Time; it does not mean the work has not started. |
| 7. Desktop / iPhone / Print relevance | Desktop / office Project Hub Labour. Field is unchanged. Print later. Bounded synthetic live UAT **PASS** on Project **50**. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim FG-035 closed. PERF-C. |

### MANUAL IMPACT — PERF-A (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 PERF-A Project Hub Labour Allowed · Used · Remaining |
| Product status at capture | **SUPERSEDED AS CURRENT** for newest Manual Impact by PERF-B. PERF-A product remains **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**. Project **49**. |
| 1. What new contractor capability exists? | On the Project page, after Time and before MONITOR, a Labour section shows how many hours are Allowed, Used, and Remaining (or Over by). It also shows hours Waiting for approval. Extra work is listed separately while it is still extra work. After a Change Order authorizes that extra work, those hours move into Authorized labour. |
| 2. When would the contractor use it? | Checking how a job is doing on labour. Asking how many hours are left. Seeing whether extra work time is sitting outside the authorized allowance. Checking labour again after extra work is authorized. |
| 3. What workflow will the final Manual need to teach? | How many labour hours do we have left? What is Used? What is Waiting for approval? What does Over by mean? Why is Extra Work shown separately? What happens after Extra Work is authorized? What does Allowance not available mean? |
| 4. What contractor-facing terms must be used? | Labour. Allowed. Used. Remaining. Waiting for approval. Over by. Extra work. Allowance not available. Needs review. Do **not** use: current_authorized_hours, scope_origin, hours_delta, DTO, performance engine, variance denominator. |
| 5. What screenshots / Print examples will eventually be needed? | Project Labour with Allowed / Used / Remaining. Over by example. Extra work with Needs review. Same job after Extra Work is authorized (Extra Work gone; hours in Authorized). Allowance not available. Do **not** capture now. Final Manual later. |
| 6. What warnings / validation distinctions need explanation? | Over by and Needs review are information only. They do not stop Time, Schedule, Change Orders, or Project work. Waiting for approval does not reduce Remaining. Used is approved hours only. Extra work stays separate until that work is authorized; then it is no longer Extra Work on Labour. Time Extra work hours can still show frozen extra-work time until Time’s own summary catches up — that is Time, not Labour. Allowance not available means there is no governed allowance to compare against, not that Allowed is zero. Allowed zero is a known allowance. |
| 7. Desktop / iPhone / Print relevance | Desktop / office Project Hub. Field is unchanged. Print later. Bounded synthetic live UAT **PASS** on Project **49**. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Claim FG-035 closed. PERF-B Needs Attention. |

### MANUAL IMPACT — SCH-D PHYSICAL IPHONE UAT PASS (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Today / Week / Month + schedule-assisted Time + job-site Directions |
| Product status at capture | **SUPERSEDED AS CURRENT** for newest Manual Impact by PERF-A. SCH-D Field product remains **PHYSICAL IPHONE UAT PASS**. G1–G6 **PHYSICAL PASS**. Directions + native iOS return **PHYSICAL PASS**. |
| 1. What new contractor capability exists? | See today’s work, this week, this month, and company today. See the job-site address. Tap Directions to open the phone’s maps. Enter Time from scheduled work, or choose the work actually done. Native iPhone return brings the worker back to CalibraytAI. |
| 2. When would the contractor use it? | Opening Field in the morning. Driving to the job. Checking what others are doing today. Entering hours. Looking at the month calendar. |
| 3. What workflow will the final Manual need to teach? | What am I doing today? What is coming this week? What is coming this month? How do I see what the company is doing today? What does Assigned to me mean? What does Crew work mean? How do I enter Time from today’s work? What if I have more than one scheduled job? What if the work I did was not scheduled? What does a Schedule warning mean? How do I get directions to today’s job? How do I return to CalibraytAI after opening Directions? How do I add CalibraytAI to my iPhone Home Screen? After opening Directions, use the iPhone’s native return-to-Safari control to return to CalibraytAI. |
| 4. What contractor-facing terms must be used? | Today. This week. This month. Company today. My work. Assigned to me. Crew work. Address. Directions. Enter time. Scheduled today. Working somewhere else? Choose different work. This is information only. Do **not** use: maps.apple.com, daddr, deep link, URL scheme, GPS, overlay, WorkScheduleItem. |
| 5. What screenshots / Print examples will eventually be needed? | Today with address + Directions. Company Today. This Week grouped by day/Project. Month calendar. Time from scheduled work. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | Schedule warnings are information only and do not block Time. Missing job-site address omits Directions; that is not a blocking warning. Time does not change Schedule. |
| 7. Desktop / iPhone / Print relevance | iPhone Field is the accepted physical surface. Desktop plans dates. Print later. Home Screen is an iPhone install topic, not a CalibraytAI navigation feature. |
| Do not | Final Manual prose. Unstable screenshots. Embedded maps. Custom return button. PERF. Claim FG-035 closed. |

### MANUAL IMPACT — SCH-D JOB-SITE LOCATION / DIRECTIONS UAT CORRECTION (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D job-site location + Directions physical UAT correction |
| Product status at capture | **SUPERSEDED AS CURRENT** by SCH-D PHYSICAL IPHONE UAT PASS. G2/G3/G4 later **PHYSICAL PASS**. |
| 1. What new contractor capability exists? | Scheduled Field work shows the job-site address. Directions hands that destination to the phone’s maps app. |
| 2. When would the contractor use it? | Opening Today, Company today, or This week to see where the job is, then tapping Directions to get there. |
| 3. What workflow will the final Manual need to teach? | How do I get directions to today’s job? See the job address. Tap Directions. Use the phone’s navigation. |
| 4. What contractor-facing terms must be used? | Address. Directions. Today. Company today. This week. Do **not** use: maps.apple.com, daddr, geocode, URI, GPS. |
| 5. What screenshots / Print examples will eventually be needed? | Today work with address + Directions. Company Today. This Week grouped by day/Project. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | If a Project has no address, Directions is not shown. That is not a blocking warning. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Today / Company Today / Week. Month calendar layout preserved. Time unchanged. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim G2/G3/G4 physical PASS. Embedded maps. GPS. PERF. |

### MANUAL IMPACT — SCH-D ADDRESS / DIRECTIONS / MONTH CALENDAR (2026-09-17)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Project address, Directions, Month calendar + day detail |
| Product status at capture | **SUPERSEDED AS CURRENT** by SCH-D JOB-SITE LOCATION / DIRECTIONS UAT CORRECTION. G5 Month **PHYSICAL PASS**. G1/G6 later PASS. |
| 1. What new contractor capability exists? | Field shows the Project/job-site address with the work. Directions sends that address to the phone’s mapping app. This Month is a calendar; tap a day to see that day’s work below. |
| 2. When would the contractor use it? | Opening Today / Company Today / This Week to see where the job is. Tapping Directions to get there. Opening This Month to see when work is happening, then tapping a day. |
| 3. What workflow will the final Manual need to teach? | Where is today’s job? How do I get directions to the job? How do I see where I’m working this week? How do I use the Month calendar? How do I tap a day to see its work? |
| 4. What contractor-facing terms must be used? | Project. Address. Directions. Today. Company today. This week. This month. Previous month. Next month. No scheduled work for this day. Do **not** use: maps.apple.com, daddr, geocode, URI, GPS, navigation provider. |
| 5. What screenshots / Print examples will eventually be needed? | Today with address + Directions. Company Today grouped. Week with address once per Project. Month calendar + selected-day detail. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | If a Project has no address, Directions is not shown. Directions does not track the worker. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Today / Company Today / Week / Month. Desktop office Project Address remains the source. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim Month or Directions physical PASS. Embedded maps. GPS tracking. Landscape work. PERF. |

### MANUAL IMPACT — SCH-D UX #5 (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Time Date, Field landscape, Back to Today |
| Status | **SUPERSEDED AS CURRENT** by SCH-D ADDRESS / DIRECTIONS / MONTH CALENDAR. Date **PHYSICAL PASS**. Portrait **PASS**. Enter Time speed **QUICK**. F4 Back to Today **PHYSICAL PASS / IMMEDIATE**. |
| 1. What new contractor capability exists? | One Date control with no blank extra box. Today and Time use the wide landscape Field shell. Back to Today should feel like other Field pages. Native calendar chrome on Date is not shown. |
| 2. When would the contractor use it? | Entering Time. Rotating the phone. Returning from Time to Today. |
| 3. What workflow will the final Manual need to teach? | Open Time. Choose Date. Rotate for landscape. Back to Today. |
| 4. What contractor-facing terms must be used? | Date. Time. Today. Back to Today. Do **not** use: calendar-picker-indicator, IndexedDB, media query. |
| 5. What screenshots / Print examples will eventually be needed? | Time Date. Today landscape. Time landscape. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | Unchanged. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Today / Time. Desktop office unchanged. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim UX #5 physical PASS. PERF. |

### MANUAL IMPACT — SCH-D UX #4 (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Time Date containment + landscape width + Field action responsiveness |
| Status | **SUPERSEDED AS CURRENT** by SCH-D UX #5. Portrait and Enter Time speed remain physical PASS. |
| 1. What new contractor capability exists? | Time Date stays inside the Time card. Field uses the wider landscape viewport. Enter Time / Today / This Week / This Month / Company Today should feel prompt on the phone (Google Fonts no longer block Field pages). |
| 2. When would the contractor use it? | Opening Field, rotating to landscape, tapping Enter Time. |
| 3. What workflow will the final Manual need to teach? | Open Time. Date stays in the card. Rotate for a wider Field layout. Identity remains **My Work — Joel**. |
| 4. What contractor-facing terms must be used? | My Work — Joel. Date. Time. Today. Enter Time. Do **not** use: overflow, media query, viewport, IndexedDB, webfont. |
| 5. What screenshots / Print examples will eventually be needed? | Time Date inside the card. Landscape using the width. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | Unchanged. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Time / Today / Week / Month. Desktop office layout unchanged. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim UX #4 physical PASS. PERF. Record “landscape is slow.” |

### MANUAL IMPACT — SCH-D UX #3 (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Today / Time physical UX #3 (identity + Date + landscape) |
| Status | **SUPERSEDED AS CURRENT** by SCH-D UX #4. **My Work — Joel** remains a physical PASS. |
| 1. What new contractor capability exists? | Today heading **My Work — Joel** (first name). Time Date label and control are sibling fields. Landscape again uses the FG-021 two-column Field layout. |
| 2. When would the contractor use it? | Opening Today to see whose work is shown. Entering Time on iPhone in portrait or landscape. |
| 3. What workflow will the final Manual need to teach? | Open Today. Confirm **My Work — first name**. Enter Time. Rotate the phone for landscape. Schedule remains the plan. |
| 4. What contractor-facing terms must be used? | My Work — Joel. Date. Today. Time. Do **not** use: overlay, User id, overflow-x, media query. |
| 5. What screenshots / Print examples will eventually be needed? | Today **My Work — Joel**. Time Date aligned. Landscape two-column Field. Do **not** capture now. |
| 6. What warnings / validation distinctions need explanation? | Unchanged. Warnings remain information only. |
| 7. Desktop / iPhone / Print relevance | iPhone Field Today / Time. Desktop Schedule unchanged. Print future only. |
| Do not | Final Manual prose. Unstable screenshots. Claim UX #3 physical PASS. PERF. |

### MANUAL IMPACT — SCH-D UX #2 (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Today / Time presentation (physical UAT UX #2) |
| Status | **SUPERSEDED AS CURRENT** by SCH-D UX #3 above for Today identity / Time Date / landscape. Scheduled Time remains **PHYSICAL PASS**. |
| CONTRACTOR CAPABILITY | See weekday and natural date on Today. My work does not repeat the worker’s own name. On Time: **Scheduled today** then **Working somewhere else?** / **Choose different work** to record actual work that was not the plan. |
| WHEN USED | When a worker opens Field, and when Ben sends them to another job without changing the Schedule first. |
| FINAL MANUAL WORKFLOW TO TEACH | Open Today. Read the weekday and date. Read My work. Enter time from scheduled work, or tap **Working somewhere else?** / **Choose different work** and pick the work actually done. Schedule stays as planned. |
| CONTRACTOR-FACING TERMS | Today. Wednesday / natural month day. My work. Scheduled today. Working somewhere else? Choose different work. Send time. Do **not** use: overlay, ad-hoc assignment record, RBAC. |
| WARNINGS / VALIDATION | Warnings remain information only. Time does not update Schedule. Unscheduled valid work remains choosable. |
| DESKTOP | Schedule planning unchanged. |
| IPHONE | YES — Field Today / Time. Scheduled Time physical PASS. Overall physical UAT **not closed**. |
| PRINT | Future relevance; do not implement. |
| SCREENSHOTS NEEDED LATER | Today weekday/date. Time Scheduled today + Choose different work. Do **not** capture now. |
| EVERYDAY TASKS | What if Ben sends me to another job? What if the work I actually did was not on my Schedule? Answer: Choose the work you actually performed when entering Time. |
| HELP / VOICE | Future topics: What if Ben sends me to another job? What if the work I actually did was not on my Schedule? |
| Do not | Final Manual prose. Unstable screenshots. PERF/LEARN planned-versus-actual. Auto-updating Schedule from Time. |

### MANUAL IMPACT — SCH-D (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-D Field Today / Week / Month + schedule-assisted Time |
| Status | **SUPERSEDED AS CURRENT** by SCH-D UX #2 above for Time/Today presentation. SCH-D product remains **IMPLEMENTED / TESTED.** Scheduled Time later recorded **PHYSICAL PASS**. |
| CONTRACTOR CAPABILITY | See **My work** for today, this week, and the next few weeks. Open **Company today** to see what the company has scheduled today. On Time, use **Scheduled today** as a suggestion, then still choose the work and hours. |
| WHEN USED | When a worker opens Field to see what they are supposed to do, or when an owner/manager wants a read-only look at company work today. |
| FINAL MANUAL WORKFLOW TO TEACH | Open Field **Today**. Read **My work**. Use **This week** / **This month**. Optionally open **Company today**. Tap **Enter time**. On Time, use **Scheduled today** or choose other work. Warnings do not stop Time. Dates are planned on desktop, not on the phone. |
| CONTRACTOR-FACING TERMS | Today. This week. This month. Company today. My work. Assigned to me. Crew work. Not assigned. Enter time. Scheduled today. You can use this scheduled work, or choose other work. Choose the work you actually did. This is information only. You can keep working. What the company has scheduled today. This does not change dates. Do **not** use: RBAC, overlay, projection, DAG, WorkScheduleItem. |
| WARNINGS / VALIDATION | **Warning:** informational only; does not block Time. **Validation:** Field does not edit Schedule. Time still requires confirmed work and hours. |
| DESKTOP | Plans dates and assignments. Company Schedule / Hub unchanged. |
| IPHONE | YES — Field views. Physical iPhone UAT **NOT CLAIMED**. |
| PRINT | Future relevance; do not implement. |
| SCREENSHOTS NEEDED LATER | Field Today / Week / Month. Company today. Time Scheduled today. Do **not** capture now. Physical iPhone screenshots wait for later authorized UAT. |
| EVERYDAY TASKS | What am I supposed to do today? What does the company have scheduled today? How do I enter time against scheduled work? |
| HELP / VOICE | Future topics only. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Field Schedule editing. Company-wide Unassigned on ordinary worker Today / Week / Month. Automatic Time. Physical iPhone PASS. |

### MANUAL IMPACT — SCH-C (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-C Lightweight Element dependencies + sequence warnings |
| Status | **SUPERSEDED AS CURRENT** by SCH-D capture below. SCH-C product remains **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.** Additive **`f9b0c1d2e3f4`**. Live current = repository head. Live UAT on Project **47** confirmed this contractor copy. No workflow/copy change from UAT. |
| CONTRACTOR CAPABILITY | Set which major work should come before other work. Under **Work order**, say which work **comes after** other work. This does not move dates by itself. |
| WHEN USED | When planning the order of major Project work. |
| FINAL MANUAL WORKFLOW TO TEACH | Add a **Comes after** / **Must follow** relationship. Remove it. Understand a **Schedule warning** when work is scheduled before prior work is finished. Understand a **Schedule warning** when work is scheduled but the prior work does not have dates yet. Optionally **Change dates** or **Review this project**. **Leave dates as they are**, or ignore the warning and continue. |
| CONTRACTOR-FACING TERMS | Work order. Comes after. Must follow. Add work order. Prior work. Schedule warning. Scheduled before prior work is finished. Scheduled, but the prior work does not have dates yet. Leave dates as they are. Change dates. Review this project. This is information only. You can continue without changing anything. Do **not** use: DAG, edge, node, graph, ProjectWorkDependency, dependency_id. |
| WARNINGS / VALIDATION | **Warning:** informational only; does not block work. **Validation:** an invalid relationship or a loop cannot be saved. |
| DESKTOP | YES — Company Schedule and Project Hub Schedule. |
| IPHONE | SCH-D / future. |
| PRINT | Future relevance; do not implement. |
| SCREENSHOTS NEEDED LATER | Work-order / sequence controls. Sequence warning. Project Schedule / Hub context. Do **not** capture now. |
| EVERYDAY TASKS | How do I tell CalibraytAI what work comes first? What does this Schedule warning mean? How do I move work after reviewing a warning? |
| HELP / VOICE | Future topics only. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Automatic date movement. |

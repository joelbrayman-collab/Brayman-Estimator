# Field time: screens, buttons, statuses and messages (22 Oct 2026)

This is a plain record of what the crew and the office see, for Field Crew training and UAT to follow.
There is one timekeeping system: Time Entry (FG-035). Synthetic names below.

## Statuses

| Status shown | Meaning |
|---|---|
| Submitted | Sent by the worker, waiting for approval. Not yet actual labour. |
| Returned | The office sent it back with a reason. The worker fixes it and sends it again. |
| Approved | Counts as actual labour hours and cost, updates banked hours, and goes to QuickBooks Time (when switched on) or the hand-entry QuickBooks time file. |
| Replaced | An approved entry the office corrected later. The original is kept; the correction is a new entry. |

History on each entry (office: Time review → open the entry → History): Submitted, Returned (with the
reason and the hours at that time), Sent again, Approved, Replaced. Nothing is deleted.

## Crew, on the phone (Field)

**Today** (`/field/today`)
- Each scheduled job card has **Enter time**.
- Without a chosen job: **Choose Project**, **My time** and **Shop / Company Work** (once set up). With a chosen
  job: Capture, **Time**, Extra work, **My time**, **Shop / Company Work**, Change project.
- **Banked hours** card (once the owner has entered the hours policy): the balance in large figures, this week
  (worked approved · regular · extra · banked), the company's policy in one line, and **See banked hours**.
- When time was returned: a red line at the top, "1 time entry was returned to you. Fix and send again on
  My time." It opens My time.

**Time** (`/field/projects/<job>/time`)
- Date (today by default; future dates are refused).
- **Scheduled today**: one button per piece of work the office scheduled for the person today. If the
  office scheduled a work item with several works under it, the button opens the **Work** box with only
  that item's works; choose one. If it has one work, it is filled in.
- **Recent work**: the last works the person used on this job.
- **Choose different work** opens **Work item** and **Work**.
- **Hours** (0.25 steps, at most 16 on one entry, at most 24 in a day). **Note** (optional).
- **+ Extra work** (customer jobs only): "What did the customer ask for?" — records the hours as extra work.
- **Send time**. Message: "Time sent for approval." (after a fix: "Time sent again for approval.").
- Messages when something is missing: "Choose the work you did.", "Choose the work you did on
  <work item>.", "Enter the hours worked.", "Time cannot be recorded for a future date.",
  "Hours for one day cannot be more than 24.00."

**My time** (`/field/time`)
- "This week (from Mon …): N hours · Approved · Waiting · Returned".
- The **Banked hours** card (as on Today).
- **Time** for the chosen job (or **Choose a job for time**), and **Shop / Company Work** once the office
  has set it up.
- Each entry: date · status, job, work item — work, hours · kind of work (Original work, Change order work
  · CO number, Extra work, Company time), note.
- Submitted: "Waiting for approval. Ask the office if something is wrong; they can return it to you."
- Returned: "Returned: <reason>" and **Fix and send again** (opens Time with the entry filled in).
- Crew never see rates, costs, prices or pay. Field-only crew cannot open office pages.

**Shop / Company Work**: the Time page for "Shop / Company Work" ("Shop / Company Work: paid company time, not
a customer's job, never billed to a customer. Choose the kind of work below."). Categories: Shop and yard,
Equipment and vehicle upkeep, Material pickup and deliveries, Safety meetings and training, Office and
estimating, and any the office adds. No Extra work button. It does not change the job the person is on today.

**Banked hours** (`/field/banked-hours`): the card, then the history: each week earned (with that week's
worked, regular and extra hours), time off taken, adjustments, and the reason. Hours only.

## Office (desktop)

**Time review** (`/time`; from a job's Project page → Time → **Review time**, or ask Cal for time review)
- Filters: From, To, Worker, Project, Status. Default: the last seven days.
- "Hours in this view": by status, and by kind of work (Original work, Change order work · CO, Extra work,
  Company time).
- **Set up Shop / Company Work** (once): "Shop / Company Work is ready. Crew choose Shop / Company Work on My
  time; it is never billed to a customer." It opens **Shop / Company Work** (`/time/company`): categories
  (add more), approved hours by category, entries. The company-time record is never listed, searched or
  counted as a customer job (projects, clients, Cal, Workflow Guide, estimates, change orders, invoices,
  QuickBooks customers); its project pages lead here.
- A **QuickBooks Time** column: the transfer status of each approved entry. Links: QuickBooks Time transfers ·
  Banked hours.
- Tick Submitted rows and **Approve selected** ("Approved 1 time entry."). Click a date to open one entry.

**One entry** (`/time/<id>`)
- **Approve** → "Time approved."
- **Return reason** + **Return** → "Time returned." (a reason is required: "Say why the time is being returned.")
- Approved entries: **Correct approved time** (hours, date, reason) → "Approved time corrected. The
  original entry is kept." The same QuickBooks Time timesheet is updated and banked hours get a difference row.
- After approving (one, selected, or a correction): "Sent to QuickBooks Time: N." when switched on, or "Not
  everything reached QuickBooks Time. Open QuickBooks Time transfers to fix and retry."
- A **QuickBooks Time** panel on approved entries: status, timesheet number, reason if it failed.
- Nobody can approve or return their own time: "You cannot approve or return your own time."

**Project page → Labour** (`/projects/<job>#hub-labour-cost`): "Estimated and actual labour": one row each
for Original work, each change order, Extra work (not on an approved change order) and, on the company-time
project, Company time; then All labour. Columns: Estimated hours, Actual hours, Difference, Estimated cost,
Actual cost, Difference, Waiting for approval. Actual = approved hours × the company costing rate on the
Labour rates page in force on the work date (work before the first rate uses that first rate). Wages and
payroll are never used. Estimated cost uses the estimate's own labour rate where the work came from an
estimate.

**Company → Accounting → Crew hours and payroll**: QuickBooks Time transfers, Banked hours, Hours policy, Shop /
Company Work — see `docs/operations/quickbooks-time.md` and `docs/operations/payroll-suzanne.md`.
**Approved time (hours to enter by hand)** and **Check time in QuickBooks** (the fallback while QuickBooks Time
is off): see `docs/operations/quickbooks.md`. An entry goes one way only: once QuickBooks Time has (or may
have) it, it leaves the hand-entry file.

## UAT exercise (what the release walk does: `tools/release/evidence_field_time.mjs`)

1. Kevin (phone): Today → Enter time → Scheduled today → choose Forms → 8 → Send time; then Stair landing
   framing 3 hours. My time shows both Submitted, 11.00 this week.
2. Ben (desktop): Project page → Review time → open the 8-hour entry → Return with a reason; open the 3-hour
   entry → Approve.
3. Kevin: Today shows the returned line → My time → Fix and send again → 7.5 → Send time.
4. Ben approves; History shows Submitted 8.00, Returned 8.00 (reason), Sent again 7.50, Approved 7.50.
5. Ben: Set up shop and company time. Kevin: My time → Shop / company time → Equipment and vehicle upkeep
   1.5. Ben: tick it → Approve selected.
6. Project page: Original 40.00 estimated / 7.50 actual, $2,600.00 / $487.50; the change order 10.00 / 3.00,
   $650.00 / $195.00. Shop time is not on the customer's job.
7. Kevin cannot open the project page, Time review, Accounting or Labour rates.
8. Ben: Accounting → Approved time → Download the file (12.00 hours); the next file has nothing new;
   Check time in QuickBooks with the report → matches.

## UAT exercise: payroll handoff (`tools/release/evidence_time_payroll.mjs`)

1. Ben (desktop): Getting Started → Hours and banked time → the hours policy form is empty → enters 8 hours
   normal week, extra after 8, banked, 1.5 per extra hour, Shop / Company Work counts, Monday, this Monday →
   Save hours policy. Getting Started shows the step done.
2. Ben: Set up Shop / Company Work; People and job links: Kevin and the job to the (test) QuickBooks Time
   person and job code.
3. Kevin (iPhone width): Today → Time → 10 hours → Send time; Shop / Company Work → Safety meetings and
   training → 1 → Send time.
4. Ben: Time review → tick both → Approve selected → "Sent to QuickBooks Time: 2." → the QuickBooks Time column
   says In QuickBooks Time.
5. Kevin: Today shows Banked hours 4.50 (11 worked, 8 regular, 3 extra × 1.5) and the policy line; See banked
   hours shows the week. No money anywhere, no sideways scrolling.
6. Ben: Correct approved time 10 → 9 → the transfer is updated (correction), Kevin's balance 3.00. Check
   QuickBooks Time → match. Banked hours → Kevin → Record time off 2 → balance 1.00.

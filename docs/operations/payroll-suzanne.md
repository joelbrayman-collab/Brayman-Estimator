# Payroll with CalibraytAI — for Suzanne (22 Oct 2026)

The crew enter their hours once, on their phones, in CalibraytAI. The office checks and approves them. Approved
hours then go to QuickBooks Time by themselves, and from there to QuickBooks Online Payroll. You do not type
hours in twice.

Until Joel switches the QuickBooks Time connection on, nothing is sent: approved hours wait on the QuickBooks
Time page, and the hand-entry file (Accounting → Approved time) still works as before.

Where things are (office computer): **Company → Accounting → Crew hours and payroll**:
QuickBooks Time transfers · Banked hours · Hours policy · Shop / Company Work. Time review is on the same
links, and on each job's page (Time → Review time).

## Every week

1. **Review the hours.** Time review (`/time`). It opens on the last seven days. Change From / To for the pay
   week. Check each person's hours, work and notes. Extra work is highlighted.
   - Right: tick the rows and press **Approve selected**. Or open one row and press **Approve**.
   - Wrong: open the row, write why in **Return reason**, press **Return**. The worker sees the reason on the
     phone, fixes it and sends it again; it comes back to you as Submitted.
   - You cannot approve your own time; someone else in the office does.
2. **Watch it go to QuickBooks Time.** After approving you see "Sent to QuickBooks Time: N." The
   **QuickBooks Time** column on Time review shows "In QuickBooks Time" for each row.
   If you see "Not everything reached QuickBooks Time", go to step 4.
3. **Run payroll** in QuickBooks Online Payroll as you do now. The hours come from QuickBooks Time.
   (If your QuickBooks Time account asks for time to be approved there too, approve the week there first.)
4. **Fix anything that did not go** — QuickBooks Time transfers (`/time/quickbooks-time`):
   - "Needs a link": a person, job or Shop / Company Work category is not linked yet. Press **Add the link**
     (the owner does this: People and job links), then **Retry**.
   - "Failed — retry": read "What to do" on the row, fix it, press **Retry**. Retry is always safe: CalibraytAI
     checks QuickBooks Time first and never enters anything twice.
     - "access token was refused": the QuickBooks Time token expired. Ask Joel; then Retry.
     - "slow down": wait five minutes, then Retry.
     - "the week may be approved or locked there": unapprove that week in QuickBooks Time, Retry, approve again.
     - "something was missing or wrong": check the person's and the job's links.
   - "In a hand-entry file (not sent)": these hours were already typed into QuickBooks from the old file. Leave
     them. Only if that hand entry was deleted in QuickBooks, write why and press **Send anyway**.
5. **Check (once a week)**: QuickBooks Time transfers → **Check QuickBooks Time** → the pay week → **Check**.
   It only reads. It lists: match; different there (someone changed it in QuickBooks Time — change it back
   there, or correct it here); sent but no longer there (Retry creates it again); in QuickBooks Time more than
   once (delete the extra one there); entered directly in QuickBooks Time (make sure it is not a double);
   approved here but not sent yet.

## Correcting hours after approval

Open the entry on Time review → **Correct approved time** → the right hours (and date if needed) and the
reason → press it. CalibraytAI keeps the original, records the correction, changes the **same** timesheet in
QuickBooks Time, and fixes the banked hours. Nothing is deleted. If the week is already approved and locked in
QuickBooks Time, unapprove it there first, then press Retry on the transfer.

## Banked hours

- **Banked hours** (`/time/banked-hours`) shows everyone's balance and the company's hours policy in one line.
  Open a person for their ledger: each week's hours worked, regular hours, extra hours and hours banked; time
  off taken; adjustments; who did each and why.
- **Record time off taken**: open the person → Day off, Hours, What for → **Record time off**. It cannot be
  more than their balance.
- **Adjust**: Hours (2 adds, -2 removes) and Why → **Adjust**. Use it only for agreed corrections.
- You cannot change your own banked hours; someone else in the office does.
- Banked time off is **not** sent to QuickBooks Time yet: pay it in payroll from this page (see the questions
  below).
- The crew see their own balance on the phone (Today, My time, See banked hours). They never see pay or rates.

## Shop / Company Work

Paid time that is not for a customer: shop and yard, equipment and vehicle upkeep, material pickup and
deliveries, safety meetings and training, office and estimating. Crew press **Shop / Company Work** on Today or
My time. You approve it like other time. It goes to payroll (to the Shop job code in QuickBooks Time) and
counts toward banked hours if the hours policy says so. It is never charged to a customer's job or invoiced.
Add a category: Accounting → Shop / Company Work → New category → Add.

## The hours policy (the owner sets it)

Getting Started → **Hours and banked time**, or Accounting → **Hours policy** (owner or System Administrator).
Every value is entered by the company; nothing is filled in for you:
normal work week (hours) · extra hours start after (hours in a week) · extra hours are banked or paid as
overtime · banked hours for each extra hour · whether Shop / Company Work counts · the day the week starts ·
the date it takes effect. Nothing is banked until it is saved. A change takes effect from its date; earlier
weeks keep the rules they were worked under. Every change is listed with who, when and old → new.

## For Joel and Suzanne to decide before banking starts (not built into the screens)

These are policy and payroll decisions, not software settings CalibraytAI can decide:

1. **The numbers.** Joel's normal week is 40 hours. Under Ontario's *Employment Standards Act, 2000*, overtime
   is generally owed after **44 hours** in a work week, at **1.5×** the regular rate. So "extra hours start
   after" could be 40 (bank everything over 40) or 44 (bank or pay only the statutory overtime), with a bank rate
   of 1 or 1.5. Source summary: Gowling WLG, *Navigating overtime rules under the Ontario ESA* (2024),
   https://gowlingwlg.com/en/insights-resources/articles/2024/navigating-overtime-rules-under-the-ontario-esa
2. **Time off in lieu of overtime pay** under the ESA needs a **written agreement** with each employee; it is
   **1.5 hours off for each overtime hour**; and it must be taken within **3 months** of the work week (or
   **12 months** if the employee agrees), otherwise the overtime is paid. CalibraytAI records hours and the
   policy you enter; it does not track agreements, expiry or pay-out. Keep the signed agreements on file.
3. **Averaging agreements** (overtime averaged over up to 4 weeks) also need a written agreement; CalibraytAI's
   week is one week.
4. **Hours between 40 and 44.** Banking them is a company practice, not statutory overtime: decide the rate.
5. **Payroll treatment.** If banked, QuickBooks Time/Payroll must not also pay those hours as overtime. When
   banked time is taken, how is it paid (a PTO job code in QuickBooks Time, or entered in payroll)?
6. **Shop / Company Work** — counts toward the week (normally yes: it is paid work).
7. **Who may record time off and adjustments** (today: any office person except for themselves).
8. **Start date** for banking.

Confirm these with your accountant or employment lawyer before saving the policy.

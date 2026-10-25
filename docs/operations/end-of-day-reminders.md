# End-of-day reminders (25 Oct 2026)

Part of the Magnificent Seven everyday operations (`docs/operations/everyday-operations.md`). Code:
`app/services/reminders.py`; command `flask reminders send-due`; settings page `/operations/reminders` (owner or
System Administrator changes them; others can read).

## What is sent, to whom

- **Crew** (each person booked today, Field-only crew included): what they still have to do today, live from the
  records — enter today's hours; today's job update for each job they were on; a change to tomorrow's work made today;
  returned time entries to fix; the office's question on extra work they reported. Nothing listed → nothing sent.
- **Owner and System Administrators** (Ben): the counts on WHAT NEEDS MY ATTENTION? (time to approve, material
  requests, extra work, delivery items, supplier prices, receipts, QuickBooks items — including projects to confirm —,
  job problems, schedule conflicts).
- **Once a day per person** (dedupe key `company:person:audience:date`; a second run makes none).
- **When**: between the company's reminder time and latest time (defaults 16:30 and 20:00) on its working days
  (default Monday–Friday), in the company's clock (`app/services/local_time.py`, America/Toronto).

## In the app or by text

- Every reminder is **in the app**: Field Today (crew) shows "Before you finish today"; Home (owner) shows the
  attention list. Read / dismiss on Field Today.
- By **text** only when all three hold: the person chose "Also by text" (Field → Texts; default off), they consented
  to texts (existing SMS consent, `docs/operations/sms-notifications.md`), and texting is switched on (Twilio
  activation). Otherwise the reminder says **"Texts not switched on"** and stays in the app. Texts carry counts and
  a link only — no names, amounts or job details.

## Schedule (Render cron job — document only; not created by this build)

| Name | Command | Schedule |
|---|---|---|
| End-of-day reminders | `flask reminders send-due` | `*/15 * * * *` (every 15 minutes) |

Same environment group as the web service. Safe to run as often as wanted; it prints counts only
(`companies=… crew=… owner=… texts=… already=… not_due=… nothing=…`). The owner's **Make reminders now** on
`/operations/reminders` runs the same thing for one company.

## Tests

`tests/test_magnificent_seven.py` (crew and owner content, dedupe, window and working days, consent, "Texts not
switched on", Twilio test transport only) and `tools/release/evidence_magnificent_seven.mjs`.

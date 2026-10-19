# G1 — Crew notification when work dates change: bounded recommendation (NOT implemented)

Status: review only. Nothing here is built or switched on. Turning on any email or text to crews needs Joel's separate approval.

## 1. What exists today (facts, with file:line)

- **Every date change is already recorded in one place.**
  - All three ways of moving work end in `_record_history` with event `DATES_CHANGED`: `update_schedule_window` (`app/services/schedule.py:430`), `schedule_activity_with_element_adjustment` (`:499`) and `shift_project_schedule` (`:596`).
  - The history row stores who moved it, when, and the old and new dates (`schedule.py:267-300`; model `WorkScheduleHistory` in `app/models/schedule.py:152`).
  - Each of the three ends with one hook after the commit, `_propose_linked_deliveries()` (`schedule.py:495`, `:592`, `:649`). This is today's single point where "work moved" is known after saving, and the natural place for crew notices.
- **Who is on the work.**
  - Direct assignments: `WorkScheduleAssignment.worker_user_id`.
  - Crew assignments: `crew_id`. The members on given dates come from `users_on_crew_during_window` (`app/services/organization_crew.py:147-169`, which uses membership effective dates).
  - `worker_assigned_on_date` (`schedule.py:1461`) already combines direct and crew assignment for one day.
- **Email.** `send_transactional_message` (`app/services/transactional_email.py:333`) writes one `TransactionalMessage` row per attempt. The statuses (`app/models/transactional_message.py:25-29`):

  | Status | Meaning |
  |---|---|
  | `LOCAL_CAPTURED` | Written to a file on the server, **not delivered**. This is the default when `TRANSACTIONAL_EMAIL_PROVIDER` is not `postmark` (`transactional_email.py:323-331`, `:200-228`). |
  | `ACCEPTED` | Postmark took the email. |
  | `FAILED` | The provider refused it, or there was a transport error. |
  | `FAILED_CONFIG` | Postmark was selected but `POSTMARK_SERVER_TOKEN` is missing (`:246-252`). |
  | `SKIPPED_ALLOWLIST` | `TRANSACTIONAL_UAT_ALLOWLIST` is set and the recipient is not on it (`:359-377`). |

  The templates are a fixed list (`transactional_message.py:16-22`). A crew notice needs a new template id.
- **Texts.** `send_text_to_user` (`app/services/text_messages.py:90-95`) sends only if the person saved a mobile number **and** ticked consent (`NotificationContact.sms_opt_in`, `app/models/supplier_portal.py:249-260`). `send_text` (`text_messages.py:97-121`) writes a `TextMessage` row with one of these statuses:
  - `SENT`;
  - `FAILED`;
  - `NOT_CONFIGURED` (`TWILIO_SETTINGS_MISSING`);
  - `LOCAL_CAPTURED` (in tests).

  Texting needs `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` and `TWILIO_FROM_NUMBER` (`text_messages.py:86-87`). Without them, every text is recorded as not sent.
- **How supplier notices are sent today, the model to copy.** `supplier_hub._send` (`app/services/supplier_hub.py:989-1009`):
  - removes duplicate recipients by user id;
  - sends an email and an optional text;
  - never lets a notice failure block the schedule change. Exceptions are swallowed, so the failure is visible only in the message rows.
- **Production settings, names only.** Email is delivered only if all of these are set in Render:
  - `TRANSACTIONAL_EMAIL_PROVIDER=postmark`
  - `POSTMARK_SERVER_TOKEN`
  - `TRANSACTIONAL_FROM_EMAIL`
  - optionally `TRANSACTIONAL_FROM_NAME`, `TRANSACTIONAL_REPLY_TO` and `PUBLIC_BASE_URL`

  `TRANSACTIONAL_UAT_ALLOWLIST` must be empty for everyone to receive email. I did not read production, so **whether email is actually delivered today is unverified**.

## 2. Recommendation

### Who gets a notice
1. **Directly assigned workers** on the moved item (`worker_user_id`).
2. **Crew members** of an assigned crew who are members on any day of the **old or the new** dates. That covers someone who was expecting to work and someone who now needs to. Use `users_on_crew_during_window` over each range.
3. Only **active users with an active membership in the same organization**. Never suppliers, clients or anyone in another organization.
4. **Not** the person who made the move, unless they are also on the work.

### One message per person per change
- **One message per person** per move, even when they are both directly assigned and on the crew. Remove duplicates by user id, as `_send` does.
- **Whole-project moves become one message.** `shift_project_schedule` moves every item at once; each person gets a single message listing only *their* items, with old and new dates. Do this by collecting the moves in `db.session.info` (the existing `schedule_moves` pattern, `schedule.py:296-298`), extended with `prior_end`, `new_start`, `new_end` and the history row id. Then send once per person in the same post-commit hook.
- **Quick repeated moves:** one of these two approaches, and I recommend the first:
  - **(a) Short delay and replacement (recommended):** hold notices for ~5 minutes in a small outbox table. A later move of the same item replaces the waiting notice, and the message shows the original old date and the final new date.
  - **(b)** Send at once, and add "this replaces the earlier notice" when a notice for the same item went out within the last hour.

  Approach (a) needs a small outbox table and a sender: a request-time flush or the existing app process. **No new external service or scheduler** is required: on each request, send outbox rows older than 5 minutes.

### What the message says
- Use the history row's old and new dates (`WorkScheduleHistory` `prior_scheduled_start` / `prior_scheduled_end` / `new_scheduled_start` / `new_scheduled_end`), never recomputed values.
- **Content:** the project name, the work name, "moved from <old dates> to <new dates>", who moved it, and a link to Field Today or Week. **No prices, costs, client contact details, notes or appointments.** Personal appointments are never part of construction notices.
- **Email** uses a new `CREW_SCHEDULE_CHANGE` template.
- **A text** is sent only with consent, under 160 characters where possible.

### Delivery status and failures
- Every attempt is already recorded: `TransactionalMessage` and `TextMessage` rows, with `related_type="work_schedule_item"`, `related_id=<item>`.
- **Office visibility:** a "Notices" line on the item's history, or on Company Attention, for the last move: for example "Sent to 3 · 1 not delivered (no email provider) · texts not configured".
- **Retry:** one automatic retry for `FAILED` email after 10 minutes. No retry for `FAILED_CONFIG`, `NOT_CONFIGURED` or `SKIPPED_ALLOWLIST`, which are settings problems. Those are shown to the office instead.
- A notice **never** blocks or rolls back the schedule change (same rule as `_send`).

### Preferences
- Per person: Email on/off, plus Text on/off for those who have consented to texts. Store this on `NotificationContact`, or in a small preferences table.
- **Default:** email on for crew; text off until the person opts in, as now.

### No-external-service option (can go first, needs no approval for messaging)
- A banner in **Field** ("Your schedule changed: Footings moved Tue → Thu") for each person, shown until they tap "Got it".
- It is built from history rows newer than the person's last acknowledgment, which needs a per-person "seen up to" timestamp.
- It sends nothing outside the app and pairs with the G5 freshness fix.

## 3. Size, files and tests
- **Files:**
  - `app/services/schedule.py`: pass `prior_end` and `new_*` into the hook;
  - a new `app/services/crew_notices.py`: recipients, duplicate removal, message text, outbox;
  - `app/models/transactional_message.py`: the new template id;
  - `app/services/transactional_email.py`: the template body;
  - a migration: the outbox table, preferences, and the Field "seen up to" timestamp;
  - Field template and banner;
  - an office "Notices" line.
- **Tests to add:**
  - direct only;
  - crew only, with membership dates: someone who joins after the old dates gets the notice only if they overlap the new dates;
  - direct and crew together gives one message;
  - a whole-project move gives one message per person;
  - a move followed by another quick move gives one combined notice (with (a));
  - another organization's users are never selected;
  - message content has no price, client or notes;
  - email status on each provider setting;
  - text sent only with consent, and `NOT_CONFIGURED` without Twilio;
  - a notice failure does not block the move;
  - the Field banner appears, then clears once acknowledged.
- **Estimated size:**
  - Field banner alone: about half a day, with a small migration.
  - Email/text notices with the outbox and status line: about 1.5–2 days, including tests.

## 4. Needs Joel's approval
1. Switching on crew emails, and texts if wanted. Today nothing is sent to crews.
2. Confirming production email settings (`TRANSACTIONAL_EMAIL_PROVIDER=postmark`, `POSTMARK_SERVER_TOKEN`, sender address), and Twilio if texts are wanted.
3. The quick-move policy: (a) delay and replace, or (b) send at once.
4. Whether the person who made the move also receives a copy.
5. The migration for the outbox, preferences and banner state.

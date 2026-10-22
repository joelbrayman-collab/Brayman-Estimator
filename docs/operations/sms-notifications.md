# Schedule-change text messages (SMS) to crews

Status (22 Oct 2026): **implemented and tested, not switched on.** Joel decided SMS notifications are mandatory for
V1. Nothing is sent to a real phone until Joel provides the Twilio items in section 6 and authorizes production
activation. Until then each notice is worked out and listed for the office, and each text is recorded as
"Not sent: texting is not switched on".

Design: [G1](../planned/crew-schedule-change-notifications.md). Code: `app/services/crew_notices.py` (who, when, what),
`app/services/text_messages.py` (the one sending path for every text, consent, Twilio, callbacks, retry),
`app/routes/sms_notifications.py` (pages), `app/models/sms_notification.py` (tables), migration
`m8s4n2c6t1q7_sms_schedule_notifications.py`. Tests: `tests/test_sms_schedule_notices.py`. Browser walk:
`tools/release/evidence_sms_notifications.mjs`.

## 1. What happens

1. The office changes scheduled work through the existing scheduling authority (Calendar, Set dates, Assign,
   Remove, Retire, Move project). The schedule records the change in `work_schedule_history` as it always did.
2. In the same database transaction, CalibraytAI works out the **directly affected workers**: people assigned to
   the work, and members of an assigned crew on the **old or the new** dates (membership dates count), active
   members of the same company only. It writes one waiting row per worker per piece of work in
   `sms_schedule_notices`, keeping the worker's schedule **as it was before the first change**. A change that is
   rolled back leaves no notice. A notice problem never blocks or undoes the schedule change.
3. **Coalescing.** Further edits to the same work for the same worker update that row and push its send time back.
   A worker's waiting rows go out together as **one text** once nothing about their schedule has changed for
   `SMS_NOTICE_COALESCE_SECONDS` (default 300, G1 option (a)). A whole-project move is one text per worker.
4. When the quiet period ends, the saved schedule is compared with the "before" snapshot:
   - **Moved**: `Footings (Merrickville) moved: Mon Nov 2 -> Wed Nov 4`
   - **Added**: `Footings (Merrickville) added: Mon Nov 2`
   - **Taken off**: `Footings (Merrickville): you are off this work (was Mon Nov 2)`
   - **Cancelled** (the dates were retired): `Footings (Merrickville) cancelled (was Mon Nov 2)`
   - Edits that cancel out (moved and moved back) send nothing (`NO_CHANGE`).
5. Not sent, and shown to the office with the reason:
   - **No consent** (`NO_CONSENT`): no mobile number or no recorded agreement.
   - **Their own edit** (`SELF`): the worker made every one of the changes themselves (for example an office
     member who assigned themselves). Decision: a text about your own edit is noise. A change by anyone else
     in the batch means the text goes out.
6. Who sends: a background sender thread in the web process (every 60 s, `SMS_NOTICE_SWEEP_SECONDS`), on by
   default on the hosted office (`CALIBRAYTAI_HOSTED=1`, off in tests; `SMS_NOTICE_SWEEPER=on/off` overrides);
   **Send waiting notices now** on the office page; `flask sms send-due` from a shell. Rows are claimed with a
   conditional update before sending, so two senders never send the same notice twice. A sender interrupted
   mid-way (restart) leaves rows marked "could not be prepared" for the office to **Send again**; they are not
   resent automatically because the text may already have gone.

### What a text says (and does not)

```
Brayman Construction: schedule change. Footings (Merrickville) moved: Mon Nov 2 -> Wed Nov 4.
Field: https://calibryatai.onrender.com/field/week
Reply STOP to stop texts.
```

- The company's display name (sender identification), the **work's name** with the **site town**, or the job
  number when the job has no town, old and new dates, and a link to Field This week (`PUBLIC_BASE_URL`, else
  `SMS_FIELD_LINK_BASE`, default `https://calibryatai.onrender.com`).
- **Never**: the customer's name, the project name (it often holds the customer's name), the street address,
  prices, costs, notes, or who made the change. Office pages show those to the office; the phone does not.
- Several changes: `Brayman Construction: 2 schedule changes.` then one `- ` line each (up to 4, then
  `- and N more`).
- Plain ASCII (`->`, `-`) so each text stays a cheap GSM-7 text (a `→` or `•` would make every segment
  Unicode, 70 characters instead of 160). A single change fits in about 160 characters.
- "Reply STOP to stop texts." is added to the **first** schedule text to a number. Twilio itself handles STOP
  on long codes and toll-free numbers (section 4).
- Times: the schedule holds dates, not clock times, so texts carry dates.

## 2. Consent and privacy

- A text goes only to a person with a mobile number and a recorded agreement (`notification_contacts`, the
  same record the supplier delivery texts use). **No consent, no text.**
- Ways to agree, each recorded in `sms_consent_events` with who, when, how and which number:
  - **primary (Joel, 22 Oct 2026): the worker, at Field setup.** The first time a worker opens Field (after setting
    their password, or from the Home Screen icon, which opens Field Today) Field Today shows one question: "Get a
    text when your schedule changes?" with their mobile number (filled in if the office saved one), the agreement
    sentence, and **Yes, text me** / **Not now**. Yes records consent (`SELF_FIELD_SETUP`, note "self, at Field
    setup"); Not now records `NOT_NOW` and texts stay off. It is asked once (any consent answer or change counts);
    Not now never blocks Field;
  - the worker, on **Field → Texts** (`/field/text-messages`): number, tick the agreement sentence
    (`CONSENT_WORDING` in `text_messages.py`), Turn on schedule texts (`SELF_FIELD`);
  - secondary: the owner or a System Administrator, on the worker's **People & Access** page, Schedule texts:
    number, how they agreed (required), and a box confirming the worker agreed (`OFFICE_ON_BEHALF`). Without the
    box the office saves the number only (no texts); Field's setup question then shows it filled in;
  - a supplier or office person on their own Text settings page (`SELF_ACCOUNT`, supplier delivery texts).
- Ways to stop, each recorded: Stop schedule texts on Field; Turn off schedule texts on People & Access (with a
  reason); replying STOP (and STOPALL, UNSUBSCRIBE, CANCEL, END, QUIT, ARRET) when the inbound webhook is set up
  (`REPLY_STOP`); Twilio refusing with error 21610 (the number opted out at Twilio, `PROVIDER`). START / UNSTOP
  after a STOP reply turns texts back on only when that STOP reply was the person's last consent change.
- A Field-only worker sees only their own setting. Office lists show only the last four digits of a number.
- Retry re-checks consent and uses the worker's **current** number.

## 3. Office visibility, failures and retry

- **Calendar → Text notices** (`/schedule/text-notices`), for anyone with scheduling authority (office members,
  never Field-only): whether texting is on, the waiting count with **Send waiting notices now**, every text
  (worker, masked number, status, failure reason, the exact words) with **Retry**, and every notice with its
  outcome (texted, no consent, no net change, their own edit, could not be prepared → **Send again**).
- The Calendar's **Text notices** link turns red with "N not delivered", and **Home** shows "N schedule texts to
  workers not delivered" when a schedule text in the last 14 days failed, was not delivered or was not sent and
  has not been retried.
- After a schedule change the office sees: "Workers on this work who agreed to texts get one text about it in
  about 5 minutes".
- Statuses (`text_messages.status`): `SENT` (Twilio accepted it: queued/sending/sent), `DELIVERED`,
  `UNDELIVERED`, `FAILED`, `NOT_CONFIGURED` (switched off or settings missing, with the reason),
  `SKIPPED_ALLOWLIST`, `LOCAL_CAPTURED` (tests). Twilio's own status, the delivery time and the retry chain are
  in `sms_text_message_details`; every verified delivery report is kept in `sms_delivery_events`. Reports can
  arrive out of order: a final status is never moved back, and replays change nothing.
- **Retry** sends the same words once more; each attempt can be retried once (a unique link in the database
  refuses a second press or a replayed form). Retry is offered for Failed, Not delivered, Not sent (not switched
  on) and Not on the test list, so texts recorded before Twilio is switched on can be sent afterwards.

## 4. Twilio (provider)

Real sending needs all of these environment settings on the hosted office (never in code or the database):

| Setting | Value |
|---|---|
| `TRANSACTIONAL_SMS_PROVIDER` | `twilio` (anything else, or unset: nothing is sent; this is the default) |
| `TWILIO_ACCOUNT_SID` | the account SID (`AC…`) |
| `TWILIO_AUTH_TOKEN` | the auth token (also verifies Twilio's callbacks) |
| `TWILIO_MESSAGING_SERVICE_SID` | preferred: the Messaging Service (`MG…`) holding the sender number(s) |
| `TWILIO_FROM_NUMBER` | or: the sender number in E.164, e.g. `+16135550100` (used only without a Messaging Service) |
| `PUBLIC_BASE_URL` | `https://…` address of the office; delivery reports go to `<PUBLIC_BASE_URL>/sms/twilio/status` |
| `TRANSACTIONAL_SMS_UAT_ALLOWLIST` | optional: comma-separated test numbers; while set, only they get texts (others `SKIPPED_ALLOWLIST`) |
| `SMS_NOTICE_COALESCE_SECONDS` | optional, default 300 |

`flask sms status` prints what the app sees (names and yes/no only). The training site (`TRAINING_ENVIRONMENT`)
never sends, whatever is set.

Webhooks to configure in Twilio (on the Messaging Service, or on the number):

- **Delivery status callback**: `https://<office address>/sms/twilio/status` (also sent per message as
  `StatusCallback` when `PUBLIC_BASE_URL` is https).
- **Incoming messages**: `https://<office address>/sms/twilio/inbound` (records STOP / START; answers empty TwiML).

Both are **public endpoints** (no sign-in, no CSRF token; added deliberately to `protect_office_routes` and the
security route sweep). Each request must carry a valid `X-Twilio-Signature`: HMAC-SHA1 with the auth token over
the full URL followed by each POST field name and value sorted by name, Base64. The URL checked is
`PUBLIC_BASE_URL` + path (Render's proxy may show `http://` internally), then the request URL, each with and
without an explicit port. Anything else gets 403 and changes nothing. A request that must not be trusted is
never written to the database.

Twilio documentation relied on:

- Messages API (create a message, `MessagingServiceSid` / `From`, `StatusCallback`):
  https://www.twilio.com/docs/messaging/api/message-resource
- Message status values and status callbacks (`MessageSid`, `MessageStatus`, `ErrorCode`; callbacks may arrive
  out of order): https://www.twilio.com/docs/messaging/guides/track-outbound-message-status
- Webhook security, validating `X-Twilio-Signature` (algorithm, ports, query string):
  https://www.twilio.com/docs/usage/security#validating-requests (the test vector in
  `tests/test_sms_schedule_notices.py` is Twilio's published example and gives `RSOYDt4T1cUTdK1PDd93/VVr8B8=`)
- Error 21610 "Attempt to send to unsubscribed recipient" (the number replied STOP; texts resume only after
  START): https://www.twilio.com/docs/api/errors/21610
- Opt-out keywords handled by Twilio by default: Twilio's help article on opt-out keywords
  (https://help.twilio.com/articles/223134027) could **not** be opened from this workspace on 22 Oct 2026, so the
  word list in `STOP_WORDS` / `START_WORDS` (STOP, STOPALL, UNSUBSCRIBE, CANCEL, END, QUIT, OPTOUT, REVOKE, ARRET;
  START, UNSTOP, YES) is from memory and must be checked against it (and against Advanced Opt-Out if the
  Messaging Service uses custom or French keywords) before switching on. Twilio's own handling blocks texts
  either way; the list only decides what CalibraytAI records.
- A2P 10DLC (US): https://www.twilio.com/docs/messaging/compliance/a2p-10dlc
- Canada SMS guidelines: https://www.twilio.com/en-us/guidelines/ca/sms

## 5. Canadian and US decision points (not legal conclusions)

These are questions for Joel (and counsel if he wants); the code makes no legal conclusion.

1. **CASL.** Text messages are electronic messages under Canada's Anti-Spam Legislation (CRTC FAQ:
   https://crtc.gc.ca/eng/com500/faq500.htm). The Act applies its consent, identification and unsubscribe rules
   to *commercial* electronic messages (definition, s. 1(2)). A work-schedule notice from an employer to its own
   worker may not be a commercial electronic message at all; and s. 6(6)(e) lists messages that "provide
   information directly related to an employment relationship … in which the person … is currently involved" among
   those exempt from the consent requirement of s. 6(1)(a) (Act:
   https://laws-lois.justice.gc.ca/eng/acts/E-1.6/page-1.html). Subcontractors and workers who are not employees
   may not fit (e). **Decision:** CalibraytAI asks for and records explicit consent from everyone anyway, identifies
   the sender (the company name) and offers STOP, which meets the stricter reading. Joel to confirm this policy
   and the consent wording (section 7).
2. **Canadian sender.** Twilio's Canada guidelines: domestic long codes are supported and keep the sender ID;
   Twilio recommends short codes or **verified toll-free numbers** for application-to-person traffic because
   Canadian carriers filter A2P traffic strictly; toll-free numbers require verification; alphanumeric sender
   IDs are not supported; honour HELP/STOP, in French too. **Decision:** a Canadian long code (613 / 343 number,
   cheapest, fine at Brayman's volume) or a verified toll-free number (more reliable delivery, verification
   takes days to weeks).
3. **US numbers.** Any text sent from a US 10-digit long code to US phones requires **A2P 10DLC** registration
   (brand + campaign, with fees and review time); toll-free and short codes are outside 10DLC. If every worker
   has a Canadian number and the sender is Canadian, 10DLC does not apply. **Decision:** confirm that no crew
   phone is a US number; if one is, register a 10DLC campaign (use case: account notifications / employee
   schedule) or use a verified toll-free number.
4. **Quiet hours.** Twilio recommends sending non-urgent messages during the recipient's daytime. Schedule
   changes made at night currently go out about 5 minutes later (Brayman crews start at 5 AM, so a late change
   matters). **Decision:** keep it, or hold texts between e.g. 9 PM and 6 AM (not built; small change).

## 6. What Joel must provide to switch it on

1. A **Twilio account** (owner: Brayman Construction), upgraded from trial (a trial only texts verified numbers
   and prefixes every text). Put `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` into the Render service environment
   (Claude can do it with Joel's authorization; the values are never written to the repository or chat).
2. A **sender**: buy a Canadian local number (or a toll-free number and complete toll-free verification), put it
   in a **Messaging Service** and give `TWILIO_MESSAGING_SERVICE_SID` (or just `TWILIO_FROM_NUMBER`).
   US 10DLC registration only if a US sender or US phones are involved (section 5.3).
3. On the Messaging Service (or number): **status callback URL** `https://calibryatai.onrender.com/sms/twilio/status`
   and **incoming message webhook** `https://calibryatai.onrender.com/sms/twilio/inbound` (or the HostPapa address
   when the office moves; `PUBLIC_BASE_URL` must be the same address). Keep Twilio's default opt-out handling on.
4. **Consent-policy approval** (section 7).
5. **Production activation authorization**: then set `TRANSACTIONAL_SMS_PROVIDER=twilio` and
   `PUBLIC_BASE_URL`, deploy the release with migration `m8s4n2c6t1q7`, start with
   `TRANSACTIONAL_SMS_UAT_ALLOWLIST=<Joel's mobile>` for one real test move, then clear the allowlist.

## 7. Consent-policy questions for Joel

1. Wording the worker agrees to (Field and the office checkbox): "I agree to receive work schedule text
   messages from my employer through CalibraytAI at this number. Message and data rates may apply. Reply STOP to
   stop." Approve or change.
2. Field setup is now the primary consent moment. Should the owner / a System Administrator still be able to turn
   texts on for a worker who agreed verbally (recorded with how and when), or only save the number for Field's
   question?
3. Subcontractors and suppliers' staff: same policy?
4. Should the person who made the change also get a copy? (Now: no text about your own edit.)
5. Quiet hours (section 5.4) and the 5-minute coalescing window: keep?
6. Keep consent and message history indefinitely (now), or delete after a period?

## 8. Running it

- `flask sms status` — settings as the app sees them.
- `flask sms send-due` — send waiting notices whose quiet period is over.
- Office: Calendar → Text notices. Owner: People & Access → a person → Schedule texts. Worker: Field → Texts.
- Release: migration `m8s4n2c6t1q7` adds `sms_schedule_notices`, `sms_text_message_details`,
  `sms_consent_events`, `sms_delivery_events` (new tables only; no existing table changes):
  `release_gate.sh … --migration-to m8s4n2c6t1q7 --new-tables sms_consent_events,sms_delivery_events,sms_schedule_notices,sms_text_message_details`.

# Calendar Integration Architecture — Outlook, Google Calendar, Apple Calendar

| Attribute | Value |
|-----------|--------|
| Date | 19 October 2026 |
| Owner direction | Joel, 19 Oct 2026 ("External Calendar Integrations — Approved Scope") |
| Applies to | CalibraytAI (built here first) and AiRIA (to adopt the reusable parts later) |
| Audience | AiRIA Architect, CalibraytAI maintainers, reviewers |
| Status | Section 3 is **implemented** (development branch `calendar/appointments-2026-10-19`, not yet released). Sections 6 to 9 are **proposed architecture only**. Nothing in them is built, registered or authorized. |

Labels used in this document:

- **IMPLEMENTED**: in the code, with tests.
- **PROPOSED**: a design for later. It needs separate approval before any build, provider registration, credential storage or new permission.
- **EXCLUDED**: deliberately not done, by owner decision.

---

## 1. Three different things

These three are often called "calendar sync". They differ in risk, consent and permissions.

| Kind | What happens | Who is source of truth | Credentials needed | Status |
|---|---|---|---|---|
| **Subscription (one-way publish)** | The platform publishes a calendar. Outlook, Google Calendar or Apple Calendar fetches it on a schedule. A single appointment can also be downloaded as a calendar file. | The platform, always. External edits cannot come back. | None from the user. A secret feed key, created by the platform. | **IMPLEMENTED** |
| **Two-way synchronization** | Events created or changed in Outlook or Google flow back into the platform, and platform changes are written into the person's calendar. | Shared, so a conflict policy is required. | OAuth consent per person (and possibly per organization), with stored access and refresh tokens. | **PROPOSED** (§6) |
| **Availability (free/busy) checking** | Before booking, the platform asks the provider when a person is busy. It gets times only, no titles. | The provider, for busy times only. | OAuth consent with a free/busy or read scope. | **PROPOSED** (§7) |

Apple Calendar is supported through **subscriptions only** (§8).

---

## 2. Design rules (both products)

1. **Publishing is one-way by default.** An outside calendar never changes a platform record automatically. Anything coming in (§6) is either applied under an explicit rule for that field, or held for review. It is never applied silently to a protected record.
2. **Consent before any connection.** Nothing connects to a person's external account without that person's explicit, revocable consent. Turning a connection off takes effect at once.
3. **Personal privacy.** A personal appointment is visible only to its owner. It is published only in the owner's own feed, and is never sent to anyone else.
4. **Organization isolation.** Feeds, keys, tokens and mappings belong to one organization and one person. A person who leaves the organization loses their feed at once.
5. **Secrets are never stored in readable form.** Feed keys are stored as hashes. OAuth tokens (when approved) are encrypted at rest. No secret appears in source code, logs, URLs written to logs, or Git.
6. **Least disclosure to third-party clouds.** A subscribed or synced calendar sits on Microsoft's, Google's or Apple's servers. Publish only what the person needs to see there.
7. **The publishing core holds no domain rules.** Construction rules (CalibraytAI) and legal rules (AiRIA) live in each product's adapter (§4), never in the shared core.

---

## 3. IMPLEMENTED — what exists today (CalibraytAI)

### 3.1 Components

| Layer | File | Reusable by AiRIA? | Purpose |
|---|---|---|---|
| **Publishing core** | `app/services/calendar_sync.py` | **Yes, as is.** Standard library only, enforced by a test. | Builds an iCalendar (RFC 5545) file from plain event dictionaries. Creates and hashes feed keys. Builds `https://` and `webcal://` addresses. |
| Host adapter | `app/services/appointments.py` (`appointment_event`, `appointment_file`, `turn_on_feed`, `turn_off_feed`, `active_feed`, `feed_for_key`) | No (CalibraytAI-specific). AiRIA writes its own; see §4. | Turns a CalibraytAI appointment into the event contract, chooses which appointments go in a person's feed, and applies membership and privacy checks. |
| Feed key store | `app/models/appointment.py` `CalendarFeedKey`, table `calendar_feed_keys` (migration `z3c4d5e6f7a8`) | The pattern, yes. Copy the table shape. | One live key per person and organization: `key_hash` (SHA-256, unique), `created_at`, `last_fetched_at`, `revoked_at`. |
| Public feed endpoint | `app/routes/calendar_feed.py`, `GET /calendar-feed/<key>.ics` | The pattern, yes. | Needs no sign-in, so calendar programs can fetch it. The secret key is the only credential. Allow-listed in `protect_office_routes` (`app/__init__.py`). |
| Signed-in endpoints | `app/routes/schedule.py`: `GET /schedule/appointments/<id>/calendar.ics`, and `GET/POST /schedule/calendar-feed` (turn on, new address, turn off) | The pattern, yes. | Download one appointment; manage your own feed. |
| Screens | `app/templates/schedule/calendar_feed.html`, plus the "Add to my calendar (.ics)" button on the appointment page | The pattern, yes. | Shows the address once, with Copy, an "Open in Apple Calendar or Outlook" (`webcal://`) button, and steps for Google, Outlook and Apple. |

### 3.2 Event data contract (publishing core input)

Each event is a dictionary. **Times are wall-clock times in the office time zone** (`DEFAULT_TZID = "America/Toronto"`); the file carries the matching `VTIMEZONE` with North American daylight-saving rules.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `uid` | str | yes | Stable, globally unique id (CalibraytAI uses `appointment-<id>@<org>.calibraytai`). It must never change for the same record, because calendar programs match updates by it. |
| `title` | str | yes | `SUMMARY`. |
| `date` | date | yes | Day of the event. |
| `all_day` | bool | yes | If true, it is an all-day event (`DTSTART;VALUE=DATE` / exclusive `DTEND`). |
| `start`, `end` | time or None | when not all day | Wall-clock start and end in `tzid`. |
| `location` | str | no | `LOCATION`. |
| `description` | str | no | `DESCRIPTION` (escaped, multi-line). |
| `cancelled` | bool | no | `STATUS:CANCELLED` (used in single files; feeds simply leave cancelled items out). |
| `sequence` | int | no | `SEQUENCE`; increases with each change so clients replace older copies. |
| `updated` | datetime (UTC) | no | `LAST-MODIFIED`. |
| `url` | str | no | Link back to the authoritative record. |

`build_calendar(events, name=..., tzid=..., refresh_minutes=60, now=None)` returns the full text. The output:
- uses CRLF line endings;
- folds lines at 75 octets;
- escapes `\ ; , newline`;
- sets `METHOD:PUBLISH`;
- includes `REFRESH-INTERVAL` and `X-PUBLISHED-TTL` hints;
- marks every event `TRANSP:OPAQUE`.

What the file deliberately leaves out:
- **No `ORGANIZER` or `ATTENDEE`.** Including them can make some calendar programs send invitation emails. The platform sends nothing.
- **No `VALARM`.** Reminders belong to each person's own calendar program.

### 3.3 What a person's feed contains (CalibraytAI rules, in the adapter)

**Included:**
- active appointments in the window from 60 days back to 400 days ahead, where the person is:
  - the person the appointment is for;
  - or the maker of an appointment that is for no one in particular;
  - or an attendee.
- the person's own **personal** appointments.

**Excluded:**
- other people's appointments;
- other people's personal appointments, which are never visible to anyone but their owner;
- cancelled appointments, which drop out of the feed so the calendar programs remove them;
- construction work and supplier deliveries. They are not in the feed today (§10, open item).

### 3.4 Security boundaries (implemented and tested)

| Boundary | How |
|---|---|
| Key strength | `secrets.token_urlsafe(32)` (256 bits). |
| Key storage | SHA-256 hash only. The full address is shown **once** at creation; a lost address is replaced, never recovered. |
| Revocation | "Make a new address" revokes the old key at once; "Turn off" revokes it. A revoked or unknown key returns 404. |
| People who leave | The feed returns 404 if the user is inactive or their membership in that organization is inactive. |
| Organization isolation | The key is bound to one organization and one user. Appointment queries filter by that organization. |
| Personal privacy | Personal appointments are filtered in the database query (`list_active` / `_mine_filter`), not hidden in the page. Others get 404 for the appointment's page, its file, edit and cancel. |
| Abuse limits | Keys longer than 200 characters are rejected. The endpoint only reads. `last_fetched_at` is written at most hourly. |
| Response headers | Feed: `Cache-Control: private, max-age=300`, `X-Robots-Tag: noindex, nofollow`, `Referrer-Policy: no-referrer`. Single file: `Cache-Control: no-store`. |
| Suppliers and signed-out visitors | Every appointment page and settings page requires an office sign-in. Suppliers are refused by the existing access wall. |
| No outbound messages | Neither creating a feed nor fetching it sends email or text. |

### 3.5 Tests and verification

**Automated tests:**
- `tests/test_calendar_sync.py`:
  - standards conformance (CRLF, folding, escaping, time zones, all-day, status, sequence);
  - the `webcal` form of the address;
  - file download and its privacy;
  - feed contents, update and cancel;
  - new address and turn-off;
  - a person who leaves loses their feed;
  - sign-in required for the settings page;
  - **the publishing core imports only the standard library**.
- `tests/test_calendar_ownership.py`: personal appointments stay out of other people's feeds and files, and each organization's data stays separate.

**Independent parsing check (19 Oct 2026):** a single file and a feed produced by this code were parsed by two independent iCalendar libraries (`icalendar` 6.1.0 and `vobject` 0.9.9). Both parsed and re-serialized cleanly. Times resolved correctly in both seasons:
- 9:00 on 3 Nov resolved to UTC−05:00 (EST);
- 13:00 on 15 Jul resolved to UTC−04:00 (EDT);
- the 1 Nov changeover day resolved correctly.

**Real-client check (pending, for Joel):** this needs the released, public `https://` address, because Google fetches subscriptions from its own servers and cannot reach a development machine.
1. Turn on the feed under **Outlook · Google · Apple Calendar** and copy the address.
2. **Google Calendar** (computer): Other calendars → + → From URL → paste.
3. **Outlook**: Add calendar → Subscribe from web → paste.
4. **Apple Calendar**: File → New Calendar Subscription → paste. Or use the "Open in Apple Calendar or Outlook" button.
5. Confirm the appointments appear at the right times. Change one, then confirm it updates after the provider's next refresh.
6. Download one appointment's `.ics` file and open it in each program.

### 3.6 Known limitations of subscriptions

- **The refresh timing belongs to the provider.**
  - Google Calendar refreshes subscribed calendars on its own timing, often several hours apart and sometimes up to about a day. This can't be forced.
  - Outlook refreshes on its own interval.
  - Apple Calendar lets the person choose (for example, every 5 minutes).

  For this reason a subscription is **not** a way to deliver urgent schedule changes.
- **Read-only** in the person's calendar program. Edits there are not sent back, by design.
- **One time zone per publisher** (`America/Toronto` today). Adding another zone means adding its rules to `_VTIMEZONES`.
- **A public HTTPS address is required.** The feed works only from the released site.
- **The address is a bearer secret.** Anyone who has it can read that person's feed until it is replaced. The page says this to the person.

---

## 4. How AiRIA adopts this

**Copy unchanged:**
- `calendar_sync.py`;
- the shape of the feed key table;
- the public endpoint pattern;
- the settings screen pattern.

**Write an AiRIA adapter that answers four questions:**

1. **Which records become events?** For example, a lawyer's appointments, hearings, court appearances, filing deadlines and limitation dates.
2. **Who receives which records?** For example: the responsible lawyer; the assigned clerk or paralegal; team members on the matter; never a person outside the matter's ethical wall.
3. **What may leave AiRIA for a third-party cloud?** See §5.2. Matter names, client names and privileged content may need to be withheld or reduced to a neutral title.
4. **How is a UID built?** For example `airia-<record type>-<id>@<firm>.airia`. It must be stable for the life of the record.

The adapter fills the §3.2 contract; the core does the rest. **No CalibraytAI construction logic is imported.** The core has no knowledge of projects, crews, deliveries or schedules.

---

## 5. AiRIA legal scheduling safeguards (required in AiRIA's adapter)

### 5.1 Protected legal dates are published one-way only

- **Protected dates** include:
  - court dates, hearings and trials;
  - filing and service deadlines;
  - limitation dates;
  - court-ordered dates;
  - any record the firm marks as protected.
- Protected dates are **only ever published** (subscription or file).
- If two-way sync is approved later, protected records must be **excluded from inbound processing entirely**. An inbound change to the event that mirrors a protected date must:
  - leave the AiRIA record untouched;
  - create a **review item** showing the original value, the external value, who changed it (if the provider says), and when;
  - log the event in the matter's audit trail;
  - optionally re-publish the authoritative value at the next sync. The external calendar may be corrected **from** AiRIA, never the other way round.
- **Deleting** a protected event in an outside calendar is also treated only as a review item. It never cancels or removes anything in AiRIA.
- The event description should carry a line such as "Authoritative record in AiRIA — changes made here are not applied", plus a link (`url`) back to the record.

### 5.2 Confidential and privileged information

- Choose the disclosure level for each event in the AiRIA adapter:
  - **full**: matter, parties, court, room;
  - **neutral**: for example "Court appearance — Superior Court" with the matter reference only;
  - **busy only**: for example "AiRIA: busy".

  Default protected or privileged matters to *neutral* or *busy only*.
- Apply ethical walls in the adapter's "who receives which records" rule. A screened lawyer's feed must not contain the screened matter.
- A person's feed key gives read access to whatever that feed contains. Treat it like a password and make "Make a new address" easy to find.

### 5.3 Lawyer availability

- Availability checking (§7) returns busy times only. AiRIA must not store external event titles or attendees.
- Bookings proposed from availability are **suggestions** until a person confirms them in AiRIA. They never write into a protected record.

---

## 6. PROPOSED — two-way synchronization (Outlook and Google)

Not built. **It needs separate approval** for:
- provider registrations;
- credential storage;
- permissions;
- the conflict policy.

### 6.1 Components

| Component | Responsibility |
|---|---|
| Provider connector (one per provider) | Exposes a common interface: `authorize_url`, `exchange_code`, `refresh`, `revoke`, `list_changes(since_token)`, `get_event`, `create_event`, `update_event(etag)`, `delete_event`, `subscribe_webhook`, `renew_webhook`. |
| Connection store | One row per person and provider. Holds the encrypted tokens (see §6.3), granted scopes, the external calendar id, and status (active / needs re-consent / revoked), plus consent time and the consent text version. |
| Mapping store | Maps the local record (type and id) to the external event id. Also holds the provider etag or change key, the last pushed hash, the last pulled hash, the sync time, and a "protected" flag. |
| Sync engine | Pushes outbound changes; pulls inbound changes with provider delta tokens; applies field ownership rules; detects conflicts; avoids loops (ignores echoes of its own writes by comparing hashes and etags). |
| Review queue | Holds inbound changes that need a person: every change to a protected record, and every conflict on a shared field. |
| Audit log | Records every inbound and outbound action, with who, what, before and after. |

### 6.2 Provider dependencies

These are listed from published provider documentation. **Verify each against current documentation at design-approval time.**

| Provider | API | Notes |
|---|---|---|
| Microsoft 365 / Outlook.com | Microsoft Graph Calendar API | Needs an **app registration in Microsoft Entra ID**. Delegated scopes such as `Calendars.ReadWrite` (and `offline_access` for refresh tokens). Inbound changes via delta queries, plus change-notification subscriptions, which expire and must be renewed. Some organizations require an administrator to grant consent. |
| Google Calendar | Google Calendar API v3 | Needs a **Google Cloud project with an OAuth consent screen**. Calendar scopes are restricted/sensitive and normally require **Google app verification** before general use. Inbound changes via `syncToken` incremental sync, plus push notification channels, which expire and must be renewed. |
| Apple Calendar | **EXCLUDED** for two-way | See §8. |

Both webhook mechanisms need a public HTTPS endpoint and validation of each notification's authenticity.

### 6.3 Consent and token management

- **Consent:**
  - Use the OAuth 2.0 authorization-code flow with PKCE, the state parameter, and redirect URIs that exactly match the registration.
  - Request the **minimum scopes**: read-only for availability, read/write only if two-way is approved.
  - Show the person what will be shared, in both directions, before they connect. Record the consent text version and time.
- **Storage:**
  - Encrypt access and refresh tokens at rest with a key held outside the database (a Render environment secret or a key management service).
  - Never log tokens. Never put them in URLs.
  - Rotate the encryption key on a set procedure.
- **Lifecycle:**
  - Refresh tokens before they expire.
  - On `invalid_grant`, mark the connection "needs re-consent" and tell the person.
  - "Disconnect" revokes at the provider, deletes the tokens, and stops the webhooks.
  - Leaving the organization disconnects automatically.
- **Isolation:** connections belong to one person in one organization. An administrator cannot use or read another person's connection.

### 6.4 Conflict detection and resolution

Each field belongs to one side, and anything unclear goes to a person.

| Situation | Rule |
|---|---|
| Protected record (AiRIA §5) changed or deleted outside | **Never applied.** A review item is created and the original is kept. The authoritative value may be re-published. |
| Construction work date (CalibraytAI) changed outside | **Never applied.** Construction schedules have downstream effects: crews, supplier deliveries, dependencies. Create a review item. |
| Ordinary appointment changed only outside since the last sync | Apply only if that field is marked inbound-editable for that record type. Otherwise create a review item. |
| Changed on both sides since the last sync (etag or hash mismatch on both) | **Conflict.** Keep the platform value, create a review item showing both versions, and do not overwrite either side automatically. |
| Deleted outside | For ordinary appointments, a review item ("cancel it here too?"). For protected records, a review item only. |
| Created outside | Off by default. If enabled, it is imported as a *personal* appointment of the connected person, never as a company or legal record. |
| Outbound write rejected (etag changed) | Pull again, re-evaluate, and fall back to a conflict review. |

---

## 7. PROPOSED — availability (free/busy) checking

Not built. **It needs separate approval.**

- **Microsoft Graph:** the schedule/free-busy lookup (for example `getSchedule`) returns busy blocks for the people asked about, subject to tenant sharing settings.
- **Google:** the `freeBusy` query returns busy intervals.
- **What comes back:** only start and end times plus a busy, tentative or out-of-office status. Titles, attendees and locations must not be requested, stored or shown.
- **Caching:** cache briefly (minutes), keep it per organization, never across organizations, and drop it on disconnect.
- **Use:** to suggest times for an appointment, or for a lawyer's availability in AiRIA. A suggestion becomes a booking only when a person confirms it.
- **Consent:** each person connects their own calendar. Organization-wide access, such as a Microsoft 365 administrator granting free/busy access for all staff, is a separate decision with its own approval.

---

## 8. Apple Calendar

- **Supported:** the subscription feed (`webcal://` / `https://`) and single-appointment `.ics` files. Both are **IMPLEMENTED**.
- **EXCLUDED, by owner decision on 19 Oct 2026:**
  - app-specific passwords;
  - CalDAV credential handling;
  - any two-way Apple integration.

  Apple offers no OAuth-based calendar API for third-party servers, and the practical two-way route (CalDAV with an app-specific password) would mean handling a user's password-equivalent. That is not permitted.
- Apple Calendar can subscribe to the same feed and refresh it often, chosen by the person. Apple Calendar can also show Microsoft 365 and Google accounts that a person adds on their own device, independently of the platform.

---

## 9. Required approvals before any proposed work

1. Provider registrations: a Microsoft Entra app and a Google Cloud project with an OAuth consent screen. Google app verification, if calendar scopes are used.
2. The token encryption key and where it is held; the credential storage tables (a migration).
3. The scopes requested from people, and any organization-wide (administrator) consent.
4. The conflict policy table (§6.4) for each record type, including which fields, if any, may be edited from outside.
5. For AiRIA: the disclosure levels (§5.2), the protected-date list, and the ethical-wall rule for feeds.

---

## 10. Open items

- **Construction work in feeds (CalibraytAI).** People's feeds carry appointments only. Adding a person's assigned construction work as all-day events is possible with the same core. Remember that subscriptions refresh slowly (§3.6), so crews must still rely on Field for changes.
- **Real-client verification** (§3.5) after release.
- **Time zones beyond Eastern** if either product serves other regions.
- **Production email delivery** is a separate setting from calendars. The schedule synchronization review noted that emails are only delivered if the email provider is configured in production.

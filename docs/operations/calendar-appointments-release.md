# Calendar Appointments release — database change, rehearsal, release and recovery

| Attribute | Value |
|-----------|--------|
| Date | 19 October 2026 |
| Release | Calendar (My Calendar \| Company Calendar, appointments, calendar feed), the G2/G3 supplier delivery corrections, Field offline label (G5) |
| Branch | `calendar/appointments-2026-10-19`, from live `d450188` |
| Database change | migration `z3c4d5e6f7a8` (follows `y2b3c4d5e6f7`) |
| Status | Prepared. **Not released, not migrated.** Needs Joel's authorization of the release **and** of the production migration. |

## 1. The four new tables

Nothing existing is altered: no column, index, constraint or row in any existing table changes. Every foreign key is `ON DELETE RESTRICT`.

| Table | Purpose | Key rules |
|---|---|---|
| `company_appointments` | One business appointment on one day. It is either all day, or has a start and end time. | **Type** must be site visit, client meeting, supplier meeting, estimate consultation or general. **Visibility** is `COMPANY` (every employee of the organization) or `PERSONAL` (owner only). **Times:** all day means no times; otherwise both times are present and end is after start. **Status** is `ACTIVE` or `CANCELLED`; cancelled appointments are kept. Belongs to one organization. The owner, client and project are optional. |
| `company_appointment_attendees` | Other company people attending a company appointment. | One row per appointment and person (unique). Belongs to one organization. |
| `company_appointment_history` | Who added, changed, rescheduled or cancelled an appointment, and when. | Event is one of `CREATED`, `CHANGED`, `RESCHEDULED`, `CANCELLED`. Records the earlier and new date and times, and which fields changed. Append-only. |
| `calendar_feed_keys` | A person's private calendar-feed key, for Outlook, Google or Apple Calendar. | Holds a SHA-256 **hash** only, unique; the key itself is never stored. Records when it was created, last fetched and revoked. |

**Privacy constraints in the code** (the tests check every one):
- A personal appointment is filtered out of every other person's views in the database query.
- A personal appointment's maker and owner are the same person, and it has no attendees.
- Each organization sees only its own rows.

## 2. Rehearsal (before any authorization)

Run automatically by the release gate with `--migration-to z3c4d5e6f7a8 --new-tables ...`, on the office Mac:

1. The gate takes a **fresh production backup** (SQLite online backup on the instance), copies it to the Mac, and checks that the checksums match and integrity is ok.
2. The gate copies that backup and runs the candidate's migration on the **copy**:
   `tools/release/migration_check.py rehearse`
3. It proves all of the following:
   - every existing table keeps its exact schema, and every row is identical (count and SHA-256 of all rows in order);
   - exactly the four new tables were added, and they are empty;
   - the revision is now `z3c4d5e6f7a8`;
   - integrity is ok.
4. The rehearsal copy is **deleted**, because it holds production data. The evidence stays in `<label>-release-*-rehearsal.txt`.

The same check runs in the test suite on synthetic databases (`tests/test_migration_check.py`, `tests/test_company_appointments_migration.py`).

## 3. Release order (only after Joel authorizes the release and the migration)

1. Claude pushes the tested commit itself to `main` (fast-forward), then deploys it on Render (auto-deploy off).
2. Joel runs `release_migrate.sh --label <label>` on the Mac. It:
   - waits until the instance runs the release;
   - on the instance, **takes its own pre-migration backup** (`instance/backups/pre-migrate-<label>-<UTC>.db`) and verifies it;
   - runs the migration, then proves again that existing tables and records are unchanged, the new tables are empty, and integrity is ok;
   - copies the pre-migration backup to the Mac and verifies its checksum.
3. Joel runs `postrelease_check.sh --label <label>`, which is read-only. It confirms:
   - the running SHA, and revision `z3c4d5e6f7a8`;
   - rows equal to the pre-release backup, plus the four empty tables;
   - integrity, and the public checks.

**Between steps 1 and 2** (a minute or two), the calendar page needs the new tables, so opening it shows the error page until the migration finishes. Other pages work. Release at a quiet time and run step 2 straight away.

## 4. Rollback and recovery (two separate procedures)

**Code rollback** (any problem with the application):
- Redeploy `d450188` (`dep-dbb0lejrjlhs73avpu10`) on Render with the same settings.
- The previous code ignores the four new tables, so it runs unchanged with them present. No database step is needed, and nothing is lost: any appointments already made stay stored for when the release returns.

**Database recovery** (only if the database itself were damaged; **only with Joel's explicit approval**):
1. Stop traffic. A code rollback first is the safe order.
2. Restore the pre-migration backup taken by `release_migrate.sh` (on the instance, plus the Mac copy), using the same SQLite online-backup method used for releases.
3. Anything written after the migration, including appointments, would be lost.

The migration's own downgrade **refuses** while any appointment rows exist. Recovery is always the backup, never a destructive downgrade.

## 5. Gate command shape

```
bash /tmp/release_gate.sh --label <label> --candidate <sha> --branch calendar/appointments-2026-10-19 \
  --main-base d450188ba6a3b923c3cba191395255c8206a0a23 --live-base d450188ba6a3b923c3cba191395255c8206a0a23 \
  --live-deploy dep-dbb0lejrjlhs73avpu10 --browser-expected 55 \
  --migration-to z3c4d5e6f7a8 \
  --new-tables company_appointments,company_appointment_attendees,company_appointment_history,calendar_feed_keys
```

What the gate requires:
- the full native Mac regression, including the historical-estimate tests: no skips allowed;
- the end-to-end walk and the Cal tests;
- 55 browser checks in Google Chrome: the existing 43 plus 12 calendar checks;
- the fresh backup, with a matching Mac checksum and integrity;
- the migration rehearsal;
- then it stops at `READY_FOR_PUSH`.

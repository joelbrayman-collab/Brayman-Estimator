# Backup and restore

Brayman Construction. 7 October 2026. Authority corrected 9 October 2026.

Joel does this. Ben does not.

The working office is the hosted platform. Its database is the operational file. The Mac file is a mirror. See [operating-authority-2026-10-09.md](operating-authority-2026-10-09.md).

The steps below copy the Mac file `instance/brayman_estimator.db`. They remain the steps for that mirror. Completing them does not back up the hosted office. On 9 October 2026 at 13:01 local, that Mac file was checked as a current mirror of hosted backup `hosted-current-2026-10-09-1258.db`, revision `t0a1b2c3d4e5`.

There is no automatic backup. A copy is not finished until the check says ok and a second copy exists outside that live file. The current hosted backup is `hosted-current-2026-10-09-1258.db`, integrity `ok`, revision `t0a1b2c3d4e5`, with a verified Desktop second copy. The earlier hosted backup `pre-t0-2026-10-09-1202.db` remains revision `s9f0a1b2c3d4` and was not overwritten. Joel makes another checked backup at the end of a day a real project changed.

Do this before the first real project is typed in, at the end of any day a real project changed, and before any change to the office file's structure. Ben never makes that structure change.

## Backup

1. Tell Ben to stop entering work.
2. Stop the office. In the terminal where it is running, press Control-C.
3. Do not run a database upgrade.
4. From the Brayman-Estimator folder, run:

```
mkdir -p instance/backups
sqlite3 instance/brayman_estimator.db ".backup 'instance/backups/brayman-office-YYYY-MM-DD-HHMM.db'"
sqlite3 instance/backups/brayman-office-YYYY-MM-DD-HHMM.db "PRAGMA integrity_check; SELECT version_num FROM alembic_version;"
```

5. The check must print `ok`, then one revision line. The backup made on 7 October 2026 before the office structure update is revision `h8c9d0e1f2a3`. After that update the live office revision is `q7d8e9f0a1b2`. A backup keeps the revision of the file that was copied.
6. Copy that same backup file to a second place that is not the live office file and not only `instance/backups`. Write that place in the backup log the first time you use it.
7. Add one line to `docs/operations/v1-backup-log.md`: date, file name, `ok`, the revision line, the second-copy place, and your name.

`instance/` is not in git. The backup log is. Do not commit the database file.

## Restore

These steps restore the Mac mirror. They do not replace the hosted office.

1. Stop the Mac copy. Do not start it if `instance/brayman_estimator.db` is missing. Starting it can create an empty file.
2. Rename the current file. Do not delete it. Example: `instance/brayman_estimator.unusable-YYYY-MM-DD-HHMM.db`. Move `brayman_estimator.db-wal` and `brayman_estimator.db-shm` aside too, if they are there.
3. Copy the chosen backup onto `instance/brayman_estimator.db`.
4. Run the same integrity check. It must print `ok` and a revision line.
5. To check the mirror, start it from the Brayman-Estimator folder with `flask run --port 5001` and open `http://127.0.0.1:5001`. That address is the mirror, not the working office.
6. Sign in and open the project. If it is missing, stop. Do not type it in again on a blank office.
7. Write the restore in the backup log.

## If the office is unusable

Stop. Do not create a new database. Do not run an upgrade to fix it. Do not keep typing. Restore from the last line in the backup log whose check said ok.

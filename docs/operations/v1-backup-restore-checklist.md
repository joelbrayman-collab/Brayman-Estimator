# Backup and restore

Brayman Construction. Mac office. 7 October 2026.

Joel does this. Ben does not.

The office is one file: `instance/brayman_estimator.db` in the Brayman-Estimator folder. There is no automatic backup. A copy is not finished until the check says ok and a second copy exists outside that live file.

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

1. Stop the office. Do not start it if `instance/brayman_estimator.db` is missing. Starting it can create an empty office.
2. Rename the current file. Do not delete it. Example: `instance/brayman_estimator.unusable-YYYY-MM-DD-HHMM.db`. Move `brayman_estimator.db-wal` and `brayman_estimator.db-shm` aside too, if they are there.
3. Copy the chosen backup onto `instance/brayman_estimator.db`.
4. Run the same integrity check. It must print `ok` and a revision line.
5. Start the office the same way: from the Brayman-Estimator folder, `flask run --port 5001`. Open `http://127.0.0.1:5001`.
6. Sign in and open the project. If it is missing, stop. Do not type it in again on a blank office.
7. Write the restore in the backup log.

## If the office is unusable

Stop. Do not create a new database. Do not run an upgrade to fix it. Do not keep typing. Restore from the last line in the backup log whose check said ok.

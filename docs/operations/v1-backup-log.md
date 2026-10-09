# Office backup log

Joel appends one line each time he makes or restores a backup. He does not rewrite an older line.

The first verified backup of the Mac office file `instance/brayman_estimator.db` was made on 7 October 2026 before the office structure was updated. That backup is revision `h8c9d0e1f2a3`, 3,485,696 bytes. The original file was not overwritten and was not deleted. After the existing revisions were applied, the Mac file was intact, revision `q7d8e9f0a1b2`, 3,645,440 bytes, last changed 2026-10-07 11:06:09. That was the Mac file on that date. The current mirror is recorded in the 9 October section below.

| Date | Action | File | Check | Revision | Second copy | Who |
|------|--------|------|-------|----------|-------------|-----|
| 2026-10-07 | Backup before schema update | instance/backups/brayman-office-2026-10-07-1105.db | ok | h8c9d0e1f2a3 | /Users/joelbrayman/Desktop/Brayman-office-backups/brayman-office-2026-10-07-1105.db | Cursor on Joel's Mac |
| 2026-10-09 | Backup of the hosted office | /opt/render/project/src/instance/backups/hosted-current-2026-10-09-1258.db | ok | t0a1b2c3d4e5 | /Users/joelbrayman/Desktop/Brayman-office-backups/hosted-current-2026-10-09-1258.db | Cursor on Joel's Mac |

## 2026-10-09 hosted backup

The 7 October line above is unchanged.

Hosted source: `https://calibryatai.onrender.com`, application `dccd5cac6f7c8c281a312e252fe3aacb15ad3e6b`, deploy `dep-db4h3dks728c73aohka0`, instance `srv-dar95mh42hec73df4rug-w78cf`, file `/opt/render/project/src/instance/brayman_estimator.db`. That live file was last changed 2026-10-09 16:38 UTC. Integrity `ok`. Revision `t0a1b2c3d4e5`. Size 3,678,208 bytes. No journal files were present.

BACKUP CREATED. `sqlite3 .backup` wrote `/opt/render/project/src/instance/backups/hosted-current-2026-10-09-1258.db` at 2026-10-09 16:58 UTC. The earlier file `pre-t0-2026-10-09-1202.db` was not overwritten. Its size stayed 3,657,728 bytes and its time stayed 2026-10-09 16:02 UTC.

BACKUP VERIFIED. The new file exists, size 3,678,208 bytes, integrity `ok`, revision `t0a1b2c3d4e5`. SHA-256 `1b4c064d363534305152ecc473e746fbf3e2e8a1139eb408b058a8ab02ad7276`. Construction revisions 1 and 2 are present for project 46. Estimate 41, version 47, line 137 quantity 3, pricing snapshot 15 total 49.86, costing snapshot 23 direct cost 37.50, and proposal 18 Draft total 49.86 are present. The same records were read from the live file after the backup. A SQLite backup is not a raw byte copy, so the backup checksum is not the checksum of the live file.

SECOND COPY VERIFIED. `/Users/joelbrayman/Desktop/Brayman-office-backups/hosted-current-2026-10-09-1258.db` has the same size, the same SHA-256, integrity `ok`, and revision `t0a1b2c3d4e5`.

MAC MIRROR CURRENT. `instance/brayman_estimator.db` was replaced at 2026-10-09 13:01:46 local only after the previous Mac file was preserved. The mirror has the same SHA-256, integrity `ok`, and revision `t0a1b2c3d4e5`. The previous Mac file is `instance/brayman_estimator.q7-before-mirror-2026-10-09-1258.db`, integrity `ok`, revision `q7d8e9f0a1b2`. A separate SQLite backup of that previous file is `instance/backups/brayman-office-q7-preserved-2026-10-09-1258.db`, with a Desktop copy of that preservation. The 7 October backup was not overwritten.

Restore steps remain [v1-backup-restore-checklist.md](v1-backup-restore-checklist.md). Restoring the Mac mirror does not replace the hosted office.

# Operating authority — 9 October 2026

Joel decided this on 9 October 2026. It supersedes the earlier instruction that the Mac office was the primary place for a real job and that a real job must not be entered on the hosted platform.

## Working platform

The live hosted platform is the working office.

- Address: `https://calibryatai.onrender.com`
- Live application: `dccd5cac6f7c8c281a312e252fe3aacb15ad3e6b`
- Deploy: `dep-db4h3dks728c73aohka0`
- Hosted database revision last read: `t0a1b2c3d4e5`, integrity `ok`

Ben uses this platform. Real projects, construction models, estimates, costing, and customer Proposals are entered here. They are entered only after the readiness gates already required for a real job. This decision does not open real contractor UAT. Ben’s sign-in on this platform is not verified by this note.

GitHub is the product source and the release history. It is not the office database.

## Mac mirror

The Mac is a mirrored backup and a recovery resource. It is not the primary contractor office. It is not a prerequisite for live use. It is not the authority for current hosted project data.

The Mac file was last read on 7 October 2026 at revision `q7d8e9f0a1b2`. It was not synchronized to the hosted revision `t0a1b2c3d4e5`. Until a later check shows the same revision and an integrity result of `ok`, the Mac file is not a current mirror.

## Four copies

| Copy | What it is | Status on 9 October 2026 |
|------|------------|--------------------------|
| Live hosted database | The operational office file on the hosted platform | Authoritative. Revision `t0a1b2c3d4e5`. Integrity `ok` when last read. |
| Verified hosted backup | A checked copy of the hosted file from before the construction-revision change | `pre-t0-2026-10-09-1202.db`. Integrity `ok`. Revision `s9f0a1b2c3d4`. Not a copy of the database after the synthetic project work. |
| Mac file | The mirror on this Mac | Last read revision `q7d8e9f0a1b2` on 7 October 2026. Not verified against the hosted file. |
| Mac backup in the log | The checked copy made before the 7 October structure update | Revision `h8c9d0e1f2a3`. Recorded in the backup log. Not a current hosted backup. |

## Backup requirement that already exists

Joel still makes a checked backup before a real project is typed in, and again at the end of a day a real project changed. The check is the one already written: integrity `ok`, one revision line, a second copy outside the live file, and one new line in the backup log. Ben does not make that copy and Ben does not restore it.

That requirement now applies to the hosted operational file. The written Mac steps remain the steps for copying the Mac mirror. They do not, by themselves, back up the hosted office. No new backup system is created by this note. No database was copied for this decision.

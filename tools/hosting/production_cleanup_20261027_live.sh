#!/bin/bash
# CalibraytAI Production cleanup, 27 Oct 2026 — the live run Joel authorized (02:49). Office Mac, Terminal.
#   bash production_cleanup_20261027_live.sh <commit> <approved plan hash>
# In order, stopping at the first problem (nothing after a STOP is done):
#   1-2 fresh online Production backup on the instance, integrity checked
#   3-4 copy to ~/CalibraytAI-Office/office-backups, SHA-256 compared with the instance's
#     live dry run: must be exactly the approved plan and READY=yes
#   5-6 the cleanup (one all-or-nothing transaction; files to instance/cleanup-quarantine-20261027/)
#   7-8 row-by-row verification against the backup: integrity, foreign keys, kept rows unchanged
#     a read-only snapshot of the cleaned database to release-work for the application checks
# Everything is logged to ~/CalibraytAI-Office/release-work/cleanup-live-<time>.log. Prints no secrets.
set -uo pipefail
S=${1:?commit}
EXPECT=${2:?approved plan hash}
H=srv-dar95mh42hec73df4rug@ssh.virginia.render.com
SSH=(ssh -o UpdateHostKeys=no -o ServerAliveInterval=15)
RPY='cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=$(command -v python3); fi; $PY -'
LIVE=/opt/render/project/src/instance/brayman_estimator.db
REPO=~/Desktop/Brayman-Estimator
OUT=~/CalibraytAI-Office/release-work
BK=~/CalibraytAI-Office/office-backups
TS=$(date +%Y%m%d-%H%M%S)
LOG=$OUT/cleanup-live-$TS.log
mkdir -p "$OUT" "$BK"
exec > >(tee -a "$LOG") 2>&1
stop() { echo "STOP: $*"; echo "== Nothing after this point was done. Log: $LOG"; exit 1; }
show() { git -C "$REPO" show "$S:$1"; }
echo "== CalibraytAI Production cleanup (live) $(date) commit=$S plan=$EXPECT"
git -C "$REPO" fetch -q origin ops/prod-inventory-2026-10-27 || stop "could not fetch the cleanup branch"
show tools/hosting/production_cleanup_20261027.py >/dev/null || stop "commit $S not found"

echo "== 1-2. Fresh Production backup (online SQLite backup), integrity check"
PRE=$(show tools/release/hosted_preflight.py | "${SSH[@]}" "$H" "export BACKUP_PREFIX=pre-cleanup; $RPY" 2>&1)
echo "$PRE" | grep -v '^TABLE_COUNTS='
BP=$(echo "$PRE" | grep '^BACKUP_PATH=' | cut -d= -f2)
BS=$(echo "$PRE" | grep '^BACKUP_SHA256=' | cut -d= -f2)
grep -q '^BACKUP_INTEGRITY=ok' <<<"$PRE" && [ -n "$BP" ] && [ -n "$BS" ] || stop "the backup did not complete"

echo "== 3-4. Copy the backup to this Mac and compare fingerprints"
MAC="$BK/$(basename "$BP")"
for i in 1 2 3; do scp -q -o UpdateHostKeys=no "$H:$BP" "$MAC" && break; echo "  copy attempt $i did not complete; retrying in 10 s"; sleep 10; done
MS=$(shasum -a 256 "$MAC" 2>/dev/null | cut -d' ' -f1)
echo "INSTANCE_SHA256=$BS"
echo "MAC_SHA256=$MS  ($MAC)"
[ "$MS" = "$BS" ] || stop "the Mac copy's fingerprint does not match the instance backup"

echo "== Live dry run (must be exactly the approved plan)"
PLAN=$(show tools/hosting/production_cleanup_20261027.py | "${SSH[@]}" "$H" "$RPY plan" 2>&1)
echo "$PLAN"
grep -q "^PLAN_HASH=$EXPECT " <<<"$PLAN" && grep -q '^READY=yes' <<<"$PLAN" || stop "live plan is not the approved $EXPECT (Production changed?)"

echo "== 5-6. Cleanup and file quarantine (one transaction)"
APPLY=$(show tools/hosting/production_cleanup_20261027.py | "${SSH[@]}" "$H" \
  "$RPY apply --db $LIVE --instance /opt/render/project/src/instance --expect-plan $EXPECT --live --backup $BP" 2>&1)
echo "$APPLY"
grep -q "^APPLIED plan $EXPECT" <<<"$APPLY" || stop "the cleanup did not apply (the database is unchanged unless APPLIED is shown above)"

echo "== 7-8. Verify the cleaned database against the backup"
VER=$(show tools/hosting/production_cleanup_20261027.py | "${SSH[@]}" "$H" "$RPY verify --before $BP --after $LIVE" 2>&1)
echo "$VER"
grep -q '^VERIFY=ok' <<<"$VER" || stop "verification failed: do not use Production; send this log to Claude (rollback needs Joel)"

echo "== Read-only snapshot of the cleaned database for the application checks"
"${SSH[@]}" "$H" 'cd /opt/render/project/src && T=$(mktemp /tmp/after-XXXXXX.db) && python3 -c "import sqlite3,sys; s=sqlite3.connect(\"file:instance/brayman_estimator.db?mode=ro\",uri=True); d=sqlite3.connect(sys.argv[1]); s.backup(d); d.close()" "$T" && cat "$T"; rm -f "$T"' > "$OUT/prod-after-cleanup-$TS.db"
"${SSH[@]}" "$H" 'cd /opt/render/project/src/instance && find . -type f ! -path "./backups/*" -printf "%P\t%s\n"' > "$OUT/prod-files-after-cleanup-$TS.tsv"
echo "AFTER_SNAPSHOT=$OUT/prod-after-cleanup-$TS.db"
echo "ROLLBACK_BACKUP_INSTANCE=$BP"
echo "ROLLBACK_BACKUP_MAC=$MAC"
echo "CLEANUP_LIVE=done $(date)"

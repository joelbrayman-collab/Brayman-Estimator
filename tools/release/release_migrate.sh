#!/bin/bash
# CalibraytAI: apply an AUTHORIZED release migration on the live instance. Runs on the office Mac, only
# after Joel authorized the release and its migration, and Claude pushed the tested commit to main and
# deployed it. Then run postrelease_check.sh.
#   bash /tmp/release_migrate.sh --label <same label as the release gate>
# (fetch it from the released commit: git -C ~/Desktop/Brayman-Estimator show <sha>:tools/release/release_migrate.sh > /tmp/release_migrate.sh)
#   1 the release gate reached READY_FOR_PUSH for this commit WITH a rehearsed migration; GitHub main is that commit
#   2 the live instance runs it (waits up to 40 minutes)
#   3 on the instance: its own pre-migration backup (online), then the upgrade, then proof that every existing
#     table's schema and rows are unchanged, exactly the new tables were added (empty), integrity ok
#   4 the pre-migration backup is copied to this Mac and its checksum verified
# Safe to run more than once: an already-migrated database is reported and left alone.
set -u
LABEL=""
while [ $# -gt 0 ]; do case "$1" in --label) LABEL=$2; shift 2;; *) sed -n '2,13p' "$0"; exit 2;; esac; done
[[ "$LABEL" =~ ^[a-z0-9-]+$ ]] || { sed -n '2,13p' "$0"; exit 2; }
REPO_URL=https://github.com/joelbrayman-collab/Brayman-Estimator.git
OFFICE_LOCAL="${CALIBRAYTAI_OFFICE_LOCAL:-$HOME/CalibraytAI-Office}"
GEN="$OFFICE_LOCAL/release-work"; BACKUPS="$OFFICE_LOCAL/office-backups"
HOST=srv-dar95mh42hec73df4rug@ssh.virginia.render.com
SSH_OPTS=(-o UpdateHostKeys=no)
STATUS="$GEN/$LABEL-release-status.txt"; STATE="$GEN/$LABEL-release-state.txt"
TS=$(date +%Y%m%d-%H%M%S); OUT="$GEN/$LABEL-migrate-$TS"; LOG="$OUT.log"
exec > >(tee "$LOG") 2>&1
status() { echo "$1" >> "$STATUS"; echo "  [status] $1"; }
stop() { status "STOPPED (migration): $1"; echo "STOP: $1"; exit 1; }
val() { grep "^$1=" "$2" | head -1 | cut -d= -f2-; }
REMOTE_PY='cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=$(command -v python3); fi; $PY -'
[ -f "$STATE" ] || stop "no release state for $LABEL ($STATE); run the release gate first"
SHA=$(val SHA "$STATE"); REVISION=$(val REVISION "$STATE"); DEST=$(val CLONE "$STATE")
MIGRATION_TO=$(val MIGRATION_TO "$STATE"); NEW_TABLES=$(val NEW_TABLES "$STATE"); ALTERED_TABLES=$(val ALTERED_TABLES "$STATE")
ALTERED_CHECKS=$(val ALTERED_CHECKS "$STATE")  # 29 Oct 2026: the rehearsed check constraints, applied the same way
[ -n "$MIGRATION_TO" ] || stop "this release has no migration; run postrelease_check.sh only"
grep -q "^READY_FOR_PUSH commit=$SHA" "$STATUS" 2>/dev/null || stop "the release gate did not reach READY_FOR_PUSH for $SHA"
grep -q "^MIGRATION_REHEARSAL $REVISION -> $MIGRATION_TO" "$STATUS" || stop "no successful rehearsal of $REVISION -> $MIGRATION_TO in this release"
SCRIPT="$DEST/tools/release/migration_check.py"
[ "$(git -C "$DEST" rev-parse HEAD)" = "$SHA" ] && [ -f "$SCRIPT" ] || stop "the release clone $DEST is not at $SHA"
[ -z "$(git -C "$DEST" status --porcelain -- tools/release)" ] || stop "release helpers in $DEST differ from $SHA"

echo "== 1. GitHub main"
MAIN=$(git ls-remote "$REPO_URL" refs/heads/main | cut -f1)
[ "$MAIN" = "$SHA" ] || stop "GitHub main is $MAIN, not the tested $SHA"

echo "== 2. Live instance runs the release"
RUN=""
for i in $(seq 1 80); do
  RUN=$(ssh "${SSH_OPTS[@]}" -n "$HOST" 'echo SHA=$RENDER_GIT_COMMIT' 2>/dev/null | tr -d '\r' | grep '^SHA=' | cut -d= -f2)
  [ "$RUN" = "$SHA" ] && break
  sleep 30
done
[ "$RUN" = "$SHA" ] || stop "live instance did not report $SHA within 40 minutes (still $RUN)"

echo "== 3. Migration on the live instance ($REVISION -> $MIGRATION_TO), after its own backup"
# The deployed release already holds migration_check.py; run that file (after proving it is byte-identical
# to the tested release clone's copy) rather than piping it, so it finds the instance folder itself.
CHECK_SHA=$(shasum -a 256 "$SCRIPT" | awk '{print $1}')
REMOTE_RUN="cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=\$(command -v python3); fi; \
[ \"\$(sha256sum tools/release/migration_check.py | cut -d' ' -f1)\" = $CHECK_SHA ] || { echo FAIL=the instance migration_check.py differs from the tested release; exit 1; }; \
\$PY tools/release/migration_check.py"
ssh "${SSH_OPTS[@]}" -n "$HOST" "$REMOTE_RUN apply --from $REVISION --to $MIGRATION_TO --new-tables $NEW_TABLES${ALTERED_TABLES:+ --altered-tables $ALTERED_TABLES}${ALTERED_CHECKS:+ --altered-checks $ALTERED_CHECKS} --expect-sha $SHA --label $LABEL" \
  > "$OUT-migrate.txt" 2>&1
cat "$OUT-migrate.txt" | grep -E '^[A-Z_]+='
grep -q '^MIGRATE=ok' "$OUT-migrate.txt" || stop "migration did not complete (see $OUT-migrate.txt); the app keeps running; database recovery only with Joel"
if grep -q '^ALREADY_MIGRATED=yes' "$OUT-migrate.txt"; then
  status "MIGRATED already at $MIGRATION_TO (nothing done)"
  exit 0
fi
PBACK=$(val PRE_MIGRATION_BACKUP "$OUT-migrate.txt"); PSHA=$(val PRE_MIGRATION_BACKUP_SHA256 "$OUT-migrate.txt")

echo "== 4. Pre-migration backup to this Mac"
LOCALP="$BACKUPS/$(basename "$PBACK")"
for i in 1 2 3 4 5; do
  scp "${SSH_OPTS[@]}" -q "$HOST:$PBACK" "$BACKUPS/" && [ "$(shasum -a 256 "$LOCALP" | awk '{print $1}')" = "$PSHA" ] && break
  echo "  backup copy attempt $i did not complete; retrying in $((i * 10)) s"; rm -f "$LOCALP"; sleep $((i * 10))
done
[ -f "$LOCALP" ] && [ "$(shasum -a 256 "$LOCALP" | awk '{print $1}')" = "$PSHA" ] || stop "could not copy the pre-migration backup to the Mac (it is still on the instance: $PBACK)"
echo "PRE_MIGRATION_BACKUP_MAC=$LOCALP" >> "$STATE"
status "MIGRATED $REVISION -> $MIGRATION_TO on the live instance: $(val EXISTING_TABLES_UNCHANGED "$OUT-migrate.txt"); new: $(val NEW_TABLES "$OUT-migrate.txt"); integrity $(val INTEGRITY_AFTER "$OUT-migrate.txt"); pre-migration backup $PBACK sha256=$PSHA, Mac copy $LOCALP matches"
echo "== DONE. Now run postrelease_check.sh --label $LABEL"

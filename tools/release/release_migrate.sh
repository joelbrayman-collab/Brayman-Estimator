#!/bin/bash
# CalibraytAI: apply an AUTHORIZED release migration on the live instance. Runs on the office Mac, only
# after Joel authorized the release and its migration, and Claude pushed the tested commit to main and
# deployed it. Then run postrelease_check.sh. release.sh runs it itself (with --run) after Joel types the
# confirmation phrase in its window (3 Nov 2026).
#   bash /tmp/release_migrate.sh --label <same label as the release gate> [--run <run ID>]
# (fetch it from the released commit: git -C ~/Desktop/Brayman-Estimator show <sha>:tools/release/release_migrate.sh > /tmp/release_migrate.sh)
#   0 which gate run: --run <run ID>, or the run of this label whose READY_FOR_PUSH is the commit on GitHub main
#   1 the release gate reached READY_FOR_PUSH for this commit WITH a rehearsed migration; GitHub main is that commit
#   2 the live instance runs it (waits up to 40 minutes)
#   3 on the instance: its own pre-migration backup (online), then the upgrade, then proof that every existing
#     table's schema and rows are unchanged, exactly the new tables were added (empty), integrity ok
#   4 the pre-migration backup is copied to this Mac and its checksum verified
# Safe to run more than once: an already-migrated database is reported and left alone (no second backup).
set -u
LABEL=""; RUN_ARG=""
while [ $# -gt 0 ]; do case "$1" in --label) LABEL=$2; shift 2;; --run) RUN_ARG=$2; shift 2;; *) sed -n '2,14p' "$0"; exit 2;; esac; done
[[ "$LABEL" =~ ^[a-z0-9-]+$ ]] || { sed -n '2,14p' "$0"; exit 2; }
[ -z "$RUN_ARG" ] || [[ "$RUN_ARG" =~ ^[a-z0-9-]+$ ]] || { sed -n '2,14p' "$0"; exit 2; }
REPO_URL=https://github.com/joelbrayman-collab/Brayman-Estimator.git
OFFICE_LOCAL="${CALIBRAYTAI_OFFICE_LOCAL:-$HOME/CalibraytAI-Office}"
GEN="$OFFICE_LOCAL/release-work"; BACKUPS="$OFFICE_LOCAL/office-backups"
HOST=srv-dar95mh42hec73df4rug@ssh.virginia.render.com
SSH_OPTS=(-o UpdateHostKeys=no)
# >>> release-runs (3 Nov 2026). Byte-identical in release.sh, release_gate.sh, release_migrate.sh and
# postrelease_check.sh (tests/test_release_runs.py checks this), so each script still works when fetched on its own.
# Every gate run has its own run ID (<label>-<YYYYMMDD-HHMMSS>) and folder $GEN/runs/<run ID>/; nothing in one run's
# folder is ever truncated or rewritten by another run. A run's gate/ folder is sealed when the gate ends (a SHA-256
# MANIFEST of every file, then every file and the folder read-only); gate/READY_FOR_PUSH marks a run that passed.
# Plain bash 3.2 (the Mac's /bin/bash): no associative arrays, no mapfile.
rr_sha256() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$@"; else sha256sum "$@"; fi; }
rr_val() { grep "^$1=" "$2" 2>/dev/null | head -1 | cut -d= -f2-; }
# rr_require <file> <key> <what the file is>: prints the value, or explains exactly what is missing and returns 1.
rr_require() {
  local f=$1 k=$2 what=${3:-file} v
  if [ ! -e "$f" ]; then
    echo "$what $f does not exist, so $k cannot be read"; return 1
  fi
  if [ ! -s "$f" ]; then
    echo "$what $f is EMPTY (0 bytes), so $k cannot be read; it was truncated or never written (the gate run that made it did not reach READY_FOR_PUSH). Nothing was guessed. Run release.sh --label <label> --list to see every run and which one reached READY_FOR_PUSH"; return 1
  fi
  v=$(rr_val "$k" "$f")
  if [ -z "$v" ]; then
    echo "$what $f has no value for $k (line '$k=' missing or blank; $(grep -c . "$f") line(s) in the file)"; return 1
  fi
  printf '%s\n' "$v"
}
# rr_new_run <label> [<run ID>]: creates $GEN/runs/<run ID>/ atomically (mkdir, never -p on the run folder) and prints
# the run ID. Without a run ID, <label>-<timestamp> (with -2, -3, ... if that second is already taken). An existing
# run folder is never reused.
rr_new_run() {
  local label=$1 id=${2:-} base n=1
  mkdir -p "$GEN/runs" || return 1
  if [ -n "$id" ]; then
    case "$id" in "$label"-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]*) ;; *)
      echo "run ID $id is not $label-<YYYYMMDD-HHMMSS>" >&2; return 1;; esac
    mkdir "$GEN/runs/$id" 2>/dev/null || { echo "run $id already exists in $GEN/runs; its evidence is never reused or overwritten" >&2; return 1; }
  else
    base="$label-$(date +%Y%m%d-%H%M%S)"; id=$base
    until mkdir "$GEN/runs/$id" 2>/dev/null; do
      n=$((n + 1)); id="$base-$n"; [ "$n" -lt 100 ] || { echo "could not create a run folder in $GEN/runs" >&2; return 1; }
    done
  fi
  printf 'RUN_ID=%s\nLABEL=%s\nCREATED=%s\n' "$id" "$label" "$(date '+%Y-%m-%d %H:%M:%S %z')" > "$GEN/runs/$id/run.txt" \
    && chmod a-w "$GEN/runs/$id/run.txt" && echo "$id"
}
# rr_seal <folder>: SHA-256 MANIFEST of every file below it, then every file and folder in it read-only. Once only.
rr_seal() {
  local d=$1
  [ -d "$d" ] || { echo "cannot seal $d: no such folder"; return 1; }
  [ -e "$d/MANIFEST.sha256" ] && { echo "$d is already sealed"; return 1; }
  ( cd "$d" && find . -type f ! -path ./MANIFEST.sha256 | LC_ALL=C sort | while IFS= read -r f; do rr_sha256 "$f"; done \
      > MANIFEST.sha256 ) || return 1
  chmod -R a-w "$d"
}
# rr_verify <folder>: the folder is sealed, every file matches its MANIFEST line and no file was added or removed.
rr_verify() {
  local d=$1 listed present
  [ -s "$d/MANIFEST.sha256" ] || { echo "$d has no MANIFEST.sha256 (not sealed)"; return 1; }
  ( cd "$d" && rr_sha256 -c MANIFEST.sha256 >/dev/null 2>&1 ) || { echo "a file in $d differs from its MANIFEST.sha256 entry"; return 1; }
  listed=$(sed -E 's/^[0-9a-f]{64}  //' "$d/MANIFEST.sha256" | LC_ALL=C sort)
  present=$(cd "$d" && find . -type f ! -path ./MANIFEST.sha256 | LC_ALL=C sort)
  [ "$listed" = "$present" ] || { echo "files were added to or removed from sealed $d"; return 1; }
}
# rr_runs <label>: "<run ID> <outcome> <commit>" for every run of this label, oldest first. Outcome is RELEASED,
# READY_FOR_PUSH (passed, not yet released), STOPPED, INTERRUPTED or RUNNING (no end marker: running, or killed).
rr_runs() {
  local d id outcome
  for d in "$GEN/runs/$1"-[0-9]*; do
    [ -d "$d" ] && [ "$(rr_val LABEL "$d/run.txt")" = "$1" ] || continue
    id=${d##*/}
    if [ -f "$d/RELEASED" ]; then outcome=RELEASED
    elif [ -f "$d/gate/READY_FOR_PUSH" ]; then outcome=READY_FOR_PUSH
    elif [ -f "$d/gate/STOPPED" ]; then outcome=STOPPED
    elif [ -f "$d/gate/INTERRUPTED" ]; then outcome=INTERRUPTED
    else outcome=RUNNING; fi
    echo "$id $outcome $(rr_val SHA "$d/gate/READY_FOR_PUSH" || true)"
  done
}
# rr_bind <label> <commit>: the run whose READY_FOR_PUSH is exactly <commit> (the commit on GitHub main and live).
# Several such runs: the one that already holds migration or post-release records, else the newest. A run whose gate
# evidence fails its MANIFEST is never bound. Prints the run ID, or explains and returns 1.
rr_bind() {
  local label=$1 sha=$2 id outcome commit picked="" used="" all
  [ -n "$sha" ] || { echo "no commit to bind to (the commit read from GitHub main is blank)"; return 1; }
  all=$(rr_runs "$label")
  while read -r id outcome commit; do
    [ -n "$id" ] && [ "$commit" = "$sha" ] || continue
    case "$outcome" in RELEASED|READY_FOR_PUSH) ;; *) continue;; esac
    rr_verify "$GEN/runs/$id/gate" >/dev/null || continue
    picked=$id
    if [ -d "$GEN/runs/$id/migrate" ] || [ -d "$GEN/runs/$id/post" ]; then used=$id; fi
  done <<EOF
$all
EOF
  [ -n "$used" ] && picked=$used
  if [ -z "$picked" ]; then
    echo "no gate run of $label reached READY_FOR_PUSH for $sha (with its sealed evidence intact). Runs of $label: $(echo "$all" | grep . | tr '\n' ';' || true)"
    [ -n "$all" ] || echo "(none in $GEN/runs)"
    return 1
  fi
  echo "$picked"
}
# rr_resolve <label> <run ID or empty>: which run release_migrate.sh / postrelease_check.sh act on. With a run ID, that
# run (it must be of this label, have reached READY_FOR_PUSH and have intact sealed evidence). Without one, the run
# bound to the commit on GitHub main (rr_bind). A label with no run folders at all is a release gated before 3 Nov 2026:
# its $GEN/<label>-release-status.txt and -state.txt are used, as before. Sets RUN_ID, RUN_DIR, STATUS, GSTATE (the
# gate's sealed state) and STATE (where the migration adds its records); prints STOP: ... and returns 1 otherwise.
rr_resolve() {
  local label=$1 run=$2 main="" tries outcome
  RUN_ID=""
  if [ -n "$run" ]; then
    outcome=$(rr_runs "$label" | awk -v r="$run" '$1 == r {print $2}')
    [ -n "$outcome" ] || { echo "STOP: run $run is not a run of $label in $GEN/runs"; return 1; }
    case "$outcome" in RELEASED|READY_FOR_PUSH) ;; *) echo "STOP: run $run did not reach READY_FOR_PUSH (its outcome: $outcome)"; return 1;; esac
    rr_verify "$GEN/runs/$run/gate" >/dev/null || { echo "STOP: $(rr_verify "$GEN/runs/$run/gate")"; return 1; }
    RUN_ID=$run
  elif [ -n "$(rr_runs "$label")" ]; then
    for tries in 1 2 3; do
      main=$(git ls-remote "$REPO_URL" refs/heads/main | cut -f1)
      [ -n "$main" ] && break
      [ "$tries" -lt 3 ] && sleep 5
    done
    [ -n "$main" ] || { echo "STOP: GitHub main could not be read (git ls-remote returned nothing, 3 tries), so no run can be bound; check the network and run the same command again"; return 1; }
    RUN_ID=$(rr_bind "$label" "$main") || { echo "STOP: $RUN_ID"; return 1; }
  fi
  if [ -n "$RUN_ID" ]; then
    RUN_DIR="$GEN/runs/$RUN_ID"; STATUS="$RUN_DIR/status.txt"; GSTATE="$RUN_DIR/gate/state.txt"; STATE="$RUN_DIR/after-state.txt"
    echo "== Run $RUN_ID (READY_FOR_PUSH $(rr_val SHA "$RUN_DIR/gate/READY_FOR_PUSH")); evidence $RUN_DIR"
  else
    RUN_DIR=""; STATUS="$GEN/$label-release-status.txt"; GSTATE="$GEN/$label-release-state.txt"; STATE=$GSTATE
    echo "== No run folders for $label in $GEN/runs: using the pre-3 Nov 2026 files $GSTATE and $STATUS"
  fi
}
# <<< release-runs
rr_resolve "$LABEL" "$RUN_ARG" || exit 1
TS=$(date +%Y%m%d-%H%M%S)
if [ -n "$RUN_ID" ]; then
  # This run's migration reports (the seed-on-rerun block below reads earlier ones from the same folder).
  REPORTS="$RUN_DIR/migrate"; mkdir -p "$REPORTS" || { echo "STOP: could not create $REPORTS"; exit 1; }
else
  REPORTS="$GEN"
fi
OUT="$REPORTS/$LABEL-migrate-$TS"; LOG="$OUT.log"
exec > >(tee "$LOG") 2>&1
status() { echo "$1" >> "$STATUS"; echo "  [status] $1"; }
stop() { status "STOPPED (migration): $1"; echo "STOP: $1"; exit 1; }
val() { grep "^$1=" "$2" | head -1 | cut -d= -f2-; }
REMOTE_PY='cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=$(command -v python3); fi; $PY -'
[ -f "$GSTATE" ] || stop "no release state for $LABEL ($GSTATE); run the release gate first"
# Blank values stop with the file and the reason (3 Nov 2026).
SHA=$(rr_require "$GSTATE" SHA "release state") || stop "$SHA"
REVISION=$(rr_require "$GSTATE" REVISION "release state") || stop "$REVISION"
DEST=$(rr_require "$GSTATE" CLONE "release state") || stop "$DEST"
MIGRATION_TO=$(val MIGRATION_TO "$GSTATE"); NEW_TABLES=$(val NEW_TABLES "$GSTATE"); ALTERED_TABLES=$(val ALTERED_TABLES "$GSTATE")
ALTERED_CHECKS=$(val ALTERED_CHECKS "$GSTATE")  # 29 Oct 2026: the rehearsed check constraints, applied the same way
FILLED_COLUMNS=$(val FILLED_COLUMNS "$GSTATE")  # 30 Oct 2026: the rehearsed declared data, applied the same way
POPULATED_TABLES=$(val POPULATED_TABLES "$GSTATE")
[ -z "$RUN_ID" ] || [ "$(rr_val SHA "$RUN_DIR/gate/READY_FOR_PUSH")" = "$SHA" ] || stop "run $RUN_ID: READY_FOR_PUSH and the release state name different commits"
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
ssh "${SSH_OPTS[@]}" -n "$HOST" "$REMOTE_RUN apply --from $REVISION --to $MIGRATION_TO --new-tables $NEW_TABLES${ALTERED_TABLES:+ --altered-tables $ALTERED_TABLES}${ALTERED_CHECKS:+ --altered-checks $ALTERED_CHECKS}${FILLED_COLUMNS:+ --filled-columns $FILLED_COLUMNS}${POPULATED_TABLES:+ --populated-tables $POPULATED_TABLES} --expect-sha $SHA --label $LABEL" \
  > "$OUT-migrate.txt" 2>&1
cat "$OUT-migrate.txt" | grep -E '^[A-Z_]+='
grep -q '^MIGRATE=ok' "$OUT-migrate.txt" || stop "migration did not complete (see $OUT-migrate.txt); the app keeps running; database recovery only with Joel"
if grep -q '^ALREADY_MIGRATED=yes' "$OUT-migrate.txt"; then
  # >>> seed-on-rerun (review fix M4, 1 Nov 2026): postrelease_check.sh needs MIGRATION_SEEDED. A rerun keeps the
  # value already recorded; otherwise it takes it from the first apply's saved report, or records it empty when no
  # table was declared populated; with no record of the seed it stops rather than guess.
  if ! grep -q '^MIGRATION_SEEDED=' "$STATE"; then
    if [ -z "$POPULATED_TABLES" ]; then
      echo "MIGRATION_SEEDED=" >> "$STATE"
    else
      EARLIER=""
      for f in "$REPORTS/$LABEL"-migrate-*-migrate.txt; do
        [ -f "$f" ] && [ "$f" != "$OUT-migrate.txt" ] || continue
        grep -q '^MIGRATE=ok' "$f" && grep -q '^POPULATED_TABLE=' "$f" && ! grep -q '^ALREADY_MIGRATED=' "$f" && EARLIER=$f
      done
      [ -n "$EARLIER" ] || stop "the database is already at $MIGRATION_TO but this Mac has no report of the first apply, so the rows it seeded into $POPULATED_TABLES are not recorded; do not run postrelease_check.sh; send Claude the status file ($STATUS) — the seed counts are then read from the pre-migration backup on the instance (instance/backups/pre-migrate-$LABEL-*.db) with Joel"
      RESEED=$(grep '^POPULATED_TABLE=' "$EARLIER" | sed -E 's/^POPULATED_TABLE=([a-z_][a-z0-9_]*): ([0-9]+) row\(s\).*/\1=\2/' | paste -sd, -)
      echo "MIGRATION_SEEDED=$RESEED" >> "$STATE"
      status "MIGRATION_SEEDED=$RESEED recorded from the first apply's report $EARLIER"
    fi
  fi
  # <<< seed-on-rerun
  status "MIGRATED already at $MIGRATION_TO (nothing done)"
  exit 0
fi
PBACK=$(val PRE_MIGRATION_BACKUP "$OUT-migrate.txt"); PSHA=$(val PRE_MIGRATION_BACKUP_SHA256 "$OUT-migrate.txt")
# 31 Oct 2026 (e2p1 follow-up): record what the migration seeded into each declared --populated-tables, so the
# post-release check can prove the live rows are the backup plus exactly that seed.
SEEDED=$(grep '^POPULATED_TABLE=' "$OUT-migrate.txt" | sed -E 's/^POPULATED_TABLE=([a-z_][a-z0-9_]*): ([0-9]+) row\(s\).*/\1=\2/' | paste -sd, -)
if [ -n "$POPULATED_TABLES" ]; then
  [ -n "$SEEDED" ] || stop "the migration did not report the rows it seeded into $POPULATED_TABLES"
  echo "MIGRATION_SEEDED=$SEEDED" >> "$STATE"
fi

echo "== 4. Pre-migration backup to this Mac"
LOCALP="$BACKUPS/$(basename "$PBACK")"
for i in 1 2 3 4 5; do
  scp "${SSH_OPTS[@]}" -q "$HOST:$PBACK" "$BACKUPS/" && [ "$(shasum -a 256 "$LOCALP" | awk '{print $1}')" = "$PSHA" ] && break
  echo "  backup copy attempt $i did not complete; retrying in $((i * 10)) s"; rm -f "$LOCALP"; sleep $((i * 10))
done
[ -f "$LOCALP" ] && [ "$(shasum -a 256 "$LOCALP" | awk '{print $1}')" = "$PSHA" ] || stop "could not copy the pre-migration backup to the Mac (it is still on the instance: $PBACK)"
echo "PRE_MIGRATION_BACKUP_MAC=$LOCALP" >> "$STATE"
status "MIGRATED $REVISION -> $MIGRATION_TO on the live instance: $(val EXISTING_TABLES_UNCHANGED "$OUT-migrate.txt"); new: $(val NEW_TABLES "$OUT-migrate.txt"); integrity $(val INTEGRITY_AFTER "$OUT-migrate.txt"); pre-migration backup $PBACK sha256=$PSHA, Mac copy $LOCALP matches"
echo "== DONE. Now run postrelease_check.sh --label $LABEL${RUN_ID:+ --run $RUN_ID}"

#!/bin/bash
# CalibraytAI post-release checks. Run on the office Mac only AFTER Joel has authorized production and
# Claude has pushed the tested commit to main and deployed it. Read-only: changes nothing.
#   bash /tmp/postrelease_check.sh --label <same label as the release gate> [--run <run ID>]
# (fetch it from the released commit: git -C ~/Desktop/Brayman-Estimator show <sha>:tools/release/postrelease_check.sh > /tmp/postrelease_check.sh)
# release.sh runs it itself, with --run, once the commit is on main and live (3 Nov 2026).
#   0 which gate run: --run <run ID>, or the run of this label whose READY_FOR_PUSH is the commit on GitHub main
#     (never a later or failed run of the same label); its sealed evidence must match its MANIFEST
#   1 the release gate reached READY_FOR_PUSH for this commit; GitHub main is that commit; git fsck
#   2 the live instance reports it (waits up to 40 minutes)
#   3 database re-read: revision unchanged (or, for a release with a migration, at the new revision after
#     release_migrate.sh), integrity ok, rows equal to the pre-release backup (plus the new, empty tables)
#   4 signed-out public checks: sign-in required, supplier sign-in, material demand, manifest, icons and
#     logo, Cal (signed-out /cal/find goes to sign-in, no Cal on sign-in, approved icon bytes, script, styles)
# Safe to run more than once. RELEASED seals the whole run folder (MANIFEST, read-only); a later run then only reports it.
set -u
LABEL=""; RUN_ARG=""
while [ $# -gt 0 ]; do case "$1" in --label) LABEL=$2; shift 2;; --run) RUN_ARG=$2; shift 2;; *) sed -n '2,16p' "$0"; exit 2;; esac; done
[[ "$LABEL" =~ ^[a-z0-9-]+$ ]] || { sed -n '2,16p' "$0"; exit 2; }
[ -z "$RUN_ARG" ] || [[ "$RUN_ARG" =~ ^[a-z0-9-]+$ ]] || { sed -n '2,16p' "$0"; exit 2; }
CAL64_SHA=0b10a30a284877f117fd933f8126cf68155d89591f90117b6db4b2043f92ef3d
SITE=https://calibryatai.onrender.com
REPO_URL=https://github.com/joelbrayman-collab/Brayman-Estimator.git
OFFICE_LOCAL="${CALIBRAYTAI_OFFICE_LOCAL:-$HOME/CalibraytAI-Office}"
GEN="$OFFICE_LOCAL/release-work"
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
  if [ -f "$RUN_DIR/RELEASED" ]; then
    CHECK=$(rr_verify "$RUN_DIR") || { echo "STOP: run $RUN_ID is RELEASED but its sealed folder no longer matches: $CHECK"; exit 1; }
    echo "== Run $RUN_ID was already RELEASED ($(cat "$RUN_DIR/RELEASED")); its folder is sealed and intact. Nothing to do."
    exit 0
  fi
  mkdir -p "$RUN_DIR/post" || { echo "STOP: could not create $RUN_DIR/post"; exit 1; }
  OUT="$RUN_DIR/post/$LABEL-post-$TS"
else
  OUT="$GEN/$LABEL-post-$TS"
fi
LOG="$OUT.log"
status() { echo "$1" >> "$STATUS"; echo "  [status] $1"; }
stop() { status "STOPPED (post-release): $1"; echo "STOP: $1"; exit 1; }
val() { grep "^$1=" "$2" | head -1 | cut -d= -f2-; }
REMOTE_PY='cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=$(command -v python3); fi; $PY -'

# The checks run as one function piped into the log, so the log is complete before a RELEASED run is sealed.
post_main() {
[ -f "$GSTATE" ] || stop "no release state for $LABEL ($GSTATE); run the release gate first"
# Blank values stop with the file and the reason (3 Nov 2026: an emptied state file once gave a blank SHA here).
SHA=$(rr_require "$GSTATE" SHA "release state") || stop "$SHA"
LIVE_BASE=$(rr_require "$GSTATE" LIVE_BASE "release state") || stop "$LIVE_BASE"
LIVE_DEPLOY=$(rr_require "$GSTATE" LIVE_DEPLOY "release state") || stop "$LIVE_DEPLOY"
REVISION=$(rr_require "$GSTATE" REVISION "release state") || stop "$REVISION"
LOCALB=$(rr_require "$GSTATE" BACKUP "release state") || stop "$LOCALB"
BROWS=$(rr_require "$GSTATE" BACKUP_ROWS "release state") || stop "$BROWS"
DEST=$(rr_require "$GSTATE" CLONE "release state") || stop "$DEST"
MIGRATION_TO=$(val MIGRATION_TO "$GSTATE"); NEW_TABLES=$(val NEW_TABLES "$GSTATE")
POPULATED_TABLES=$(val POPULATED_TABLES "$GSTATE"); SEEDED=$(val MIGRATION_SEEDED "$STATE")
BACKUP_ROWS=$BROWS
if [ -n "$RUN_ID" ]; then
  [ "$(rr_val SHA "$RUN_DIR/gate/READY_FOR_PUSH")" = "$SHA" ] || stop "run $RUN_ID: READY_FOR_PUSH and the release state name different commits"
fi
EXPECT_REVISION=${MIGRATION_TO:-$REVISION}
if [ -n "$MIGRATION_TO" ]; then
  grep -q "^MIGRATED .*-> $MIGRATION_TO\|^MIGRATED already at $MIGRATION_TO" "$STATUS" || stop "run release_migrate.sh --label $LABEL${RUN_ID:+ --run $RUN_ID} first (migration $REVISION -> $MIGRATION_TO)"
  NEWN=$(echo "$NEW_TABLES" | tr ',' '\n' | grep -c .)
  [ "$NEW_TABLES" = "none" ] && NEWN=0  # a column-only migration (27 Oct 2026): no table added
  BROWS=$(echo "$BROWS" | awk -v n="$NEWN" '{split($1,a,"="); split($2,b,"="); printf "TABLES=%d ROWS=%d", a[2]+n, b[2]}')
fi
grep -q "^READY_FOR_PUSH commit=$SHA" "$STATUS" 2>/dev/null || stop "the release gate did not reach READY_FOR_PUSH for $SHA (status file $STATUS)"
POST="$DEST/tools/release/hosted_postcheck.py"
[ "$(git -C "$DEST" rev-parse HEAD)" = "$SHA" ] && [ -f "$POST" ] || stop "the release clone $DEST is not at $SHA"
[ -z "$(git -C "$DEST" status --porcelain -- tools/release)" ] || stop "release helpers in $DEST differ from $SHA"

echo "== 1. GitHub main"
MAIN=$(git ls-remote "$REPO_URL" refs/heads/main | cut -f1)
[ "$MAIN" = "$SHA" ] || stop "GitHub main is $MAIN, not the tested $SHA"
git -C "$DEST" fetch -q origin main && [ "$(git -C "$DEST" rev-parse origin/main)" = "$SHA" ] \
  && git -C "$DEST" fsck --full >/dev/null 2>&1 || stop "git fsck or main fetch failed in the release clone"
status "PUSHED main=$MAIN (the tested commit itself); git fsck ok"

echo "== 2. Live instance"
RUN=""
for i in $(seq 1 80); do
  RUN=$(ssh "${SSH_OPTS[@]}" -n "$HOST" 'echo SHA=$RENDER_GIT_COMMIT' 2>/dev/null | tr -d '\r' | grep '^SHA=' | cut -d= -f2)
  [ "$RUN" = "$SHA" ] && break
  sleep 30
done
[ "$RUN" = "$SHA" ] || stop "live instance did not report $SHA within 40 minutes (still $RUN)"

echo "== 3. Database re-read (read-only)"
for i in 1 2 3; do ssh "${SSH_OPTS[@]}" "$HOST" "$REMOTE_PY" < "$POST" > "$OUT-postcheck.txt" 2>&1 && grep -q '^POSTCHECK=ok' "$OUT-postcheck.txt" && break; sleep 20; done
cat "$OUT-postcheck.txt"
grep -q '^POSTCHECK=ok' "$OUT-postcheck.txt" || stop "post-deploy database check failed"
[ "$(val RUNNING_SHA "$OUT-postcheck.txt")" = "$SHA" ] || stop "post-check did not run on $SHA"
[ "$(val REVISION "$OUT-postcheck.txt")" = "$EXPECT_REVISION" ] || stop "database revision is $(val REVISION "$OUT-postcheck.txt"), expected $EXPECT_REVISION"
[ "$(val INTEGRITY "$OUT-postcheck.txt")" = "ok" ] || stop "database integrity is not ok"
# Live row totals with the same helper the release gate used for the backup (review fix C1, 1 Nov 2026): every table
# except sqlite_* and the search index (document_search and its FTS5 shadow tables, derived data the app rewrites,
# reported on its own line). hosted_postcheck.py's TABLES= line counts every table and is not the comparison.
ssh "${SSH_OPTS[@]}" "$HOST" "$REMOTE_PY count-rows --live" < "$DEST/tools/release/migration_check.py" > "$OUT-rows-live.txt" 2>&1
cat "$OUT-rows-live.txt"
LROWS=$(grep '^TABLES=' "$OUT-rows-live.txt")
LSEARCH=$(val SEARCH_INDEX "$OUT-rows-live.txt")
[ -n "$LROWS" ] && [ -n "$LSEARCH" ] || stop "could not count the live database's rows (see $OUT-rows-live.txt)"
if [ -n "$MIGRATION_TO" ] && [ -n "$POPULATED_TABLES" ]; then
  # 31 Oct 2026 (e2p1 follow-up): the approved migration seeded the declared new tables; read their counts on the
  # live database (read-only) and prove live = backup + new tables + exactly that seed.
  [ -n "$SEEDED" ] || stop "release_migrate.sh did not record the rows the migration seeded into $POPULATED_TABLES"
  COUNTS=$(ssh "${SSH_OPTS[@]}" "$HOST" "$REMOTE_PY $POPULATED_TABLES" <<'PYEOF' | tr -d '\r' | grep '^COUNTS=' | cut -d= -f2-
import os, sqlite3, sys
uri = os.environ.get("CALIBRAYTAI_DATABASE_URI", "")
c = sqlite3.connect("file:" + uri[len("sqlite:///"):] + "?mode=ro", uri=True)
print("COUNTS=" + ",".join("%s=%d" % (t, c.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]) for t in sys.argv[1].split(",")))
PYEOF
)
  [ -n "$COUNTS" ] || stop "could not read the seeded tables' row counts on the live database"
  python3 "$DEST/tools/release/migration_check.py" postcheck-rows --backup "$BACKUP_ROWS" --live "$LROWS" \
    --new-tables "$NEW_TABLES" --populated-tables "$POPULATED_TABLES" --seeded "$SEEDED" --live-counts "$COUNTS" \
    > "$OUT-rows.txt" 2>&1
  cat "$OUT-rows.txt"
  grep -q '^ROWS_CHECK=ok' "$OUT-rows.txt" || stop "records differ from the pre-release backup plus the declared migration seed (see $OUT-rows.txt) — check whether anyone used the app during the release"
  BROWS=$(val EXPECTED_LIVE "$OUT-rows.txt")
fi
[ "$LROWS" = "$BROWS" ] || stop "records differ from the pre-release backup (backup: $BROWS; live: $LROWS) — check whether anyone used the app during the release"
if [ -n "$MIGRATION_TO" ] && [ -n "$POPULATED_TABLES" ]; then
  status "LIVE_RUNNING_SHA=$RUN; revision $MIGRATION_TO (migrated from $REVISION); $LROWS = the pre-release backup's rows plus the new tables plus the migration's declared seed ($SEEDED); search index $LSEARCH (not in the totals); $(grep '^PROPOSALS=' "$OUT-postcheck.txt"); integrity ok"
elif [ -n "$MIGRATION_TO" ]; then
  status "LIVE_RUNNING_SHA=$RUN; revision $MIGRATION_TO (migrated from $REVISION); $LROWS = the pre-release backup's rows plus the new, empty tables; search index $LSEARCH (not in the totals); $(grep '^PROPOSALS=' "$OUT-postcheck.txt"); integrity ok"
else
  status "LIVE_RUNNING_SHA=$RUN; revision $REVISION unchanged; $LROWS equal to the pre-release backup; search index $LSEARCH (not in the totals); $(grep '^PROPOSALS=' "$OUT-postcheck.txt"); integrity ok"
fi

echo "== 4. Public and Cal checks (signed out)"
CODE=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$SITE/projects/")
case "$CODE" in 302*login*) ;; *) stop "a signed-out visitor was not sent to sign-in ($CODE)";; esac
curl -fsS "$SITE/static/manifest.webmanifest" > "$OUT-manifest.json" || stop "app manifest is not served"
grep -q '"name": *"CalibraytAI"' "$OUT-manifest.json" || stop "app manifest does not name CalibraytAI"
grep -q '"start_url": *"/"' "$OUT-manifest.json" || stop "installed app does not start on Home"
for icon in calibraytai-app-icon-192.png calibraytai-app-icon-512.png calibraytai-app-icon-maskable-512.png calibraytai-app-icon-180.png calibraytai-logo-v1-dark.png; do
  [ "$(curl -s -o /dev/null -w '%{http_code}' "$SITE/static/branding/$icon")" = "200" ] || stop "$icon is not served"
done
curl -fsS "$SITE/supplier/login" | grep -q 'data-password-reveal' || stop "supplier sign-in page is not served"
CODE=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$SITE/supplier/1/demand")
case "$CODE" in 302*supplier/login*) ;; *) stop "material demand did not require supplier sign-in ($CODE)";; esac
CODE=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$SITE/cal/find?q=harbour")
case "$CODE" in 302*login*) ;; *) stop "signed-out /cal/find was not sent to sign-in ($CODE)";; esac
curl -fsS "$SITE/login" | grep -q 'id="cal-launch"' && stop "Cal appears on the signed-out sign-in page"
[ "$(curl -fsS "$SITE/static/img/cal-assistant/cal-64.png" | shasum -a 256 | awk '{print $1}')" = "$CAL64_SHA" ] || stop "served Cal icon differs from the recorded derivative"
curl -fsS "$SITE/static/js/cal_assistant.js" | grep -q 'cal-launch' || stop "Cal script is not served"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$SITE/static/css/cal-assistant.css")" = "200" ] || stop "Cal styles are not served"
status "PUBLIC_CHECKS signed-out redirect to sign-in; supplier sign-in served; material demand requires supplier sign-in; manifest CalibraytAI on Home; icons and logo served; CAL signed-out /cal/find goes to sign-in, no Cal on sign-in page, approved icon bytes match, script and styles served"
if [ -n "$MIGRATION_TO" ]; then
  status "ROLLBACK_TARGET=code: redeploy $LIVE_BASE ($LIVE_DEPLOY, same settings), which runs unchanged with the added tables; database: only with Joel's approval, restore $(val PRE_MIGRATION_BACKUP_MAC "$STATE")"
else
  status "ROLLBACK_TARGET=redeploy $LIVE_BASE ($LIVE_DEPLOY, same settings); no database change to undo; restore only with Joel's approval from $LOCALB"
fi
status "RELEASED $(date)${RUN_ID:+ run=$RUN_ID}"
[ -z "$RUN_ID" ] || echo "$SHA $(date '+%Y-%m-%d %H:%M:%S %z')" > "$RUN_DIR/RELEASED"
echo "== DONE. $SHA is live. Claude now checks the release signed in."
}

post_main 2>&1 | tee "$LOG"
POST_EXIT=${PIPESTATUS[0]}
if [ "$POST_EXIT" -eq 0 ] && [ -n "$RUN_ID" ] && [ -f "$RUN_DIR/RELEASED" ]; then
  # The released run is final: its whole folder (gate, migration, post-release, status) is sealed.
  rr_seal "$RUN_DIR" >/dev/null && echo "== Run $RUN_ID sealed (MANIFEST.sha256, read-only)" || { echo "STOP: could not seal $RUN_DIR"; exit 1; }
fi
exit "$POST_EXIT"

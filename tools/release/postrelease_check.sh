#!/bin/bash
# CalibraytAI post-release checks. Run on the office Mac only AFTER Joel has authorized production and
# Claude has pushed the tested commit to main and deployed it. Read-only: changes nothing.
#   bash /tmp/postrelease_check.sh --label <same label as the release gate>
# (fetch it from the released commit: git -C ~/Desktop/Brayman-Estimator show <sha>:tools/release/postrelease_check.sh > /tmp/postrelease_check.sh)
#   1 the release gate reached READY_FOR_PUSH for this commit; GitHub main is that commit; git fsck
#   2 the live instance reports it (waits up to 40 minutes)
#   3 database re-read: revision unchanged, integrity ok, tables and rows equal to the pre-release backup
#   4 signed-out public checks: sign-in required, supplier sign-in, material demand, manifest, icons and
#     logo, Cal (signed-out /cal/find goes to sign-in, no Cal on sign-in, approved icon bytes, script, styles)
# Safe to run more than once.
set -u
LABEL=""
while [ $# -gt 0 ]; do case "$1" in --label) LABEL=$2; shift 2;; *) sed -n '2,12p' "$0"; exit 2;; esac; done
[[ "$LABEL" =~ ^[a-z0-9-]+$ ]] || { sed -n '2,12p' "$0"; exit 2; }
CAL64_SHA=0b10a30a284877f117fd933f8126cf68155d89591f90117b6db4b2043f92ef3d
SITE=https://calibryatai.onrender.com
REPO_URL=https://github.com/joelbrayman-collab/Brayman-Estimator.git
GEN=/Users/joelbrayman/Desktop/Brayman-Estimator/generated
HOST=srv-dar95mh42hec73df4rug@ssh.virginia.render.com
SSH_OPTS=(-o UpdateHostKeys=no)
STATUS="$GEN/$LABEL-release-status.txt"; STATE="$GEN/$LABEL-release-state.txt"
TS=$(date +%Y%m%d-%H%M%S); OUT="$GEN/$LABEL-post-$TS"; LOG="$OUT.log"
exec > >(tee "$LOG") 2>&1
status() { echo "$1" >> "$STATUS"; echo "  [status] $1"; }
stop() { status "STOPPED (post-release): $1"; echo "STOP: $1"; exit 1; }
val() { grep "^$1=" "$2" | head -1 | cut -d= -f2-; }
REMOTE_PY='cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=$(command -v python3); fi; $PY -'
[ -f "$STATE" ] || stop "no release state for $LABEL ($STATE); run the release gate first"
SHA=$(val SHA "$STATE"); LIVE_BASE=$(val LIVE_BASE "$STATE"); LIVE_DEPLOY=$(val LIVE_DEPLOY "$STATE")
REVISION=$(val REVISION "$STATE"); LOCALB=$(val BACKUP "$STATE"); BROWS=$(val BACKUP_ROWS "$STATE"); DEST=$(val CLONE "$STATE")
grep -q "^READY_FOR_PUSH commit=$SHA" "$STATUS" 2>/dev/null || stop "the release gate did not reach READY_FOR_PUSH for $SHA"
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
[ "$(val REVISION "$OUT-postcheck.txt")" = "$REVISION" ] || stop "database revision changed"
[ "$(val INTEGRITY "$OUT-postcheck.txt")" = "ok" ] || stop "database integrity is not ok"
LROWS=$(grep '^TABLES=' "$OUT-postcheck.txt")
[ "$LROWS" = "$BROWS" ] || stop "records differ from the pre-release backup (backup: $BROWS; live: $LROWS) — check whether anyone used the app during the release"
status "LIVE_RUNNING_SHA=$RUN; revision $REVISION unchanged; $LROWS equal to the pre-release backup; $(grep '^PROPOSALS=' "$OUT-postcheck.txt"); integrity ok"

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
status "ROLLBACK_TARGET=redeploy $LIVE_BASE ($LIVE_DEPLOY, same settings); no database change to undo; restore only with Joel's approval from $LOCALB"
status "RELEASED $(date)"
echo "== DONE. $SHA is live. Claude now checks the release signed in."

#!/bin/bash
# CalibraytAI Training Centre on the HostPapa VPS (22 Oct 2026; pinned commits 23 Oct 2026). Run as root in WHM Terminal.
# Usage: bash install_training_centre.sh [commit]
#   commit: the CalibraytAI commit to run (default below: the v1rel8 release candidate). A full SHA or a short one
#   reachable from v1/rel8-2026-10-23, main or v1/training-centre-2026-10-21.
# Prerequisites already done: system user calibrayt, /opt/calibrayt/app (git, venv), /opt/calibrayt/env (600),
# the training database /opt/calibrayt/data/training.db named in /opt/calibrayt/env.
# Keeps /opt/calibrayt/env and /opt/calibrayt/data as they are: the only new file there is a timestamped backup copy
# of training.db, taken with the service stopped and before any migration. "flask training build-environment" adds
# only what is missing; it never resets a password, a trainee's progress or an acceptance result.
# Idempotent: safe to run again. Prints no passwords or secrets.
set -u
COMMIT=${1:-f3a01e1ba1929c2c698c7cb0fc821001be657f90}
APP=/opt/calibrayt/app
DATA=/opt/calibrayt/data
DB=$DATA/training.db
SITE=https://training.calibraytai.com
as_app() { sudo -u calibrayt "$@"; }
in_env() { sudo -u calibrayt bash -c "cd $APP && set -a && . /opt/calibrayt/env && set +a && $1"; }

echo "== 0. checks"
[ -f /opt/calibrayt/env ] || { echo "STOP: /opt/calibrayt/env is missing"; exit 1; }
grep -q "training.db" /opt/calibrayt/env || { echo "STOP: /opt/calibrayt/env does not name $DB"; exit 1; }
[ -f "$DB" ] || { echo "STOP: $DB is missing (this script never creates or replaces the training database)"; exit 1; }
echo "running now: $(as_app git -C $APP log --oneline -1 2>/dev/null)"

echo "== 1. code at $COMMIT"
as_app git -C $APP fetch -q --depth 200 origin v1/rel8-2026-10-23 main v1/training-centre-2026-10-21 2>/dev/null
as_app git -C $APP cat-file -e "$COMMIT^{commit}" 2>/dev/null || as_app git -C $APP fetch -q origin "$COMMIT" 2>/dev/null
as_app git -C $APP cat-file -e "$COMMIT^{commit}" 2>/dev/null || { echo "STOP: commit $COMMIT not found"; exit 1; }
as_app git -C $APP -c advice.detachedHead=false checkout -q --force "$COMMIT" || { echo "STOP: checkout failed"; exit 1; }
as_app git -C $APP log --oneline -1
as_app $APP/venv/bin/pip install -q -r $APP/requirements.txt gunicorn || { echo "STOP: pip install failed"; exit 1; }

echo "== 2. stop, back up the training database, migrate, add what is missing"
systemctl stop calibrayt-training 2>/dev/null
mkdir -p $DATA/backups && chown calibrayt:calibrayt $DATA/backups && chmod 700 $DATA/backups
BACKUP=$DATA/backups/training-$(date +%Y%m%d-%H%M%S).db
as_app $APP/venv/bin/python -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$BACKUP" \
  || { echo "STOP: backup failed; nothing was migrated"; systemctl start calibrayt-training; exit 1; }
chmod 600 "$BACKUP"
echo "backup: $BACKUP ($(stat -c %s "$BACKUP") bytes; database $(stat -c %s "$DB") bytes)"
in_env "./venv/bin/flask db upgrade" || { echo "STOP: migration failed. Restore with: cp $BACKUP $DB"; exit 1; }
echo "database revision: $(in_env "./venv/bin/flask db current 2>/dev/null" | tail -1)"
out=$(in_env "./venv/bin/flask training build-environment --passwords-from-env" 2>&1); rc=$?
printf '%s\n' "$out" | grep -vEi "password|secret|token" | cut -c1-160
[ "$rc" = "0" ] || { echo "STOP: build-environment failed (backup: $BACKUP)"; exit 1; }

echo "== 3. start script and service"
cat > /opt/calibrayt/run.sh <<'RUN'
#!/bin/bash
# Starts the Training Centre only. Migrations run in install_training_centre.sh, after a backup.
cd /opt/calibrayt/app || exit 1
set -a; . /opt/calibrayt/env; set +a
mkdir -p instance
exec ./venv/bin/gunicorn -w 3 --bind 127.0.0.1:8010 --forwarded-allow-ips=127.0.0.1 --access-logfile - 'app:create_app()'
RUN
chown root:calibrayt /opt/calibrayt/run.sh; chmod 750 /opt/calibrayt/run.sh
cat > /etc/systemd/system/calibrayt-training.service <<'UNIT'
[Unit]
Description=CalibraytAI Training Centre (training.calibraytai.com)
After=network-online.target
Wants=network-online.target

[Service]
User=calibrayt
Group=calibrayt
ExecStart=/opt/calibrayt/run.sh
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable calibrayt-training >/dev/null 2>&1
systemctl restart calibrayt-training
code=""
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8010/training/signin)
  [ "$code" = "200" ] && break; sleep 2
done
echo "service: $(systemctl is-active calibrayt-training)  local sign-in page: $code"
journalctl -u calibrayt-training --no-pager -n 40 | grep -E "Error|Traceback|STOP" | cut -c1-160

echo "== 4. Apache: training.calibraytai.com -> the service (http and https)"
for kind in std ssl; do
  d=/etc/apache2/conf.d/userdata/$kind/2_4/solarlight/training.calibraytai.com
  mkdir -p "$d"
  cat > "$d/calibrayt-training.conf" <<'PROXY'
# CalibraytAI Training Centre (22 Oct 2026): everything except the certificate check goes to the app.
ProxyPreserveHost On
ProxyPass /.well-known/ !
ProxyPass / http://127.0.0.1:8010/ timeout=120
ProxyPassReverse / http://127.0.0.1:8010/
PROXY
done
echo 'RequestHeader set X-Forwarded-Proto "https"' >> /etc/apache2/conf.d/userdata/ssl/2_4/solarlight/training.calibraytai.com/calibrayt-training.conf
echo 'RequestHeader set X-Forwarded-Proto "http"' >> /etc/apache2/conf.d/userdata/std/2_4/solarlight/training.calibraytai.com/calibrayt-training.conf
/scripts/rebuildhttpdconf >/dev/null && /scripts/restartsrv_httpd >/dev/null && echo "apache: reloaded"

echo "== 5. HTTPS checks"
fail=0
page=$(curl -s --max-time 30 "$SITE/training/signin")
code=$(curl -s -o /dev/null --max-time 30 -w '%{http_code}' "$SITE/training/signin")
echo "$SITE/training/signin: $code"
[ "$code" = "200" ] || fail=1
for choice in contractor field supplier; do
  if printf '%s' "$page" | grep -q "data-signin=\"$choice\""; then echo "  sign-in choice $choice: yes"; else echo "  sign-in choice $choice: MISSING"; fail=1; fi
done
for p in /login /training /field-sw.js; do
  echo "$SITE$p: $(curl -s -o /dev/null --max-time 30 -w '%{http_code}' "$SITE$p")"
done
if [ "$fail" = "0" ]; then echo "== done: $(as_app git -C $APP log --oneline -1)"; else echo "STOP: HTTPS checks failed (backup: $BACKUP)"; exit 1; fi

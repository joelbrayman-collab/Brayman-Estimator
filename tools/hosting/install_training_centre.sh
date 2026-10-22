#!/bin/bash
# CalibraytAI Training Centre on the HostPapa VPS (22 Oct 2026). Run as root in WHM Terminal.
# Prerequisites already done: system user calibrayt, /opt/calibrayt/app (git, venv), /opt/calibrayt/env (600).
# Idempotent: safe to run again. Prints no passwords or secrets.
echo "== 1. code"
sudo -u calibrayt git -C /opt/calibrayt/app fetch -q --depth 1 origin v1/training-centre-2026-10-21 \
  && sudo -u calibrayt git -C /opt/calibrayt/app reset -q --hard FETCH_HEAD
sudo -u calibrayt git -C /opt/calibrayt/app log --oneline -1
sudo -u calibrayt /opt/calibrayt/app/venv/bin/pip install -q -r /opt/calibrayt/app/requirements.txt gunicorn || { echo "STOP: pip install failed"; exit 1; }

echo "== 2. start script and service"
cat > /opt/calibrayt/run.sh <<'RUN'
#!/bin/bash
cd /opt/calibrayt/app || exit 1
set -a; . /opt/calibrayt/env; set +a
mkdir -p instance
./venv/bin/flask db upgrade || exit 1
./venv/bin/flask training build-environment --passwords-from-env || exit 1
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
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8010/training/signin)
  [ "$code" = "200" ] && break; sleep 2
done
echo "service: $(systemctl is-active calibrayt-training)  local sign-in page: $code"
journalctl -u calibrayt-training --no-pager -n 40 | grep -E "ADMIN|OWNER|Error|Traceback|STOP" | cut -c1-160

echo "== 3. Apache: training.calibraytai.com -> the service (http and https)"
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
code=$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: training.calibraytai.com' http://127.0.0.1/training/signin)
echo "through apache: $code"
echo "== done"

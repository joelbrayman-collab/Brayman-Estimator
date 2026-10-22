#!/bin/bash
# CalibraytAI public website -> calibraytai.com document root (22 Oct 2026). Run as root in WHM Terminal.
# Copies the static build from branch website/calibrayt-static-2026-10-22. Deletes nothing.
docroot=$(whmapi1 domainuserdata domain=calibraytai.com 2>/dev/null | awk '/documentroot:/{print $2; exit}')
[ -n "$docroot" ] || { echo "STOP: no document root for calibraytai.com"; exit 1; }
echo "document root: $docroot"
work=$(mktemp -d)
git clone -q --depth 1 --branch website/calibrayt-static-2026-10-22 https://github.com/joelbrayman-collab/Brayman-Estimator.git "$work/site" || { echo "STOP: download failed"; exit 1; }
git -C "$work/site" log --oneline -1
mkdir -p "$docroot"
if [ -n "$(ls -A "$docroot" 2>/dev/null)" ]; then
  b=/root/calibrayt-migration/website-before-$(date +%Y%m%d-%H%M%S).tar.gz; tar czf "$b" -C "$docroot" . && echo "previous contents saved: $b"
fi
rsync -a --exclude .git "$work/site/" "$docroot/"
chown -R solarlight:solarlight "$docroot"; find "$docroot" -type d -exec chmod 755 {} +; find "$docroot" -type f -exec chmod 644 {} +
rm -rf "$work"
echo "files: $(find "$docroot" -type f | wc -l)"
for p in / /plan/ /useful-tools/concrete/; do
  echo "$p $(curl -s -o /dev/null -w '%{http_code}' -H 'Host: calibraytai.com' http://127.0.0.1$p)"
done
echo "== done"

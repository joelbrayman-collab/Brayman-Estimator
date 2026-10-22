#!/bin/bash
# CalibraytAI storybooks on calibraytai.com (HostPapa VPS). Run as root in WHM Terminal. Safe to run again.
# Copies the four storybooks from the GitHub branch storybooks/site into the website folder, under /storybook/.
# Reads the repository through the existing /opt/calibrayt/app clone; does not change the Training Centre's code.
echo "== 1. find the calibraytai.com website folder"
# calibraytai.com may be its own cPanel domain, or an alias of another one (for example calibraytai.solarlightasaservice.com).
DOC=$(awk -F': ' '/^documentroot:/{print $2}' /var/cpanel/userdata/*/calibraytai.com 2>/dev/null | head -1)
if [ -z "$DOC" ]; then
  for f in /var/cpanel/userdata/*/*; do
    case "$f" in *.cache|*.json|*_SSL|*/main|*/cache) continue;; esac
    if grep -qE '^(servername|serveralias):.*(^|[ :])(www\.)?calibraytai\.com( |$)' "$f" && ! grep -qE '^servername: *training\.' "$f"; then
      DOC=$(awk -F': ' '/^documentroot:/{print $2}' "$f"); echo "found in $f"; break
    fi
  done
fi
if [ -z "$DOC" ] || [ ! -d "$DOC" ]; then
  echo "STOP: could not find the website folder from cPanel. These files mention calibraytai.com:"
  grep -rl "calibraytai.com" /etc/apache2/conf.d /etc/nginx /var/cpanel/userdata 2>/dev/null | head -10
  exit 1
fi
OWNER=$(stat -c %U "$DOC"); echo "website folder: $DOC (owner $OWNER)"

echo "== 2. get the storybooks"
sudo -u calibrayt git -C /opt/calibrayt/app fetch -q --depth 1 origin storybooks/site || { echo "STOP: fetch failed"; exit 1; }
TMP=$(mktemp -d)
sudo -u calibrayt git -C /opt/calibrayt/app archive FETCH_HEAD storybook | tar -x -C "$TMP" || { echo "STOP: unpack failed"; exit 1; }

echo "== 3. install under $DOC/storybook"
mkdir -p "$DOC/storybook"
cp -r "$TMP"/storybook/* "$DOC/storybook/"
chown -R "$OWNER":"$OWNER" "$DOC/storybook"; chmod -R u=rwX,go=rX "$DOC/storybook"
rm -rf "$TMP"
sha256sum "$DOC"/storybook/*/index.html

echo "== 4. check the live addresses (expect 200)"
for b in contractor supplier-connection bmr-winchester kbc; do
  printf "%-20s " "$b"; curl -s -o /dev/null -w "%{http_code}\n" "https://calibraytai.com/storybook/$b/"
done
echo "If any line is not 200, send Claude this whole output."

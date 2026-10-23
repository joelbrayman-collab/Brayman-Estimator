# Runs ON the Render instance. READ-ONLY email diagnosis: it sends nothing and changes nothing.
# Prints the email settings by NAME (a secret is shown only as set / not set), the allowlist with addresses
# masked, the last 10 email attempts the app recorded, and what Postmark itself reports for this server.
import json, os, sqlite3, sys, urllib.request, urllib.error


def mask(addr):
    addr = (addr or "").strip().lower()
    if "@" not in addr:
        return "?"
    user, dom = addr.split("@", 1)
    return (user[:2] + "***@" + dom) if user else "***@" + dom


env = os.environ.get
print("PROVIDER=" + (env("TRANSACTIONAL_EMAIL_PROVIDER") or "(not set: local capture, nothing is sent)"))
print("FROM_EMAIL=" + (env("TRANSACTIONAL_FROM_EMAIL") or "(not set)"))
print("REPLY_TO=" + (env("TRANSACTIONAL_REPLY_TO") or "(not set)"))
print("PUBLIC_BASE_URL=" + (env("PUBLIC_BASE_URL") or "(not set)"))
token = (env("POSTMARK_SERVER_TOKEN") or "").strip()
print("POSTMARK_SERVER_TOKEN=" + ("set" if token else "NOT SET"))
allow = [a.strip().lower() for a in (env("TRANSACTIONAL_UAT_ALLOWLIST") or "").split(",") if a.strip()]
print("ALLOWLIST=" + ("(empty: every address may receive email)" if not allow else
                       "%d address(es): %s" % (len(allow), ", ".join(mask(a) for a in allow))))
for extra in sys.argv[1:]:
    print("ALLOWLIST_HAS %s=%s" % (mask(extra), "yes" if extra.strip().lower() in allow else "no"))

uri = env("CALIBRAYTAI_DATABASE_URI", "")
db = uri[len("sqlite:///"):] if uri.startswith("sqlite:///") else ""
if db and os.path.exists(db):
    c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
    rows = c.execute("SELECT created_at, template_id, to_email, provider, status, error_code FROM transactional_messages "
                     "ORDER BY id DESC LIMIT 10").fetchall()
    print("== Last %d email attempts recorded by the app (newest first)" % len(rows))
    for r in rows:
        print("ATTEMPT %s %s to=%s provider=%s status=%s error=%s" % (r[0][:19], r[1], mask(r[2]), r[3], r[4], r[5] or "-"))
else:
    print("DB=not found")


def postmark(path):
    req = urllib.request.Request("https://api.postmarkapp.com" + path,
                                 headers={"Accept": "application/json", "X-Postmark-Server-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read() or b"{}"), None
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read() or b"{}")
        except Exception:
            body = {}
        return None, "HTTP %s ErrorCode=%s %s" % (e.code, body.get("ErrorCode"), body.get("Message", ""))
    except Exception as e:
        return None, "unreachable (%s)" % type(e).__name__


if token:
    print("== Postmark (read-only)")
    server, err = postmark("/server")
    print("POSTMARK_SERVER=" + (err or "%s (delivery type %s)" % (server.get("Name"), server.get("DeliveryType"))))
    out, err = postmark("/messages/outbound?count=10&offset=0")
    if err:
        print("POSTMARK_OUTBOUND=" + err)
    else:
        print("POSTMARK_OUTBOUND_TOTAL=%s" % out.get("TotalCount"))
        for m in out.get("Messages", []):
            print("SENT %s to=%s status=%s from=%s" % ((m.get("ReceivedAt") or "")[:19],
                  ",".join(mask(x) for x in m.get("Recipients", [])), m.get("Status"), m.get("From", "").split("<")[-1].rstrip(">")))
    bounces, err = postmark("/bounces?count=10&offset=0")
    if err:
        print("POSTMARK_BOUNCES=" + err)
    else:
        for b in bounces.get("Bounces", []):
            print("BOUNCE %s to=%s type=%s %s" % ((b.get("BouncedAt") or "")[:19], mask(b.get("Email")), b.get("Type"),
                  (b.get("Description") or "")[:120]))
print("EMAIL_CHECK=done (nothing was sent or changed)")

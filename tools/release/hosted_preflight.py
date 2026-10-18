# Runs ON the Render instance (read-only except one new backup file). Prints KEY=VALUE lines.
import glob, hashlib, json, os, sqlite3, sys, time

ROOT = os.environ.get("RELEASE_ROOT", "/opt/render/project/src")
DB = os.path.join(ROOT, "instance", "brayman_estimator.db")
uri = os.environ.get("CALIBRAYTAI_DATABASE_URI", "")
print("RUNNING_SHA=" + os.environ.get("RENDER_GIT_COMMIT", ""))
print("DATABASE_URI=" + uri)
# The live database must be exactly this file, named by the service's own URI.
uri_path = uri[len("sqlite:///"):] if uri.startswith("sqlite:///") else ""
if not uri_path or not os.path.exists(DB) or os.path.realpath(uri_path) != os.path.realpath(DB):
    print("FAIL=live database URI does not point at " + DB); sys.exit(1)
if os.environ.get("DECK_TAKEOFF_ROOT"):
    print("FAIL=DECK_TAKEOFF_ROOT is set; stored requests are not under instance/deck_takeoff"); sys.exit(1)
src = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
print("LIVE_INTEGRITY=" + src.execute("PRAGMA integrity_check").fetchone()[0])
print("LIVE_REVISION=" + src.execute("SELECT version_num FROM alembic_version").fetchone()[0])
stamp = time.strftime("%Y%m%d-%H%M", time.gmtime())
os.makedirs(os.path.join(ROOT, "instance", "backups"), exist_ok=True)
dest_path = os.path.join(ROOT, "instance", "backups", os.environ.get("BACKUP_PREFIX", "pre-release") + "-" + stamp + ".db")
if os.path.exists(dest_path):
    print("FAIL=backup file already exists"); sys.exit(1)
dest = sqlite3.connect(dest_path)
src.backup(dest)
dest.close(); src.close()
chk = sqlite3.connect("file:" + dest_path + "?mode=ro", uri=True)
print("BACKUP_PATH=" + dest_path)
print("BACKUP_INTEGRITY=" + chk.execute("PRAGMA integrity_check").fetchone()[0])
print("BACKUP_REVISION=" + chk.execute("SELECT version_num FROM alembic_version").fetchone()[0])
print("BACKUP_TABLES=%d" % chk.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0])
chk.close()
print("BACKUP_SHA256=" + hashlib.sha256(open(dest_path, "rb").read()).hexdigest())
# Row counts of every table, so the migration can be shown to change nothing that exists.
live = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
tables = [r[0] for r in live.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
counts = {t: live.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for t in tables}
live.close()
print("TABLE_COUNTS=" + json.dumps(counts, sort_keys=True))
print("BACKUP_BYTES=%d" % os.path.getsize(dest_path))
# Historical supplier requests: fingerprint every stored request file (read only).
files = sorted(glob.glob(os.path.join(ROOT, "instance", "deck_takeoff", "**", "requests", "*"), recursive=True))
digest = hashlib.sha256()
for f in files:
    digest.update(f.encode()); digest.update(hashlib.sha256(open(f, "rb").read()).digest())
print("STORED_REQUEST_FILES=%d" % len(files))
print("STORED_REQUESTS_FINGERPRINT=" + digest.hexdigest())
print("PREFLIGHT=ok")

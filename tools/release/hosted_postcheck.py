# Runs ON the Render instance after the deploy. Read-only SQLite checks; no application import.
import os, sqlite3, sys
uri = os.environ.get("CALIBRAYTAI_DATABASE_URI", "")
DB = uri[len("sqlite:///"):] if uri.startswith("sqlite:///") else ""
if not DB or not os.path.exists(DB):
    print("FAIL=no live SQLite database"); sys.exit(1)
c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
print("RUNNING_SHA=" + os.environ.get("RENDER_GIT_COMMIT", ""))
print("REVISION=" + c.execute("SELECT version_num FROM alembic_version").fetchone()[0])
print("INTEGRITY=" + c.execute("PRAGMA integrity_check").fetchone()[0])
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("TABLES=%d ROWS=%d" % (len(tables), sum(c.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for t in tables)))
print("PROPOSALS=%d" % c.execute("SELECT COUNT(*) FROM proposals").fetchone()[0])
print("POSTCHECK=ok")

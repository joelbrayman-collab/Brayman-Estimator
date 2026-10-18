# Runs ON the Render instance (read-only SQLite and directory checks; no application import, no writes).
# Confirms what contract signing needs before the release that turns it on.
import os, sqlite3, sys
uri = os.environ.get("CALIBRAYTAI_DATABASE_URI", "")
DB = uri[len("sqlite:///"):] if uri.startswith("sqlite:///") else ""
if not DB or not os.path.exists(DB):
    print("FAIL=no live SQLite database"); sys.exit(1)
c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
pk = c.execute("SELECT package_code, library_state, authority_class FROM legal_content_jurisdiction_packages "
               "WHERE library_state='ACTIVE' AND authority_class='PRODUCTION'").fetchall()
print("ACTIVE_PRODUCTION_PACKAGES=" + ";".join("%s/%s/%s" % row for row in pk))
print("CONSENT_VERSIONS=" + ";".join("%s/%s" % row for row in c.execute("SELECT version_code, authority_class FROM signing_consent_versions")))
print("GENERATED_CONTRACTS=%d" % c.execute("SELECT COUNT(*) FROM project_generated_contracts").fetchone()[0])
print("SIGNING_REQUESTS=" + ";".join("%s:%d" % row for row in c.execute(
    "SELECT document_family || '/' || status, COUNT(*) FROM signing_requests GROUP BY 1")))
inst = os.path.dirname(DB)
for name in ("signing_artifacts", "generated_contracts"):
    path = os.path.join(inst, name)
    print("%s=%s exists=%s writable=%s" % (name.upper(), path, os.path.isdir(path), os.access(path, os.W_OK)))
print("READINESS=" + ("ok" if pk else "NO_ACTIVE_PRODUCTION_PACKAGE"))

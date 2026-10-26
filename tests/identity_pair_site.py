"""One local site for the release gate's one-identity walk (tools/release/evidence_identity.mjs, 26 Oct 2026):
"production" (the identity provider) or "training" (connected to it; the synthetic training company). Synthetic data
only; mail is captured to files. Usage: identity_pair_site.py production|training <port> <provider port> [<training port>].
Prints READY <port>."""
import os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); os.chdir(ROOT)
from alembic import command
from alembic.config import Config
from app import create_app, db

ROLE, PORT, PROV_PORT, SECRET = sys.argv[1], int(sys.argv[2]), sys.argv[3], "synthetic-pair-secret-0123456789abcdefghijk"
OWNER = ("joel.owner@example.com", "Synthetic-Joel-prod-1", "Joel Owner (synthetic)")
work = tempfile.mkdtemp(prefix=f"pair-{ROLE}-")
uri = f"sqlite:///{work}/{ROLE}.db"
cfg = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri, "SECRET_KEY": f"pair-{ROLE}-key",
       "WTF_CSRF_ENABLED": True, "TRANSACTIONAL_EMAIL_PROVIDER": "local", "MAIL_CAPTURE_ROOT": os.environ["MAIL_" + ROLE.upper()],
       "PUBLIC_BASE_URL": f"http://127.0.0.1:{PORT}"}
if ROLE == "production":
    cfg.update(IDENTITY_CLIENTS=f"training={SECRET}", IDENTITY_TRAINING_SITE_URL=f"http://127.0.0.1:{sys.argv[4]}")
else:
    cfg.update(TRAINING_ENVIRONMENT=True, IDENTITY_PROVIDER_URL=f"http://127.0.0.1:{PROV_PORT}",
               IDENTITY_CLIENT_ID="training", IDENTITY_CLIENT_SECRET=SECRET)
app = create_app(cfg)
with app.app_context():
    c = Config(str(ROOT / "migrations" / "alembic.ini")); c.set_main_option("script_location", str(ROOT / "migrations"))
    c.set_main_option("sqlalchemy.url", uri); command.upgrade(c, "head")
    from app.models.user import UserMembership
    from app.services.instance_authority import set_instance_owner
    from tests.auth_fixtures import ensure_office_user
    if ROLE == "production":
        owner = ensure_office_user(email=OWNER[0], password=OWNER[1], display_name=OWNER[2])
        set_instance_owner("ORG-001", UserMembership.query.filter_by(user_id=owner.id).one().id, owner.id)
    else:
        from app.training.environment import build
        # Joel is the training administrator with the SAME email; his Training Centre hash is a different, old one.
        build(app, {k: f"Synthetic-{k}-training-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat", "admin")},
              administrator=(OWNER[2], OWNER[0]))
print(f"READY {PORT}", flush=True)
app.run(host="127.0.0.1", port=PORT, use_reloader=False, threaded=True)

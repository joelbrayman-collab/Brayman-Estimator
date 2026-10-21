"""Local training site for the Training Centre's browser checks and screenshot capture (21 Oct 2026).

Built as the hosted training site would be: real migrations on an empty SQLite database, TRAINING_ENVIRONMENT
on, then ``flask training build-environment`` (app/training/environment.build) with known synthetic passwords.
Outgoing mail is captured to files, CSRF is on. Synthetic data only; never reads any hosted database.
Prints ``FACTS <json>`` (people, passwords, ids) and ``READY <port>``.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app import create_app, db  # noqa: E402

PASSWORDS = {k: f"Synthetic-{k}-training-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat")}


def main():
    workdir = tempfile.mkdtemp(prefix="training-site-")
    uri = f"sqlite:///{workdir}/training.db"
    config = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
              "SECRET_KEY": "training-site-secret-key", "WTF_CSRF_ENABLED": True, "TRAINING_ENVIRONMENT": True,
              "TRANSACTIONAL_EMAIL_PROVIDER": "local", "MAIL_CAPTURE_ROOT": os.path.join(workdir, "mail"),
              "CONTRACT_ARTIFACT_ROOT": os.path.join(workdir, "contracts"),
              "SIGNING_ARTIFACT_ROOT": os.path.join(workdir, "signing"),
              "BRAND_LOGO_ROOT": os.path.join(workdir, "logos"),
              "DECK_TAKEOFF_ROOT": os.path.join(workdir, "deck_takeoff")}
    application = create_app(config)
    with application.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", uri)
        command.upgrade(cfg, "head")
        from app.training.environment import build

        people = build(application, PASSWORDS)
        facts = {"people": {k: v for k, v in people.items() if not k.startswith("_")}, **people["_facts"],
                 "mail_dir": config["MAIL_CAPTURE_ROOT"], "database_uri": uri, "workdir": workdir}
    port = int(os.environ["TRAINING_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()

"""Walk one person's journey on the training site WITHOUT changing the training site (26 Oct 2026).

Run on the HostPapa server (WHM Terminal) as the calibrayt user with the training site's settings:
    sudo -u calibrayt bash -c 'cd /opt/calibrayt/app && set -a && . /opt/calibrayt/env && set +a && \
        ./venv/bin/python tools/hosting/check_training_person.py person@example.com'

It copies training.db (SQLite online backup) to a private temporary folder, points the deployed code at the COPY,
signs in as that person inside the program (no password is read, typed, changed or printed), opens every page of
the review journey, and deletes the copy. Email and texts are switched off for the run. Prints PASS / FAIL lines and
the account's facts with the address masked. The live training database is only read, once, by the backup.
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import time


def mask(address):
    user, _, domain = (address or "").partition("@")
    return f"{user[:2]}***@{domain}"


def main(email):
    uri = os.environ.get("CALIBRAYTAI_DATABASE_URI", "")
    if not uri.startswith("sqlite:///"):
        print("STOP: CALIBRAYTAI_DATABASE_URI is not a SQLite file"); return 2
    live = uri[len("sqlite:///"):]
    work = tempfile.mkdtemp(prefix="person-check-")
    copy = os.path.join(work, "training-copy.db")
    src = sqlite3.connect(f"file:{live}?mode=ro", uri=True)
    dst = sqlite3.connect(copy)
    src.backup(dst); dst.close(); src.close()
    os.environ["CALIBRAYTAI_DATABASE_URI"] = f"sqlite:///{copy}"
    for name in ("TRANSACTIONAL_EMAIL_PROVIDER",):
        os.environ[name] = "local"
    os.environ["MAIL_CAPTURE_ROOT"] = os.path.join(work, "mail")
    for name in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "QBT_ACCESS_TOKEN", "POSTMARK_SERVER_TOKEN"):
        os.environ.pop(name, None)
    try:
        return walk(email)
    finally:
        shutil.rmtree(work, ignore_errors=True)
        print("== the copy was deleted; the live training database was not changed")


def walk(email):
    sys.path.insert(0, os.getcwd())
    from app import create_app, db
    from app.models.user import User, UserMembership
    from app.models.organization import Organization
    from app.services.access_domains import membership_is_field_only
    from app.training import service as svc

    app = create_app()
    app.config.update(SESSION_COOKIE_SECURE=False, WTF_CSRF_ENABLED=False)
    results = []

    def rec(name, ok, note=""):
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name}{' — ' + note if note else ''}")

    with app.app_context():
        user = User.query.filter(db.func.lower(User.email) == email.strip().lower()).first()
        if user is None:
            print(f"FAIL account {mask(email)} does not exist on the training site"); return 1
        memberships = UserMembership.query.filter_by(user_id=user.id).all()
        print(f"== account {mask(email)}: {user.display_name}; active={'yes' if user.is_active else 'NO'}")
        for m in memberships:
            org = db.session.get(Organization, m.organization_id)
            print(f"   company: {org.display_name if org else m.organization_id}; Field only: "
                  f"{'yes' if membership_is_field_only(m) else 'no'}; training administrator: "
                  f"{'yes' if svc.is_admin(user) is not None else 'no'}")
        trainee = svc.trainee_for(user)
        print(f"   training pathway now: {trainee.role if trainee else 'not chosen yet'}; may choose: "
              f"{', '.join(svc.allowed_roles(user)) or 'nothing'}")
        session_id = user.get_id()
        rec("account active", bool(user.is_active))

    client = app.test_client()
    with client.session_transaction() as s:
        s["_user_id"] = session_id
        s["_fresh"] = True
        s["last_activity_at"] = time.time()

    def get(path):
        r = client.get(path, follow_redirects=True)
        return r.status_code, r.get_data(as_text=True)

    status, html = get("/training")
    rec("1 Training Centre opens signed in", status == 200, f"HTTP {status}")
    r = client.post("/training/register", data={"role": "OWNER"})
    status, html = get("/training")
    rec("2 Contractor (owner) pathway with its lessons", status == 200 and html.count("/training/lessons/") > 10,
        f"{html.count('/training/lessons/')} lesson links")
    status, html = get("/training/workflow")
    rec("3 Contractor Workflow Map (/training/workflow)", status == 200 and "Workflow Map" in html, f"HTTP {status}")
    status, _ = get("/training/review/contractor")
    rec("   the old link (/training/review/contractor) is the owner-only preview", status == 403, f"HTTP {status}")
    status, html = get("/")
    rec("4 Platform (Office) opens with the same sign-in", status == 200 and 'name="password"' not in html, f"HTTP {status}")
    rec("5 Fictional company", "Brayman Construction (training)" in html)
    status, html = get("/projects/")
    rec("5 Fictional project", status == 200 and "Harbour Lane Pool Deck (training)" in html)
    office = {p: get(p)[0] for p in ("/estimating/start", "/clients/", "/schedule", "/wizards/GUIDED_ESTIMATING/start")}
    rec("6-7 Office functions", all(v == 200 for v in office.values()), str(office))
    admin_only = {p: get(p)[0] for p in ("/settings/people", "/training/admin", "/training/review", "/settings/hours-policy")}
    rec("11 Administrator-only areas refused", all(v in (403, 404) for v in admin_only.values()), str(admin_only))
    client.post("/training/register", data={"role": "FIELD"})
    status, html = get("/training")
    rec("8 Change pathway → Field Crew", status == 200 and "Field Crew" in html)
    field = {p: get(p)[0] for p in ("/field/today", "/field/week", "/field/time", "/field/projects")}
    rec("9-10 Field functions", all(v == 200 for v in field.values()), str(field))
    print("== ALL PASS" if all(results) else "== SOME FAIL")
    return 0 if all(results) else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_training_person.py person@example.com"); sys.exit(2)
    sys.exit(main(sys.argv[1]))

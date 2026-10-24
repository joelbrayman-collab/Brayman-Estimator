"""Supplier practice logins for training administrators (Joel, 24 Oct 2026). Training site only.

Joel takes the Supplier trainee pathway from his own Owner training sign-in, so his Contractor and Field progress
and every acceptance result stay on his own trainee record. A person cannot be on the contractor and the supplier
side at once (the Training Centre and the Supplier Hub fail closed for such a sign-in), so the supplier lessons'
practice in the Supplier Hub uses a separate synthetic login:

* ``environment.build`` creates, only on the training site and only for a training administrator (the training
  company's Instance Owner or a System Administrator), one login "<Name> (supplier practice)" at
  supplier-practice-<user id>@training.calibraytai.invalid. It has no usable password (it cannot sign in from a
  sign-in page), no contractor membership, and one active membership: the synthetic training supplier
  (BMR Winchester (training), demo_synthetic) only. Running build again adds nothing new.
* On a supplier lesson step, the administrator presses "Open the supplier practice site as <Name> (supplier
  practice)" (a CSRF-protected POST). The Training Centre checks again that he is a training administrator and that
  the login is his own linked, synthetic, supplier-only practice login, writes an audit line, and opens the Supplier
  Hub page signed in as that login. Every training-site page then shows "Back to the Training Centre as <Name>",
  which signs him back in as himself (same checks, audited) and returns him to the lesson step.
* Lesson progress and acceptance results are recorded only on the administrator's own trainee record. The practice
  login never registers as a trainee: any Training Centre page it opens offers the way back instead.

Nothing here changes a production permission or the live application's sign-in: with TRAINING_ENVIRONMENT off,
every function refuses and the Training Centre routes answer 404.
"""

from __future__ import annotations

import logging
import re
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlsplit

from flask import session

from app import db

DOMAIN = "training.calibraytai.invalid"
NAME_SUFFIX = " (supplier practice)"
TRAINING_SUPPLIER_CODE = "BMR-WINCHESTER-TRAINING"
SESSION_KEY = "tc_supplier_practice"
MAX_AGE = timedelta(hours=12)
_EMAIL = re.compile(r"^supplier-practice-(\d+)@training\.calibraytai\.invalid$")
_NO_PASSWORD = "!no-password:supplier-practice:"  # not a werkzeug hash: no password ever verifies against it

audit = logging.getLogger("app.training.supplier_practice")

REFUSED = "The supplier practice site is only for training administrators, on the training site."
NOT_SET_UP = ("Your supplier practice login is not set up yet. It is added when the training site is built "
              "(flask training build-environment).")


class PracticeError(ValueError):
    pass


def practice_email(admin_id: int) -> str:
    return f"supplier-practice-{int(admin_id)}@{DOMAIN}"


def practice_name(admin) -> str:
    return ((admin.display_name or admin.email or "Administrator").strip())[:150 - len(NAME_SUFFIX)] + NAME_SUFFIX


def is_practice_login(user) -> bool:
    return bool(user is not None and getattr(user, "email", None) and _EMAIL.match(user.email or ""))


def _enabled() -> bool:
    from app.training.service import enabled

    return enabled()


def training_supplier():
    from app.models.supplier_catalogue import Supplier

    return Supplier.query.filter_by(code=TRAINING_SUPPLIER_CODE, demo_synthetic=True).first()


def training_administrators(organization_id: str) -> List:
    """The training company's Instance Owner and System Administrators who are training administrators."""
    from app.models.organization import OrganizationSystemAdministratorMembership
    from app.models.user import User, UserMembership
    from app.services.instance_authority import get_instance_owner_membership
    from app.training.service import is_admin

    membership_ids = [row.membership_id for row in OrganizationSystemAdministratorMembership.query.filter_by(
        organization_id=organization_id).all()]
    owner = get_instance_owner_membership(organization_id)
    if owner is not None:
        membership_ids.insert(0, owner.id)
    out, seen = [], set()
    for mid in membership_ids:
        membership = db.session.get(UserMembership, mid)
        user = db.session.get(User, membership.user_id) if membership is not None else None
        if user is None or user.id in seen or is_practice_login(user):
            continue
        if is_admin(user) == organization_id:
            seen.add(user.id)
            out.append(user)
    return out


def ensure_practice_logins(organization_id: str, supplier) -> List[dict]:
    """environment.build (training site only): one practice login per training administrator. Idempotent."""
    if not _enabled():
        raise PracticeError(REFUSED)
    from app.models.supplier_portal import MEMBERSHIP_ACTIVE, SupplierUserMembership
    from app.models.user import User

    if supplier is None or supplier.code != TRAINING_SUPPLIER_CODE or not supplier.demo_synthetic:
        raise PracticeError("The practice login belongs to the synthetic training supplier only.")
    rows = []
    for admin in training_administrators(organization_id):
        email = practice_email(admin.id)
        user = User.query.filter_by(email=email).first()
        created = user is None
        if created:
            user = User(email=email, display_name=practice_name(admin), is_active=True,
                        password_hash=_NO_PASSWORD + secrets.token_hex(16))
            db.session.add(user)
            db.session.flush()
        if not SupplierUserMembership.query.filter_by(user_id=user.id, supplier_id=supplier.id,
                                                      status=MEMBERSHIP_ACTIVE).first():
            db.session.add(SupplierUserMembership(user_id=user.id, supplier_id=supplier.id, status=MEMBERSHIP_ACTIVE,
                                                  created_by_name="Training site set-up (supplier practice)",
                                                  created_by_organization_id=organization_id))
        db.session.commit()
        rows.append({"name": user.display_name, "email": email, "for": admin.display_name, "created": created})
    return rows


def _valid_link(practice, admin) -> bool:
    """The practice login is this administrator's own, synthetic, supplier-only login on the training supplier."""
    from app.models.supplier_portal import SupplierUserMembership
    from app.models.user import UserMembership

    if practice is None or admin is None or not practice.is_active:
        return False
    if (practice.email or "") != practice_email(admin.id) or not (practice.password_hash or "").startswith(_NO_PASSWORD):
        return False
    if UserMembership.query.filter_by(user_id=practice.id).count():
        return False  # never on the contractor side
    supplier = training_supplier()
    memberships = SupplierUserMembership.query.filter_by(user_id=practice.id).all()
    if supplier is None or [(m.supplier_id, m.status) for m in memberships] != [(supplier.id, "ACTIVE")]:
        return False
    return True


def practice_login_for(admin):
    """The administrator's own supplier practice login, or None (not on the training site, not an administrator,
    not set up, or not exactly the synthetic supplier-only login)."""
    if admin is None or not _enabled() or is_practice_login(admin):
        return None
    from app.models.user import User
    from app.training.service import is_admin

    if is_admin(admin) is None:
        return None
    practice = User.query.filter_by(email=practice_email(admin.id)).first()
    return practice if _valid_link(practice, admin) else None


def _safe_supplier_path(target: str) -> Optional[str]:
    text = (target or "").strip()
    if (not text.startswith("/supplier") or "//" in text or "\\" in text or "://" in text or len(text) > 600
            or "\n" in text or "\r" in text):
        return None
    if text not in ("/supplier", "/supplier/") and not text.startswith(("/supplier/", "/supplier?")):
        return None
    return text


def _safe_training_path(target: str) -> Optional[str]:
    text = (target or "").strip()
    if (not text.startswith("/training") or "//" in text or "\\" in text or "://" in text or len(text) > 300
            or "\n" in text or "\r" in text):
        return None
    return text


def _back_from(target: str) -> str:
    query = parse_qs(urlsplit(target).query)
    back = _safe_training_path((query.get("tc_back") or [""])[0])
    return back if back and back.startswith("/training/lessons/") else "/training"


def _remote() -> str:
    from flask import has_request_context, request

    return (request.remote_addr or "") if has_request_context() else ""


def open_practice(admin, target: str, back: str = "") -> Tuple[object, str]:
    """Sign in as the administrator's practice login and return (practice login, Supplier Hub path to open)."""
    from flask_login import login_user

    if not _enabled():
        raise PracticeError(REFUSED)
    from app.training.service import is_admin

    if admin is None or is_practice_login(admin) or is_admin(admin) is None:
        raise PracticeError(REFUSED)
    practice = practice_login_for(admin)
    if practice is None:
        raise PracticeError(NOT_SET_UP)
    supplier = training_supplier()
    path = _safe_supplier_path(target) or "/supplier/"
    back = _safe_training_path(back) or _back_from(path)
    audit.info("supplier practice opened: administrator user %s (%s) as practice login user %s (%s), supplier %s, "
               "page %s, from %s", admin.id, admin.email, practice.id, practice.email, supplier.id, path.split("?")[0],
               _remote())
    login_user(practice, remember=False)
    session[SESSION_KEY] = {"admin": admin.id, "practice": practice.id, "back": back,
                            "at": datetime.utcnow().isoformat(timespec="seconds")}
    return practice, path


def marker_for(user) -> Optional[dict]:
    """The way back for a signed-in practice login: {'admin': User, 'back': path}, or None."""
    if not _enabled() or not is_practice_login(user):
        return None
    data = session.get(SESSION_KEY) or {}
    try:
        if int(data.get("practice")) != user.id:
            return None
        at = datetime.fromisoformat(data.get("at"))
    except (TypeError, ValueError):
        return None
    if datetime.utcnow() - at > MAX_AGE:
        return None
    from app.models.user import User

    admin = db.session.get(User, int(data.get("admin") or 0))
    if admin is None or not admin.is_active or practice_login_for(admin) is None \
            or practice_login_for(admin).id != user.id:
        return None
    return {"admin": admin, "back": _safe_training_path(data.get("back") or "") or "/training"}


def return_to_admin(user, back: str = "") -> Tuple[object, str]:
    """From the practice login back to the administrator's own sign-in (same checks), and the page to go to."""
    from flask_login import login_user, logout_user

    marker = marker_for(user)
    session.pop(SESSION_KEY, None)
    if marker is None:
        if is_practice_login(user):
            logout_user()
        raise PracticeError("Sign in again as yourself to go back to your training.")
    admin = marker["admin"]
    audit.info("supplier practice closed: practice login user %s back to administrator user %s (%s), from %s",
               user.id, admin.id, admin.email, _remote())
    login_user(admin, remember=False)
    return admin, _safe_training_path(back) or marker["back"]

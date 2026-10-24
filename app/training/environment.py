"""The training site's synthetic company (Joel, 21 Oct 2026): the one connected example every lesson uses.

Built only on the training site (TRAINING_ENVIRONMENT=1, its own database); it refuses anywhere else so it
can never touch the production office. Everything is synthetic and marked so:

    Brayman Construction (training): Ben Brayman (Instance Owner), Olivia Office (office staff),
        Kevin Field and Liam Field (crew, Field only)
    Customer Morgan Ellis (training), job "Harbour Lane Pool Deck (training)", 14 Harbour Lane, Merrickville ON
    BMR Winchester (training): Darcy (store) and Pat (PRO Desk), already Brayman's supplier. BMR sells
        concrete to the contractor; Tomlinson Ready-Mix supplies it to BMR (upstream, not a CalibraytAI party).
    "<Name> (supplier practice)" for each training administrator: a BMR Winchester (training) login with no
        password, opened only from the Training Centre (app/training/practice.py).

Passwords are made at random and printed once by the command; nothing is stored in code. Running it again
changes nothing that exists (it only adds what is missing).
"""

from __future__ import annotations

import os
import secrets
from typing import Dict

from app import db

COMPANY = "Brayman Construction (training)"
OFFICE_PEOPLE = (
    ("ben", "Ben Brayman (training)", "ben@training.calibraytai.invalid", "OWNER"),
    ("olivia", "Olivia Office (training)", "olivia@training.calibraytai.invalid", "OFFICE"),
    ("kevin", "Kevin Field (training crew)", "kevin@training.calibraytai.invalid", "FIELD"),
    ("liam", "Liam Field (training crew)", "liam@training.calibraytai.invalid", "FIELD"),
)
SUPPLIER = "BMR Winchester (training)"
SUPPLIER_LOCATION = "Winchester store (training)"
SUPPLIER_PEOPLE = (
    ("darcy", "Darcy (BMR Winchester, training)", "darcy@training.calibraytai.invalid"),
    ("pat", "Pat at the PRO Desk (BMR Winchester, training)", "pat@training.calibraytai.invalid"),
)
CUSTOMER = "Morgan Ellis (training)"
JOB = "Harbour Lane Pool Deck (training)"
JOB_ADDRESS = "14 Harbour Lane, Merrickville, ON"
# Guided Estimating practice (23 Oct 2026): the customer for the synthetic new home each trainee creates, and the
# company costs the estimate review matches by unit. Kevin's Contractor Review needs no company or QuickBooks set-up:
# the labour rate and the pricing policy are already the company's (seeded by the migrations).
NEW_HOME_CUSTOMER = "Jordan Avery (training)"
PRACTICE_COSTS = (
    ("TRN-CONC-YD3", "Ready-mix concrete 25 MPa (training)", "yd3", "210.00"),
    ("TRN-CONC-M3", "Ready-mix concrete 25 MPa per m3 (training)", "m3", "275.00"),
    ("TRN-STUD-EA", "2x6 stud 92-5/8 in (training)", "ea", "7.25"),
    ("TRN-FLOOR-FT2", "Engineered flooring (training)", "ft2", "4.10"),
)


class TrainingEnvironmentError(RuntimeError):
    pass


def _require_training_site(app) -> None:
    if not (app.config.get("TRAINING_ENVIRONMENT") or os.environ.get("TRAINING_ENVIRONMENT") == "1"):
        raise TrainingEnvironmentError("Refused: this is not the training site (TRAINING_ENVIRONMENT is not 1).")


def _password() -> str:
    return "Training-" + secrets.token_urlsafe(9)


ADMIN_KEY = "admin"


def administrator_from_env() -> tuple | None:
    """The real person who runs the training site (Joel, 21 Oct 2026), from the site's settings:
    TRAINING_ADMIN_EMAIL (required) and TRAINING_ADMIN_NAME. Their first password comes from
    TRAINING_PASSWORD_ADMIN, set by them in the host's settings, so it never passes through anyone else."""
    email = (os.environ.get("TRAINING_ADMIN_EMAIL") or "").strip().lower()
    if not email:
        return None
    return (os.environ.get("TRAINING_ADMIN_NAME") or "").strip() or "Training administrator", email


def build(app, passwords: Dict[str, str] | None = None, administrator: tuple | None = None) -> Dict[str, dict]:
    """Add whatever is missing of the training company. Returns who was created, with their new password
    (people who already existed keep theirs and are listed without one)."""
    _require_training_site(app)
    from app.models import Client, Organization, Project
    from app.models.supplier_catalogue import ContractorSupplierAccount, Supplier, SupplierLocation
    from app.models.supplier_portal import MEMBERSHIP_ACTIVE, SupplierUserMembership
    from app.models.user import User, UserMembership
    from app.services.access_domains import set_field_only
    from app.services.auth import hash_password
    from app.services.brayman_v1_interim_contract import ensure_brayman_v1_interim_ontario_package
    from app.services.instance_authority import set_instance_owner
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from app.services.organizations import ensure_default_organization
    from app.services.supplier_catalogue import (
        create_contractor_supplier_account,
        create_supplier,
        create_supplier_location,
    )
    from app.services.work_structure import ensure_baseline_work_catalog

    passwords = dict(passwords or {})
    out: Dict[str, dict] = {}
    org = ensure_default_organization()
    org.legal_name = org.display_name = COMPANY
    ensure_baseline_work_catalog()
    ensure_brayman_v1_interim_ontario_package()
    db.session.commit()

    users = {}
    for key, name, email, role in OFFICE_PEOPLE:
        user = User.query.filter_by(email=email).first()
        if user is None:
            password = passwords.get(key) or _password()
            user = User(email=email, display_name=name, password_hash=hash_password(password), is_active=True)
            db.session.add(user)
            db.session.flush()
            db.session.add(UserMembership(user_id=user.id, organization_id=ORG, is_active=True))
            db.session.commit()
            out[key] = {"name": name, "email": email, "password": password, "role": role}
        else:
            out[key] = {"name": name, "email": email, "password": None, "role": role}
        users[key] = user
    ben_membership = UserMembership.query.filter_by(user_id=users["ben"].id, organization_id=ORG).one()
    set_instance_owner(ORG, ben_membership.id, users["ben"].id)
    db.session.commit()
    if administrator is not None:
        # A real administrator account (not synthetic): System Administrator of the training company, so it
        # sees the Training administrator dashboard and People & Access. An existing account keeps its password.
        from app.services.instance_authority import appoint_system_administrator

        admin_name, admin_email = administrator
        admin = User.query.filter_by(email=admin_email).first()
        created = admin is None
        if created:
            password = passwords.get(ADMIN_KEY) or _password()
            admin = User(email=admin_email, display_name=admin_name, password_hash=hash_password(password),
                         is_active=True)
            db.session.add(admin)
            db.session.flush()
        membership = UserMembership.query.filter_by(user_id=admin.id, organization_id=ORG).first()
        if membership is None:
            membership = UserMembership(user_id=admin.id, organization_id=ORG, is_active=True)
            db.session.add(membership)
            db.session.flush()
        db.session.commit()
        appoint_system_administrator(ORG, membership.id, users["ben"])
        out[ADMIN_KEY] = {"name": admin_name, "email": admin_email, "password": password if created else None,
                          "role": "ADMIN"}
    for key, _name, _email, role in OFFICE_PEOPLE:
        if role == "FIELD":
            membership = UserMembership.query.filter_by(user_id=users[key].id, organization_id=ORG).one()
            set_field_only(membership, True, users["ben"])
    db.session.commit()

    code = "BMR-WINCHESTER-TRAINING"
    supplier = Supplier.query.filter_by(code=code).first() or create_supplier(code=code, legal_name=SUPPLIER,
                                                                              demo_synthetic=True)
    location = (SupplierLocation.query.filter_by(supplier_id=supplier.id).first()
                or create_supplier_location(supplier_id=supplier.id, code="MAIN", display_name=SUPPLIER_LOCATION,
                                            demo_synthetic=True))
    if ContractorSupplierAccount.query.filter_by(organization_id=ORG, supplier_id=supplier.id).first() is None:
        create_contractor_supplier_account(organization_id=ORG, supplier_id=supplier.id,
                                           supplier_location_id=location.id)
    for key, name, email in SUPPLIER_PEOPLE:
        user = User.query.filter_by(email=email).first()
        if user is None:
            password = passwords.get(key) or _password()
            user = User(email=email, display_name=name, password_hash=hash_password(password), is_active=True)
            db.session.add(user)
            db.session.flush()
            db.session.add(SupplierUserMembership(user_id=user.id, supplier_id=supplier.id, status=MEMBERSHIP_ACTIVE,
                                                  created_by_name="Training site set-up",
                                                  created_by_organization_id=ORG))
            db.session.commit()
            out[key] = {"name": name, "email": email, "password": password, "role": "SUPPLIER"}
        else:
            out[key] = {"name": name, "email": email, "password": None, "role": "SUPPLIER"}

    client = Client.query.filter_by(organization_id=ORG, name=CUSTOMER).first()
    if client is None:
        client = Client(organization_id=ORG, name=CUSTOMER, email="morgan.ellis@training.calibraytai.invalid",
                        phone="613-555-0142", address=JOB_ADDRESS)
        db.session.add(client)
        db.session.flush()
    project = Project.query.filter_by(organization_id=ORG, name=JOB).first()
    if project is None:
        project = Project(organization_id=ORG, name=JOB, client_id=client.id, status="Estimating", address=JOB_ADDRESS)
        db.session.add(project)
        db.session.commit()
    _job_location_and_model(project)
    db.session.commit()
    _guided_estimating_practice(ORG)
    # Supplier practice logins for the training administrators (Joel, 24 Oct 2026; app/training/practice.py): the
    # supplier lessons' Supplier Hub practice, on the synthetic training supplier only, with no usable password.
    from app.training.practice import ensure_practice_logins

    out["_practice"] = ensure_practice_logins(ORG, supplier)
    out["_facts"] = {"organization_id": ORG, "supplier_id": supplier.id, "company": COMPANY, "customer": CUSTOMER,
                     "job": JOB, "supplier": SUPPLIER}
    return out


def _guided_estimating_practice(org_id) -> None:
    """The new-home customer and the practice costs for module 13 (added once; nothing else changes)."""
    from decimal import Decimal

    from app.models import Client, CostItem

    if Client.query.filter_by(organization_id=org_id, name=NEW_HOME_CUSTOMER).first() is None:
        db.session.add(Client(organization_id=org_id, name=NEW_HOME_CUSTOMER,
                              email="jordan.avery@training.calibraytai.invalid", phone="613-555-0177",
                              address="22 Lakeview Road, Kemptville, ON"))
    for code, name, unit, cost in PRACTICE_COSTS:
        if CostItem.query.filter_by(organization_id=org_id, code=code).first() is None:
            db.session.add(CostItem(organization_id=org_id, code=code, name=name, category="Material", unit=unit,
                                    unit_cost=Decimal(cost), default_markup_percent=Decimal("0"), is_active=True))
    db.session.commit()


def _job_location_and_model(project) -> None:
    """The job's civic location (so suppliers see the delivery town) and its construction model (the
    drawing a supplier request is built from). Added once."""
    from app.models.project import ProjectLocation
    from app.services.permit_foundation import establish_project_location_and_profile
    from app.services.project_construction_model import save_construction_model_revision
    from app.training.harbour_lane_model import SOURCE_REFERENCE, model

    if ProjectLocation.query.filter_by(project_id=project.id).first() is None:
        establish_project_location_and_profile(
            project.id, {"street": "14 Harbour Lane", "municipality": "Merrickville", "province_state": "Ontario",
                         "postal_zip": "K0G 1N0", "country": "Canada"},
            organization_id=project.organization_id, generated_by="Training site set-up", commit=True)
    from app.models.project_construction_model import ProjectConstructionModelRevision

    if ProjectConstructionModelRevision.query.filter_by(project_id=project.id).first() is None:
        save_construction_model_revision(organization_id=project.organization_id, project_id=project.id,
                                         content=model(), source_kind="source_document",
                                         source_reference=SOURCE_REFERENCE, actor_display_name="Training site set-up")


def register_cli(app) -> None:
    import click

    @app.cli.group("training")
    def training_group():
        """Training site (TRAINING_ENVIRONMENT=1 only)."""

    @training_group.command("build-environment")
    @click.option("--passwords-from-env", is_flag=True,
                  help="Take each person's first password from TRAINING_PASSWORD_<NAME> (e.g. TRAINING_PASSWORD_BEN) "
                       "and print no passwords. For a site started without a shell.")
    def build_environment(passwords_from_env):
        """Add the synthetic training company, its people, BMR Winchester (training) and the example job."""
        given = {}
        if passwords_from_env:
            keys = [k for k, *_ in OFFICE_PEOPLE] + [k for k, *_ in SUPPLIER_PEOPLE] + [ADMIN_KEY]
            given = {k: os.environ[f"TRAINING_PASSWORD_{k.upper()}"] for k in keys
                     if os.environ.get(f"TRAINING_PASSWORD_{k.upper()}")}
        try:
            people = build(app, given, administrator=administrator_from_env())
        except TrainingEnvironmentError as exc:
            raise click.ClickException(str(exc))
        for key, row in people.items():
            if key.startswith("_"):
                continue
            if row["password"] is None:  # the account already existed: build() left its password alone
                pw = "(already existed; password unchanged)"
            elif passwords_from_env:
                pw = "(password from the site's settings)" if key in given else "(random; reset it to sign in)"
            else:
                pw = row["password"]
            click.echo(f"{row['role']:<9} {row['name']:<48} {row['email']:<42} {pw}")
        for row in people.get("_practice", []):
            click.echo(f"{'PRACTICE':<9} {row['name']:<48} {row['email']:<42} (no password: opened from the "
                       f"Training Centre by {row['for']})")
        if not passwords_from_env:
            click.echo("Give each person their own email and password privately. Passwords are not shown again.")

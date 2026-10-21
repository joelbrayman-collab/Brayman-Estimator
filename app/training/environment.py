"""The training site's synthetic company (Joel, 21 Oct 2026): the one connected example every lesson uses.

Built only on the training site (TRAINING_ENVIRONMENT=1, its own database); it refuses anywhere else so it
can never touch the production office. Everything is synthetic and marked so:

    Brayman Construction (training): Ben Brayman (Instance Owner), Olivia Office (office staff),
        Kevin Field and Liam Field (crew, Field only)
    Customer Morgan Ellis (training), job "Harbour Lane Pool Deck (training)", 14 Harbour Lane, Merrickville ON
    BMR Winchester (training): Darcy (store) and Pat (PRO Desk), already Brayman's supplier. BMR sells
        concrete to the contractor; Tomlinson Ready-Mix supplies it to BMR (upstream, not a CalibraytAI party).

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


class TrainingEnvironmentError(RuntimeError):
    pass


def _require_training_site(app) -> None:
    if not (app.config.get("TRAINING_ENVIRONMENT") or os.environ.get("TRAINING_ENVIRONMENT") == "1"):
        raise TrainingEnvironmentError("Refused: this is not the training site (TRAINING_ENVIRONMENT is not 1).")


def _password() -> str:
    return "Training-" + secrets.token_urlsafe(9)


def build(app, passwords: Dict[str, str] | None = None) -> Dict[str, dict]:
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
    out["_facts"] = {"organization_id": ORG, "supplier_id": supplier.id, "company": COMPANY, "customer": CUSTOMER,
                     "job": JOB, "supplier": SUPPLIER}
    return out


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
            keys = [k for k, *_ in OFFICE_PEOPLE] + [k for k, *_ in SUPPLIER_PEOPLE]
            given = {k: os.environ[f"TRAINING_PASSWORD_{k.upper()}"] for k in keys
                     if os.environ.get(f"TRAINING_PASSWORD_{k.upper()}")}
        try:
            people = build(app, given)
        except TrainingEnvironmentError as exc:
            raise click.ClickException(str(exc))
        for key, row in people.items():
            if key.startswith("_"):
                continue
            if passwords_from_env:
                pw = "(password from the site's settings)" if key in given else "(random; reset it to sign in)"
            else:
                pw = row["password"] or "(already existed; password unchanged)"
            click.echo(f"{row['role']:<9} {row['name']:<48} {row['email']:<42} {pw}")
        if not passwords_from_env:
            click.echo("Give each person their own email and password privately. Passwords are not shown again.")

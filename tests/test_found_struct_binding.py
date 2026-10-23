"""Joel's decision 4 (14 Oct 2026): Foundation uses the footing quantity authority,
Structure the framing authorities; Site work stays contractor-entered (decision 1).

The binding only chooses which existing page Continue opens. Quantities still enter
the estimate through the calculation review and the contractor's confirmation.
"""

from __future__ import annotations

from pathlib import Path

from app.models.project_work_package import DELIVERY_INTERNAL, DELIVERY_SUBCONTRACT
from app.services.estimates import create_estimate
from app.services.project_setup import (
    FOOTING_AVAILABLE_COPY,
    FRAMING_AVAILABLE_COPY,
    ICF_AVAILABLE_COPY,
    NOT_APPLICABLE_COPY,
    NOT_DERIVABLE_COPY,
)
from app.services.project_work_package import confirm_package
from app.services.start_project_walk import resolve_start_project_walk
from app.services.work_structure import BASELINE_ELEMENTS, PLATFORM_ENGINE_PRODUCERS
from app.models import EstimateLineItem
from tests.test_icf_governed_estimate_path import _action, _baseline, _project, app, client  # noqa: F401

REPO = Path(__file__).resolve().parents[1]


def _confirmed(code, delivery=DELIVERY_INTERNAL, with_estimate=True):
    project = _project(f"{code} {delivery} Binding")
    confirm_package(organization_id=project.organization_id, project_id=project.id,
                    work_element_template_id=_baseline(code).id, delivery=delivery, actor="Binding Contractor")
    estimate = None
    if with_estimate:
        estimate = create_estimate(project_id=project.id, estimate_number=f"BIND-{code}-{delivery}"[:40],
                                   title=f"{code} binding", organization_id=project.organization_id)
    return project.id, estimate


def test_baseline_bindings_are_exactly_the_decided_ones():
    bindings = {code: engine for code, _n, engine, _o in BASELINE_ELEMENTS}
    assert bindings == {"SITE": None, "FOUND": "rectangular_footing", "STRUCT": "wall_framing", "ICF": "icf_wall"}
    assert PLATFORM_ENGINE_PRODUCERS == {"icf_wall", "rectangular_footing", "wall_framing"}


def test_foundation_continue_opens_the_footing_quantities(client, app):
    with app.app_context():
        project_id, estimate = _confirmed("FOUND")
        walk = resolve_start_project_walk(estimate.organization_id, project_id)
        assert walk.platform_engine_id == "rectangular_footing" and "ENGINE_ELIGIBLE" in walk.evidence
        expected = f"/estimates/{estimate.id}/versions/{estimate.current_version_id}/footing-quantities"
        lines_before = EstimateLineItem.query.count()
    html = client.get(f"/projects/{project_id}/setup").get_data(as_text=True)
    assert FOOTING_AVAILABLE_COPY in html and ICF_AVAILABLE_COPY not in html
    assert _action(html) == expected
    assert client.get(expected).status_code == 200
    with app.app_context():
        assert EstimateLineItem.query.count() == lines_before  # opening the page adds nothing


def test_structure_continue_opens_the_framing_and_deck_member_quantities(client, app):
    with app.app_context():
        project_id, estimate = _confirmed("STRUCT")
        walk = resolve_start_project_walk(estimate.organization_id, project_id)
        assert walk.platform_engine_id == "wall_framing"
        expected = f"/estimates/{estimate.id}/versions/{estimate.current_version_id}/calculations"
    html = client.get(f"/projects/{project_id}/setup").get_data(as_text=True)
    assert FRAMING_AVAILABLE_COPY in html and _action(html) == expected
    listing = client.get(expected).get_data(as_text=True)
    assert "framing-quantities" in listing and "footing-quantities" in listing


def test_site_work_stays_contractor_entered(client, app):
    with app.app_context():
        project_id, estimate = _confirmed("SITE")
        walk = resolve_start_project_walk(estimate.organization_id, project_id)
        assert walk.platform_engine_id is None and "ENGINE_REQUIREMENT_NOT_DERIVABLE" in walk.evidence
    html = client.get(f"/projects/{project_id}/setup").get_data(as_text=True)
    assert NOT_DERIVABLE_COPY in html and "allowances or subcontract costs" in html
    assert _action(html) == f"/estimates/{estimate.id}"


def test_subcontracted_foundation_needs_no_crew_calculation(client, app):
    with app.app_context():
        project_id, _e = _confirmed("FOUND", delivery=DELIVERY_SUBCONTRACT)
        walk = resolve_start_project_walk(_e.organization_id, project_id)
        assert walk.platform_engine_id is None and "ENGINE_NOT_APPLICABLE" in walk.evidence
    assert NOT_APPLICABLE_COPY in client.get(f"/projects/{project_id}/setup").get_data(as_text=True)


def test_the_migration_binds_only_baseline_rows_and_reverses(tmp_path):
    """Upgrade then downgrade on a disposable database built from the migrations."""
    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from app import create_app, db

    db_uri = f"sqlite:///{tmp_path / 'binding.db'}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg = Config(str(REPO / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(REPO / "migrations"))
        cfg.set_main_option("sqlalchemy.url", db_uri)
        assert ScriptDirectory.from_config(cfg).get_heads() == ["w7d3b9c1e5a8"]

        def rows():
            with db.engine.begin() as conn:
                return dict(conn.execute(sa.text(
                    "SELECT code, platform_engine_id FROM work_element_templates "
                    "WHERE organization_id IS NULL AND code IN ('SITE','FOUND','STRUCT','ICF')")).fetchall())

        command.upgrade(cfg, "v2c3d4e5f6a7")
        before = rows()
        assert set(before) >= {"FOUND", "STRUCT", "ICF"}
        assert before["FOUND"] is None and before["STRUCT"] is None and before["ICF"] == "icf_wall"
        command.upgrade(cfg, "y2b3c4d5e6f7")
        assert rows() == {**before, "FOUND": "rectangular_footing", "STRUCT": "wall_framing"}
        command.downgrade(cfg, "v2c3d4e5f6a7")
        assert rows() == before


def test_site_work_entered_by_hand_is_costed_priced_and_issued(app):
    """Decision 1: contractor-entered quantity and allowance lines go through the same
    costing approval, pricing and proposal issue rule as everything else."""
    from decimal import Decimal

    from app.services.estimate_builder import add_manual_line, create_section
    from app.services.proposals import create_proposal, create_proposal_template
    from tests.proposal_issue_support import approve_for_issue

    with app.app_context():
        _project_id, estimate = _confirmed("SITE")
        version = estimate.current_version
        section = create_section(version, name="Site work")
        add_manual_line(section, line_type="Custom", description="Strip topsoil (contractor quantity)",
                        quantity=120, unit="m2", unit_cost=4)
        add_manual_line(section, line_type="Allowance", description="Rock removal allowance",
                        quantity=1, unit="ls", unit_cost=2500)
        approve_for_issue(version)
        assert version.pricing_snapshot.direct_cost_basis == Decimal("2980.00")
        template = create_proposal_template(name="Site D1", is_active=True, default_intro_text="Intro",
                                            default_payment_terms="Net 30")
        proposal = create_proposal(estimate=estimate, version=version, template=template, status="Issued")
        assert proposal.status == "Issued"

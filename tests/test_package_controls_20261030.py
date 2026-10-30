"""Cost, margin, actuals and closeout by work package (Joel, 30 Oct 2026). Synthetic data only."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import db
from app.models import LabourTimeEntry, ProjectWorkActivity, ProjectWorkElement
from app.project_controls.models import ChangeOrder, ChangeOrderItem
from app.services import package_controls as PC
from app.services import procurement_gate as PG
from tests.auth_fixtures import ensure_office_user
from tests.test_governed_schedule_20261030 import MONDAY, _seeded
from tests.test_work_packages_20261030 import JOEL, app  # noqa: F401

M = Decimal


def _time(project, element, hours, day, worker):
    activity = ProjectWorkActivity.query.filter_by(project_work_element_id=element.id).first()
    db.session.add(LabourTimeEntry(organization_id=project.organization_id, worker_user_id=worker.id,
                                   worker_display_name=worker.display_name, work_date=day, hours=M(hours),
                                   project_id=project.id, project_work_element_id=element.id,
                                   project_work_activity_id=activity.id, project_name=project.name,
                                   element_display_name=element.display_name,
                                   activity_display_name=activity.display_name, scope_origin="ORIGINAL",
                                   status="APPROVED"))


def test_cost_report_and_closeout_by_package(app):
    project = _seeded()
    worker = ensure_office_user(email="crew@example.invalid", password="synthetic-password-2",
                                display_name="Crew (synthetic)")
    elements = {e.display_name: e for e in ProjectWorkElement.query.filter_by(project_id=project.id)}
    siding = elements["HardiePanel siding & battens"]
    _time(project, siding, "50", MONDAY, worker)
    _time(project, siding, "46", MONDAY + timedelta(days=3), worker)
    db.session.commit()
    commitment = PG.propose_subcontract(project, actor_name=JOEL, subcontractor_name="Soffit Co (synthetic)",
                                        scope_text="Soffit", amount="2500", guided_stage_id=siding.guided_stage_id)
    from tests.schedule_support import company_manager

    PG.approve_subcontract(commitment, user=company_manager(project.organization_id))
    change = ChangeOrder(organization_id=project.organization_id, project_id=project.id, number="CO-SYN-1",
                         title="Extra battens (synthetic)", status="Approved")
    db.session.add(change)
    db.session.flush()
    db.session.add(ChangeOrderItem(change_order_id=change.id, description="Battens", quantity=M("1"), unit="ls",
                                   unit_price=M("1200"), total=M("1200.00"), guided_stage_id=siding.guided_stage_id))
    db.session.commit()

    report = PC.package_cost_report(project)
    rows = {r["package"].display_name: r for r in report["rows"]}
    row = rows["HardiePanel siding & battens"]
    assert row["estimate_hours"] == M("84.00") and row["actual_hours"] == M("96.00")
    assert row["estimate_direct"] == M("17021.28")  # 10,721.28 + 84 h x $75
    assert row["committed"] == M("2500.00") and row["change"] == M("1200.00")
    assert row["actual_labour"] == M("7200.00")
    assert row["forecast"] == M("10721.28") + M("7200.00")  # non-labour estimate + labour already beyond estimate
    assert row["margin"] == row["revenue"] - row["forecast"]
    assert report["totals"]["estimate_hours"] == M("304.00")

    closeout = PC.closeout_report(project)
    siding_row = next(r for r in closeout["rows"] if r["package"].display_name == "HardiePanel siding & battens")
    assert siding_row["productivity_factor"] == M("1.143") and siding_row["actual_days"] == 4
    with pytest.raises(ValueError, match="person"):
        PC.record_closeout(project, actor="system")
    PC.record_closeout(project, actor=JOEL, note="Siding ran long (synthetic)")
    proposals = {p["name"]: p for p in PC.calibration_proposals(project.organization_id)}
    assert proposals["HardiePanel siding & battens"]["average_factor"] == M("1.143")


def test_controls_page(app):
    from tests.auth_fixtures import login_office_user

    project = _seeded()
    ensure_office_user()
    http = app.test_client()
    login_office_user(http)
    page = http.get(f"/projects/{project.id}/package-controls").get_data(as_text=True)
    assert "data-package-controls" in page and page.count("data-package-row=") == 8
    http.post(f"/projects/{project.id}/package-controls", data={"note": "First closeout (synthetic)"})
    page = http.get(f"/projects/{project.id}/package-controls").get_data(as_text=True)
    assert "First closeout (synthetic)" in page

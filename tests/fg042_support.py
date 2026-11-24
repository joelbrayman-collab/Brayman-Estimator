"""Shared synthetic fixtures for the FG-042 (Living Project P&L Gate 1) tests."""

from __future__ import annotations

from decimal import Decimal

from app import db
from app.models import Client, Project
from app.models.work_structure import ProjectWorkActivity, ProjectWorkElement
from app.services import create_estimate
from app.services.estimates import set_version_status
from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.work_structure import seed_project_work_structure


def seeded_project(name="FG042 synthetic project", quantity="800", code="LT-FG042"):
    client_row = Client(name=f"{name} Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.flush()
    project = Project(name=name, client_id=client_row.id, organization_id=DEFAULT_ORGANIZATION_ID,
                      status="Estimating")
    db.session.add(project)
    db.session.commit()
    task = create_labour_task(task_code=code, canonical_name="Forms", production_unit="sq ft",
                              unit_of_measure="sqft", trade="Concrete", category="Foundation",
                              organization_id=DEFAULT_ORGANIZATION_ID, created_by="Joel Brayman")
    estimate = create_estimate(project_id=project.id, estimate_number=f"EST-{code}", title="FG042 synthetic")
    version = estimate.current_version
    create_estimate_labour_snapshot(
        estimate_version_id=version.id, labour_task_id=task.id, quantity=Decimal(quantity),
        override_production_rate=Decimal("0.05"), override_production_reason="FG042 test",
        override_direct_labour_cost_rate=Decimal("65"), override_direct_labour_reason="FG042 test",
        created_by="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    set_version_status(version, "Issued")
    db.session.refresh(version)
    seed_project_work_structure(project_id=project.id, estimate_version_id=version.id, seeded_by="Joel Brayman")
    activity = ProjectWorkActivity.query.join(ProjectWorkElement).filter(
        ProjectWorkElement.project_id == project.id).one()
    return project, activity, version

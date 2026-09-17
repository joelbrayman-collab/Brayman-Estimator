"""FG-035 PERF-C derived Company Attention.

Office / management only. Consumes sealed PERF-B Project attention.
No persistence. No second fact engine. No Field surface.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.presentation import contractor_copy
from app.services.project_performance import (
    FACT_EXTRA_WORK_NEEDS_REVIEW,
    FACT_LABOUR_ALLOWANCE_USED,
    FACT_LABOUR_GETTING_CLOSE,
    FACT_LABOUR_OVER_ALLOWANCE,
    FACT_SCHEDULED_FINISH_PASSED,
    FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME,
    FACT_SEQUENCE,
    assemble_project_attention,
)
from app.services.shared_api import list_organization_projects

SEALED_FACT_TYPES = frozenset(
    {
        FACT_EXTRA_WORK_NEEDS_REVIEW,
        FACT_LABOUR_GETTING_CLOSE,
        FACT_LABOUR_ALLOWANCE_USED,
        FACT_LABOUR_OVER_ALLOWANCE,
        FACT_SCHEDULED_FINISH_PASSED,
        FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME,
        FACT_SEQUENCE,
    }
)


def assemble_company_attention(
    organization_id, *, today: Optional[date] = None
) -> dict:
    """Return organization-wide attention facts derived from sealed PERF-B."""
    projects = _ordered_organization_projects(organization_id)
    items = []
    grouped = []
    for project in projects:
        attention = assemble_project_attention(
            organization_id, project.id, today=today
        )
        project_items = []
        for fact in attention.get("items") or []:
            if fact.get("fact_type") not in SEALED_FACT_TYPES:
                continue
            row = _company_item(project, fact)
            items.append(row)
            project_items.append(row)
        if project_items:
            grouped.append(
                {
                    "project": _project_identity(project),
                    "items": project_items,
                }
            )
    return {
        "question": contractor_copy.COMPANY_ATTENTION_QUESTION,
        "items": items,
        "projects": grouped,
        "positive": not items,
        "positive_title": contractor_copy.LABOUR_NOTHING_NEEDS_ATTENTION,
    }


def _ordered_organization_projects(organization_id):
    """Preserve list_organization_projects created_at desc, with id desc tiebreaker."""
    projects = list(list_organization_projects(organization_id))
    return sorted(
        projects,
        key=lambda project: (project.created_at, project.id),
        reverse=True,
    )


def _project_identity(project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "project_number": project.project_number,
        "status": project.status,
    }


def _company_item(project, fact: dict) -> dict:
    identity = _project_identity(project)
    return {
        "fact_type": fact.get("fact_type"),
        "title": fact.get("title"),
        "detail": fact.get("detail"),
        "project_id": project.id,
        "project": identity,
        "work": fact.get("work"),
        "destination": fact.get("destination"),
    }

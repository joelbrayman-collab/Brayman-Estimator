"""Governed workflow documents the contractor sees on a project.

The page iterates this register. A later document is a new entry here.
Presentation only. This module does not generate documents.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Optional, Sequence

from flask import url_for

from app.models.estimate import Estimate


@dataclass(frozen=True)
class WorkflowDocument:
    family_id: str
    name: str
    audience: str
    group: str
    group_title: str
    stage: str
    purpose: str
    availability_label: str
    action_key: Optional[str] = None
    warning: str = ""


WORKFLOW_DOCUMENTS: tuple = (
    WorkflowDocument(
        family_id="01",
        name="Labour Calculation Detail",
        audience="Internal",
        group="internal",
        group_title="Internal working documents",
        stage="Estimating",
        purpose="How the labour hours on this job were calculated.",
        availability_label="Not yet available",
    ),
    WorkflowDocument(
        family_id="02",
        name="Internal Detailed Cost Breakdown",
        audience="Internal",
        group="internal",
        group_title="Internal working documents",
        stage="Estimating",
        purpose="How the price was built from cost. For the office, not the customer.",
        availability_label="Current office view",
        action_key="internal_breakdown",
    ),
    WorkflowDocument(
        family_id="03",
        name="Customer Facing Estimate",
        audience="Customer",
        group="customer",
        group_title="Customer documents",
        stage="Customer price",
        purpose="The estimate prepared for the customer.",
        availability_label="Not yet available",
    ),
    WorkflowDocument(
        family_id="04",
        name="QuickBooks Estimate Entry",
        audience="Internal",
        group="internal",
        group_title="Internal working documents",
        stage="Office entry",
        purpose=(
            "What the office types into QuickBooks by hand. "
            "Not a customer document. Nothing is sent to QuickBooks."
        ),
        availability_label="Current office entry",
        action_key="quickbooks_entry",
    ),
    WorkflowDocument(
        family_id="05",
        name="Ontario Construction Contract",
        audience="Customer",
        group="contract",
        group_title="Contract",
        stage="Contract",
        purpose="A draft presentation of an Ontario construction contract.",
        availability_label="Commercial draft",
        warning="Commercial draft. Not for execution. Not for signature.",
    ),
    WorkflowDocument(
        family_id="06",
        name="Door / Window / Skylight Schedule",
        audience="Customer",
        group="customer",
        group_title="Customer documents",
        stage="Customer documents",
        purpose="The doors, windows, and skylights on the job, for the customer.",
        availability_label="Not yet available",
    ),
    WorkflowDocument(
        family_id="07",
        name="Client Construction Proposal",
        audience="Customer",
        group="customer",
        group_title="Customer documents",
        stage="Customer proposal",
        purpose="The proposal prepared for the customer.",
        availability_label="Not yet available",
    ),
)


def _internal_breakdown_href(project) -> Optional[str]:
    estimates = (
        Estimate.query.filter_by(
            project_id=project.id,
            organization_id=project.organization_id,
        )
        .order_by(Estimate.id.desc())
        .all()
    )
    for estimate in estimates:
        version = estimate.current_version
        if version is not None:
            return url_for(
                "estimates.internal_cost_breakdown",
                id=estimate.id,
                version_id=version.id,
            )
    return None


def _href_for(project, document: WorkflowDocument) -> Optional[str]:
    if document.action_key == "internal_breakdown":
        return _internal_breakdown_href(project)
    if document.action_key == "quickbooks_entry":
        return url_for("estimate_quickbooks.review", project_id=project.id)
    return None


def workflow_document_groups(project, register: Optional[Sequence[WorkflowDocument]] = None):
    """Group register rows for one project. Unknown groups still appear."""
    documents = WORKFLOW_DOCUMENTS if register is None else register
    grouped = []
    index = {}
    for document in documents:
        href = _href_for(project, document)
        label = document.availability_label
        if document.action_key == "internal_breakdown" and href is None:
            label = "No estimate on this job yet"
        row = SimpleNamespace(
            family_id=document.family_id,
            name=document.name,
            audience=document.audience,
            stage=document.stage,
            purpose=document.purpose,
            availability_label=label,
            warning=document.warning,
            href=href,
        )
        if document.group not in index:
            index[document.group] = len(grouped)
            grouped.append(
                SimpleNamespace(
                    key=document.group,
                    title=document.group_title,
                    documents=[],
                )
            )
        grouped[index[document.group]].documents.append(row)
    return grouped

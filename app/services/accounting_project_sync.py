"""Projects into QuickBooks Online and QuickBooks Time (Joel, 25 Oct 2026, approved item A).

CalibraytAI owns the operational project; QuickBooks Online owns the accounting. When a project is created or its
proposal accepted (and again by ``flask quickbooks-online sync-projects`` and Sync now), CalibraytAI makes sure that:

- QuickBooks Online has the customer (the CalibraytAI client) and the project as a sub-customer
  (Accounting API v3 Customer, ``Job: true``, ``ParentRef`` → the customer), named like the job reference the
  QuickBooks files and receipts already use ("<project number> <project name>");
- QuickBooks Time has a job code for it (``/jobcodes``); Shop / Company Work is ONE fixed job code, linked to every
  shop / company category so approved shop time goes to it.

Never a duplicate: a stored id is used first (read again for its current SyncToken); otherwise an exact name is looked
up. A record CalibraytAI made itself is recognised (the QuickBooks Online Notes carry [CT-C…] / [CT-P…]; a lost
QuickBooks Time answer is followed by a look-up before any second try) and adopted. Anything else with the same name is
an existing job: it is matched ONCE, by Suzanne or the owner on Accounting → QuickBooks projects, never automatically.
Every create carries Intuit's requestid (QuickBooks Online), so a retry returns the first answer.

Renames send the new name, and a closed project is made inactive (reopened: active again) — sparse updates of
DisplayName / Active only (QuickBooks Time: name / active). No accounting field is overwritten, nothing is deleted,
and no financial transaction is created here. Mismatches and failures are listed in WHAT NEEDS MY ATTENTION? with
a retry. Every step is in the QuickBooks history (quickbooks_online_events, with the project).

Off unless switched on: QBO_PROJECT_SYNC_ENABLED=1 (default off) on top of the QuickBooks Online connection
(app/services/quickbooks_online.py) and the QuickBooks Time connection (QBT_SYNC_ENABLED, QBT_ACCESS_TOKEN).
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Optional

from flask import current_app, has_app_context

from app import db
from app.models import Project
from app.models.field_operations import (
    PSYNC_FAILED,
    PSYNC_NEEDS_CONFIRM,
    PSYNC_OFF,
    PSYNC_PENDING,
    PSYNC_SENT,
    PSYNC_SYNCED,
    QBO_LINK_CUSTOMER,
    AccountingProjectLink,
    QuickBooksOnlineEvent,
)
from app.services.field_operations import actor_label

ENV_ENABLED = "QBO_PROJECT_SYNC_ENABLED"
SHOP_JOBCODE_NAME = "Shop / Company Work"


class ProjectSyncError(ValueError):
    pass


def enabled() -> bool:
    value = ""
    if has_app_context():
        value = str(current_app.config.get(ENV_ENABLED) or "")
    return (value or os.environ.get(ENV_ENABLED, "")).strip() == "1"


def jobcodes_from_qbo() -> bool:
    """QBT_JOBCODES_FROM_QBO=1: the company's QuickBooks Time imports jobs from QuickBooks Online (Intuit's own
    integration), so CalibraytAI links to the imported job code instead of making one. Default off (Joel's
    instruction: CalibraytAI makes the job code); Shop / Company Work is always made here."""
    value = ""
    if has_app_context():
        value = str(current_app.config.get("QBT_JOBCODES_FROM_QBO") or "")
    return (value or os.environ.get("QBT_JOBCODES_FROM_QBO", "")).strip() == "1"


def _salt(org: str) -> str:
    return hashlib.sha256(org.encode()).hexdigest()[:8]


def _event(org, project_id, kind, message, *, actor=None, detail=None):
    db.session.add(QuickBooksOnlineEvent(organization_id=org, project_id=project_id, kind=kind[:30],
                                         message=message[:4000], detail_json=detail,
                                         actor_user_id=getattr(actor, "id", None),
                                         actor_name=actor_label(actor) if actor is not None else "CalibraytAI"))


def link_for(project, *, create: bool = False) -> Optional[AccountingProjectLink]:
    row = AccountingProjectLink.query.filter_by(project_id=project.id).first()
    if row is None and create:
        row = AccountingProjectLink(organization_id=project.organization_id, project_id=project.id,
                                    qbo_status=PSYNC_OFF, qbt_status=PSYNC_OFF)
        db.session.add(row)
        db.session.flush()
    return row


def project_name(project) -> str:
    from app.services.accounting import job_reference

    return job_reference(project)[:100]  # QuickBooks DisplayName: at most 100 characters


def _is_company(project) -> bool:
    from app.services.time_entry import is_company_time_project

    return is_company_time_project(project)


def _active(project) -> bool:
    return getattr(project, "operating_state", "ACTIVE") == "ACTIVE"


def mark(kind: str, number: int) -> str:
    return f"[CT-{kind}{number}]"


# ----------------------------------------------------------------------------------------------- the hooks
def project_changed(project, *, actor=None) -> None:
    """Called after a project is created, accepted, renamed, closed or reopened. Never raises to the page."""
    if project is None or not enabled():
        return
    try:
        sync_project(project, actor=actor)
    except Exception:  # the office's own action has already succeeded; the sync is retried later
        db.session.rollback()
        import logging

        logging.getLogger(__name__).exception("project sync to QuickBooks could not run")
        if has_app_context() and current_app.testing:
            raise


def sync_project(project, *, actor=None) -> AccountingProjectLink:
    link = link_for(project, create=True)
    link.attempts = (link.attempts or 0) + 1
    if not _is_company(project):
        _sync_qbo(project, link, actor)
    _sync_qbt(project, link, actor)
    if link.qbo_status in (PSYNC_SYNCED, PSYNC_OFF) and link.qbt_status in (PSYNC_SYNCED, PSYNC_OFF):
        link.last_synced_at = datetime.utcnow()
    db.session.commit()
    return link


def sync_all(organization_id: Optional[str] = None, *, actor=None) -> dict:
    summary = {"projects": 0, "synced": 0, "confirm": 0, "failed": 0, "waiting": 0}
    if not enabled():
        return {**summary, "off": 1}
    query = Project.query
    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    for project in query.order_by(Project.id).all():
        summary["projects"] += 1
        link = sync_project(project, actor=actor)
        statuses = {link.qbo_status, link.qbt_status}
        if PSYNC_FAILED in statuses:
            summary["failed"] += 1
        elif PSYNC_NEEDS_CONFIRM in statuses:
            summary["confirm"] += 1
        elif PSYNC_PENDING in statuses or PSYNC_SENT in statuses:
            summary["waiting"] += 1
        else:
            summary["synced"] += 1
    return summary


# ------------------------------------------------------------------------------------------- QuickBooks Online
def _qbo():
    from app.services import quickbooks_online as qbo

    return qbo


def _sync_qbo(project, link, actor):
    qbo = _qbo()
    org = project.organization_id
    conn = qbo.connection(org)
    transport = qbo.get_transport()
    if transport is None or conn is None or not qbo.is_connected(org):
        link.qbo_status = PSYNC_PENDING
        link.qbo_last_error = "Waiting: QuickBooks Online is not connected."
        return
    if link.qbo_status == PSYNC_NEEDS_CONFIRM:
        return  # an existing job waits for Suzanne or the owner
    try:
        previous_customer = link.qbo_customer_id
        customer_id = _ensure_customer(qbo, conn, transport, project, link, actor)
        if customer_id is None:
            return
        _ensure_qbo_project(qbo, conn, transport, project, link, customer_id, actor,
                            previous_customer=previous_customer)
    except qbo.TransportError:
        link.qbo_status = PSYNC_SENT
        link.qbo_last_error = ("QuickBooks Online could not be reached, so it is not known whether it arrived. Retry is "
                               "safe: CalibraytAI checks QuickBooks first and sends the same request id.")
        _event(org, project.id, "PROJECT_UNKNOWN", link.qbo_last_error, actor=actor)
    except (qbo.QuickBooksOnlineError, ProjectSyncError) as exc:
        link.qbo_status = PSYNC_FAILED
        link.qbo_last_error = str(exc)
        _event(org, project.id, "PROJECT_FAILED", f"{project_name(project)}: {exc}", actor=actor)


def _customer_query(qbo, conn, transport, name):
    return qbo._query(conn, transport, f"select * from Customer where DisplayName = '{qbo._q(name)}' "
                                       "and Active IN (true, false)")


def _read_customer(qbo, conn, transport, customer_id):
    status_code, payload = qbo._call(conn, transport, "GET", f"customer/{customer_id}")
    if status_code != 200 or "Customer" not in payload:
        return None
    return payload["Customer"]


def _write_customer(qbo, conn, transport, body, *, request_id):
    status_code, payload = qbo._call(conn, transport, "POST", "customer", params={"requestid": request_id},
                                     json_body=body)
    if status_code != 200 or "Customer" not in payload:
        raise ProjectSyncError(qbo._fault_text(payload) or f"QuickBooks answered {status_code}.")
    return payload["Customer"]


def _candidates(rows):
    return [{"id": str(r["Id"]), "name": r.get("DisplayName"), "parent": (r.get("ParentRef") or {}).get("value"),
             "job": bool(r.get("Job")), "active": r.get("Active", True)} for r in rows]


def _ensure_customer(qbo, conn, transport, project, link, actor):
    from app.models import Client
    from app.services.quickbooks_online import _link, _save_link

    org = project.organization_id
    client = db.session.get(Client, project.client_id) if project.client_id else None
    if client is None:
        raise ProjectSyncError("The project has no customer in CalibraytAI.")
    key = f"client:{client.id}"
    stored = _link(org, QBO_LINK_CUSTOMER, key)
    if stored is not None:
        row = _read_customer(qbo, conn, transport, stored.qbo_id)
        if row is None:
            raise ProjectSyncError(f"QuickBooks no longer has customer {stored.qbo_id} for {client.name}.")
        link.qbo_customer_id, link.qbo_customer_sync_token = str(row["Id"]), str(row.get("SyncToken"))
        return link.qbo_customer_id
    name = client.name[:100]
    found = _customer_query(qbo, conn, transport, name)
    ours = [r for r in found if mark("C", client.id) in (r.get("Notes") or "")]
    if ours:
        row = ours[0]
    elif found:
        link.qbo_status = PSYNC_NEEDS_CONFIRM
        link.qbo_candidates_json = {"what": "customer", "name": name, "client_id": client.id,
                                    "candidates": _candidates(found)}
        link.qbo_last_error = (f"QuickBooks already has a customer named '{name}'. Confirm it is this customer "
                               "(Accounting → QuickBooks projects).")
        _event(org, project.id, "CUSTOMER_MATCH", link.qbo_last_error, actor=actor)
        return None
    else:
        row = _write_customer(qbo, conn, transport, {
            "DisplayName": name, "Notes": f"Created by CalibraytAI {mark('C', client.id)}",
            **({"PrimaryEmailAddr": {"Address": client.email}} if getattr(client, "email", None) else {})},
            request_id=f"CT-CUST-{_salt(org)}-{client.id}")
        _event(org, project.id, "CUSTOMER_CREATED", f"Customer '{name}' created in QuickBooks ({row['Id']}).",
               actor=actor, detail={"customer_id": row["Id"]})
    _save_link(org, actor, QBO_LINK_CUSTOMER, key, row)
    link.qbo_customer_id, link.qbo_customer_sync_token = str(row["Id"]), str(row.get("SyncToken"))
    return link.qbo_customer_id


def _ensure_qbo_project(qbo, conn, transport, project, link, customer_id, actor, *, previous_customer=None):
    from app.services.quickbooks_online import _save_link, customer_key

    org = project.organization_id
    name = project_name(project)
    active = _active(project)
    if link.qbo_project_id:
        row = _read_customer(qbo, conn, transport, link.qbo_project_id)
        if row is None:
            raise ProjectSyncError(f"QuickBooks no longer has project {link.qbo_project_id}. Check it in QuickBooks.")
        parent = str((row.get("ParentRef") or {}).get("value") or "")
        if previous_customer and previous_customer != customer_id and parent != customer_id:
            # The job was moved to another customer in CalibraytAI. Moving a project between customers is an
            # accounting change, so CalibraytAI does not make it; the office moves it in QuickBooks, then Retry.
            link.qbo_customer_id = previous_customer
            raise ProjectSyncError(f"The job's customer changed in CalibraytAI; in QuickBooks the project "
                                   f"{link.qbo_project_id} is still under customer {parent or previous_customer}. "
                                   "Move it in QuickBooks if that is right, then press Retry.")
    else:
        found = [r for r in _customer_query(qbo, conn, transport, name)]
        ours = [r for r in found if mark("P", project.id) in (r.get("Notes") or "")]
        if ours:
            row = ours[0]
            _event(org, project.id, "PROJECT_ADOPTED", f"'{name}' was already made by CalibraytAI ({row['Id']}).",
                   actor=actor)
        elif found:
            link.qbo_status = PSYNC_NEEDS_CONFIRM
            link.qbo_candidates_json = {"what": "project", "name": name, "candidates": _candidates(found)}
            link.qbo_last_error = (f"QuickBooks already has '{name}'. Confirm it is this job (Accounting → QuickBooks "
                                   "projects); it is matched once.")
            _event(org, project.id, "PROJECT_MATCH", link.qbo_last_error, actor=actor)
            return
        else:
            row = _write_customer(qbo, conn, transport, {
                "DisplayName": name, "Job": True, "ParentRef": {"value": customer_id}, "BillWithParent": True,
                "Active": active, "Notes": f"CalibraytAI project {mark('P', project.id)}"},
                request_id=f"CT-PROJ-{_salt(org)}-{project.id}")
            _event(org, project.id, "PROJECT_CREATED", f"Project '{name}' created in QuickBooks under the customer "
                   f"({row['Id']}).", actor=actor, detail={"project_qbo_id": row["Id"], "parent": customer_id})
    link.qbo_project_id, link.qbo_project_sync_token = str(row["Id"]), str(row.get("SyncToken"))
    changes = {}
    if row.get("DisplayName") != name:
        changes["DisplayName"] = name
    if bool(row.get("Active", True)) != active:
        changes["Active"] = active
    if changes:
        updated = _write_customer(qbo, conn, transport, {"Id": link.qbo_project_id,
                                                         "SyncToken": link.qbo_project_sync_token, "sparse": True,
                                                         **changes},
                                  request_id=f"CT-PROJ-{_salt(org)}-{project.id}-U{link.qbo_project_sync_token}")
        link.qbo_project_sync_token = str(updated.get("SyncToken"))
        _event(org, project.id, "PROJECT_UPDATED", f"QuickBooks project {link.qbo_project_id}: "
               + ", ".join(f"{k} → {v}" for k, v in changes.items()) + " (only these fields).", actor=actor,
               detail={"changes": changes})
    link.qbo_synced_name, link.qbo_synced_active = name, active
    link.qbo_status, link.qbo_last_error, link.qbo_candidates_json = PSYNC_SYNCED, None, None
    _save_link(org, actor, QBO_LINK_CUSTOMER, customer_key(project.id), {"Id": link.qbo_project_id,
                                                                         "DisplayName": name})


# --------------------------------------------------------------------------------------------- QuickBooks Time
def _jobcodes(payload) -> list:
    return list(((payload or {}).get("results") or {}).get("jobcodes", {}).values())


def _sync_qbt(project, link, actor):
    from app.services.quickbooks_time import get_transport
    from app.services.quickbooks_time_transport import TransportError

    org = project.organization_id
    transport = get_transport()
    if transport is None:
        link.qbt_status = PSYNC_PENDING
        link.qbt_last_error = "Waiting: QuickBooks Time is not switched on."
        return
    if link.qbt_status == PSYNC_NEEDS_CONFIRM:
        return
    name = (SHOP_JOBCODE_NAME if _is_company(project) else project_name(project))[:64]
    active = True if _is_company(project) else _active(project)
    try:
        row = _ensure_jobcode(transport, project, link, name, actor)
        if row is None:
            return
        changes = {}
        if row.get("name") != name:
            changes["name"] = name
        if bool(row.get("active", True)) != active:
            changes["active"] = active
        if changes:
            code, payload = transport.request("PUT", "jobcodes", body={"data": [{"id": int(row["id"]), **changes}]})
            item = (_jobcodes(payload) or [{}])[0]
            if code != 200 or int(item.get("_status_code") or 0) != 200:
                raise ProjectSyncError(f"QuickBooks Time did not update the job code ({item.get('_status_message') or code}).")
            _event(org, project.id, "JOBCODE_UPDATED", f"QuickBooks Time job code {row['id']}: "
                   + ", ".join(f"{k} → {v}" for k, v in changes.items()) + ".", actor=actor)
        link.qbt_jobcode_id, link.qbt_synced_name, link.qbt_synced_active = str(row["id"]), name, active
        link.qbt_status, link.qbt_last_error, link.qbt_candidates_json = PSYNC_SYNCED, None, None
        _link_jobcode(project, str(row["id"]), name, actor)
    except TransportError:
        link.qbt_status = PSYNC_SENT
        link.qbt_last_error = ("QuickBooks Time could not be reached, so it is not known whether the job code arrived. "
                               "Retry is safe: CalibraytAI looks for it by name before making one.")
        _event(org, project.id, "JOBCODE_UNKNOWN", link.qbt_last_error, actor=actor)
    except ProjectSyncError as exc:
        link.qbt_status = PSYNC_FAILED
        link.qbt_last_error = str(exc)
        _event(org, project.id, "JOBCODE_FAILED", f"{name}: {exc}", actor=actor)


def _ensure_jobcode(transport, project, link, name, actor):
    org = project.organization_id
    if link.qbt_jobcode_id:
        code, payload = transport.request("GET", "jobcodes", params={"ids": link.qbt_jobcode_id, "active": "both"})
        rows = _jobcodes(payload)
        if code != 200 or not rows:
            raise ProjectSyncError(f"QuickBooks Time no longer has job code {link.qbt_jobcode_id}.")
        return rows[0]
    if _is_company(project):
        existing = _shop_jobcode(org)
        if existing:
            code, payload = transport.request("GET", "jobcodes", params={"ids": existing, "active": "both"})
            rows = _jobcodes(payload)
            if rows:
                return rows[0]
    from_qbo = jobcodes_from_qbo() and not _is_company(project)
    code, payload = transport.request("GET", "jobcodes", params={"name": name, "active": "both"})
    found = [r for r in _jobcodes(payload)
             if r.get("name") == name and (from_qbo or int(r.get("parent_id") or 0) == 0)]
    if found and link.qbt_status == PSYNC_SENT:
        _event(org, project.id, "JOBCODE_ADOPTED", f"Job code '{name}' arrived on the earlier try ({found[0]['id']}).",
               actor=actor)
        return found[0]
    if found:
        link.qbt_status = PSYNC_NEEDS_CONFIRM
        link.qbt_candidates_json = {"what": "jobcode", "name": name,
                                    "candidates": [{"id": str(r["id"]), "name": r["name"], "active": r.get("active")}
                                                   for r in found]}
        link.qbt_last_error = (f"QuickBooks Time already has a job code '{name}'. Confirm it is this job "
                               "(Accounting → QuickBooks projects).")
        _event(org, project.id, "JOBCODE_MATCH", link.qbt_last_error, actor=actor)
        return None
    if from_qbo:
        # Intuit's QuickBooks Online ↔ QuickBooks Time integration imports customers and jobs as job codes; making
        # one here as well would give two. Wait for the import, then the office confirms it once.
        link.qbt_status = PSYNC_PENDING
        link.qbt_last_error = ("Waiting for QuickBooks Time to bring in this job from QuickBooks Online "
                               "(QBT_JOBCODES_FROM_QBO=1); checked again on the next sync.")
        return None
    link.qbt_status = PSYNC_SENT  # if the answer is lost, the retry looks for it by name first
    db.session.flush()
    code, payload = transport.request("POST", "jobcodes", body={"data": [
        {"name": name, "type": "regular", "parent_id": 0, "billable": False, "assigned_to_all": True}]})
    item = (_jobcodes(payload) or [{}])[0]
    if code != 200 or int(item.get("_status_code") or 0) != 200 or not item.get("id"):
        raise ProjectSyncError(f"QuickBooks Time did not create the job code "
                               f"({item.get('_status_extra') or item.get('_status_message') or code}).")
    _event(org, project.id, "JOBCODE_CREATED", f"Job code '{name}' created in QuickBooks Time ({item['id']}).",
           actor=actor)
    return item


def _shop_jobcode(org) -> Optional[str]:
    from app.models.payroll_time import QuickBooksTimeJobcodeLink

    row = QuickBooksTimeJobcodeLink.query.filter(QuickBooksTimeJobcodeLink.organization_id == org,
                                                 QuickBooksTimeJobcodeLink.project_work_activity_id.isnot(None)).first()
    return row.qbt_jobcode_id if row is not None else None


def _link_jobcode(project, jobcode_id, name, actor):
    """Use the existing QuickBooks Time links (approved time already reads them): the job, or every shop / company
    category to the one Shop job code."""
    from app.models.payroll_time import QuickBooksTimeJobcodeLink
    from app.models.work_structure import ProjectWorkActivity, ProjectWorkElement

    org = project.organization_id
    who = actor_label(actor)
    if _is_company(project):
        targets = [{"project_id": None, "project_work_activity_id": a.id} for a in
                   ProjectWorkActivity.query.join(ProjectWorkElement).filter(
                       ProjectWorkElement.project_id == project.id, ProjectWorkActivity.organization_id == org).all()]
    else:
        targets = [{"project_id": project.id, "project_work_activity_id": None}]
    for key in targets:
        row = QuickBooksTimeJobcodeLink.query.filter_by(organization_id=org, **key).first()
        if row is None:
            db.session.add(QuickBooksTimeJobcodeLink(organization_id=org, qbt_jobcode_id=jobcode_id,
                                                     qbt_jobcode_name=name[:160], linked_by_name=who, **key))
        elif row.qbt_jobcode_id != jobcode_id or row.qbt_jobcode_name != name:
            row.qbt_jobcode_id, row.qbt_jobcode_name = jobcode_id, name[:160]


# -------------------------------------------------------------------------------------- confirm, retry, list
def confirm_match(link: AccountingProjectLink, actor, *, system: str, record_id: str) -> AccountingProjectLink:
    """Suzanne or the owner says the existing QuickBooks record IS this customer / project / job code (once)."""
    from app.services.quickbooks_online import _save_link

    project = link.project
    org = link.organization_id
    if system == "qbo":
        data = link.qbo_candidates_json or {}
        chosen = next((c for c in data.get("candidates") or [] if c["id"] == str(record_id)), None)
        if link.qbo_status != PSYNC_NEEDS_CONFIRM or chosen is None:
            raise ProjectSyncError("Choose one of the QuickBooks records listed.")
        if data.get("what") == "customer":
            _save_link(org, actor, QBO_LINK_CUSTOMER, f"client:{data['client_id']}",
                       {"Id": chosen["id"], "DisplayName": chosen["name"]})
        else:
            link.qbo_project_id = chosen["id"]
        link.qbo_status, link.qbo_candidates_json, link.qbo_last_error = PSYNC_PENDING, None, None
    elif system == "qbt":
        data = link.qbt_candidates_json or {}
        chosen = next((c for c in data.get("candidates") or [] if c["id"] == str(record_id)), None)
        if link.qbt_status != PSYNC_NEEDS_CONFIRM or chosen is None:
            raise ProjectSyncError("Choose one of the QuickBooks Time job codes listed.")
        link.qbt_jobcode_id = chosen["id"]
        link.qbt_status, link.qbt_candidates_json, link.qbt_last_error = PSYNC_PENDING, None, None
    else:
        raise ProjectSyncError("Unknown system.")
    link.confirmed_by_name, link.confirmed_at = actor_label(actor), datetime.utcnow()
    _event(org, project.id, "MATCH_CONFIRMED", f"{actor_label(actor)} confirmed {system.upper()} record "
           f"{record_id} for {project_name(project)}.", actor=actor, detail={"system": system, "id": str(record_id)})
    db.session.commit()
    if enabled():
        sync_project(project, actor=actor)
    return link


def retry(link: AccountingProjectLink, actor) -> AccountingProjectLink:
    for prefix in ("qbo", "qbt"):
        if getattr(link, f"{prefix}_status") == PSYNC_FAILED:
            setattr(link, f"{prefix}_status", PSYNC_PENDING)
    _event(link.organization_id, link.project_id, "PROJECT_RETRY", "Retry pressed.", actor=actor)
    db.session.commit()
    if not enabled():
        raise ProjectSyncError("Project sync to QuickBooks is not switched on (QBO_PROJECT_SYNC_ENABLED).")
    return sync_project(link.project, actor=actor)


def rows(organization_id: str) -> list:
    projects = Project.query.filter_by(organization_id=organization_id).order_by(Project.id.desc()).all()
    links = {l.project_id: l for l in AccountingProjectLink.query.filter_by(organization_id=organization_id).all()}
    return [{"project": p, "link": links.get(p.id), "name": project_name(p), "company": _is_company(p)}
            for p in projects]


def problems(organization_id: str) -> list:
    return [l for l in AccountingProjectLink.query.filter_by(organization_id=organization_id).all()
            if PSYNC_FAILED in (l.qbo_status, l.qbt_status) or PSYNC_NEEDS_CONFIRM in (l.qbo_status, l.qbt_status)
            or PSYNC_SENT in (l.qbo_status, l.qbt_status)]


def project_events(organization_id: str, project_id: int, limit: int = 30) -> list:
    return (QuickBooksOnlineEvent.query.filter_by(organization_id=organization_id, project_id=project_id)
            .order_by(QuickBooksOnlineEvent.id.desc()).limit(limit).all())

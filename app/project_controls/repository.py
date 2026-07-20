"""Data access helpers for Change Orders."""

from datetime import datetime

from sqlalchemy import or_

from app import db
from app.models.project import Project
from app.project_controls.models import (
    OPEN_CHANGE_ORDER_STATUSES,
    ChangeOrder,
    ChangeOrderItem,
)


def get_change_order(change_order_id):
    return db.session.get(ChangeOrder, change_order_id)


def get_change_order_item(item_id):
    return db.session.get(ChangeOrderItem, item_id)


def list_change_orders(
    *,
    project_id=None,
    status=None,
    date_from=None,
    date_to=None,
    search=None,
):
    query = ChangeOrder.query.outerjoin(Project)

    if project_id:
        query = query.filter(ChangeOrder.project_id == project_id)
    if status:
        query = query.filter(ChangeOrder.status == status)
    if date_from:
        query = query.filter(ChangeOrder.updated_at >= date_from)
    if date_to:
        query = query.filter(ChangeOrder.updated_at <= date_to)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ChangeOrder.number.ilike(term),
                ChangeOrder.title.ilike(term),
                ChangeOrder.description.ilike(term),
                Project.name.ilike(term),
            )
        )

    return query.order_by(ChangeOrder.updated_at.desc()).all()


def list_change_orders_for_project(project_id):
    return (
        ChangeOrder.query.filter_by(project_id=project_id)
        .order_by(ChangeOrder.updated_at.desc())
        .all()
    )


def count_open_change_orders():
    return ChangeOrder.query.filter(
        ChangeOrder.status.in_(OPEN_CHANGE_ORDER_STATUSES)
    ).count()


def count_pending_approval():
    return ChangeOrder.query.filter_by(status="Pending Approval").count()


def count_approved_this_month(now=None):
    now = now or datetime.utcnow()
    start = datetime(now.year, now.month, 1).date()
    return ChangeOrder.query.filter(
        ChangeOrder.status == "Approved",
        ChangeOrder.approved_date.isnot(None),
        ChangeOrder.approved_date >= start,
    ).count()


def sum_change_order_value(statuses=None):
    query = db.session.query(db.func.coalesce(db.func.sum(ChangeOrder.total), 0))
    if statuses:
        query = query.filter(ChangeOrder.status.in_(statuses))
    return query.scalar() or 0


def next_change_order_number():
    latest = (
        ChangeOrder.query.order_by(ChangeOrder.id.desc())
        .with_entities(ChangeOrder.number)
        .first()
    )
    if not latest:
        return "CO-000001"
    number = latest[0]
    try:
        seq = int(str(number).split("-")[-1])
    except (TypeError, ValueError):
        seq = ChangeOrder.query.count()
    return f"CO-{seq + 1:06d}"


def add_change_order(change_order):
    db.session.add(change_order)
    return change_order


def delete_change_order_item(item):
    db.session.delete(item)

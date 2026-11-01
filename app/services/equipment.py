"""The equipment register: add, change, retire and restore, every change written to the insert-only history."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.equipment import (
    EQUIPMENT_ACTIVE,
    EQUIPMENT_CATEGORY_LABELS,
    EQUIPMENT_RETIRED,
    OrganizationEquipment,
    OrganizationEquipmentEvent,
)

EDITABLE = ("name", "category", "unit_number", "make", "model", "serial_number", "plate_or_registration", "year",
            "purchased_on", "notes")
LIMITS = {"name": 160, "unit_number": 40, "make": 80, "model": 80, "serial_number": 80, "plate_or_registration": 40,
          "notes": 5000}


class EquipmentError(ValueError):
    pass


def _actor(user):
    return (int(user.id) if user is not None else None,
            ((getattr(user, "display_name", None) or getattr(user, "email", None) or "Unknown")[:150]
             if user is not None else "Calibrayt"))


def clean_fields(form) -> dict:
    out = {}
    for key in EDITABLE:
        raw = (form.get(key) or "").strip()
        if key == "year":
            if raw:
                try:
                    out[key] = int(raw)
                except ValueError as exc:
                    raise EquipmentError("Year must be a number like 2021.") from exc
                if not 1900 <= out[key] <= 2100:
                    raise EquipmentError("Year must be between 1900 and 2100.")
            else:
                out[key] = None
        elif key == "purchased_on":
            try:
                out[key] = date.fromisoformat(raw) if raw else None
            except ValueError as exc:
                raise EquipmentError("Enter the purchase date as a date.") from exc
        elif key == "category":
            out[key] = raw if raw in EQUIPMENT_CATEGORY_LABELS else "OTHER"
        else:
            out[key] = raw[:LIMITS[key]] or None
    if not out.get("name"):
        raise EquipmentError("Give the equipment a name, like \"Truck 3\" or \"Kubota KX040\".")
    return out


def _event(item, user, event_type, field=None, previous=None, new=None):
    uid, name = _actor(user)
    db.session.add(OrganizationEquipmentEvent(organization_id=item.organization_id, equipment_id=item.id,
                                              event_type=event_type, field_name=field,
                                              previous_value=None if previous is None else str(previous),
                                              new_value=None if new is None else str(new), actor_user_id=uid,
                                              actor_name=name, at=datetime.utcnow()))


def create_equipment(organization_id, user, fields) -> OrganizationEquipment:
    uid, _ = _actor(user)
    item = OrganizationEquipment(organization_id=organization_id, status=EQUIPMENT_ACTIVE, created_by_user_id=uid,
                                 updated_by_user_id=uid, created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
                                 **fields)
    db.session.add(item)
    try:
        db.session.flush()
    except IntegrityError as exc:
        db.session.rollback()
        raise EquipmentError("Another item already has that unit number.") from exc
    _event(item, user, "CREATED", new=item.name)
    db.session.commit()
    return item


def update_equipment(item, user, fields) -> int:
    changed = 0
    for key, value in fields.items():
        previous = getattr(item, key)
        if previous != value:
            setattr(item, key, value)
            _event(item, user, "UPDATED", key, previous, value)
            changed += 1
    if changed:
        item.updated_at = datetime.utcnow()
        item.updated_by_user_id = _actor(user)[0]
        try:
            db.session.flush()
        except IntegrityError as exc:
            db.session.rollback()
            raise EquipmentError("Another item already has that unit number.") from exc
    db.session.commit()
    return changed


def set_retired(item, user, retired: bool) -> None:
    target = EQUIPMENT_RETIRED if retired else EQUIPMENT_ACTIVE
    if item.status == target:
        return
    item.status = target
    item.updated_at = datetime.utcnow()
    _event(item, user, "RETIRED" if retired else "RESTORED")
    db.session.commit()


def history(item) -> list:
    return (OrganizationEquipmentEvent.query.filter_by(equipment_id=item.id, organization_id=item.organization_id)
            .order_by(OrganizationEquipmentEvent.at.desc(), OrganizationEquipmentEvent.id.desc()).all())

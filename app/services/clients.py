"""Customers (Clients): create and update with a structured address (Project Creation UX, 27 Oct 2026).

One place for the customer rules, used by the Clients pages and by Start a New Project, so the wizard never has a
second way of making a customer:

* Only the name is required. Email, phone and address may be added later; what is missing is listed on
  WHAT NEEDS MY ATTENTION? (app/services/needs_attention.py) until it is filled in.
* The address is kept as structured fields (street, unit, city, province or state, postal code, country). The
  one-line ``address`` the rest of the platform reads is composed from them. A customer saved before the structured
  fields existed keeps the address exactly as it was typed until someone fills the fields in: nothing is parsed or
  guessed.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from app import db
from app.models import Client

CANADA = "Canada"
UNITED_STATES = "United States"
COUNTRIES = (CANADA, UNITED_STATES)
PROVINCES = ("Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador",
             "Northwest Territories", "Nova Scotia", "Nunavut", "Ontario", "Prince Edward Island", "Quebec",
             "Saskatchewan", "Yukon")
STATES = ("Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
          "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas",
          "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
          "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York",
          "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
          "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
          "West Virginia", "Wisconsin", "Wyoming")
REGIONS = {CANADA: PROVINCES, UNITED_STATES: STATES}
DEFAULT_COUNTRY = CANADA
DEFAULT_PROVINCE = "Ontario"

ADDRESS_FIELDS = ("street_address", "unit", "city", "province_state", "postal_code", "country")
TEXT_FIELDS = ("name", "company", "email", "phone", "notes")
FIELDS = TEXT_FIELDS + ADDRESS_FIELDS + ("address",)
LIMITS = {"name": 150, "company": 150, "email": 150, "phone": 50, "address": 255, "street_address": 255, "unit": 60,
          "city": 160, "province_state": 120, "postal_code": 20, "country": 120}
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CA_POSTAL = re.compile(r"^([A-Za-z]\d[A-Za-z])\s*-?\s*(\d[A-Za-z]\d)$")


class ClientError(ValueError):
    """A customer that cannot be saved; the message is for the person."""


def _clean(field: str, value) -> str:
    text = str(value or "")
    if field != "notes":
        text = " ".join(text.split())
    return text.strip()[: LIMITS.get(field, 10000)]


def fields_from_form(form) -> Dict[str, str]:
    return {field: _clean(field, form.get(field, "")) for field in FIELDS}


def stored_fields(client: Optional[Client]) -> Dict[str, str]:
    if client is None:
        return {field: "" for field in FIELDS}
    return {field: (getattr(client, field) or "").strip() for field in FIELDS}


def has_structured_address(values) -> bool:
    get = values.get if isinstance(values, dict) else (lambda k: getattr(values, k, None))
    return any((get(k) or "").strip() for k in ("street_address", "unit", "city", "postal_code"))


def normalize_postal(code: str, country: str) -> str:
    text = (code or "").strip().upper()
    match = _CA_POSTAL.match(text)
    if match and (country or CANADA) == CANADA:
        return f"{match.group(1)} {match.group(2)}"
    return text


def compose_address(values: Dict[str, str]) -> str:
    """'12 Main Street, Unit 4, Merrickville, Ontario K0G 1N0, Canada' from the structured fields."""
    street = values.get("street_address") or ""
    unit = values.get("unit") or ""
    if unit and street:
        unit_text = unit if re.match(r"(?i)^(unit|suite|apt|apartment|#)", unit) else f"Unit {unit}"
        street = f"{street}, {unit_text}"
    region = " ".join(x for x in (values.get("province_state") or "", values.get("postal_code") or "") if x)
    parts = [street, values.get("city") or "", region, values.get("country") or ""]
    return ", ".join(p for p in parts if p)[:255]


def _validate(values: Dict[str, str]) -> Dict[str, str]:
    if not values.get("name"):
        raise ClientError("Client name is required.")
    if values.get("email") and not _EMAIL.match(values["email"]):
        raise ClientError("That email address does not look right. Check it, or leave it empty and add it later.")
    country = values.get("country") or ""
    if has_structured_address(values):
        country = country or DEFAULT_COUNTRY
        values["country"] = country
        region = values.get("province_state") or ""
        if region and country in REGIONS and region not in REGIONS[country]:
            raise ClientError(f"Choose the {'province' if country == CANADA else 'state'} from the list.")
        values["postal_code"] = normalize_postal(values.get("postal_code", ""), country)
    elif not values.get("province_state"):
        values["country"] = ""  # a country on its own is not an address
    return values


def _apply(client: Client, values: Dict[str, str]) -> None:
    for field in TEXT_FIELDS:
        setattr(client, field, values.get(field, ""))
    if has_structured_address(values):
        for field in ADDRESS_FIELDS:
            setattr(client, field, values.get(field) or None)
        client.address = compose_address(values)
    else:
        # No structured address entered: the one-line address stays as typed (older customers keep theirs).
        for field in ADDRESS_FIELDS:
            setattr(client, field, None)
        client.address = values.get("address", "")


def create_client(organization_id: str, form_or_values, *, commit: bool = True) -> Client:
    """Create one customer of this company and return it (its id is the exact record created)."""
    values = form_or_values if isinstance(form_or_values, dict) else fields_from_form(form_or_values)
    values = _validate({field: _clean(field, values.get(field, "")) for field in FIELDS})
    client = Client(organization_id=organization_id)
    _apply(client, values)
    db.session.add(client)
    db.session.flush()
    if commit:
        db.session.commit()
    return client


def update_client(client: Client, form_or_values, *, commit: bool = True) -> Client:
    values = form_or_values if isinstance(form_or_values, dict) else fields_from_form(form_or_values)
    values = _validate({field: _clean(field, values.get(field, "")) for field in FIELDS})
    _apply(client, values)
    if commit:
        db.session.commit()
    return client


def missing_information(client: Client) -> List[str]:
    """What a customer record still lacks for the job: email, phone and an address."""
    missing = []
    if not (client.email or "").strip():
        missing.append("Email")
    if not (client.phone or "").strip():
        missing.append("Phone")
    if not (client.address or "").strip() and not has_structured_address(client):
        missing.append("Address")
    return missing


def location_values(client: Optional[Client]) -> Dict[str, str]:
    """The customer's address as job-location fields ("Same as customer address")."""
    if client is None:
        return {}
    if has_structured_address(client):
        street = client.street_address or ""
        if client.unit:
            street = f"{street}, {client.unit}" if street else client.unit
        return {"street": street, "municipality": client.city or "", "province_state": client.province_state or "",
                "postal_zip": client.postal_code or "", "country": client.country or DEFAULT_COUNTRY, "address": ""}
    return {"street": "", "municipality": "", "province_state": "", "postal_zip": "", "country": "",
            "address": client.address or ""}


def form_options() -> Dict:
    """What the customer fields partial needs (clients/_fields.html)."""
    return {"regions": REGIONS, "countries": COUNTRIES, "default_country": DEFAULT_COUNTRY,
            "default_province": DEFAULT_PROVINCE}

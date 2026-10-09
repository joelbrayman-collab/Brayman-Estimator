"""Versioned ICF manufacturer profiles.

This module stores source-attributed product facts. It does not calculate
quantities, labour, or price, and it does not write a project or an estimate.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

FIELD_STATUSES = ("VERIFIED_FROM_SOURCE", "NOT_ESTABLISHED", "NOT_APPLICABLE")
CALCULATION_NOT_SELECTED = "not_selected"
_CORE_TOKEN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?$")
_APPROVAL_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_APPROVAL_FIELDS = (
    "approval_id",
    "manufacturer_id",
    "product_family",
    "record_id",
    "observation_id",
    "core_size_in",
    "component_type",
    "measurement_type",
    "value",
    "unit",
    "source_document",
    "source_url",
    "decision",
    "approver",
    "approval_date",
    "destination_unit",
)
# A published measurement may fill one engine field only when the meaning matches.
_FACTOR_DESTINATIONS = {
    ("concrete_volume", "yd3"): "concrete_volume_yd3",
    ("concrete_cavity_width", "ft"): "concrete_cavity_width_ft",
    ("wall_coverage", "ft2"): "wall_coverage_ft2",
}
ENGINE_STANDARD_FIELDS = (
    "length_in",
    "height_in",
    "wall_coverage_ft2",
    "concrete_volume_yd3",
)
_DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "icf_manufacturer_profiles_v1.json"
)


class IcfProfileError(LookupError):
    """The requested manufacturer profile is not in the registry."""


def profiles_are_organization_scoped():
    return False


def load_registry():
    with _DATA_PATH.open(encoding="utf-8") as handle:
        registry = json.load(handle)
    _validate_registry(registry)
    return registry


def list_profiles(version="1"):
    registry = load_registry()
    _require_version(registry, version)
    profiles = registry["profiles"][version]
    return tuple(profiles[key] for key in sorted(profiles))


def get_profile(manufacturer_id, version="1"):
    registry = load_registry()
    _require_version(registry, version)
    profiles = registry["profiles"][version]
    if manufacturer_id not in profiles:
        raise IcfProfileError(
            "No ICF manufacturer profile exists for {0} version {1}.".format(
                manufacturer_id, version
            )
        )
    return profiles[manufacturer_id]


def missing_engine_fields(profile, unit_code="standard_8"):
    """Name the 8-inch standard facts a future engine still cannot use."""
    unit = profile.get("units", {}).get(unit_code, {})
    missing = []
    for field_name in ENGINE_STANDARD_FIELDS:
        field = unit.get(field_name)
        if not isinstance(field, dict) or field.get("status") != "VERIFIED_FROM_SOURCE":
            missing.append("{0}.{1}".format(unit_code, field_name))
    return tuple(missing)


def engine_profile_view(manufacturer_id, version="1"):
    """Return verified unit facts and the explicit gaps.

    Product records are evidence. This view does not read them and does not
    calculate.
    """
    profile = get_profile(manufacturer_id, version=version)
    verified = {}
    _collect_verified(profile.get("units", {}), verified)
    return {
        "manufacturer_id": profile["manufacturer_id"],
        "product_system_name": profile["product_system_name"],
        "profile_version": profile["profile_version"],
        "verified": verified,
        "missing": missing_engine_fields(profile),
    }


def _require_version(registry, version):
    if version not in registry["profiles"]:
        raise IcfProfileError(
            "ICF manufacturer profile version {0} is not established.".format(version)
        )


def _validate_registry(registry):
    if registry.get("scope") != "platform_reference":
        raise IcfProfileError("ICF profiles must stay platform reference data.")
    for version, profiles in registry["profiles"].items():
        for manufacturer_id, profile in profiles.items():
            if profile.get("manufacturer_id") != manufacturer_id:
                raise IcfProfileError("Profile identity does not match its key.")
            if profile.get("profile_version") != version:
                raise IcfProfileError("Profile version does not match the registry.")
            if "organization_id" in profile:
                raise IcfProfileError("ICF profiles are not organization records.")
            _validate_fields(profile)
            _validate_product_records(profile)
            _validate_factor_approvals(profile)


def _exact_core_token(value):
    """True for a positive inch token such as 8 or 6.25."""
    if not isinstance(value, str) or _CORE_TOKEN.fullmatch(value) is None:
        return False
    whole, _, fraction = value.partition(".")
    return whole != "0" or bool(fraction)


def _validate_product_records(profile):
    """Evidence may disagree. It is not a calculation factor."""
    records = profile.get("product_records")
    if records is None:
        return
    if not isinstance(records, dict):
        raise IcfProfileError("Product records must be an object.")
    manufacturer_id = profile.get("manufacturer_id")
    for record_id, record in records.items():
        if not isinstance(record, dict):
            raise IcfProfileError("A product record must be an object.")
        if record.get("record_id") != record_id:
            raise IcfProfileError("Product record identity does not match its key.")
        if record.get("manufacturer_id") != manufacturer_id:
            raise IcfProfileError("A product record does not match its manufacturer.")
        if not _text(record.get("product_family")):
            raise IcfProfileError("A product record has no product family.")
        code = record.get("product_code")
        if not isinstance(code, dict) or "status" not in code:
            raise IcfProfileError("A product code has no governed status.")
        if not _exact_core_token(record.get("core_size_in")):
            raise IcfProfileError("A product record core size must be an exact decimal.")
        if not _text(record.get("component_type")) or not _text(record.get("variant")):
            raise IcfProfileError("A product record is missing its component identity.")
        observations = record.get("observations")
        if not isinstance(observations, dict) or not observations:
            raise IcfProfileError("A product record has no observations.")
        for observation_id, observation in observations.items():
            _validate_observation(observation_id, observation)


def _validate_observation(observation_id, observation):
    if not isinstance(observation, dict):
        raise IcfProfileError("An observation must be an object.")
    if observation.get("observation_id") != observation_id:
        raise IcfProfileError("Observation identity does not match its key.")
    if not _text(observation.get("measurement_type")) or not _text(observation.get("unit")):
        raise IcfProfileError("An observation has no measurement identity.")
    if observation.get("status") not in FIELD_STATUSES:
        raise IcfProfileError("An observation has no governed status.")
    if observation.get("calculation_selection") != CALCULATION_NOT_SELECTED:
        raise IcfProfileError("An observation is not an unselected evidence record.")
    revision = observation.get("source_revision", "missing")
    if revision == "missing" or (revision not in (None, "") and not isinstance(revision, str)):
        raise IcfProfileError("A source revision must be text when it is known.")
    if isinstance(revision, str) and not revision.strip():
        raise IcfProfileError("A source revision must be text when it is known.")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_factor_approval(profile, approval):
    """Check one candidate approval. Do not select an observation or write a unit."""
    if not isinstance(profile, dict) or not isinstance(approval, dict):
        raise IcfProfileError("A factor approval must name a profile and an approval.")
    for key in _APPROVAL_FIELDS:
        if not _text(approval.get(key)):
            raise IcfProfileError("A factor approval is missing {0}.".format(key))
    if approval["decision"] != "approved":
        raise IcfProfileError("A factor approval has no explicit approval decision.")
    if _APPROVAL_DATE.fullmatch(approval["approval_date"]) is None:
        raise IcfProfileError("A factor approval date must be YYYY-MM-DD.")
    if not _text(approval.get("approver")):
        raise IcfProfileError("A factor approval has no authority.")
    if profile.get("manufacturer_id") != approval["manufacturer_id"]:
        raise IcfProfileError("A factor approval does not match its manufacturer.")
    record = (profile.get("product_records") or {}).get(approval["record_id"])
    if not isinstance(record, dict):
        raise IcfProfileError("A factor approval names a missing product record.")
    if record.get("manufacturer_id") != approval["manufacturer_id"]:
        raise IcfProfileError("A factor approval does not match its manufacturer.")
    if record.get("product_family") != approval["product_family"]:
        raise IcfProfileError("A factor approval does not match its product family.")
    if record.get("core_size_in") != approval["core_size_in"]:
        raise IcfProfileError("A factor approval does not match its core.")
    if record.get("component_type") != approval["component_type"]:
        raise IcfProfileError("A factor approval does not match its component.")
    _require_product_identity(profile, record)
    supersedes = approval.get("supersedes")
    if supersedes is not None and not _text(supersedes):
        raise IcfProfileError("A factor approval must name the earlier approval it supersedes.")
    if _text(supersedes) and supersedes == approval["approval_id"]:
        raise IcfProfileError("A factor approval cannot supersede itself.")
    observation = (record.get("observations") or {}).get(approval["observation_id"])
    if not isinstance(observation, dict):
        raise IcfProfileError("A factor approval names a missing observation.")
    if observation.get("measurement_type") != approval["measurement_type"]:
        raise IcfProfileError("A factor approval does not match its measurement.")
    if observation.get("unit") != approval["unit"]:
        raise IcfProfileError("A factor approval does not match its unit.")
    if observation.get("value") != approval["value"]:
        raise IcfProfileError("A factor approval does not match the published value.")
    if observation.get("status") != "VERIFIED_FROM_SOURCE":
        raise IcfProfileError("Publication status alone is not a factor approval.")
    if not _text(observation.get("source_document")) or not _text(observation.get("source_url")):
        raise IcfProfileError("A factor approval is missing source provenance.")
    if (
        approval["source_document"] != observation["source_document"]
        or approval["source_url"] != observation["source_url"]
    ):
        raise IcfProfileError("A factor approval does not match its source.")
    expected = _FACTOR_DESTINATIONS.get((approval["measurement_type"], approval["unit"]))
    if expected is None or approval["destination_unit"] != expected:
        raise IcfProfileError("A factor approval destination does not match its measurement.")
    if _conflicting_observations(profile, record, observation):
        raise IcfProfileError("A factor approval is blocked by a conflicting observation.")
    checked = {key: approval[key] for key in _APPROVAL_FIELDS}
    checked["supersedes"] = supersedes if _text(supersedes) else None
    return checked


def _validate_factor_approvals(profile):
    """An empty list is valid. A stored approval must still pass the gate."""
    approvals = profile.get("factor_approvals", "missing")
    if not isinstance(approvals, list):
        raise IcfProfileError("Factor approvals must be a list.")
    seen = []
    for approval in approvals:
        checked = validate_factor_approval(profile, approval)
        if checked["approval_id"] in seen:
            raise IcfProfileError("A factor approval identity is duplicated.")
        seen.append(checked["approval_id"])
    known = set(seen)
    superseded = set()
    for approval in approvals:
        prior = approval.get("supersedes")
        if prior is None:
            continue
        if prior not in known:
            raise IcfProfileError(
                "A factor approval must keep the earlier approval it supersedes."
            )
        superseded.add(prior)
    current = []
    for approval in approvals:
        if approval.get("approval_id") in superseded:
            continue
        current.append((approval.get("record_id"), approval.get("observation_id")))
    if len(current) != len(set(current)):
        raise IcfProfileError(
            "A current factor approval already exists for that observation."
        )


def _require_product_identity(profile, record):
    """A verified code identifies a product. An unpublished code needs one clear record."""
    if _established_product_code(record) is not None:
        return
    code = record.get("product_code") or {}
    identified = (
        _text(record.get("manufacturer_id"))
        and _text(record.get("product_family"))
        and _exact_core_token(record.get("core_size_in"))
        and _text(record.get("component_type"))
        and _text(code.get("source_document"))
        and _text(code.get("source_url"))
    )
    matches = _records_for_same_component(profile, record)
    if not identified or len(matches) != 1:
        raise IcfProfileError("Ambiguous product identity blocks factor approval.")


def _records_for_same_component(profile, record):
    found = []
    for other in (profile.get("product_records") or {}).values():
        if not isinstance(other, dict):
            continue
        if other.get("manufacturer_id") != record.get("manufacturer_id"):
            continue
        if other.get("product_family") != record.get("product_family"):
            continue
        if other.get("core_size_in") != record.get("core_size_in"):
            continue
        if other.get("component_type") != record.get("component_type"):
            continue
        found.append(other.get("record_id"))
    return tuple(found)


def _established_product_code(record):
    code = record.get("product_code") or {}
    if code.get("status") != "VERIFIED_FROM_SOURCE" or not _text(code.get("value")):
        return None
    return code["value"]


def _same_product(left, right):
    """Verified codes must match. Unpublished records match only their own component slot."""
    left_code = _established_product_code(left)
    right_code = _established_product_code(right)
    if left_code is not None or right_code is not None:
        if left_code != right_code:
            return False
    return (
        left.get("product_family") == right.get("product_family")
        and left.get("core_size_in") == right.get("core_size_in")
        and left.get("component_type") == right.get("component_type")
    )


def _conflicting_observations(profile, record, observation):
    """Different values conflict only for the same product and measurement."""
    found = []
    for other in (profile.get("product_records") or {}).values():
        if not isinstance(other, dict) or not _same_product(record, other):
            continue
        for item in (other.get("observations") or {}).values():
            if not isinstance(item, dict):
                continue
            if item.get("observation_id") == observation.get("observation_id"):
                continue
            if item.get("measurement_type") != observation.get("measurement_type"):
                continue
            if item.get("unit") != observation.get("unit"):
                continue
            if item.get("value") != observation.get("value"):
                found.append(item.get("observation_id"))
    return tuple(found)


def _validate_fields(value):
    if isinstance(value, dict) and "status" in value:
        if value["status"] not in FIELD_STATUSES:
            raise IcfProfileError("A profile field has no governed status.")
        if value["status"] == "VERIFIED_FROM_SOURCE":
            if value.get("value") in (None, ""):
                raise IcfProfileError("A verified profile field has no value.")
            if not value.get("source_document") or not value.get("source_url"):
                raise IcfProfileError("A verified profile field has no source.")
        if value["status"] == "NOT_ESTABLISHED" and value.get("value") not in (None, ""):
            raise IcfProfileError("An unverified profile field must not carry a value.")
        return
    if isinstance(value, dict):
        for item in value.values():
            _validate_fields(item)
    elif isinstance(value, list):
        for item in value:
            _validate_fields(item)


def _collect_verified(value, found, prefix=""):
    if isinstance(value, dict) and value.get("status") == "VERIFIED_FROM_SOURCE":
        found[prefix] = value["value"]
        return
    if isinstance(value, dict) and "status" in value:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            path = "{0}.{1}".format(prefix, key) if prefix else key
            _collect_verified(item, found, path)

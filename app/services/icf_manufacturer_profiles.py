"""Versioned ICF manufacturer profiles.

This module stores source-attributed product facts. It does not calculate
quantities, labour, or price, and it does not write a project or an estimate.
"""

from __future__ import annotations

import json
from pathlib import Path

FIELD_STATUSES = ("VERIFIED_FROM_SOURCE", "NOT_ESTABLISHED", "NOT_APPLICABLE")
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
    """Return verified facts and the explicit gaps. This does not calculate."""
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

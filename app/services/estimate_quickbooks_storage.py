"""Private filesystem custody for issued QuickBooks-ready PDFs (FG-032)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from flask import current_app

_ORG_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]{1,50}$")
_SHA_RE = re.compile(r"^[a-f0-9]{64}$")
_KIND_TO_FILENAME = {
    "sales": "sales.pdf",
    "cost_class": "cost-class.pdf",
}


class QuickBooksPackageStorageError(ValueError):
    """Raised when QuickBooks package PDF bytes or a storage path cannot be accepted."""


def get_quickbooks_package_root() -> Path:
    root = current_app.config.get("QUICKBOOKS_PACKAGE_ROOT")
    if root:
        path = Path(root)
    else:
        path = Path(current_app.instance_path) / "quickbooks_packages"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def storage_key(organization_id: str, package_id: int, kind: str) -> str:
    if not _ORG_SEGMENT_RE.match(organization_id or ""):
        raise QuickBooksPackageStorageError("Invalid organization storage segment.")
    if kind not in _KIND_TO_FILENAME:
        raise QuickBooksPackageStorageError("Unknown QuickBooks artifact kind.")
    if int(package_id) <= 0:
        raise QuickBooksPackageStorageError("Invalid package identity.")
    return f"{organization_id}/{int(package_id)}/{_KIND_TO_FILENAME[kind]}"


def resolve_storage_key(key: str) -> Path:
    if not key or ".." in key or key.startswith("/"):
        raise QuickBooksPackageStorageError("Invalid storage key.")
    parts = key.split("/")
    if len(parts) != 3:
        raise QuickBooksPackageStorageError("Invalid storage key.")
    org_id, package_id, filename = parts
    if not _ORG_SEGMENT_RE.match(org_id):
        raise QuickBooksPackageStorageError("Invalid organization storage segment.")
    if not package_id.isdigit():
        raise QuickBooksPackageStorageError("Invalid package identity.")
    if filename not in _KIND_TO_FILENAME.values():
        raise QuickBooksPackageStorageError("Unknown QuickBooks artifact filename.")
    root = get_quickbooks_package_root().resolve()
    path = (root / org_id / package_id / filename).resolve()
    if root not in path.parents:
        raise QuickBooksPackageStorageError("Storage path escaped custody root.")
    return path


def write_issued_pdf(*, organization_id: str, package_id: int, kind: str, data: bytes) -> tuple[str, str]:
    if not data:
        raise QuickBooksPackageStorageError("PDF bytes are required.")
    digest = sha256_hex(data)
    if not _SHA_RE.match(digest):
        raise QuickBooksPackageStorageError("SHA-256 digest is invalid.")
    key = storage_key(organization_id, package_id, kind)
    path = resolve_storage_key(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if sha256_hex(path.read_bytes()) == digest:
            return key, digest
        raise QuickBooksPackageStorageError("Issued QuickBooks artifact already exists.")
    path.write_bytes(data)
    return key, digest


def read_issued_pdf(key: str) -> bytes:
    path = resolve_storage_key(key)
    if not path.is_file():
        raise QuickBooksPackageStorageError("QuickBooks artifact is not stored.")
    return path.read_bytes()

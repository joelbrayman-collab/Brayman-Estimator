"""Private filesystem custody for takeoff product facts, issued supplier
requests, and supplier responses.

Every record is written once. A later record is a new file. Nothing is
overwritten, so earlier facts, requests, and supplier prices stay
available. No database table is added.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from flask import current_app

_SEGMENT = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class TakeoffStorageError(ValueError):
    pass


def root() -> Path:
    configured = current_app.config.get("DECK_TAKEOFF_ROOT")
    path = Path(configured) if configured else Path(current_app.instance_path) / "deck_takeoff"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _project_dir(organization_id: str, project_id: int, kind: str) -> Path:
    if not _SEGMENT.match(str(organization_id or "")):
        raise TakeoffStorageError("Invalid organization storage segment.")
    if int(project_id) <= 0:
        raise TakeoffStorageError("Invalid project identity.")
    if kind not in ("product_facts", "requests", "responses"):
        raise TakeoffStorageError("Unknown takeoff record kind.")
    path = root() / organization_id / str(int(project_id)) / kind
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_once(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() == data:
            return
        raise TakeoffStorageError("A stored takeoff record cannot be overwritten.")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, indent=1, default=str).encode("utf-8")


# Product facts -------------------------------------------------------------


def save_product_facts(organization_id: str, project_id: int, record: dict) -> dict:
    folder = _project_dir(organization_id, project_id, "product_facts")
    number = len(list(folder.glob("*.json"))) + 1
    stored = dict(record)
    stored["version"] = number
    _write_once(folder / f"{number:04d}.json", _json_bytes(stored))
    return stored


def current_product_facts(organization_id: str, project_id: int) -> Optional[dict]:
    folder = _project_dir(organization_id, project_id, "product_facts")
    files = sorted(folder.glob("*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text("utf-8"))


# Issued requests -----------------------------------------------------------


def _check_id(identifier: str) -> str:
    if not _SEGMENT.match(identifier or ""):
        raise TakeoffStorageError("Invalid record identity.")
    return identifier


def save_request(organization_id: str, project_id: int, manifest: dict, pdf: bytes) -> None:
    folder = _project_dir(organization_id, project_id, "requests")
    rid = _check_id(manifest["request_id"])
    existing = folder / f"{rid}.json"
    if existing.exists():
        return
    _write_once(folder / f"{rid}.pdf", pdf)
    _write_once(existing, _json_bytes(manifest))


def load_request(organization_id: str, project_id: int, request_id: str) -> Optional[dict]:
    folder = _project_dir(organization_id, project_id, "requests")
    path = folder / f"{_check_id(request_id)}.json"
    if not path.exists():
        return None
    manifest = json.loads(path.read_text("utf-8"))
    if manifest.get("organization_id") != organization_id or int(manifest.get("project_id")) != int(project_id):
        return None
    return manifest


def request_pdf(organization_id: str, project_id: int, request_id: str) -> Optional[bytes]:
    folder = _project_dir(organization_id, project_id, "requests")
    path = folder / f"{_check_id(request_id)}.pdf"
    return path.read_bytes() if path.exists() else None


def list_requests(organization_id: str, project_id: int) -> List[dict]:
    folder = _project_dir(organization_id, project_id, "requests")
    items = [json.loads(p.read_text("utf-8")) for p in folder.glob("*.json")]
    return sorted(items, key=lambda m: m.get("issued_at", ""), reverse=True)


# Supplier responses --------------------------------------------------------


def save_response(organization_id: str, project_id: int, record: dict, pdf: Optional[bytes]) -> dict:
    folder = _project_dir(organization_id, project_id, "responses")
    number = len(list(folder.glob("*.json"))) + 1
    response_id = f"RSP-{int(project_id)}-{number:04d}"
    stored = dict(record)
    stored["response_id"] = response_id
    if pdf is not None:
        _write_once(folder / f"{response_id}.pdf", pdf)
    _write_once(folder / f"{response_id}.json", _json_bytes(stored))
    return stored


def load_response(organization_id: str, project_id: int, response_id: str) -> Optional[dict]:
    folder = _project_dir(organization_id, project_id, "responses")
    path = folder / f"{_check_id(response_id)}.json"
    if not path.exists():
        return None
    record = json.loads(path.read_text("utf-8"))
    if record.get("organization_id") != organization_id or int(record.get("project_id")) != int(project_id):
        return None
    return record


def list_responses(organization_id: str, project_id: int) -> List[dict]:
    folder = _project_dir(organization_id, project_id, "responses")
    items = [json.loads(p.read_text("utf-8")) for p in folder.glob("*.json")]
    return sorted(items, key=lambda r: r.get("response_id", ""), reverse=True)

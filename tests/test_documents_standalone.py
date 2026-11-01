"""Calibrayt's documents feature is standalone: no AiRIA import, configuration, host or network call.

1. Import boundary (AST): no file under app/, migrations/, tools/ or tests/ imports an AiRIA root package.
2. The new document modules import only app.*, the standard library and locked third-party packages.
3. No AiRIA configuration key, host or URL in app/ or the requirements.
4. With sockets blocked, the whole documents flow works: upload, classify, extract, dates, search, attention,
   connect existing records, download.
Synthetic data only.
"""

from __future__ import annotations

import ast
import importlib.util
import io
import re
import socket
import sys
import sysconfig
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# AiRIA's top-level packages (frozen from the read-only reference copy, 31 Oct 2026). Generic names that are
# also ordinary words in any project (tests, scripts, config, data, docs, static, templates, fixtures) are left out.
AIRIA_ROOTS = frozenset({
    "airiadocs", "airiadocs_web", "airia_calendar", "office_dms", "case_files_dms", "case_evidence_links",
    "case_facts", "case_proof_report", "case_intake", "identity", "security", "shell", "review_preview",
    "practice_workspaces", "practice_checklist", "universal_find", "discovery_generation", "discovery_inbound",
    "discovery_package", "discovery_research", "discovery_triage", "discovery_workspace", "element_proof_discovery",
    "evidence_world", "matter_workspace", "matter_membership", "chronology", "contradiction", "count_verdicts",
    "depositions", "litigation", "legal_eval", "legal_knowledge", "pleading_engine", "research_elements",
    "research_reports", "semantic_models", "semantic_runtime", "source_backfill", "source_matter_links",
    "source_viewers", "governed_model", "guided_workflows", "knowledge_base", "erm", "orentis", "local_ocr",
    "speech_worker", "search_benchmark", "engine_audit", "export_validation", "lawyer_acceptance_fixture",
    "uat_telemetry", "uat_fixtures", "background_jobs", "citation_ref", "lifecycle_observability",
    "sqlite_lifecycle", "release_gate", "package_export", "weekly_digest", "build_index", "migrate_originals",
})
DOCUMENT_MODULES = [
    "app/models/documents.py", "app/models/equipment.py", "app/services/document_storage.py",
    "app/services/equipment.py", "app/routes/documents.py", "app/routes/equipment.py", "app/cli/documents.py",
    *sorted(str(p.relative_to(REPO)) for p in (REPO / "app/services/documents").glob("*.py")),
]
ALLOWED_THIRD_PARTY = {"flask", "flask_login", "sqlalchemy", "werkzeug", "markupsafe", "pypdf", "docx", "click"}


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0]


def test_no_airia_package_is_imported_anywhere():
    offenders = []
    for folder in ("app", "migrations", "tools", "tests"):
        for path in (REPO / folder).rglob("*.py"):
            for root in _imports(path):
                if root in AIRIA_ROOTS:
                    offenders.append(f"{path.relative_to(REPO)}: {root}")
    assert offenders == []


def _is_stdlib(root: str) -> bool:
    """True when `root` is a standard-library module. sys.stdlib_module_names only exists from Python 3.10;
    production and the office Mac run 3.9.6, so the answer comes from where the module is installed."""
    names = getattr(sys, "stdlib_module_names", None)
    if names is not None:
        return root in names
    if root in sys.builtin_module_names:
        return True
    spec = importlib.util.find_spec(root)
    if spec is None:
        return False
    if spec.origin in (None, "built-in", "frozen"):
        return True
    stdlib = sysconfig.get_paths()["stdlib"]
    return spec.origin.startswith(stdlib) and "site-packages" not in spec.origin


def test_stdlib_check_works_on_python_39_as_well():
    for root in ("json", "pathlib", "sqlite3", "hashlib", "zipfile", "re"):
        assert _is_stdlib(root), root
    for root in ("flask", "sqlalchemy", "pypdf", "app"):
        assert not _is_stdlib(root), root


def test_document_modules_import_only_calibrayt_stdlib_and_locked_packages():
    lock = (REPO / "requirements-lock.txt").read_text().lower()
    for module in DOCUMENT_MODULES:
        for root in _imports(REPO / module):
            if root == "app" or root == "__future__" or _is_stdlib(root):
                continue
            assert root in ALLOWED_THIRD_PARTY, (module, root)
    for package in ("flask", "flask-login", "sqlalchemy", "werkzeug", "markupsafe", "pypdf", "python-docx"):
        assert package in lock


def test_no_airia_configuration_host_or_url():
    pattern = re.compile(r"AIRIA_[A-Z_]+|https?://[^\s\"']*airia|discovery-search|airiadocs", re.IGNORECASE)
    hits = []
    for path in list((REPO / "app").rglob("*")) + list(REPO.glob("requirements*.txt")):
        if path.suffix not in (".py", ".html", ".js", ".txt", ".json", ".css") or not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{path.relative_to(REPO)}:{number}")
    assert hits == []


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise OSError("network is blocked in this test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


@pytest.mark.no_office_auth
def test_documents_work_with_the_network_blocked(no_network):
    from datetime import timedelta

    from app import db
    from app.models.documents import CONTEXT_PROJECT, CONTEXT_SUBCONTRACTOR, DATE_EXPIRES, Document, DocumentDate
    from app.services.documents import ingest
    from app.services.documents.access import office_scope
    from app.services.documents.attention import document_attention_items
    from app.services.documents.search import Filters, search
    from app.services.documents.sources import connect_existing_documents
    from app.services.organizations import ensure_default_organization
    from tests.documents_support import ORG, STAFF, TODAY, make_app, make_world, signed_in, text_pdf

    with pytest.raises(OSError):
        socket.create_connection(("example.com", 443))
    application = make_app()
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        world = make_world(crew=False)
        client = signed_in(application, STAFF)
        data = text_pdf("WSIB clearance certificate", "Valid until 2026-11-20")
        response = client.post("/documents/upload", data={
            "context": CONTEXT_SUBCONTRACTOR, "context_id": str(world["sub"].id), "quick": "1",
            "file": (io.BytesIO(data), "WSIB clearance.pdf")}, content_type="multipart/form-data")
        assert response.status_code == 302
        document = Document.query.one()
        assert document.document_type == "WSIB_CLEARANCE"
        proposed = DocumentDate.query.filter_by(document_id=document.id, date_kind=DATE_EXPIRES).one()
        ingest.confirm_date(document, ingest.Actor.of(world["staff"]), proposed.id)
        scope = office_scope(world["staff"], ORG)
        assert search(scope, Filters(q="clearance"), today=TODAY).total == 1
        assert any(i["due_date"] for i in document_attention_items(ORG, world["staff"], TODAY + timedelta(days=1)))
        assert connect_existing_documents(ORG).reconciled
        assert client.get(f"/documents/{document.public_id}").status_code == 200
        assert client.get(f"/documents/{document.public_id}/file").data == data
        assert client.get(f"/projects/{world['project'].id}/documents").status_code == 200
        assert search(scope, Filters(context_kind=CONTEXT_PROJECT), today=TODAY).total == 0
        db.session.remove()
        db.drop_all()


def test_stored_files_stay_under_the_documents_root(tmp_path):
    from app import db
    from app.models.documents import CONTEXT_COMPANY
    from app.services import document_storage
    from app.services.organizations import ensure_default_organization
    from tests.documents_support import file_pdf, make_app, make_world

    root = tmp_path / "documents-root"
    application = make_app(DOCUMENT_ROOT=str(root))
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        world = make_world(crew=False)
        document = file_pdf(world["staff"], CONTEXT_COMPANY, None, "policy.pdf", "Policy")
        path = document_storage.absolute_stored_path(document.current_version.storage_key)
        assert root.resolve() in path.parents and path.is_file()
        assert [p for p in tmp_path.rglob("*") if p.is_file()] == [path]
        db.session.remove()
        db.drop_all()

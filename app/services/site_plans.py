"""Site Plans: every project's plans and drawings, from the office and from the crew's iPhones (Joel, 23 Oct 2026).

"I want this to go on almost every project screen in the office App and I also want it to load on the boys'
iPhones like the calculator App so they can instantly access all project plans while on a job site."

This module stores nothing and uploads nothing. It reads the two places CalibraytAI already keeps a project's
plans and drawings, and decides who may see them:

- Project Plans (app/plan_intelligence): the PDFs the office uploads on Plans → Upload Plan PDF, and generated
  drawings saved there. Private files under PLAN_UPLOAD_ROOT, one PlanDocument row each; archived ones are left
  out. Sheet numbers and names come from the Sheet Index (PlanSheet / PlanSheetPage) where the office made one.
- Construction drawing sets (app/models/construction_drawing.py): the generated deck drawings, write-once PDF
  bytes with their own sheet index. A set already saved to Project Plans is shown once, as that plan.

Who sees which projects is the rule Field already uses, unchanged:
- a Field-only crew member: app/services/access_domains.field_visible_project_ids (the jobs they are booked on,
  directly or through their crew, ending no more than two weeks ago), exactly as app/routes/field.py
  _visible_projects / _project_or_redirect apply it;
- an office member: the organization's active projects (app/services/shared_api.list_current_operating_projects);
  any of the organization's projects opens from that project's own office page (its Plans button).
Every query is scoped to the signed-in person's organization; another organization's project or file is "not
found", never shown.

Nothing here reads an estimate, price, cost, wage, customer contact or any money: a plan list is project name and
number, file names, dates, page counts and sheet numbers and names.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from io import BytesIO
from typing import List, Optional, Tuple

KIND_PLAN = "plan"
KIND_DRAWING = "drawing"
KINDS = (KIND_PLAN, KIND_DRAWING)


class PlanFileNotFound(Exception):
    """The file is not on this project, not this organization's, archived, or missing on disk."""


# ------------------------------------------------------------------ who sees which projects (Field's own rule)


def visible_project_ids(user, organization_id: str):
    """None for office members (no restriction); for Field-only crew, the projects Field shows them."""
    from app.services.access_domains import field_visible_project_ids

    return field_visible_project_ids(user, organization_id)


def visible_projects(user, organization_id: str):
    """The project list: Field's _visible_projects, word for word (active projects, crew filtered)."""
    from app.services.shared_api import list_current_operating_projects

    rows = list_current_operating_projects(organization_id)
    ids = visible_project_ids(user, organization_id)
    return rows if ids is None else [p for p in rows if p.id in ids]


def project_for(user, organization_id: str, project_id: int):
    """One project the person may open, or None: Field's _project_or_redirect, word for word."""
    from app.services.shared_api import get_organization_project

    project = get_organization_project(organization_id, project_id)
    if project is None:
        return None
    ids = visible_project_ids(user, organization_id)
    if ids is not None and project.id not in ids:
        return None
    return project


# ------------------------------------------------------------------ the plans of one project


@dataclass
class Sheet:
    page: int            # 1-based page in the PDF
    number: str = ""
    title: str = ""
    width: int = 0       # the page's size in points, so the phone lays the page out before it loads
    height: int = 0

    @property
    def label(self) -> str:
        if self.number and self.title:
            return f"{self.number} · {self.title}"
        return self.number or self.title or f"Page {self.page}"


@dataclass
class PlanFile:
    kind: str            # KIND_PLAN or KIND_DRAWING
    id: int
    title: str
    detail: str          # date, pages, revision: no money
    page_count: int
    sheets: List[Sheet] = field(default_factory=list)
    latest: bool = False

    @property
    def key(self) -> str:
        return f"{self.kind}-{self.id}"


def _plan_sheets(document) -> List[Sheet]:
    """Sheet numbers and names from the office's Sheet Index for this PDF (void sheets left out)."""
    from app.plan_intelligence.models import PlanSheet, PlanSheetPage

    rows = (PlanSheetPage.query.filter_by(plan_document_id=document.id)
            .join(PlanSheet, PlanSheet.id == PlanSheetPage.sheet_id)
            .order_by(PlanSheetPage.page_index, PlanSheetPage.order_index).all())
    sheets, seen = [], set()
    for row in rows:
        sheet = row.sheet
        if sheet is None or sheet.is_void or row.page_index in seen:
            continue
        seen.add(row.page_index)
        sheets.append(Sheet(page=row.page_index + 1, number=(sheet.number or "").strip(),
                            title=(sheet.title or "").strip()))
    return sheets


def _set_sheets(drawing_set) -> List[Sheet]:
    try:
        index = json.loads(drawing_set.sheet_index_json or "[]")
    except ValueError:
        index = []
    return [Sheet(page=i + 1, number=str(s.get("number") or "").strip(), title=str(s.get("title") or "").strip())
            for i, s in enumerate(index) if isinstance(s, dict)]


def _date(value) -> str:
    return value.strftime("%b %d, %Y").replace(" 0", " ") if value else ""


def _pages(count) -> str:
    if not count:
        return ""
    return f"{count} page{'s' if count != 1 else ''}"


def plan_files(organization_id: str, project) -> List[PlanFile]:
    """Every plan and drawing stored for the project, newest first: Project Plans PDFs, then drawing sets not
    already saved there. The project must already be checked for this person (project_for)."""
    from app.models.construction_drawing import ConstructionDrawingSet
    from app.plan_intelligence.services import list_plan_documents

    if project is None or project.organization_id != organization_id:
        return []
    sets = (ConstructionDrawingSet.query.filter_by(organization_id=organization_id, project_id=project.id)
            .order_by(ConstructionDrawingSet.drawing_revision.desc()).all())
    set_by_document = {s.plan_document_id: s for s in sets if s.plan_document_id is not None}
    files: List[PlanFile] = []
    listed_documents = set()
    for document in list_plan_documents(project.id):
        if "pdf" not in (document.content_type or "").lower():
            continue
        listed_documents.add(document.id)
        sheets = _plan_sheets(document)
        source = set_by_document.get(document.id)
        if not sheets and source is not None:
            sheets = _set_sheets(source)
        detail = " · ".join(x for x in (_date(document.created_at), _pages(document.page_count)) if x)
        files.append(PlanFile(KIND_PLAN, document.id, document.original_filename, detail,
                              int(document.page_count or 0), sheets))
    newest = sets[0].id if sets else None
    for drawing_set in sets:
        if drawing_set.plan_document_id in listed_documents:
            continue  # already listed above as the saved plan
        detail = " · ".join(x for x in (f"Revision {drawing_set.label}", _date(drawing_set.created_at),
                                         _pages(drawing_set.sheet_count)) if x)
        files.append(PlanFile(KIND_DRAWING, drawing_set.id, "Construction drawings", detail,
                              int(drawing_set.sheet_count or 0), _set_sheets(drawing_set),
                              latest=drawing_set.id == newest))
    return files


def plan_file(organization_id: str, project, kind: str, file_id: int) -> Tuple[PlanFile, bytes]:
    """One file of this project and its PDF bytes. PlanFileNotFound for anything else."""
    if project is None or project.organization_id != organization_id or kind not in KINDS:
        raise PlanFileNotFound()
    match = next((f for f in plan_files(organization_id, project) if f.kind == kind and f.id == int(file_id)), None)
    if match is None:
        raise PlanFileNotFound()
    if kind == KIND_PLAN:
        from app.plan_intelligence.services import (
            PlanIntelligenceServiceError,
            get_plan_document,
            open_plan_document_file,
        )

        document = get_plan_document(project.id, match.id)
        try:
            data = open_plan_document_file(document).read_bytes()
        except (PlanIntelligenceServiceError, ValueError, OSError) as exc:
            raise PlanFileNotFound() from exc
    else:
        from app.models.construction_drawing import ConstructionDrawingSet

        record = ConstructionDrawingSet.query.filter_by(id=match.id, organization_id=organization_id,
                                                        project_id=project.id).first()
        if record is None or not record.pdf_bytes:
            raise PlanFileNotFound()
        data = bytes(record.pdf_bytes)
    return match, data


def page_sizes(data: bytes) -> List[Tuple[int, int]]:
    """(width, height) in points of every page, as shown (rotation applied). [] if the PDF cannot be read."""
    from pypdf import PdfReader

    try:
        sizes = []
        for p in PdfReader(BytesIO(data)).pages:
            w, h = float(p.mediabox.width), float(p.mediabox.height)
            if int(p.get("/Rotate", 0) or 0) % 180:
                w, h = h, w
            sizes.append((max(1, round(w)), max(1, round(h))))
        return sizes
    except Exception:  # an unreadable PDF still opens as a whole file
        return []


def single_page(data: bytes, page: int) -> Optional[bytes]:
    """Page `page` (1-based) of the PDF as a one-page PDF, unchanged; None when there is no such page. The iPhone
    shows one page of a PDF inside a page, so each sheet is served on its own (the file itself is not changed)."""
    from pypdf import PdfReader, PdfWriter

    try:
        reader = PdfReader(BytesIO(data))
        if page < 1 or page > len(reader.pages):
            return None
        writer = PdfWriter()
        writer.add_page(reader.pages[page - 1])
        out = BytesIO()
        writer.write(out)
        return out.getvalue()
    except Exception:
        return None


def full_sheet_list(plan: PlanFile, sizes: List[Tuple[int, int]]) -> List[Sheet]:
    """One entry per page: the sheet number and name where known, otherwise "Page N", with the page's size."""
    named = {s.page: s for s in plan.sheets}
    pages = len(sizes) or plan.page_count
    out = []
    for n in range(1, max(pages, 0) + 1):
        known = named.get(n)
        w, h = sizes[n - 1] if n <= len(sizes) else (0, 0)
        out.append(Sheet(page=n, number=known.number if known else "", title=known.title if known else "",
                         width=w, height=h))
    return out


# ------------------------------------------------------------------ the office Plans button


def _int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# Office blueprints whose pages belong to one project. Field, the Site Plans app itself, the API, sign-in, training
# and supplier pages never show the office button.
_NO_BUTTON_BLUEPRINTS = frozenset({"field", "site_plans", "api_v1", "auth", "training", "supplier_portal",
                                   "supplier_pro_desk", "useful_calculators", "sign", "proposal_link",
                                   "supplier_quote_link", "walkthrough", "decision_tools"})


def button_project_id(endpoint: Optional[str], view_args: Optional[dict], args, organization_id: Optional[str]):
    """The project an office page is about, or None. One small query at most; always this organization's."""
    if not endpoint or not organization_id:
        return None
    blueprint = endpoint.split(".", 1)[0] if "." in endpoint else ""
    if blueprint in _NO_BUTTON_BLUEPRINTS:
        return None
    view_args = view_args or {}
    project_id = _int(view_args.get("project_id"))
    if project_id is None:
        from app.models import Project
        from app.models.estimate import Estimate

        if blueprint == "projects" and "id" in view_args:
            project_id = _int(view_args.get("id"))
        elif blueprint in ("estimates", "approved_costs", "estimate_labour") and "id" in view_args:
            estimate = Estimate.query.filter_by(id=_int(view_args.get("id")), organization_id=organization_id).first()
            project_id = estimate.project_id if estimate is not None else None
        elif "estimate_id" in view_args and blueprint in ("proposals", "project_controls"):
            estimate = Estimate.query.filter_by(id=_int(view_args.get("estimate_id")),
                                                organization_id=organization_id).first()
            project_id = estimate.project_id if estimate is not None else None
        elif blueprint == "proposals" and "id" in view_args:
            from app.models.proposal import Proposal

            proposal = Proposal.query.filter_by(id=_int(view_args.get("id")), organization_id=organization_id).first()
            estimate = (Estimate.query.filter_by(id=proposal.estimate_id, organization_id=organization_id).first()
                        if proposal is not None else None)
            project_id = estimate.project_id if estimate is not None else None
        elif blueprint == "project_controls" and "id" in view_args:
            from app.project_controls.models import ChangeOrder

            order = ChangeOrder.query.filter_by(id=_int(view_args.get("id")), organization_id=organization_id).first()
            project_id = order.project_id if order is not None else None
        elif blueprint == "schedule" and "item_id" in view_args:
            from app.models.schedule import WorkScheduleItem

            item = WorkScheduleItem.query.filter_by(id=_int(view_args.get("item_id")),
                                                    organization_id=organization_id).first()
            project_id = item.project_id if item is not None else None
        elif blueprint == "schedule" and args is not None and args.get("project_id"):
            project_id = _int(args.get("project_id"))
        if project_id is None:
            return None
        project = Project.query.filter_by(id=project_id, organization_id=organization_id).first()
        return project.id if project is not None else None
    from app.models import Project

    project = Project.query.filter_by(id=project_id, organization_id=organization_id).first()
    return project.id if project is not None else None

"""Turn the governed workflow definition into what one viewer may see and open (Joel, 21 Oct 2026).

Read-only. The only records read are the viewer's own: the chosen project (checked against the viewer's
company), their training progress and acceptance-test results. Nothing from another company or the other
party is read or shown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from flask import url_for

from app.workflow_map import definition as D

KIND_OFFICE = "office"
KIND_FIELD = "field"
KIND_SUPPLIER = "supplier"

AUDIENCE_LABELS = {
    D.OFFICE_ROLES: "For the owner and office staff",
    D.CONTRACTOR_ROLES: "For everyone in the contractor company",
    D.SUPPLIER_ROLES: "For everyone at the store",
    D.SUPPLIER_DESK_ROLES: "Mainly for the store's owner and administrators",
}


@dataclass
class Viewer:
    kind: str
    people_admin: bool = False
    company_management: bool = False
    supplier_id: Optional[int] = None
    project_id: Optional[int] = None
    project_name: str = ""
    training: bool = False          # the training site: lesson and acceptance-test links exist
    trainee: object = None          # TrainingTrainee when registered
    role: Optional[str] = None      # training role used to choose lessons
    projects: List[dict] = field(default_factory=list)  # the viewer's own projects, to choose from
    default_stage: Optional[str] = None  # where the viewer is when no stage was asked for (the project's stage)


def can_open(dest: D.Destination, viewer: Viewer):
    """(allowed, reason). The reason names who can open it, never what is there."""
    req = dest.requires
    if req == D.REQ_SUPPLIER:
        ok = viewer.kind == KIND_SUPPLIER
    elif req == D.REQ_CONTRACTOR:
        ok = viewer.kind in (KIND_OFFICE, KIND_FIELD)
    elif req == D.REQ_OFFICE:
        ok = viewer.kind == KIND_OFFICE
    elif req == D.REQ_PEOPLE_ADMIN:
        ok = viewer.kind == KIND_OFFICE and viewer.people_admin
    elif req == D.REQ_COMPANY_MANAGEMENT:
        ok = viewer.kind == KIND_OFFICE and viewer.company_management
    else:
        ok = False
    if ok:
        return True, ""
    if viewer.kind == KIND_SUPPLIER and req != D.REQ_SUPPLIER:
        return False, "Done in the contractor's own CalibraytAI."
    if viewer.kind != KIND_SUPPLIER and req == D.REQ_SUPPLIER:
        return False, D.REQUIREMENT_REASONS[D.REQ_SUPPLIER]
    return False, D.REQUIREMENT_REASONS.get(req, "Not available to you.")


def link_for(dest: D.Destination, viewer: Viewer) -> Optional[dict]:
    """The URL for a destination with this viewer's context, or the page where they choose the context."""
    context = {D.CTX_PROJECT: viewer.project_id, D.CTX_SUPPLIER: viewer.supplier_id}
    if all(context.get(ctx) for ctx in dest.needs):
        args = {arg: context[ctx] for arg, ctx in dest.path}
        args.update({arg: context[ctx] for arg, ctx in dest.query if context.get(ctx)})
        args.update(dict(dest.fixed))
        href = url_for(dest.endpoint, **args) + (f"#{dest.anchor}" if dest.anchor else "")
        return {"href": href, "label": dest.label, "choose": False, "endpoint": dest.endpoint}
    if dest.fallback:
        return {"href": url_for(dest.fallback), "label": dest.fallback_label, "choose": True,
                "endpoint": dest.fallback}
    return None


def _help_anchor(dest: D.Destination, viewer: Viewer) -> Optional[dict]:
    """The page's own Help, when the office has a Help topic for it (outside the training site)."""
    if viewer.kind != KIND_OFFICE or dest.needs:
        return None
    from app.services.cal_find import HELP_TOPIC_ENDPOINTS

    for key, (endpoint, args) in HELP_TOPIC_ENDPOINTS.items():
        if endpoint == dest.endpoint and dict(args) == dict(dest.fixed):
            return {"href": url_for(endpoint, **args) + f"#help-{key}", "label": "View instructions (Help)"}
    return None


# ------------------------------------------------------------------ training: lessons and acceptance tests


def _lesson_allowed(key: str, viewer: Viewer) -> bool:
    from app.training import content as C

    found = C.find_lesson(key)
    if found is None:
        return False
    module, lesson = found
    if viewer.role:
        return viewer.role in C.lesson_roles(module, lesson)
    pathway = C.PATHWAY_SUPPLIER if viewer.kind == KIND_SUPPLIER else C.PATHWAY_CONTRACTOR
    return module.pathway == pathway


def _uat_allowed(key: str, viewer: Viewer) -> bool:
    from app.training import content as C

    case = C.find_uat(key)
    if case is None:
        return False
    if viewer.role:
        return viewer.role in case.roles
    return case.pathway == (C.PATHWAY_SUPPLIER if viewer.kind == KIND_SUPPLIER else C.PATHWAY_CONTRACTOR)


class _Training:
    """The viewer's lesson states and latest acceptance-test results, read once."""

    def __init__(self, viewer: Viewer):
        self.lessons: Dict[str, dict] = {}
        self.uat: Dict[str, str] = {}
        if not (viewer.training and viewer.trainee is not None):
            return
        from app.training import service as svc

        for row in svc.overview(viewer.trainee)["modules"]:
            for x in row["lessons"]:
                self.lessons[x["lesson"].key] = {"state": x["state"], "ticked": x["ticked"], "steps": x["steps"],
                                                 "step": x["step"]}
        for row in svc.uat_overview(viewer.trainee)["rows"]:
            self.uat[row["case"].key] = row["latest"].status if row["latest"] else "NOT_TESTED"


def _lesson_rows(keys, viewer: Viewer, progress: _Training) -> List[dict]:
    from app.training import content as C

    rows = []
    for key in keys:
        if not _lesson_allowed(key, viewer):
            continue
        _module, lesson = C.find_lesson(key)
        p = progress.lessons.get(key, {})
        href = url_for("training.lesson", key=key, step=p.get("step", 0)) if viewer.training else ""
        rows.append({"key": key, "title": lesson.title, "href": href, "state": p.get("state", ""),
                     "ticked": p.get("ticked", 0), "steps": p.get("steps", len(lesson.steps))})
    return rows


def _uat_rows(keys, viewer: Viewer, progress: _Training) -> List[dict]:
    from app.training import content as C

    rows = []
    for key in keys:
        if not _uat_allowed(key, viewer):
            continue
        case = C.find_uat(key)
        rows.append({"key": key, "title": case.title,
                     "href": url_for("training.uat_case", key=key) if viewer.training else "",
                     "status": progress.uat.get(key, "")})
    return rows


# ------------------------------------------------------------------ the map


def build(map_key: str, viewer: Viewer, *, current: Optional[str], stage_endpoint: str,
          stage_args: Optional[dict] = None) -> dict:
    """Everything the map template needs for one viewer. ``stage_endpoint``/``stage_args`` make the
    ?stage= links (Back, Next, the stage cards) on the page the map is shown on."""
    wmap = D.MAPS[map_key]
    ordered = D.map_stages(map_key)
    ids = [s.id for s in ordered]
    if current not in ids:
        current = viewer.default_stage if viewer.default_stage in ids else ids[0]
    progress = _Training(viewer)
    stage_args = dict(stage_args or {})
    if viewer.project_id and map_key == D.MAP_CONTRACTOR:
        stage_args.setdefault("project_id", viewer.project_id)

    def stage_href(sid: str) -> str:
        return url_for(stage_endpoint, **stage_args, stage=sid) + "#workflow-stage"

    stages = []
    for index, s in enumerate(ordered):
        journey = D.JOURNEYS_BY_KEY[s.journey]
        substeps = []
        for x in s.substeps:
            row = {"key": x.key, "label": x.label, "availability": x.availability,
                   "availability_label": D.AVAILABILITY_LABELS[x.availability], "note": x.note,
                   "link": None, "reason": "", "instructions": None}
            if x.availability == D.AVAILABLE and x.dest is not None:
                ok, reason = can_open(x.dest, viewer)
                if ok:
                    row["link"] = link_for(x.dest, viewer)
                else:
                    row["reason"] = reason
            if x.lesson and viewer.training and _lesson_allowed(x.lesson, viewer):
                row["instructions"] = {"href": url_for("training.lesson", key=x.lesson), "label": "Instructions"}
            substeps.append(row)
        open_link, open_reason = None, ""
        if s.primary is not None:
            ok, open_reason = can_open(s.primary, viewer)
            open_link = link_for(s.primary, viewer) if ok else None
        lessons = _lesson_rows(s.lessons, viewer, progress)
        uat = _uat_rows(s.uat, viewer, progress)
        instructions = None
        if lessons and viewer.training:
            first = next((r for r in lessons if r["state"] != "done"), lessons[0])
            instructions = {"href": first["href"], "label": "View instructions"}
        elif s.primary is not None and open_link and not open_link["choose"]:
            instructions = _help_anchor(s.primary, viewer)
        training = None
        uat_link = None
        if viewer.training:
            training = {"href": url_for("training.workflow_map", stage=s.id) + "#workflow-stage",
                        "label": "Open training"}
            if uat:
                todo = next((r for r in uat if r["status"] not in ("PASS",)), uat[0])
                uat_link = {"href": todo["href"], "label": "Open UAT"}
        prev_id = ids[index - 1] if index > 0 else None
        next_id = ids[index + 1] if index + 1 < len(ids) else None
        loops = []
        for lp in s.loops:
            target = D.STAGES_BY_ID[lp.target]
            loops.append({"label": lp.label, "text": lp.text, "action": lp.action, "target": lp.target,
                          "href": stage_href(lp.target), "target_label": target.label})
        for_you = not viewer.role or viewer.role in s.roles
        stages.append({
            "id": s.id, "number": s.number, "label": s.label, "title": s.title, "summary": s.summary,
            "description": s.description, "journey": journey.key, "journey_letter": journey.letter,
            "journey_title": journey.title, "journey_size": len(journey.stage_ids), "position": index + 1,
            "href": stage_href(s.id), "substeps": substeps, "open": open_link, "open_reason": open_reason,
            "instructions": instructions, "training": training, "uat_link": uat_link, "lessons": lessons,
            "uat": uat, "loops": loops, "handoffs": list(s.handoffs),
            "prev": {"id": prev_id, "label": D.STAGES_BY_ID[prev_id].label, "href": stage_href(prev_id)} if prev_id else None,
            "next": {"id": next_id, "label": D.STAGES_BY_ID[next_id].label, "href": stage_href(next_id)} if next_id else None,
            "for_you": for_you, "audience": AUDIENCE_LABELS.get(s.roles, ""), "current": s.id == current,
        })
    by_id = {row["id"]: row for row in stages}
    journeys = []
    for key in wmap.journeys:
        j = D.JOURNEYS_BY_KEY[key]
        journeys.append({"key": j.key, "letter": j.letter, "title": j.title, "flow": j.flow, "summary": j.summary,
                         "loop_note": j.loop_note, "stages": [by_id[sid] for sid in j.stage_ids],
                         "current": any(by_id[sid]["current"] for sid in j.stage_ids)})
    handoffs = []
    if wmap.shows_handoffs:
        mine_is_supplier = wmap.side == D.SIDE_SUPPLIER
        for h in D.HANDOFFS:
            my_stage = h.supplier_stage if mine_is_supplier else h.contractor_stage
            their_stage = h.contractor_stage if mine_is_supplier else h.supplier_stage
            handoffs.append({"number": h.number, "title": h.title,
                             "mine": h.supplier if mine_is_supplier else h.contractor,
                             "theirs": h.contractor if mine_is_supplier else h.supplier,
                             "my_stage": by_id[my_stage], "their_stage": D.STAGES_BY_ID[their_stage].label})
    branches = []
    for b in wmap.branches:
        links = []
        for dest in b.dests:
            ok, reason = can_open(dest, viewer)
            links.append({**link_for(dest, viewer), "reason": ""} if ok else
                         {"href": "", "label": dest.label.replace("Open ", ""), "choose": False, "reason": reason})
        branches.append({"key": b.key, "label": b.label, "description": b.description, "links": links,
                         "opens_cal": b.opens_cal and viewer.kind == KIND_OFFICE,
                         "lessons": _lesson_rows(b.lessons, viewer, progress) if viewer.training else []})
    cur = by_id[current]
    return {
        "key": wmap.key, "side": wmap.side, "title": wmap.title, "eyebrow": wmap.eyebrow, "intro": wmap.intro,
        "journeys": journeys, "stages": stages, "current": cur, "total": len(stages), "handoffs": handoffs,
        "privacy_note": D.PRIVACY_NOTE if wmap.shows_handoffs else "", "branches": branches,
        "project": {"id": viewer.project_id, "name": viewer.project_name} if viewer.project_id else None,
        "projects": viewer.projects, "training": viewer.training, "version": D.DEFINITION_VERSION,
        "other_side": "supplier" if wmap.side != D.SIDE_SUPPLIER else "contractor",
    }

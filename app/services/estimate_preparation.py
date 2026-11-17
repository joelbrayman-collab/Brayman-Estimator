"""PREPARE MY ESTIMATE (Joel, 16 Nov 2026): the AI reads the drawings and scope; the existing engines do the estimating.

The interpreter turns drawings text and scope notes into FACTS (a plan: foundation elements with wall segments, other
scopes). It never prices or approves anything. The facts go through the existing quantity engine
(estimating_quantity.estimate_project -> foundation_quantity with the two-stage pour rule) and the result is recorded as
an EstimatePreparationRun for Ben's review; costing approval, pricing, quotation approval and CaliSIGN stay with the
existing human steps. Provider-agnostic: any object with .read_facts() works. Paid calls are OFF unless
AI_ESTIMATING_ENABLED=1 and a per-run cap AI_ESTIMATING_MAX_CENTS is set (Joel authorizes the figure first).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app import db
from app.models.estimating_assistant import EstimatePreparationRun


class PreparationError(ValueError):
    pass


# Joel, 16 Nov 2026: start at $10 per month, only to compare provider costs on real jobs. The cap is enforced here,
# before any paid call, from the cost recorded on this month's runs. Raising it needs his authorization.
MONTHLY_CAP_CENTS = 1000


def spent_this_month_cents(organization_id: str) -> int:
    start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    rows = EstimatePreparationRun.query.filter(EstimatePreparationRun.organization_id == organization_id,
                                               EstimatePreparationRun.created_at >= start).all()
    return sum(r.cost_cents or 0 for r in rows)


def monthly_cap_cents() -> int:
    return min(int(os.environ.get("AI_ESTIMATING_MONTHLY_CAP_CENTS", MONTHLY_CAP_CENTS)), MONTHLY_CAP_CENTS)


@dataclass
class Interpretation:
    plan: dict                      # {"foundation_elements": [...], "scopes": [...]}
    assumptions: list = field(default_factory=list)
    open_questions: list = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "recorded"


class RecordedInterpreter:
    """No AI: returns facts a person already read (used for tests, demos and manual fallback). Costs nothing."""

    def __init__(self, interpretation: Interpretation):
        self._i = interpretation

    name = "recorded"

    def read_facts(self, *, drawings_text: str = "", scope_text: str = "", project_id: int = 0, attachments=()) -> Interpretation:
        return self._i


class ChatCompletionsInterpreter:
    """Any OpenAI-style /chat/completions provider (Augure, Anthropic gateway, others). Disabled until authorized.

    Rates are dollars per million tokens, supplied by configuration (never assumed): AI_RATE_IN_PER_M,
    AI_RATE_OUT_PER_M (CAD or USD as the provider bills; the cap is in the same currency's cents)."""

    def __init__(self, *, base_url, api_key, model, rate_in_per_m, rate_out_per_m, max_cents):
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model
        self.rate_in, self.rate_out, self.max_cents = Decimal(str(rate_in_per_m)), Decimal(str(rate_out_per_m)), int(max_cents)
        self.name = model

    @classmethod
    def from_env(cls):
        if os.environ.get("AI_ESTIMATING_ENABLED") != "1":
            raise PreparationError("AI estimating is not enabled. It needs Joel's authorization of the cost first.")
        need = ("AI_BASE_URL", "AI_API_KEY", "AI_MODEL", "AI_RATE_IN_PER_M", "AI_RATE_OUT_PER_M", "AI_ESTIMATING_MAX_CENTS")
        missing = [k for k in need if not os.environ.get(k)]
        if missing:
            raise PreparationError("AI estimating is missing settings: " + ", ".join(missing))
        e = os.environ
        return cls(base_url=e["AI_BASE_URL"], api_key=e["AI_API_KEY"], model=e["AI_MODEL"],
                   rate_in_per_m=e["AI_RATE_IN_PER_M"], rate_out_per_m=e["AI_RATE_OUT_PER_M"],
                   max_cents=e["AI_ESTIMATING_MAX_CENTS"])

    @staticmethod
    def _attachment_parts(attachments):
        """Drawings go in as the provider accepts them: images as image_url, PDFs as file parts (base64)."""
        import base64

        parts = []
        for filename, data, media_type in attachments:
            b64 = base64.b64encode(data).decode()
            if media_type == "application/pdf":
                parts.append({"type": "file", "file": {"filename": filename, "file_data": f"data:application/pdf;base64,{b64}"}})
            elif media_type in ("image/png", "image/jpeg", "image/webp", "image/gif"):
                parts.append({"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}"}})
            else:
                raise PreparationError(f"{filename}: this file type cannot be read by the AI. Use a PDF or an image.")
        return parts

    def cost_cents(self, tokens_in, tokens_out) -> int:
        dollars = (Decimal(tokens_in) * self.rate_in + Decimal(tokens_out) * self.rate_out) / Decimal(1_000_000)
        return int((dollars * 100).to_integral_value(rounding="ROUND_CEILING"))

    def read_facts(self, *, drawings_text="", scope_text="", project_id=0, attachments=()) -> Interpretation:
        import urllib.request

        if self.cost_cents((len(drawings_text + scope_text) + sum(len(a[1]) for a in attachments) // 4) // 3 + 1500, 3000) > self.max_cents:
            raise PreparationError("This job's drawings are larger than the per-estimate AI spending cap allows. "
                                   "Nothing was sent.")
        prompt = ("Read the drawings text and scope. Reply with JSON only: {\"foundation_elements\": [...], "
                  "\"scopes\": [...], \"assumptions\": [...], \"open_questions\": [...]}. For ICF walls give "
                  "an element {\"id\",\"kind\":\"icf_wall\",\"manufacturer_id\",\"corner_90_count\",\"corner_45_count\","
                  "\"wall_segments\":[{label,length_ft,height_ft}]}. Never invent a dimension: ask instead.\n\nDRAWINGS:\n"
                  + drawings_text + "\n\nSCOPE:\n" + scope_text)
        parts = [{"type": "text", "text": prompt}] + self._attachment_parts(attachments)
        body = json.dumps({"model": self.model, "messages": [{"role": "user", "content": parts}],
                           "max_tokens": 3000, "response_format": {"type": "json_object"}}).encode()
        req = urllib.request.Request(self.base_url + "/chat/completions", data=body, headers={
            "Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"})
        data = json.loads(urllib.request.urlopen(req, timeout=120).read())
        usage = data.get("usage") or {}
        out = json.loads(data["choices"][0]["message"]["content"])
        return Interpretation(plan={"foundation_elements": out.get("foundation_elements") or [],
                                    "scopes": out.get("scopes") or []},
                              assumptions=out.get("assumptions") or [], open_questions=out.get("open_questions") or [],
                              input_tokens=int(usage.get("prompt_tokens", 0)),
                              output_tokens=int(usage.get("completion_tokens", 0)), model=self.model)


_UNIT = {"EA": "ea", "YD3": "yd3", "M3": "m3", "FT2": "ft2", "M2": "m2", "FT": "ft", "M": "m"}


def contract_payload(project_id: int, lines, engine_id: str, engine_version: str, facts: dict) -> dict | None:
    """The existing Calculation Result Contract V1, built from the existing engine's KNOWN quantity lines, so the
    existing estimate review (calculation_estimate_mapping) takes it exactly like a calculator result."""
    import hashlib

    quantities = [{"code": l["element"], "quantity": str(l["quantity"]), "unit_code": _UNIT[str(l["unit"]).upper()]}
                  for l in lines if l.get("status") == "KNOWN" and l.get("quantity") not in (None, "")
                  and str(l.get("unit") or "").upper() in _UNIT]
    if not quantities:
        return None
    digest = hashlib.sha256(json.dumps([project_id, facts, quantities], sort_keys=True, default=str).encode()).hexdigest()[:24]
    return {"contract_version": "1", "result_id": "prep-" + digest, "engine_id": engine_id, "engine_version": engine_version,
            "variant": None, "measurement_system": "imperial", "inputs": [], "assumptions": [],
            "product_specification": None, "components": [], "quantities": quantities}


def prepare_estimate(project, *, user, interpreter, drawings_text: str = "", scope_text: str = "", attachments=()) -> EstimatePreparationRun:
    """Run the preparation. The existing engines produce every quantity; the run records what happened."""
    from app.services.estimating_library import ensure_estimating_library
    from app.services.estimating_quantity import estimate_project

    run = EstimatePreparationRun(organization_id=project.organization_id, project_id=project.id, status="RUNNING",
                                 interpreter=getattr(interpreter, "name", "unknown")[:60],
                                 created_by_user_id=getattr(user, "id", None))
    db.session.add(run)
    db.session.commit()
    steps = []
    try:
        steps.append({"step": "cost library", "result": "ensured", "added": ensure_estimating_library(project.organization_id)})
        if getattr(interpreter, "cost_cents", None) is not None and \
                spent_this_month_cents(project.organization_id) >= monthly_cap_cents():
            raise PreparationError("The monthly AI spending cap has been reached. Nothing was sent.")
        found = interpreter.read_facts(drawings_text=drawings_text, scope_text=scope_text, project_id=project.id,
                                       attachments=attachments)
        run.input_tokens, run.output_tokens = found.input_tokens, found.output_tokens
        rate_cost = getattr(interpreter, "cost_cents", None)
        run.cost_cents = rate_cost(found.input_tokens, found.output_tokens) if rate_cost else 0
        run.facts_json = json.dumps(found.plan, default=str)
        steps.append({"step": "read drawings and scope", "interpreter": run.interpreter})
        plan = dict(found.plan, project_id=project.id)
        quantities = estimate_project(plan)
        lines = list(quantities.get("lines") or ())
        unresolved = [l for l in lines if l.get("status") not in (None, "KNOWN")]
        payload = contract_payload(project.id, lines, "foundation_quantity", "1", found.plan)
        if payload is None:
            steps.append({"step": "estimate review (existing)", "result": "no quantities to review"})
        else:
            from app.services import calculator_projects as CP
            from app.services import guided_estimating as G

            guided = G.get_guided(project.organization_id, project.id)
            if guided is not None and guided.estimate is None:  # the existing step that opens the estimate
                G.ensure_estimate(guided, actor="AI estimating assistant", user_id=getattr(user, "id", None))
                db.session.commit()
                steps.append({"step": "estimate opened (existing)", "result": "ensured"})

            actor = (getattr(user, "email", None) or "AI estimating assistant")[:150]
            record, _created = CP.save_to_project(
                organization_id=project.organization_id, project=project, calculator="icf_wall",
                summary="Prepared by the estimating assistant from the drawings and scope",
                result_text="\n".join(f"{q['code']}: {q['quantity']} {q['unit_code']}" for q in payload["quantities"]),
                entered=[], payload=payload, user_id=getattr(user, "id", None), actor_display_name=actor)
            try:
                intake = CP.send_to_review(organization_id=project.organization_id, record=record, actor=actor,
                                           user_id=getattr(user, "id", None))
                steps.append({"step": "estimate review (existing)", "result": "quantities waiting for confirmation",
                              "intake_id": intake.id})
            except CP.CalculatorProjectError as exc:
                steps.append({"step": "estimate review (existing)", "result": "saved on the project; " + str(exc)})
        steps.append({"step": "quantity engines (existing)", "lines": len(lines), "unresolved": len(unresolved)})
        run.assumptions_json = json.dumps(found.assumptions)
        questions = list(found.open_questions) + [l.get("description") or l.get("code") for l in unresolved]
        run.open_questions_json = json.dumps(questions, default=str)
        run.status = "NEEDS_INPUT" if questions else "COMPLETED"
    except Exception as exc:  # noqa: BLE001 - recorded, never swallowed
        db.session.rollback()
        run = db.session.get(EstimatePreparationRun, run.id)
        run.status = "FAILED"
        steps.append({"step": "failed", "error": str(exc)[:300]})
    run.steps_json = json.dumps(steps, default=str)
    run.completed_at = datetime.utcnow()
    db.session.commit()
    return run

"""What a wizard step reads: the run, who is signed in, and the real records the run points at (read only)."""

from __future__ import annotations

from functools import cached_property

from flask import url_for

from app.models.wizard import SIDE_SUPPLIER


class WizardContext:
    def __init__(self, run, wizard, *, user, organization_id=None, supplier=None):
        self.run = run
        self.wizard = wizard
        self.user = user
        self.organization_id = organization_id
        self.supplier = supplier

    # ------------------------------------------------------------------ who
    @property
    def user_id(self):
        return getattr(self.user, "id", None)

    @property
    def actor(self) -> str:
        name = (getattr(self.user, "display_name", None) or getattr(self.user, "email", None) or "").strip()
        return name[:150]

    @property
    def is_supplier(self) -> bool:
        return self.run.side == SIDE_SUPPLIER

    # ------------------------------------------------------------------ contractor records (company scoped)
    @cached_property
    def project(self):
        if self.is_supplier or not self.run.project_id:
            return None
        from app.models.project import Project

        return Project.query.filter_by(id=self.run.project_id, organization_id=self.organization_id).first()

    @cached_property
    def guided(self):
        if self.project is None:
            return None
        from app.services.guided_estimating import get_guided

        return get_guided(self.organization_id, self.project.id)

    @cached_property
    def draft(self) -> dict:
        from app.wizards.service import draft_fields

        return draft_fields(self.run)

    # ------------------------------------------------------------------ supplier records (supplier scoped)
    @cached_property
    def share(self):
        if not self.is_supplier or not self.run.supplier_share_id:
            return None
        from app.services.supplier_hub import SupplierHubError, supplier_share

        try:
            return supplier_share(self.supplier.id, self.run.supplier_share_id)
        except SupplierHubError:
            return None

    @cached_property
    def quote(self):
        if not self.is_supplier or not self.run.supplier_quote_id:
            return None
        from app.services.supplier_pro_desk import ProDeskError, supplier_quote

        try:
            return supplier_quote(self.supplier.id, self.run.supplier_quote_id)
        except ProDeskError:
            return None

    # ------------------------------------------------------------------ wizard urls
    def step_url(self, step_key: str, **params) -> str:
        if self.is_supplier:
            return url_for("supplier_portal.wizard_step", supplier_id=self.supplier.id, run_id=self.run.id,
                           step_key=step_key, **params)
        return url_for("wizards.step", run_id=self.run.id, step_key=step_key, **params)

    def return_to(self, step_key: str) -> str:
        """The wizard step, as the ``return_to`` an existing page accepts (app/services/return_path.py)."""
        return self.step_url(step_key)

    def start_url(self, wizard_key: str) -> str:
        if self.is_supplier:
            return url_for("supplier_portal.wizard_start", supplier_id=self.supplier.id)
        return url_for("wizards.start", wizard_key=wizard_key)

    def _endpoint(self, name):
        return f"supplier_portal.wizard_{name}" if self.is_supplier else f"wizards.{name}"

    def _ids(self):
        ids = {"run_id": self.run.id}
        if self.is_supplier:
            ids["supplier_id"] = self.supplier.id
        return ids

    def open_url(self, step_key: str, href: str) -> str:
        """Open an existing page from a step, with a "Return to the wizard" bar shown there."""
        return url_for(self._endpoint("open" if self.is_supplier else "open_page"), step_key=step_key, to=href,
                       **self._ids())

    def manual_url(self, step_key: str) -> str:
        return url_for(self._endpoint("manual"), step_key=step_key, **self._ids())

    def end_url(self) -> str:
        return url_for(self._endpoint("end"), **self._ids())

    def autosave_url(self, step_key: str) -> str:
        if self.is_supplier:
            return ""
        return url_for("wizards.autosave", run_id=self.run.id, step_key=step_key)

    def help_url(self) -> str:
        if self.is_supplier:
            return url_for("supplier_portal.wizard_help", supplier_id=self.supplier.id)
        return url_for("help.ask_help")

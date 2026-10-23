"""Delivery model label (23 Oct 2026): the stored "Self-Perform" reads "Internal" everywhere it is shown."""
from app.services.commercial_context import DELIVERY_MODELS, delivery_model_label


def test_self_perform_reads_internal_and_others_are_unchanged():
    assert delivery_model_label("Self-Perform") == "Internal"
    assert delivery_model_label("Mixed") == "Mixed"
    assert delivery_model_label("Primarily Subcontracted") == "Primarily Subcontracted"
    assert "Self-Perform" in DELIVERY_MODELS  # the stored value is unchanged; no data migration


def test_project_forms_show_internal(tmp_path):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app" / "templates" / "projects"
    for name in ("form.html", "edit_context.html"):
        text = (root / name).read_text()
        assert "{{ opt|delivery_model_label }}</option>" in text
    assert "ctx.delivery_model|delivery_model_label" in (root / "detail.html").read_text()

"""The approved Supplier Pricing Request form (Joel, 28 Oct 2026): the request for estimate template.

Joel approved the fillable "Supplier Pricing Request" PDF (dark Brayman and CalibraytAI logos on the navy header,
28 Oct 2026) and asked for it to be the template in the repository: "DO NOT change the form or calculations". This
module draws that exact form — the same page, positions, colours, fonts, fields, field names and the same
JavaScript calculation (quantity x unit cost, the totals, HST, the pricing summary on page 2) — from data, so that:

* ``render_supplier_pricing_request_form(request)`` fills it for one job and one supplier (the workflow fills the
  project, the supplier and the supplier's contact, the dates, the items and the quantities; the supplier's boxes
  stay fillable), and
* ``render_blank_supplier_pricing_request_form()`` gives the blank master: every important value is a fillable box,
  including the supplier's contact, the items and the quantities, with the same calculation.

Joel's additions of 28 Oct 2026 ("not only values but contact info for the supplier"): the supplier's contact (name
and phone, then email) under the supplier's name on both pages, and the blank master. Nothing else differs from the
approved form. With no contact given, the filled form is the approved form exactly.

Up to ten items fit page 1 exactly as approved; more continue on further pages of the same table, and the totals
follow the last item. Up to four groups appear on the pricing summary (the approved form has two: "Siding package"
and "Soffit, fascia & aluminum").

Manual transport only: this module writes no price into the commercial records and sends nothing.
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Optional, Sequence

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

PAGE_W, PAGE_H = letter  # 612 x 792

# The approved form's own colours (taken from the approved PDF).
NAVY = Color(0.121569, 0.227451, 0.372549)    # #1F3A5F
GOLD = Color(0.780392, 0.603922, 0.168627)    # #C79A2B
MUTED = Color(0.356863, 0.407843, 0.466667)   # #5B6877
PANEL = Color(0.956863, 0.964706, 0.972549)   # #F4F6F8
BAND = Color(0.980392, 0.984314, 0.988235)    # #FAFBFC
RULE = Color(0.72549, 0.768627, 0.811765)     # #B9C4CF
BLACK = Color(0, 0, 0)
WHITE = Color(1, 1, 1)

BRANDING = Path(__file__).resolve().parents[1] / "static" / "branding"
BRAYMAN_LOGO_DARK = BRANDING / "brayman-construction-logo-dark.png"
CALIBRAYTAI_LOGO_DARK = BRANDING / "calibraytai-logo-v1-dark.png"

CONTRACTOR = "Brayman Construction Co. Inc."
HOW_TO_PRICE = ("Review our takeoff. Supplier Qty is pre-filled; change it only if you see an adjustment. Enter Ben "
                "Unit Cost - extensions and totals calculate automatically.")
READER_URL = "https://get.adobe.com/reader/"
READER_LABEL = "get.adobe.com/reader"
HOW_TO_OPEN = ("Open this form in free Adobe Acrobat Reader (",
               ") or in Chrome, Edge or Firefox so the totals calculate. Fill it in, save it, and send it back.")
HST_RATE = 0.13
ROWS_PER_PAGE = 10
ROW_H = 39
TABLE_TOP = 545
MAX_GROUPS = 4
BLANK_ROWS = 10


class SupplierPricingFormError(ValueError):
    pass


# ---------------------------------------------------------------------------------------------- public API
def render_supplier_pricing_request_form(request: dict) -> bytes:
    """The approved form filled for one job and one supplier.

    ``request``: project, supplier, supplier_tag (header, e.g. "TIMBER MART / IROQUOIS"), requested (date text),
    plans, scope, optional contact {name, phone, email}, optional contractor, optional prepared_by (pre-filled
    'Prepared by'), items [{key, item, spec, qty, unit, group}] and groups [{key, label}] (each item's group is one
    of them; the summary shows each group's total).
    """
    data = _validated(request)
    return _build(data, blank=False)


def render_blank_supplier_pricing_request_form() -> bytes:
    """The blank master: the same form with every important value a fillable box (ten item rows, two groups)."""
    items = [{"key": f"row{n:02d}", "item": "", "spec": "", "qty": "", "unit": "", "group": ""}
             for n in range(1, BLANK_ROWS + 1)]
    data = {"project": "", "supplier": "", "supplier_tag": "", "requested": "", "plans": "", "scope": "",
            "contact": {}, "contractor": CONTRACTOR, "prepared_by": "", "items": items,
            "groups": [{"key": "group1", "label": ""}, {"key": "group2", "label": ""}]}
    return _build(data, blank=True)


def supplier_contact(supplier) -> dict:
    """The supplier's contact for the form, from the Supplier Hub: the first active supplier user (name, email,
    mobile) — empty when the supplier has no sign-in yet (the boxes are then left to fill by hand)."""
    from app.models.supplier_portal import SupplierUserMembership

    membership = (SupplierUserMembership.query.filter_by(supplier_id=supplier.id, status="ACTIVE")
                  .order_by(SupplierUserMembership.id.asc()).first())
    if membership is None or membership.user is None:
        return {}
    user = membership.user
    name = getattr(user, "display_name", None) or getattr(user, "name", None) or ""
    return {"name": name, "email": getattr(user, "email", "") or "",
            "phone": getattr(user, "mobile_phone", None) or getattr(user, "phone", None) or ""}


def project_label(project) -> str:
    """The form's PROJECT value: the job name with the Brayman Project # (and the Client Project # when it fits),
    taken from the project record (Joel, 30 Oct 2026). The form's layout is unchanged."""
    from app.services.project_identity import is_numbered_customer_project

    label = project.name
    if is_numbered_customer_project(project):
        label = f"{label} · {project.project_number}"
        if project.client_project_number and len(label) + len(project.client_project_number) + 12 <= 52:
            label = f"{label} · Client # {project.client_project_number}"
    return label


def request_for_supplier_account(account, *, project, items: Sequence[dict], groups: Sequence[dict], requested: str,
                                 plans: str = "", scope: str = "", contact: Optional[dict] = None) -> dict:
    """The form's data when a supplier is chosen in the workflow: the project, the supplier (and branch) and the
    supplier's contact come from the records; items and quantities from the takeoff."""
    supplier = account.supplier
    location = getattr(account, "supplier_location", None)
    branch = location.display_name if location is not None else ""
    name = supplier.legal_name if not branch else f"{supplier.legal_name} - {branch}"
    tag = supplier.legal_name.upper() + (f" / {branch.upper()}" if branch else "")
    return {"project": project_label(project), "supplier": name, "supplier_tag": tag, "requested": requested, "plans": plans,
            "scope": scope, "contact": contact if contact is not None else supplier_contact(supplier),
            "items": list(items), "groups": list(groups)}


# ---------------------------------------------------------------------------------------------- data
def _validated(request: dict) -> dict:
    data = dict(request)
    for key in ("project", "supplier", "supplier_tag", "requested"):
        if not str(data.get(key) or "").strip():
            raise SupplierPricingFormError(f"The form needs the {key.replace('_', ' ')}.")
    data.setdefault("plans", "")
    data.setdefault("scope", "")
    data["contact"] = {k: str(v or "").strip() for k, v in (data.get("contact") or {}).items()}
    data.setdefault("contractor", CONTRACTOR)
    data.setdefault("prepared_by", "")
    items = list(data.get("items") or [])
    groups = list(data.get("groups") or [])
    if not items:
        raise SupplierPricingFormError("The form needs at least one item.")
    if not 1 <= len(groups) <= MAX_GROUPS:
        raise SupplierPricingFormError(f"The pricing summary takes one to {MAX_GROUPS} groups.")
    group_keys = [g["key"] for g in groups]
    keys = [i["key"] for i in items]
    if len(set(keys)) != len(keys) or any(not k.replace("_", "").isalnum() for k in keys):
        raise SupplierPricingFormError("Each item needs its own simple key (letters and numbers).")
    for item in items:
        if item.get("group") not in group_keys:
            raise SupplierPricingFormError(f"Item {item['key']} is in no group of the summary.")
    data["items"], data["groups"] = items, groups
    return data


def _qty_text(value) -> str:
    """The Calibrayt quantity as shown in its column (1,750)."""
    try:
        number = float(str(value).replace(",", ""))
    except ValueError:
        return str(value)
    return f"{number:,.0f}" if number == int(number) else f"{number:,.2f}".rstrip("0").rstrip(".")


def _qty_value(value) -> str:
    """The Supplier Qty box's value (1750): a plain number the calculation reads."""
    return str(value).replace(",", "")


# ---------------------------------------------------------------------------------------------- drawing
def _build(data: dict, *, blank: bool) -> bytes:
    pages = _item_pages(data["items"])
    total_pages = len(pages) + 1
    buffer = BytesIO()
    form = Canvas(buffer, pagesize=letter)
    form.setTitle("Supplier Pricing Request")
    form.setAuthor(data["contractor"])
    editable = []
    for number, rows in enumerate(pages, start=1):
        if number > 1:
            form.showPage()
        _header(form, "SUPPLIER PRICING REQUEST", data, number, total_pages)
        _request_info(form, data, blank)
        _how_to_price(form)
        _table(form, rows, number, blank, editable)
        if number == len(pages):
            _totals(form, editable, data.get("prepared_by", ""))
        _footer(form, "Supplier Pricing Request")
    form.showPage()
    _header(form, "PRICING SUMMARY", data, total_pages, total_pages)
    _summary(form, data, blank)
    _footer(form, "Supplier Pricing Summary")
    form.save()
    return _with_calculation(buffer.getvalue(), data, blank, editable)


def _item_pages(items):
    return [items[i:i + ROWS_PER_PAGE] for i in range(0, len(items), ROWS_PER_PAGE)]


def _text(form, x, y, text, font, size, color, *, align="left"):
    form.setFillColor(color)
    form.setFont(font, size)
    if align == "centre":
        form.drawCentredString(x, y, text)
    elif align == "right":
        form.drawRightString(x, y, text)
    else:
        form.drawString(x, y, text)


def _box(form, name, x, y, w, h, *, size=8, value="", read_only=False, font="Helvetica", plain=False):
    """A fillable box exactly as on the approved form (white, 0.7 pt rule border); ``plain`` boxes (the blank
    master's header values) are light grey with no border, so the header keeps its look."""
    form.acroForm.textfield(
        name=name, x=x, y=y, width=w, height=h, value=value, fontName=font, fontSize=size, maxlen=100,
        borderWidth=0 if plain else 0.7, borderColor=PANEL if plain else RULE, fillColor=PANEL if plain else WHITE,
        textColor=BLACK, fieldFlags="readOnly" if read_only else "", forceBorder=not plain)


def _logo(form, path, x, y, w, h):
    image = ImageReader(str(path))
    form.drawImage(image, x, y, w, h, mask="auto", preserveAspectRatio=True, anchor="c")


def _header(form, title, data, page, pages):
    form.setFillColor(NAVY)
    form.rect(0, 706, 612, 86, fill=1, stroke=0)
    form.setFillColor(GOLD)
    form.rect(0, 702, 612, 4, fill=1, stroke=0)
    _logo(form, BRAYMAN_LOGO_DARK, 39, 717, 122, 61)
    _text(form, 184, 744, title, "Helvetica-Bold", 8.5, GOLD)
    _logo(form, CALIBRAYTAI_LOGO_DARK, 446.3289, 718, 120.3422, 58)
    tag = data["supplier_tag"]
    _text(form, 578, 712, (f"{tag}  |  " if tag else "") + f"Page {page} of {pages}", "Helvetica", 6.4, WHITE,
          align="right")


def _label(form, x, y, text):
    _text(form, x, y, text, "Helvetica-Bold", 6.8, MUTED)


def _value(form, x, y, text):
    _text(form, x, y, text, "Helvetica", 9, BLACK)


def _contact_lines(contact):
    first = " · ".join(v for v in (contact.get("name", ""), contact.get("phone", "")) if v)
    return [line for line in (first, contact.get("email", "")) if line]


def _request_info(form, data, blank):
    _label(form, 34, 684, "PROJECT")
    _label(form, 280, 684, "CONTRACTOR")
    _value(form, 280, 670, data["contractor"])
    _label(form, 455, 684, "SUPPLIER")
    _label(form, 34, 645, "REQUESTED")
    _label(form, 170, 645, "PLANS")
    _label(form, 390, 645, "SCOPE")
    if blank:
        _box(form, "project", 34, 666, 236, 14, size=9, plain=True)
        _box(form, "supplier", 455, 666, 123, 14, size=9, plain=True)
        _box(form, "supplier_contact", 455, 657, 123, 8.5, size=6.5, plain=True)
        _box(form, "supplier_email", 455, 648, 123, 8.5, size=6.5, plain=True)
        _box(form, "requested", 34, 627, 126, 14, size=9, plain=True)
        _box(form, "plans", 170, 627, 210, 14, size=9, plain=True)
        _box(form, "scope", 390, 627, 188, 14, size=9, plain=True)
        return
    _value(form, 34, 670, data["project"])
    _value(form, 455, 670, data["supplier"])
    for n, line in enumerate(_contact_lines(data["contact"])):
        _text(form, 455, 661 - 8 * n, line, "Helvetica", 6.5, MUTED)
    _value(form, 34, 631, data["requested"])
    _value(form, 170, 631, data["plans"])
    _value(form, 390, 631, data["scope"])


def _how_to_price(form):
    form.setFillColor(PANEL)
    form.roundRect(34, 585, 544, 41, 5, stroke=0, fill=1)
    _text(form, 44, 613, "HOW TO PRICE", "Helvetica-Bold", 8, NAVY)
    _text(form, 44, 602, HOW_TO_PRICE, "Helvetica", 7.3, MUTED)
    # Joel, 29 Oct 2026: the totals calculate only in a viewer that runs the form's calculation, so the form
    # says which ones, with a link to the free Reader.
    x = 44
    for text, font in ((HOW_TO_OPEN[0], "Helvetica"), (READER_LABEL, "Helvetica-Bold"), (HOW_TO_OPEN[1], "Helvetica")):
        _text(form, x, 591, text, font, 7.3, NAVY if font.endswith("Bold") else MUTED)
        width = stringWidth(text, font, 7.3)
        if text == READER_LABEL:
            form.linkURL(READER_URL, (x, 589, x + width, 599), relative=0)
        x += width


HEAD_CELLS = ((34, 168, ("ITEM / SPECIFICATION",)), (202, 142, ("CALIBRAYT", "QTY")), (344, 45, ("SUPPLIER", "QTY")),
              (389, 50, ("UNIT",)), (439, 75, ("BEN UNIT", "COST")), (514, 78, ("EXTENDED", "COST")))


def _table(form, rows, page, blank, editable):
    for x, w, lines in HEAD_CELLS:
        form.setFillColor(NAVY)
        form.rect(x, TABLE_TOP, w, 27, fill=1, stroke=0)
        for n, line in enumerate(lines):
            _text(form, x + w / 2, 562 - 8 * n, line, "Helvetica-Bold", 6.4, WHITE, align="centre")
    for index, item in enumerate(rows):
        bottom = TABLE_TOP - ROW_H * (index + 1)
        if index % 2 == 0:
            form.setFillColor(BAND)
            form.rect(34, bottom, 544, ROW_H, fill=1, stroke=0)
        form.setStrokeColor(RULE)
        form.line(34, bottom, 592, bottom)
        key = item["key"]
        if blank:
            _box(form, f"item_{key}", 39, bottom + 21, 158, 12, size=7.4, font="Helvetica-Bold", plain=True)
            _box(form, f"spec_{key}", 39, bottom + 8, 158, 11, size=6.5, plain=True)
            _box(form, f"cqty_{key}", 250, bottom + 12, 46, 14, size=8, font="Helvetica-Bold", plain=True)
            _box(form, f"unit_{key}", 396, bottom + 12, 36, 14, size=7.5, font="Helvetica-Bold", plain=True)
        else:
            _text(form, 39, bottom + 24, item["item"], "Helvetica-Bold", 7.4, BLACK)
            _text(form, 39, bottom + 11, item.get("spec", ""), "Helvetica", 6.5, MUTED)
            _text(form, 273, bottom + 16, _qty_text(item["qty"]), "Helvetica-Bold", 8, BLACK, align="centre")
        _box(form, f"qty_{key}", 347, bottom + 8, 39, 22, value="" if blank else _qty_value(item["qty"]))
        editable.append(f"qty_{key}")
        if not blank:
            _text(form, 414, bottom + 16, item["unit"], "Helvetica-Bold", 7.5, BLACK, align="centre")
        _box(form, f"cost_{key}", 443, bottom + 8, 66, 22)
        editable.append(f"cost_{key}")
        _box(form, f"ext_{key}", 518, bottom + 8, 70, 22, read_only=True)


def _totals(form, editable, prepared_by):
    form.setFillColor(PANEL)
    form.roundRect(330, 83, 262, 62, 4, stroke=0, fill=1)
    _text(form, 342, 127, "MATERIAL SUBTOTAL - PRE-HST", "Helvetica-Bold", 8, NAVY)
    _box(form, "subtotal", 487, 119, 95, 19, read_only=True)
    _text(form, 342, 107, f"HST ({HST_RATE:.0%})", "Helvetica-Bold", 8, MUTED)
    _box(form, "hst", 487, 99, 95, 19, read_only=True)
    _text(form, 342, 88, "TOTAL INCLUDING HST", "Helvetica-Bold", 9, NAVY)
    _box(form, "total_hst", 487, 80, 95, 19, size=9, read_only=True)
    for x, label in ((34, "SUPPLIER QUOTE #"), (170, "PREPARED BY"), (306, "VALID UNTIL"), (422, "SUPPLIER NOTES")):
        _label(form, x, 68, label)
    _box(form, "quote_no", 34, 41, 120, 22)
    editable.append("quote_no")
    _box(form, "prepared_by", 170, 41, 120, 22, value=prepared_by)
    editable.append("prepared_by")
    _box(form, "valid_until", 306, 41, 100, 22)
    _box(form, "supplier_notes", 422, 23, 170, 40, size=7)


def _footer(form, title):
    form.setStrokeColor(RULE)
    form.line(34, 25, 578, 25)
    _text(form, 34, 14, f"Brayman Construction Co. Inc.  |  {title}", "Helvetica", 6.4, MUTED)
    _text(form, 578, 14, "Prepared with CalibraytAI", "Helvetica-Bold", 6.4, GOLD, align="right")


def _summary(form, data, blank):
    _label(form, 34, 682, "PROJECT")
    _label(form, 355, 682, "SUPPLIER")
    if blank:
        _box(form, "summary_project", 34, 664, 300, 14, size=9, plain=True)
        _box(form, "summary_supplier", 355, 664, 223, 14, size=9, plain=True)
    else:
        _value(form, 34, 668, data["project"])
        _value(form, 355, 668, data["supplier"])
        contact = " · ".join(_contact_lines(data["contact"]))
        if contact:
            _text(form, 355, 659, contact, "Helvetica", 6.5, MUTED)
    form.setFillColor(PANEL)
    form.roundRect(34, 602, 544, 48, 6, stroke=0, fill=1)
    _text(form, 48, 630, "FINAL MATERIAL QUOTE - PRE-HST", "Helvetica-Bold", 10, NAVY)
    _box(form, "summary_total", 390, 613, 185, 27, size=13, read_only=True)
    # As on the approved form: the HST box is white with the default 1 pt black outline. It reaches down to 535
    # so the Total box (541-561) sits inside it (it hung 6 pt out of the bottom; Joel, 29 Oct 2026).
    form.setFillColor(WHITE)
    form.setStrokeColor(BLACK)
    form.setLineWidth(1)
    form.roundRect(34, 535, 544, 55, 5, stroke=1, fill=1)
    _text(form, 48, 573, f"HST ({HST_RATE:.0%})", "Helvetica-Bold", 8, MUTED)
    _box(form, "summary_hst", 390, 562, 185, 20, size=9, read_only=True)
    _text(form, 48, 552, "TOTAL INCLUDING HST", "Helvetica-Bold", 9, NAVY)
    _box(form, "summary_total_hst", 390, 541, 185, 20, size=10, read_only=True)
    groups = data["groups"]
    for n, group in enumerate(groups):
        y = 473 - 48 * n
        form.setStrokeColor(RULE)
        form.roundRect(34, y, 544, 34, 4, stroke=1, fill=0)
        if blank:
            _box(form, f"label_{group['key']}", 48, y + 9, 300, 14, size=9, font="Helvetica-Bold", plain=True)
        else:
            _text(form, 48, y + 13, group["label"], "Helvetica-Bold", 9, BLACK)
        _box(form, f"sum_{group['key']}", 425, y + 7, 150, 21, size=9, read_only=not blank)
    shift = 48 * (len(groups) - 2)
    form.setFillColor(NAVY)
    form.roundRect(34, 393 - shift, 544, 24, 4, stroke=0, fill=1)
    _text(form, 45, 401 - shift, "SUPPLIER ADJUSTMENTS", "Helvetica-Bold", 8, WHITE)
    _text(form, 34, 379 - shift, "Only differences from the Calibrayt takeoff need to be noted here.", "Helvetica", 7.2,
          MUTED)
    for n in range(4):
        _box(form, f"adj_{n + 1}", 34, 339 - 31 * n - shift, 544, 22, size=7)
    form.setFillColor(PANEL)
    form.roundRect(34, 185 - shift, 544, 48, 5, stroke=0, fill=1)
    _text(form, 46, 215 - shift, "SUPPLIER CONFIRMATION", "Helvetica-Bold", 8, NAVY)
    _text(form, 46, 202 - shift, "If no quantities are changed, the Calibrayt takeoff is considered supplier-confirmed "
          "for pricing purposes.", "Helvetica", 7.1, MUTED)
    for x, label in ((34, "PREPARED BY"), (204, "DATE"), (344, "QUOTE #")):
        _label(form, x, 62, label)
    _box(form, "summary_prepared", 34, 34, 150, 22, value=data.get("prepared_by", ""))
    _box(form, "summary_date", 204, 34, 120, 22)
    _box(form, "summary_quote", 344, 34, 120, 22)


# ---------------------------------------------------------------------------------------------- calculation
def calculation_script(keys: Sequence[str], groups: Sequence[dict], members: dict, *, blank: bool) -> str:
    """The approved form's calculation, for these items and groups (the approved form's script, generalised)."""
    lines = [
        "",
        "function n(v){ var x=parseFloat(v); return isNaN(x)?0:x; }",
        "function m(v){ return '$' + v.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ','); }",
        "function recalc(){",
        f" var keys={json.dumps(list(keys))}; var groups={json.dumps({} if blank else members)}; var total=0;"
        + " var sums={};",
        " for(var i=0;i<keys.length;i++){",
        "  var k=keys[i]; var q=n(this.getField('qty_'+k).value); var c=n(this.getField('cost_'+k).value); var e=q*c;",
        "  this.getField('ext_'+k).value = c?m(e):''; total+=e;",
        "  if(groups[k]){ sums[groups[k]]=(sums[groups[k]]||0)+e; }",
        " }",
        f" var tax=total*{HST_RATE}; var grand=total+tax;",
        " this.getField('subtotal').value=m(total); this.getField('hst').value=m(tax); "
        "this.getField('total_hst').value=m(grand);",
        " this.getField('summary_total').value=m(total); this.getField('summary_hst').value=m(tax); "
        "this.getField('summary_total_hst').value=m(grand);",
    ]
    if not blank:
        lines.append(" " + " ".join(f"this.getField('sum_{g['key']}').value=m(sums['{g['key']}']||0);"
                                    for g in groups))
    lines += [
        " this.getField('summary_prepared').value=this.getField('prepared_by').value;",
        " this.getField('summary_quote').value=this.getField('quote_no').value;",
        "}",
        "recalc();",
        "",
    ]
    return "\n".join(lines)


def _with_calculation(pdf: bytes, data: dict, blank: bool, editable: list) -> bytes:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, TextStringObject

    keys = [item["key"] for item in data["items"]]
    members = {item["key"]: item["group"] for item in data["items"]}
    script = calculation_script(keys, data["groups"], members, blank=blank)
    writer = PdfWriter(clone_from=PdfReader(BytesIO(pdf)))
    writer.add_js(script)

    def action():
        return DictionaryObject({NameObject("/S"): NameObject("/JavaScript"),
                                 NameObject("/JS"): TextStringObject(script)})

    wanted = set(editable)
    for page in writer.pages:
        for annot in page.get("/Annots", []) or []:
            widget = annot.get_object()
            if str(widget.get("/T")) in wanted:
                widget[NameObject("/AA")] = DictionaryObject({NameObject("/Bl"): action(), NameObject("/V"): action()})
    out = BytesIO()
    writer.write(out)
    return out.getvalue()

# Supplier Pricing Request — template library

> **29 Oct 2026 — Supplier Unit Pricing.** Templates now have a schema 2 (requirements in takeoff units, sell units with
> verified conversions only) and are used in the app on the project's Supplier requests page:
> [../architecture/supplier-unit-pricing.md](../architecture/supplier-unit-pricing.md). `hardie-vertical-aluminum-v1`
> is **superseded** by `hardie-vertical-aluminum-v2`: its box ratios and sealant coverage were not verified product
> data and are removed (left unresolved until a person records a verified conversion). v1 stays loadable.

Joel, 29 Oct 2026: "we should save this template for Hardie Board estimates? We should have a library of these?"

A template is a reusable package for one kind of job: the item list, specifications, units, summary groups and the
rule that turns plan measurements into each item's quantity. The next job of that kind needs only its
measurements; the approved Supplier Pricing Request form is filled unchanged.

- Library: `app/data/supplier_pricing_templates/` — one JSON file per template; the version is in the key
  (`…-v1`). A changed template is a new file, so earlier requests stay reproducible.
- Code: `app/services/supplier_pricing_templates.py` (`list_templates`, `load_template`, `quantities`,
  `request_from_template`).
- Tool: `tools/documents/supplier_pricing_request_form.py --list-templates` and `--job job.json OUT.pdf`
  (job.json: template key, measurements, project, supplier, supplier tag, requested date, optional plans,
  colour choices, contact, prepared by). Real job files stay outside Git.
- Templates hold no prices, client or supplier (a test enforces it).
- Quantities round up (we lean slightly high so the supplier does no work).

## Templates

| Key | Title | Measurements |
|---|---|---|
| `hardie-vertical-aluminum-v1` | Hardie vertical siding + aluminum soffit, fascia & trim | siding SF, battens, panel joints, trim joints, soffit SF, fascia, corners, window trim, door trim, drip cap, freeze boards, J-channel (LF) |

Hardie v1 rules: sheets = SF x 1.10 / 32; 12 ft pieces = LF x 1.10 / 12; 10 ft pieces = LF x 1.10 / 10;
soffit = SF x 1.10 / 16; sealant = trim-joint LF / 25 per tube; touch-up kit 1. Box counts were set so the first
job (29 Oct 2026) reproduces exactly and should be confirmed by Joel: Hardie nails 1 box per 25 sheets; aluminum
trim nails 1 box per 40 aluminum pieces; soffit/fascia fasteners 1 box per 14 soffit pieces.

Not yet: a page in the app to choose a template and enter measurements (where it appears is Joel's decision,
together with the blank master's place). Nothing here is deployed.

"""Write the approved Supplier Pricing Request form: the blank master, or a filled one from a JSON file.

  ./venv/bin/python tools/documents/supplier_pricing_request_form.py --blank OUT.pdf
  ./venv/bin/python tools/documents/supplier_pricing_request_form.py --request request.json OUT.pdf
  ./venv/bin/python tools/documents/supplier_pricing_request_form.py --job job.json OUT.pdf
  ./venv/bin/python tools/documents/supplier_pricing_request_form.py --list-templates

request.json holds what app.services.supplier_pricing_request_form.render_supplier_pricing_request_form takes
(project, supplier, supplier_tag, requested, plans, scope, contact, items, groups). job.json names a template from
the library and the job's measurements: {"template": "hardie-vertical-aluminum-v1", "measurements": {...},
"project", "supplier", "supplier_tag", "requested", optional "plans", "choices", "contact", "prepared_by"}; the
quantities come from the template's rules. Real job files stay outside Git.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import app.models  # noqa: E402,F401  (the services package needs the models loaded first)
from app.services.supplier_pricing_request_form import (  # noqa: E402
    render_blank_supplier_pricing_request_form, render_supplier_pricing_request_form)
from app.services.supplier_pricing_templates import list_templates, request_from_template  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--blank", action="store_true")
    group.add_argument("--request")
    group.add_argument("--job")
    group.add_argument("--list-templates", action="store_true")
    parser.add_argument("out", nargs="?")
    args = parser.parse_args()
    if args.list_templates:
        for t in list_templates():
            print(f"{t['key']}  -  {t['title']}")
        return
    if not args.out:
        parser.error("name the PDF to write")
    if args.blank:
        pdf = render_blank_supplier_pricing_request_form()
    elif args.job:
        job = json.loads(Path(args.job).read_text())
        key, measurements = job.pop("template"), job.pop("measurements")
        pdf = render_supplier_pricing_request_form(request_from_template(key, measurements, **job))
    else:
        pdf = render_supplier_pricing_request_form(json.loads(Path(args.request).read_text()))
    Path(args.out).write_bytes(pdf)
    print(args.out)


if __name__ == "__main__":
    main()

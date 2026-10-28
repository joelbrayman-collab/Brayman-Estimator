"""Write the approved Supplier Pricing Request form: the blank master, or a filled one from a JSON file.

  ./venv/bin/python tools/documents/supplier_pricing_request_form.py --blank OUT.pdf
  ./venv/bin/python tools/documents/supplier_pricing_request_form.py --request request.json OUT.pdf

request.json holds what app.services.supplier_pricing_request_form.render_supplier_pricing_request_form takes
(project, supplier, supplier_tag, requested, plans, scope, contact, items, groups). Real job files stay outside Git.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import app.models  # noqa: E402,F401  (the services package needs the models loaded first)
from app.services.supplier_pricing_request_form import (  # noqa: E402
    render_blank_supplier_pricing_request_form, render_supplier_pricing_request_form)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--blank", action="store_true")
    group.add_argument("--request")
    parser.add_argument("out")
    args = parser.parse_args()
    pdf = (render_blank_supplier_pricing_request_form() if args.blank
           else render_supplier_pricing_request_form(json.loads(Path(args.request).read_text())))
    Path(args.out).write_bytes(pdf)
    print(args.out)


if __name__ == "__main__":
    main()

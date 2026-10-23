"""Check that the storybook's browser worksheet gives the same results as the CalibraytAI Supplier Economics
Calculator (app/services/supplier_economic_model.py, model version 2). Run with the app's venv python."""
import json, sys
from decimal import Decimal
from playwright.sync_api import sync_playwright

REPO = "/home/claude/joelbrayman-collab/brayman-estimator"
import importlib.util
_spec = importlib.util.spec_from_file_location("sem", f"{REPO}/app/services/supplier_economic_model.py")
_sem = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_sem)
calculate = _sem.calculate
assert _sem.MODEL_VERSION == "2", _sem.MODEL_VERSION

BOOK = sys.argv[1]
BASE = {"active_contractor_accounts": "8", "takeoff_share_percent": "50", "takeoff_requests_per_month": "10", "manual_hours_per_takeoff": "3",
        "estimator_cost_per_hour": "80", "validation_hours_per_takeoff": "0.5", "hours_per_quote": "5", "contribution_per_quote": "400",
        "average_material_value": "10000", "quote_to_order_percent": "25", "material_gross_margin_percent": "20", "base_platform_cost": "5000",
        "active_contractor_cost": "3000", "unpriced_requested_value": "50000", "missed_capture_percent": "30"}
CASES = [BASE,
         {**BASE, "takeoff_share_percent": "100", "quote_to_order_percent": "40", "contribution_per_quote": ""},
         {**BASE, "validation_hours_per_takeoff": "3", "base_platform_cost": "90000"},
         {**BASE, "hours_per_quote": "0", "missed_capture_percent": "120"},
         {**BASE, "unpriced_requested_value": "", "material_gross_margin_percent": "12.5", "takeoff_requests_per_month": "37"},
         {k: "" for k in BASE}]
KEYS = ["annual_takeoff_volume", "calibraytai_originated_takeoff_volume", "takeoff_labour_value", "hours_released", "additional_quote_capacity",
        "capacity_value", "commercial_value", "program_cost", "operational_value", "net_supplier_value", "takeoff_labour_value_won_quotes",
        "takeoff_labour_value_unsuccessful_quotes", "missed_opportunity_value", "net_supplier_value_with_missed_opportunity"]
fails = 0
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto("file://" + BOOK); pg.wait_for_timeout(500)
    for n, case in enumerate(CASES, 1):
        py = calculate({k: {"value": v, "classification": "estimated"} for k, v in case.items()})["results"]
        js = pg.evaluate("c => semModel(k => { const v = c[k]; return (v === '' || v === undefined) ? null : Number(v); })", case)
        for k in KEYS:
            pv = py[k]["value"] if py[k]["status"] == "established" else None
            jv = js.get(k)
            ok = (pv is None and jv is None) or (pv is not None and jv is not None and abs(Decimal(pv) - Decimal(str(round(jv, 4)))) <= Decimal("0.01"))
            if not ok:
                fails += 1
                print(f"case {n} {k}: python={pv} browser={jv}")
    b.close()
print("parity", "OK" if not fails else f"FAILED ({fails})", f"{len(CASES)} cases × {len(KEYS)} results")
sys.exit(1 if fails else 0)

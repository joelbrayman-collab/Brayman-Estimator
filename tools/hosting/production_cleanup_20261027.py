"""CalibraytAI Production cleanup, 27 Oct 2026 — the ONE cleanup Joel approved (Step 2). Not a general tool.

What it does, and only this:
  * removes the projects, customers, sign-ins, organizations and shared test items Joel approved by ID
    (each ID is pinned to its exact name or email as found on 27 Oct 2026; a mismatch stops everything);
  * removes every record attached to them, found through the database's own foreign keys plus the few
    links the schema keeps without a declared key (UNDECLARED below);
  * renames two display names (Joel (test) -> Joel Brayman; Joel (test) (supplier) -> Joel Brayman (Supplier));
  * moves the files that belong only to removed records into instance/cleanup-quarantine-<date>/ (never deletes).

It refuses to run when: the database is not at revision e5d1v4r7y2k9; any pinned ID no longer matches; a
protected record (Joel's identities, Ben, Kevin, ORG-001, P27 and everything attached to it, the historical
estimates, legal/signing configuration, pricing and labour configuration, audit history, ...) would be removed or
changed; an audit/history row would be left pointing at a removed record (reported, never deleted); or the
database's foreign-key check would show any violation that was not already there before.

Modes (stdlib only; run with python3):
  plan    --db PATH [--files LISTING.tsv]                       dry run: prints everything, changes nothing
  apply   --db PATH --instance DIR --expect-plan HASH [--live --backup PATH]
          one all-or-nothing transaction; files copied to quarantine and checked before the commit, originals
          removed only after it. Without --live it refuses to touch the Production database path.
  verify  --before COPY --after PATH                            proves the result row by row
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
from collections import Counter, defaultdict

REVISION = "e5d1v4r7y2k9"
LIVE_DB = "/opt/render/project/src/instance/brayman_estimator.db"
TODAY = "20261027"

# ------------------------------------------------------------------------------------------------ the approved plan
# Joel's Step 2 decisions (27 Oct 2026): every project except P27; every customer except C22 (P27's); sign-ins
# U2-U14; the two test organizations; and the shared test items listed. Each ID pinned to its exact label.
REMOVE = {
    "projects": {
        1: "Estimator Project", 2: "FG-009 UAT Test", 3: "FG-010 UAT", 4: "FG015-UAT-ISO-OTHER-ORG",
        5: "FG015-UAT-COMPLETE", 6: "FG015-UAT-INCOMPLETE", 7: "FG015-UAT-UNKNOWN", 8: "FG015-UAT-GOWER",
        9: "FG-016 UAT — Mike Pratt Coach House", 10: "FG-016 UAT — Unsupported Coverage (synthetic)",
        11: "FG-016 UAT — Unsupported Use (synthetic Ottawa garage)", 12: "FG-018 UAT Actor Project",
        13: "FG-023 UAT MONITOR", 14: "FG029-UAT-BMR-DEMO", 15: "FG031-UAT-SCOPE-ROUTING",
        16: "FG031-UAT-SCOPE-ROUTING", 17: "FG031-UAT-SCOPE-ROUTING", 18: "FG031-UAT-SCOPE-ROUTING",
        19: "FG031-UAT-SCOPE-ROUTING", 20: "FG031B-UAT-SUBCONTRACT-QUOTES", 21: "FG031B-UAT-SUBCONTRACT-QUOTES",
        22: "FG031B-UAT-SUBCONTRACT-QUOTES", 23: "FG031B-UAT-SUBCONTRACT-QUOTES", 24: "FG031B-UAT-SUBCONTRACT-QUOTES",
        25: "FG031B-UAT-SUBCONTRACT-QUOTES", 26: "FG032-UAT-QB-ENTRY", 28: "FG024C-UAT Contract Generation",
        29: "FG024D-UAT SYNTHETIC ONTARIO CONTRACT UAT — NOT FOR EXECUTION",
        30: "FG033A-UAT SYNTHETIC NATIVE SIGNING — NOT FOR EXECUTION",
        31: "FG033B-UAT SYNTHETIC CUSTOMER CEREMONY — NOT FOR EXECUTION",
        32: "FG033C-UAT SYNTHETIC COUNTERSIGN — NOT FOR EXECUTION",
        33: "FG033C-UAT SYNTHETIC NO-COUNTERSIGN — NOT FOR EXECUTION",
        34: "FG033C-UAT SYNTHETIC RESEND — NOT FOR EXECUTION", 35: "FG033C-UAT SYNTHETIC VOID — NOT FOR EXECUTION",
        36: "FG033C-UAT SYNTHETIC EXPIRE — NOT FOR EXECUTION", 37: "FG033C-UAT SYNTHETIC DECLINE — NOT FOR EXECUTION",
        38: "FG033D-UAT SYNTHETIC IPHONE CEREMONY — NOT FOR EXECUTION", 39: "FG034-UAT MAIL-B SYNTHETIC — NOT A CUSTOMER",
        40: "FG033-UAT SYNTHETIC CONTRACT SIGN-A — NOT FOR EXECUTION", 41: "FG034-UAT AUTH-D SYNTHETIC CO",
        42: "FG035-UAT TAX/WBS SYNTHETIC — NOT A CUSTOMER", 43: "FG035-UAT SCOPE SYNTHETIC — NOT A CUSTOMER",
        44: "FG035-UAT TIME SYNTHETIC — NOT A CUSTOMER", 45: "FG035-UAT SCH-A SYNTHETIC — NOT A CUSTOMER",
        46: "FG035-UAT SCH-B SYNTHETIC — NOT A CUSTOMER", 47: "FG035-UAT SCH-C SYNTHETIC — NOT A CUSTOMER",
        48: "FG035-UAT SCH-D SYNTHETIC — NOT A CUSTOMER", 49: "FG035-UAT PERF-A SYNTHETIC — NOT A CUSTOMER",
        50: "FG035-UAT PERF-B SYNTHETIC — NOT A CUSTOMER", 51: "SYNTHETIC UAT 1 OCT 2026 Live Walk",
        52: "M3-SCRATCH-2026-10-08", 53: "Synthetic rectangular footing 2026-10-10",
        54: "SYNTHETIC drawings release check 20261014-2235 (not a customer)",
    },
    "clients": {i: None for i in list(range(1, 22)) + list(range(23, 49))},  # names checked: see CLIENT_PIN
    "users": {
        2: "uat-inactive-fg018@example.invalid", 3: "uat-nomember-fg018@example.invalid",
        4: "uat-multi-fg018@example.invalid", 5: "uat-foreign-fg018@example.invalid",
        # U6 (authb-uat) stays, switched off: the system-administrator history points at its membership.
        7: "authc-uat@example.invalid", 8: "mailb-uat@example.invalid", 9: "authd-uat@example.invalid",
        10: "fg035-time-worker@example.com", 11: "fg035-time-reviewer@example.com",
        12: "fg035-sch-b-worker-a@example.invalid", 13: "fg035-sch-b-worker-b@example.invalid",
        14: "fg035-sch-b-inactive@example.invalid",
    },
    "organizations": {"ORG-FG014-UAT": "FG-014 UAT Isolation Org", "ORG-002": "FG031B Isolation DEMO"},
    "organization_crews": {1: "FG035-UAT Concrete Crew", 2: "FG035-UAT Retire Proof Crew", 3: "FG035-UAT SCH-D Field Crew"},
    "assemblies": {1: "FG014-UAT-ASM", 2: "FG026-UAT-DOOR"},
    "cost_items": {3: "MAT-FG009-UAT", 4: "FG014-UAT-MAT", 5: "FG014-UAT-LAB", 6: "FG014-UAT-EQP", 7: "FG014-UAT-SUB",
                   8: "FG014-UAT-ALL", 9: "FG014-UAT-OTH", 10: "FG014-UAT-CROSS", 11: "MAT-FG032-UAT",
                   12: "MAT-M3-SCRATCH-20261008"},
    "work_types": {2: "FG035-UAT-TES-EXTRA"},
    # Template 1 stays for now: P27's draft proposal PROP-2026-0006 uses it (Joel to decide).
    "proposal_templates": {2: "FG-017 UAT Isolation Template",
                           3: "FG024D-UAT SYNTHETIC TEMPLATE", 4: "FG033A-UAT Template"},
    "subcontractors": {1: "FG031B-HVAC", 2: "FG031B-HVAC-2", 3: "FG031B-INSTALL", 4: "FG031B-LABOUR", 5: "FG031B-ISSUED"},
    "suppliers": {1: "BMR-WINCHESTER-DEMO", 2: "YARD-M3-SCRATCH", 3: "SYN-DRW-20261014-2235"},
}
# Which column holds the pinned label for each seed table.
LABEL = {"projects": "name", "clients": "name", "users": "email", "organizations": "display_name",
         "organization_crews": "name", "assemblies": "code", "cost_items": "code", "work_types": "code",
         "proposal_templates": "name", "subcontractors": "code", "suppliers": "code"}
CLIENT_PIN = {1: "Michelle Steele", 47: "M3 scratch client"}  # every other removed customer must be labelled UAT/SYNTHETIC
CLIENT_MARK = re.compile(r"UAT|SYNTHETIC", re.I)

# (table, id): (column, old value, new value, guard column, guard value)
RENAME = {("users", 15): ("display_name", "Joel (test)", "Joel Brayman", "email", "joel.brayman@gmail.com"),
          ("users", 18): ("display_name", "Joel (test) (supplier)", "Joel Brayman (Supplier)", "email",
                          "joel.brayman+supplier@gmail.com"),
          # Switch off the UAT sign-in that has to stay because history points at it.
          ("users", 6): ("is_active", 1, 0, "email", "authb-uat@example.invalid"),
          ("user_memberships", 5): ("is_active", 1, 0, "user_id", 6)}

# Protected records: never removed, never changed (beyond RENAME). Rows of P27 are protected as a whole.
PROTECT_ROWS = {
    "users": {1: "joel@braymanconstruction.ca", 15: "joel.brayman@gmail.com", 16: "ben@braymanconstruction.ca",
              17: "kgarnett53@icloud.com", 18: "joel.brayman+supplier@gmail.com"},
    "organizations": {"ORG-001": "Brayman Construction"},
    "projects": {27: "40x80 Thickened-Edge Concrete Slab"},
    "clients": {22: "Marc Bouliion"},
    "cost_items": {1: "LAB-001", 2: "001"},  # undecided: protected until Joel decides
}
PROTECT_PROJECT_TREE = {27}
# Whole tables that must come through untouched (configuration, legal, history, identity, audit).
PROTECT_TABLES = {
    "alembic_version", "historical_cost_line_items", "historical_data_quality_flags",
    "historical_estimate_review_decisions", "historical_estimates", "historical_labour_items",
    "historical_source_observations", "historical_source_workbooks", "historical_subcontract_items",
    "historical_upload_attempts", "legal_content_activation_events", "legal_content_candidate_changes",
    "legal_content_candidate_impacts", "legal_content_jurisdiction_packages", "legal_content_objects",
    "legal_content_review_events", "legal_content_source_snapshots", "legal_content_sources",
    "signing_consent_versions", "jurisdiction_aliases", "jurisdiction_definitions", "permit_rules",
    "canonical_materials", "banked_hours_policies", "organization_pricing_policies",
    "direct_labour_cost_rate_standards", "production_rate_standards", "labour_tasks", "labour_task_mappings",
    "labour_calibration_candidates", "work_element_templates", "work_activity_templates",
    "organization_people", "wizard_runs", "wizard_run_events",
}
# Audit and history kept as evidence (Joel's decision 8). Rows here that belong to a removed project's own
# records go with the project; any OTHER row here pointing at a removed record is reported and blocks the run.
AUDIT_TABLES = {
    "pricing_audit_events", "labour_audit_events", "people_access_events", "organization_instance_owner_events",
    "organization_system_administrator_events", "password_reset_access_attempts", "transactional_messages",
    "transactional_delivery_events", "signing_token_access_attempts",
}
# Records owned by the rows that point at them (a signing request points at its frozen document): removed when
# every row pointing at them is removed, kept when any kept row still points at them.
OWNED_BY_REFERRERS = {
    "signing_frozen_artifacts": [("signing_requests", "frozen_artifact_id"),
                                 ("signing_executed_artifacts", "source_frozen_artifact_id")],
}
# Links the schema keeps without a declared foreign key; treated exactly like foreign keys.
UNDECLARED = {
    ("project_contract_snapshots", "project_id"): "projects",
    ("project_contract_snapshots", "client_id"): "clients",
    ("project_contract_snapshots", "estimate_version_id"): "estimate_versions",
    ("project_contract_snapshots", "proposal_id"): "proposals",
    ("project_contract_snapshots", "organization_id"): "organizations",
    ("estimate_versions", "signed_off_by_user_id"): "users",
    ("takeoff_package_items", "plan_document_id"): "plan_documents",
    ("takeoff_package_items", "drawing_revision_id"): "drawing_revisions",
    ("takeoff_package_items", "plan_page_id"): "plan_pages",
    ("takeoff_package_items", "plan_sheet_id"): "plan_sheets",
    ("takeoff_estimate_insertion_citations", "takeoff_package_item_id"): "takeoff_package_items",
    ("takeoff_estimate_insertion_citations", "takeoff_candidate_id"): "takeoff_candidates",
    ("takeoff_estimate_insertion_citations", "takeoff_run_id"): "takeoff_extraction_runs",
    ("takeoff_estimate_insertion_citations", "plan_document_id"): "plan_documents",
    ("takeoff_estimate_insertion_citations", "drawing_revision_id"): "drawing_revisions",
    ("takeoff_estimate_insertion_citations", "plan_page_id"): "plan_pages",
    ("takeoff_estimate_insertion_citations", "plan_sheet_id"): "plan_sheets",
    ("supplier_package_lines", "material_requirement_id"): "material_requirements",
    ("project_work_scope_history", "actor_user_id"): "users",
    ("work_schedule_history", "assignment_id"): "work_schedule_assignments",
    ("work_schedule_history", "dependency_id"): "project_work_dependencies",
    ("calculation_quantity_reviews", "suggested_cost_item_id"): "cost_items",
    ("calculation_quantity_reviews", "suggested_assembly_id"): "assemblies",
    ("calculation_mapping_acceptances", "target_cost_item_id"): "cost_items",
    ("calculation_mapping_acceptances", "target_assembly_id"): "assemblies",
    ("project_calculations", "estimate_version_id"): "estimate_versions",
}
# Soft mentions (type + id, no link): reported for information only; history keeps its wording.
SOFT = [("pricing_audit_events", "entity_type", "entity_id"), ("labour_audit_events", "entity_type", "entity_id"),
        ("transactional_messages", "related_type", "related_id")]
# Files: project folders, plus generated contracts named by storage key.
FILE_PROJECT = [re.compile(r"^plan_uploads/(\d+)/"), re.compile(r"^deck_takeoff/[^/]+/(\d+)/")]
FILE_KEYED = [("generated_contracts/", "project_generated_contracts", "artifact_storage_key"),
              ("generated_contracts/", "project_contract_snapshots", "artifact_storage_key")]


class Refuse(Exception):
    pass


# ------------------------------------------------------------------------------------------------ the engine
def open_db(path, write=False):
    con = sqlite3.connect(path if write else f"file:{path}?mode=ro", uri=not write, isolation_level=None)
    con.row_factory = sqlite3.Row
    return con


def schema(con):
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    pk = {}
    links = defaultdict(list)  # parent table -> [(child table, child column)]
    for t in tables:
        info = con.execute(f'PRAGMA table_info("{t}")').fetchall()
        pks = [r["name"] for r in info if r["pk"]]
        pk[t] = pks[0] if len(pks) == 1 else "rowid"
        for r in con.execute(f'PRAGMA foreign_key_list("{t}")'):
            links[r["table"]].append((t, r["from"]))
    for (t, c), parent in UNDECLARED.items():
        if t in pk:
            links[parent].append((t, c))
    return tables, pk, links


def check_pins(con):
    for table, rows in REMOVE.items():
        col = LABEL[table]
        key = "id"
        for rid, label in rows.items():
            r = con.execute(f'SELECT "{col}" FROM "{table}" WHERE "{key}"=?', (rid,)).fetchone()
            if r is None:
                raise Refuse(f"{table} {rid} is no longer there (pinned {label!r})")
            have = r[0]
            if table == "clients":
                want = CLIENT_PIN.get(rid)
                ok = (have == want) if want else bool(CLIENT_MARK.search(have or ""))
            elif table == "organizations":
                ok = have == label
            else:
                ok = have == label
            if not ok:
                raise Refuse(f"{table} {rid} is now {have!r}, not the approved {label or 'UAT/SYNTHETIC customer'!r}")
    for table, rows in PROTECT_ROWS.items():
        col = LABEL.get(table, "name")
        for rid, label in rows.items():
            r = con.execute(f'SELECT "{col}" FROM "{table}" WHERE id=?', (rid,)).fetchone()
            if r is None or not str(r[0]).startswith(label):
                raise Refuse(f"protected {table} {rid} is not {label!r} as expected")
    for (table, rid), (col, old, new, gcol, gval) in RENAME.items():
        r = con.execute(f'SELECT "{gcol}", "{col}" FROM "{table}" WHERE id=?', (rid,)).fetchone()
        if r is None or r[0] != gval or r[1] not in (old, new):
            raise Refuse(f"change target {table} {rid} is not {gcol}={gval!r} with {col}={old!r}")


def closure(con, pk, links, seeds):
    """Every row reachable from the seeds by following links from parent to child (rows that point at a removed
    row are removed too). Returns {table: set(keys)} and the audit rows that were reached (not removed)."""
    gone = defaultdict(set)
    audit_hits = defaultdict(set)
    frontier = []
    for t, keys in seeds.items():
        for k in keys:
            if k not in gone[t]:
                gone[t].add(k)
                frontier.append((t, k))
    while frontier:
        by_table = defaultdict(list)
        for t, k in frontier:
            by_table[t].append(k)
        frontier = []
        for parent, keys in by_table.items():
            for child, col in links.get(parent, []):
                key = pk[child]
                for i in range(0, len(keys), 500):
                    chunk = keys[i:i + 500]
                    marks = ",".join("?" * len(chunk))
                    for r in con.execute(f'SELECT "{key}" FROM "{child}" WHERE "{col}" IN ({marks})', chunk):
                        k = r[0]
                        if child in AUDIT_TABLES or child in PROTECT_TABLES:
                            audit_hits[(child, col, parent)].add(k)
                            continue
                        if k not in gone[child]:
                            gone[child].add(k)
                            frontier.append((child, k))
    return gone, audit_hits


def project_tree(con, pk, links, project_ids):
    tree, _hits = closure(con, pk, links, {"projects": set(project_ids)})
    return tree


def plan(con, files=None):
    rev = con.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    if rev != REVISION:
        raise Refuse(f"database revision {rev}, expected {REVISION}")
    check_pins(con)
    tables, pk, links = schema(con)
    seeds = {t: set(rows) for t, rows in REMOVE.items()}
    gone, audit_hits = closure(con, pk, links, seeds)
    for owned, referrers in OWNED_BY_REFERRERS.items():
        extra = set()
        for r in con.execute(f'SELECT id FROM "{owned}"'):
            pointing = [(t, k) for t, col in referrers
                        for (k,) in con.execute(f'SELECT "{pk[t]}" FROM "{t}" WHERE "{col}"=?', (r[0],))]
            if pointing and all(k in gone.get(t, set()) for t, k in pointing):
                extra.add(r[0])
        if extra:
            more, more_hits = closure(con, pk, links, {owned: extra})
            for t, k in more.items():
                gone[t] |= k
            for key, v in more_hits.items():
                audit_hits[key] |= v
    # The audit rows reached only through records of a removed project tree are part of that tree (they are the
    # project's own history, e.g. signing_events); org-level audit pointing at a removed row blocks the run.
    project_rows = project_tree(con, pk, links, REMOVE["projects"])
    blockers = []
    for (child, col, parent), keys in sorted(audit_hits.items()):
        if child in PROTECT_TABLES or child in AUDIT_TABLES:
            blockers.append({"table": child, "column": col, "points_to": parent, "rows": sorted(keys)})
    # Protection checks.
    problems = []
    keep_tree = project_tree(con, pk, links, PROTECT_PROJECT_TREE)
    for t, keys in keep_tree.items():
        hit = keys & gone.get(t, set())
        if hit:
            problems.append(f"P27's {t} rows {sorted(hit)[:10]} would be removed")
    for t, rows in PROTECT_ROWS.items():
        hit = set(rows) & gone.get(t, set())
        if hit:
            problems.append(f"protected {t} {sorted(hit)} would be removed")
    for t in PROTECT_TABLES:
        if gone.get(t):
            problems.append(f"protected table {t} would lose rows")
    soft = []
    for t, tcol, icol in SOFT:
        if t not in pk:
            continue
        for r in con.execute(f'SELECT "{tcol}", "{icol}" FROM "{t}" WHERE "{icol}" IS NOT NULL'):
            soft.append((t, r[0], r[1]))
    soft_hits = Counter()
    name_of = {"Project": "projects", "Estimate": "estimates", "EstimateVersion": "estimate_versions",
               "CostItem": "cost_items", "Assembly": "assemblies", "Proposal": "proposals", "ChangeOrder": "change_orders",
               "LabourTask": "labour_tasks", "User": "users", "Client": "clients", "user": "users",
               "signing_request": "signing_requests", "EstimatePricingSnapshot": "estimate_pricing_snapshots",
               "EstimateLabourSnapshot": "estimate_labour_snapshots"}
    for t, typ, rid in soft:
        target = name_of.get(str(typ))
        if target and str(rid).isdigit() and int(rid) in gone.get(target, set()):
            soft_hits[(t, typ)] += 1
    file_plan = plan_files(con, gone, files or [])
    counts = {t: len(k) for t, k in sorted(gone.items()) if k}
    digest = hashlib.sha256(json.dumps({t: sorted(map(str, k)) for t, k in gone.items() if k},
                                       sort_keys=True).encode()).hexdigest()[:16]
    return {"revision": rev, "counts": counts, "total": sum(counts.values()), "gone": gone, "pk": pk,
            "blockers": blockers, "problems": problems, "soft": soft_hits, "files": file_plan, "hash": digest,
            "tables": tables, "links": links}


def plan_files(con, gone, listing):
    removed_projects = gone.get("projects", set())
    keys_gone, keys_kept = set(), set()
    for prefix, table, col in FILE_KEYED:
        pkcol = "id"
        for r in con.execute(f'SELECT "{pkcol}", "{col}" FROM "{table}" WHERE "{col}" IS NOT NULL'):
            (keys_gone if r[0] in gone.get(table, set()) else keys_kept).add(prefix + r[1])
    out = []
    for rel, size in listing:
        why = None
        for rx in FILE_PROJECT:
            m = rx.match(rel)
            if m:
                pid = int(m.group(1))
                why = ("quarantine", f"project {pid}") if pid in removed_projects else ("keep", f"project {pid}")
        if rel in keys_kept:
            why = ("keep", "referenced by a kept record")
        elif rel in keys_gone and why is None:
            why = ("quarantine", "generated contract of a removed project")
        if why is None:
            why = ("keep", "not owned by any removed record")
        out.append({"path": rel, "size": size, "action": why[0], "reason": why[1]})
    return out


def report(p):
    print(f"PLAN_HASH={p['hash']}  revision={p['revision']}")
    print(f"ROWS_TO_REMOVE={p['total']} in {len(p['counts'])} tables")
    for t, n in p["counts"].items():
        print(f"  {t}: {n}")
    q = [f for f in p["files"] if f["action"] == "quarantine"]
    print(f"FILES_TO_QUARANTINE={len(q)} ({sum(f['size'] for f in q)} bytes)")
    for f in p["files"]:
        print(f"  {f['action'].upper():10} {f['path']} ({f['size']} bytes; {f['reason']})")
    print("CHANGES=" + "; ".join(f"{t} {i} {c}: {old!r} -> {new!r}" for (t, i), (c, old, new, _g, _v) in RENAME.items()))
    print(f"SOFT_MENTIONS (history wording only, kept): " + (", ".join(f"{t}:{ty}={n}" for (t, ty), n in sorted(p['soft'].items())) or "none"))
    if p["blockers"]:
        print("BLOCKERS (kept audit/configuration rows that point at a record to be removed):")
        for b in p["blockers"]:
            print(f"  {b['table']}.{b['column']} -> {b['points_to']}: rows {b['rows']}")
    if p["problems"]:
        print("PROTECTION_PROBLEMS:")
        for x in p["problems"]:
            print("  " + x)
    print("READY=" + ("yes" if not p["blockers"] and not p["problems"] else "no"))


# ------------------------------------------------------------------------------------------------ apply
def fk_violations(con):
    return sorted(tuple(r) for r in con.execute("PRAGMA foreign_key_check"))


def dangling_undeclared(con, gone):
    bad = []
    for (t, c), parent in UNDECLARED.items():
        ids = gone.get(parent)
        if not ids:
            continue
        for r in con.execute(f'SELECT rowid, "{c}" FROM "{t}" WHERE "{c}" IS NOT NULL'):
            if r[1] in ids:
                bad.append((t, c, r[0]))
    return bad


def order_for_delete(gone, links):
    """Children before parents (cycles are fine: foreign keys are checked once, at the end)."""
    deps = defaultdict(set)
    for parent, kids in links.items():
        for child, _c in kids:
            if child != parent:
                deps[parent].add(child)
    done, out = set(), []

    def visit(t, stack=()):
        if t in done or t in stack:
            return
        for c in deps.get(t, ()):
            if c in gone:
                visit(c, stack + (t,))
        done.add(t)
        out.append(t)
    for t in gone:
        visit(t)
    return out


def apply(db, instance, expect_hash, live=False, backup=None, listing=None):
    if os.path.realpath(db) == LIVE_DB and not live:
        raise Refuse("this is the live Production database: add --live (and --backup) only with Joel's authorization")
    if live:
        if not backup or not os.path.exists(backup):
            raise Refuse("--live needs --backup pointing at the pre-cleanup backup")
        age = dt.datetime.now().timestamp() - os.path.getmtime(backup)
        if age > 1800:
            raise Refuse(f"backup {backup} is {int(age // 60)} minutes old; take a fresh one")
        b = open_db(backup)
        if b.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise Refuse("the backup does not pass its integrity check")
        b.close()
    ro = open_db(db)
    files = listing if listing is not None else scan_files(instance)
    p = plan(ro, files)
    ro.close()
    if p["hash"] != expect_hash:
        raise Refuse(f"plan changed since the dry run (now {p['hash']}, approved {expect_hash})")
    if p["blockers"] or p["problems"]:
        raise Refuse("blockers or protection problems remain; see the dry run")
    con = open_db(db, write=True)
    con.execute("PRAGMA foreign_keys=OFF")  # no automatic cascades or SET NULL: exactly the planned rows go
    before = fk_violations(con)
    qdir = os.path.join(instance, f"cleanup-quarantine-{TODAY}")
    os.makedirs(os.path.join(qdir, "files"), exist_ok=True)
    manifest = {"cleanup": "CalibraytAI Production cleanup 27 Oct 2026", "plan_hash": p["hash"],
                "started_at": dt.datetime.now(dt.timezone.utc).isoformat(), "database": db, "rows": {}, "renames": [],
                "files": [], "pre_existing_fk_violations": before}
    staged = []
    try:
        for f in p["files"]:  # copy first, check, originals removed only after the commit
            if f["action"] != "quarantine":
                continue
            src = os.path.join(instance, f["path"])
            dst = os.path.join(qdir, "files", f["path"])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            h1, h2 = sha256(src), sha256(dst)
            if h1 != h2:
                raise Refuse(f"quarantine copy of {f['path']} does not match")
            staged.append((src, dst))
            manifest["files"].append({"path": f["path"], "size": f["size"], "sha256": h1,
                                      "quarantined_to": os.path.relpath(dst, instance)})
        con.execute("BEGIN IMMEDIATE")
        for t in order_for_delete(p["gone"], p["links"]):
            keys = sorted(p["gone"][t], key=str)
            key = p["pk"][t]
            rows = []
            for i in range(0, len(keys), 500):
                chunk = keys[i:i + 500]
                marks = ",".join("?" * len(chunk))
                for r in con.execute(f'SELECT * FROM "{t}" WHERE "{key}" IN ({marks})', chunk):
                    rows.append({k: _jsonable(r[k]) for k in r.keys()})
                n = con.execute(f'DELETE FROM "{t}" WHERE "{key}" IN ({marks})', chunk).rowcount
                if n != len(chunk):
                    raise Refuse(f"{t}: expected to remove {len(chunk)} rows, removed {n}")
            manifest["rows"][t] = rows
        for (t, rid), (col, old, new, gcol, gval) in RENAME.items():
            cur = con.execute(f'SELECT "{col}" FROM "{t}" WHERE id=?', (rid,)).fetchone()[0]
            if cur != new:
                n = con.execute(f'UPDATE "{t}" SET "{col}"=? WHERE id=? AND "{gcol}"=?', (new, rid, gval)).rowcount
                if n != 1:
                    raise Refuse(f"could not change {t} {rid}")
                manifest["renames"].append({"table": t, "id": rid, "column": col, "old": cur, "new": new})
        after = fk_violations(con)
        if after != before:
            raise Refuse(f"foreign-key check changed: {sorted(set(after) - set(before))[:10]}")
        dangling = dangling_undeclared(con, p["gone"])
        if dangling:
            raise Refuse(f"records still point at removed rows: {dangling[:10]}")
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise Refuse("integrity check failed")
        manifest["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        with open(os.path.join(qdir, "manifest.json"), "w") as fh:
            json.dump(manifest, fh, indent=1, sort_keys=True)
        con.execute("COMMIT")
    except BaseException:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        for _src, dst in staged:
            try:
                os.remove(dst)
            except OSError:
                pass
        raise
    for src, _dst in staged:
        os.remove(src)
    con.close()
    print(f"APPLIED plan {p['hash']}: {p['total']} rows removed, {len(staged)} files quarantined, "
          f"{len(manifest['renames'])} renames; manifest {os.path.join(qdir, 'manifest.json')}")
    return p


def _jsonable(v):
    if isinstance(v, bytes):
        return {"base64": base64.b64encode(v).decode()}
    return v


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def scan_files(instance):
    out = []
    for root, dirs, names in os.walk(instance):
        rel_root = os.path.relpath(root, instance)
        if rel_root.split(os.sep)[0] in ("backups",) or rel_root.startswith("cleanup-quarantine-"):
            dirs[:] = []
            continue
        for n in names:
            rel = os.path.normpath(os.path.join(rel_root, n))
            if rel.endswith(".db") or rel.endswith(".db-wal") or rel.endswith(".db-shm"):
                continue
            out.append((rel, os.path.getsize(os.path.join(root, n))))
    return sorted(out)


def read_listing(path):
    out = []
    for line in open(path):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2 and not parts[0].endswith(".db"):
            out.append((parts[0], int(parts[1])))
    return out


# ------------------------------------------------------------------------------------------------ verify
def verify(before_path, after_path):
    b, a = open_db(before_path), open_db(after_path)
    p = plan(b)  # recompute from the untouched copy
    ok = True
    print(f"INTEGRITY={a.execute('PRAGMA integrity_check').fetchone()[0]}")
    vb, va = fk_violations(b), fk_violations(a)
    print(f"FOREIGN_KEYS: before {len(vb)} violation(s), after {len(va)}; same={'yes' if vb == va else 'NO'}")
    ok &= vb == va and a.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    renamed = {(t, i): (col, new) for (t, i), (col, _o, new, _g, _v) in RENAME.items()}
    changed, missing, removed_left = [], [], []
    for t in p["tables"]:
        key = p["pk"][t]
        gone = p["gone"].get(t, set())
        after_rows = {r[0]: tuple(r) for r in a.execute(f'SELECT "{key}", * FROM "{t}"')}
        for r in b.execute(f'SELECT "{key}", * FROM "{t}"'):
            k = r[0]
            if k in gone:
                if k in after_rows:
                    removed_left.append((t, k))
                continue
            if k not in after_rows:
                missing.append((t, k))
                continue
            if tuple(r) != after_rows[k]:
                if (t, k) in renamed:
                    continue
                changed.append((t, k))
    print(f"KEPT_ROWS_MISSING={len(missing)} {missing[:10]}")
    print(f"KEPT_ROWS_CHANGED={len(changed)} {changed[:10]} (allowed: only the listed CHANGES)")
    print(f"REMOVED_ROWS_STILL_PRESENT={len(removed_left)}")
    for (t, i), (col, new) in renamed.items():
        print(f"CHANGED {t} {i} {col}: {a.execute(f'SELECT {col} FROM {t} WHERE id=?', (i,)).fetchone()[0]!r}")
    dangling = dangling_undeclared(a, p["gone"])
    print(f"DANGLING_UNDECLARED_LINKS={len(dangling)}")
    ok &= not missing and not changed and not removed_left and not dangling
    print("VERIFY=" + ("ok" if ok else "FAILED"))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    s = sub.add_parser("plan")
    s.add_argument("--db", default=LIVE_DB)
    s.add_argument("--files")
    s = sub.add_parser("apply")
    s.add_argument("--db", required=True)
    s.add_argument("--instance", required=True)
    s.add_argument("--expect-plan", required=True)
    s.add_argument("--live", action="store_true")
    s.add_argument("--backup")
    s = sub.add_parser("verify")
    s.add_argument("--before", required=True)
    s.add_argument("--after", required=True)
    args = ap.parse_args(argv)
    try:
        if args.mode == "plan":
            con = open_db(args.db)
            listing = read_listing(args.files) if args.files else scan_files(os.path.dirname(args.db))
            report(plan(con, listing))
        elif args.mode == "apply":
            apply(args.db, args.instance, args.expect_plan, live=args.live, backup=args.backup)
        else:
            sys.exit(0 if verify(args.before, args.after) else 1)
    except Refuse as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()

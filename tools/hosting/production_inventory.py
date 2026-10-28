"""CalibraytAI Production cleanup inventory (27 Oct 2026). READ ONLY.

Opens the live SQLite database with SQLite's own read-only mode (``mode=ro``): it cannot write, delete or lock
anything. Prints an inventory for Joel's KEEP / REMOVE / REVIEW decision: every table's row count, every project
with its customer and every record that belongs to it (found by following the database's own foreign keys, so
all tables are covered), customers, people and sign-ins, organizations, suppliers and shared configuration.

Email addresses of real-looking people are shortened (first two letters + domain); synthetic ones (.invalid,
example.com) are printed in full so they can be recognised. No password hashes, tokens or secrets are read out.

Run on the Production instance (Mac Terminal):
  git -C ~/Desktop/Brayman-Estimator show <sha>:tools/hosting/production_inventory.py \
    | ssh srv-...@ssh.virginia.render.com 'cd /opt/render/project/src && python3 - ' > inventory.txt
"""
from __future__ import annotations

import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

DB = os.environ.get("INVENTORY_DB") or (sys.argv[1] if len(sys.argv) > 1 else
                                         "/opt/render/project/src/instance/brayman_estimator.db")
SYNTHETIC = re.compile(r"synthetic|demo|\btest|uat|sample|example|\.invalid|training|fixture|fake|dummy|"
                       r"lorem|placeholder|\bfg-?\d|walkthrough|smoke|e2e|qa\b", re.I)
SECRET_COLUMNS = re.compile(r"password|hash|token|secret|key_material|credential", re.I)


def mask(email):
    if not email:
        return ""
    email = str(email)
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if domain.endswith(".invalid") or domain in {"example.com", "example.org", "example.invalid"}:
        return email
    return f"{local[:2]}***@{domain}"


def flag(*values):
    hits = sorted({m.group(0).lower() for v in values if v for m in SYNTHETIC.finditer(str(v))})
    return ("SYNTHETIC-MARKERS: " + ",".join(hits)) if hits else ""


def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    q = lambda sql, *a: con.execute(sql, a).fetchall()  # noqa: E731
    tables = [r[0] for r in q("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                              "ORDER BY name")]
    cols = {t: [r["name"] for r in q(f'PRAGMA table_info("{t}")')] for t in tables}
    fks = {t: [(r["from"], r["table"], r["to"] or "id") for r in q(f'PRAGMA foreign_key_list("{t}")')]
           for t in tables}
    counts = {t: q(f'SELECT COUNT(*) FROM "{t}"')[0][0] for t in tables}
    rev = q("SELECT version_num FROM alembic_version")
    print("== CalibraytAI Production inventory (read-only)")
    print(f"DATABASE={DB} REVISION={rev[0][0] if rev else '?'} TABLES={len(tables)} ROWS={sum(counts.values())}")

    # ---------------------------------------------------------------- project ownership through foreign keys
    owner = {"projects": {r["id"]: r["id"] for r in q("SELECT id FROM projects")}}
    rows = {}
    for t in tables:
        if t == "projects" or not counts[t]:
            continue
        pk = "id" if "id" in cols[t] else "rowid"
        fkcols = [c for c, _, _ in fks[t]]
        if not fkcols:
            continue
        sel = ", ".join([f'"{pk}" AS __pk'] + [f'"{c}"' for c in fkcols])
        rows[t] = [dict(r) for r in q(f'SELECT {sel} FROM "{t}"')]
    changed = True
    while changed:
        changed = False
        for t, data in rows.items():
            mine = owner.setdefault(t, {})
            for r in data:
                if r["__pk"] in mine:
                    continue
                for c, parent, to in fks[t]:
                    v = r.get(c)
                    if v is None or to != "id":
                        continue
                    p = owner.get(parent, {}).get(v)
                    if p is not None:
                        mine[r["__pk"]] = p
                        changed = True
                        break
    per_project = defaultdict(Counter)
    for t, m in owner.items():
        if t == "projects":
            continue
        for _pk, p in m.items():
            per_project[p][t] += 1
    project_owned_tables = Counter()
    for t, m in owner.items():
        if t != "projects" and m:
            project_owned_tables[t] = len(m)

    # ---------------------------------------------------------------- A. projects
    print("\n== A. PROJECTS")
    clients = {r["id"]: dict(r) for r in q("SELECT * FROM clients")}
    orgs = {r["id"]: dict(r) for r in q("SELECT * FROM organizations")}
    for p in q("SELECT * FROM projects ORDER BY id"):
        p = dict(p)
        c = clients.get(p.get("client_id")) or {}
        org = orgs.get(p.get("organization_id")) or {}
        mark = flag(p.get("name"), p.get("description"), p.get("address"), p.get("project_number"),
                    c.get("name"), c.get("company"), c.get("email"), org.get("display_name"))
        print(f"\n[P{p['id']}] {p.get('project_number') or '-'} | {p['name']}")
        print(f"  org={p.get('organization_id')} ({org.get('display_name', '?')}) status={p.get('status')} "
              f"state={p.get('operating_state')} created={str(p.get('created_at'))[:10]}")
        print(f"  customer=C{c.get('id', '-')} {c.get('name', '-')}"
              f"{' / ' + c['company'] if c.get('company') else ''} {mask(c.get('email'))} | address={p.get('address') or '-'}")
        if mark:
            print(f"  {mark}")
        related = per_project.get(p["id"], Counter())
        print(f"  related records: {sum(related.values())} in {len(related)} tables")
        if related:
            print("    " + ", ".join(f"{t}={n}" for t, n in sorted(related.items())))

    # ---------------------------------------------------------------- B. customers
    print("\n== B. CUSTOMERS (clients)")
    used = Counter(r["client_id"] for r in q("SELECT client_id FROM projects WHERE client_id IS NOT NULL"))
    other_refs = [(t, c) for t in tables for c, parent, _ in fks[t] if parent == "clients" and t != "projects"]
    for c in clients.values():
        refs = sum(q(f'SELECT COUNT(*) FROM "{t}" WHERE "{col}"=?', c["id"])[0][0] for t, col in other_refs)
        mark = flag(c.get("name"), c.get("company"), c.get("email"), c.get("notes"), c.get("address"))
        print(f"C{c['id']} org={c.get('organization_id')} | {c['name']}{' / ' + c['company'] if c.get('company') else ''}"
              f" | {mask(c.get('email'))} | phone={'yes' if c.get('phone') else 'no'} | address={c.get('address') or '-'}"
              f" | projects={used.get(c['id'], 0)} other_refs={refs} | created={str(c.get('created_at'))[:10]}"
              f"{' | ' + mark if mark else ''}")
    for t in tables:
        if t != "clients" and re.search(r"contact|subcontractor|attendee", t) and counts[t]:
            print(f"-- {t}: {counts[t]} rows")
            namecols = [x for x in cols[t] if x in ("name", "display_name", "company", "company_name", "email",
                                                     "trade", "phone_label", "label")]
            if namecols:
                for r in q(f'SELECT id, {", ".join(chr(34) + x + chr(34) for x in namecols)} FROM "{t}" LIMIT 60'):
                    vals = [mask(r[x]) if "email" in x else r[x] for x in namecols]
                    print(f"   {t[:3]}{r['id']}: " + " | ".join(str(v) for v in vals if v)
                          + (" | " + flag(*vals) if flag(*vals) else ""))

    # ---------------------------------------------------------------- C. users and people
    print("\n== C. USERS / PEOPLE")
    mem = defaultdict(list)
    for m in q("SELECT * FROM user_memberships"):
        mem[m["user_id"]].append(dict(m))
    owners = {o["instance_owner_membership_id"]: oid for oid, o in orgs.items() if o.get("instance_owner_membership_id")}
    sysadm = set()
    if "organization_system_administrator_memberships" in tables and counts["organization_system_administrator_memberships"]:
        c2 = cols["organization_system_administrator_memberships"]
        active = " WHERE revoked_at IS NULL" if "revoked_at" in c2 else ""
        mcol = "user_membership_id" if "user_membership_id" in c2 else ("membership_id" if "membership_id" in c2 else None)
        if mcol:
            sysadm = {r[0] for r in q(f'SELECT "{mcol}" FROM organization_system_administrator_memberships{active}')}
    grants = defaultdict(list)
    if "user_membership_access_domain_grants" in tables:
        for g in q("SELECT user_membership_id, domain_key FROM user_membership_access_domain_grants"):
            grants[g[0]].append(g[1])
    sup = defaultdict(list)
    if "supplier_user_memberships" in tables:
        sc = cols["supplier_user_memberships"]
        for s in q("SELECT * FROM supplier_user_memberships"):
            s = dict(s)
            sup[s.get("user_id")].append(f"supplier={s.get('supplier_id')} status={s.get('status')}")
    for u in q("SELECT id, email, display_name, is_active, created_at FROM users ORDER BY id"):
        roles = []
        for m in mem.get(u["id"], []):
            r = f"{m['organization_id']}{'' if m['is_active'] else '(inactive)'}"
            if m["id"] in owners:
                r += ":OWNER"
            if m["id"] in sysadm:
                r += ":SYSADMIN"
            if grants.get(m["id"]):
                r += ":grants=" + "/".join(grants[m["id"]])
            for extra in ("role", "access_level", "field_only", "is_field_only"):
                if extra in m and m[extra] not in (None, 0, False, ""):
                    r += f":{extra}={m[extra]}"
            roles.append(r)
        mark = flag(u["email"], u["display_name"])
        print(f"U{u['id']} {mask(u['email'])} | {u['display_name']} | active={bool(u['is_active'])} | "
              f"memberships={','.join(roles) or 'none (identity only)'} | supplier={';'.join(sup.get(u['id'], [])) or '-'}"
              f" | created={str(u['created_at'])[:10]}{' | ' + mark if mark else ''}")
    for t in ("organization_people", "organization_crews", "organization_crew_members"):
        if t in tables and counts[t]:
            namecols = [x for x in cols[t] if x in ("display_name", "name", "email", "role", "status", "crew_id",
                                                     "organization_person_id", "user_id", "is_active")]
            print(f"-- {t}: {counts[t]} rows")
            for r in q(f'SELECT id, {", ".join(chr(34) + x + chr(34) for x in namecols)} FROM "{t}"'):
                vals = [mask(r[x]) if "email" in x else r[x] for x in namecols]
                print(f"   {r['id']}: " + " | ".join(f"{k}={v}" for k, v in zip(namecols, vals) if v is not None))

    # ---------------------------------------------------------------- organizations
    print("\n== ORGANIZATIONS")
    for o in orgs.values():
        n = sum(q(f'SELECT COUNT(*) FROM "{t}" WHERE organization_id=?', o["id"])[0][0]
                for t in tables if "organization_id" in cols[t])
        print(f"{o['id']} | {o['display_name']} ({o['legal_name']}) | active={bool(o['is_active'])} | "
              f"rows referencing it={n}{' | ' + flag(o['display_name'], o['legal_name']) if flag(o['display_name'], o['legal_name']) else ''}")

    # ---------------------------------------------------------------- D. project-owned data by table
    print("\n== D. PROJECT-OWNED RECORDS BY TABLE (rows that trace back to a project / rows in table)")
    for t, n in sorted(project_owned_tables.items()):
        print(f"{t}: {n}/{counts[t]}")
    print("-- non-empty tables NOT traced to any project (shared or global data; see E):")
    for t in tables:
        if counts[t] and t != "projects" and not project_owned_tables.get(t):
            print(f"{t}: {counts[t]}")

    # ---------------------------------------------------------------- E. shared configuration samples
    print("\n== E. SHARED DATA (names only, for KEEP / REVIEW)")
    for t in tables:
        if not counts[t] or project_owned_tables.get(t) == counts[t] or t in ("users", "clients", "projects",
                                                                              "organizations", "alembic_version"):
            continue
        namecols = [x for x in cols[t] if re.fullmatch(r"(name|display_name|legal_name|code|title|label|"
                                                       r"description|key|slug|policy_name|status|kind)", x)
                    and not SECRET_COLUMNS.search(x)][:4]
        if not namecols:
            continue
        print(f"-- {t} ({counts[t]})")
        for r in q(f'SELECT {", ".join(chr(34) + x + chr(34) for x in namecols)} FROM "{t}" LIMIT 40'):
            vals = [str(r[x])[:80] for x in namecols if r[x] is not None]
            print("   " + " | ".join(vals) + (" | " + flag(*vals) if flag(*vals) else ""))
    print("\n== END (nothing was changed: the database was opened read-only)")


if __name__ == "__main__":
    main()

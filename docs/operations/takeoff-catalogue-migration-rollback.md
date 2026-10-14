# Takeoff catalogue migration — apply and roll back

| Field | Value |
|-------|--------|
| Revision | `u1b2c3d4e5f6` (from `t0a1b2c3d4e5`) |
| Status | **Prepared and rehearsed. Not applied to the Mac office or the hosted database.** |
| Decision | [ADR-057](../adr/ADR-057-takeoff-catalogue-categories-and-derived-identities.md) |

## What it changes

Three CHECK constraints are replaced: `ck_canonical_materials_category` (seven new categories), `ck_canonical_materials_uom` and `ck_material_requirements_uom` (`PKG` added). No row is inserted, changed, or deleted. No table is added.

## Before applying (hosted)

1. Hosted backup with integrity `ok` and the revision `t0a1b2c3d4e5` recorded, as for earlier releases.
2. Second copy on the Mac, checksum matched.
3. Deploy the accepted SHA with auto-deploy off; run `flask db upgrade` once.

## Verify after applying

- `SELECT version_num FROM alembic_version` → `u1b2c3d4e5f6`.
- `PRAGMA integrity_check` → `ok`.
- Row counts and contents of every table unchanged (only `alembic_version` differs).

## Roll back

- **No takeoff identity recorded yet:** `flask db downgrade t0a1b2c3d4e5`. The three constraints return to their earlier rules.
- **Any takeoff identity or `PKG` row exists:** the downgrade refuses with "Restore the pre-migration backup instead." Stop the service, restore the pre-migration backup file, confirm its checksum and integrity, restart, and redeploy the previous SHA. Evidence recorded after the backup must be re-entered from the stored supplier response records (`instance/deck_takeoff/.../responses`), which are kept as files.

## Rehearsal, 13 Oct 2026 (disposable copy of the Mac office mirror)

Source `instance/brayman_estimator.db`, revision `t0a1b2c3d4e5`, SHA-256 `1b4c064d…7276`, 150 tables, 3,627 rows. The copy was made in the Linux workspace; the original was not opened for writing.

| Step | Result |
|---|---|
| Upgrade to `u1b2c3d4e5f6` | Only `alembic_version` changed; every other table's row count and content hash unchanged. Integrity `ok`. |
| Foreign-key check | One pre-existing row: `labour_audit_events` id 16 names `ORG-999`, which does not exist. Present before the upgrade; not caused by it. |
| New category | `CAL-DECK-CAPCOMP-20` (`DECKING`) created; synthetic supplier evidence 76.00 CAD / EA recorded and approved through `record_contractor_cost_approval`. |
| History | All 4 earlier price-evidence rows and the 1 earlier approval unchanged. |
| Downgrade with a takeoff row | Refused with the backup message. |
| Restore the pre-migration backup | Checksum equal to the backup; every table equal to the original. |

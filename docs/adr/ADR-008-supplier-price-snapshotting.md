# ADR-008 — Supplier Price Snapshotting

| Field | Value |
|-------|--------|
| Title | ADR-008: Supplier Price Snapshotting |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [supplier architecture](../architecture/supplier-catalogue-inventory-pricing.md) · [supplier channel](../architecture/supplier-channel-and-launch-partner.md) · [ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md) · [ADR-036](ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** (evidence classes; does **not** accept this ADR) · Rules 3 & 5 |

## Context

Catalogue and API prices change. Estimates, proposals, and future POs must not silently float with supplier refreshes.

## Decision

*(Proposed)* When an estimate (or PO) line adopts a supplier price, persist a **price snapshot** (supplier, SKU, unit price, currency, effective dating, source, retrieved_at). Catalogue refresh updates catalogue only. Locked estimate versions and accepted proposals remain unchanged.

## Alternatives Considered

- Always live-price at PDF time — Rejected for historical integrity.
- Snapshot only at proposal issue — Insufficient; estimate history also needs protection.

## Consequences

Positive: auditability. Negative: storage and “why doesn’t refresh update my bid?” UX education.

## Module Ownership Impact

Supplier module owns catalogue; Estimating/Procurement store snapshots on consumption.

## Data Ownership Impact

Snapshots become part of commercial history.

## Migration Impact

Deferred to Phase E+.

## Testing Impact

Refresh catalogue → draft may optionally re-price; locked/accepted unchanged.

## Documentation Impact

Supplier architecture; Estimating module when wired.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | No implementation in this documentation sprint | |

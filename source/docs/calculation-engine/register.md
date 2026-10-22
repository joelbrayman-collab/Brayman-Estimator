# Calculation Engine Register

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED** |
| Date | 2026-09-26 |
| Contract | V1, pin `2903a45074df21b1c99390cb9aab68638970a2ff` |

| Engine | Status | Engine version | Public page | Contract V1 | Save / Download | Formula verified | Platform-mapping relevance | Next action / notes |
|--------|--------|----------------|-------------|-------------|-----------------|------------------|----------------------------|---------------------|
| Concrete slab | **IMPLEMENTED / LIVE / GOVERNED** | `1.0.0` | `/useful-tools/concrete/` | Conformant | Implemented / Implemented | Approved fixtures reproduced with pinned fingerprints | Yes — quantities are intended for later reviewed estimate mapping | Public modes are `standard` and `thickened_edge` only. See [authority record](concrete-authority.md) and [formula record](concrete-slab-1.0.0.md). |
| ICF wall | **NOT STARTED** | — | Not built | Expected to use `product_specification` | No / No | No | Yes — after a real manufacturer/system is governed | Select and verify the first supported product system before specification. |
| Stair | **EXISTING PUBLIC-PROGRAMME PROTOTYPE / NOT LIVE** | Not established | Private review only | Not yet assessed | Save specified in prototype / Download not implemented | Geometry/profile tests exist outside this specification package | To be determined; do not force estimate mapping | Establish engine identity/version and mapping relevance before Contract V1 alignment. |
| Wall framing | **ROADMAP / NOT STARTED** | — | Not built | Not assessed | No / No | No | Potentially relevant | Await explicit product authorization. |
| Drywall | **ROADMAP / NOT STARTED** | — | Not built | Not assessed | No / No | No | Potentially relevant | Await explicit product authorization. |
| Roofing | **ROADMAP / NOT STARTED** | — | Not built | Not assessed | No / No | No | Potentially relevant | Await explicit product authorization. |
| Flooring | **ROADMAP / NOT STARTED** | — | Not built | Not assessed | No / No | No | Potentially relevant | Await explicit product authorization. |

Rules:

- One row is one engine version. A formula change is a new `engine_version`, not a silent edit of `1.0.0`.
- `engine_version` is the calculation version. `contract_version` stays `"1"` until the envelope itself changes.
- A result with `engine_version` `"0"` is the pinned illustrative example. It is not `1.0.0`.
- This register preserves the seven-engine governed roadmap. A roadmap row does not authorize specification or implementation.

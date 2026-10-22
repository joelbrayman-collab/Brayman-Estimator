# Contract V1 validation

| Attribute | Value |
|-----------|--------|
| Status | **VALIDATED** |
| Date | 2026-09-26 |
| Checker | Platform file `app/services/calculation_result_contract.py` at pin `2903a45074df21b1c99390cb9aab68638970a2ff`, loaded by file path |
| Platform tree | Not modified. Flask app not imported. |

The checker is the pinned `validate_contract_v1` and `calculation_fingerprint` functions. The Website repository does not depend on that module at runtime.

## Mirror

| File | SHA-256 match to pin | `validate_contract_v1` |
|------|----------------------|------------------------|
| `calculation-engine-result-contract-v1.md` | Yes. `2738e3beff4102f2ab7110ec1527ec05535013a1a868a306e968ef2cab833e27` | Not a payload |
| `fixtures/thickened-edge-slab.example.json` | Yes | No errors. Fingerprint `aabd2126e55440a68ad20ac187350273cfa428d1d664378ce7ed8a57e7559862` |
| `fixtures/icf-wall.example.json` | Yes | No errors. Fingerprint `f0141efc2a13a41f37a1c369a4b84366cfbd7e15408925855cd572f367d48643` |
| `fixtures/invalid-missing-engine-version.example.json` | Yes | `missing engine_version` |
| `fixtures/invalid-missing-unit.example.json` | Yes | `quantities[0] needs a V1 quantity unit` |

The valid illustrative slab fixture remains valid. Its `engine_version` is `"0"` and its `thickened_edge_concrete` quantity is `"1"`. Those values are not the `concrete_slab` `1.0.0` formula. See the shared notes.

## Engine 1.0.0 payloads

Each file under `fixtures/concrete-slab-1.0.0/` except `manifest.json` passed `validate_contract_v1` with no errors. Fingerprints are in that manifest. They were computed with the pinned fingerprint function.

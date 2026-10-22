# Calculation Engine Programme Charter

| Attribute | Value |
|-----------|--------|
| Status | **SPECIFICATION RECORDED / NOT IMPLEMENTED / NOT PUBLISHED** |
| Date | 2026-09-26 |
| Repository | Website. This charter does not govern the Contractor Platform. |
| First engine | `concrete_slab` version `1.0.0` |
| Live site | `https://calibai.joel-brayman.chatgpt.site/` is not changed by this charter. |

## Purpose

The Website owns public calculation engines. A person can enter measurements, receive a versioned quantity result, read a professional summary, save it on the device, and download it. No account is required.

The Contractor Platform may later accept a downloaded result. It does not own the public calculator, and it does not calculate.

## Authority

The quantity envelope is Calculation Engine Result Contract V1, pinned in the Platform repository at `2903a45074df21b1c99390cb9aab68638970a2ff`.

The Website mirror is a copy for local specification. It is not a second contract. If the mirror and the pin differ, the pin wins.

This programme does not redefine or extend that contract. A gap in the contract is recorded as a shared architecture note.

## Ownership

The engine owns inputs, assumptions, the deterministic calculation, the structured result, and `engine_version`.

The engine does not own company identity, cost items, assemblies, labour rates, margin, sell price, proposal price, estimate identity, or Platform workflow.

The Website owns the public page, the engine, the summary, save on this device, and download.

The Platform owns any later human review, mapping, pricing, estimate, and project save. Those actions are outside this charter.

## Sequence

1. Specify `concrete_slab` `1.0.0` with variants `standard` and `thickened_edge`.
2. Stop. Do not implement the page in the specification phase.
3. A later authorization may implement that engine and its Website consumer.
4. ICF is not started.
5. Platform mapping, pricing, estimates, persistence, and workflow are not started.

## Boundaries

- No runtime call between the Website and the Platform.
- No shared database.
- No Platform sign-in on a public calculator.
- No company price in a public result.
- No lead form, email, or phone number on the calculation.
- Employment versus entrepreneurship is a separate parked tool. It does not use this contract.

## Names

Programme language may say STANDARD and THICKENED_EDGE. Contract V1 payloads use the strings `standard` and `thickened_edge`. The payload strings are the ones that validate.

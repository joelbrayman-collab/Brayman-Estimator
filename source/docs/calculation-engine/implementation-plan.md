# Implementation plan

| Attribute | Value |
|-----------|--------|
| Status | **PREPARED / NOT STARTED** |
| Date | 2026-09-26 |
| This phase | Specification, formula record, register, and this plan. Complete at the stop line below. |

## Later Website work, when separately authorized

1. Add a pure calculation module in this Website repository for `concrete_slab` `1.0.0` only. Decimal arithmetic. No network call.
2. Check that module against `fixtures/concrete-slab-1.0.0/`. The manifest fingerprints must match. Rejected inputs must not produce a payload.
3. Add the public consumer: optional project or reference name, Calculation Summary, Save on This Device, and Download Calculation, as specified in [website-consumer.md](website-consumer.md).
4. Keep the downloaded file in the handoff shape from [platform-handoff.md](platform-handoff.md).

## Not part of that later slice unless a new authorization says so

- Publishing or editing `https://calibai.joel-brayman.chatgpt.site/`.
- ICF or any engine other than `concrete_slab` `1.0.0`.
- Platform mapping, pricing, estimates, persistence, or workflow.
- A shared code package between the two repositories.
- A change to Contract V1. Gaps stay in [shared-architecture-notes.md](shared-architecture-notes.md).

## Stop

Specification of `concrete_slab` `1.0.0` is recorded. Implementation has not started. The live Website is unchanged.

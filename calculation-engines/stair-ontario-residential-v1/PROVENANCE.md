# Ontario residential stair provenance

This folder preserves the original Website stair calculator. It is the calculation and diagram authority for the contractor office page. Do not edit the formula files. Do not replace them with a Python copy or a drawing from a job file.

| Fact | Value |
|------|--------|
| Website project | `appgprj_6a9095543b74819186183f9a522890e5` |
| Website version | 31 |
| Source SHA | `5dcb4f2b9cc0a291a16375f06ce89f09a02262cf` |
| Recorded deployment | `appgdep_6abd379bbb8081918aae3b170706263b` |
| Archive | `calibraytai-website-v31-concrete-stair-source-recovery.zip` |
| Archive SHA-256 | `c991ee6418da69a134a615a77dfa403b914cb2f90537a64c8c9896093eacc240` |
| Engine | `website-source/lib/useful-tools/stairs.mjs` |
| Engine SHA-256 | `b14e5c718ca2608f941e93f5829a56f3915cf0f61377d382f81cdb0dc23828d6` |
| Units SHA-256 | `f24960c6c5202be6d9334593cfca791bc48eccf79e2399c476fbeca01fee2686` |
| Profile SHA-256 | `b510265cfc1bc70b45d754fdc8751c414c52fa184a9fe187cc4c318654dd4b76` |
| Diagram geometry SHA-256 | `dbf5957f9e1a45de33f9afa2a566a7fadd36431c73acf47e45d2bf4b1110a74c` |
| Calculator SHA-256 | `befe63f2b756d90f927a4c01c20ebdb953656886bd2ca0770aefbe7c35d96598` |
| Diagram SHA-256 | `a1810e14a9c1cc72b72051805a7ecbe770af3bfc100afe57f41765cdc9cc5775` |
| Profile | `ontario-residential-v1` |
| Office runtime | The browser loads `app/static/js/stair-calculator.js`, a build of the preserved React calculator. The office does not call the public Website and does not write an estimate. |

The result is stair geometry and profile checks. It is not a Contract V1 envelope. Width and tread thickness are recorded for the diagram label. The profile evaluates rise and run.

The recovered conformance script also calls the dormant concrete prototype. That prototype is not copied here. The stair fixture loop is run by `tests/stair-conformance.mjs`.

# QCAD Professional crew-drawing proof

5 Oct 2026. Slice 24. Generic fixture only: `post-1`, `beam-front`, `joist-1`.

**QCAD PROFESSIONAL PROOF FAILED VISUAL ACCEPTANCE.**

QCAD is not adopted. The trial is not a product install. The adapter under `tools/qcad_proof/` is proof-only. It is not imported by the application. Nothing was deployed. V1 was not rescored.

## Environment

| Item | Record |
|------|--------|
| Product | QCAD Professional 3.33.1 trial, Qt 6, Apple Silicon |
| Bundle revision | `897079c2d11aaa0869f839a6cf5df8a937dbddbe` |
| Disk image | `qcad-3.33.1-trial-macos-13-26-qt6-arm64.dmg` |
| SHA-256 | `e5640499d3d790b34fccc1180b39b3e213bd13255555003701eb316b4ac94a45` |
| Host | macOS, display platform `cocoa` |
| Offscreen | The bundle does not ship a Qt `offscreen` plugin. `-platform offscreen` cannot start. |
| Execution | `QCAD -no-gui -allow-multiple-instances -exec` then `dwg2pdf` |
| Scripting | ECMAScript |
| Input | JSON specification from the generic fixture |
| Output | DXF, then a named layout PDF |
| Unattended | Yes, on this desktop session, after a 15-second trial wait. The process does not quit on its own after export. The runner stops it once the DXF is written. |
| License | Trial only. The scalable server license was not purchased. |

Professional trial plugins loaded, including `dwg2pdf`. Removing the trial add-on was not done. Community Edition was not installed.

## What the sheet is

One 17 × 11 inch landscape page, MediaBox 1224 × 792 points. Layout name `S-1`. Four paper-space viewports. Title block from the fixture sheet fields. Plan, elevation, section, and a `POST_BEAM_DETAIL` block when `rel-bear-post-1-beam-front` is present.

Dimensions are QCAD dimension entities measured from model points. The sheet shows `10'-0"` for the beam, `10'-0"` for the joist, `1'-11"` for the post, and `3"` for the stored bearing. The adapter does not type those strings.

## Why it failed

The sheet would not be handed to the crew.

The trial stamps `QCAD Trial Version` and `qcad.org` across the page. A plot without that stamp was not available inside the proof limit. The stamp alone blocks delivery.

Under the stamp, the construction graphic is still rectangles in large empty viewports.

- The plan draws the three profiles. At the sheet scale they read as thin bars, with empty paper above them.
- The elevation shows the post, the beam, and the joist at the stored elevations, with the post-height dimension and the stored `supports` callout. It is three rectangles.
- The section has `ANSI31` hatch entities in the DXF. On the plotted sheet those hatches do not read. The view is open rectangles and blank paper. It is not a construction section.
- The post/beam detail is a block. It is still two rectangles, a `3"` dimension, a solid bar for the supplied 1/4 inch plate, and two bolt circles. The supplied bolt diameter is larger than the supplied plate thickness, and the sheet says so. That is not a connection a crew can build from.

The title block, the layout, the dimension style, the leaders, the block, and the refusal sentence are ahead of the ReportLab, FreeCAD, and OpenCASCADE sheets. The graphic the crew would use is not. This proof does not clear those four failures.

## No-guessing

Case A keeps `rel-bear-post-1-beam-front`. The detail block is created.

Case B removes that relationship. The DXF has no `POST_BEAM_DETAIL` block. The detail viewport says `You need to provide this information.` The joist `supports` relationship is a different fact and is not used as a substitute bearing.

The joist hanger named on `connection-beam-joist` has no connector geometry. The elevation says connector geometry is not supplied. No hanger was drawn.

## Determinism

Two exports from the same specification. PDF bytes differ. The only differences are the PDF creation, modification, and XMP timestamps. Rasters of the two pages at 40 dpi are identical.

## Files

- [sheet.pdf](sheet.pdf) — case A, first plot
- [sheet-run-2.pdf](sheet-run-2.pdf) — case A, second plot
- [case-b.pdf](case-b.pdf) — bearing removed
- [sheet.png](sheet.png), [section.png](section.png), [detail.png](detail.png) — the inspected page

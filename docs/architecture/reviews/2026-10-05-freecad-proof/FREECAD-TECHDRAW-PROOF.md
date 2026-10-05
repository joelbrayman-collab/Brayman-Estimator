# FreeCAD TechDraw proof — 5 Oct 2026

| Field | Record |
|-------|--------|
| Result | **FAILED visual acceptance.** Not adopted. |
| Engine | FreeCAD 1.0.2, revision 39319. macOS arm64 conda disk image. SHA-256 `2fde16da356b62cfce656cd12effaa79f97f2f28a71f1520dd90fabb88f9d3fd`. |
| Process | `FreeCAD.app` out of process. Not imported by Flask. Not installed in the application virtual environment. |
| Offscreen | `QT_QPA_PLATFORM=offscreen` exits 139 on this Mac. The PDF was exported on the native display. |
| Model | Generic complete-deck fixture members `post-1`, `beam-front`, and `joist-1`. Not Bushel. |
| Sheet | `run-1.pdf`. MediaBox 1224 × 792 points, which is 17 × 11 inches. |
| Second run | `run-2.pdf` is the same length and is not byte-identical. The creation timestamps differ. Removing that timestamp still leaves other byte differences. |

## What the sheet shows

The plan reads as a line, not a member profile. The front elevation is two rectangles, the same visual character as the ReportLab post-and-beam sheet. The section is a line. It has no visible hatch and no cut-line hierarchy. The post/beam title sits away from a composed detail. The connector note is not readable. The lower half of the sheet is blank. The title block is not a readable construction title block.

Would we hand this detail to the boys? No.

## Bushel facts still missing

The proving fixture does not contain post locations, beam coordinates, joist lengths, joist elevations, or a post-beam-joist relationship. Those facts were not invented. This sheet does not prove Bushel.

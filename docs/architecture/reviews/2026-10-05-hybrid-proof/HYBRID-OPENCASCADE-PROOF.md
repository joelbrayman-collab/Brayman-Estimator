# Hybrid OpenCASCADE proof — 5 Oct 2026

| Field | Record |
|-------|--------|
| Result | **FAILED visual acceptance.** The hybrid architecture is not proven. |
| Projection | CadQuery 2.8.0 on Python 3.13, OpenCASCADE (OCP) 7.9.3.1, in a side virtual environment. No Qt. No FreeCAD. Not installed in the application virtual environment. |
| Process | The projection ran as a separate Python process. Flask did not import OpenCASCADE. |
| Model | Generic complete-deck fixture members `post-1`, `beam-front`, and `joist-1`. Not Bushel. |
| Sheet | `sheet.pdf`. MediaBox 1224 × 792 points, which is 17 × 11 inches. |
| Pipeline | The projection and compositor were not kept. This PDF is the evidence. |

## What the sheet shows

The plan shows the post as a rectangle, the beam as a narrow pair of lines, and the joist as a narrow pair of lines, with section marks. The front elevation stacks the post, the beam, and the joist. Section A hatches the cut post, the cut beam, and the cut joist. That hatch is a real difference from the ReportLab sheets and from the FreeCAD proof.

The post/beam detail does not explain the connection. The post cap is a line. The two bolts are dots. The post name sits on the post. Each view still has a large empty field. The title block, the notes, and the 3 inch bearing dimension are present.

Would we hand this sheet to the boys? No.

## What failed

- The detail does not show a readable plate or readable bolts.
- Member names collide with the linework.
- The plan and the elevation still leave most of the viewport empty.
- A quarter-inch thickness has to be drawn as a fraction. An early sheet rounded it to 0 inches. The inspected sheet names the plate as 1/4 inch, and the geometry of that plate is still a line.

## What the session tests showed before the pipeline was removed

The specification matched the model. Removing `rel-bear-post-1-beam-front` refused the detail. Removing the beam-to-joist `supports` relationship refused that note. The section cut faces matched the stored post width, beam depth, and joist profile. The PDF MediaBox was 17 × 11 inches. Those checks are not in the product, because the sheet failed the visual gate.

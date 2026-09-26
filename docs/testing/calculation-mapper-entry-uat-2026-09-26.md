# Calculation mapper — contractor entry UAT

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-26 |
| Status | Joel stopped before mapping. Entry experience corrected. Joel has not yet reviewed the correction. |
| Estimate used | Synthetic `EST-2026-0018`, version 33, on the hosted validation office |

## Finding

Joel reached the estimate prepared for mapper UAT. He stopped and said: "I see the page but am confused at what it is all about."

That is a product finding. The page asked for a calculation file before it explained the job.

## What the ordinary page does now

Add from calculation explains that a CalibraytAI calculation works out project quantities and that only confirmed quantities are added to the estimate. It does not ask for a file. It does not show a calculator button, because no production engine is connected.

## What stays available for a controlled test

`/estimates/<id>/versions/<version_id>/calculations/test-load` accepts a test calculation file. It says the page is for testing and is not part of normal estimating. It is not linked from Add from calculation.

## Not this test

Do not judge slab or ICF mathematics. Do not paste a test file as the normal way through the estimate. Calculator formulas, Labour, and Website work were not part of this correction.

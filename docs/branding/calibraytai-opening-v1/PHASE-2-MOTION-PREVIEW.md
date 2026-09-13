# CalibraytAI Opening V1 — Phase 2 Motion Preview

| Attribute | Value |
|-----------|--------|
| Status | **PHASE 2 PASS 2 APPROVED (Joel, 2026-09-13)** |
| Version | Opening V1 |
| Date | 2026-09-13 |
| Product | CalibraytAI |
| Phase | 2 of 4 (compressed timing preview only) |

## STOP

Joel approved Phase 2 Pass 2 on 2026-09-13: *“It's good for now — let's deploy and move on.”*

Frame F is **immutable** for Opening V1:

`docs/branding/calibraytai-opening-v1/storyboard/frame-f-completed-house-master-v1-approved.png`

SHA-256 `e73c121be02198bdc8e5e70a786b4f8f56b3fa234720b68669c79c2def54ab7b` (byte-identical to the Phase 1 candidate). Do not regenerate a different house.

## Preview file

| Field | Value |
|-------|--------|
| Path | `/Users/joelbrayman/Desktop/Brayman-Estimator/docs/branding/calibraytai-opening-v1/phase-2/opening-v1-phase-2-motion-preview.mp4` |
| Format | H.264 MP4, yuv420p, **no audio** |
| Size | 1280×720 (16:9) — compressed preview, **not** the HQ 1920×1080 master |
| Duration | **7.000 s** |
| Frame rate | 30 fps (210 frames) |
| File size | 2,446,065 bytes (~2.3 MiB) |
| SHA-256 | `ad5121c32985d4b72a9927bbec9b9e188bf45f13b06899f4d967047291d9a17e` |
| Composition | `phase-2/compose_motion_preview.py` (pass 2: long cosine dissolves, one camera) |
| Pass 1 preserved | `phase-2/opening-v1-phase-2-motion-preview-pass1.mp4` SHA-256 `63e692c173f077f33966928ef153106dae1a7a0f0f15e91e3fbfc10081f82d7d` |

## Exact timeline (pass 2)

Joel asked for less jerk and much softer still-to-still transitions. Pass 2 keeps the same stills and 7.0s length.

| Time | Content |
|------|---------|
| 0.00–0.45s | Frame A |
| 0.45–1.40s | Soft dissolve A→B (0.95s) |
| 1.40–1.55s | Frame B |
| 1.55–2.50s | Soft dissolve B→C (0.95s) |
| 2.50–2.60s | Frame C |
| 2.60–3.55s | Soft dissolve C→D (0.95s) |
| 3.55–3.65s | Frame D |
| 3.65–4.60s | Soft dissolve D→E (0.95s) |
| 4.60–4.70s | Frame E |
| 4.70–5.70s | Soft dissolve E→F (1.00s) |
| 5.70–5.90s | Frame F completed house (**approved master**) |
| 5.90–6.85s | Soft dissolve F→G (0.95s) |
| 6.85–7.00s | Frame G approved V1 logo; no slogan |

Camera is one slow pull-out (zoom 1.08→1.00) shared by both plates in every dissolve, so zoom does not reset per still. Mid-dissolve uses a light optical blur. Gold wash is weaker than pass 1.

## What this preview is

A **timing and sequence** preview built from the approved Phase 1 stills. Pass 2 uses ~0.95s cosine dissolves, one continuous camera, and a light mid-fade blur.

## What this preview is not

- Not the HQ continuous 3D construction composition.
- Not web delivery media.
- Not application-ingested.
- Crossfades **do not** satisfy the final production rule that the house must assemble continuously. Phase 3 must replace still-to-still dissolves with a true build (blueprint wall → foundation wall → framed wall → finished wall) from the locked Frame F.

## Continuity notes

- F→G is the same plate: approved V1 logo composited over Frame F. That transition is legitimate.
- A (overhead plan) vs C–G (3/4 exterior) still changes viewing orientation once, as specified.
- Residual still drift from Phase 1 remains visible during B/C/E fades (busier plan; simpler foundation rectangle; warmer sheathing).

## Not in this phase

HQ master, web MP4, WebM, `static/opening/` ingest, startup tests, Product UAT, deploy.

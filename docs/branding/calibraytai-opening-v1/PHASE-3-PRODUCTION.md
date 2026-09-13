# CalibraytAI Opening V1 — Phase 3 production + ingest

| Attribute | Value |
|-----------|--------|
| Status | **INGESTED / LOCALLY OPERATIONAL** |
| Date | 2026-09-13 |
| Product | CalibraytAI |
| Phase | 3 of 4 (HQ media + application ingest) |

## Approval

Joel approved Phase 2 Pass 2 on 2026-09-13: *“It's good for now — let's deploy and move on.”*

Locked Frame F SHA-256 `e73c121be02198bdc8e5e70a786b4f8f56b3fa234720b68669c79c2def54ab7b` (not regenerated).

Phase 2 Pass 2 SHA-256 `ad5121c32985d4b72a9927bbec9b9e188bf45f13b06899f4d967047291d9a17e` (preserved). Pass 1 preserved.

## Production approach

HQ is **not** an upscaled copy of the Phase 2 still-dissolve preview.

After the overhead blueprint, construction plates were generated on the **locked Frame F camera** (same 3/4 house: garage right, porch left). Sequence:

blueprint → 3/4 layout footprint → foundation (including garage volume) → wood framing → envelope → **locked Frame F** → V1 logo composite on Frame F.

Pacing matches Pass 2: ~0.95–1.0s cosine dissolves, one slow camera pull, light mid-fade blur, 7.000s, silent. Frame G is composited from upscaled Frame F + approved V1 PNG (not a redrawn mark). No narrative title cards. No new tagline.

Residual interpolation between construction plates remains; Joel instructed not to start another subjective polish cycle.

## Final media

| Asset | Path | SHA-256 |
|-------|------|---------|
| HQ MP4 1920×1080 | `docs/branding/calibraytai-opening-v1/phase-3/opening-v1-hq.mp4` | `4ea4f6f265c1b8a3fff44dacda051ae0dfa7da596d7d3deec34b0bdc8defbe83` |
| Web MP4 1280×720 | `docs/branding/calibraytai-opening-v1/phase-3/opening-v1-web.mp4` | `89cc657b48a8c074d6464b0194c2b7e041acb6f7847156e0342b47ecfc303c07` |
| WebM 1280×720 VP9 yuv420p | `docs/branding/calibraytai-opening-v1/phase-3/opening-v1-web.webm` | `b0ee195386a45421624b3764e757e08f3306d34526151aaab3d5f97f4d352fc0` |
| Contact sheet | `docs/branding/calibraytai-opening-v1/phase-3/contact-sheet-phase-3.jpg` | `4570af47300e7a24e52ba1a7cb36931b4d6612380b645a6f32bb6dc8e481c19d` |
| Manifest | `docs/branding/calibraytai-opening-v1/phase-3/manifest.json` | — |
| Editable composition | `docs/branding/calibraytai-opening-v1/phase-3/compose_hq.py` | — |

HQ is **not** served to browsers.

## Application ingest

`app/static/opening/v1/`

- `opening-v1-web.mp4` (same SHA as web MP4)
- `opening-v1-web.webm` (same SHA as WebM)
- `opening-v1-poster.jpg`
- `opening-v1-reduced-motion.jpg` (locked house still)

Playback: JS-injected overlay on unauthenticated `/login` only. Login form is in the HTML without the overlay (no-JS fail-open). Skip, Escape, `prefers-reduced-motion` bypass, media/play/timeout fail-open. Session no-replay. 7-day `localStorage` suppression. Authenticated navigation never mounts the controller.

Website integration: **MEDIA AVAILABLE / WEBSITE INTEGRATION SEPARATE**. Do not publish the public website from this repository.

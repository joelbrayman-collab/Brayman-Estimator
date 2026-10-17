# Cal — approved assistant identity (frozen)

**Owner approval:** 17 October 2026. **Status:** FROZEN / approved visual master. Do not redesign, regenerate, restyle or substitute without Joel's explicit approval.

## Exact approved image

- Filename: `Cal_Assistant_Approved_Identity_2026-10-17.png`
- SHA-256: `d8857f1bfef06c709390e8eaedfe437aea49983236c79843ee7845d561617e87`
- Origin: final accepted Cal emblem generated in the ChatGPT conversation on 17 October 2026, after removing the unnecessary dividing seam in the tape-measure section.
- **Binary asset pending repository import:** This documentation commit records the frozen design and checksum; the PNG must be copied unchanged from the provided ChatGPT download into `app/static/img/cal-assistant/Cal_Assistant_Approved_Identity_2026-10-17.png` by the implementation agent and checksum-verified. Do not claim the image is committed until it is.

## Visual requirements

- Name: **Cal**; identity: **Your CalibraytAI Assistant**.
- Brushed navy/charcoal and gold circular C.
- Small lowercase navy a inside the C.
- The inner gold band of the C is a **single continuous curved measuring tape** with black measurement ticks; **no blue/black dividing seam or break at the lower left**.
- The hammer is integrated at the right, with its handle forming a straight, rectangular, gold-beveled **capital L** with navy fill. Keep the foot flush within the overall circular badge proportions.
- Premium metallic 3D lighting, bevels and textures; white background in the approved source.
- Preserve all approved proportions, layout, finishes and letterforms. No further image generation or creative reinterpretation.

## Intended usage

Cal is the unobtrusive, one-click help assistant for the CalibraytAI contractor office and phone app. The icon remains out of the way until summoned; future features are Find it, Understand it, Get it done. Implementation and authorization are separate; this design approval does not enable AI access, change security, or authorize production deployment.

## Acceptance

Once the PNG is imported, verify its SHA-256 against the above master and render it at desktop header, mobile header, and assistant-panel sizes. Derivative sizes may be produced from the frozen source without modifying its design. Record each derivative separately. No product code or deployment is authorized by this document.

## Derivatives (recorded 17 Oct 2026, Cal Phase 1 — Find It)

Master in the repository: `app/static/branding/Cal_Assistant_Approved_Identity_2026-10-17.png`, SHA-256 verified as `d8857f1bfef06c709390e8eaedfe437aea49983236c79843ee7845d561617e87` (also asserted by `tests/test_cal_find_it.py`). Each derivative is a proportional Lanczos resize of that master. Nothing is redrawn, recoloured or cropped.

| File | Pixels | Used for | SHA-256 |
|---|---|---|---|
| `app/static/img/cal-assistant/cal-64.png` | 64 × 61 | header icon (26 px wide) and panel head (40 px), 1× screens | `0b10a30a284877f117fd933f8126cf68155d89591f90117b6db4b2043f92ef3d` |
| `app/static/img/cal-assistant/cal-128.png` | 128 × 123 | the same places on 2× / 3× screens (`srcset`) | `b524454d8d3defe55d7b24728fe41ed45c5ab3121d7a5f1a63ef8e94505ad4bf` |

The white background of the approved source is blended into the header with CSS `mix-blend-mode: multiply`; the image file itself is unchanged.

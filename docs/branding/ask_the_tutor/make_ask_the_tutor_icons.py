"""Build the brand-coloured 'Ask the Tutor' icons from Joel's approved master (23 Oct 2026).

The master's shape, cap, tassel, ring and two-line wording are kept pixel for pixel.  Only the colour
of the blue family and the gold tassel is mapped, by darkness, so every highlight and shadow of the
master survives.  Transparency outside the circle is untouched (nothing is added behind it).

Brand colours are the ones in each platform's own code:
  AiRIA        static/css/airia_shell.css  --airia-sidebar-navy #1a3654, --airia-sidebar-navy-deep #122a43,
               --airia-brand-gold #c9a84c
  CalibraytAI  app/static/css/app.css      --gold #c79a2b, --gold-soft #e8d7a8, --black #141414,
               --sidebar #17191d

Usage: python3 docs/branding/ask_the_tutor/make_ask_the_tutor_icons.py MASTER.png OUT_DIR PLATFORM   (airia | calibraytai)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

WHITE = (255, 255, 255)


def _hex(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


PLATFORMS = {
    "airia": {
        # darkness (0 = white .. 1 = black) -> colour, linear between points
        "ring": [(0.0, WHITE), (0.58, _hex("#1a3654")), (0.86, _hex("#122a43")), (1.0, _hex("#122a43"))],
        "cap": [(0.0, WHITE), (0.58, _hex("#1a3654")), (0.86, _hex("#122a43")), (1.0, _hex("#122a43"))],
        "ask": [(0.0, WHITE), (0.58, _hex("#1a3654")), (0.86, _hex("#122a43")), (1.0, _hex("#122a43"))],
        "tutor": [(0.0, WHITE), (0.58, _hex("#1a3654")), (0.86, _hex("#122a43")), (1.0, _hex("#122a43"))],
        "gold": [(0.0, WHITE), (0.11, _mix(_hex("#c9a84c"), WHITE, 0.45)), (0.26, _hex("#c9a84c")),
                 (0.52, _mix(_hex("#c9a84c"), (0, 0, 0), 0.25)), (1.0, _mix(_hex("#c9a84c"), (0, 0, 0), 0.25))],
    },
    "calibraytai": {
        "ring": [(0.0, WHITE), (0.45, _hex("#e8d7a8")), (0.61, _hex("#c79a2b")),
                 (0.82, _mix(_hex("#c79a2b"), (0, 0, 0), 0.25)), (1.0, _mix(_hex("#c79a2b"), (0, 0, 0), 0.25))],
        "cap": [(0.0, WHITE), (0.5, _mix(_hex("#17191d"), WHITE, 0.45)), (0.76, _hex("#17191d")),
                (0.90, _hex("#141414")), (1.0, _hex("#141414"))],
        "ask": [(0.0, WHITE), (0.5, _mix(_hex("#141414"), WHITE, 0.45)), (0.76, _hex("#17191d")),
                (0.89, _hex("#141414")), (1.0, _hex("#141414"))],
        "tutor": [(0.0, WHITE), (0.45, _hex("#e8d7a8")), (0.68, _hex("#c79a2b")),
                  (0.86, _mix(_hex("#c79a2b"), (0, 0, 0), 0.25)), (1.0, _mix(_hex("#c79a2b"), (0, 0, 0), 0.25))],
        "gold": [(0.0, WHITE), (0.11, _hex("#e8d7a8")), (0.26, _hex("#c79a2b")),
                 (0.52, _mix(_hex("#c79a2b"), (0, 0, 0), 0.25)), (1.0, _mix(_hex("#c79a2b"), (0, 0, 0), 0.25))],
    },
}


def _ramp(d, points):
    xs = [p[0] for p in points]
    out = np.zeros(d.shape + (3,), dtype=float)
    for c in range(3):
        out[..., c] = np.interp(d, xs, [p[1][c] for p in points])
    return out


def recolour(master: Image.Image, platform: str) -> Image.Image:
    ramps = PLATFORMS[platform]
    arr = np.array(master.convert("RGBA")).astype(float)
    rgb, alpha = arr[..., :3] / 255.0, arr[..., 3]
    h, w = alpha.shape
    mx, mn = rgb.max(2), rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # hue in 0..1
    delta = np.maximum(mx - mn, 1e-9)
    hue = np.where(mx == r, ((g - b) / delta) % 6, np.where(mx == g, (b - r) / delta + 2, (r - g) / delta + 4)) / 6
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    dark = 1 - luma
    yy, xx = np.mgrid[0:h, 0:w]
    cx = cy = (w - 1) / 2
    dist = np.hypot(xx - cx, yy - cy)
    blue = (sat > 0.04) & (hue >= 0.5) & (hue <= 0.75)
    gold = (sat > 0.05) & (hue >= 0.07) & (hue <= 0.18)
    # Regions of the master: ring, cap (above the wording), "Ask the", "Tutor".
    ring_m = blue & (dist > 535)
    cap_m = blue & (dist <= 535) & (yy < 722)
    ask_m = blue & (dist <= 535) & (yy >= 722) & (yy < 862)
    tut_m = blue & (dist <= 535) & (yy >= 862)
    out = rgb * 255.0
    for mask, key in ((ring_m, "ring"), (cap_m, "cap"), (ask_m, "ask"), (tut_m, "tutor"), (gold, "gold")):
        if mask.any():
            out[mask] = _ramp(dark[mask], ramps[key])
    out = np.clip(out, 0, 255)
    # The master's white interior is alpha 250-254; make it fully opaque so it does not show through
    # on a dark page.  Outside the circle alpha is untouched (0 stays 0, antialiased edge stays partial).
    alpha = np.where(alpha >= 248, 255, alpha)
    out[alpha == 0] = 0
    res = np.dstack([out, alpha]).round().astype(np.uint8)
    return Image.fromarray(res, "RGBA")


def export(img: Image.Image, out_dir: Path, name: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    full = out_dir / f"{name}.png"
    img.save(full, optimize=True)
    paths.append(full)
    for size in (512, 192, 96, 48):
        small = img.convert("RGBa").resize((size, size), Image.LANCZOS).convert("RGBA")
        p = out_dir / f"{name}-{size}.png"
        small.save(p, optimize=True)
        paths.append(p)
    return paths


if __name__ == "__main__":
    master_path, out, platform = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    master = Image.open(master_path)
    res = recolour(master, platform)
    for p in export(res, out, f"ask-the-tutor-{platform}"):
        print(p)

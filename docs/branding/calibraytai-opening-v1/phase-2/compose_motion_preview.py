#!/usr/bin/env python3
"""Phase 2 timing preview from approved Opening V1 stills.

Pass 2: longer cosine dissolves, one continuous camera, mid-fade optical blur.
Does not regenerate Frame F. Still a stills-derived preview, not HQ 3D assembly.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
STORYBOARD = ROOT / "storyboard"
FRAMES_DIR = Path(__file__).resolve().parent / "frames"

W, H = 1280, 720
FPS = 30
DURATION_S = 7.0
TOTAL = int(DURATION_S * FPS)  # 210

# Sequential stills. Each fade is ~0.90–0.95s with a short hold after.
# (incoming_key, fade_start_s, fade_duration_s)
FADES: list[tuple[str, float, float]] = [
    ("B", 0.45, 0.95),
    ("C", 1.55, 0.95),
    ("D", 2.60, 0.95),
    ("E", 3.65, 0.95),
    ("F", 4.70, 1.00),
    ("G", 5.90, 0.95),
]


def smoother(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def load(name: str) -> Image.Image:
    im = Image.open(STORYBOARD / name).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.Resampling.LANCZOS)
    return im


def ken_burns(im: Image.Image, zoom: float, pan_x: float, pan_y: float) -> Image.Image:
    zoom = max(1.0, zoom)
    cw = max(1, int(round(W / zoom)))
    ch = max(1, int(round(H / zoom)))
    max_x = W - cw
    max_y = H - ch
    x = int(round(max_x * pan_x))
    y = int(round(max_y * pan_y))
    return im.crop((x, y, x + cw, y + ch)).resize((W, H), Image.Resampling.LANCZOS)


def camera_at(t: float) -> tuple[float, float, float]:
    u = smoother(t / DURATION_S)
    zoom = lerp(1.08, 1.0, u)
    pan_x = lerp(0.48, 0.50, u)
    pan_y = lerp(0.45, 0.48, u)
    return zoom, pan_x, pan_y


def gold_hint(im: Image.Image, amount: float) -> Image.Image:
    if amount <= 0.01:
        return im
    overlay = Image.new("RGB", im.size, (199, 154, 43))
    return Image.blend(im, overlay, amount * 0.045)


def optical_mix(a: Image.Image, b: Image.Image, t: float) -> Image.Image:
    u = smoother(t)
    blended = Image.blend(a, b, u)
    # Peak a very light blur at mid-dissolve so geometry snap is less visible.
    peak = 4.0 * u * (1.0 - u)
    radius = 1.15 * peak
    if radius > 0.08:
        blended = blended.filter(ImageFilter.GaussianBlur(radius=radius))
    return blended


def active_pair(t: float) -> tuple[str, str, float]:
    """Return (from_key, to_key, mix 0..1). mix=0 means fully from_key."""
    current = "A"
    for key, start, dur in FADES:
        end = start + dur
        if t < start:
            return current, key, 0.0
        if t < end:
            return current, key, (t - start) / dur
        current = key
    return current, current, 0.0


def compose_frame(i: int, stills: dict[str, Image.Image]) -> Image.Image:
    t = i / FPS
    zoom, pan_x, pan_y = camera_at(t)
    src, dst, mix_t = active_pair(t)
    plate_a = ken_burns(stills[src], zoom, pan_x, pan_y)
    if mix_t <= 0.0 or src == dst:
        frame = plate_a
    else:
        plate_b = ken_burns(stills[dst], zoom, pan_x, pan_y)
        frame = optical_mix(plate_a, plate_b, mix_t)

    gold = 0.0
    if 0.45 <= t <= 1.55:
        gold = max(gold, max(0.0, 1.0 - abs((t - 1.00) / 0.55)))
    if 5.40 <= t <= 6.50:
        gold = max(gold, 0.4 * max(0.0, 1.0 - abs((t - 5.95) / 0.55)))
    return gold_hint(frame, gold)


def main() -> None:
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    stills = {
        "A": load("frame-a-blueprint.png"),
        "B": load("frame-b-layout.png"),
        "C": load("frame-c-foundation.png"),
        "D": load("frame-d-framing.png"),
        "E": load("frame-e-envelope.png"),
        "F": load("frame-f-completed-house-master-v1-approved.png"),
        "G": load("frame-g-brand-composited.png"),
    }
    for i in range(TOTAL):
        compose_frame(i, stills).save(FRAMES_DIR / f"f{i:04d}.jpg", "JPEG", quality=90, subsampling=0)
        if i % 30 == 0:
            print(f"wrote {i}/{TOTAL}", flush=True)
    print("done", TOTAL)


if __name__ == "__main__":
    main()

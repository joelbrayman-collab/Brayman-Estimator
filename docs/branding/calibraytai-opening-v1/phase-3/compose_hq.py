#!/usr/bin/env python3
"""Opening V1 Phase 3 HQ composition.

Locked Frame F is upscaled, never regenerated. Construction plates share the
Frame F camera after the blueprint. Pass 2 pacing: ~0.95s cosine dissolves,
one continuous pull, light mid-fade blur. Silent 1920×1080 @ 30 fps / 7.0s.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STORYBOARD = ROOT / "storyboard"
ASSETS = Path(
    "/Users/joelbrayman/.cursor/projects/Users-joelbrayman-Desktop-Brayman-Estimator/assets"
)
PHASE3 = Path(__file__).resolve().parent
STILLS = PHASE3 / "stills"
FRAMES_DIR = PHASE3 / "frames"
WEB_DIR = Path("/Users/joelbrayman/Desktop/Brayman-Estimator/app/static/opening/v1")

W, H = 1920, 1080
FPS = 30
DURATION_S = 7.0
TOTAL = int(DURATION_S * FPS)

LOCKED_F = STORYBOARD / "frame-f-completed-house-master-v1-approved.png"
LOCKED_F_SHA = "e73c121be02198bdc8e5e70a786b4f8f56b3fa234720b68669c79c2def54ab7b"
LOGO = STORYBOARD / "approved-logo-v1-dark-reference.png"

FADES: list[tuple[str, float, float]] = [
    ("L", 0.40, 0.95),
    ("C", 1.50, 0.95),
    ("D", 2.55, 0.95),
    ("E", 3.60, 0.95),
    ("F", 4.65, 1.00),
    ("G", 5.85, 0.95),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smoother(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def fit(im: Image.Image) -> Image.Image:
    im = im.convert("RGB")
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
    return lerp(1.06, 1.0, u), lerp(0.49, 0.50, u), lerp(0.46, 0.48, u)


def gold_hint(im: Image.Image, amount: float) -> Image.Image:
    if amount <= 0.01:
        return im
    overlay = Image.new("RGB", im.size, (199, 154, 43))
    return Image.blend(im, overlay, amount * 0.04)


def optical_mix(a: Image.Image, b: Image.Image, t: float) -> Image.Image:
    u = smoother(t)
    blended = Image.blend(a, b, u)
    peak = 4.0 * u * (1.0 - u)
    radius = 1.05 * peak
    if radius > 0.08:
        blended = blended.filter(ImageFilter.GaussianBlur(radius=radius))
    return blended


def active_pair(t: float) -> tuple[str, str, float]:
    current = "A"
    for key, start, dur in FADES:
        end = start + dur
        if t < start:
            return current, key, 0.0
        if t < end:
            return current, key, (t - start) / dur
        current = key
    return current, current, 0.0


def composite_g(frame_f: Image.Image) -> Image.Image:
    logo = Image.open(LOGO).convert("RGBA")
    target_w = int(frame_f.width * 0.48)
    ratio = target_w / float(logo.width)
    logo = logo.resize((target_w, max(1, int(logo.height * ratio))), Image.Resampling.LANCZOS)
    base = frame_f.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    h, w = base.height, base.width
    for y in range(int(h * 0.52), h):
        t = max(0.0, (y - h * 0.52) / (h * 0.48))
        od.line([(0, y), (w, y)], fill=(8, 12, 22, int(175 * (t ** 1.25))))
    out = Image.alpha_composite(base, overlay)
    lx = (w - logo.width) // 2
    ly = h - logo.height - int(h * 0.04)
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        [lx - 18, ly - 10, lx + logo.width + 18, ly + logo.height + 14],
        radius=14,
        fill=(0, 0, 0, 70),
    )
    out = Image.alpha_composite(out, shadow.filter(ImageFilter.GaussianBlur(12)))
    out.paste(logo, (lx, ly), logo)
    return out.convert("RGB")


def prepare_stills() -> dict[str, Image.Image]:
    STILLS.mkdir(parents=True, exist_ok=True)
    f_sha = sha256(LOCKED_F)
    if f_sha != LOCKED_F_SHA:
        raise SystemExit(f"LOCKED Frame F hash mismatch: {f_sha}")

    mapping = {
        "A": STORYBOARD / "frame-a-blueprint.png",
        "L": ASSETS / "calibraytai-opening-v1-p3-layout-34.png",
        "C": ASSETS / "calibraytai-opening-v1-p3-foundation-34.png",
        "D": ASSETS / "calibraytai-opening-v1-p3-framing-34.png",
        "E": ASSETS / "calibraytai-opening-v1-p3-envelope-34.png",
        "F": LOCKED_F,
    }
    stills: dict[str, Image.Image] = {}
    for key, src in mapping.items():
        im = fit(Image.open(src))
        dest = STILLS / f"plate-{key.lower()}.jpg"
        im.save(dest, "JPEG", quality=95, subsampling=0)
        stills[key] = im
    g = composite_g(stills["F"])
    g.save(STILLS / "plate-g.jpg", "JPEG", quality=95, subsampling=0)
    stills["G"] = g
    return stills


def compose_frame(i: int, stills: dict[str, Image.Image]) -> Image.Image:
    t = i / FPS
    zoom, pan_x, pan_y = camera_at(t)
    src, dst, mix_t = active_pair(t)
    plate_a = ken_burns(stills[src], zoom, pan_x, pan_y)
    if mix_t <= 0.0 or src == dst:
        frame = plate_a
    else:
        frame = optical_mix(plate_a, ken_burns(stills[dst], zoom, pan_x, pan_y), mix_t)
    gold = 0.0
    if 0.45 <= t <= 1.50:
        gold = max(gold, max(0.0, 1.0 - abs((t - 0.95) / 0.55)))
    if 5.40 <= t <= 6.50:
        gold = max(gold, 0.35 * max(0.0, 1.0 - abs((t - 5.95) / 0.55)))
    return gold_hint(frame, gold)


def encode(src_pattern: str, dest: Path, extra: list[str]) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        src_pattern,
        *extra,
        str(dest),
    ]
    subprocess.run(cmd, check=True)


def contact_sheet(stills: dict[str, Image.Image]) -> None:
    order = [
        ("A", "BLUEPRINT"),
        ("L", "LAYOUT"),
        ("C", "FOUNDATION"),
        ("D", "FRAMING"),
        ("E", "ENVELOPE"),
        ("F", "COMPLETED HOUSE  LOCKED"),
        ("G", "CALIBRAYTAI"),
    ]
    tw, th = 480, 270
    pad, header, label_h = 16, 72, 40
    cols = 4
    sheet_w = pad + cols * (tw + pad)
    sheet_h = header + 2 * (th + label_h + pad) + pad
    sheet = Image.new("RGB", (sheet_w, sheet_h), (10, 14, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", 24)
        font_lab = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 13)
    except OSError:
        font_title = font_lab = ImageFont.load_default()
    draw.text((pad, 18), "CALIBRAYTAI OPENING V1  PHASE 3  HQ CONTACT SHEET", font=font_title, fill=(236, 230, 214))
    draw.text((pad, 46), "Frame F locked  |  1920x1080  |  7.0s silent  |  construction plates on approved house camera", font=font_lab, fill=(199, 154, 43))
    for i, (key, title) in enumerate(order):
        if i < 4:
            x = pad + i * (tw + pad)
            r = 0
        else:
            x = pad + int((cols - 3) * (tw + pad) / 2) + (i - 4) * (tw + pad)
            r = 1
        y = header + r * (th + label_h + pad)
        thumb = stills[key].resize((tw, th), Image.Resampling.LANCZOS)
        draw.rectangle([x - 1, y - 1, x + tw, y + th], outline=(199, 154, 43))
        sheet.paste(thumb, (x, y))
        draw.text((x, y + th + 8), f"{key}  {title}", font=font_lab, fill=(236, 230, 214))
    sheet.save(PHASE3 / "contact-sheet-phase-3.jpg", "JPEG", quality=92, subsampling=0)


def ffmpeg_encode() -> dict[str, Path]:
    pattern = str(FRAMES_DIR / "f%04d.jpg")
    hq = PHASE3 / "opening-v1-hq.mp4"
    web = PHASE3 / "opening-v1-web.mp4"
    webm = PHASE3 / "opening-v1-web.webm"
    encode(
        pattern,
        hq,
        [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "high",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-an",
            "-movflags",
            "+faststart",
        ],
    )
    encode(
        pattern,
        web,
        [
            "-vf",
            "scale=1280:720",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "high",
            "-crf",
            "24",
            "-preset",
            "medium",
            "-an",
            "-movflags",
            "+faststart",
        ],
    )
    encode(
        pattern,
        webm,
        [
            "-vf",
            "scale=1280:720",
            "-c:v",
            "libvpx-vp9",
            "-b:v",
            "0",
            "-crf",
            "32",
            "-an",
            "-row-mt",
            "1",
        ],
    )
    return {"hq": hq, "web": web, "webm": webm}


def ingest_web(outputs: dict[str, Path], stills: dict[str, Image.Image]) -> None:
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(outputs["web"], WEB_DIR / "opening-v1-web.mp4")
    shutil.copy2(outputs["webm"], WEB_DIR / "opening-v1-web.webm")
    poster = stills["G"].resize((1280, 720), Image.Resampling.LANCZOS)
    poster.save(WEB_DIR / "opening-v1-poster.jpg", "JPEG", quality=90, subsampling=0)
    stills["F"].resize((1280, 720), Image.Resampling.LANCZOS).save(
        WEB_DIR / "opening-v1-reduced-motion.jpg", "JPEG", quality=90, subsampling=0
    )


def write_manifest(outputs: dict[str, Path]) -> None:
    files = {
        "frame_f_locked": LOCKED_F,
        "hq_mp4": outputs["hq"],
        "web_mp4": outputs["web"],
        "web_webm": outputs["webm"],
        "contact_sheet": PHASE3 / "contact-sheet-phase-3.jpg",
        "ingest_mp4": WEB_DIR / "opening-v1-web.mp4",
        "ingest_webm": WEB_DIR / "opening-v1-web.webm",
        "ingest_poster": WEB_DIR / "opening-v1-poster.jpg",
        "ingest_reduced_motion": WEB_DIR / "opening-v1-reduced-motion.jpg",
        "phase2_pass2": ROOT / "phase-2" / "opening-v1-phase-2-motion-preview.mp4",
        "phase2_pass1": ROOT / "phase-2" / "opening-v1-phase-2-motion-preview-pass1.mp4",
    }
    manifest = {
        "version": "opening-v1",
        "duration_s": DURATION_S,
        "fps": FPS,
        "hq_size": [W, H],
        "web_size": [1280, 720],
        "audio": False,
        "locked_frame_f_sha256": LOCKED_F_SHA,
        "files": {name: {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size} for name, path in files.items()},
    }
    (PHASE3 / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def main() -> None:
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    stills = prepare_stills()
    contact_sheet(stills)
    for i in range(TOTAL):
        compose_frame(i, stills).save(FRAMES_DIR / f"f{i:04d}.jpg", "JPEG", quality=92, subsampling=0)
        if i % 30 == 0:
            print(f"frame {i}/{TOTAL}", flush=True)
    outputs = ffmpeg_encode()
    ingest_web(outputs, stills)
    write_manifest(outputs)


if __name__ == "__main__":
    main()

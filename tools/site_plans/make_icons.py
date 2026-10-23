"""Site Plans home-screen icons from the approved artwork (Joel, 23 Oct 2026).

Made exactly the way tools/useful_calculators/make_icons.py made the Useful Calculators set. The approved PNG is
frozen: this script never redraws, recolours or paints into it. It copies the original unchanged into the
repository and makes the sizes the phone needs by cropping away transparent margin, padding to a square on
transparency, resizing, and, where an icon must be opaque, placing it unchanged on a solid background.

    venv/bin/python tools/site_plans/make_icons.py /path/to/CalibraytAI_Site_Plans_Approved.png

The approved artwork is 1312 x 1199 (not square) with a wide transparent margin around the rounded tile. So:

1. crop to the artwork's visible extent (every pixel with alpha >= CROP_ALPHA, which keeps the tile and its soft
   shadow; only near-invisible margin is removed), so the tile fills the icon like the other Home Screen icons;
2. pad that to a square on transparency, centred;
3. resize the square.

Writes app/static/site-plans/:
    <original file name>              the approved PNG, byte for byte
    site-plans-icon-192.png           manifest "any" (keeps the artwork's transparency)
    site-plans-icon-512.png           manifest "any" (keeps the artwork's transparency)
    site-plans-icon-32.png            browser tab and the office Plans button (keeps transparency)
    site-plans-icon-180.png           apple-touch-icon: opaque (iOS fills transparent Home Screen pixels with black),
                                      the square artwork full size on the tile's own dark navy (see tile_colour)
    site-plans-icon-maskable-512.png  manifest "maskable": opaque, the artwork at 80 % (the safe zone) on that navy
and prints the SHA-256 of every file and the background colour used. iOS rounds the Home Screen icon's corners.

A later replacement artwork is a one-step swap: set APPROVED_NAME below, run the script with it, and update the
hashes in tests/test_site_plans.py.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "static" / "site-plans"
APPROVED_NAME = "CalibraytAI_Site_Plans_Approved.png"
SIZES = {"site-plans-icon-192.png": 192, "site-plans-icon-512.png": 512, "site-plans-icon-32.png": 32}
APPLE_TOUCH = "site-plans-icon-180.png"
MASKABLE = "site-plans-icon-maskable-512.png"
MASKABLE_SAFE = 0.80  # the maskable safe zone: the whole artwork sits inside the centre 80 %
CROP_ALPHA = 8        # crop away only margin fainter than this (alpha 0-255); the tile's shadow is kept
RIM_SKIP, RIM_TAKE = 20, 10  # tile_colour: step over the tile's lighter rim, then sample the body


def visible_box(image: Image.Image) -> tuple:
    alpha = image.convert("RGBA").getchannel("A").point(lambda v: 255 if v >= CROP_ALPHA else 0)
    box = alpha.getbbox()
    if box is None:
        raise SystemExit("The artwork is fully transparent.")
    return box


def squared(image: Image.Image) -> Image.Image:
    """Crop to the visible artwork, then pad to a square on transparency, centred. Pixels are copied, not changed."""
    art = image.convert("RGBA").crop(visible_box(image))
    side = max(art.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(art, ((side - art.size[0]) // 2, (side - art.size[1]) // 2))
    return canvas


def tile_colour(image: Image.Image) -> tuple:
    """The rounded tile's own dark navy: coming in from each side along 41 lines spread over the middle 80 % of the
    tile, find the first solid pixel (alpha >= 250), step over the lighter rim (RIM_SKIP px) and average the next
    RIM_TAKE pixels of the tile body. The tile is a gradient (lighter at the top); this is its average."""
    rgba = image.convert("RGBA")
    w, h = rgba.size
    solid = rgba.getchannel("A").point(lambda v: 255 if v >= 250 else 0).getbbox()
    if solid is None:
        raise SystemExit("No solid tile found in the artwork.")
    left, top, right, bottom = solid
    samples = []

    def walk(points):
        points = list(points)
        for i, (x, y) in enumerate(points):
            if rgba.getpixel((x, y))[3] >= 250:
                for x2, y2 in points[i + RIM_SKIP:i + RIM_SKIP + RIM_TAKE]:
                    samples.append(rgba.getpixel((x2, y2))[:3])
                return

    for k in range(41):
        f = 0.1 + 0.8 * k / 40
        y = int(top + (bottom - top) * f)
        x = int(left + (right - left) * f)
        walk((i, y) for i in range(w))
        walk((i, y) for i in range(w - 1, -1, -1))
        walk((x, j) for j in range(h))
        walk((x, j) for j in range(h - 1, -1, -1))
    return tuple(round(sum(p[i] for p in samples) / len(samples)) for i in range(3))


def resized(square: Image.Image, size: int) -> Image.Image:
    return square.resize((size, size), Image.LANCZOS)


def on_background(square: Image.Image, size: int, inner: int, colour: tuple) -> Image.Image:
    """The square artwork resized to inner x inner, unchanged, centred on an opaque size x size square of colour."""
    canvas = Image.new("RGBA", (size, size), colour + (255,))
    offset = (size - inner) // 2
    canvas.alpha_composite(resized(square, inner), (offset, offset))
    return canvas.convert("RGB")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make(source: Path, out: Path = OUT) -> dict:
    source = Path(source)
    image = Image.open(source)
    image.load()
    out.mkdir(parents=True, exist_ok=True)
    original = out / APPROVED_NAME
    if source.resolve() != original.resolve():
        shutil.copyfile(source, original)  # byte for byte
    written = {APPROVED_NAME: _sha(original)}
    square = squared(image)
    for name, size in SIZES.items():
        resized(square, size).save(out / name, "PNG")
        written[name] = _sha(out / name)
    colour = tile_colour(image)
    on_background(square, 180, 180, colour).save(out / APPLE_TOUCH, "PNG")
    written[APPLE_TOUCH] = _sha(out / APPLE_TOUCH)
    on_background(square, 512, round(512 * MASKABLE_SAFE), colour).save(out / MASKABLE, "PNG")
    written[MASKABLE] = _sha(out / MASKABLE)
    written["background"] = "#{:02x}{:02x}{:02x}".format(*colour)
    written["crop"] = "x {} to {}, y {} to {}".format(*(lambda b: (b[0], b[2], b[1], b[3]))(visible_box(image)))
    written["square"] = f"{square.size[0]} x {square.size[1]}"
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source", help="the approved Site Plans PNG")
    args = parser.parse_args(argv)
    for name, detail in make(Path(args.source)).items():
        print(f"{name}: {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Useful Calculators home-screen icons from the approved artwork (Joel, 22 Oct 2026).

"ONE APPROVED ICON." The approved PNG is frozen: this script never redraws, recolours or crops into it. It
copies the original unchanged into the repository and makes the sizes the phone needs by resizing the whole
image, and, where an icon must be opaque, by placing it unchanged on a solid background (padding only).

    venv/bin/python tools/useful_calculators/make_icons.py /path/to/CalibraytAI_Useful_Calculators_Transparent_Approved.png

Writes app/static/useful-calculators/:
    <original file name>                       the approved PNG, byte for byte
    useful-calculators-icon-192.png            manifest "any" (keeps the artwork's transparency)
    useful-calculators-icon-512.png            manifest "any" (keeps the artwork's transparency)
    useful-calculators-icon-32.png             browser tab (keeps transparency)
    useful-calculators-icon-180.png            apple-touch-icon: opaque. iOS fills transparent pixels of a
                                               Home Screen icon with black, so the artwork, full size and
                                               unchanged, sits on the tile's own edge blue (see edge_colour)
    useful-calculators-icon-maskable-512.png   manifest "maskable": opaque, the artwork at 80 % (the safe zone)
                                               on the same edge blue
and prints the SHA-256 of the approved PNG and the background colour used. iOS rounds the corners of the Home
Screen icon itself.

A later replacement artwork is a one-step swap: set APPROVED_NAME below to its file name, run the script with
it, and update the hash in tests/test_useful_calculators.py.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "static" / "useful-calculators"
APPROVED_NAME = "CalibraytAI_Useful_Calculators_Transparent_Approved.png"
SIZES = {"useful-calculators-icon-192.png": 192, "useful-calculators-icon-512.png": 512,
         "useful-calculators-icon-32.png": 32}
APPLE_TOUCH = "useful-calculators-icon-180.png"
MASKABLE = "useful-calculators-icon-maskable-512.png"
MASKABLE_SAFE = 0.80  # the maskable safe zone: the whole artwork sits inside the centre 80 %


def edge_colour(image: Image.Image) -> tuple:
    """The tile's own edge blue: the mean colour of the outermost fully opaque band of the artwork (the first
    three opaque pixels met coming in from each side), along rows and columns spread over the middle 80 % of
    each side. The tile is a gradient (lighter at the top, darker at the bottom); this is its average edge."""
    rgba = image.convert("RGBA")
    w, h = rgba.size
    samples = []
    lines = [int(w * (0.1 + 0.8 * i / 40)) for i in range(41)]

    def walk(points):
        taken = 0
        for x, y in points:
            r, g, b, a = rgba.getpixel((x, y))
            if a >= 250:
                samples.append((r, g, b))
                taken += 1
                if taken == 3:
                    return

    for k in lines:
        walk((x, k) for x in range(w))
        walk((x, k) for x in range(w - 1, -1, -1))
        walk((k, y) for y in range(h))
        walk((k, y) for y in range(h - 1, -1, -1))
    if not samples:
        raise SystemExit("No opaque edge found in the artwork.")
    return tuple(round(sum(p[i] for p in samples) / len(samples)) for i in range(3))


def on_background(image: Image.Image, size: int, inner: int, colour: tuple) -> Image.Image:
    """The artwork resized to inner x inner, unchanged, centred on an opaque size x size square of colour."""
    canvas = Image.new("RGBA", (size, size), colour + (255,))
    art = resized(image.convert("RGBA"), inner)
    offset = (size - inner) // 2
    canvas.alpha_composite(art, (offset, offset))
    return canvas.convert("RGB")


def resized(image: Image.Image, size: int) -> Image.Image:
    """The whole image scaled to size x size. Square artwork only: nothing is cropped."""
    return image.resize((size, size), Image.LANCZOS)


def make(source: Path, out: Path = OUT) -> dict:
    source = Path(source)
    image = Image.open(source)
    image.load()
    if image.size[0] != image.size[1]:
        raise SystemExit(f"The approved artwork must be square; {source} is {image.size[0]} x {image.size[1]}.")
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")
    out.mkdir(parents=True, exist_ok=True)
    original = out / APPROVED_NAME
    if source.resolve() != original.resolve():
        shutil.copyfile(source, original)  # byte for byte
    written = {APPROVED_NAME: hashlib.sha256(original.read_bytes()).hexdigest()}
    for name, size in SIZES.items():
        resized(image, size).save(out / name, "PNG")
        written[name] = f"{size}x{size}, transparency kept"
    colour = edge_colour(image)
    hex_colour = "#{:02x}{:02x}{:02x}".format(*colour)
    on_background(image, 180, 180, colour).save(out / APPLE_TOUCH, "PNG")
    written[APPLE_TOUCH] = f"180x180 opaque, artwork full size on {hex_colour} {colour}"
    inner = round(512 * MASKABLE_SAFE)
    on_background(image, 512, inner, colour).save(out / MASKABLE, "PNG")
    written[MASKABLE] = f"512x512 opaque, artwork {inner}px on {hex_colour} {colour}"
    written["background"] = hex_colour
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source", help="the approved Useful Calculators PNG")
    args = parser.parse_args(argv)
    for name, detail in make(Path(args.source)).items():
        print(f"{name}: {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

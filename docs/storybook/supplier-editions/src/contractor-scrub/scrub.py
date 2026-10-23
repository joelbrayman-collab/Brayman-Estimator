"""Remove the Brayman Construction name, logo and street address from the Contractor Storybook's app screens and
drawings (re-applies the 22 Oct 2026 audit to the source images). Originals are kept in build/assets/pre-scrub/.
Each change replaces an exact OCR word run with new text set in the same font, size, colour and position."""
import csv, collections, os, shutil, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

S = "/tmp/claude-0/-home-claude/93001464-bbef-59f1-b978-132f6dd14297/scratchpad"
A = f"{S}/build/assets"
ORIG = f"{A}/pre-scrub"
F = f"{S}/scrub/fonts"
PLEX = {w: f"{F}/ibm-plex-sans-latin-{w}-normal.ttf" for w in (400, 500, 600, 700)}
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
os.makedirs(ORIG, exist_ok=True)

HDR = [("Brayman Construction".split(), "Your Company", 400), ("Brayman Office".split(), "Office", 500)]
SIDE = [("BRAYMAN CONSTRUCTION".split(), "YOUR COMPANY", "caps")]
OPS = {
    "screen-ch01": [("Brayman Construction Home".split(), "Home", 600)] + HDR + SIDE,
    "screen-ch03": HDR + SIDE + [("The Brayman contract is generated from".split(), "The contract is generated from", 400)],
    "screen-ch04": HDR + SIDE,
    "screen-ch06": HDR + SIDE + [("Brayman calculates.".split(), "You calculate.", "shift"),
                                 (("BOX", "BRAYMAN CONSTRUCTION", 38, 276, 372, 18), "YOUR COMPANY", "caps")],  # OCR splits this one
    "screen-ch07": [("is Brayman's quantity".split(), "is your quantity", 400)],
    "screen-ch08": HDR + SIDE,
    "screen-ch09": HDR + SIDE,
    "screen-ch10a": HDR + SIDE + [
        ("active Brayman V1 Ontario contract package.".split(), "active V1 Ontario contract package.", "shift"),
        ("Brayman V1 Interim Contract".split(), "V1 Interim Contract", 500),
        ("Package CA-ON-BRAYMAN-V1-INTERIM".split(), "Package CA-ON-V1-INTERIM", 400)],
    "screen-ch10b": [("Brayman Construction".split(), "Your Company", 700),
                     ("and contact Brayman Construction.".split(), "and contact your contractor.", 400)],
    "screen-ch11": HDR + SIDE,
    "screen-ch12": HDR + SIDE + [(["Brayman", "Office"], "Office", 400)],
}
SHEETS = ["j1-sheet-2", "j1-sheet-5", "j1-sheet-7"]


def ocr(path):
    out = subprocess.run(["tesseract", path, "-", "tsv"], capture_output=True, text=True).stdout
    rows = [r for r in csv.reader(out.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE)][1:]
    lines = collections.defaultdict(list)
    for r in rows:
        if len(r) > 11 and r[11].strip():
            lines[(r[2], r[3], r[4])].append((r[11], int(r[6]), int(r[7]), int(r[8]), int(r[9])))
    return [sorted(v, key=lambda w: w[1]) for v in lines.values()]


def runs(lines, seq):
    for ws in lines:
        for i in range(len(ws) - len(seq) + 1):
            if [w[0] for w in ws[i:i + len(seq)]] == seq:
                yield ws[i:i + len(seq)], ws[i + len(seq):]


def bg_and_ink(im, box):
    x0, y0, x1, y1 = box
    border = [im.getpixel((x, y)) for x in range(x0, x1, 2) for y in (y0, y1)] + [im.getpixel((x, y)) for y in range(y0, y1, 2) for x in (x0, x1)]
    bg = max(set(border), key=border.count)
    inner = [im.getpixel((x, y)) for x in range(x0, x1) for y in range(y0, y1)]
    ink = max(inner, key=lambda p: sum((a - b) ** 2 for a, b in zip(p, bg)))
    return bg, ink


def draw_caps(d, x, top, text, size, track, ink, font):
    for ch in text:
        bb = font.getbbox(ch)
        d.text((x, top - font.getbbox("H")[1]), ch, font=font, fill=ink)
        x += font.getlength(ch) + track


def apply(im, run, new, mode, log, rest=None):
    d = ImageDraw.Draw(im)
    x0 = run[0][1]; y0 = min(w[2] for w in run); x1 = max(w[1] + w[3] for w in run); y1 = max(w[2] + w[4] for w in run)
    pad = 4
    box = (x0 - pad, y0 - pad, x1 + pad, y1 + pad + 6)
    bg, ink = bg_and_ink(im, (x0 - pad - 2, y0 - pad - 2, x1 + pad + 2, y1 + pad + 8))
    old = " ".join(w[0] for w in run)
    if mode == "caps":
        h = y1 - y0
        font = ImageFont.truetype(PLEX[700], 10)
        size = round(10 * h / (font.getbbox("H")[3] - font.getbbox("H")[1]))
        font = ImageFont.truetype(PLEX[700], size)
        ob = font.getbbox(old)
        track = (x1 - x0 - (ob[2] - ob[0])) / (len(old) - 1)
        d.rectangle(box, fill=bg)
        draw_caps(d, x0 - font.getbbox(old[0])[0], y0, new, size, track, ink, font)
    else:
        src_im = im.copy()
        path = SERIF_B if mode == "serif" else PLEX[400 if mode == "shift" else mode]
        size = 20
        for _ in range(6):  # fit the original text's ink width
            font = ImageFont.truetype(path, size)
            b = font.getbbox(old)
            size = size * (x1 - x0) / (b[2] - b[0])
        font = ImageFont.truetype(path, round(size))
        b = font.getbbox(old)
        d.rectangle(box, fill=bg)
        if rest:  # move the rest of the line left so no gap is left behind
            tail = (x1 + 1, y0 - pad, max(w[1] + w[3] for w in rest) + pad, y1 + pad + 6)
            piece = src_im.crop(tail)
            d.rectangle(tail, fill=bg)
            nx1 = x0 - b[0] + font.getbbox(new)[2]
            im.paste(piece, (nx1 + 1, tail[1]))
        d.text((x0 - b[0], y0 - b[1]), new, font=font, fill=ink)
    log.append(f"  {old!r} -> {new!r}  at {box}  size {round(size)}  ink {ink} bg {bg}")


def main():
    log = []
    for name, ops in OPS.items():
        src = f"{ORIG}/{name}.png"
        if not os.path.exists(src):
            shutil.copy2(f"{A}/{name}.png", src)
        im = Image.open(src).convert("RGB")
        lines = ocr(src)
        log.append(name)
        done = []
        for seq, new, mode in ops:
            found = [([(seq[1],) + seq[2:]], [])] if seq[0] == "BOX" else list(runs(lines, seq))
            assert found, (name, seq)
            for r, rest in found:
                bx = (r[0][1], min(w[2] for w in r), max(w[1] + w[3] for w in r), max(w[2] + w[4] for w in r))
                if any(not (bx[2] < o[0] or bx[0] > o[2] or bx[3] < o[1] or bx[1] > o[3]) for o in done):
                    continue
                done.append(bx)
                apply(im, r, new, mode, log, rest if mode == "shift" else None)
        im.save(f"{A}/{name}.png")
    for name in SHEETS:
        src = f"{ORIG}/{name}.png"
        if not os.path.exists(src):
            shutil.copy2(f"{A}/{name}.png", src)
        im = Image.open(src).convert("RGB")
        lines = ocr(src)
        log.append(name)
        d = ImageDraw.Draw(im)
        title = next(runs(lines, ["Brayman", "Construction"]))[0]
        sub = next(runs(lines, "Brayman Construction Inc.".split()))[0]
        addr = next(r for ws in lines for r in [ws] if any("Merrickville" in w[0] for w in ws))
        addr = [w for w in addr if w[1] >= sub[0][1] - 5]
        ax1 = max(w[1] + w[3] for w in addr); ay1 = max(w[2] + w[4] for w in addr)
        white = (255, 255, 255)
        # logo: everything left of the title text, above the gold rule
        d.rectangle((60, 20, title[0][1] - 12, ay1 + 18), fill=white)
        d.rectangle((sub[0][1] - 4, sub[0][2] - 6, ax1 + 6, ay1 + 8), fill=white)
        apply(im, title, "Your Company", "serif", log)
        im.save(f"{A}/{name}.png")
    open(f"{S}/scrub/scrub-log.txt", "w").write("\n".join(log) + "\n")
    print("\n".join(log))


main()

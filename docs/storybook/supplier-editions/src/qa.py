"""QA a screen-edition book: every page at laptop size (overflow, smallest text) and phone size; contact sheets."""
import sys, os, json
from playwright.sync_api import sync_playwright
from PIL import Image

f = sys.argv[1]
tag = sys.argv[2] if len(sys.argv) > 2 else "qa"
out = os.path.join(os.path.dirname(f), tag)
os.makedirs(out, exist_ok=True)
CHECK = """() => { const p = document.querySelector('.pg.on'); const res = {id: p.id, over: [], minfont: 99, minel: ''};
  p.querySelectorAll('.pad, .l, .ov, .calc').forEach(el => { if (el.scrollHeight > el.clientHeight + 2 && getComputedStyle(el).overflowY !== 'auto' && !document.getElementById('app').classList.contains('flow')) res.over.push(el.className + ' +' + (el.scrollHeight - el.clientHeight)); });
  const pr = p.getBoundingClientRect();
  p.querySelectorAll('*').forEach(el => { if (!el.childNodes.length) return; const t = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!t) return;
    const r = el.getBoundingClientRect(); if (r.width === 0) return;
    if (!document.getElementById('app').classList.contains('flow') && (r.right > pr.right + 2 || r.bottom > pr.bottom + 2)) res.over.push('outside: ' + el.tagName + ' ' + el.textContent.trim().slice(0, 40));
    const fs = parseFloat(getComputedStyle(el).fontSize); if (fs < res.minfont) { res.minfont = fs; res.minel = el.textContent.trim().slice(0, 40); } });
  const fo = p.querySelector('.folio'); if (fo && !document.getElementById('app').classList.contains('flow')) { const ft = fo.getBoundingClientRect().top;
    p.querySelectorAll('.pad *').forEach(el => { if (fo.contains(el)) return; const t = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!t) return;
      const r = el.getBoundingClientRect(); if (r.width && r.bottom > ft + 2) res.over.push('over folio: ' + el.tagName + ' ' + el.textContent.trim().slice(0, 30)); }); }
  return res; }"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp, mob in (("laptop", {"width": 1440, "height": 820}, False), ("phone", {"width": 390, "height": 760}, True)):
        ctx = b.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=1)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file://" + f); pg.wait_for_timeout(1200)
        n = pg.evaluate("document.querySelectorAll('.pg').length")
        shots, probs, mins = [], [], []
        for i in range(n):
            if i:
                pg.click("#next"); pg.wait_for_timeout(420)
            r = pg.evaluate(CHECK)
            mins.append((round(r["minfont"], 1), r["id"], r["minel"]))
            if r["over"]:
                probs.append((i + 1, r["id"], r["over"][:3]))
            path = f"{out}/{name}-{i + 1:02d}.png"
            pg.screenshot(path=path)
            shots.append(path)
        print(name, "pages", n, "errors", errs, "scrollW", pg.evaluate("document.documentElement.scrollWidth"))
        print("  problems:", json.dumps(probs, ensure_ascii=False))
        mins.sort()
        print("  smallest text px:", mins[:4])
        body = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.pg')).fontSize)")
        print("  body text px:", round(body, 1))
        ims = [Image.open(s) for s in shots]
        w, h = ims[0].size
        sc = 0.25 if name == "laptop" else 0.4
        tw, th = int(w * sc), int(h * sc)
        cols = 8 if name == "laptop" else 12
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th), "white")
        for k, im in enumerate(ims):
            sheet.paste(im.resize((tw, th)), ((k % cols) * tw, (k // cols) * th))
        sheet.save(f"{out}/sheet-{name}.jpg", quality=80)
        ctx.close()
    b.close()

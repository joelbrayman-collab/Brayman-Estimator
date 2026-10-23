"""Landscape PDF of a screen-edition book: one 16:10 page per screen, for email."""
import sys, subprocess, os
from playwright.sync_api import sync_playwright
src, out = sys.argv[1], sys.argv[2]
tmp = out + ".tmp.pdf"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto("file://" + src); pg.wait_for_timeout(1500)
    pg.evaluate("document.fonts.ready")
    pg.pdf(path=tmp, width="1600px", height="1000px", print_background=True, prefer_css_page_size=True)
    b.close()
subprocess.run(["gs", "-q", "-sDEVICE=pdfwrite", "-dPDFSETTINGS=/printer", "-dNOPAUSE", "-dBATCH", f"-sOutputFile={out}", tmp], check=True)
os.remove(tmp)
print(out, round(os.path.getsize(out) / 1e6, 2), "MB")

"""Screen-first CalibraytAI Storybook engine (21 Oct 2026).

Feedback: the flipbooks showed letter-size print pages as pictures, two at a time, so body text was ~6-7 px on a laptop.
This engine renders every page as real HTML text on a wide 16:10 page that fills the screen one page at a time.
Type is sized from the page width (body about 22 px on a 13-inch laptop); on a phone the pages reflow into a
scrolling column with fixed, readable sizes. Live calculators are real inputs. Same visual identity: CalibraytAI
navy and gold, Gelasio headings, IBM Plex Sans text, the approved photographs, artwork and actual screens.
"""
import base64, hashlib, html, io, json, os
from PIL import Image

E = html.escape
S = "/tmp/claude-0/-home-claude/93001464-bbef-59f1-b978-132f6dd14297/scratchpad"
FONTS = f"{S}/nbuild/assets"


def _font(fam, w, style, f):
    b = base64.b64encode(open(f"{FONTS}/{f}", "rb").read()).decode()
    return f'@font-face{{font-family:{fam};font-weight:{w};font-style:{style};font-display:swap;src:url(data:font/woff2;base64,{b}) format("woff2")}}'


FONT_CSS = "".join([
    _font("Plex", 400, "normal", "ibm-plex-sans-latin-400-normal.woff2"), _font("Plex", 400, "italic", "ibm-plex-sans-latin-400-italic.woff2"),
    _font("Plex", 500, "normal", "ibm-plex-sans-latin-500-normal.woff2"), _font("Plex", 600, "normal", "ibm-plex-sans-latin-600-normal.woff2"),
    _font("Plex", 700, "normal", "ibm-plex-sans-latin-700-normal.woff2"), _font("Serif", 400, "normal", "gelasio-latin-400-normal.woff2"),
    _font("Serif", 400, "italic", "gelasio-latin-400-italic.woff2"), _font("Serif", 700, "normal", "gelasio-latin-700-normal.woff2"),
])

_cache = {}


def img(path, w=1800, q=80, crop=None):
    """Embed an image as WebP (photos and screens), resized for the screen."""
    key = (path, w, q, crop)
    if os.environ.get("IMGLOG"):
        open(os.environ["IMGLOG"], "a").write(path + "\n")
    if key in _cache:
        return _cache[key]
    im = Image.open(path)
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") and path.endswith(".png") else "RGB")
    if crop:
        im = im.crop(crop)
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=q, method=6)
    uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    _cache[key] = uri
    return uri


CSS = r"""
:root{--navy:#061426;--navy2:#0b2138;--gold:#c99220;--gold2:#e0b14b;--ink:#1c2430;--mute:#525c69;--paper:#ffffff;--stone:#f4f1ea;--rule:#dcd6ca;--u:13px}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;background:var(--navy);color:var(--ink);font-family:Plex,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
#app{display:grid;grid-template-rows:auto 1fr auto;grid-template-columns:minmax(0,1fr);width:100%;height:100vh;height:100dvh}
#top{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 20px;color:#fff}
#top .t{min-width:0;font:600 13px/1.2 Plex,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:var(--gold2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#top .s{min-width:0;font:400 13px/1.2 Plex,sans-serif;color:#b9c3d0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#stage{position:relative;overflow:hidden;min-height:0}
#deck{position:absolute;left:50%;top:50%;width:var(--pw);height:var(--ph);transform:translate(-50%,-50%)}
.pg{position:absolute;inset:0;overflow:hidden;background:var(--paper);font-size:calc(var(--u)*1.72);line-height:1.5;
  opacity:0;visibility:hidden;transform:translateX(2.5%);transition:opacity .35s ease,transform .35s ease,visibility 0s linear .35s;box-shadow:0 18px 50px rgba(0,0,0,.45)}
.pg.on{opacity:1;visibility:visible;transform:none;transition:opacity .35s ease,transform .35s ease}
.pg.back{transform:translateX(-2.5%)}
.side{position:absolute;top:50%;transform:translateY(-50%);z-index:5;width:54px;height:54px;border-radius:50%;border:0;background:var(--gold);color:var(--navy);
  font:700 30px/1 Plex,sans-serif;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,.4)}
.side:disabled{opacity:.25;cursor:default}#sprev{left:14px}#snext{right:14px}
#bar{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;padding:10px 14px 12px}
#bar button,#bar select{font:600 15px/1 Plex,sans-serif;border-radius:999px;padding:11px 18px;border:1px solid #3a4c63;background:#0e2338;color:#fff;cursor:pointer}
#bar #next{background:var(--gold);color:var(--navy);border-color:var(--gold)}
#bar button:disabled{opacity:.35;cursor:default}
#bar .count{font:500 15px/1 Plex,sans-serif;color:#c9d2de;min-width:9.5em;text-align:center}
#bar select{max-width:16em;appearance:auto}
button:focus-visible,select:focus-visible,input:focus-visible,a:focus-visible{outline:3px solid var(--gold2);outline-offset:2px}

/* type */
.kicker{font-size:calc(var(--u)*1.12);letter-spacing:.2em;text-transform:uppercase;font-weight:700;color:var(--gold)}
h1,h2,h3,h4{font-family:Serif,Georgia,serif;color:var(--navy);font-weight:700;line-height:1.12}
h1{font-size:calc(var(--u)*5.4)}
h2{font-size:calc(var(--u)*3.5);margin:calc(var(--u)*.7) 0 calc(var(--u)*1.1)}
h3{font-size:calc(var(--u)*2.6)}
h4{font-size:calc(var(--u)*2)}
p+p{margin-top:calc(var(--u)*.9)}
.lede{font-family:Serif,Georgia,serif;font-size:calc(var(--u)*2.15);line-height:1.38;color:var(--navy)}
.small,.cap{font-size:calc(var(--u)*1.3);line-height:1.45;color:var(--mute)}
.goldrule{width:calc(var(--u)*5);height:3px;background:var(--gold)}
.pad{position:absolute;inset:0;padding:calc(var(--u)*4.4) calc(var(--u)*6.2) calc(var(--u)*5.2);display:flex;flex-direction:column}
.folio{position:absolute;left:calc(var(--u)*6.2);right:calc(var(--u)*6.2);bottom:calc(var(--u)*1.8);display:flex;justify-content:space-between;
  font-size:calc(var(--u)*1.05);letter-spacing:.16em;text-transform:uppercase;color:var(--mute);border-top:1px solid var(--rule);padding-top:calc(var(--u)*.8)}
.folio b{color:var(--gold)}
.dark{background:var(--navy);color:#e9edf3}.dark h1,.dark h2,.dark h3,.dark h4{color:#fff}.dark .lede{color:#fff}.dark .small{color:#b9c3d0}
.dark .card{color:var(--ink)}.dark .card h4{color:var(--navy)}.dark .card p,.art .ov .card p{color:var(--ink)}
.dark .toc button{color:#fff;border-color:#24384f}
.dark .folio{color:#8f9bab;border-color:#24384f}
.tag{display:inline-block;font-size:calc(var(--u)*1.02);letter-spacing:.14em;text-transform:uppercase;font-weight:700;padding:calc(var(--u)*.35) calc(var(--u)*.8);border-radius:3px;background:var(--navy);color:#fff}
.tag.next{background:var(--gold2);color:var(--navy)}.tag.built{background:#2e6b4f}.tag.future{background:transparent;color:var(--navy);border:1.5px solid var(--navy)}
.flag{display:inline-block;align-self:flex-start;font-size:calc(var(--u)*1.1);letter-spacing:.14em;text-transform:uppercase;font-weight:700;padding:calc(var(--u)*.45) calc(var(--u)*1);background:var(--gold2);color:var(--navy);border-radius:3px}

/* cover */
.cover{display:grid;grid-template-columns:44% 56%}
.cover .l{background:var(--navy);padding:calc(var(--u)*5) calc(var(--u)*4.6);display:flex;flex-direction:column;justify-content:center;border-left:calc(var(--u)*.8) solid var(--gold)}
.cover h1{color:#fff;margin:calc(var(--u)*1.2) 0}.cover h1 span{color:var(--gold2)}
.cover .strap{font-family:Serif,Georgia,serif;font-size:calc(var(--u)*2.3);color:#fff;line-height:1.3}
.cover .sub{margin-top:calc(var(--u)*1.4);color:#c3ccd8;font-size:calc(var(--u)*1.6)}
.cover .ser{margin-top:calc(var(--u)*2.4);font-size:calc(var(--u)*1.1);letter-spacing:.2em;text-transform:uppercase;color:var(--gold2);font-weight:600}
.cover .r{background:var(--navy);position:relative}
.cover .r img{width:100%;height:100%;object-fit:contain;background:transparent}
.art.hero{background:var(--navy)}.art.hero img.bg{top:3%;height:49%;object-fit:contain;object-position:50% 50%;background:transparent}.art.hero .ov{background:none}
.cover .start{margin-top:calc(var(--u)*2.6);align-self:flex-start;font:600 calc(var(--u)*1.5)/1 Plex,sans-serif;padding:calc(var(--u)*1.1) calc(var(--u)*2);border-radius:999px;border:0;background:var(--gold);color:var(--navy);cursor:pointer}

/* full-bleed art / photo pages */
.art img.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.art .ov{position:absolute;left:0;right:0;bottom:0;padding:calc(var(--u)*3) calc(var(--u)*6.2) calc(var(--u)*4);background:linear-gradient(rgba(6,20,38,.45),rgba(6,20,38,.94) 20%)}
.art .ov h2{color:#fff;max-width:28em}.art .ov h2 span{color:var(--gold2)}.art .ov p{color:#dfe5ee;max-width:46em}
.lifeline{margin-top:calc(var(--u)*1.2);font-size:calc(var(--u)*1.2);letter-spacing:.22em;font-weight:700;color:var(--gold2)}

/* opener */
.opener{display:grid;grid-template-columns:40% 60%}
.opener .l{background:var(--navy);padding:calc(var(--u)*4.4) calc(var(--u)*4.2);display:flex;flex-direction:column;position:relative}
.opener .num{font-family:Serif,Georgia,serif;font-size:calc(var(--u)*9);line-height:1;color:transparent;-webkit-text-stroke:2px var(--gold2)}
.opener h2{color:#fff;margin-top:calc(var(--u)*1.2)}
.opener .osub{color:var(--gold2);font-size:calc(var(--u)*1.65);font-weight:500}
.opener .story{margin-top:auto;font-family:Serif,Georgia,serif;font-style:italic;font-size:calc(var(--u)*1.85);line-height:1.5;color:#e7ecf3}
.opener .r{position:relative}.opener .r img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.credit{position:absolute;right:calc(var(--u)*1.2);bottom:calc(var(--u)*1);font-size:calc(var(--u)*.95);color:#fff;text-shadow:0 1px 3px #000;opacity:.9}

/* text pages */
.cols2{column-count:2;column-gap:calc(var(--u)*4)}
.cols2 p{break-inside:avoid}
.cols2.big{font-size:calc(var(--u)*1.9);line-height:1.5}
.split{display:grid;grid-template-columns:1.25fr 1fr;gap:calc(var(--u)*4.2);align-items:start;flex:1;min-height:0}
.split.even{grid-template-columns:1fr 1fr}
.split.wide{grid-template-columns:1.6fr 1fr}
.photo{width:100%;border-radius:4px;object-fit:cover}
.pts{display:grid;grid-template-columns:repeat(3,1fr);gap:calc(var(--u)*2)}
.pt{border-top:3px solid var(--gold);padding-top:calc(var(--u)*1)}
.pt b{display:block;font-family:Serif,Georgia,serif;font-size:calc(var(--u)*2);color:var(--navy);line-height:1.2;margin-bottom:calc(var(--u)*.4)}
.pt span{font-size:calc(var(--u)*1.6);line-height:1.45}
.mean{margin-top:auto;background:var(--navy);color:#fff;padding:calc(var(--u)*1.6) calc(var(--u)*2.2);border-radius:4px}
.mean .kicker{color:var(--gold2);margin-bottom:calc(var(--u)*1)}
.mean .pt{border-color:var(--gold2)}.mean .pt b{color:#fff}.mean .pt span{color:#d6dde7}
.card{background:var(--stone);border-top:4px solid var(--gold);padding:calc(var(--u)*1.6) calc(var(--u)*1.8);border-radius:0 0 4px 4px}
.card h4{margin-bottom:calc(var(--u)*.5)}
.card p,.card li{font-size:calc(var(--u)*1.6);line-height:1.45}
.cards{display:grid;gap:calc(var(--u)*1.8)}
.cards.c2{grid-template-columns:1fr 1fr}.cards.c3{grid-template-columns:repeat(3,1fr)}.cards.c4{grid-template-columns:repeat(4,1fr)}
ul.ticks{list-style:none}
ul.ticks li{position:relative;padding-left:calc(var(--u)*2);margin:calc(var(--u)*.55) 0;font-size:calc(var(--u)*1.65);line-height:1.4}
ul.ticks li:before{content:"✓";position:absolute;left:0;color:var(--gold);font-weight:700}
ul.ticks.no li:before{content:"✕";color:#a33a2c}
.dark ul.ticks li{color:#e6ebf1}
.rules{display:grid;grid-template-columns:1fr 1fr;gap:calc(var(--u)*1.2) calc(var(--u)*3)}
.rule{display:grid;grid-template-columns:calc(var(--u)*3) 1fr;gap:calc(var(--u)*1);align-items:start;border-top:1px solid var(--rule);padding-top:calc(var(--u)*1)}
.rule i{font-style:normal;font-family:Serif,Georgia,serif;font-size:calc(var(--u)*2.4);color:var(--gold);line-height:1}
.rule b{display:block;color:var(--navy);font-size:calc(var(--u)*1.75)}
.rule span{font-size:calc(var(--u)*1.55);line-height:1.45;color:var(--ink)}
.pull{font-family:Serif,Georgia,serif;font-size:calc(var(--u)*2.2);line-height:1.35;color:var(--navy);border-left:4px solid var(--gold);padding:calc(var(--u)*.4) 0 calc(var(--u)*.4) calc(var(--u)*1.8)}
.pull small{display:block;margin-top:calc(var(--u)*.6);font-family:Plex,sans-serif;font-size:calc(var(--u)*1.05);letter-spacing:.16em;text-transform:uppercase;color:var(--gold);font-weight:700}
table.t{width:100%;border-collapse:collapse;font-size:calc(var(--u)*1.55);line-height:1.4}
table.t th{text-align:left;font-size:calc(var(--u)*1.05);letter-spacing:.14em;text-transform:uppercase;color:var(--gold);padding:calc(var(--u)*.6) calc(var(--u)*1);border-bottom:2px solid var(--gold)}
table.t td{padding:calc(var(--u)*.9) calc(var(--u)*1);border-bottom:1px solid var(--rule);vertical-align:top}
table.t td.g{font-family:Serif,Georgia,serif;font-weight:700;color:var(--navy);font-size:calc(var(--u)*1.8);white-space:nowrap}
table.t td.m{color:var(--mute)}
table.t.tight td{padding:calc(var(--u)*.4) calc(var(--u)*.8)}table.t.tight th{padding:calc(var(--u)*.4) calc(var(--u)*.8)}

/* screens */
.shot{flex:1;min-height:0;display:flex;gap:calc(var(--u)*2);align-items:center;justify-content:center;margin-top:calc(var(--u)*.6)}
.shot .desk{flex:1;min-width:0;max-height:100%;display:flex;flex-direction:column;align-items:center;min-height:0;height:100%}
.shot .desk img{max-width:100%;max-height:100%;min-height:0;object-fit:contain;border:1px solid #cfc8bb;box-shadow:0 4px 18px rgba(8,23,36,.14);border-radius:4px;background:#fff;cursor:zoom-in}
.shot .phone{height:100%;max-height:100%;display:flex;align-items:center}
.shot .phone img{height:100%;max-height:100%;width:auto;border:calc(var(--u)*.55) solid var(--navy);border-radius:calc(var(--u)*2);background:#fff;cursor:zoom-in}
.capline{display:flex;justify-content:space-between;gap:calc(var(--u)*2);align-items:baseline;margin-top:calc(var(--u)*1)}
.capline .cap{font-size:calc(var(--u)*1.45);color:var(--ink)}
.capline .tag{white-space:nowrap}
.hint{font-size:calc(var(--u)*1.05);color:var(--mute)}
#zoom{position:fixed;inset:0;z-index:50;background:rgba(3,10,20,.94);display:none;align-items:center;justify-content:center;padding:16px;cursor:zoom-out;overflow:auto}
#zoom.on{display:flex}#zoom img{max-width:none;width:min(1800px,160vw);height:auto;background:#fff}
#zoom .x{position:fixed;top:12px;right:16px;font:600 15px Plex,sans-serif;color:#fff;background:#0e2338;border:1px solid #3a4c63;border-radius:999px;padding:10px 16px;cursor:pointer}

/* contents */
.toc{display:grid;grid-template-columns:1fr 1fr;gap:0 calc(var(--u)*4);margin-top:calc(var(--u)*.6)}
.toc .stg{grid-column:span 1;font-size:calc(var(--u)*1.05);letter-spacing:.2em;text-transform:uppercase;color:var(--gold);font-weight:700;margin:calc(var(--u)*1.1) 0 calc(var(--u)*.3)}
.toc button{display:grid;grid-template-columns:calc(var(--u)*3.2) 1fr auto;align-items:baseline;width:100%;text-align:left;background:none;border:0;border-bottom:1px solid var(--rule);
  padding:calc(var(--u)*.45) 0;font:inherit;color:var(--navy);cursor:pointer}
.toc button:hover b{color:var(--gold)}
.toc button i{font-style:normal;font-weight:700;color:var(--gold);font-size:calc(var(--u)*1.3)}
.toc button b{font-weight:600;font-size:calc(var(--u)*1.6)}
.toc button span{font-size:calc(var(--u)*1.2);color:var(--mute)}
.tocgrp{break-inside:avoid}
.toc.tight button{padding:calc(var(--u)*.28) 0}.toc.tight .stg{margin:calc(var(--u)*.8) 0 calc(var(--u)*.2)}
.opener.long h2{font-size:calc(var(--u)*2.8)}.opener.long .story{font-size:calc(var(--u)*1.55)}.opener.long .osub{font-size:calc(var(--u)*1.4)}
.toc.one{grid-template-columns:1fr 1fr}
.zrow{display:flex;gap:calc(var(--u)*2);flex:1;min-height:0;align-items:stretch}
.zrow figure{flex:1;min-width:0;display:flex;flex-direction:column;min-height:0}
.zrow figure .im{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;background:#f7f5f0;border:1px solid #cfc8bb;border-radius:4px;overflow:hidden}
.zrow figure img{max-width:100%;max-height:100%;object-fit:contain;cursor:zoom-in}
.zrow figcaption{margin-top:calc(var(--u)*.6);font-size:calc(var(--u)*1.35);line-height:1.4;color:var(--ink)}
.zrow figcaption b{color:var(--navy)}

/* calculators */
.calc{display:grid;gap:calc(var(--u)*1.6);min-height:0}
.calc .cc{background:var(--stone);border-top:4px solid var(--gold);padding:calc(var(--u)*1.3) calc(var(--u)*1.6);border-radius:0 0 4px 4px}
.calc .cc h4{font-size:calc(var(--u)*1.85);margin-bottom:calc(var(--u)*.6)}
.calc label{display:grid;grid-template-columns:1fr calc(var(--u)*9.5);align-items:center;gap:calc(var(--u)*1);font-size:calc(var(--u)*1.45);line-height:1.3;margin:calc(var(--u)*.35) 0}
.calc input{width:100%;font:600 calc(var(--u)*1.7)/1 Plex,sans-serif;color:var(--navy);text-align:right;padding:calc(var(--u)*.55) calc(var(--u)*.8);
  background:#fff3c4;border:2px solid var(--gold2);border-radius:4px}
.calc input:focus{background:#fff8dc;border-color:var(--gold)}
.calc .eq{display:flex;justify-content:space-between;align-items:baseline;border-top:1px solid var(--rule);margin-top:calc(var(--u)*.6);padding-top:calc(var(--u)*.6);font-size:calc(var(--u)*1.45);color:var(--mute)}
.calc .eq output{font:700 calc(var(--u)*2.1)/1 Plex,sans-serif;color:var(--navy)}
.res{background:var(--navy);color:#fff;border-radius:4px;padding:calc(var(--u)*1.6) calc(var(--u)*2)}
.res .kicker{color:var(--gold2)}
.res .row{display:flex;justify-content:space-between;align-items:baseline;gap:calc(var(--u)*1);padding:calc(var(--u)*.75) 0;border-bottom:1px solid #24384f;font-size:calc(var(--u)*1.5);color:#d6dde7}
.res .row output{font:700 calc(var(--u)*2.3)/1 Plex,sans-serif;color:#fff;white-space:nowrap}
.res .row.big output{font-size:calc(var(--u)*3.2);color:var(--gold2)}
.res .row.big{color:#fff;font-weight:600}
.res .note{font-size:calc(var(--u)*1.2);color:#aeb9c7;margin-top:calc(var(--u)*.8);line-height:1.4}
.typehere{display:inline-flex;align-items:center;gap:calc(var(--u)*.8);font-size:calc(var(--u)*1.35);font-weight:600;color:var(--navy);background:#fff3c4;border:2px solid var(--gold2);border-radius:999px;padding:calc(var(--u)*.45) calc(var(--u)*1.2)}
.go{font:600 calc(var(--u)*1.4)/1 Plex,sans-serif;color:var(--navy);background:none;border:2px solid var(--gold);border-radius:999px;padding:calc(var(--u)*.7) calc(var(--u)*1.4);cursor:pointer}
.go:hover{background:var(--gold)}

/* mock (proposed illustration) */
.mock{border:2px dashed var(--gold);border-radius:6px;padding:calc(var(--u)*1.4);background:#fffdf7}
.mock .mh{font-size:calc(var(--u)*1.2);letter-spacing:.12em;text-transform:uppercase;font-weight:700;color:var(--mute);margin-bottom:calc(var(--u)*1)}
.mock .opt{display:grid;grid-template-columns:calc(var(--u)*2.2) 1fr;gap:calc(var(--u)*1);padding:calc(var(--u)*1) 0;border-top:1px solid var(--rule);font-size:calc(var(--u)*1.5)}
.mock .opt i{width:calc(var(--u)*1.5);height:calc(var(--u)*1.5);border:2px solid var(--navy);border-radius:50%;margin-top:calc(var(--u)*.3)}
.mock .opt.on i{background:radial-gradient(var(--gold) 45%,#fff 50%)}
.mock .opt b{color:var(--navy);font-size:calc(var(--u)*1.7)}
.mock .kv{display:flex;justify-content:space-between;color:var(--mute)}.mock .kv em{font-style:normal;font-weight:700;color:var(--navy)}

/* phone / narrow: reflow into a scrolling column with fixed sizes */
#app.flow #deck{left:0;top:0;transform:none;width:100%;height:100%}
#app.flow .pg{overflow-y:auto;-webkit-overflow-scrolling:touch;box-shadow:none}
#app.flow .pad{position:relative;inset:auto;min-height:100%;padding:28px 20px 70px}
#app.flow .folio{position:static;margin-top:28px}
#app.flow h1{font-size:40px}#app.flow h2{font-size:30px}#app.flow h3{font-size:24px}#app.flow h4{font-size:21px}
#app.flow .lede{font-size:21px}
#app.flow .cover,#app.flow .opener{display:flex;flex-direction:column;min-height:100%}
#app.flow .cover .r{height:46vw;order:-1}#app.flow .opener .r{height:62vw;order:-1;flex:none}
#app.flow .cover .l,#app.flow .opener .l{padding:28px 20px 40px;flex:1}
#app.flow .opener .num{font-size:64px}
#app.flow .opener .story{margin-top:22px}
#app.flow .art{display:flex;flex-direction:column}#app.flow .art img.bg{position:relative;height:56vw;flex:none}
#app.flow .art .ov{position:relative;background:var(--navy);padding:24px 20px 60px}
#app.flow .cols2{column-count:1}
#app.flow .split,#app.flow .split.even,#app.flow .split.wide,#app.flow .cards.c2,#app.flow .cards.c3,#app.flow .cards.c4,#app.flow .pts,#app.flow .rules,#app.flow .toc{grid-template-columns:1fr}
#app.flow .shot{flex-direction:column;height:auto}
#app.flow .zrow{flex-direction:column}#app.flow .zrow figure .im{height:auto}
#app.flow .shot .desk,#app.flow .shot .phone{height:auto}
#app.flow .shot .phone img{height:auto;width:62%;margin:0 auto}
#app.flow .capline{flex-direction:column}
#app.flow .mean{margin-top:24px}
#app.flow .calc label{grid-template-columns:1fr 120px}
#app.flow table.t td.g{white-space:normal}
#app.flow .side{display:none}
#app.flow [style*="grid-template-columns"]{grid-template-columns:1fr!important}
@media (max-width:700px){#top .s{display:none}#bar{gap:6px}#bar button,#bar select{padding:10px 13px;font-size:14px}#bar .count{min-width:auto;font-size:13px}#fs{display:none}}

/* print: one landscape page per screen */
@media print{
  @page{size:1600px 1000px;margin:0}
  html,body{background:#fff;height:auto}
  #top,#bar,.side,#zoom{display:none!important}
  #app{display:block;height:auto}#stage{overflow:visible}
  #deck{position:static;transform:none;width:1600px;height:auto;--u:16px!important}
  .pg{position:relative;width:1600px;height:1000px;opacity:1!important;visibility:visible!important;transform:none!important;box-shadow:none;break-after:page;page-break-after:always;transition:none}
  .start,.go{display:none}
}
"""

JS = r"""
const app = document.getElementById("app"), deck = document.getElementById("deck"), stage = document.getElementById("stage");
const pages = [...document.querySelectorAll(".pg")];
const N = pages.length;
const prevB = document.getElementById("prev"), nextB = document.getElementById("next"), sprev = document.getElementById("sprev"), snext = document.getElementById("snext");
const count = document.getElementById("count"), jump = document.getElementById("jump");
let cur = 0;
function layout(){
  const w = stage.clientWidth, h = stage.clientHeight;
  const flow = w < 760 || (w < 1000 && h > w * 1.05);
  app.classList.toggle("flow", flow);
  if (flow) { deck.style.setProperty("--u", "10.5px"); return; }
  const pad = w < 1100 ? 24 : 150;
  let pw = Math.min(w - pad, (h - 20) * 1.6), ph = pw / 1.6;
  deck.style.setProperty("--pw", Math.floor(pw) + "px"); deck.style.setProperty("--ph", Math.floor(ph) + "px");
  deck.style.setProperty("--u", (pw / 100).toFixed(3) + "px");
}
function show(i, fromHash){
  i = Math.max(0, Math.min(N - 1, i));
  pages.forEach((p, k) => { p.classList.toggle("on", k === i); p.classList.toggle("back", k < i); p.setAttribute("aria-hidden", k === i ? "false" : "true"); });
  cur = i;
  const p = pages[i];
  p.scrollTop = 0;
  count.textContent = (p.dataset.label || "") + " · " + (i + 1) + " of " + N;
  prevB.disabled = sprev.disabled = i === 0; nextB.disabled = snext.disabled = i === N - 1;
  if (!fromHash) history.replaceState(null, "", "#" + p.id);
  const sec = [...jump.options].filter(o => +o.dataset.i <= i).pop();
  jump.value = "";
}
prevB.onclick = sprev.onclick = () => show(cur - 1);
nextB.onclick = snext.onclick = () => show(cur + 1);
document.querySelectorAll("[data-go]").forEach(b => b.addEventListener("click", () => { const t = document.getElementById(b.dataset.go); if (t) show(pages.indexOf(t)); }));
jump.onchange = () => { if (jump.value !== "") show(+jump.value); jump.value = ""; };
document.addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT" || document.getElementById("zoom").classList.contains("on")) { if (e.key === "Escape") closeZoom(); return; }
  if (["ArrowRight", "PageDown", " "].includes(e.key)) { e.preventDefault(); show(cur + 1); }
  if (["ArrowLeft", "PageUp"].includes(e.key)) { e.preventDefault(); show(cur - 1); }
  if (e.key === "Home") show(0); if (e.key === "End") show(N - 1);
});
let tx = null, ty = null;
stage.addEventListener("touchstart", e => { if (e.target.closest("input")) { tx = null; return; } tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, {passive: true});
stage.addEventListener("touchend", e => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
  if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.4) show(cur + (dx < 0 ? 1 : -1)); tx = null; }, {passive: true});
const fs = document.getElementById("fs");
if (!(document.fullscreenEnabled || document.webkitFullscreenEnabled)) fs.style.display = "none";
fs.onclick = () => { const on = document.fullscreenElement || document.webkitFullscreenElement;
  if (on) (document.exitFullscreen || document.webkitExitFullscreen).call(document); else (app.requestFullscreen || app.webkitRequestFullscreen).call(app); };
const fsl = () => { fs.textContent = (document.fullscreenElement || document.webkitFullscreenElement) ? "✕ Exit full screen" : "⛶ Full screen"; };
document.addEventListener("fullscreenchange", fsl); document.addEventListener("webkitfullscreenchange", fsl);
const zoom = document.getElementById("zoom"), zimg = zoom.querySelector("img");
function closeZoom(){ zoom.classList.remove("on"); }
document.querySelectorAll(".shot img, img.z").forEach(im => im.addEventListener("click", () => { zimg.src = im.src; zimg.alt = im.alt; zoom.classList.add("on"); }));
zoom.addEventListener("click", closeZoom);
// calculators: same-named inputs share one value
const val = {};
document.querySelectorAll("input.ci").forEach(i => { if (val[i.dataset.n] === undefined) val[i.dataset.n] = i.value; });
// Same formulas as the CalibraytAI Supplier Economics Calculator, model version 2
// (app/services/supplier_economic_model.py); checked against it by verify_model.py.
const num = k => { const v = String(val[k] ?? "").replace(/[,$%\s]/g, ""); if (v === "" || isNaN(Number(v)) || Number(v) < 0) return null; return Number(v); };
function semModel(g){
  const R = {}, has = (...xs) => xs.every(x => x !== null);
  const q = g("takeoff_requests_per_month"), sh = g("takeoff_share_percent"), mh = g("manual_hours_per_takeoff"), vh = g("validation_hours_per_takeoff"),
        rate = g("estimator_cost_per_hour"), hpq = g("hours_per_quote"), cpq = g("contribution_per_quote"), mv = g("average_material_value"),
        conv = g("quote_to_order_percent"), mg = g("material_gross_margin_percent"), base = g("base_platform_cost"), act = g("active_contractor_cost"),
        unp = g("unpriced_requested_value"), cap = g("missed_capture_percent");
  const pct = x => x !== null && x <= 100 ? x : null;
  const share = pct(sh), cv = pct(conv), m = pct(mg), cp = pct(cap);
  R.annual_takeoff_volume = has(q) ? q * 12 : null;
  const orig = has(q, share) ? q * 12 * share / 100 : null;
  R.calibraytai_originated_takeoff_volume = orig;
  R.takeoff_labour_value = has(orig, mh, vh, rate) ? orig * mh * rate - orig * vh * rate : null;
  R.hours_released = has(orig, mh, vh) ? orig * (mh - vh) : null;
  R.additional_quote_capacity = has(R.hours_released, hpq) && hpq !== 0 ? R.hours_released / hpq : null;
  R.capacity_value = has(R.additional_quote_capacity, cpq) ? R.additional_quote_capacity * cpq : null;
  R.commercial_value = has(q, mv, cv, m) ? q * 12 * mv * cv / 100 * m / 100 : null;
  R.program_cost = has(base, act) ? base + act : null;
  R.operational_value = R.takeoff_labour_value === null ? null : R.takeoff_labour_value + (R.capacity_value ?? 0);
  R.net_supplier_value = has(R.operational_value, R.commercial_value, R.program_cost) ? R.operational_value + R.commercial_value - R.program_cost : null;
  R.takeoff_labour_value_won_quotes = has(R.takeoff_labour_value, cv) ? R.takeoff_labour_value * cv / 100 : null;
  R.takeoff_labour_value_unsuccessful_quotes = has(R.takeoff_labour_value, cv) ? R.takeoff_labour_value * (1 - cv / 100) : null;
  R.missed_opportunity_value = has(unp, cp, m) ? unp * cp / 100 * m / 100 : null;
  R.net_supplier_value_with_missed_opportunity = has(R.net_supplier_value, R.missed_opportunity_value) ? R.net_supplier_value + R.missed_opportunity_value : null;
  return R;
}
window.semModel = semModel;
const fmt = (x, dec) => x === null || x === undefined || !isFinite(x) ? "—" : x.toLocaleString("en-CA", {maximumFractionDigits: dec || 0, minimumFractionDigits: 0});
function recalc(){
  document.querySelectorAll("input.ci").forEach(i => { if (document.activeElement !== i) i.value = val[i.dataset.n] ?? ""; });
  const R = semModel(num);
  document.querySelectorAll("output.co").forEach(o => { const v = R[o.dataset.n]; o.textContent = v === null || v === undefined ? "—" : (v < 0 ? "−" : "") + (o.dataset.pre || "") + fmt(Math.abs(v)); });
}
document.querySelectorAll("input.ci").forEach(i => i.addEventListener("input", () => { val[i.dataset.n] = i.value; recalc(); }));
recalc();
window.addEventListener("resize", layout);
layout();
const h0 = location.hash.slice(1), t0 = h0 && document.getElementById(h0);
show(t0 ? pages.indexOf(t0) : 0, true);
window.addEventListener("hashchange", () => { const t = document.getElementById(location.hash.slice(1)); if (t && pages.indexOf(t) !== cur) show(pages.indexOf(t), true); });
"""


class Deck:
    def __init__(self, title, subtitle, page_title):
        self.title, self.subtitle, self.page_title = title, subtitle, page_title
        self.pages = []   # (id, label, html)
        self.menu = []    # (label, page id)

    def add(self, pid, label, body, cls="", menu=None):
        self.pages.append((pid, label, f'<section class="pg {cls}" id="{pid}" data-label="{E(label)}">{body}</section>'))
        if menu:
            self.menu.append((menu, pid))

    def html(self):
        idx = {pid: i for i, (pid, _, _) in enumerate(self.pages)}
        opts = '<option value="">Go to…</option>' + "".join(f'<option value="{idx[pid]}" data-i="{idx[pid]}">{E(lab)}</option>' for lab, pid in self.menu)
        body = "".join(h for _, _, h in self.pages)
        return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
                f'<title>{E(self.page_title)}</title><style>{FONT_CSS}{CSS}</style></head><body>'
                f'<div id="app"><div id="top"><span class="t">{E(self.title)}</span><span class="s">{E(self.subtitle)}</span></div>'
                f'<div id="stage"><button class="side" id="sprev" aria-label="Previous page">‹</button><div id="deck">{body}</div>'
                f'<button class="side" id="snext" aria-label="Next page">›</button></div>'
                f'<div id="bar"><button id="prev">‹ Previous</button><span class="count" id="count"></span><button id="next">Next ›</button>'
                f'<label for="jump" style="position:absolute;left:-9999px">Go to a chapter</label><select id="jump">{opts}</select>'
                f'<button id="fs">⛶ Full screen</button></div></div>'
                f'<div id="zoom" role="dialog" aria-label="Enlarged screen"><button class="x">✕ Close</button><img alt=""></div>'
                f'<script>{JS}</script></body></html>')


# ---------- page builders ----------
def folio(left, n=None):
    return f'<div class="folio"><span>{E(left)}</span><b>{n if n is not None else ""}</b></div>'


def P(paras):
    return "".join(f"<p>{E(x)}</p>" for x in paras)


def points(pts, dark=True, title="What it means"):
    inner = "".join(f'<div class="pt"><b>{E(h)}</b><span>{E(t)}</span></div>' for h, t in pts)
    return f'<div class="mean"><div class="kicker">{E(title)}</div><div class="pts">{inner}</div></div>'


def shot(desk, caption, phone=None, tag="Actual CalibraytAI screen", alt=""):
    ph = f'<div class="phone"><img src="{phone}" alt="The same screen on a phone"></div>' if phone else ""
    return (f'<div class="shot"><div class="desk"><img src="{desk}" alt="{E(alt or caption)}"></div>{ph}</div>'
            f'<div class="capline"><span class="cap">{E(caption)} <span class="hint">· Click the screen to enlarge</span></span><span class="tag">{E(tag)}</span></div>')


def ci(name, value, label, pre=""):
    return f'<label>{label}<input class="ci" data-n="{name}" value="{E(str(value))}" inputmode="decimal" autocomplete="off" aria-label="{E(label)}"></label>'


def co(name, label, pre="$", cls="eq"):
    return f'<div class="{cls}"><span>{E(label)}</span><output class="co" data-n="{name}" data-pre="{pre}"></output></div>'


def shots(items, caption, tag="Actual CalibraytAI screen"):
    """items: list of (uri, kind, alt) with kind desk | phone | doc."""
    parts = []
    for uri, kind, alt in items:
        if kind == "phone":
            parts.append(f'<div class="phone"><img src="{uri}" alt="{E(alt)}"></div>')
        else:
            parts.append(f'<div class="desk"><img src="{uri}" alt="{E(alt)}"></div>')
    return (f'<div class="shot">{"".join(parts)}</div>'
            f'<div class="capline"><span class="cap">{E(caption)} <span class="hint">· Click a screen to enlarge</span></span><span class="tag">{E(tag)}</span></div>')


# ---------- the shared economic worksheet (one implementation for every edition) ----------
EXAMPLE = {"active_contractor_accounts": 8, "takeoff_share_percent": 50, "takeoff_requests_per_month": 10, "manual_hours_per_takeoff": 3,
           "estimator_cost_per_hour": 80, "validation_hours_per_takeoff": 0.5, "hours_per_quote": 5, "contribution_per_quote": 400,
           "average_material_value": 10000, "quote_to_order_percent": 25, "material_gross_margin_percent": 20, "base_platform_cost": 5000,
           "active_contractor_cost": 3000, "unpriced_requested_value": 50000, "missed_capture_percent": 30}


def calc_pages(d, nxt, who, sponsor="Sponsorship and program cost", menu=True, accounts_label="Eligible Pro contractor accounts"):
    """Two worksheet pages using the Supplier Economics Calculator's own inputs and formulas (model version 2)."""
    X = EXAMPLE
    row = lambda n, l: ci(n, X[n], l)
    note = ('<p class="small" style="margin-top:calc(var(--u)*.7);font-size:calc(var(--u)*1.12);line-height:1.35"><b>How to read it.</b> Yellow boxes are assumptions: the example numbers are illustrative, '
            'so type over them. Capacity value is staff time, not cash, until hours are cut or used to sell more. Measured results come only later, from the store’s '
            'own Dashboard and Material demand pages. Same formulas as the CalibraytAI Supplier Economics Calculator.</p>')
    d.add("calc1", "The economics: time", f'''<div class="pad"><div class="kicker">The economics · 1 of 2 · Spend less</div>
<h2 style="margin-bottom:calc(var(--u)*.4)">The desk’s time, recovered.</h2>
<p style="margin-bottom:calc(var(--u)*1)"><span class="typehere">✎ Type over the example numbers. Answers update as you type.</span></p>
<div class="calc" style="grid-template-columns:1.15fr 1fr;align-items:start">
<div class="cc"><h4>⏱ Takeoffs and quotes at {E(who)}</h4>{row("takeoff_requests_per_month", "Takeoff requests a month")}{row("takeoff_share_percent", "Share starting from CalibraytAI, %")}
{row("manual_hours_per_takeoff", "Hours per takeoff by hand today")}{row("validation_hours_per_takeoff", "Hours to check a CalibraytAI takeoff")}
{row("estimator_cost_per_hour", "Estimator cost per hour, fully loaded, $")}{row("quote_to_order_percent", "Quotes that become orders, %")}
{row("hours_per_quote", "Estimator hours in one quote")}{row("contribution_per_quote", "Contribution from one more quote, $")}</div>
<div class="res"><div class="kicker">Each year</div>
<div class="row"><span>Hours released</span><output class="co" data-n="hours_released" data-pre=""></output></div>
<div class="row big"><span>Takeoff labour value</span><output class="co" data-n="takeoff_labour_value" data-pre="$"></output></div>
<div class="row"><span>· on quotes that are won</span><output class="co" data-n="takeoff_labour_value_won_quotes" data-pre="$"></output></div>
<div class="row"><span>· on unsuccessful quotes</span><output class="co" data-n="takeoff_labour_value_unsuccessful_quotes" data-pre="$"></output></div>
<div class="row"><span>Extra quotes the same hours allow</span><output class="co" data-n="additional_quote_capacity" data-pre=""></output></div>
<div class="row"><span>Capacity value (time, not cash)</span><output class="co" data-n="capacity_value" data-pre="$"></output></div>
<button class="go" data-go="calc2" style="margin-top:calc(var(--u)*.8);color:#fff">Sales, missed items and net ›</button></div></div>
{note}{folio("The economics", nxt())}</div>''', menu="The economics (calculator)" if menu else None)
    d.add("calc2", "The economics: sales and net", f'''<div class="pad"><div class="kicker">The economics · 2 of 2 · Sell more · Miss less</div>
<h2 style="margin-bottom:calc(var(--u)*.4)">Sales, missed items and the net.</h2>
<p style="margin-bottom:calc(var(--u)*1)"><span class="typehere">✎ The takeoff numbers from the previous page carry over.</span></p>
<div class="calc" style="grid-template-columns:1fr 1fr 1.05fr;align-items:start">
<div class="cc"><h4>↑ Sell more</h4>{row("average_material_value", "Material value of one opportunity, $")}{row("material_gross_margin_percent", "Material gross margin, %")}
<div class="eq"><span>Material gross profit</span><output class="co" data-n="commercial_value" data-pre="$"></output></div>
<h4 style="margin-top:calc(var(--u)*1)">▦ Miss less</h4>{row("unpriced_requested_value", "Asked for but not priced, a year, $")}{row("missed_capture_percent", "Share you could capture, %")}
<div class="eq"><span>Missed-item gross profit</span><output class="co" data-n="missed_opportunity_value" data-pre="$"></output></div></div>
<div class="cc"><h4>{E(sponsor)}</h4>{row("base_platform_cost", "Base platform cost, a year, $")}{row("active_contractor_cost", "Active contractor cost, a year, $")}
<div class="eq"><span>Total, a year</span><output class="co" data-n="program_cost" data-pre="$"></output></div>
<p class="small" style="margin-top:calc(var(--u)*.8)">Amounts the supplier enters for discussion. No price is set here, and sponsorship never makes a contractor exclusive.</p></div>
<div class="res"><div class="kicker">Net program economics, a year</div>
<div class="row"><span>Takeoff labour + capacity value</span><output class="co" data-n="operational_value" data-pre="$"></output></div>
<div class="row"><span>Material gross profit</span><output class="co" data-n="commercial_value" data-pre="$"></output></div>
<div class="row"><span>Less sponsorship and program cost</span><output class="co" data-n="program_cost" data-pre="−$"></output></div>
<div class="row big"><span>Net program value</span><output class="co" data-n="net_supplier_value" data-pre="$"></output></div>
<div class="row"><span>Plus missed items captured</span><output class="co" data-n="net_supplier_value_with_missed_opportunity" data-pre="$"></output></div></div></div>
{folio("The economics", nxt())}</div>''')


CONCEPT_CSS = r"""
.cgrid{display:grid;grid-template-columns:1.2fr 1.1fr 0.7fr;grid-template-rows:auto auto;gap:calc(var(--u)*1.1);align-items:stretch}
.cpanel{border:1px solid #cfc8bb;border-radius:6px;overflow:hidden;background:#fff;box-shadow:0 3px 12px rgba(8,23,36,.10);display:flex;flex-direction:column}
.cpanel .bar{background:var(--navy);color:#fff;font-size:calc(var(--u)*1);letter-spacing:.12em;text-transform:uppercase;font-weight:700;padding:calc(var(--u)*.5) calc(var(--u)*.9)}
.cpanel .body{padding:calc(var(--u)*.9) calc(var(--u)*1);font-size:calc(var(--u)*1.25);line-height:1.4;flex:1}
.cpanel .body b{color:var(--navy)}
.sbadge{display:inline-flex;align-items:center;gap:calc(var(--u)*.7);border:1px solid var(--rule);background:#fafaf7;border-radius:4px;padding:calc(var(--u)*.4) calc(var(--u)*.7);font-size:calc(var(--u)*1.05);color:var(--mute)}
.sbadge img{height:calc(var(--u)*2.1);width:auto}
.sbadge b{display:block;color:var(--navy);font-size:calc(var(--u)*1.15)}
.copt{display:flex;justify-content:space-between;align-items:center;gap:calc(var(--u)*.8);border-top:1px solid var(--rule);padding:calc(var(--u)*.55) 0}
.copt .btn{font-size:calc(var(--u)*1);font-weight:700;padding:calc(var(--u)*.35) calc(var(--u)*.7);border-radius:4px;background:var(--gold);color:var(--navy);white-space:nowrap}
.copt .btn.o{background:none;border:1.5px solid var(--navy)}
.ckv{display:flex;justify-content:space-between;border-top:1px solid var(--rule);padding:calc(var(--u)*.35) 0}
.ckv em{font-style:normal;font-weight:700;color:var(--navy)}
.cphone{border:calc(var(--u)*.5) solid var(--navy);border-radius:calc(var(--u)*1.6);overflow:hidden;background:#fff;grid-row:span 2;display:flex;flex-direction:column}
.cphone .top{background:var(--navy);color:#fff;font-size:calc(var(--u)*1);padding:calc(var(--u)*.8) calc(var(--u)*.7) calc(var(--u)*.5)}
.cphone .nav div{padding:calc(var(--u)*.5) calc(var(--u)*.7);border-bottom:1px solid var(--rule);font-size:calc(var(--u)*1.1)}
#app.flow .cgrid{grid-template-columns:1fr}
#app.flow .cphone{grid-row:auto}
"""


def sponsor_concept(d, nxt, pid, menu, sponsor_text, logo_uri, store, rewards_line, foot):
    """Proposed sponsorship recognition across CalibraytAI, adapted selectively from Joel's seven-panel concept.
    An illustration built from HTML, not a V1 screen; the only supplier artwork is the supplier's own logo file."""
    logo = f'<img src="{logo_uri}" alt="">' if logo_uri else ""
    badge = f'<span class="sbadge">{logo}<span><span>Sponsored by</span><b>{E(sponsor_text)}</b></span></span>'
    d.add(pid, menu, f'''<style>{CONCEPT_CSS}</style><div class="pad"><span class="flag">Proposed concept · Illustration, not a CalibraytAI V1 screen</span>
<h2 style="margin:calc(var(--u)*.6) 0 calc(var(--u)*.4)">Visible sponsorship. Never control.</h2>
<p style="font-size:calc(var(--u)*1.5);margin-bottom:calc(var(--u)*.9)">Where {E(store)} sponsors access, the contractor sees it in a few places. It never limits their choices.</p>
<div class="cgrid">
<div class="cpanel"><div class="bar">Contractor dashboard</div><div class="body"><div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><b style="font-size:1.25em">Welcome back</b>{badge}</div>
<p style="margin-top:calc(var(--u)*.6)">The sponsor appears beside the contractor’s own company name, as recognition, not as the owner of the account.</p></div></div>
<div class="cpanel"><div class="bar">Estimate · Supplier quotes</div><div class="body">
<div class="copt"><span><b>{E(store)}</b><br>Your sponsoring supplier</span><span class="btn">Request quote</span></div>
<div class="copt"><span><b>Any other supplier</b><br>The same list, your choice</span><span class="btn o">Request quote</span></div>
<div class="copt"><span><b>My own pricing</b><br>Nothing is shared</span><span class="btn o">Price it</span></div>
<p class="small" style="margin-top:calc(var(--u)*.4)">{E(rewards_line)}</p></div></div>
<div class="cphone"><div class="top">CalibraytAI<br><span style="opacity:.8">On the phone</span></div><div style="padding:calc(var(--u)*.6)"><span class="sbadge" style="flex-direction:column;align-items:flex-start">{logo}<span>Sponsored by <b>{E(sponsor_text)}</b></span></span></div>
<div class="nav"><div>Dashboard</div><div>Projects</div><div>Estimates</div><div>Calendar</div><div>Suppliers</div></div></div>
<div class="cpanel" style="grid-column:span 2"><div class="bar">Account settings · Sponsored access</div><div class="body" style="display:grid;grid-template-columns:1fr 1fr;gap:calc(var(--u)*1.4)">
<div><div class="ckv"><span>Sponsor</span><em>{E(sponsor_text)}</em></div><div class="ckv"><span>Account type</span><em>Sponsored contractor</em></div><div class="ckv"><span>Your data</span><em>Always under your control</em></div></div>
<div style="background:#eef4fb;border-radius:4px;padding:calc(var(--u)*.7)">Your projects, estimates and documents remain your property, and stay with you if your sponsorship changes. The sponsor never sees your account, clients, margins or labour rates.</div></div></div>
</div>
<p class="small" style="margin-top:calc(var(--u)*.5);font-size:calc(var(--u)*1.05);line-height:1.35">{E(foot)}</p>
{folio(menu, nxt())}</div>''', menu=menu)


HOOK_CSS = """<style>
.hook .hk{display:grid;grid-template-columns:repeat(3,1fr);gap:calc(var(--u)*1.6);margin-top:calc(var(--u)*1.6)}
.hook .hk>div{background:#fff;border:1px solid var(--line,#d9dee6);border-top:5px solid var(--gold);border-radius:6px;padding:calc(var(--u)*1.4) calc(var(--u)*1.5)}
.hook .hk b.n{display:block;font-family:Plex,sans-serif;font-size:calc(var(--u)*1.05);letter-spacing:.16em;text-transform:uppercase;color:var(--gold);margin-bottom:calc(var(--u)*.5)}
.hook .hk h4{font-size:calc(var(--u)*1.85);line-height:1.2;color:var(--navy);margin:0 0 calc(var(--u)*.6)}
.hook .hk p{font-size:calc(var(--u)*1.42);line-height:1.42;margin:0}
.hook .ask{display:flex;align-items:center;gap:calc(var(--u)*1.6);margin-top:auto;background:var(--navy);color:#fff;border-radius:6px;padding:calc(var(--u)*1.2) calc(var(--u)*1.6)}
.hook .ask p{flex:1;margin:0;font-family:Serif,Georgia,serif;font-size:calc(var(--u)*1.9);line-height:1.3;color:#fff}
.hook .ask button.go{color:#fff;white-space:nowrap}
.hook .fine{font-size:calc(var(--u)*1.1);color:#5b6675;margin-top:calc(var(--u)*.7)}
#app.flow .hook .hk{grid-template-columns:1fr}#app.flow .hook .ask{flex-direction:column;align-items:flex-start}
</style>"""


def hook_page(d, nxt, store, accounts, desk):
    """The opening argument: why a supplier would put CalibraytAI in its contractors' hands. One wording, every edition.
    store: who the reader is ("your store", "KBC"); accounts: their contractor customers; desk: where requests land."""
    cards = (("You are first in line",
              f"The price that comes back first and complete usually wins the order. When {accounts} estimate in CalibraytAI, "
              f"{store} is already connected: one click sends the takeoff to {desk} as a complete request. The contractor can still ask anyone else."),
             ("A reason to stay that is not a price cut",
              "CalibraytAI helps contractors plan, price and build their jobs. Offered by your store, it is a Pro Account benefit "
              "they use every day, and it keeps them coming back without another discount."),
             ("Your desk does less, and sees more",
              "Requests arrive ready to price, with nothing retyped, and the order comes back to the store that quoted it. "
              "You also see what contractors ask for that you do not price or stock."))
    hk = "".join(f'<div><b class="n">{i}</b><h4>{E(h)}</h4><p>{E(p)}</p></div>' for i, (h, p) in enumerate(cards, 1))
    d.add("hook", "Why give your contractors CalibraytAI", f'''{HOOK_CSS}<div class="pad hook"><div class="kicker">Why give your contractors CalibraytAI</div>
<h2>Put {E(store)} inside your contractors’ estimates.</h2>
<p class="lede">Give {E(accounts)} CalibraytAI, and the jobs they price can come to {E(desk)} as complete requests, ready to quote, before the work goes anywhere else.</p>
<div class="hk">{hk}</div>
<div class="ask"><p>What would that be worth to {E(store)}?</p><button class="go" data-go="calc1">Try your own numbers ›</button></div>
<p class="fine">A proposal for discussion. Contractors always choose their suppliers and what they share; sponsorship never makes a contractor exclusive.</p>
{folio("Why give your contractors CalibraytAI", nxt())}</div>''', menu="Why give your contractors CalibraytAI")

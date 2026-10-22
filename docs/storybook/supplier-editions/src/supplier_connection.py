"""CalibraytAI — Supplier Connection, screen edition (supplier-neutral). Content from nbuild/build_neutral.py."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import calc_pages, Deck, E, P, S, img, folio, points, shot, ci, co  # noqa: E402

A = f"{S}/nbuild/assets"
src = open(f"{S}/nbuild/build_neutral.py").read()
ns = {"E": E}
exec(src[src.index("CREDITS = ["):src.index("N_CSS = ")], ns)
CH, CREDITS, credit, PHOTO = ns["CH"], ns["CREDITS"], ns["credit"], ns["PHOTO"]
POS = {4: "100% 50%", 6: "100% 50%", 7: "72% 50%", 8: "100% 50%"}
GOALS = [("Sell more", "↑", "Get more of the work professional contractors are pricing. Every authorized request arrives complete and ready to price, and when the contractor buys, the order comes straight back to the supplier that priced it.",
          "Requests, quotes, quote-to-order conversion, orders and ordered value, measured period by period.", "Chapters 04–06"),
         ("Spend less", "⏱", "Do more business with the same staff: less time on every quote, every order and every delivery change. No retyping, no arithmetic, SKUs remembered.",
          "The minutes each quote takes, recorded by the desk, on the supplier’s own dashboard.", "Chapters 04 and 07"),
         ("Miss less", "▦", "Know what contractors are asking for: the products that keep coming back, and the items asked for but never priced, which are possible gaps in the range.",
          "Material demand totals every request, product by product, and lists possible range gaps.", "Chapter 08")]

d = Deck("CalibraytAI — Supplier Connection", "Connecting Contractors, Suppliers and Construction Projects.", "Supplier Connection Storybook")
n = [0]


def nxt():
    n[0] += 1
    return n[0]


# 1 cover
d.add("cover", "Cover", f'''<div class="l"><div class="kicker" style="color:var(--gold2)">The CalibraytAI Storybook</div>
<h1>CalibraytAI —<br><span>Supplier Connection</span></h1>
<div class="strap">Connecting Contractors, Suppliers and Construction Projects.</div>
<div class="sub">How one platform connects the people planning and building homes with the suppliers who provide the materials.</div>
<div class="ser">Supplier-neutral edition · October 2026</div>
<button class="start" data-go="intro">Start reading ›</button></div>
<div class="r"><img src="{img(f"{A}/art-supplier-hero.png", 1600, 82)}" alt="CalibraytAI connecting plans to materials"></div>''', "cover", menu="Cover")
d.add("connect", "Supplier Connection", f'''<img class="bg" src="{img(f"{A}/web-connection.png", 1900, 80)}" alt="" style="object-fit:contain;background:#000">
<div class="ov"><div class="kicker" style="color:var(--gold2)">Supplier Connection</div>
<h2>The contractor plans and prices. <span>The supplier quotes and delivers.</span></h2>
<p>CalibraytAI connects the two on one record: the request, the quote, the order and the delivery, each agreed and kept.</p>
<div class="lifeline">REQUEST → QUOTE → ORDER → CONFIRM → DELIVER</div></div>''', "art dark")
d.add("intro", "Introduction", f'''<div class="pad"><div class="kicker">Introduction</div>
<h2>From the estimate to the delivery, one connected workflow.</h2>
<div class="split"><div>{P(["Residential construction runs on materials. Every home passes through estimates, supplier quotes, purchase orders and delivery dates, and most of that still moves by phone, email and spreadsheet.",
 "CalibraytAI is a construction platform contractors use to plan, price and build their projects. Supplier Connection links a contractor’s projects to the building suppliers they choose: the request goes out complete, the quote comes back priced, the order is placed and signed, and the delivery is agreed, all on one record.",
 "This book follows one residential project, the Harbour Lane pool deck. The projects, companies and people are synthetic; every application image is an actual CalibraytAI screen."])}</div>
<figure><img class="photo" src="{img(f"{A}/photo-nintro.jpg", 1400, 80)}" alt="A new home under construction" style="height:calc(var(--u)*30)"><figcaption class="small" style="margin-top:6px">{E(credit("Introduction"))}</figcaption></figure></div>
{folio("Introduction", nxt())}</div>''', menu="Introduction")

# contents (filled after pages exist: ids are known in advance)
TOC = [("The opportunity", [("·", "The economics: time", "calc1"), ("·", "The economics: sales and net", "calc2"), ("·", "Sell more. Spend less. Miss less.", "goals")]),
       ("The connection", [("·", "One journey, three roles", "roles"), ("·", "Trust by design", "trust")]),
       ("The journey", [(f'{c["n"]:02d}', c["title"], f'ch{c["n"]}') for c in CH]),
       ("Next", [("·", "What you just read", "recap"), ("·", "Supplier-sponsored access", "spons"), ("·", "The intelligence ahead", "ai"),
                 ("·", "Supplier choice and loyalty", "choose"), ("·", "A supplier network demonstration", "demo"),
                 ])]
col1 = "".join(f'<div class="tocgrp"><div class="stg">{E(st)}</div>' + "".join(f'<button data-go="{pid}"><i>{E(k)}</i><b>{E(t)}</b><span>›</span></button>' for k, t, pid in items) + "</div>" for st, items in (TOC[0], TOC[1], TOC[3]))
col2 = "".join(f'<div class="tocgrp"><div class="stg">{E(st)}</div>' + "".join(f'<button data-go="{pid}"><i>{E(k)}</i><b>{E(t)}</b><span>›</span></button>' for k, t, pid in items) + "</div>" for st, items in (TOC[2],))
d.add("contents", "Contents", f'''<div class="pad"><div class="kicker">Contents · Click any line to go there</div>
<h2 style="margin-bottom:0">Ten steps, one connection</h2>
<div class="toc tight"><div>{col1}</div><div>{col2}</div></div>{folio("Contents", nxt())}</div>''', menu="Contents")

# calculators
calc_pages(d, nxt, "the supplier", "Optional sponsorship and program cost")
gl = "".join(f'<div class="card"><h4>{ic} {E(nm)}</h4><p>{E(pr)}</p><p class="small" style="margin-top:calc(var(--u)*.8)"><b>The proof:</b> {E(pf)} <b style="color:var(--gold)">{E(chs)}</b></p></div>' for nm, ic, pr, pf, chs in GOALS)
d.add("goals", "Three goals", f'''<div class="pad"><div class="kicker">Three goals for the supplier</div>
<h2>Sell more. Spend less. Miss less.</h2>
<p class="lede" style="margin-bottom:calc(var(--u)*2)">Supplier Connection brings professional contractors’ work straight to the suppliers they choose. For a participating supplier, that adds up to three goals, each measured on its own pages.</p>
<div class="cards c3">{gl}</div>

{folio("Three goals", nxt())}</div>''', menu="Sell more. Spend less. Miss less.")

d.add("roles", "One journey, three roles", f'''<div class="pad"><div class="kicker">The connection</div>
<h2>One journey, three roles.</h2>
<p class="lede" style="margin-bottom:calc(var(--u)*2)">The value is not only in producing an estimate. It is in connecting the estimate to supplier selection, purchasing and the schedule, so each party does its part once.</p>
<div class="cards c3">
<div class="card"><h4>The contractor</h4><p>Plans and prices the project, chooses the supplier and what to share, approves the price and places the order. Owns the project record.</p></div>
<div class="card"><h4>The supplier</h4><p>Prices the request, sells the materials, confirms the order and the delivery, and manages the commercial relationship.</p></div>
<div class="card"><h4>The fulfillment partner</h4><p>Manufactures, distributes or delivers part of an order for the supplier, under the supplier’s own arrangement.</p></div></div>
<div class="pull" style="margin-top:auto">The contractor plans and prices. The supplier quotes and delivers. CalibraytAI connects them.<small>Supplier Connection</small></div>
{folio("The connection", nxt())}</div>''', menu="One journey, three roles")
sees = ["Items, quantities and units", "The date needed and the delivery town", "The contractor’s company and contact", "A project reference", "On a purchase order: the delivery address, date, window and site contact"]
never = ["The client’s name", "The contractor’s margins, labour rates or internal costs", "Other suppliers’ prices", "Estimates, or projects not sent to the supplier", "The site address before an order"]
d.add("trust", "Trust by design", f'''<div class="pad"><div class="kicker">Trust by design</div>
<h2>Each side sees what it needs to do business, and nothing more.</h2>
<div class="cards c2" style="flex:1;align-content:start">
<div class="card"><h4>What a request shows the supplier</h4><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in sees)}</ul></div>
<div class="card" style="border-color:#a33a2c"><h4>What it never shows</h4><ul class="ticks no">{"".join(f"<li>{E(x)}</li>" for x in never)}</ul></div></div>
{folio("Trust by design", nxt())}</div>''', menu="Trust by design")
principles = [("Independent accounts.", "Every contractor has their own account and owns their project record."),
              ("Only what is authorized.", "A supplier receives only what the contractor sends it."),
              ("Private stays private.", "Estimates, margins, labour rates and unrelated projects are never shared."),
              ("No price peeking.", "A supplier never sees another supplier’s price."),
              ("No exclusivity.", "Sponsorship or a preferred supplier never stops a contractor choosing another."),
              ("Aggregate means anonymous.", "Program and demand figures count contractors without naming them or their jobs.")]
rr = "".join(f'<div class="rule"><i>{i}</i><div><b>{E(a)}</b><span>{E(b)}</span></div></div>' for i, (a, b) in enumerate(principles, 1))
d.add("trust2", "Six privacy principles", f'''<div class="pad"><div class="kicker">Trust by design · Six principles</div>
<h2>Privacy is built in, not added on.</h2>
<div class="rules">{rr}</div>
{folio("Trust by design", nxt())}</div>''')

SHOTS = {
    2: (("n-takeoff",), None), 3: (("n-send",), None), 4: (("n-inbox",), "n-inbox-ph"), 5: (("n-approve",), None),
    6: (("n-po",), "n-po-ph"), 7: (("n-delivery",), None), 8: (("n-dashboard",), None), 9: (("n-contractor",), None), 10: (("n-areas",), None),
}
for c in CH:
    k = c["n"]
    title = f'{k:02d} · {c["title"]}'
    pos = POS.get(k, "50% 50%")
    d.add(f"ch{k}", title, f'''<div class="l"><div class="num">{k:02d}</div><div class="kicker" style="color:var(--gold2);margin-top:calc(var(--u)*1)">Chapter {k:02d}</div>
<h2>{E(c["title"])}</h2><div class="osub">{E(c["sub"])}</div><p class="story">{E(c["story"])}</p></div>
<div class="r"><img src="{img(f"{A}/photo-{PHOTO[k]}.jpg", 1500, 80)}" alt="" style="object-position:{pos}"><div class="credit">{E(credit(f"Chapter {k:02d}"))}</div></div>''',
          "opener", menu=title)
    long_ch = sum(len(x.split()) for x in c["body"]) > 105
    pt_block = f'<div style="margin-top:auto;padding-top:calc(var(--u)*1.2)">{points(c["points"])}</div>'
    pt_text, pt_shot = ("", pt_block) if long_ch else (pt_block, "")
    d.add(f"ch{k}t", title, f'''<div class="pad"><div class="kicker">Chapter {k:02d} · {E(c["title"])}</div>
<h2>{E(c["headline"])}</h2><div class="cols2 big">{P(c["body"])}</div>
{pt_text}
{folio(title, nxt())}</div>''')
    if k == 1:
        rows = "".join(f'<tr><td class="m">{E(a)}</td><td><b style="color:var(--navy)">{E(b)}</b></td></tr>' for a, b in c["table"])
        body = f'<table class="t"><tr><th>The patchwork today</th><th>With Supplier Connection</th></tr>{rows}</table>'
    else:
        (dk,), ph = SHOTS[k]
        cap = c["fig"][2]
        body = shot(img(f"{A}/screen-{dk}.png", 2000, 82), cap, img(f"{A}/screen-{ph}.png", 700, 85) if ph else None)
    calc_btn = '<button class="go" data-go="calc1" style="align-self:flex-start;margin-top:calc(var(--u)*1)">⏱ Work out the desk’s time savings ›</button>' if k == 4 else ""
    d.add(f"ch{k}s", title, f'''<div class="pad"><div class="kicker">Chapter {k:02d} · {"The difference" if k == 1 else "On screen"}</div>
{body}{calc_btn}
{pt_shot}
{folio(title, nxt())}</div>''')

# closing section
recap = [("Sell more", "Authorized requests arrive complete; orders come back against the supplier’s own quote.", "Requests, quotes returned, quote-to-order conversion"),
         ("Spend less", "Totals calculated, SKUs remembered, orders signed, deliveries agreed in writing.", "Minutes per quote, lines per request, delivery changes"),
         ("Miss less", "Every request adds to material demand; items asked for but not priced are listed.", "Recurring products, possible range gaps, ordered from you")]
rows3 = "".join(f'<tr><td class="g">{E(a)}</td><td>{E(b)}</td><td class="m">{E(c)}</td></tr>' for a, b, c in recap)
d.add("recap", "What you just read", f'''<div class="pad"><div class="kicker">What you just read</div>
<h2>Sell more. Spend less. Miss less.</h2>
<p class="lede" style="margin-bottom:calc(var(--u)*1.4)">CalibraytAI gives a participating supplier the opportunity to sell more, spend less and miss less, by connecting professional contractors directly to its business while preserving contractor independence.</p>
<table class="t"><tr><th>Goal</th><th>What you saw</th><th>Proof on the supplier’s pages</th></tr>{rows3}</table>
<div style="display:flex;gap:12px;margin-top:auto"><button class="go" data-go="calc1">↺ Revisit the calculator</button><button class="go" data-go="demo">See the demonstration ›</button></div>
{folio("What you just read", nxt())}</div>''', menu="What you just read")
getc = ["CalibraytAI to run their jobs: calculators, takeoffs, estimates, supplier requests, orders and deliveries.", "The supplier one step away, with a Send to supplier button on every takeoff.", "A sponsored start, as part of their trade account with the supplier."]
supg = ["Sell more: more professional contractors sending their jobs to the supplier first.", "Spend less: every sponsored account priced the same fast way.", "Miss less: more of its contractors’ demand in Material demand.", "Engagement: sponsored accounts activated and repeat use, reported as totals only."]
srules = [("Access, not control.", "The supplier never sees the contractor’s account, projects, clients, margins or labour rates."),
          ("Not exclusive.", "A sponsored contractor can still choose another supplier, or price a job themselves."),
          ("Portable.", "If sponsorship ends, the contractor keeps their account and their history.")]
d.add("spons", "Supplier-sponsored access", f'''<div class="pad"><span class="flag">Proposed · Optional</span>
<h2>Supplier-sponsored access to CalibraytAI.</h2>
<div class="cards c3" style="grid-template-columns:1fr 1fr 1fr">
<div class="card"><h4>The contractor gets</h4><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in getc)}</ul></div>
<div class="card"><h4>The supplier gets</h4><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in supg)}</ul></div>
<div class="card" style="background:var(--navy);color:#fff"><h4 style="color:#fff">The rules</h4>{"".join(f'<p style="color:#dfe5ee"><b style="color:var(--gold2)">{E(a)}</b> {E(b)}</p>' for a, b in srules)}</div></div>
{folio("Supplier-sponsored access", nxt())}</div>''', menu="Supplier-sponsored access")
airows = [("Sell more", "Read the sketch", "CalibraytAI reads a customer’s sketch and asks the questions a good counter person would, so a rough drawing becomes a priced list."),
          ("Spend less", "Pre-price the request", "Suggested SKU matches and prices from the supplier’s own quoting history, ready for the desk to check and send."),
          ("Miss less", "Forecast the demand", "Demand forecast by product and season, and items worth stocking flagged before the gaps repeat.")]
tr = "".join(f'<tr><td class="g">{E(a)}</td><td><b style="color:var(--navy)">{E(b)}</b><br>{E(c)} <span class="tag next">Next</span></td></tr>' for a, b, c in airows)
d.add("ai", "The intelligence ahead", f'''<div class="pad"><div class="kicker">The intelligence ahead</div>
<h2>AI and machine learning, built on your data.</h2>
<p class="lede" style="margin-bottom:calc(var(--u)*1.2)">Every request, quote, order and gap is recorded from the first day, in clean, structured form: exactly what AI and machine learning need.</p>
<table class="t"><tr><th>Goal</th><th>What comes next</th></tr>{tr}</table>
<div class="pull" style="margin-top:auto">The sooner a supplier starts, the more its data is worth.<small>Construction intelligence. Calibrated.</small></div>
{folio("The intelligence ahead", nxt())}</div>''', menu="The intelligence ahead")
d.add("choose", "Supplier choice and loyalty", f'''<div class="pad"><span class="flag">Proposed · Illustration, not a current screen</span>
<h2>Your price and your rewards, in the contractor’s estimate.</h2>
<div class="split wide"><div class="mock"><div class="mh">Estimate · Harbour Lane Pool Deck · Choose a supplier</div>
<div class="opt on"><i></i><div><b>Participating Building Supplier</b><div class="kv"><span>Your contractor price</span><em>$3,573.22</em></div><div class="kv"><span>Optional loyalty rewards</span><em>per the supplier’s program</em></div><div class="kv"><span>Rewards balance</span><em>with an authorized connection</em></div></div></div>
<div class="opt"><i></i><div><b>Another supplier</b><div>Send the same list to any supplier you choose</div></div></div>
<div class="opt"><i></i><div><b>My own pricing</b><div>Price it yourself; nothing is shared</div></div></div></div>
<div><p>When a contractor chooses a participating supplier in the estimate, CalibraytAI would show that supplier’s contractor-specific price and, where the supplier offers one, the loyalty rewards the order would earn.</p>
<p>The contractor chooses the supplier and what is shared. Prices and rewards would come only from each supplier, through a connection it authorizes.</p>
<p class="small">The $3,573.22 is the synthetic quote used in this book. Nothing on this page is live today.</p></div></div>
{folio("Supplier choice and loyalty", nxt())}</div>''', menu="Supplier choice and loyalty")
d.add("demo", "A supplier network demonstration", f'''<img class="bg" src="{img(f"{A}/photo-nclose.jpg", 1900, 80)}" alt="">
<div class="credit" style="top:12px;bottom:auto">{E(credit("A supplier network demonstration"))}</div>
<div class="ov"><div class="kicker" style="color:var(--gold2)">Next steps</div><h2>A supplier network demonstration.</h2>
<div class="cards c4" style="margin-top:calc(var(--u)*1)">{"".join(f'<div class="card" style="background:rgba(255,255,255,.95)"><h4 style="font-size:calc(var(--u)*1.7)">{E(a)}</h4><p>{E(b)}</p></div>' for a, b in (
    ("Sign-ins", "The staff who quote get Supplier Connection sign-ins for their supplier area."),
    ("Real requests", "Participating contractors send material and concrete requests through Supplier Connection."),
    ("Watch the figures", "Requests, quotes, orders, quoting time and demand, on the supplier’s own pages."),
    ("Grow the network", "Add locations, suppliers and contractors on the same connection.")))}</div>
<p style="margin-top:calc(var(--u)*1.2)"><b style="color:var(--gold2)">Arrange a walkthrough:</b> a request, a quote, an order and a delivery change, start to finish, on actual CalibraytAI screens.</p></div>''', "art dark", menu="A supplier network demonstration")
crs = "".join(f"<tr><td>{E(k)}</td><td class='m'>{E(w)} · {E(s)}</td></tr>" for k, w, s in CREDITS)
d.add("notes", "Notes and credits", f'''<div class="pad"><div class="kicker">About this book</div><h2>Notes and credits</h2>
<div class="split even" style="font-size:calc(var(--u)*1.42);line-height:1.45"><div>
<p><b>The story.</b> The Harbour Lane project, the contractor, the suppliers and the people in this book are synthetic. Every application image is an actual CalibraytAI screen, captured on 21 October 2026 from a synthetic company. The Fulfillment Partner is described, not shown: it is not connected to CalibraytAI.</p>
<p><b>Supplier Connection</b> is labelled “Supplier Hub” on screen.</p>
<p><b>Not yet live.</b> Capabilities not yet live are labelled where they appear. Signing is built and tested and goes live with its next release.</p>
<p><b>Branding.</b> CalibraytAI artwork and the approved CalibraytAI logo. No supplier’s name or logo is used. Company names on the Chapter 07 trucks are softened.</p></div>
<table class="t tight" style="font-size:calc(var(--u)*1.12)">{crs}</table></div>
{folio("CalibraytAI · Supplier Connection", nxt())}</div>''', menu="Notes and credits")
d.add("end", "Back cover", f'''<div class="l" style="justify-content:center"><img src="{img(f"{A}/approved-logo-v1-dark-reference.png", 900, 90)}" alt="CalibraytAI" style="width:70%;margin-bottom:calc(var(--u)*2)">
<h2 style="color:#fff">Your projects. Your suppliers. <span style="color:var(--gold2)">One connection.</span></h2>
<p style="color:#c3ccd8">From the contractor’s takeoff to the supplier’s confirmed delivery, CalibraytAI connects every project to the suppliers the contractor chooses.</p>
<div class="lifeline">REQUEST → QUOTE → ORDER → CONFIRM → DELIVER</div>
<button class="start" data-go="contents">‹ Back to contents</button></div>
<div class="r"><img src="{img(f"{A}/art-build-neutral.jpg", 1500, 80)}" alt="A builder reviewing the supplier dashboard on a tablet" style="object-fit:cover;object-position:50% 55%"></div>''', "cover")

out = f"{S}/deck/out/supplier-connection.html"
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w").write(d.html())
print(out, len(d.pages), "pages", round(os.path.getsize(out) / 1e6, 2), "MB")

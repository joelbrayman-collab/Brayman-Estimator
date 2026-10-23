"""Your Price in More Estimates — BMR Winchester edition, screen edition.
Content read (not modified) from sbuild/build_store.py; assets from sbuild/assets."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import hook_page, sponsor_concept, calc_pages, Deck, E, P, S, img, folio, points, shots, ci, co  # noqa: E402

A = f"{S}/sbuild/assets"
BR = f"{S}/deck/brand"
BMRLOGO = img(f"{BR}/bmr-logo-site-342x90.png", 342, 95)  # official bmr.ca site logo, as served (see deck/brand/SHA256SUMS)
ELEV = img(f"{BR}/bmr-pro-elevation-360-banner-1260x340.jpg", 1260, 85)  # BMR's own Elevation 360 graphic from bmr.ca
src = open(f"{S}/sbuild/build_store.py").read()
ns = {"E": E}
exec(src[src.index("CREDITS = ["):src.index("STARTS = {")], ns)
CH, PILLARS, CREDITS, credit = ns["CH"], ns["PILLARS"], ns["CREDITS"], ns["credit"]
PHOTO = {1: "d01", 2: "d02", 3: "d03", 4: "d04c", 5: "d04", 6: "d05", 7: "d06", 8: "d07", 9: "d08"}
POS = {1: "100% 50%", 2: "100% 50%", 3: "100% 50%", 7: "75% 50%", 9: "100% 50%"}

d = Deck("Your Price in More Estimates · BMR Winchester", "Sell more. Spend less. Miss less. · with CalibraytAI", "CalibraytAI Supplier Storybook")
n = [0]


def nxt():
    n[0] += 1
    return n[0]


def SC(k, w=2000):
    return img(f"{A}/screen-{k}.png", w, 82 if w > 1000 else 85)


d.add("cover", "Cover", f'''<div class="l"><div class="kicker" style="color:var(--gold2)">The CalibraytAI Supplier Opportunity</div>
<h1>Your Price in<br><span>More Estimates</span></h1>
<div class="strap">Sell more. Spend less. Miss less.</div>
<div class="sub">How CalibraytAI gives BMR Winchester’s Pro Accounts an end-to-end way to run their business, and brings them closer to BMR.</div>
<div style="margin-top:calc(var(--u)*2.2);display:flex;align-items:center;gap:calc(var(--u)*1.2)"><span style="background:#fff;border-radius:4px;padding:calc(var(--u)*.5) calc(var(--u)*.8);line-height:0"><img src="{BMRLOGO}" alt="BMR" style="height:calc(var(--u)*3)"></span><div class="ser" style="margin-top:0">Prepared for BMR Winchester<br>October 2026</div></div>
<button class="start" data-go="intro">Start reading ›</button></div>
<div class="r"><img src="{img(f"{A}/art-supplier-hero.png", 1600, 82)}" alt="CalibraytAI connecting plans to materials"></div>''', "cover", menu="Cover")
d.add("connect", "Supplier Connection", f'''<img class="bg" src="{img(f"{A}/web-connection.png", 1900, 80)}" alt="">
<div class="ov"><div class="kicker" style="color:var(--gold2)">Supplier Connection</div>
<h2>Let your Pro Account contractors <span>do the work for you.</span></h2>
<p>CalibraytAI connects your Pro Accounts to your Pro Desk by streamlining the entire estimate, order and delivery process.</p>
<div class="lifeline">ESTIMATE → ORDER → DELIVER</div>
<p style="margin-top:calc(var(--u)*1.4);font-size:calc(var(--u)*1);line-height:1.4;color:#aab4c2;max-width:60em">The BMR, BMR PRO and Elevation 360 names and logos shown in this book are used for illustrative purposes only, to facilitate discussion. They belong to BMR Group. Their use does not mean BMR Group or BMR Winchester has endorsed, approved or agreed to the proposed partnership or sponsorship.</p></div>''', "art dark hero")
hook_page(d, nxt, "BMR Winchester", "your Pro Account contractors", "your Pro Desk")
d.add("intro", "Introduction", f'''<div class="pad"><div class="kicker">Introduction</div>
<h2>Getting your price into more estimates.</h2>
<div class="split"><div style="font-size:calc(var(--u)*1.62)">{P(["Brayman Construction is a residential contractor that buys its building materials, and its concrete, from BMR Winchester; BMR supplies the concrete through its own purchasing relationship with Tomlinson. CalibraytAI is the platform Brayman built to run its own jobs. The Supplier Hub is the part of CalibraytAI that connects a contractor’s jobs to the stores that supply them.",
 "When a contractor prices a job, the supplier whose price is in the estimate is the one most likely to get the order. Dealers take almost three days on average to return a contractor’s quote, and builders rank speed of response above price.¹ CalibraytAI gets BMR Winchester’s price back first, with less work at the Pro Desk. This book shows how, in three goals: sell more, spend less and miss less."])}
<p class="small" style="margin-top:calc(var(--u)*1)">¹ Buildxact and The Farnsworth Group, research with North American builders and dealers, 2022: most builders rated a dealer’s speed of response above price, and dealers took 2.7 days on average to answer a request for a quote.</p></div>
<figure><img class="photo" src="{img(f"{A}/photo-intro2.jpg", 1400, 80)}" alt="" style="height:calc(var(--u)*30)"><figcaption class="small" style="margin-top:6px">{E(credit("Introduction"))}</figcaption></figure></div>
{folio("Introduction", nxt())}</div>''', menu="Introduction")

later = [("·", "What you just read", "recap"), ("·", "A BMR PRO-sponsored experience", "spons"), ("·", "Sponsorship in the app (concept)", "sponsview"), ("·", "The intelligence ahead", "ai"),
         ("·", "Supplier choice and rewards", "choose"), ("·", "Trust, both ways", "trust"), ("·", "Let’s run a pilot", "pilot"), ("·", "Notes and credits", "notes")]


def grp(st, items):
    return f'<div class="tocgrp"><div class="stg">{E(st)}</div>' + "".join(f'<button data-go="{pid}"><i>{E(k)}</i><b>{E(t)}</b><span>›</span></button>' for k, t, pid in items) + "</div>"


col1 = grp("The plan", [("·", "The economics: time", "calc1"), ("·", "The economics: sales and net", "calc2"), ("·", "Two sides of every Pro job", "sides")])
col1 += grp("Part 1 · Sell more", [(f'{c["n"]:02d}', c["title"], f'ch{c["n"]}') for c in CH if c["p"] == 1])
col2 = grp("Part 2 · Spend less", [(f'{c["n"]:02d}', c["title"], f'ch{c["n"]}') for c in CH if c["p"] == 2])
col2 += grp("Part 3 · Miss less", [(f'{c["n"]:02d}', c["title"], f'ch{c["n"]}') for c in CH if c["p"] == 3])
col2 += grp("Growing together", [x for x in later if x[2] != "notes"])
d.add("contents", "Contents", f'''<div class="pad"><div class="kicker">Contents · Click any line to go there</div>
<h2 style="margin-bottom:0;font-size:calc(var(--u)*2.7)">What doing business a more streamlined way could be worth</h2>
<div class="toc tight"><div>{col1}</div><div>{col2}</div></div>{folio("Contents", nxt())}</div>''', menu="Contents")

calc_pages(d, nxt, "BMR Winchester", "BMR PRO sponsorship and program cost")
gets = [("Jobs, ready to price", "Items, quantities and units from the contractor’s own takeoff, final lines marked."),
        ("The when and the where", "The date needed and the delivery town, with one contact."),
        ("Purchase orders against your quote", "The lines, the total, the address, the date, the window and the site contact."),
        ("Changes in writing", "A delivery moves only with a reason, and only when you accept."),
        ("Your price, used as returned", "Recorded and approved line by line, never retyped.")]
gives = [("Your SKU on each line", "The product you will actually supply."), ("Your price and your discount", "Entered fresh; CalibraytAI does the totals."),
         ("A valid-until date", "So everyone knows how long the price holds."), ("Substitutions, by line", "Before anything is ordered, not at the yard."),
         ("A confirmed delivery", "The date the yard can make, or a problem flagged early.")]
li = lambda rows: "".join(f"<li><b>{E(a)}.</b> {E(b)}</li>" for a, b in rows)
d.add("sides", "Two sides of every Pro job", f'''<div class="pad"><div class="kicker">The plan</div>
<h2 style="margin-bottom:calc(var(--u)*.8)">Two sides of every Pro job.</h2>
<div class="cards c2" style="align-content:start"><div class="card"><h4>What the contractor sends you</h4><ul class="ticks" style="font-size:.95em">{li(gets)}</ul></div>
<div class="card" style="background:var(--navy)"><h4 style="color:#fff">What you send back</h4><ul class="ticks" style="font-size:.95em">{"".join(f'<li style="color:#e6ebf1"><b style="color:var(--gold2)">{E(a)}.</b> {E(b)}</li>' for a, b in gives)}</ul></div></div>
{folio("The plan", nxt())}</div>''', menu="Two sides of every Pro job")
d.add("why", "Why it pays", f'''<div class="pad"><div class="kicker">The plan</div>
<h2>Why it pays.</h2>
<p class="lede">The contractor’s estimate is built from the prices that come back first and complete. CalibraytAI gets BMR Winchester’s quote back fast, and when the contractor buys, the purchase order comes straight back to the store that priced it.</p>
<div class="card" style="margin-top:calc(var(--u)*2)"><h4>Fully automatic, when connected <span class="tag future">Future integration</span></h4><p>With an authorized connection to BMR’s cost system, the whole quote can be produced automatically. Requests arrive already priced, and the Pro Desk only approves.</p></div>
{folio("The plan", nxt())}</div>''')

for k in (1, 2, 3):
    pl = PILLARS[k]
    chs = [c for c in CH if c["p"] == k]
    chl = "".join(f'<button data-go="ch{c["n"]}"><i>{c["n"]:02d}</i><b>{E(c["title"])}{" · next" if c.get("proposed") else ""}</b><span>›</span></button>' for c in chs)
    d.add(f"part{k}", f'Part {k} · {pl["name"]}', f'''<div class="pad" style="justify-content:center"><div class="num" style="font-family:Serif,Georgia,serif;font-size:calc(var(--u)*7);color:transparent;-webkit-text-stroke:2px var(--gold2);line-height:1">0{k}</div>
<div class="kicker" style="color:var(--gold2);margin-top:calc(var(--u)*1)">Part {k} · Goal</div>
<h1 style="color:#fff">{pl["icon"]} {E(pl["name"])}.</h1>
<p class="lede" style="max-width:34em;margin-top:calc(var(--u)*1)">{E(pl["promise"])}</p>
<div class="toc" style="grid-template-columns:1fr;max-width:40em;margin-top:calc(var(--u)*1.6)"><div>{chl}</div></div></div>''', "dark", menu=f'Part {k} · {pl["name"]}')
    d.add(f"part{k}m", f'Part {k} · {pl["name"]}', f'''<div class="pad"><div class="kicker">Part {k} · {E(pl["name"])}</div>
<h2>What it means for BMR Winchester.</h2>
<div class="split wide"><div style="font-size:calc(var(--u)*1.6)">{P(pl["means"])}</div>
<div class="card"><h4>The proof, on the store’s {E(pl["where"])} page</h4><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in pl["measures"])}</ul>
<p class="small">Counted from what actually happens in CalibraytAI, period by period.</p></div></div>
{folio(f"Part {k} · {pl['name']}", nxt())}</div>''')
    for c in chs:
        m = c["n"]
        title = f'{m:02d} · {c["title"]}'
        flag = '<span class="flag" style="margin-bottom:calc(var(--u)*1)">Next · Proposed</span>' if c.get("proposed") else ""
        d.add(f"ch{m}", title, f'''<div class="l">{flag}<div class="num">{m:02d}</div><div class="kicker" style="color:var(--gold2);margin-top:calc(var(--u)*1)">Part {k} · {E(pl["name"])} · Chapter {m:02d}</div>
<h2>{E(c["title"])}</h2><div class="osub">{E(c["sub"])}</div><p class="story">{E(c["story"])}</p></div>
<div class="r"><img src="{img(f"{A}/photo-{PHOTO[m]}.jpg", 1500, 80)}" alt="" style="object-position:{POS.get(m, "50% 50%")}"><div class="credit">{E(credit(f"Chapter {m:02d}"))}</div></div>''', "opener" + (" long" if len(c["story"]) + len(c["title"]) + len(c["sub"]) > 330 else ""), menu=title)
        extra = ""
        if c.get("flow"):
            extra = '<table class="t" style="margin-top:calc(var(--u)*.6)">' + "".join(
                f'<tr><td style="width:4%"><b style="color:var(--gold)">{i}</b></td><td><b style="color:var(--navy)">{E(a)}.</b> {E(b)}</td><td style="width:9%"><span class="tag{" next" if t == "Next" else ""}">{t}</span></td></tr>' for i, (a, b, t) in enumerate(c["flow"], 1)) + "</table>"
            extra += f'<p class="small" style="margin-top:calc(var(--u)*.8)">{E(c["flownote"])}</p>'
        notes = "".join(f'<p class="small" style="margin-top:calc(var(--u)*.4);font-size:calc(var(--u)*1.05);line-height:1.35">{E(x)}</p>' for x in c.get("notes", []))
        words = sum(len(x.split()) for x in c["body"])
        body_cls = "" if c.get("flow") else ("cols2" if (c.get("notes") or words > 150) else "cols2 big")
        d.add(f"ch{m}t", title, f'''<div class="pad"><div class="kicker">Chapter {m:02d} · {E(c["title"])}</div>
<h2>{E(c["headline"])}</h2><div class="{body_cls}">{P(c["body"])}</div>{extra}
<div style="margin-top:auto">{notes}</div>
{folio(title, nxt())}</div>''')
        kind, keys, cap = c["fig"]
        if kind == "desk":
            items, tag = [(SC(keys), "desk", cap)], "Actual CalibraytAI V1 screen"
        elif kind == "deskphone":
            items, tag = [(SC(keys[0]), "desk", cap), (SC(keys[1], 800), "phone", cap)], "Actual CalibraytAI V1 screens"
        else:  # sketch
            items, tag = [(SC(keys[0], 1600), "desk", "A real customer’s sketch"), (SC(keys[1]), "desk", "Material takeoff")], "Actual sketch and CalibraytAI V1 screen"
        note = ('<p class="small" style="margin-top:calc(var(--u)*.6)"><b>Next step, proposed.</b> The calculators and takeoff work in CalibraytAI today; offering them at BMR Winchester’s counter, priced from the store’s own price list, is what we propose to build together.</p>' if c.get("proposed") else "")
        calc_btn = '<button class="go" data-go="calc1" style="align-self:flex-start;margin-top:calc(var(--u)*.8)">⏱ Work out the desk’s time savings ›</button>' if c.get("calc") else ""
        d.add(f"ch{m}s", title, f'''<div class="pad"><div class="kicker">Chapter {m:02d} · On screen</div>
{shots(items, cap, tag)}{note}{calc_btn}
<div style="margin-top:calc(var(--u)*1)">{points(c["points"], title=f'{pl["name"]} · ' + ("Next for BMR Winchester" if c.get("proposed") else "What it means for BMR Winchester"))}</div>
{folio(title, nxt())}</div>''')

rows = "".join(f'<tr><td class="g">{E(PILLARS[k]["name"])}</td><td>{E(PILLARS[k]["proof"][0])} {E(PILLARS[k]["proof"][1])}</td><td class="m">{E(", ".join([PILLARS[k]["measures"][0]] + [x[0].lower() + x[1:] for x in PILLARS[k]["measures"][1:3]]))}</td></tr>' for k in (1, 2, 3))
d.add("recap", "What you just read", f'''<div class="pad"><div class="kicker">What you just read</div>
<h2>Sell more. Spend less. Miss less.</h2>
<p style="margin-bottom:calc(var(--u)*1)">CalibraytAI gives BMR Winchester the opportunity to sell more, spend less and miss less by connecting its PRO contractors directly to its building-supply business, while preserving contractor independence.</p>
<table class="t"><tr><th>Goal</th><th>What you saw</th><th>Proof on the store’s pages</th></tr>{rows}</table>
<div style="display:flex;gap:12px;margin-top:auto"><button class="go" data-go="calc1">↺ Revisit the calculator</button><button class="go" data-go="pilot">Let’s run a pilot ›</button></div>
{folio("What you just read", nxt())}</div>''', menu="What you just read")
getc = ["CalibraytAI to run their jobs: calculators, takeoffs, estimates, supplier requests, orders and deliveries.", "BMR Winchester one step away, with the Send to BMR Winchester in CalibraytAI button.", "A sponsored start, as part of their BMR PRO account."]
bmrg = ["Sell more: more PRO customers sending their jobs to BMR Winchester first.", "Spend less: every sponsored account priced the same fast way.", "Miss less: more of the store’s Pro demand in Material demand.", "PRO engagement: sponsored accounts activated, repeat use and calculator use, as totals only."]
srules = [("Access, not control.", "BMR never sees the contractor’s account, projects, customers, margins or labour rates."),
          ("Not exclusive.", "A sponsored contractor can still choose another supplier, or price a job themselves."),
          ("Portable.", "If sponsorship ends, the contractor keeps their account and their history.")]
d.add("spons", "A BMR PRO-sponsored experience", f'''<div class="pad"><span class="flag">Proposed · For discussion</span>
<h2>A BMR PRO-sponsored CalibraytAI experience.</h2>
<p style="margin-bottom:calc(var(--u)*1)">A proposal, subject to BMR’s authorization: BMR sponsors access, CalibraytAI operates the platform, and the contractor controls the business and chooses the supplier.</p>
<div class="cards c3" style="grid-template-columns:1fr 1fr 1fr;font-size:.92em">
<div class="card"><h4>The PRO customer gets</h4><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in getc)}</ul></div>
<div class="card"><h4>BMR Winchester gets</h4><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in bmrg)}</ul></div>
<div class="card" style="background:var(--navy)"><h4 style="color:#fff">The rules</h4>{"".join(f'<p style="color:#dfe5ee"><b style="color:var(--gold2)">{E(a)}</b> {E(b)}</p>' for a, b in srules)}</div></div>
{folio("Growing together", nxt())}</div>''', menu="A BMR PRO-sponsored experience")
sponsor_concept(d, nxt, "sponsview", "Sponsorship in the app (concept)", "BMR PRO", BMRLOGO, "BMR Winchester",
                "With a BMR-authorized connection, the BMR price and the projected Elevation 360 points would show beside this choice.",
                "Adapted selectively from the seven-panel BMR PRO concept. The BMR logo is BMR’s own file from bmr.ca; “BMR PRO” is plain text because no official BMR PRO logo file was available.")
airows = [(1, "Read the sketch", "CalibraytAI reads a customer’s sketch and asks the questions a good counter person would, so a rough drawing becomes a priced list."),
          (2, "Pre-price the request", "Suggested SKU matches and prices from the store’s own quoting history, ready for the desk to check and send."),
          (3, "Forecast the demand", "Demand forecast by product and season, and items worth stocking flagged before the gaps repeat.")]
tr = "".join(f'<tr><td class="g">{E(PILLARS[k]["name"])}</td><td><b style="color:var(--navy)">{E(a)}</b><br>{E(b)} <span class="tag next">Next</span></td></tr>' for k, a, b in airows)
d.add("ai", "The intelligence ahead", f'''<div class="pad"><div class="kicker">The intelligence ahead</div>
<h2>AI and machine learning, built on your data.</h2>
<p class="lede" style="margin-bottom:calc(var(--u)*1)">Every request, quote, order and gap is recorded from the first day, in clean, structured form. That is exactly what AI and machine learning need.</p>
<table class="t"><tr><th>Goal</th><th>What comes next</th></tr>{tr}</table>
<div class="pull" style="margin-top:auto">The sooner the store starts, the more its data is worth.<small>Construction intelligence. Calibrated.</small></div>
{folio("The intelligence ahead", nxt())}</div>''', menu="The intelligence ahead")
d.add("choose", "Supplier choice and rewards", f'''<div class="pad"><span class="flag">Proposed · Illustration, not a current screen</span>
<h2>Your price and your rewards, in the contractor’s estimate.</h2>
<div class="split wide"><div class="mock"><div class="mh">Estimate · Harbour Lane Pool Deck · Choose a supplier</div>
<div class="opt on"><i></i><div><b>BMR Winchester</b><div class="kv"><span>Your BMR PRO price</span><em>$3,573.22</em></div><div class="kv"><span>Projected points, eligible purchases</span><em>up to ≈ 3,573</em></div><div class="kv"><span>Points balance</span><em>with a live connection</em></div></div></div>
<div class="opt"><i></i><div><b>Another supplier</b><div>Send the same list to any supplier you choose</div></div></div>
<div class="opt"><i></i><div><b>My own pricing</b><div>Price it yourself; nothing is shared</div></div></div><p class="small" style="margin-top:calc(var(--u)*.6);font-size:calc(var(--u)*1.1)">Projected, not confirmed: one point per eligible dollar, the earning rate BMR publishes for the BMR PRO Elevation 360 rewards program, on the eligible purchase value only. Confirmed points and balances would come only from BMR through an authorized connection. The $3,573.22 is the synthetic quote in Chapter 02. Nothing here is live today.</p></div>
<div style="font-size:calc(var(--u)*1.55)"><p>When a contractor chooses BMR Winchester in the estimate, CalibraytAI would show BMR’s authorized contractor price and the BMR PRO Elevation 360 points the order would earn, side by side. The contractor chooses the supplier and what is shared.</p>
<figure style="margin-top:calc(var(--u)*.8)"><img src="{ELEV}" alt="BMR PRO Elevation 360, from bmr.ca" style="width:100%;border-radius:4px"><figcaption class="small">BMR’s own Elevation 360 graphic, from bmr.ca/en/elevation-360-pro, shown unchanged.</figcaption></figure>
</div></div>
{folio("Supplier choice and rewards", nxt())}</div>''', menu="Supplier choice and rewards")
sees = ["Items, quantities and units", "The date needed and the delivery town", "The contractor’s company and contact", "A project reference", "On a purchase order: the delivery address, date, window and site contact"]
never = ["The customer’s name", "The contractor’s margins, labour rates or internal costs", "Other suppliers’ prices", "Estimates, or projects not sent to the store", "The site address before an order"]
d.add("trust", "Trust, both ways", f'''<div class="pad"><div class="kicker">Trust, both ways</div>
<h2>Your business stays yours.</h2>
<p style="margin-bottom:calc(var(--u)*1)">The contractor owns the job record, and the store owns its prices. Each side sees exactly what it needs to do business, and nothing more.</p>
<div class="cards c2"><div class="card"><h4>What a request shows the store</h4><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in sees)}</ul></div>
<div class="card" style="border-color:#a33a2c"><h4>What it never shows</h4><ul class="ticks no">{"".join(f"<li>{E(x)}</li>" for x in never)}</ul></div></div>
{folio("Trust, both ways", nxt())}</div>''', menu="Trust, both ways")
prules = [("Each store sees its own.", "Store staff see only what was sent to their store. An owner of several stores would see each store’s own figures (next)."),
          ("Your costs and prices stay yours.", "The contractor sees BMR’s price, never BMR’s cost from Tomlinson or any vendor. A store’s prices are never shown to another supplier."),
          ("The contractor stays in control.", "A contractor chooses which store gets each request, and can withdraw it until an order is placed."),
          ("Everything is on the record.", "Each request, quote, order, confirmation and delivery change is recorded with who and when.")]
d.add("trust2", "Trust, both ways", f'''<div class="pad"><div class="kicker">Trust, both ways</div>
<h2>Four promises.</h2>
<div class="rules">{"".join(f'<div class="rule"><i>{i}</i><div><b>{E(a)}</b><span>{E(b)}</span></div></div>' for i, (a, b) in enumerate(prules, 1))}</div>
{folio("Trust, both ways", nxt())}</div>''')
steps = [("Sign-ins for the desk", "The Pro Desk staff who quote sign in to BMR Winchester’s Supplier Hub."),
         ("Real jobs from Brayman", "Brayman sends its material and concrete orders to BMR Winchester; BMR fulfils concrete through Tomlinson as it does today, and reschedules are agreed and signed in the Hub."),
         ("Watch the numbers", "Sales, quoting time and opportunities, on the store’s own pages."),
         ("Build the next step together", "The counter takeoff, PRO sponsorship and the intelligence ahead.")]
d.add("pilot", "Let’s run a pilot", f'''<img class="bg" src="{img(f"{A}/photo-close.jpg", 1900, 80)}" alt="">
<div class="credit" style="top:12px;bottom:auto">{E(credit("Let’s run a pilot"))}</div>
<div class="ov"><div class="kicker" style="color:var(--gold2)">Next steps</div><h2>Let’s run a pilot at BMR Winchester.</h2>
<div class="cards c4" style="margin-top:calc(var(--u)*1)">{"".join(f'<div class="card" style="background:rgba(255,255,255,.95)"><h4 style="font-size:calc(var(--u)*1.7)">{E(a)}</h4><p style="font-size:calc(var(--u)*1.4)">{E(b)}</p></div>' for a, b in steps)}</div>
<p style="margin-top:calc(var(--u)*1)"><b style="color:var(--gold2)">Arrange a walkthrough:</b> Brayman Construction can walk the Pro Desk through a request, a quote, an order and a delivery change, start to finish.</p></div>''', "art dark", menu="Let’s run a pilot")
crs = "".join(f"<tr><td>{E(k)}</td><td class='m'>{E(w)} · {E(s)}</td></tr>" for k, w, s in CREDITS)
d.add("notes", "Notes and credits", f'''<div class="pad"><div class="kicker">About this book</div><h2 style="margin-bottom:calc(var(--u)*.5)">Notes and credits</h2>
<div class="split even" style="font-size:calc(var(--u)*1.25);line-height:1.42"><div>
<p><b>The story.</b> The Harbour Lane, Rideau Street and Merrickville jobs are fictional. Every application image is an actual CalibraytAI V1 screen, captured on 20 October 2026 with synthetic data only; the store appears as “BMR Winchester (synthetic)”. Concrete is ordered from BMR Winchester; Tomlinson is not connected to CalibraytAI. The Chapter 04 sketch is a real customer’s, shown without their name.</p>
<p><b>Signing and the calculator.</b> Signing on supplier orders, confirmations and delivery changes is built and tested and goes live with its next release. The online Supplier Economics Calculator is being prepared for stores.</p>
<p><b>What is live.</b> Everything in Parts 1 to 3 works in CalibraytAI V1 today, except Chapter 04 and anything marked Future integration. Future integration, only with BMR’s authorization: live BMR pricing, Elevation 360 balances, stock and BMR systems.</p>
<p><b>Branding.</b> CalibraytAI artwork and the approved logo. The BMR logo and the Elevation 360 graphic are BMR’s own files from bmr.ca, shown unchanged; no BMR PRO or Elevation 360 logo file was available, so those names appear in plain text. All are BMR Group’s marks, shown for illustration and discussion only, subject to BMR’s authorization.</p>
<p><b>Sources.</b> Buildxact and The Farnsworth Group, 2022. BMR PRO Elevation 360: bmr.ca/en/elevation-360-pro.</p></div>
<table class="t" style="font-size:calc(var(--u)*1.25)">{crs}</table></div>
{folio("CalibraytAI · Supplier Connection", nxt())}</div>''', menu="Notes and credits")
d.add("end", "Back cover", f'''<div class="l" style="justify-content:center"><img src="{img(f"{A}/approved-logo-v1-dark-reference.png", 900, 90)}" alt="CalibraytAI" style="width:70%;margin-bottom:calc(var(--u)*2)">
<h2 style="color:#fff">Your price in <span style="color:var(--gold2)">more estimates.</span></h2>
<div style="display:flex;align-items:center;gap:calc(var(--u)*1);margin:calc(var(--u)*.6) 0 calc(var(--u)*1)"><span style="background:#fff;border-radius:4px;padding:calc(var(--u)*.4) calc(var(--u)*.7);line-height:0"><img src="{BMRLOGO}" alt="BMR" style="height:calc(var(--u)*2.4)"></span><span class="small" style="color:#c3ccd8">Prepared for BMR Winchester · a proposal for discussion</span></div>
<p style="color:#c3ccd8">From the contractor’s takeoff to the store’s confirmed delivery, CalibraytAI connects every job to the store that prices it.</p>
<div class="lifeline">REQUEST → QUOTE → ORDER → CONFIRM → DELIVER</div>
<button class="start" data-go="contents">‹ Back to contents</button></div>
<div class="r"><img src="{img(f"{A}/art-build-hub.jpg", 1500, 80)}" alt="A builder reviewing the Supplier Hub on a tablet" style="object-fit:cover;object-position:50% 55%"></div>''', "cover")

out = f"{S}/deck/out/bmr.html"
open(out, "w").write(d.html())
print(out, len(d.pages), "pages", round(os.path.getsize(out) / 1e6, 2), "MB")

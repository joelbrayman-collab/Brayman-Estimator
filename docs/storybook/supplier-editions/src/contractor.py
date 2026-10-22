"""The Contractor Storybook, screen edition. Content from build/chapters.py, build/build.py and build/calendar_spread.py."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import Deck, E, P, S, img, folio, points, shots, shot  # noqa: E402

B = f"{S}/build"
A = f"{B}/assets"
sys.path.insert(0, B)
from chapters import CH  # noqa: E402

CREDITS = [
    ("The working day", "Artem Podrez", 5025644), ("Chapter 01", "Joel Brayman", "own"),
    ("Chapter 02", "Joel Brayman", "own"), ("Chapter 03", "Mikael Blomkvist", 8961295),
    ("Chapter 04", "Daniel McCullough", "unsplash"), ("Chapter 05", "Serhat Tuğ", 37499256),
    ("Chapter 06", "Mark Stebnicki", 12278586),
    ("Chapter 08", "Lezgin Epik", 5476052), ("Chapter 09", "Jennifer Kalenberg", "unsplash"), ("Chapter 11", "Khush Sandhu", 15477575),
    ("Chapter 12", "Ronnakorn Triraganon", "unsplash"), ("Chapter 13", "Curtis Adams", 7027853),
    ("Chapter 14", "Troy Allen", "unsplash"),
]


def credit(key):
    for k, who, pid in CREDITS:
        if k == key:
            return f"Photo: {who}" if pid == "own" else f"Photo: {who} / {'Unsplash' if pid == 'unsplash' else 'Pexels'}"
    return ""


POS = {1: "0% 50%", 11: "100% 50%"}
STAGE = {1: "Plan", 2: "Plan", 3: "Plan", 4: "Plan", 5: "Plan", 6: "Price", 7: "Price", 8: "Price", 9: "Price", 10: "Contract", 11: "Build", 12: "Build", 13: "Build", 14: "Monitor · Learn"}

d = Deck("CalibraytAI — The Contractor Storybook", "A Day in the Life of a Busy Contractor", "CalibraytAI Contractor Storybook")
n = [0]


def nxt():
    n[0] += 1
    return n[0]


def S_(k):
    return img(f"{A}/screen-{k}.png", 2000, 82)


d.add("cover", "Cover", f'''<div class="l"><img src="{img(f"{A}/approved-logo-v1-dark-reference.png", 800, 90)}" alt="CalibraytAI" style="width:52%;margin-bottom:calc(var(--u)*1.6)">
<div class="kicker" style="color:var(--gold2)">The Contractor Storybook</div>
<h1>A Day in the Life of a <span>Busy Contractor</span></h1>
<div class="sub">How CalibraytAI takes a contractor from the first call to a finished project.</div>
<div class="ser">Plan · Price · Contract · Build · Monitor · Learn</div>
<button class="start" data-go="intro">Start reading ›</button></div>
<div class="r"><img src="{img(f"{A}/art-cover-hero.jpg", 1400, 82)}" alt="A contractor on site with CalibraytAI" style="object-fit:cover"></div>''', "cover", menu="Cover")
d.add("compass", "Plan • Price • Build", f'''<img class="bg" src="{img(f"{A}/web-compass.jpg", 1600, 82)}" alt="">
<div class="ov"><div class="kicker" style="color:var(--gold2)">Plan • Price • Build</div>
<h2>Construction intelligence. <span>Calibrated.</span></h2>
<p>One authoritative project record connects every phase, and every completed project makes the next one smarter.</p>
<div class="lifeline">PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN</div></div>''', "art dark")
d.add("intro", "The working day", f'''<div class="pad"><div class="kicker">The working day</div>
<h2>It starts with a phone call.</h2>
<div class="split"><div><p class="lede">A customer has an idea. A supplier needs a list. The crew needs a plan. And the contractor needs enough hours in the day to keep everything moving.</p>
<p style="margin-top:calc(var(--u)*1.2)">This is the story of how one connected project helps bring those pieces together. Follow the fictional Harbour Lane Pool Deck through the same kinds of decisions contractors make every day. The application images are actual CalibraytAI V1 screens; the photographs show real construction work.</p></div>
<figure><img class="photo" src="{img(f"{A}/photo-intro.jpg", 1400, 80)}" alt="A contractor on the phone" style="height:calc(var(--u)*28)"><figcaption class="small" style="margin-top:6px">{E(credit("The working day"))}</figcaption></figure></div>
{folio("CalibraytAI · Plan • Price • Build", nxt())}</div>''', menu="The working day")

grp = {}
for c in CH:
    grp.setdefault(STAGE[c["n"]], []).append(c)
cols = [["Plan", "Price"], ["Contract", "Build", "Monitor · Learn"]]
tocc = ""
for col in cols:
    tocc += "<div>" + "".join(f'<div class="tocgrp"><div class="stg">{E(st)}</div>' + "".join(f'<button data-go="ch{c["n"]}"><i>{c["n"]:02d}</i><b>{E(c["title"])}</b><span>›</span></button>' for c in grp[st]) + "</div>" for st in col)
    if col is cols[1]:
        tocc += '<div class="tocgrp"><div class="stg">Beyond one job</div>' + "".join(f'<button data-go="{pid}"><i>·</i><b>{E(t)}</b><span>›</span></button>' for t, pid in (
            ("Running the company", "company"), ("The road ahead", "road"), ("Notes and credits", "notes"))) + "</div>"
    tocc += "</div>"
d.add("contents", "Contents", f'''<div class="pad"><div class="kicker">Contents · Click any line to go there</div>
<h2 style="margin-bottom:0">Fourteen chapters, one lifecycle</h2>
<div class="toc">{tocc}</div>{folio("Contents", nxt())}</div>''', menu="Contents")

d.add("begin", "Before we begin", f'''<div class="pad"><div class="kicker">Before we begin</div>
<h2>One system for the whole company.</h2>
<p class="lede" style="margin-bottom:calc(var(--u)*1.2)">Most contractors run their business on a patchwork, and they hold it together through sheer effort.</p>
<div class="cols2">{P(["A spreadsheet for estimates. A notebook in the truck. Texts with the crew, emails with the supplier, a folder of contracts and a great deal kept in memory. Every handoff is a chance to retype a number wrong, lose a detail or forget what was agreed.",
 "CalibraytAI replaces the patchwork with one connected record. Each job is a single project that carries everything about it, from the first call to the final walkthrough. The office works at a computer, the crew works on a phone, and both are looking at the same job.",
 "It is built around your way of working: your costs, your crews, your pricing, your templates and your brand. It was built by a contractor, for contractors, and proven on real residential jobs."])}</div>
{folio("Before we begin", nxt())}</div>''', menu="Before we begin")
vs = [("Estimates in a spreadsheet", "One estimate with four outputs"), ("Material lists on a scratch pad", "A takeoff from the confirmed job"),
      ("Supplier prices retyped from emails", "The supplier’s completed request, uploaded"), ("Contracts printed, signed and scanned", "Signed on the customer’s phone"),
      ("The crew schedule on a whiteboard", "The Company Calendar and each crew’s phone"), ("Job history in someone’s head", "Every job kept with its full record")]
d.add("patch", "The patchwork", f'''<div class="pad"><div class="kicker">Before we begin</div>
<h2>From the patchwork to one record.</h2>
<table class="t"><tr><th>The patchwork</th><th>With CalibraytAI</th></tr>{"".join(f'<tr><td class="m">{E(a)}</td><td><b style="color:var(--navy)">{E(b)}</b></td></tr>' for a, b in vs)}</table>
<div class="pull" style="margin-top:auto">Enter it once. Use it everywhere. Keep it for the next job.<small>The idea behind CalibraytAI</small></div>
{folio("Before we begin", nxt())}</div>''')
stg = [("Plan", "Ch 01–05", "Captures the customer and the job, turns confirmed dimensions into drawings and does the calculations."),
       ("Price", "Ch 06–09", "Builds the material list, brings in supplier prices, applies your costs and pricing, and produces the estimate."),
       ("Contract", "Ch 10", "Generates the contract from the accepted estimate, and the customer signs it on a phone."),
       ("Build", "Ch 11–13", "Schedules the crews, records time, costs and changes, and tracks the punch list to a clean closeout."),
       ("Monitor", "Ch 12, 14", "Shows estimated against actual on every job while there is still time to act."),
       ("Learn", "Ch 14", "Keeps every finished job as evidence, so the next estimate starts from what really happened.")]
d.add("stages", "Six stages", f'''<div class="pad"><div class="kicker">How it works</div>
<h2>Six stages, one project record.</h2>
<div class="cards c3">{"".join(f'<div class="card"><h4>{k}. {E(a)} <span class="small" style="font-family:Plex,sans-serif;font-weight:600;color:var(--gold)">{E(ch)}</span></h4><p>{E(t)}</p></div>' for k, (a, ch, t) in enumerate(stg, 1))}</div>
{folio("How it works", nxt())}</div>''', menu="Six stages, one record")
pr = [("Nothing is guessed.", "Anything not yet known stays marked as missing until someone confirms it."),
      ("You approve every number.", "Costs, prices and pricing are applied only after you approve them, and each approval records who made it."),
      ("Nothing is invented.", "CalibraytAI never makes up a price, a quantity or a contract term on its own."),
      ("Nothing is lost.", "Issued estimates, signed contracts and past decisions are kept, not quietly overwritten.")]
d.add("promise", "What you can count on", f'''<div class="pad"><div class="kicker">How it works</div>
<h2>What you can count on.</h2>
<div class="rules">{"".join(f'<div class="rule"><i>{i}</i><div><b>{E(a)}</b><span>{E(b)}</span></div></div>' for i, (a, b) in enumerate(pr, 1))}</div>
{folio("How it works", nxt())}</div>''')


def figitems(fig):
    kind, keys, cap = fig
    if kind == "desk":
        return [(S_(keys), "desk", cap)], "Actual CalibraytAI V1 screen"
    if kind == "phones":
        return [(img(f"{A}/screen-{k}.png", 800, 85), "phone", cap) for k in keys], "Actual CalibraytAI V1 screens"
    if kind == "deskdoc":
        return [(S_(keys[0]), "desk", cap), (img(f"{A}/screen-{keys[1]}.png", 2000, 82), "desk", "The customer estimate document")], "Actual CalibraytAI V1 screen and document"
    return [(S_(keys[0]), "desk", cap), (img(f"{A}/screen-{keys[1]}.png", 800, 85), "phone", cap)], "Actual CalibraytAI V1 screens"


for c in CH:
    k = c["n"]
    title = f'{k:02d} · {c["title"]}'
    if k == 10:
        src, cr, extra = f"{A}/art-contract.jpg", "Artwork: CalibraytAI", ""
    elif k == 7:
        src, cr, extra = f"{A}/web-supplier.jpg", "Artwork: CalibraytAI", "object-fit:contain;background:#000;"
    else:
        src, cr, extra = f"{A}/photo-ch{k:02d}.jpg", credit(f"Chapter {k:02d}"), ""
    d.add(f"ch{k}", title, f'''<div class="l"><div class="num">{k:02d}</div><div class="kicker" style="color:var(--gold2);margin-top:calc(var(--u)*1)">{STAGE[k]} · Chapter {k:02d}</div>
<h2>{E(c["title"])}</h2><div class="osub">{E(c["sub"])}</div><p class="story">{E(c["story"])}</p></div>
<div class="r"><img src="{img(src, 1500, 80)}" alt="" style="{extra}object-position:{POS.get(k, "50% 50%")}"><div class="credit">{E(cr)}</div></div>''', "opener", menu=title)
    d.add(f"ch{k}t", title, f'''<div class="pad"><div class="kicker">Chapter {k:02d} · {E(c["title"])}</div>
<h2>{E(c["headline"])}</h2><div class="cols2 big">{P(c["body"])}</div>
{folio(title, nxt())}</div>''')
    items, tag = figitems(c["fig"])
    pts = [("Save time", c["time"]), ("Protect your money", c["money"]), ("Make life easier", c["easier"])]
    d.add(f"ch{k}s", title, f'''<div class="pad"><div class="kicker">Chapter {k:02d} · On screen</div>
{shots(items, c["fig"][2], tag)}
<div style="margin-top:calc(var(--u)*1.2)">{points(pts, title="What’s in it for you")}</div>
{folio(title, nxt())}</div>''')
    if k == 4:
        d.add("real1", "04 · A real pool-deck sketch", f'''<div class="pad"><div class="kicker">Chapter 04 · A real job</div>
<h2>A real pool-deck sketch.</h2>
<p style="margin-bottom:calc(var(--u)*1)">Harbour Lane is fictional. This sketch is real: a customer’s own sketch for a pool deck, with a 21-foot pool, an 18-foot upper deck, stairs down to a lower deck and a gate. From it, the contractor confirmed the dimensions and developed a preliminary drawing set.</p>
<div class="zrow"><figure><div class="im"><img class="z" src="{img(f"{A}/bushel-sketch.png", 1600, 82)}" alt="The customer’s original sketch"></div><figcaption><b>The original sketch.</b> Photographed on graph paper and shown as received. Nothing redrawn or added.</figcaption></figure>
<figure><div class="im"><img class="z" src="{img(f"{A}/j1-sheet-2.png", 2200, 82)}" alt="Drawing issue J1, sheet 2"></div><figcaption><b>Drawing issue J1 · Sheet 2 of 8.</b> Dimensioned pier and foundation plan developed from the sketch.</figcaption></figure></div>
{folio("04 · From a sketch to a drawing", nxt())}</div>''')
        d.add("real2", "04 · The drawing set", f'''<div class="pad"><div class="kicker">Chapter 04 · A real job</div>
<h2>From the sketch, a preliminary drawing set.</h2>
<div class="zrow"><figure><div class="im"><img class="z" src="{img(f"{A}/j1-sheet-5.png", 2200, 82)}" alt="Sheet 5"></div><figcaption><b>Sheet 5 of 8.</b> Front and side elevations showing the framing. Preliminary issue J1, 1 October 2026, subject to permit review and field verification.</figcaption></figure>
<figure><div class="im"><img class="z" src="{img(f"{A}/j1-sheet-7.png", 2200, 82)}" alt="Sheet 7"></div><figcaption><b>Sheet 7 of 8.</b> Typical helical pier, bracket, post, beam and joist detail, with the connector count.</figcaption></figure></div>
<p class="small" style="margin-top:calc(var(--u)*.6)">Click a drawing to enlarge it.</p>
{folio("04 · From a sketch to a drawing", nxt())}</div>''')
    if k == 11:
        L = "11 · The calendar"
        d.add("cal1", L, f'''<div class="pad"><div class="kicker">Chapter 11 · Organize the crew · The calendar</div>
<h2>One calendar for the company. One for you.</h2>
<p class="lede" style="margin-bottom:calc(var(--u)*1.6)">Tuesday at Harbour Lane: framing with the deck crew and a nine o’clock check with Morgan. Everything the company has on, and each person’s own day, in one place.</p>
<div class="cards c2"><div class="card"><h4>Company Calendar</h4><p>Every job’s scheduled work, crews and deliveries, and every company appointment. Filter it to one project when you need to.</p></div>
<div class="card"><h4>My Calendar</h4><p>Where the calendar opens: your appointments, the ones you attend, and the work assigned to you or your crew.</p></div></div>
<div class="pull" style="margin-top:auto">🔒 Personal stays personal. A personal appointment is seen only by the person it belongs to: not colleagues, not administrators, not suppliers. Company appointments are seen by everyone in the company.<small>Privacy</small></div>
{folio(L, nxt())}</div>''', menu="11 · The calendar")
        d.add("cal2", L, f'''<div class="pad"><div class="kicker">Chapter 11 · The calendar · On screen</div>
<div class="zrow"><figure><div class="im"><img class="z" src="{S_("cal-company-week")}" alt="Company Calendar, week view"></div><figcaption><b>Company Calendar, week view:</b> the Harbour Lane and Nair Basement work for every crew, with company appointments below.</figcaption></figure>
<figure><div class="im"><img class="z" src="{S_("cal-my-week")}" alt="My Calendar, week view"></div><figcaption><b>My Calendar, the same week for Ben:</b> his crew’s work, his appointments, and his personal Dentist appointment with its lock.</figcaption></figure></div>
<div class="capline"><span class="hint">Click a screen to enlarge</span><span class="tag">Actual CalibraytAI V1 screens</span></div>
{folio(L, nxt())}</div>''')
        cpts = [("With or without a project", "Site visits, client meetings, supplier meetings, estimate consultations and general business appointments. Link a client and project when there is one."),
                ("Who attends", "Each appointment is for one person, and others from the company can be added as attending. It shows on each of their My Calendars."),
                ("Day, Week and Month", "Day and Week run by the hour, opening at 7 AM, for the 5 AM starts and the late pours. Month scrolls from three months back to a year ahead."),
                ("Outlook, Google and Apple Calendar", "Add one appointment to your own calendar, or subscribe to your private CalibraytAI calendar address so appointments appear and update by themselves.")]
        d.add("cal3", L, f'''<div class="pad"><div class="kicker">Chapter 11 · The calendar</div>
<h2 style="margin-bottom:calc(var(--u)*1)">Appointments, any view, any calendar app.</h2>
<div class="split" style="grid-template-columns:1fr 1.25fr"><div class="zrow" style="height:100%"><figure><div class="im"><img class="z" src="{S_("cal-appt")}" alt="An appointment"></div><figcaption>An appointment: who can see it, type, date and time, location, who it is for, an optional client and project, and who else attends.</figcaption></figure></div>
<div class="cards" style="gap:calc(var(--u)*1)">{"".join(f'<div class="rule" style="grid-template-columns:1fr"><div><b>{E(a)}</b><span>{E(b)}</span></div></div>' for a, b in cpts)}</div></div>
{folio(L, nxt())}</div>''')
        d.add("cal4", L, f'''<div class="pad"><div class="kicker">Chapter 11 · The calendar · On the phone and in Field</div>
<div class="shot">
<div class="phone"><img src="{img(f"{A}/screen-cal-phone-day.png", 800, 85)}" alt="My Calendar, Day, on a phone"></div>
<div class="phone"><img src="{img(f"{A}/screen-cal-field.png", 800, 85)}" alt="Field Today for Alex on the deck crew"></div>
<div style="flex:1;align-self:center"><p><b style="color:var(--navy)">Connected to the job.</b> Work scheduled from the estimate’s hours, crew assignments and deliveries show on both calendars, and each crew sees its own Today and Week in Field. Appointments never move project dates.</p>
<div class="shot" style="height:calc(var(--u)*14);flex:none;justify-content:flex-start"><div class="desk"><img src="{S_("cal-feed")}" alt="Calendar connection"></div></div>
<p class="small">Calendar connection: a private, read-only address you can replace or turn off at any time. Outside calendars show CalibraytAI appointments; changes are made in CalibraytAI and the outside calendar follows. It is not two-way. Saving an appointment sends no messages, so tell the crew as you do today.</p></div></div>
<div class="capline"><span class="cap">My Calendar, Day, on a phone · Field Today for Alex on the deck crew <span class="hint">· Click a screen to enlarge</span></span><span class="tag">Actual CalibraytAI V1 screens</span></div>
{folio(L, nxt())}</div>''')

tl = [("Home", "Home and Company Attention", "Today’s work, what needs a decision, and where the business needs attention across every job."),
      ("Calendar", "My Calendar and Company Calendar", "Your own day, and every crew, job and appointment, with each crew’s own Today and Week."),
      ("Clients", "Clients", "Every customer with their full history of projects, estimates and signed documents."),
      ("Costs", "What we pay", "Supplier costs and labour, approved and dated, ready to use on the next estimate."),
      ("Costs", "Reusable work", "A group of items you price together again and again, built once and reused."),
      ("Pricing", "How we price", "Your labour rate and pricing policy, applied the same way on every job."),
      ("Documents", "Templates and your brand", "Estimates, proposals and contracts that look like your company."),
      ("History", "Past jobs", "Upload previous estimates so your own history starts working from day one."),
      ("Books", "QuickBooks-ready entries", "Each estimate produces an entry ready for your bookkeeping, nothing retyped."),
      ("Tools", "Ten calculators", "Concrete, footings, stairs, ICF walls, framing, roofing, siding, drywall, flooring, and a job-versus-business tool.")]
d.add("company", "Running the company", f'''<div class="pad"><div class="kicker">Beyond one job</div>
<h2 style="margin-bottom:calc(var(--u)*.8)">Running the company, not just the job.</h2>
<div class="rules" style="gap:calc(var(--u)*.5) calc(var(--u)*3)">{"".join(f'<div class="rule" style="grid-template-columns:calc(var(--u)*7.5) 1fr;padding-top:calc(var(--u)*.55)"><i style="font-family:Plex,sans-serif;font-size:calc(var(--u)*1.05);letter-spacing:.12em;text-transform:uppercase;font-weight:700;padding-top:calc(var(--u)*.4)">{E(a)}</i><div><b style="font-size:calc(var(--u)*1.6)">{E(b)}</b><span style="font-size:calc(var(--u)*1.4)">{E(x)}</span></div></div>' for a, b, x in tl)}</div>
{folio("Beyond one job", nxt())}</div>''', menu="Running the company")
rd = [("tag", "Today", "A complete record of every job", "Every estimate, supplier price, change order, hour and actual cost is kept against the project it belongs to."),
      ("tag next", "Learn", "Estimates calibrated by your own jobs", "Comparing what was estimated with what really happened, to sharpen labour standards and costs. Suggestions are always shown to you for approval."),
      ("tag built", "In development", "More drawing sets", "The drawing engine that produces deck sets is being extended to more of the work the calculators cover."),
      ("tag future", "Planned", "From plans to quantities", "Reading PDF plans and producing quantities for takeoff, with a person reviewing every number before it is priced."),
      ("tag future", "Planned", "Connected building suppliers", "Requests and prices moving automatically at both ends, while staying supplier-neutral."),
      ("tag future", "Planned", "Anywhere in Canada", "A provincial library of contract packages and code profiles, for contractors in every province.")]
d.add("road", "The road ahead", f'''<div class="pad"><div class="kicker">The road ahead</div>
<h2 style="margin-bottom:calc(var(--u)*.6)">Every job makes the next one smarter.</h2>
<table class="t">{"".join(f'<tr><td style="width:17%"><span class="{k}">{E(a)}</span></td><td><b style="color:var(--navy)">{E(b)}.</b> {E(x)}</td></tr>' for k, a, b, x in rd)}</table>
{folio("The road ahead", nxt())}</div>''', menu="The road ahead")
d.add("lifecycle", "The complete lifecycle", f'''<img class="bg" src="{img(f"{A}/web-lifecycle.jpg", 1600, 82)}" alt="The complete construction lifecycle, connected: Plan, Price, Contract, Build, Monitor and Learn" style="object-fit:contain;background:#000">''', "art dark", menu="The complete lifecycle")
d.add("turn", "Now it is your turn", f'''<img class="bg" src="{img(f"{A}/art-build.jpg", 1900, 80)}" alt="" style="object-position:50% 40%">
<div class="ov"><div class="kicker" style="color:var(--gold2)">The next chapter</div><h2>Now it is your turn.</h2>
<p>Open CalibraytAI. Explore the tools. Follow a project. See how the information moves from one step of the job to the next.</p>
<div class="lifeline">PLAN • PRICE • BUILD</div></div>''', "art dark")
crs = "".join(f"<tr><td>{E(k)}</td><td class='m'>{E(w)} · {'Unsplash' if pid == 'unsplash' else 'own photograph' if pid == 'own' else 'Pexels'}</td></tr>" for k, w, pid in CREDITS)
d.add("notes", "Notes and credits", f'''<div class="pad"><div class="kicker">About this book</div><h2>Notes and credits</h2>
<div class="split even" style="font-size:calc(var(--u)*1.42);line-height:1.45"><div>
<p><b>The story.</b> Harbour Lane Pool Deck and Morgan Ellis are fictional. Every application image is an actual CalibraytAI V1 screen, captured in October 2026 with synthetic data only.</p>
<p><b>The real job.</b> The pool-deck sketch and drawing issue J1 in Chapter 04 come from a real job. The customer’s name and address are not shown.</p>
<p><b>Artwork and branding.</b> The cover, the Chapter 07 and 10 openers, the lifecycle pages and the closing page use CalibraytAI artwork. The logo is the approved original file.</p>
<p><b>Photography.</b> The Chapter 01 and 02 photographs are the author’s own. Phones showing actual CalibraytAI screens were added to the Chapter 01, 02 and 11 photographs. Other photographs are from Pexels and Unsplash, used under their free licences.</p></div>
<table class="t" style="font-size:calc(var(--u)*1.3)">{crs}</table></div>
{folio("CalibraytAI · Plan • Price • Build", nxt())}</div>''', menu="Notes and credits")
d.add("end", "Back cover", f'''<div class="l" style="justify-content:center"><img src="{img(f"{A}/approved-logo-v1-dark-reference.png", 900, 90)}" alt="CalibraytAI" style="width:70%;margin-bottom:calc(var(--u)*2)">
<h2 style="color:#fff">Construction intelligence. <span style="color:var(--gold2)">Calibrated.</span></h2>
<p style="color:#c3ccd8">From the first customer call to the final walkthrough, a clearer, easier way to plan, price and build.</p>
<div class="lifeline">PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN</div>
<button class="start" data-go="contents">‹ Back to contents</button></div>
<div class="r"><img src="{img(f"{A}/web-connection.jpg", 1500, 82)}" alt="" style="object-fit:contain;background:#000"></div>''', "cover")

out = f"{S}/deck/out/contractor.html"
open(out, "w").write(d.html())
print(out, len(d.pages), "pages", round(os.path.getsize(out) / 1e6, 2), "MB")

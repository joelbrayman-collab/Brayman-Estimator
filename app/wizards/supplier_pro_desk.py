"""Wizard 4 — Supplier Pro Desk (brief §5): a contractor's request, or a walk-in quotation, to a closed order.

Two kinds of transaction, one wizard:

* A contractor request (Supplier Hub): what the contractor chose to share with this supplier — never anything
  else of the contractor's — then the supplier's returned quote, the contractor's order, the supplier's
  confirmation, delivery and closing. The contractor alone places the order.
* A PRO Desk quotation (the supplier's own customer, Quick Quote or the full quotation): the building, its
  takeoff, the supplier's own products and prices, issue, the customer's answer, revisions and the order-ready
  package for the supplier's own sales system.

Every record is read through the supplier-scoped Supplier Hub and PRO Desk services (another supplier's request
or quotation is Not found). Prices are the supplier's own price file; availability is shown only where the
supplier's price file carries it. No point-of-sale, inventory or rewards system is assumed: CalibraytAI has no
configured rewards or Pro Account points program, so the wizard has no points step.
"""

from __future__ import annotations

from flask import url_for

from app.models.wizard import WIZARD_SUPPLIER_PRO_DESK
from app.wizards.framework import (
    DONE,
    INFO,
    NOT_NEEDED,
    TODO,
    WAITING,
    Action,
    Item,
    Step,
    StepView,
    Wizard,
    count_headline,
)


def _sid(ctx):
    return ctx.supplier.id


def is_request(ctx):
    return ctx.share is not None


def current_quote(ctx):
    """The live quotation: a revised quotation is followed to its newest revision (the earlier one is kept)."""
    quote = ctx.quote
    if quote is None:
        return None
    from app.models.supplier_quote import SupplierQuote, SupplierQuoteEvent

    for _ in range(25):
        if quote.status != "CANCELLED":
            return quote
        event = (SupplierQuoteEvent.query.filter_by(quote_id=quote.id, event_type="REVISED")
                 .order_by(SupplierQuoteEvent.id.desc()).first())
        number = (event.detail_json or {}).get("new_number") if event else None
        newer = SupplierQuote.query.filter_by(supplier_id=quote.supplier_id, number=number).first() if number else None
        if newer is None:
            return quote
        quote = newer
    return quote


def _need_record(ctx):
    if ctx.share is None and ctx.quote is None:
        return StepView(TODO, "Open a contractor request or start a quotation first (step 1).",
                        missing=["Open a contractor request or start a quotation first (step 1)."])
    return None


def _request_page(ctx):
    return url_for("supplier_portal.request_detail", supplier_id=_sid(ctx), share_id=ctx.share.id)


def _quote_page(ctx, anchor=""):
    q = current_quote(ctx)
    return url_for("supplier_pro_desk.quote", supplier_id=_sid(ctx), quote_id=q.id) + anchor


def _order(ctx):
    from app.services.supplier_hub import purchase_order_for

    return purchase_order_for(ctx.share) if ctx.share is not None else None


def _priced(ctx):
    from app.services.supplier_pro_desk import price_quote

    return price_quote(current_quote(ctx))


# ------------------------------------------------------------------------------------------------ 1 open
def _open(ctx):
    if ctx.share is not None:
        return StepView(DONE, f"Contractor request {ctx.share.number}",
                        actions=[Action("Open the request", _request_page(ctx), key="open-request")])
    if ctx.quote is not None:
        q = current_quote(ctx)
        return StepView(DONE, f"Quotation {q.number} for {q.customer.display_name}",
                        actions=[Action("Open the quotation", _quote_page(ctx), key="open-quote")])
    from app.services.supplier_hub import supplier_shares
    from app.services.supplier_pro_desk import supplier_quotes
    from app.wizards.service import active_supplier_runs

    taken_shares = {r.supplier_share_id for r in active_supplier_runs(_sid(ctx)) if r.id != ctx.run.id}
    taken_quotes = {r.supplier_quote_id for r in active_supplier_runs(_sid(ctx)) if r.id != ctx.run.id}
    shares = [s for s in supplier_shares(_sid(ctx)) if s.status in ("SENT", "OPENED", "RETURNED")
              and s.id not in taken_shares]
    quotes = [q for q in supplier_quotes(_sid(ctx)) if q.status in ("DRAFT", "ISSUED", "ACCEPTED")
              and q.id not in taken_quotes]
    sid = _sid(ctx)
    return StepView(TODO, "Which request or quotation are you working on?",
                    missing=["Choose a contractor request or a quotation (or start one)."],
                    form="supplier_choose.html", form_ctx={"shares": shares, "quotes": quotes[:30]},
                    actions=[Action("Quick Quote (a standard building)", url_for("supplier_pro_desk.quick", supplier_id=sid),
                                    primary=True, key="quick-quote",
                                    note="Come back here and choose the quotation it made."),
                             Action("New quotation", url_for("supplier_pro_desk.new_quote", supplier_id=sid),
                                    key="new-quote"),
                             Action("Contractor requests", url_for("supplier_portal.inbox", supplier_id=sid),
                                    key="inbox")])


def _choose(ctx, form):
    from app.services.supplier_hub import SupplierHubError, supplier_share
    from app.services.supplier_pro_desk import ProDeskError, supplier_quote
    from app.wizards.service import WizardError, attach

    choice = form.get("record") or ""
    kind, _, raw = choice.partition(":")
    if not raw.isdigit():
        raise WizardError("Choose a request or a quotation.")
    try:
        if kind == "share":
            share = supplier_share(_sid(ctx), int(raw))  # this supplier's own requests only
            attach(ctx.run, actor=ctx.actor, user_id=ctx.user_id, share_id=share.id)
            return f"Working on contractor request {share.number}."
        if kind == "quote":
            quote = supplier_quote(_sid(ctx), int(raw))  # this supplier's own quotations only
            attach(ctx.run, actor=ctx.actor, user_id=ctx.user_id, quote_id=quote.id)
            return f"Working on quotation {quote.number}."
    except (SupplierHubError, ProDeskError):
        raise WizardError("Not found.") from None
    raise WizardError("Choose a request or a quotation.")


# ------------------------------------------------------------------------------------------------ 2 who
def _who(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        shared = ctx.share.shared_json or {}
        return StepView(DONE, f"{shared.get('company', 'Contractor')} · {shared.get('project_reference', '')}",
                        items=[Item("Contractor", DONE, shared.get("company", "")),
                               Item("Contact", DONE, f"{shared.get('contact_name', '')} {shared.get('contact_email', '')}".strip()),
                               Item("Project", DONE, shared.get("project_reference", "")),
                               Item("Delivery town", DONE, shared.get("delivery_town", "")),
                               Item("Needed by", INFO, shared.get("needed_by") or "not given"),
                               Item("Materials requested", DONE, f"{len(shared.get('lines', []))} lines")],
                        note="Only what the contractor chose to share with you. Their costs, margins and other "
                             "suppliers' prices are never shown.")
    q = current_quote(ctx)
    customer = q.customer
    return StepView(DONE, f"{customer.display_name}" + (f" · {customer.town}" if customer.town else ""),
                    items=[Item("Customer", DONE, customer.display_name),
                           Item("Contact", INFO, " ".join(x for x in (customer.phone, customer.email) if x) or "—"),
                           Item("Email consent", INFO, "yes" if customer.consent_email else "no"),
                           Item("Building", INFO, (q.building_system or "not chosen yet").replace("_", " ").lower())],
                    actions=[Action("Open the quotation", _quote_page(ctx), key="open-quote")])


# ------------------------------------------------------------------------------------------------ 3 drawings & takeoffs
def _documents(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        lines = (ctx.share.shared_json or {}).get("lines", [])
        opened = ctx.share.opened_at is not None or ctx.share.status == "RETURNED"
        return StepView(DONE if opened else TODO,
                        f"{len(lines)} shared takeoff lines" + (" — opened" if opened else " — not opened yet"),
                        items=[Item(f"{l.get('number')}: {l.get('description') or l.get('item') or ''}", INFO,
                                    f"{l.get('quantity', '')} {l.get('unit', '')}".strip()) for l in lines[:40]],
                        actions=[Action("Open the request", _request_page(ctx), primary=True, key="open-request")],
                        missing=[] if opened else ["Open the request to read what was shared."],
                        note="The contractor decides what is shared: the takeoff lines and the request document.")
    from app.services.outbuilding import spec as S
    from app.services.supplier_pro_desk import active_sketches, spec_values

    q = current_quote(ctx)
    values = spec_values(q)
    sketches = active_sketches(q)
    drawable = S.drawable(values)
    items = [Item(f"Sketch: {f.filename}", INFO) for f in sketches]
    items.append(Item("Drawing", DONE if drawable else TODO, "ready" if drawable else "describe the building first"))
    actions = [Action("Building and sketch", _quote_page(ctx, "#building"), primary=True, key="building")]
    if drawable:
        actions.append(Action("Drawing (PDF)", url_for("supplier_pro_desk.drawing", supplier_id=_sid(ctx), quote_id=q.id,
                                                        fmt="pdf"), key="drawing"))
    return StepView(DONE if drawable else TODO, f"{len(sketches)} sketch(es); drawing {'ready' if drawable else 'not ready'}",
                    items=items, actions=actions, missing=[] if drawable else ["Describe the building so it can be drawn."])


# ------------------------------------------------------------------------------------------------ 4 quantities & products
def _quantities(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        returned = ctx.share.status == "RETURNED"
        return StepView(DONE if returned else TODO,
                        "Your SKUs are on the returned quote" if returned else "Match each line to your product (SKU)",
                        actions=[Action("Quote the request", _request_page(ctx), primary=not returned,
                                        key="quote-request")],
                        missing=[] if returned else ["Enter your SKU for each line on the request's quote form."],
                        note="Quantities are the contractor's. Say in the notes if a pack size changes a quantity.")
    priced = _priced(ctx)
    rows = priced["rows"]
    needs = [r for r in rows if r.get("price_status") in ("NO_QUANTITY", "NO_PRODUCT")]
    items = [Item(r.get("item", ""), TODO, "needs an answer" if r["price_status"] == "NO_QUANTITY" else "choose the product")
             for r in needs]
    ready = priced["takeoff"].get("ready")
    missing = [] if ready else ["Describe the building: size, wall height and roof."]
    missing += [f"{r.get('item')}: {'answer it' if r['price_status'] == 'NO_QUANTITY' else 'choose the product'}"
                for r in needs]
    total = len([r for r in rows if r.get("price_status") not in ("EXCLUDED", "BY_DESIGN")])
    return StepView(DONE if not missing else TODO, count_headline(total - len(needs), total, "line", "with a product"),
                    items=items, missing=missing,
                    actions=[Action("Price review", _quote_page(ctx, "#pricing"), primary=True, key="pricing")])


# ------------------------------------------------------------------------------------------------ 5 availability
def _availability(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        return StepView(NOT_NEEDED, "Availability is not part of the contractor request form",
                        note="Tell the contractor in the quote notes if something is a special order.")
    rows = [r for r in _priced(ctx)["rows"] if r.get("price_status") == "PRICED"]
    known = [r for r in rows if (r.get("availability") or "UNKNOWN") != "UNKNOWN"]
    labels = {"IN_STOCK": "in stock", "LIMITED": "limited", "SPECIAL_ORDER": "special order"}
    items = [Item(f"{r.get('sku')} {r.get('product_description', '')}", INFO if r["availability"] == "IN_STOCK" else TODO,
                  labels.get(r["availability"], r["availability"].lower())) for r in known]
    if not known:
        return StepView(INFO, "Your price file does not carry availability",
                        note="Check stock in your own system. Add an availability column to the price file to show it here.",
                        actions=[Action("Price file", url_for("supplier_pro_desk.prices", supplier_id=_sid(ctx)),
                                        key="prices")])
    short = sum(1 for r in known if r["availability"] != "IN_STOCK")
    return StepView(INFO, f"{len(known)} of {len(rows)} priced lines have availability; {short} not in stock",
                    items=items)


# ------------------------------------------------------------------------------------------------ 6 pricing & terms
def _pricing(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    note = "No rewards or Pro Account points program is set up in CalibraytAI; points stay in your own system."
    if is_request(ctx):
        quote = ctx.share.quote_json or {}
        if ctx.share.status == "RETURNED":
            return StepView(DONE, f"{quote.get('lines_priced', 0)} of {quote.get('lines', 0)} lines priced · "
                                  f"${quote.get('recordable_quoted_total', '0')}",
                            actions=[Action("Open the request", _request_page(ctx), key="open-request")], note=note)
        return StepView(TODO, "Enter your price and discount for each line",
                        actions=[Action("Quote the request", _request_page(ctx), primary=True,
                                        key="quote-request")],
                        missing=["Enter your prices on the request's quote form."],
                        note="Your prices go only to this contractor. " + note)
    from app.services.supplier_pro_desk import settings_blockers

    priced = _priced(ctx)
    rows = priced["rows"]
    no_price = [r for r in rows if r.get("price_status") == "NO_PRICE"]
    count = sum(1 for r in rows if r.get("price_status") == "PRICED")
    setup = settings_blockers(_sid(ctx))
    totals = priced["totals"]
    items = [Item(f"{r.get('item')} ({r.get('sku')})", TODO, "no current price") for r in no_price]
    items.append(Item("Total", INFO, f"${totals['total']}" if totals.get("total") else "tax rate not set"))
    missing = [f"{r.get('item')}: no current price" for r in no_price] + setup
    return StepView(DONE if not missing and count else TODO,
                    f"{count} line(s) priced from your price file" + (f" · total ${totals['total']}" if totals.get("total") else ""),
                    items=items, missing=missing or ([] if count else ["Price at least one line."]),
                    actions=[Action("Price review and terms", _quote_page(ctx, "#pricing"), primary=True, key="pricing"),
                             Action("Price file", url_for("supplier_pro_desk.prices", supplier_id=_sid(ctx)), key="prices"),
                             Action("Quotation settings", url_for("supplier_pro_desk.settings", supplier_id=_sid(ctx)),
                                    key="settings")],
                    note=note + (" These prices are marked synthetic." if priced.get("demo_prices") else ""))


# ------------------------------------------------------------------------------------------------ 7 substitutions
def _substitutions(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        return StepView(INFO, "Note any substitution in the quote's general notes",
                        actions=[Action("Open the request", _request_page(ctx), key="open-request")])
    rows = _priced(ctx)["rows"]
    subs = [r for r in rows if r.get("substitution")]
    left_out = [r for r in rows if r.get("price_status") == "EXCLUDED"]
    alternatives = [r for r in rows if len(r.get("matches") or []) > 1 and not r.get("substitution")]
    items = ([Item(f"{r.get('item')}: {r.get('sku')}", INFO, "chosen product") for r in subs]
             + [Item(r.get("item", ""), NOT_NEEDED, f"left out: {r.get('reason', '')}") for r in left_out]
             + [Item(r.get("item", ""), INFO, f"{len(r['matches'])} products match") for r in alternatives])
    return StepView(INFO, f"{len(subs)} product choice(s), {len(left_out)} left out, {len(alternatives)} with alternatives",
                    items=items, actions=[Action("Price review", _quote_page(ctx, "#pricing"), key="pricing")])


# ------------------------------------------------------------------------------------------------ 8 send
def _send(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        returned = ctx.share.status == "RETURNED"
        return StepView(DONE if returned else TODO,
                        f"Returned to the contractor by {ctx.share.returned_by_name}" if returned else "Not returned yet",
                        actions=[Action("Quote the request", _request_page(ctx), primary=not returned,
                                        key="quote-request")],
                        missing=[] if returned else ["Return your quote to the contractor."])
    from app.services.supplier_pro_desk import quote_events

    q = current_quote(ctx)
    events = quote_events(q)
    links = [e for e in events if e.event_type == "LINK_CREATED"]
    emailed = [e for e in events if e.event_type == "EMAILED"]
    if q.status == "DRAFT":
        return StepView(TODO, f"{q.number} is a draft", missing=["Issue the quotation (Price review → Issue)."],
                        actions=[Action("Issue the quotation", _quote_page(ctx, "#pricing"), primary=True, key="issue")])
    items = [Item("Issued", DONE, f"{q.issued_by_name}, valid until {q.valid_until or '—'}"),
             Item("Approval link", DONE if links else TODO, f"{len(links)} made" if links else "not made"),
             Item("Emailed", DONE if emailed else INFO, f"{len(emailed)} time(s)" if emailed else "not emailed")]
    return StepView(DONE, f"{q.number} issued", items=items,
                    actions=[Action("Approval link and email", _quote_page(ctx, "#approval"), key="approval"),
                             Action("Quotation PDF", url_for("supplier_pro_desk.quote_pdf", supplier_id=_sid(ctx),
                                                             quote_id=q.id), key="quote-pdf")])


# ------------------------------------------------------------------------------------------------ 9 responses
def _responses(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        from app.services.supplier_hub import share_events

        order = _order(ctx)
        events = share_events(ctx.share)
        items = [Item(e.event_type.replace("_", " ").lower(), INFO, f"{e.actor_name}") for e in events[-8:]]
        if order is not None:
            return StepView(DONE, f"The contractor placed order {order.number}", items=items)
        if ctx.share.status == "RETURNED":
            return StepView(WAITING, "Waiting for the contractor's decision", items=items)
        return StepView(TODO, "Return your quote first", items=items, missing=["Return your quote first."])
    q = current_quote(ctx)
    items = []
    if q.id != ctx.quote.id:
        items.append(Item(f"Revised: {ctx.quote.number} → {q.number}", INFO, "the earlier quotation is kept as issued"))
    if q.status == "ACCEPTED":
        return StepView(DONE, f"Accepted by {q.accepted_by_name}", items=items)
    if q.status == "DECLINED":
        return StepView(DONE, f"Declined by {q.accepted_by_name}", items=items,
                        actions=[Action("Open the quotation", _quote_page(ctx), key="open-quote")])
    if q.status == "ISSUED":
        return StepView(WAITING, "Waiting for the customer's answer", items=items,
                        actions=[Action("Record the customer's answer", _quote_page(ctx, "#approval"), primary=True,
                                        key="record-answer"),
                                 Action("Revise the quotation", _quote_page(ctx, "#approval"), key="revise")])
    return StepView(TODO, "Issue the quotation first", items=items, missing=["Issue the quotation first (step 8)."])


# ------------------------------------------------------------------------------------------------ 10 order
def _convert(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        order = _order(ctx)
        if order is None:
            return StepView(WAITING, "Only the contractor places the order from your quote",
                            note="When they do, you confirm it here with the delivery date.")
        if order.status in ("CONFIRMED", "DELIVERED"):
            return StepView(DONE, f"Order {order.number} {order.status.lower()}",
                            actions=[Action("Open the order", _request_page(ctx), key="open-order")])
        if order.status == "CANCELLED":
            return StepView(DONE, f"Order {order.number} cancelled by the contractor")
        return StepView(TODO, f"Confirm order {order.number}" if order.status == "PLACED" else
                        f"Order {order.number}: problem reported, waiting for the contractor",
                        actions=[Action("Confirm the order", _request_page(ctx), primary=True,
                                        key="confirm-order")],
                        missing=["Confirm the order with the delivery date (or report a problem)."]
                        if order.status == "PLACED" else [])
    q = current_quote(ctx)
    if q.status != "ACCEPTED":
        return StepView(WAITING if q.status == "ISSUED" else TODO, "The customer must accept the quotation first",
                        missing=[] if q.status == "ISSUED" else ["Issue the quotation first."])
    if q.order_ready_at:
        return StepView(DONE, f"Order package ready ({q.order_ready_by_name})",
                        actions=[Action("Order package", url_for("supplier_pro_desk.order", supplier_id=_sid(ctx),
                                                                 quote_id=q.id), key="order-package"),
                                 Action("Order (CSV)", url_for("supplier_pro_desk.order_csv", supplier_id=_sid(ctx),
                                                               quote_id=q.id), key="order-csv")])
    return StepView(TODO, "Accepted — make the order package", missing=["Make the order package."],
                    actions=[Action("Make the order package", url_for("supplier_pro_desk.order_ready", supplier_id=_sid(ctx),
                                                                      quote_id=q.id), method="post", primary=True,
                                    key="order-ready")],
                    note="The package is what you enter in your own sales system; CalibraytAI does not assume one.")


# ------------------------------------------------------------------------------------------------ 11 delivery / pickup
def _delivery(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        from app.services.supplier_hub import current_schedule, pending_change

        order = _order(ctx)
        if order is None or order.status in ("PLACED", "PROBLEM"):
            return StepView(WAITING, "After the order is confirmed")
        if order.status == "CANCELLED":
            return StepView(NOT_NEEDED, "Order cancelled")
        schedule = current_schedule(order)
        change = pending_change(order)
        when = schedule["date"].strftime("%b %d, %Y") if schedule.get("date") else "date not set"
        if order.status == "DELIVERED":
            return StepView(DONE, f"Delivered ({when})")
        if change is not None and change.requested_by_side == "CONTRACTOR":
            return StepView(TODO, f"Delivery {when}: the contractor asked to change it",
                            actions=[Action("Answer the delivery change", _request_page(ctx), primary=True,
                                            key="answer-change")], missing=["Answer the contractor's delivery change."])
        return StepView(WAITING, f"Delivery booked for {when}" + (" (your change is waiting)" if change else ""),
                        actions=[Action("Deliveries", url_for("supplier_portal.supplier_deliveries", supplier_id=_sid(ctx)),
                                        key="deliveries")])
    q = current_quote(ctx)
    return StepView(NOT_NEEDED if not q.order_ready_at else INFO,
                    "Pickup or delivery is arranged in your own sales system",
                    note="CalibraytAI gives you the order package; it does not track walk-in pickups or deliveries.")


# ------------------------------------------------------------------------------------------------ 12 fulfilment & close
def _close(ctx):
    blocked = _need_record(ctx)
    if blocked:
        return blocked
    if is_request(ctx):
        from app.services.supplier_hub import order_closure

        order = _order(ctx)
        closure = order_closure(order)
        if closure is not None:
            text = (f"delivered {closure['day']:%b %d}" if closure.get("day") else closure["kind"].lower())
            return StepView(DONE, f"Order {order.number} {text}; the request and order history are kept",
                            items=[Item("Recorded by", INFO, f"{closure.get('by') or ''} ({(closure.get('side') or '').lower()})")])
        if order is not None and order.status == "CONFIRMED":
            return StepView(TODO, "Mark the order delivered when it is", missing=["Mark the order delivered."],
                            actions=[Action("Mark delivered", _request_page(ctx), primary=True,
                                            key="mark-delivered")])
        return StepView(WAITING, "After the order is confirmed and delivered")
    q = current_quote(ctx)
    from app.services.supplier_pro_desk import order_package

    if q.status == "DECLINED":
        return StepView(DONE, "Declined; the quotation history is kept")
    if not q.order_ready_at:
        return StepView(WAITING if q.status in ("ISSUED", "ACCEPTED") else TODO, "After the order package is made")
    package = order_package(q)
    items = [Item(r.get("item", ""), TODO, "not included — follow up") for r in package["not_included"]]
    return StepView(DONE, f"{len(package['lines'])} line(s) in the order; {len(package['not_included'])} not included",
                    items=items, note="The quotation, its revisions and the customer's answer are kept.")


STEPS = (
    Step("open", "Open a request or start a quotation", "The contractor request or walk-in quotation you are working on.",
         "Choose an incoming contractor request, or start a Quick Quote or new quotation and choose it here.",
         "Next, who it is for.", _open, handle=_choose,
         manual=lambda ctx: ("PRO Desk", url_for("supplier_pro_desk.index", supplier_id=ctx.supplier.id))),
    Step("who", "Contractor, customer and project", "Who the quote is for and the job it serves.",
         "Check the contractor (or customer), the project and what was asked for.", "Next, the drawings and takeoff.",
         _who),
    Step("documents", "Drawings, specifications and takeoffs", "What was shared with you, or the building you described.",
         "Read the shared takeoff, or describe the customer's building so it is drawn and taken off.",
         "Next, quantities and products.", _documents),
    Step("quantities", "Quantities and products", "Each line matched to one of your products.",
         "Match each line to your SKU. Nothing is filled in for you.", "Next, availability.", _quantities),
    Step("availability", "Availability", "Whether the products are in stock, where your price file says so.",
         "Check what is short and say so on the quote.", "Next, your prices and terms.", _availability,
         required=False),
    Step("pricing", "Your pricing and customer terms", "Your own price file, discounts, delivery and tax.",
         "Price every line (or leave it out with a reason) and set delivery and discount.",
         "Next, substitutions.", _pricing),
    Step("substitutions", "Substitutions and alternatives", "Products you chose instead, and lines left out.",
         "Review each choice; leave a line out only with a reason.", "Next, issue and send.", _substitutions,
         required=False),
    Step("send", "Prepare and send the quotation", "The quotation, frozen when issued, and how it reaches the customer.",
         "Issue it, then send the approval link (email only with consent) or print it.",
         "Next, the customer's answer.", _send),
    Step("responses", "Responses and revisions", "The customer's answer, or a revision while they decide.",
         "Record an answer given in person or by phone; revise if they ask for changes.",
         "Next, the order.", _responses),
    Step("order", "Convert to an order", "An accepted quotation becomes an order.",
         "Confirm the contractor's order with a date, or make the order package for your sales system.",
         "Next, pickup or delivery.", _convert),
    Step("delivery", "Pickup or delivery", "When the materials go out.",
         "Keep the delivery date; answer any delivery change.", "Last, fulfilment.", _delivery),
    Step("close", "Fulfilment and history", "What was delivered, what is outstanding, and the kept history.",
         "Mark the order delivered; follow up anything not included.", "The transaction is closed and kept.", _close),
)


def _subject(ctx):
    if ctx.share is not None:
        return f"Request {ctx.share.number} — {(ctx.share.shared_json or {}).get('company', '')}"
    if ctx.quote is not None:
        q = current_quote(ctx)
        return f"Quotation {q.number} — {q.customer.display_name}"
    return "Request or quotation not chosen yet"


WIZARD = Wizard(
    key=WIZARD_SUPPLIER_PRO_DESK, side="SUPPLIER", title="Supplier Pro Desk",
    short="A contractor request or a walk-in quotation, through pricing, the customer's answer, the order and delivery.",
    audience="Supplier PRO Desk staff",
    steps=STEPS, manual_label="PRO Desk",
    manual_url=lambda ctx=None: url_for("supplier_pro_desk.index", supplier_id=ctx.supplier.id) if ctx else None,
    subject=_subject,
)

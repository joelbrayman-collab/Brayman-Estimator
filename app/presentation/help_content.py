"""Reusable contractor-facing Help content authority.

Presentation only. Static copy. No database, CMS, schema, LLM, or mutation.
D1 ships Project Hub topics. Later office (D3) and Field (D4) Help should
extend this module rather than invent a second knowledge base.
"""

from __future__ import annotations

from dataclasses import dataclass

HELP_CONTROL_LABEL = "Help"
WHAT_LABEL = "What is this?"
DO_LABEL = "What should I do here?"
NEXT_LABEL = "What happens next?"
FUTURE_LABEL = "Future"

SURFACE_HUB = "hub"


@dataclass(frozen=True)
class HelpTopic:
    """One contextual Help topic for a contractor-facing surface."""

    key: str
    title: str
    what: str
    do: str | None = None
    next: str | None = None
    future: bool = False
    surface: str = SURFACE_HUB


HUB_PLAN = HelpTopic(
    key="plan",
    title="PLAN",
    what=(
        "Planning is where you keep the job drawings, site location, and permit "
        "context for this Project."
    ),
    do=(
        "Review the job address, upload plan PDFs, and read the permit report. "
        "A permit report is not municipal approval."
    ),
    next="When the job information is in place, price the work under PRICE.",
)

HUB_PRICE = HelpTopic(
    key="price",
    title="PRICE",
    what="Pricing is where you build and review the estimate for this Project.",
    do=(
        "Open the related estimates, review costing, and keep the customer price "
        "consistent before you issue."
    ),
    next="When the estimate is ready, create or issue a proposal under CONTRACT.",
)

HUB_CONTRACT = HelpTopic(
    key="contract",
    title="CONTRACT",
    what=(
        "Contract is where you see customer proposals and whether a production "
        "contract can be used for this Project."
    ),
    do=(
        "Review related proposals. Production contract generation is not available "
        "yet. This Hub shows whether a production contract can be used, or why it "
        "cannot yet. It does not create a contract."
    ),
    next=(
        "After the customer has committed, run the job from BUILD and compare "
        "estimated versus actual under MONITOR."
    ),
)

HUB_BUILD = HelpTopic(
    key="build",
    title="BUILD",
    what=(
        "Build is the working job: project work, schedule, time, Punch List, "
        "client Final Walkthrough, Change Orders, and field observations."
    ),
    do=(
        "Keep the work list current, record time, and use the Punch List for "
        "unfinished physical work. Invite the client to Final Walkthrough when "
        "you are near completion. Client comments are not the Punch List until "
        "you accept them."
    ),
    next=(
        "Use MONITOR to compare estimated versus actual. Closing the Project is a "
        "separate office action."
    ),
)

HUB_MONITOR = HelpTopic(
    key="monitor",
    title="MONITOR",
    what=(
        "Monitor compares the committed estimate to actual direct costs recorded "
        "in the office. It is not a profit figure."
    ),
    do=(
        "Follow the What / Why / Next messages already on this section. Record "
        "actual direct costs when they are known. Field observations stay evidence "
        "only."
    ),
    next=(
        "Keep recording actuals as the job proceeds. LEARN is not available on "
        "this Project yet."
    ),
)

HUB_LEARN = HelpTopic(
    key="learn",
    title="LEARN",
    what=(
        "LEARN is Future. This Hub does not recommend work, compare past jobs, "
        "or treat historical labour as this Project’s operating data."
    ),
    future=True,
)

HUB_TOPICS: dict[str, HelpTopic] = {
    topic.key: topic
    for topic in (
        HUB_PLAN,
        HUB_PRICE,
        HUB_CONTRACT,
        HUB_BUILD,
        HUB_MONITOR,
        HUB_LEARN,
    )
}


def hub_topic(key: str) -> HelpTopic:
    """Return one Project Hub Help topic. Fail closed on unknown keys."""
    try:
        return HUB_TOPICS[key]
    except KeyError as exc:
        raise KeyError(f"Unknown Hub Help topic: {key}") from exc


def topics_for_surface(surface: str) -> tuple[HelpTopic, ...]:
    """Return Help topics for a later surface (office, Field) or Hub."""
    if surface == SURFACE_HUB:
        return tuple(HUB_TOPICS[key] for key in ("plan", "price", "contract", "build", "monitor", "learn"))
    return ()


def all_help_text() -> str:
    """Concatenated Help copy for governance/language tests."""
    parts: list[str] = []
    for topic in HUB_TOPICS.values():
        parts.extend(
            part
            for part in (topic.title, topic.what, topic.do, topic.next)
            if part
        )
    return "\n".join(parts)

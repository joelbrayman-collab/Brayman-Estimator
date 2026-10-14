"""Pool-deck material takeoff (governed rule pool_deck_takeoff v1).

One authority for the curved pool-deck takeoff: geometry, board courses,
curve cuts, stock-length allocation, fascia, railing, structure, piers,
connectors, and fasteners. Brayman calculates. The supplier prices.
"""

from app.services.deck_takeoff.basis import DeckBasis, read_basis, source_record
from app.services.deck_takeoff.records import (
    CALCULATED,
    ENGINEERING_REQUIRED,
    FIELD_VERIFICATION_REQUIRED,
    PRODUCT_DEPENDENT,
    RULE_ID,
    RULE_VERSION,
)
from app.services.deck_takeoff.takeoff import calculate_pool_deck_takeoff

__all__ = [
    "CALCULATED",
    "ENGINEERING_REQUIRED",
    "FIELD_VERIFICATION_REQUIRED",
    "PRODUCT_DEPENDENT",
    "RULE_ID",
    "RULE_VERSION",
    "DeckBasis",
    "calculate_pool_deck_takeoff",
    "read_basis",
    "source_record",
]

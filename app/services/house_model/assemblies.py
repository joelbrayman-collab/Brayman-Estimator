"""Wall assemblies and the questions that set them. Thickness is the finished wall: structure + sheathing/foam + drywall.
Nominal values; the contractor confirms the real assembly. These are the answers the 'house basics' input box collects."""
from __future__ import annotations

EXTERIOR_WALLS = {
    "2x4": {"label": "2x4 wood frame", "thickness_in": 4.5},      # 3-1/2 stud + 1/2 sheathing + 1/2 drywall
    "2x6": {"label": "2x6 wood frame", "thickness_in": 6.5},      # 5-1/2 stud + 1/2 + 1/2
    "icf6": {"label": "ICF 6 in core", "thickness_in": 11.0},     # 6 core + 2 x 2-1/2 foam
    "icf8": {"label": "ICF 8 in core", "thickness_in": 13.0},     # 8 core + 2 x 2-1/2 foam
}
INTERIOR_WALL_IN = 4.5                                            # 2x4 partition with 1/2 drywall both sides

BASICS_QUESTIONS = (  # what the input box asks; anything not answered stays 'unknown' and is asked again
    ("exterior_wall", "What are the exterior walls?", tuple(EXTERIOR_WALLS)),
    ("roof_pitch", "What roof pitch (rise per 12)?", (3, 4, 5, 6, 7, 8, 9, 10, 12)),
    ("ceiling_main_ft", "Main floor ceiling height (ft)?", (8, 9, 10)),
    ("ceiling_lower_ft", "Lower level ceiling height (ft)?", (8, 9, 10)),
)

"""Baseline read from the real Merrickville lot bungalow listing picture (Joel, 23 Nov 2026).

Only what the picture shows. Room sizes are in inches (15'11" = 191). The picture has no exterior outline, wall
thickness, ceiling height or roof pitch, so those are 'unknown' questions. Sizes marked low_resolution were hard to read
at the picture's size and need a check against the real plan before anything is built from them."""
from app.services.house_model import fact, new_model


def _ft(feet, inches=0):
    return feet * 12 + inches


# Where each room sits (x right, y down, inches from the front-left corner of the main floor), placed by eye from the
# listing picture's layout. The picture gives no chained dimensions, so every position is 'assumed': a schematic.
POSITION = {"room_great": (0, 0), "room_dining": (0, 184), "room_kitchen": (0, 292), "room_foyer": (0, 444),
            "room_porch": (0, 587), "room_bed2": (197, 0), "room_bath": (197, 124), "room_master": (197, 190),
            "room_closet": (197, 346), "room_ensuite": (260, 346), "room_mud": (100, 444), "room_garage": (197, 444)}


def _room(rid, label, level, w, d, note=""):
    x, y = POSITION[rid]
    return {"id": rid, "kind": "room", "label": label, "level": level,
            "x": fact(x, "assumed", "schematic position read by eye from the picture"),
            "y": fact(y, "assumed", "schematic position read by eye from the picture"),
            "width": fact(w, "plan", note) if w is not None else fact(None, "unknown", "no size on the picture"),
            "depth": fact(d, "plan", note) if d is not None else fact(None, "unknown", "no size on the picture")}


def merrickville_bungalow():
    lv = "level_main"
    els = [
        {"id": "level_main", "kind": "level", "label": "Main floor", "ceiling_height": fact(None, "unknown", "not on the picture")},
        {"id": "level_lower", "kind": "level", "label": "Lower level", "ceiling_height": fact(None, "unknown", "not on the picture")},
        _room("room_great", "Great room", lv, _ft(15, 11), _ft(15, 4)),
        _room("room_dining", "Dining room", lv, _ft(15, 11), _ft(9, 0)),
        _room("room_kitchen", "Kitchen", lv, _ft(8, 7), _ft(12, 8)),
        _room("room_master", "Master bedroom", lv, _ft(14, 6), _ft(13, 0)),
        _room("room_bed2", "Bedroom 2", lv, _ft(12, 2), _ft(10, 4)),
        _room("room_foyer", "Foyer", lv, _ft(8, 4), _ft(11, 11)),
        _room("room_garage", "Garage", lv, _ft(20, 0), _ft(21, 0)),
        _room("room_porch", "Porch", lv, _ft(12, 9), _ft(6, 0)),
        _room("room_mud", "Mud room", lv, _ft(7, 0), _ft(9, 0), "low_resolution"),
        _room("room_closet", "Closet", lv, _ft(5, 0), _ft(9, 0), "low_resolution"),
        _room("room_ensuite", "Ensuite", lv, _ft(5, 0), _ft(9, 0), "low_resolution"),
        _room("room_bath", "Bathroom", lv, None, None),
        {"id": "wall_exterior", "kind": "wall", "label": "Exterior walls", "level": lv,
         "thickness": fact(None, "unknown", "construction type not on the picture"),
         "outline": fact(None, "unknown", "no overall building dimensions on the picture")},
        {"id": "roof_main", "kind": "roof_plane", "label": "Main roof (hip, as photographed)", "form": "hip",
         "pitch_rise_per_12": fact(None, "unknown", "low pitch in the photo, number not shown"),
         "overhang": fact(None, "unknown", "not on the picture"), "refs": ["wall_exterior"]},
    ]
    return new_model("Merrickville lot bungalow", els)

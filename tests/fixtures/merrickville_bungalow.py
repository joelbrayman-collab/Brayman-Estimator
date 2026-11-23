"""Baseline read from the real Merrickville lot bungalow listing picture (Joel, 23 Nov 2026).

Only what the picture shows. Room sizes are in inches (15'11" = 191). The picture has no exterior outline, wall
thickness, ceiling height or roof pitch, so those are 'unknown' questions. Sizes marked low_resolution were hard to read
at the picture's size and need a check against the real plan before anything is built from them."""
from app.services.house_model import fact, new_model


def _ft(feet, inches=0):
    return feet * 12 + inches


# How the rooms sit against each other, read from the listing picture's layout (left column top to bottom: great room,
# dining, kitchen, foyer, porch; right column: bedroom 2, bathroom, master, closet and ensuite; mud room and garage
# along the bottom). Positions are CALCULATED from the sizes and the wall thickness, not typed in.
PLACE = {"room_great": {"origin": True},
         "room_dining": {"x_same_as": "room_great", "y_after": "room_great"},
         "room_kitchen": {"x_same_as": "room_dining", "y_after": "room_dining"},
         "room_foyer": {"x_same_as": "room_kitchen", "y_after": "room_kitchen"},
         "room_porch": {"x_same_as": "room_foyer", "y_after": "room_foyer"},
         "room_bed2": {"y_same_as": "room_great", "x_after": "room_great"},
         "room_bath": {"x_same_as": "room_bed2", "y_after": "room_bed2"},
         "room_master": {"x_same_as": "room_bed2", "y_after": "room_bath"},
         "room_closet": {"x_same_as": "room_master", "y_after": "room_master"},
         "room_ensuite": {"x_after": "room_closet", "y_same_as": "room_closet"},
         "room_mud": {"x_after": "room_kitchen", "y_same_as": "room_kitchen"},
         "room_garage": {"x_after": "room_porch", "y_same_as": "room_foyer"}}


def _room(rid, label, level, w, d, note=""):
    return {"id": rid, "kind": "room", "label": label, "level": level, "place": PLACE[rid],
            "width": fact(w, "plan", note) if w is not None else fact(None, "unknown", "no size on the picture"),
            "depth": fact(d, "plan", note) if d is not None else fact(None, "unknown", "no size on the picture")}


def merrickville_bungalow():
    lv = "level_main"
    els = [
        {"id": "level_main", "kind": "level", "label": "Main floor", "ceiling_height": fact(108, "contractor")},
        {"id": "level_lower", "kind": "level", "label": "Lower level", "ceiling_height": fact(96, "contractor")},
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
        dict(_room("room_bath", "Bathroom", lv, _ft(5, 0), _ft(8, 0)),
             width=fact(_ft(5, 0), "assumed", "standard 5 x 8 bathroom; the picture shows no size"),
             depth=fact(_ft(8, 0), "assumed", "standard 5 x 8 bathroom; the picture shows no size")),
        {"id": "basics", "kind": "level", "label": "House basics (from the input box)",
         "exterior_wall": fact("2x6", "contractor"), "roof_pitch": fact(8, "contractor"),
         "ceiling_main_ft": fact(9, "contractor"), "ceiling_lower_ft": fact(8, "contractor")},
        {"id": "wall_exterior", "kind": "wall", "label": "Exterior walls", "level": lv,
         "thickness": fact(6.5, "contractor", "2x6 wood frame, finished"),
         "outline": fact(None, "unknown", "calculated from the room sizes and wall thickness")},
        {"id": "roof_main", "kind": "roof_plane", "label": "Main roof (hip, as photographed)", "form": "hip",
         "pitch_rise_per_12": fact(8, "contractor"),
         "overhang": fact(None, "unknown", "not on the picture"), "refs": ["wall_exterior"]},
    ]
    return new_model("Merrickville lot bungalow", els)

"""Baseline read from the real Merrickville lot bungalow listing picture (Joel, 23 Nov 2026).

Only what the picture shows. Room sizes are in inches (15'11" = 191). The picture has no exterior outline, wall
thickness, ceiling height or roof pitch, so those are 'unknown' questions. Sizes marked low_resolution were hard to read
at the picture's size and need a check against the real plan before anything is built from them."""
from app.services.house_model import fact, new_model


def _ft(feet, inches=0):
    return feet * 12 + inches


# Where each room sits, SCALED FROM THE LISTING PICTURE (23 Nov 2026): the great room's labelled 15'11" measured 360 px in
# the picture, so 1.88 px per inch; the garage's labelled 20'0" then measures 237 in (a check, within 2%). Positions are
# inches from the outer face of the main floor's top-left corner, read off the picture (source 'scaled').
# 'open' rooms (great room, dining, kitchen, foyer) are one open space with no wall between them.
AT = {"room_great": (6.5, 6.5), "room_dining": (6.5, 190.5), "room_kitchen": (6.5, 298.5), "room_foyer": (54, 450.5),
      "room_stairs": (8, 452), "room_porch": (6.5, 606), "room_bed2": (226, 6.5), "room_bath": (231, 128),
      "room_master": (199.5, 191.5), "room_closet": (239, 346), "room_ensuite": (300.5, 346),
      "room_mud": (154, 346), "room_garage": (154, 452)}
OPEN = {"room_great", "room_dining", "room_kitchen", "room_foyer"}


def _room(rid, label, level, w, d, note=""):
    x, y = AT[rid]
    return {"id": rid, "kind": "room", "label": label, "level": level, "open": rid in OPEN,
            "at": {"x": fact(x, "scaled", "scaled from the picture"), "y": fact(y, "scaled", "scaled from the picture")},
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
        dict(_room("room_bath", "Bathroom", lv, 130, 58),
             width=fact(130, "scaled", "no size labelled; scaled from the picture (about 10'-10 in)"),
             depth=fact(58, "scaled", "no size labelled; scaled from the picture (about 4'-10 in)")),
        dict(_room("room_stairs", "Basement stairs", lv, 45, 122),
             width=fact(45, "scaled", "no size labelled; scaled from the picture"),
             depth=fact(122, "scaled", "no size labelled; scaled from the picture")),
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

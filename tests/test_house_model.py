"""House model and change requests (Joel, 23 Nov 2026): a change touches only what the contractor asked for."""
import pytest

from app.services.house_model import ChangeError, ChangeRequest, apply_change, fact
from tests.fixtures.merrickville_bungalow import merrickville_bungalow

GABLE = {"id": "roof_front_gable", "kind": "roof_feature", "label": "Front gable over the entry", "form": "gable",
         "pitch_rise_per_12": fact(8, "contractor"), "width": fact(153, "assumed", "porch width, to confirm"),
         "refs": ["roof_main", "room_porch"]}


def _gable_request(**kw):
    base = dict(summary="Put a gable peak over the front entry", operation="add_element", target="roof_front_gable",
                value=GABLE, touches=("roof_main",))
    base.update(kw)
    return ChangeRequest(**base)


def test_the_baseline_reads_the_picture_and_asks_about_what_it_does_not_show():
    m = merrickville_bungalow()
    assert m.elements["room_great"]["width"] == {"v": 191, "src": "plan"}      # 15'11"
    assert m.elements["room_garage"]["depth"]["v"] == 252                      # 21'0"
    q = m.questions()
    assert any("Exterior walls" in x and "outline" in x for x in q)           # the overall outline is calculated, then confirmed
    assert not any("Great room" in x for x in q) and not any("pitch" in x for x in q)   # answered in the input box
    assert m.elements["room_bath"]["width"]["src"] == "scaled"                 # a flagged scaled value, not a silent guess


def test_a_change_alters_only_what_it_names_and_keeps_the_old_version():
    base = merrickville_bungalow()
    new, diff = apply_change(base, _gable_request())
    assert new["version"] == 2 and base["version"] == 1 and "roof_front_gable" not in base.elements
    assert diff["changed"] == ["roof_front_gable"]                           # nothing else moved, not even the roof it sits on
    for eid, h in base.hashes().items():
        if eid not in diff["changed"]:
            assert new.hashes()[eid] == h                                      # every other element identical
    assert new["parent"]["version"] == 1


def test_a_change_that_would_alter_something_it_did_not_name_is_refused():
    base = merrickville_bungalow()
    sneaky = _gable_request(operation="set_fact", target="roof_main", field_name="pitch_rise_per_12", value=6, touches=())
    new, diff = apply_change(base, sneaky)                                    # naming only its own target is fine
    assert diff["changed"] == ["roof_main"] and new.elements["roof_main"]["pitch_rise_per_12"] == {"v": 6, "src": "contractor"}
    # an edit that spills onto another element (a bad request writing a second element) is stopped by the guarantee
    import app.services.house_model.changes as C
    original = C.HouseModel.validate

    def spill(self):
        if "roof_main" in self.elements and self.elements["roof_main"].get("overhang", {}).get("v") is None \
                and "roof_front_gable" in self.elements:
            self.elements["room_great"]["width"] = fact(1, "contractor")
        return original(self)

    C.HouseModel.validate = spill
    try:
        with pytest.raises(ChangeError, match="room_great"):
            apply_change(base, _gable_request())
    finally:
        C.HouseModel.validate = original


def test_bad_requests_are_refused_not_guessed():
    base = merrickville_bungalow()
    with pytest.raises(ChangeError):
        apply_change(base, _gable_request(operation="redesign"))
    with pytest.raises(ChangeError):
        apply_change(base, _gable_request(target="no_such", operation="remove_element"))
    with pytest.raises(ChangeError):
        apply_change(base, _gable_request(value=dict(GABLE, refs=["roof_missing"])))
    with pytest.raises(ChangeError):
        apply_change(base, _gable_request(operation="set_fact", target="roof_main", field_name="no_such_field", value=1))


def test_the_overall_size_is_calculated_from_the_room_sizes_and_positions_scaled_off_the_picture():
    from app.services.house_model.layout import solve_layout

    m = merrickville_bungalow()
    lay = solve_layout(m)
    assert not lay["blocked"] and lay["overlaps"] == [] and lay["exterior_thickness"] == 6.5
    rooms = {e["id"]: e for e in m.elements.values() if e["kind"] == "room"}
    right = max(r["at"]["x"]["v"] + r["width"]["v"] for r in rooms.values())
    bottom = max(r["at"]["y"]["v"] + r["depth"]["v"] for r in rooms.values())
    assert lay["overall"]["width_in"] == right + 6.5 and lay["overall"]["depth_in"] == bottom + 6.5   # from the rooms, not typed in
    # the scale check: the garage's labelled 20'0" must equal what the picture measures (1.88 px/in, 445 px) within 3%
    assert abs(rooms["room_garage"]["width"]["v"] - 445 / 1.88) / 240 < 0.03


def test_the_basics_change_the_wall_thickness_and_so_the_overall_size():
    from app.services.house_model.layout import solve_layout

    base = merrickville_bungalow()
    icf, diff = apply_change(base, ChangeRequest(summary="Make the exterior walls ICF 8 in", operation="set_fact", target="basics",
                                                 field_name="exterior_wall", value="icf8"))
    assert diff["changed"] == ["basics"]
    assert solve_layout(icf)["exterior_thickness"] == 13.0
    assert solve_layout(icf)["overall"]["width_in"] - solve_layout(base)["overall"]["width_in"] == 13.0 - 6.5


def test_a_room_with_an_unknown_size_is_not_placed_instead_of_being_guessed():
    from app.services.house_model.layout import solve_layout

    base = merrickville_bungalow()
    unknown, _ = apply_change(base, ChangeRequest(summary="Bathroom size not known", operation="set_fact", target="room_bath",
                                                   field_name="depth", value=None, source="contractor"))
    assert "room_bath" in solve_layout(unknown)["blocked"] and "room_master" not in solve_layout(unknown)["blocked"]


def test_rooms_placed_on_top_of_each_other_are_reported_not_drawn_as_fact():
    from app.services.house_model.layout import solve_layout

    m = merrickville_bungalow()
    m.elements["room_garage"]["at"]["x"] = fact(60, "scaled")          # slide the garage onto the foyer
    assert any({"room_foyer", "room_garage"} == set(o) for o in solve_layout(m)["overlaps"])


def test_the_floor_plan_is_drawn_from_the_model_and_says_what_it_does_not_know():
    from app.services.house_model.plan_svg import floor_plan_svg

    svg = floor_plan_svg(merrickville_bungalow())
    assert svg.count("data-room=") == 13                                       # every room has a size now (two scaled)
    assert "overall width" in svg and "overall depth" in svg and "PRELIMINARY CONSTRUCTION DRAWING" in svg
    assert "Assumed: Bathroom width" in svg and "scaled from the picture" in svg
    assert "Exterior walls 6.5 in" in svg and "Roof pitch 8/12" in svg
    m = merrickville_bungalow()
    m.elements["room_garage"]["at"]["x"] = fact(60, "scaled")
    assert "Check - " in floor_plan_svg(m)                                    # a layout that does not close is printed on the sheet


def test_a_front_gable_change_leaves_the_floor_plan_drawing_identical():
    from app.services.house_model.plan_svg import floor_plan_svg

    base = merrickville_bungalow()
    new, _ = apply_change(base, _gable_request())
    a, b = floor_plan_svg(base), floor_plan_svg(new)
    assert a.replace("VERSION 1", "VERSION 2") == b                           # only the version number differs

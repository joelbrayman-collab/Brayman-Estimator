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
    assert m.elements["room_bath"]["width"]["src"] == "assumed"                # a flagged assumption, not a silent guess


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


def test_the_overall_size_is_calculated_from_the_room_sizes_and_wall_thickness():
    from app.services.house_model.layout import solve_layout

    lay = solve_layout(merrickville_bungalow())
    assert not lay["blocked"] and lay["exterior_thickness"] == 6.5
    pos = lay["positions"]
    # reading the listing picture as stacked rooms does not close: the garage lands on the closet and ensuite, and the
    # drawing says so instead of hiding it (the real plan or Ben's layout input settles it)
    assert sorted(tuple(sorted(o)) for o in lay["overlaps"]) == [("room_closet", "room_garage"), ("room_ensuite", "room_garage")]
    assert pos["room_dining"] == (0, 184 + 4.5) and pos["room_bed2"][0] == 191 + 4.5   # one 4-1/2 in wall between rooms
    o = lay["overall"]
    assert o["width_in"] == o["clear_width_in"] + 13 and o["depth_in"] == o["clear_depth_in"] + 13


def test_rooms_placed_on_top_of_each_other_are_reported_not_drawn_as_fact():
    from app.services.house_model.layout import solve_layout

    m = merrickville_bungalow()
    m.elements["room_garage"]["place"] = {"x_same_as": "room_foyer", "y_same_as": "room_foyer"}
    assert any({"room_foyer", "room_garage"} == set(o) for o in solve_layout(m)["overlaps"])


def test_the_basics_change_the_wall_thickness_and_so_the_overall_size():
    from app.services.house_model.layout import solve_layout

    base = merrickville_bungalow()
    icf, diff = apply_change(base, ChangeRequest(summary="Make the exterior walls ICF 8 in", operation="set_fact", target="basics",
                                                 field_name="exterior_wall", value="icf8"))
    assert diff["changed"] == ["basics"]
    assert solve_layout(icf)["overall"]["width_in"] - solve_layout(base)["overall"]["width_in"] == 2 * (13.0 - 6.5)


def test_a_room_with_an_unknown_size_blocks_its_neighbours_instead_of_being_guessed():
    from app.services.house_model.layout import solve_layout

    base = merrickville_bungalow()
    unknown, _ = apply_change(base, ChangeRequest(summary="Bathroom size not known", operation="set_fact", target="room_bath",
                                                   field_name="depth", value=None, source="contractor"))
    blocked = solve_layout(unknown)["blocked"]
    assert set(blocked) >= {"room_bath", "room_master", "room_closet", "room_ensuite"}   # everything that hangs off it waits
    assert "room_great" not in blocked


def test_the_floor_plan_is_drawn_from_the_model_and_says_what_it_does_not_know():
    from app.services.house_model.plan_svg import floor_plan_svg

    svg = floor_plan_svg(merrickville_bungalow())
    assert svg.count("data-room=") == 12
    assert "overall width" in svg and "overall depth" in svg and "PRELIMINARY CONSTRUCTION DRAWING" in svg
    assert "Assumed: Bathroom width" in svg and "standard 5 x 8 bathroom" in svg
    assert "Exterior walls 6.5 in" in svg
    assert "Check - Garage and Closet overlap" in svg                           # a layout that does not close is printed on the sheet


def test_a_front_gable_change_leaves_the_floor_plan_drawing_identical():
    from app.services.house_model.plan_svg import floor_plan_svg

    base = merrickville_bungalow()
    new, _ = apply_change(base, _gable_request())
    a, b = floor_plan_svg(base), floor_plan_svg(new)
    assert a.replace("VERSION 1", "VERSION 2") == b                           # only the version number differs

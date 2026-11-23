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
    assert any("Main roof" in x and "pitch rise per 12" in x for x in q)
    assert any("Bathroom" in x for x in q) and any("Exterior walls" in x and "outline" in x for x in q)
    assert not any("Great room" in x for x in q)                               # nothing asked that the plan states


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

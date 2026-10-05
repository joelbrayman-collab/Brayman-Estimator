"""Focused checks for the proof-only QCAD drawing specification."""

from tools.qcad_proof.specification import (
    MEMBER_IDS,
    POST_BEAM_BEARING_ID,
    REFUSAL,
    drawing_specification,
)


def test_specification_uses_only_the_three_members():
    packet = drawing_specification()
    assert packet["member_ids"] == list(MEMBER_IDS)
    assert set(packet["plan"]) == set(MEMBER_IDS)
    assert set(packet["elevation"]) == set(MEMBER_IDS)


def test_dimensions_come_from_the_model_geometry():
    packet = drawing_specification()
    assert packet["dimensions"]["post_height"]["inches"] == 23
    assert packet["dimensions"]["beam_length"]["inches"] == 120
    assert packet["dimensions"]["joist_length"]["inches"] == 120
    assert packet["dimensions"]["bearing"]["inches"] == 3
    assert packet["dimensions"]["bearing"]["relationship_id"] == POST_BEAM_BEARING_ID


def test_post_beam_detail_requires_the_stored_bearing():
    packet = drawing_specification()
    assert packet["detail"]["refused"] is False
    assert packet["detail"]["block_name"] == "POST_BEAM_DETAIL"
    assert packet["detail"]["relationship_id"] == POST_BEAM_BEARING_ID
    assert packet["detail"]["connector_geometry_supplied"] is True
    assert len(packet["detail"]["plate"]["bolts"]) == 2
    assert packet["relationships"]["beam_supports_joist_id"]
    assert packet["relationships"]["joist_connector_geometry_supplied"] is False


def test_missing_bearing_refuses_the_detail():
    packet = drawing_specification(omit_relationship_ids=(POST_BEAM_BEARING_ID,))
    assert packet["detail"]["refused"] is True
    assert packet["detail"]["message"] == REFUSAL
    assert packet["detail"]["block_name"] is None
    assert "bearing" not in packet["dimensions"]
    assert packet["plan"]["post-1"]["polygon"]
    assert packet["plan"]["beam-front"]["polygon"]

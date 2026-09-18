import json
from pathlib import Path

import pytest

from load_hikes import compute_difficulty

ZION_HIKES_PATH = Path(__file__).parent.parent / "data" / "zion_hikes.json"


@pytest.mark.parametrize(
    ("distance_miles", "elevation_gain_ft", "expected_tier"),
    [
        (1.0, 213, "easy"),
        (2.1, 433, "easy"),
        (3.0, 583, "moderate"),
        (4.8, 1745, "moderate"),  # Angels Landing -- needs difficulty_override to strenuous
        (9.5, 2188, "strenuous"),
    ],
)
def test_compute_difficulty_buckets(distance_miles, elevation_gain_ft, expected_tier):
    _, tier = compute_difficulty(distance_miles, elevation_gain_ft)
    assert tier == expected_tier


def test_zion_hikes_json_is_well_formed():
    data = json.loads(ZION_HIKES_PATH.read_text())
    assert data["park_code"] == "zion"
    assert len(data["hikes"]) == 5
    for hike in data["hikes"]:
        assert hike["hike_type"] in {"loop", "out_and_back", "point_to_point"}
        assert hike["highlights"]


def test_angels_landing_has_a_documented_override():
    data = json.loads(ZION_HIKES_PATH.read_text())
    angels_landing = next(h for h in data["hikes"] if h["name"] == "Angels Landing Trail")
    assert angels_landing["difficulty_override"] == "strenuous"
    assert angels_landing["difficulty_override_reason"]

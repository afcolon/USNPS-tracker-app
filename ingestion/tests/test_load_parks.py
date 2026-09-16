from load_parks import expand_combined_parks, filter_national_parks

YELLOWSTONE = {
    "parkCode": "yell",
    "fullName": "Yellowstone National Park",
    "designation": "National Park",
}
STATUE_OF_LIBERTY = {
    "parkCode": "stli",
    "fullName": "Statue Of Liberty National Monument",
    "designation": "National Monument",
}
AMERICAN_SAMOA = {
    "parkCode": "npsa",
    "fullName": "National Park of American Samoa",
    "designation": "",
}
REDWOOD = {"parkCode": "redw", "fullName": "Redwood National and State Parks", "designation": ""}
NY_HARBOR = {"parkCode": "npnh", "fullName": "National Parks of New York Harbor", "designation": ""}
SEKI = {
    "parkCode": "seki",
    "fullName": "Sequoia & Kings Canyon National Parks",
    "designation": "National Parks",
    "states": "CA",
    "description": "Ancient sequoias and granite canyons.",
    "latitude": "36.5",
    "longitude": "-118.5",
}


def test_filter_excludes_non_national_parks():
    result = filter_national_parks([YELLOWSTONE, STATUE_OF_LIBERTY])
    assert result == [YELLOWSTONE]


def test_filter_includes_manual_override_park_codes_despite_blank_designation():
    result = filter_national_parks([AMERICAN_SAMOA, REDWOOD, NY_HARBOR])
    codes = {p["parkCode"] for p in result}
    assert codes == {"npsa", "redw"}


def test_expand_combined_parks_splits_seki_into_two():
    result = expand_combined_parks([YELLOWSTONE, SEKI])
    codes = {p["parkCode"] for p in result}
    assert codes == {"yell", "seki-sequoia", "seki-kings"}
    # the split entries should still carry the shared fields (states, description, coords)
    sequoia = next(p for p in result if p["parkCode"] == "seki-sequoia")
    assert sequoia["fullName"] == "Sequoia National Park"
    assert sequoia["states"] == "CA"

from alphageist import util


def test_string_to_raw_string():
    s = "\ud835"
    rs = r"\ud835"
    assert util.string_to_raw_string(s) == rs
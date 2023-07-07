"""Unit-tests for :class:`geovista.search.Preference`."""
from __future__ import annotations

import pytest

from geovista.search import Preference

EXPECTED_VALUES: tuple[str, str] = ("center", "point")


def test_member_count():
    """Test expected number of enumeration members."""
    assert len(Preference) == 2


def test_members():
    """Test expected enumeration members."""
    assert tuple([member.value for member in Preference]) == EXPECTED_VALUES


def test_values():
    """Test expected enumeration member values."""
    assert Preference.values() == EXPECTED_VALUES


@pytest.mark.parametrize(
    "member, expected",
    [
        ("center", True),
        ("Center", True),
        ("CENTER", True),
        ("cenTer", True),
        ("point", True),
        ("Point", True),
        ("POINT", True),
        ("poInt", True),
        ("face", False),
        ("vertex", False),
    ],
)
def test_valid_members(member, expected):
    """Test valid enumeration members."""
    assert Preference.valid(member) is expected
    if expected:
        assert Preference(member).value == member.lower()
    else:
        emsg = f"{member!r} is not a valid Preference"
        with pytest.raises(ValueError, match=emsg):
            _ = Preference(member)

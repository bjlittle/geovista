# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.common.Preference`."""
from __future__ import annotations

import pytest

from geovista.common import Preference

EXPECTED_VALUES: tuple[str, str] = ("cell", "point")


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
    ("member", "expected"),
    [
        ("cell", True),
        ("Cell", True),
        ("CELL", True),
        ("ceLL", True),
        ("point", True),
        ("Point", True),
        ("POINT", True),
        ("poInt", True),
        ("center", False),
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

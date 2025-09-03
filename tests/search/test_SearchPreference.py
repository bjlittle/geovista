# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.search.SearchPreference`."""

from __future__ import annotations

import pytest

from geovista.search import SearchPreference

EXPECTED_VALUES: tuple[str, str] = ("center", "point")


def test_member_count():
    """Test expected number of enumeration members."""
    assert len(SearchPreference) == 2


def test_members():
    """Test expected enumeration members."""
    assert tuple(member.value for member in SearchPreference) == EXPECTED_VALUES


def test_members___str__():
    """Test expected enumeration members string."""
    assert tuple(str(member) for member in SearchPreference) == EXPECTED_VALUES


def test_values():
    """Test expected enumeration member values."""
    assert SearchPreference.values() == EXPECTED_VALUES


@pytest.mark.parametrize(
    ("member", "expected"),
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
    assert SearchPreference.valid(member) is expected
    if expected:
        assert SearchPreference(member).value == member.lower()
    else:
        emsg = f"{member!r} is not a valid SearchPreference"
        with pytest.raises(ValueError, match=emsg):
            _ = SearchPreference(member)

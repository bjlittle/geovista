# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.geodesic.EnclosedPreference`."""

from __future__ import annotations

import pytest

from geovista.geodesic import EnclosedPreference

EXPECTED_VALUES: tuple[str, str] = ("cell", "center", "point")


def test_member_count():
    """Test expected number of enumeration members."""
    assert len(EnclosedPreference) == 3


def test_members():
    """Test expected enumeration members."""
    assert tuple([member.value for member in EnclosedPreference]) == EXPECTED_VALUES


def test_members___str__():
    """Test expected enumeration members string."""
    assert tuple([str(member) for member in EnclosedPreference]) == EXPECTED_VALUES


def test_values():
    """Test expected enumeration member values."""
    assert EnclosedPreference.values() == EXPECTED_VALUES


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
        ("center", True),
        ("Center", True),
        ("CENTER", True),
        ("cenTER", True),
        ("face", False),
        ("vertex", False),
    ],
)
def test_valid_members(member, expected):
    """Test valid enumeration members."""
    assert EnclosedPreference.valid(member) is expected
    if expected:
        assert EnclosedPreference(member).value == member.lower()
    else:
        emsg = f"{member!r} is not a valid EnclosedPreference"
        with pytest.raises(ValueError, match=emsg):
            _ = EnclosedPreference(member)

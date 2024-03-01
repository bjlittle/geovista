# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.gridlines.create_parallel_labels`."""

from __future__ import annotations

import pytest

from geovista.gridlines import (
    LABEL_DEGREE,
    LABEL_NORTH,
    LABEL_SOUTH,
    create_parallel_labels,
)


def test_empty():
    """Test nop label generation."""
    result = create_parallel_labels([])
    assert len(result) == 0


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-90, f"90{LABEL_SOUTH}"),
        ([-90], f"90{LABEL_SOUTH}"),
        (-45, f"45{LABEL_SOUTH}"),
        ([-45], f"45{LABEL_SOUTH}"),
        (0, f"0{LABEL_DEGREE}"),
        ([0], f"0{LABEL_DEGREE}"),
        (45, f"45{LABEL_NORTH}"),
        ([45], f"45{LABEL_NORTH}"),
        (90, f"90{LABEL_NORTH}"),
        ([90], f"90{LABEL_NORTH}"),
    ],
)
def test(value, expected):
    """Test label generation of a parallel."""
    result = create_parallel_labels(value, poles_parallel=True)
    assert result == [expected]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-90, None),
        (-45, f"45{LABEL_SOUTH}"),
        (0, f"0{LABEL_DEGREE}"),
        (45, f"45{LABEL_NORTH}"),
        (90, None),
    ],
)
def test_default_poles_parallel(value, expected):
    """Test label generation of a parallel, excluding poles by default."""
    result = create_parallel_labels(value)
    expected = [] if expected is None else [expected]
    assert result == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-90.1, f"90{LABEL_SOUTH}"),
        (-45.12, f"45{LABEL_SOUTH}"),
        (0.123, f"0{LABEL_DEGREE}"),
        (45.1234, f"45{LABEL_NORTH}"),
        (90.12345, f"90{LABEL_NORTH}"),
    ],
)
def test_truncation(value, expected):
    """Test label generation performs value truncation."""
    result = create_parallel_labels(value, poles_parallel=True)
    assert result == [expected]

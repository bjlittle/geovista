# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.vectors_to_cartesian`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import vectors_to_cartesian

#: Two points, as longitudes and latitudes.
LONS, LATS = [0.0, 90.0], [0.0, 45.0]

#: The eastward, northward and upward components of a vector at each point.
VECTORS = ([1.0, 2.0], [3.0, 4.0], [5.0, 6.0])


def _arrays(*values: list[float]) -> tuple[np.ndarray, ...]:
    """Return each of the values as an array."""
    return tuple(np.array(value) for value in values)


@pytest.mark.parametrize(
    ("component", "expected"),
    [(0, [0.0, 1.0, 0.0]), (1, [0.0, 0.0, 1.0]), (2, [1.0, 0.0, 0.0])],
    ids=["eastward", "northward", "upward"],
)
def test_unit_vectors_at_the_origin(component, expected):
    """Each unit component at (0, 0) points along its own cartesian axis."""
    vectors = [np.zeros(1), np.zeros(1), np.zeros(1)]
    vectors[component] = np.ones(1)

    result = vectors_to_cartesian(np.zeros(1), np.zeros(1), tuple(vectors), radius=1.0)

    np.testing.assert_allclose(np.ravel(result), expected, atol=1e-15)


@pytest.mark.parametrize("given", ["points", "vectors", "both"])
def test_lists(given):
    """Lists are accepted wherever arrays are (typing spec §3.3)."""
    expected = vectors_to_cartesian(*_arrays(LONS, LATS), _arrays(*VECTORS))
    lons, lats = (LONS, LATS) if given != "vectors" else _arrays(LONS, LATS)
    vectors = VECTORS if given != "points" else _arrays(*VECTORS)

    result = vectors_to_cartesian(lons, lats, vectors)

    np.testing.assert_array_equal(result, expected)


def test_vectors_must_match_the_points():
    """A component of another shape than the points is refused."""
    with pytest.raises(ValueError, match="some 'vectors' do not have same shape"):
        _ = vectors_to_cartesian(LONS, LATS, ([1.0], [3.0, 4.0], [5.0, 6.0]))

# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for lists given to :class:`geovista.Transform` where arrays may be."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.bridge import Transform

#: Each factory with arguments given as lists, where its signature says ArrayLike.
CASES = {
    "from_1d": (
        Transform.from_1d,
        ([0.0, 10.0, 20.0], [0.0, 10.0]),
        {"data": [1.0, 2.0]},
    ),
    "from_1d_bounds": (
        Transform.from_1d,
        ([[0.0, 10.0], [10.0, 20.0]], [[0.0, 10.0]]),
        {},
    ),
    "from_2d": (
        Transform.from_2d,
        ([[0.0, 10.0], [0.0, 10.0]], [[0.0, 0.0], [10.0, 10.0]]),
        {"data": [5.0]},
    ),
    "from_points": (
        Transform.from_points,
        ([0.0, 10.0], [0.0, 10.0]),
        {"data": [1.0, 2.0], "zlevel": [1, 2]},
    ),
    "from_unstructured": (
        Transform.from_unstructured,
        ([0.0, 10.0, 10.0, 0.0], [0.0, 0.0, 10.0, 10.0]),
        {"connectivity": [[0, 1, 2, 3]], "data": [1.0]},
    ),
    "to_structured_grid": (
        Transform.to_structured_grid,
        ([0.0, 10.0], [0.0, 10.0], [0.0, 1.0]),
        {"data": [7.0]},
    ),
}


@pytest.mark.parametrize(
    ("factory", "args", "kwargs"), CASES.values(), ids=CASES.keys()
)
def test_lists(factory, args, kwargs):
    """Lists build the mesh that arrays do (typing spec §3.3)."""
    expected = factory(
        *(np.array(arg) for arg in args),
        **{key: np.array(value) for key, value in kwargs.items()},
    )

    result = factory(*args, **kwargs)

    np.testing.assert_array_equal(result.points, expected.points)
    assert result.array_names == expected.array_names
    for name in expected.array_names:
        np.testing.assert_array_equal(result[name], expected[name])


def test_instance_lists():
    """An instance built from lists attaches data given as a list."""
    transform = Transform(
        [0.0, 10.0, 10.0, 0.0], [0.0, 0.0, 10.0, 10.0], connectivity=[[0, 1, 2, 3]]
    )

    mesh = transform(data=[3.0])

    np.testing.assert_array_equal(mesh["cell_data"], [3.0])

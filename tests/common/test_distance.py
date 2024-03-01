# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.distance`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import RADIUS, distance


@pytest.mark.parametrize("origin", [np.empty((2, 2)), range(4)])
def test_origin_fail(lfric, origin):
    """Test trap of invalid origin."""
    emsg = r"Require an \(x, y, z\) cartesian point"
    with pytest.raises(ValueError, match=emsg):
        _ = distance(lfric, origin=origin)


@pytest.mark.parametrize("scale", range(1, 11))
def test_mean_distance(lfric, scale):
    """Test mean distance calculation of mesh."""
    mesh = lfric.scale(scale)
    result = distance(mesh)
    assert np.isclose(result, scale)


@pytest.mark.parametrize(
    "origin",
    [
        np.random.default_rng().integers(0, high=10, size=3).astype(float)
        for _ in range(10)
    ],
)
def test_mean_distance__origin(lfric, origin):
    """Test mean distance with mesh translated to random origin."""
    mesh = lfric.translate(origin)
    np.testing.assert_array_equal(mesh.center, origin)
    result = distance(mesh, origin=origin)
    assert np.isclose(result, RADIUS)


@pytest.mark.parametrize("scale", range(1, 11))
def test_point_distance(lfric, scale):
    """Test point distance calculation of mesh."""
    mesh = lfric.scale(scale)
    result = distance(mesh, mean=False)
    assert result.size == lfric.n_points
    assert np.isclose(np.sum(result), lfric.n_points * scale)


@pytest.mark.parametrize(
    "origin",
    [
        np.random.default_rng().integers(0, high=10, size=3).astype(float)
        for _ in range(10)
    ],
)
def test_point_distance__origin(lfric, origin):
    """Test point distance with mesh translated to random origin."""
    mesh = lfric.translate(origin)
    np.testing.assert_array_equal(mesh.center, origin)
    result = distance(mesh, origin=origin, mean=False)
    assert result.size == lfric.n_points
    assert np.isclose(np.sum(result), lfric.n_points * RADIUS)

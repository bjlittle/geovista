# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that `Transform.to_structured_grid` reads its levels as heights."""

from __future__ import annotations

import numpy as np
import pint
import pytest

from geovista.bridge import NAME_CELLS, Transform
from geovista.globe import Globe

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]

#: The cell bounds of a small grid, in longitude and latitude.
XS, YS = [0.0, 10.0, 20.0], [0.0, 10.0]

#: Uneven levels, in metres above mean sea level.
ZS = [0.0, 100.0, 1000.0, 5000.0]


def _points(zs: list[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the longitude, latitude and height of each point, in grid order."""
    xv, yv, zv = np.meshgrid(XS, YS, zs, indexing="ij")
    return xv.ravel(order="F"), yv.ravel(order="F"), zv.ravel(order="F")


@pytest.mark.parametrize("radius", RADII)
def test_levels_at_their_heights(radius, at_heights):
    """Each level lies at its height, however unevenly the levels are spaced."""
    globe = Globe(render_radius=radius, exaggeration=20)
    grid = Transform.to_structured_grid(XS, YS, ZS, globe=globe)
    lons, lats, heights = _points(ZS)
    np.testing.assert_array_equal(grid.gv.height, heights)
    np.testing.assert_allclose(
        grid.points,
        at_heights(lons, lats, heights, globe),
        rtol=1e-9,
        atol=1e-9 * radius,
    )


def test_levels_in_another_unit():
    """Levels in another unit, or as a quantity, read back in metres."""
    grid = Transform.to_structured_grid(XS, YS, [0, 1, 3], vertical_units="km")
    np.testing.assert_array_equal(np.unique(grid.gv.height), [0.0, 1000.0, 3000.0])

    feet = pint.UnitRegistry().Quantity([0, 1000, 3000], "foot")
    grid = Transform.to_structured_grid(XS, YS, feet)
    np.testing.assert_allclose(np.unique(grid.gv.height), [0.0, 304.8, 914.4])


def test_a_grid_of_depths_passes_their_negation(at_heights):
    """A grid of depths lies below sea level, by the factor below it."""
    globe = Globe(exaggeration_below=100)
    zs = list(-np.array([0.0, 10.0, 50.0]))
    grid = Transform.to_structured_grid(XS, YS, zs, globe=globe)
    lons, lats, heights = _points(zs)
    np.testing.assert_allclose(
        grid.points, at_heights(lons, lats, heights, globe), rtol=1e-12, atol=1e-12
    )
    assert np.all(np.linalg.norm(grid.points, axis=1) <= 1.0)


@pytest.mark.parametrize(
    "zs",
    [
        [0.0, np.nan, 10.0],
        [0.0, np.inf, 10.0],
        np.ma.masked_array([0.0, 5.0, 10.0], mask=[0, 1, 0]),
    ],
    ids=["nan", "inf", "masked"],
)
def test_levels_must_be_finite(zs):
    """A level is a coordinate, so cannot be missing or infinite."""
    with pytest.raises(ValueError, match="finite"):
        Transform.to_structured_grid(XS, YS, zs)


@pytest.mark.parametrize("keyword", ["zlevel", "zscale"])
def test_zlevel_is_gone(keyword):
    """The levels are heights, so take no z-level and no zscale."""
    with pytest.raises(TypeError, match=keyword):
        Transform.to_structured_grid(XS, YS, ZS, **{keyword: 1})


def test_heights_are_not_the_data():
    """The data stays the active scalars, which threshold reads."""
    data = [np.nan, 1.0, 2.0, 3.0]
    grid = Transform.to_structured_grid(XS, YS, ZS[:3], data=data)
    assert grid.active_scalars_name == NAME_CELLS
    assert grid.threshold().n_cells == 3

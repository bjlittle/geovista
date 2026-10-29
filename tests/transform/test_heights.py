# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that :func:`geovista.transform.transform_mesh` places heights."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.bridge import Transform
from geovista.common import (
    _GV_GLOBE_FIELDS,
    GV_FIELD_ZSCALE,
    GV_POINT_HEIGHT,
    GV_POINT_ZLEVEL,
)
from geovista.crs import WGS84
from geovista.globe import Globe
from geovista.transform import transform_mesh

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]

#: The Earth's radius of the default globe, in metres.
R = 6378137.0

#: The cell bounds of a small grid, and its points in the order the bridge builds.
XS, YS = [0.0, 10.0, 20.0], [0.0, 10.0]
LONS, LATS = (np.ravel(axis) for axis in np.meshgrid(XS, YS, indexing="xy"))

#: A height for each point, above and below sea level, at it, and one missing.
HEIGHTS = np.array([1000.0, -4000.0, np.nan, 250.0, 0.0, -10.0])

#: A globe that exaggerates heights above and below sea level by their own factors.
EXAGGERATED = {"exaggeration": 20, "exaggeration_below": 100}

#: The cell bounds of a global grid, whose seam a central meridian of 75 cuts.
GLOBAL_XS, GLOBAL_YS = np.arange(-180.0, 181.0, 30.0), np.arange(-90.0, 91.0, 30.0)

#: A map whose seam, at -105, cuts the cells of the global grid.
CUT = "+proj=eqc +lon_0=75"


def _mapped(heights: np.ndarray, globe: Globe) -> np.ndarray:
    """Return V(h), worked out with numpy alone, with a missing height as 0."""
    heights = np.asarray(heights, dtype=np.float64)
    mapped = np.where(
        heights >= 0,
        globe.exaggeration * heights,
        globe.exaggeration_below * heights,
    )
    return np.where(np.isnan(heights), 0.0, mapped)


def _global(heights_of=None) -> Transform:
    """Return a global grid, with heights worked out from its unlifted points."""
    mesh = Transform.from_1d(GLOBAL_XS, GLOBAL_YS)
    if heights_of is None:
        return mesh
    return Transform.from_1d(GLOBAL_XS, GLOBAL_YS, height=heights_of(mesh.points))


@pytest.mark.parametrize("radius", RADII)
@pytest.mark.parametrize(
    ("crs", "unit"),
    [
        ("+proj=eqc", lambda mapped: mapped),
        ("+proj=eqc +units=km", lambda mapped: mapped / 1000.0),
        ("+proj=longlat +ellps=GRS80 +no_defs", lambda mapped: np.degrees(mapped / R)),
    ],
    ids=["metres", "kilometres", "degrees"],
)
def test_on_a_map_by_the_formula(crs, unit, radius):
    """On a map a point lies at V(h), in the unit of the map's axes."""
    globe = Globe(render_radius=radius, **EXAGGERATED)
    mesh = Transform.from_1d(XS, YS, height=HEIGHTS, globe=globe)
    result = transform_mesh(mesh, crs)
    expected = unit(_mapped(result[GV_POINT_HEIGHT], globe))
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-12)
    assert np.any(result.points[:, 2])


@pytest.mark.parametrize("radius", RADII)
def test_back_to_the_globe(radius, at_heights):
    """A mesh with heights brought back from a map lies at s (R + V(h))."""
    mesh = Transform.from_1d(XS, YS, height=HEIGHTS)
    projected = transform_mesh(mesh, "+proj=eqc", slice_connectivity=False)
    globe = Globe(render_radius=radius, **EXAGGERATED)
    result = transform_mesh(projected, WGS84, globe=globe)
    np.testing.assert_allclose(
        result.points,
        at_heights(LONS, LATS, HEIGHTS, globe),
        rtol=1e-9,
        atol=1e-9 * radius,
    )
    assert Globe.from_mesh(result) == globe


@pytest.mark.parametrize("kind", ["surface", "cloud"])
def test_round_trip(kind):
    """A mesh projected and brought back lies where it started."""
    globe = Globe(render_radius=6378137.0, **EXAGGERATED)
    if kind == "surface":
        mesh = Transform.from_1d(XS, YS, height=HEIGHTS, globe=globe)
    else:
        mesh = Transform.from_points(LONS, LATS, height=HEIGHTS, globe=globe)
    projected = transform_mesh(mesh, "+proj=eqc", slice_connectivity=False)
    result = transform_mesh(projected, WGS84)
    np.testing.assert_allclose(result.points, mesh.points, rtol=1e-9, atol=1e-3)
    np.testing.assert_array_equal(result.gv.height, HEIGHTS)


def test_the_seam_cut_keeps_heights():
    """The seam cut carries heights to the points it adds."""
    mesh = _global(lambda points: 1000.0 * points[:, 2])
    result = transform_mesh(mesh, CUT)
    assert result.n_points > mesh.n_points
    heights = result[GV_POINT_HEIGHT]
    assert not np.any(np.isnan(heights))
    np.testing.assert_allclose(result.points[:, 2], heights, rtol=1e-12)


def test_missing_heights_on_a_map():
    """A missing height is drawn at sea level, as is a point the cut adds by one."""
    mesh = _global(lambda points: np.where(np.isclose(points[:, 1], 0), np.nan, 1.0))
    missing = int(np.sum(np.isnan(mesh.gv.height)))
    result = transform_mesh(mesh, CUT)
    heights = result[GV_POINT_HEIGHT]
    nan = np.isnan(heights)
    assert np.sum(nan) > missing
    np.testing.assert_array_equal(result.points[nan, 2], 0.0)
    np.testing.assert_allclose(result.points[~nan, 2], 1.0, rtol=1e-12)


def test_a_zlevel_is_refused_with_heights():
    """A mesh with heights takes no z-level other than 0."""
    mesh = Transform.from_1d(XS, YS, height=HEIGHTS)
    with pytest.raises(ValueError, match="z-level"):
        transform_mesh(mesh, "+proj=eqc", zlevel=1)
    for zlevel in (0, np.zeros(mesh.n_points)):
        result = transform_mesh(mesh, "+proj=eqc", zlevel=zlevel)
        np.testing.assert_allclose(
            result.points[:, 2], _mapped(result[GV_POINT_HEIGHT], Globe())
        )


def test_a_cloud_carries_no_levels():
    """A cloud with heights carries no z-level on a map."""
    cloud = Transform.from_points(LONS, LATS, height=HEIGHTS)
    result = transform_mesh(cloud, "+proj=eqc")
    assert GV_POINT_ZLEVEL not in result.point_data
    assert GV_FIELD_ZSCALE not in result.field_data
    np.testing.assert_allclose(result.points[:, 2], _mapped(HEIGHTS, Globe()))


def test_no_transform_moves_no_point():
    """A mesh already in the target CRS keeps its points and its globe."""
    mesh = Transform.from_1d(XS, YS, height=HEIGHTS)
    result = transform_mesh(mesh, WGS84, globe=Globe(render_radius=2))
    np.testing.assert_array_equal(result.points, mesh.points)
    assert Globe.from_mesh(result) == Globe()


def test_no_globe_is_the_default():
    """A mesh with heights and no globe is placed at the default globe."""
    mesh = Transform.from_1d(XS, YS, height=HEIGHTS, globe=Globe(**EXAGGERATED))
    for name in _GV_GLOBE_FIELDS:
        del mesh.field_data[name]
    result = transform_mesh(mesh, "+proj=eqc")
    np.testing.assert_allclose(
        result.points[:, 2], np.nan_to_num(result[GV_POINT_HEIGHT]), rtol=1e-12
    )
    assert Globe.from_mesh(result) == Globe()

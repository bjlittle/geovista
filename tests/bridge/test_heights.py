# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that the :mod:`geovista.bridge` builders take heights and depths."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pint
import pytest

from geovista.bridge import NAME_CELLS, NAME_POINTS, NAME_VECTORS, Transform
from geovista.common import GV_FIELD_ZSCALE, from_cartesian
from geovista.globe import Globe

if TYPE_CHECKING:
    from collections.abc import Callable

    import pyvista as pv

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]

#: The cell bounds of a small regular grid, of 2 cells and 6 points.
XS, YS = [0.0, 10.0, 20.0], [0.0, 10.0]

#: The points of the grid, in the order the bridge builds them.
GRID_LONS, GRID_LATS = (np.ravel(axis) for axis in np.meshgrid(XS, YS, indexing="xy"))

#: The points of a small 2D mesh, of 4 cells and 9 points.
LONS_2D, LATS_2D = np.meshgrid([0.0, 10.0, 20.0], [0.0, 10.0, 20.0], indexing="xy")

#: The points of a small cloud.
CLOUD_LONS, CLOUD_LATS = [0.0, 10.0, 20.0, 30.0], [0.0, 5.0, 10.0, 15.0]

#: The points and faces of a small unstructured mesh, of 2 cells and 6 points.
UNSTRUCTURED_LONS = [0.0, 10.0, 10.0, 0.0, 20.0, 20.0]
UNSTRUCTURED_LATS = [0.0, 0.0, 10.0, 10.0, 0.0, 10.0]
CONNECTIVITY = [[0, 1, 2, 3], [1, 4, 5, 2]]

#: Each builder, with the longitudes and latitudes of its points in order, and its
#: number of cells.
BUILDERS: dict[str, tuple[Callable[..., pv.PolyData], np.ndarray, np.ndarray, int]] = {
    "from_1d": (
        lambda **kwargs: Transform.from_1d(XS, YS, clean=False, **kwargs),
        GRID_LONS,
        GRID_LATS,
        2,
    ),
    "from_2d": (
        lambda **kwargs: Transform.from_2d(LONS_2D, LATS_2D, clean=False, **kwargs),
        np.ravel(LONS_2D),
        np.ravel(LATS_2D),
        4,
    ),
    "from_points": (
        lambda **kwargs: Transform.from_points(
            CLOUD_LONS, CLOUD_LATS, clean=False, **kwargs
        ),
        np.array(CLOUD_LONS),
        np.array(CLOUD_LATS),
        4,
    ),
    "from_unstructured": (
        lambda **kwargs: Transform.from_unstructured(
            UNSTRUCTURED_LONS,
            UNSTRUCTURED_LATS,
            connectivity=CONNECTIVITY,
            clean=False,
            **kwargs,
        ),
        np.array(UNSTRUCTURED_LONS),
        np.array(UNSTRUCTURED_LATS),
        2,
    ),
    "call": (
        lambda **kwargs: Transform(XS, YS, clean=False, **kwargs)(),
        GRID_LONS,
        GRID_LATS,
        2,
    ),
}

IDS = list(BUILDERS)


def _heights(n_points: int) -> np.ndarray:
    """Return heights above and below sea level, at it, and one missing."""
    return np.resize([1000.0, -4000.0, np.nan, 250.0, 0.0, -10.0], n_points)


@pytest.fixture(params=IDS)
def builder(request) -> tuple[Callable[..., pv.PolyData], np.ndarray, np.ndarray, int]:
    """Fixture for each builder, its points in order, and its number of cells."""
    return BUILDERS[request.param]


@pytest.mark.parametrize(
    ("given", "metres"),
    [
        ({"height": 1000, "vertical_units": "ft"}, 304.8),
        ({"height": pint.UnitRegistry().Quantity(1, "km")}, 1000.0),
        ({"height": 1000.0}, 1000.0),
    ],
    ids=["vertical_units", "quantity", "metres"],
)
def test_reads_back_in_metres(builder, given, metres):
    """A height in any form reads back in metres at every point."""
    build, *_ = builder
    np.testing.assert_allclose(build(**given).gv.height, metres)


@pytest.mark.parametrize("radius", RADII)
def test_placed_by_the_formula(builder, radius, at_heights):
    """Each point lies at s (R + V(h)), and the mesh records its globe."""
    build, lons, lats, _ = builder
    globe = Globe(render_radius=radius, exaggeration=20, exaggeration_below=100)
    heights = _heights(lons.size)
    mesh = build(height=heights, globe=globe)
    np.testing.assert_allclose(
        mesh.points,
        at_heights(lons, lats, heights, globe),
        rtol=1e-9,
        atol=1e-9 * radius,
    )
    assert Globe.from_mesh(mesh) == globe


def test_depth_gives_the_negated_height(builder):
    """A depth places a point where the negated height does."""
    build, lons, *_ = builder
    depths = _heights(lons.size)
    mesh = build(depth=depths)
    np.testing.assert_array_equal(mesh.points, build(height=-depths).points)
    np.testing.assert_array_equal(mesh.gv.depth, depths)


def test_missing_heights_at_sea_level(builder):
    """A masked height and a NaN read back as NaN, and lie at sea level."""
    build, lons, *_ = builder
    heights = np.ma.masked_array(np.full(lons.size, 100.0), mask=False)
    heights[0] = np.ma.masked
    heights[1] = np.nan
    mesh = build(height=heights)
    np.testing.assert_array_equal(mesh.gv.height[:2], np.nan)
    np.testing.assert_allclose(np.linalg.norm(mesh.points[:2], axis=1), 1.0)


def test_never_the_active_scalars(builder):
    """Heights never become the active scalars."""
    build, lons, *_ = builder
    assert build(height=_heights(lons.size)).active_scalars_name is None


@pytest.mark.parametrize(
    ("build", "name"),
    [
        (
            lambda **kwargs: Transform.from_1d(XS, YS, data=[1.0, 2.0], **kwargs),
            NAME_CELLS,
        ),
        (
            lambda **kwargs: Transform.from_points(
                CLOUD_LONS, CLOUD_LATS, data=[1.0, 2.0, 3.0, 4.0], **kwargs
            ),
            NAME_POINTS,
        ),
    ],
    ids=["cells", "points"],
)
def test_the_data_stays_active(build, name):
    """The data stays the active scalars when heights are given with it."""
    assert build(height=100.0).active_scalars_name == name


def test_a_cloud_records_no_zscale():
    """A cloud with heights carries no z-level."""
    cloud = Transform.from_points(CLOUD_LONS, CLOUD_LATS, height=_heights(4))
    assert GV_FIELD_ZSCALE not in cloud.field_data
    np.testing.assert_array_equal(from_cartesian(cloud)[:, 2], 0.0)


def test_vectors_keep_their_components():
    """Vectors built with heights are those built without them."""
    vectors = ([1.0, 2.0, 3.0, 4.0], [0.5, 0.5, 0.5, 0.5], [0.0, 1.0, 0.0, 1.0])
    expected = Transform.from_points(CLOUD_LONS, CLOUD_LATS, vectors=vectors)
    result = Transform.from_points(
        CLOUD_LONS, CLOUD_LATS, vectors=vectors, height=1000.0
    )
    np.testing.assert_array_equal(result[NAME_VECTORS], expected[NAME_VECTORS])


@pytest.mark.parametrize("radius", RADII)
def test_the_factory_carries_heights(radius):
    """Each mesh a factory makes carries the heights it was made with."""
    globe = Globe(render_radius=radius, exaggeration=20, exaggeration_below=100)
    heights = _heights(6)
    expected = Transform.from_1d(XS, YS, height=heights, globe=globe)
    mesh = Transform(XS, YS, height=heights, globe=globe)(data=[1.0, 2.0])
    np.testing.assert_array_equal(mesh.gv.height, expected.gv.height)
    np.testing.assert_array_equal(mesh.points, expected.points)
    assert mesh.active_scalars_name == NAME_CELLS


def test_threshold_keeps_the_sea_at_its_depths(at_heights):
    """Data and depths masked over land drop with it, keeping the sea's depths."""
    lons, lats = [0.0, 10.0, 20.0, 30.0, 40.0], [0.0, 10.0, 20.0, 30.0]
    data = np.ma.masked_array(np.arange(12.0).reshape(3, 4), mask=False)
    data[:, 0] = np.ma.masked
    rows, cols = np.mgrid[0:4, 0:5]
    depths = np.ma.masked_array(1000.0 * cols + 100.0 * rows, mask=False)
    depths[:, 0] = np.ma.masked
    globe = Globe(exaggeration_below=100)

    mesh = Transform.from_1d(lons, lats, data=data, depth=depths, globe=globe)
    sea = mesh.threshold()

    assert sea.n_cells == 9
    assert sea.n_points == 16
    heights = sea.gv.height
    assert not np.any(np.isnan(heights))
    np.testing.assert_array_equal(np.sort(heights), np.sort(-depths[:, 1:].ravel()))
    radii = np.linalg.norm(sea.points, axis=1)
    expected = np.linalg.norm(at_heights([0.0], [0.0], heights, globe), axis=1)
    np.testing.assert_allclose(radii, expected, rtol=1e-12)


def test_height_with_depth(builder):
    """A height and a depth are never given together."""
    build, lons, *_ = builder
    with pytest.raises(ValueError, match=r"height.*depth"):
        build(height=_heights(lons.size), depth=1.0)


def test_height_with_a_zlevel(builder):
    """A height is never given with a z-level other than 0."""
    build, lons, *_ = builder
    with pytest.raises(ValueError, match=r"z-level.*zlevel=2"):
        build(height=_heights(lons.size), zlevel=2)


def test_a_cloud_with_levels():
    """A cloud is never given heights and levels other than 0."""
    with pytest.raises(ValueError, match="z-level"):
        Transform.from_points(
            CLOUD_LONS, CLOUD_LATS, height=_heights(4), zlevel=[0, 1, 0, 0]
        )


def test_zero_zlevel_with_heights(builder):
    """A z-level of 0 is no z-level."""
    build, lons, *_ = builder
    heights = _heights(lons.size)
    np.testing.assert_array_equal(
        build(height=heights, zlevel=0).points, build(height=heights).points
    )


@pytest.mark.parametrize("name", ["from_1d", "from_2d", "from_unstructured", "call"])
def test_a_height_for_each_cell(name):
    """A height for each cell is refused, naming the issue that would add it."""
    build, *_, n_cells = BUILDERS[name]
    with pytest.raises(ValueError, match="2728"):
        build(height=np.arange(float(n_cells)))


def test_the_wrong_number_of_heights(builder):
    """Heights that fit neither the points nor the whole mesh are refused."""
    build, lons, *_ = builder
    with pytest.raises(ValueError, match=rf"{lons.size} points.*got 5"):
        build(height=np.arange(5.0))


def test_an_infinite_height(builder):
    """An infinite height is refused."""
    build, lons, *_ = builder
    heights = np.zeros(lons.size)
    heights[-1] = np.inf
    with pytest.raises(ValueError, match="infinite"):
        build(height=heights)


def test_vertical_units_alone(builder):
    """vertical_units names the unit of a height, so is refused with none."""
    build, *_ = builder
    with pytest.raises(ValueError, match="vertical_units"):
        build(vertical_units="ft")


@pytest.mark.parametrize("build", ["from_1d", "from_points"])
def test_an_ellipsoidal_height(build):
    """Heights are refused with a CRS whose height is above the ellipsoid."""
    build = BUILDERS[build][0]
    with pytest.raises(ValueError, match="Ellipsoidal height"):
        build(height=100.0, crs="EPSG:4979")
    assert build(crs="EPSG:4979").gv.height is None

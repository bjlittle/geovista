# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.transform.transform_mesh`."""

from __future__ import annotations

import cartopy.crs as ccrs
import numpy as np
from pyproj import CRS, Transformer
import pytest
import pyvista as pv

import geovista as gv
from geovista.common import from_cartesian, to_cartesian
from geovista.crs import WGS84, projected, to_wkt
from geovista.transform import _ZLEVEL, transform_mesh

#: Fraction of the projection width above which a cell is considered torn.
TORN = 0.25

#: Central meridian shift that exercises the seam of a global mesh.
MERIDIAN: float = 180.0

#: Longitude/latitude extent of a regional mesh, as (xmin, xmax, ymin, ymax).
REGION: tuple[float, float, float, float] = (10.0, 30.0, 30.0, 50.0)

#: Central meridian shift applied to a regional mesh.
REGIONAL_MERIDIAN: float = 45.0

#: A planar target CRS, so that a z-level is scaled into each point's z-value.
PLANAR = "+proj=eqc"

#: Whole-globe projections carrying the central meridian in assorted ways.
#:
#: Note that "LambertConformal" and "NearsidePerspective" are deliberately
#: absent, as their limited projection domain cannot accommodate a global mesh
#: at any central meridian. Their central meridian recovery is covered by
#: ``tests/crs/test_get_central_meridian.py``.
PROJECTIONS = [
    ("Mollweide", ccrs.Mollweide),
    ("Robinson", ccrs.Robinson),
    ("AlbersEqualArea", ccrs.AlbersEqualArea),
    ("EquidistantConic", ccrs.EquidistantConic),
    ("Hammer", ccrs.Hammer),
    ("PlateCarree", ccrs.PlateCarree),
]


@pytest.fixture
def global_mesh():
    """Create a 10 degree global quad mesh."""
    lons = np.arange(-180, 181, 10, dtype=float)
    lats = np.arange(-90, 91, 10, dtype=float)
    shape = (lats.size - 1, lons.size - 1)
    data = np.arange(np.prod(shape), dtype=float).reshape(shape)
    return gv.Transform.from_1d(lons, lats, data=data)


@pytest.fixture
def regional_mesh():
    """Create a regional quad mesh, clear of both the seam and the poles."""
    lon_min, lon_max, lat_min, lat_max = REGION
    lons = np.linspace(lon_min, lon_max, 3)
    lats = np.linspace(lat_min, lat_max, 3)
    data = np.arange(4, dtype=float).reshape(2, 2)
    return gv.Transform.from_1d(lons, lats, data=data)


@pytest.fixture
def cloud():
    """Create a small point cloud, which ``transform_mesh`` never slices."""
    return gv.Transform.from_points([10.0, 20.0, 30.0], [30.0, 40.0, 50.0])


@pytest.fixture
def lone_point():
    """Create a point cloud of one point."""
    return gv.Transform.from_points([10.0], [30.0])


def _cell_widths(mesh) -> np.ndarray:
    """Calculate each cell width as a fraction of the projection width."""
    points, faces = mesh.points, mesh.faces.reshape(-1, 5)[:, 1:]
    xs = points[faces, 0]
    span = points[:, 0].max() - points[:, 0].min()
    return (xs.max(axis=1) - xs.min(axis=1)) / span


def _torn_cells(mesh) -> int:
    """Count cells spanning an implausible fraction of the projection width."""
    return int((_cell_widths(mesh) > TORN).sum())


@pytest.mark.parametrize(
    "projection", [p for _, p in PROJECTIONS], ids=[n for n, _ in PROJECTIONS]
)
def test_transform_mesh__seam(global_mesh, projection):
    """Test that a shifted central meridian does not tear the mesh.

    A central meridian that cannot be recovered from the target CRS is assumed
    to be 0, which cuts the mesh at the wrong seam and leaves cells stretched
    right across the projection. See :issue:`2512`.

    """
    tgt_crs = CRS.from_user_input(projection(central_longitude=MERIDIAN))
    result = transform_mesh(global_mesh, tgt_crs)

    assert _torn_cells(result) == 0


@pytest.mark.parametrize(
    "projection", [p for _, p in PROJECTIONS], ids=[n for n, _ in PROJECTIONS]
)
def test_transform_mesh__seam_invariant(global_mesh, projection):
    """Test that shifting the central meridian does not change mesh integrity.

    A correctly seamed mesh is cut in the same place relative to its central
    meridian, so the widest cell is unchanged by the shift.

    """
    unshifted = transform_mesh(global_mesh.copy(), CRS.from_user_input(projection()))
    shifted = transform_mesh(
        global_mesh.copy(), CRS.from_user_input(projection(central_longitude=MERIDIAN))
    )

    expected = _cell_widths(unshifted).max()

    assert _cell_widths(shifted).max() == pytest.approx(expected, abs=1e-6)


@pytest.mark.xfail(
    reason="rotated pole seam is pole-relative, not a scalar meridian - see gh#2512",
    strict=True,
)
def test_transform_mesh__rotated_pole_seam(global_mesh):
    """Test the known rotated pole tearing, to record the gap rather than hide it."""
    tgt_crs = CRS.from_user_input(
        ccrs.RotatedPole(pole_longitude=MERIDIAN, pole_latitude=45)
    )
    with pytest.warns(UserWarning, match="unable to determine the central meridian"):
        result = transform_mesh(global_mesh, tgt_crs)

    assert _torn_cells(result) == 0


def test_transform_mesh__flat_source(regional_mesh):
    """Test that an already flat mesh is not preprocessed as a sphere.

    A mesh transformed to a flat geographic CRS carries lon/lat points rather
    than cartesian xyz, so it must bypass the spherical seam slicing and the
    central meridian rotation. Otherwise ``rotate_z`` spins the lon/lat values
    as if they were cartesian. See :issue:`2522`.

    """
    flat = transform_mesh(regional_mesh, ccrs.PlateCarree())
    assert projected(flat)
    assert flat.bounds[:4] == pytest.approx(REGION)

    shifted = transform_mesh(
        flat, ccrs.PlateCarree(central_longitude=REGIONAL_MERIDIAN)
    )

    xmin, xmax, ymin, ymax = REGION
    expected = (xmin - REGIONAL_MERIDIAN, xmax - REGIONAL_MERIDIAN, ymin, ymax)

    assert shifted.n_points == flat.n_points
    assert shifted.bounds[:4] == pytest.approx(expected)


@pytest.mark.parametrize("mesh", ["regional_mesh", "cloud"])
@pytest.mark.parametrize("sequence", [list, tuple, np.array])
def test_transform_mesh__zlevel_per_point(request, mesh, sequence):
    """A per-point zlevel is honoured whatever form of ArrayLike carries it.

    Typing spec §3.3: the signature promises ``ArrayLike``, but before the
    conversion at the boundary a list or tuple met ``zlevel * zscale`` with
    ``TypeError``, and an array of more than one element raised ``ValueError``.
    Each point has a level of its own, so a level that landed on the wrong
    point would show. A point's z is linear in its level, offset by any level
    a cloud encodes, so it lies on the line through its z at levels 0 and 1.

    """
    mesh = request.getfixturevalue(mesh)
    base = transform_mesh(mesh.copy(), PLANAR, zlevel=0)
    unit = transform_mesh(mesh.copy(), PLANAR, zlevel=1)
    levels = np.arange(1, mesh.n_points + 1)

    result = transform_mesh(mesh.copy(), PLANAR, zlevel=sequence(levels.tolist()))

    np.testing.assert_array_equal(result.points[:, :2], unit.points[:, :2])
    zs = base.points[:, 2] + levels * (unit.points[:, 2] - base.points[:, 2])
    np.testing.assert_allclose(result.points[:, 2], zs, rtol=1e-9)


def test_transform_mesh__zlevel_numpy_scalar(regional_mesh):
    """A numpy scalar is a scalar zlevel like any other."""
    expected = transform_mesh(regional_mesh.copy(), PLANAR, zlevel=2)

    result = transform_mesh(regional_mesh.copy(), PLANAR, zlevel=np.float64(2))

    np.testing.assert_array_equal(result.points, expected.points)


def test_transform_mesh__zlevel_left_untouched(cloud):
    """The caller's zlevel is never mutated, though a cloud adds to it."""
    zlevel = np.full(cloud.n_points, 2.0)

    _ = transform_mesh(cloud.copy(), PLANAR, zlevel=zlevel)

    np.testing.assert_array_equal(zlevel, np.full(cloud.n_points, 2.0))


def test_transform_mesh__zlevel_that_cannot_broadcast(regional_mesh):
    """A zlevel of the wrong length fails before any point is written."""
    before = regional_mesh.points.copy()
    zlevel = [2] * (regional_mesh.n_points + 1)

    with pytest.raises(ValueError, match="does not broadcast to its 9 points"):
        _ = transform_mesh(
            regional_mesh, PLANAR, zlevel=zlevel, slice_connectivity=False, inplace=True
        )

    np.testing.assert_array_equal(regional_mesh.points, before)


def test_transform_mesh__no_crs():
    """A mesh without a CRS cannot be transformed.

    ``mypy`` reported this check as unreachable while ``from_wkt`` claimed always
    to return a CRS. The annotation was wrong, not the check.

    """
    with pytest.raises(ValueError, match="no coordinate reference system"):
        _ = transform_mesh(pv.Sphere(), PLANAR)


@pytest.mark.parametrize(
    ("mesh", "shape"),
    [("regional_mesh", (9, 1)), ("lone_point", (5,)), ("lone_point", (0,))],
    ids=["column", "longer", "empty"],
)
def test_transform_mesh__zlevel_that_broadcasts_only_with_the_points(
    request, mesh, shape
):
    """A zlevel must broadcast to the points, not merely with them.

    Each of these shapes broadcasts with a column of points into something
    larger, so a check of compatibility alone passes them, and the mesh is half
    written before numpy refuses the z column.

    """
    mesh = request.getfixturevalue(mesh)
    before = mesh.points.copy()

    with pytest.raises(ValueError, match="does not broadcast to its"):
        _ = transform_mesh(
            mesh,
            PLANAR,
            zlevel=np.full(shape, 2.0),
            slice_connectivity=False,
            inplace=True,
        )

    np.testing.assert_array_equal(mesh.points, before)


def test_transform_mesh__zlevel_follows_the_slice(global_mesh):
    """A per-point zlevel follows each point through the seam slicing.

    Slicing a global mesh at the seam adds points the caller never made, so a
    zlevel sized to the caller's mesh must travel with the points. The levels
    vary with latitude, so a level that landed on the wrong point would show.

    """
    lats = from_cartesian(global_mesh)[:, 1]
    zlevel = 1 + np.abs(lats) / 90
    unit = transform_mesh(global_mesh.copy(), PLANAR, zlevel=1)

    result = transform_mesh(global_mesh.copy(), PLANAR, zlevel=zlevel)

    assert result.n_points > global_mesh.n_points
    inverse = Transformer.from_crs(PLANAR, "EPSG:4326", always_xy=True)
    _, lats = inverse.transform(result.points[:, 0], result.points[:, 1])
    expected = (1 + np.abs(lats) / 90) * unit.points[0, 2]
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)


@pytest.mark.parametrize("zlevel", [0, [1]], ids=["scalar", "per-point"])
def test_transform_mesh__zlevel_carry_spares_the_callers_array(regional_mesh, zlevel):
    """An array of the caller's named as the zlevel carry is kept, and never read.

    A per-point zlevel travels through the seam slice as point data. The array it
    travels in must not displace one of the caller's that shares its name, and
    the clean-up must remove only what the transform added.

    """
    expected = transform_mesh(regional_mesh.copy(), PLANAR, zlevel=zlevel)
    data = np.arange(regional_mesh.n_points, dtype=float)
    regional_mesh.point_data[_ZLEVEL] = data

    result = transform_mesh(regional_mesh, PLANAR, zlevel=zlevel)

    np.testing.assert_array_equal(regional_mesh.point_data[_ZLEVEL], data)
    np.testing.assert_array_equal(result.point_data[_ZLEVEL], data)
    np.testing.assert_array_equal(result.points, expected.points)
    assert [name for name in result.point_data if _ZLEVEL in name] == [_ZLEVEL]


def test_transform_mesh__integer_levels_interpolate_as_floats():
    """Integer levels cross the seam as the same levels given as floats do.

    The seam slice splits each cell that straddles it, and interpolates the level
    of each point it adds, so integer levels must not be rounded on the way.

    """
    mesh = gv.Transform.from_1d(np.linspace(-170, 190, 13), np.linspace(-60, 60, 7))
    levels = np.where(from_cartesian(mesh)[:, 0] < 0, 0, 3)
    expected = transform_mesh(mesh.copy(), PLANAR, zlevel=levels.astype(float))

    result = transform_mesh(mesh.copy(), PLANAR, zlevel=levels)

    assert result.n_points > mesh.n_points
    np.testing.assert_array_equal(result.points, expected.points)


@pytest.mark.parametrize(
    ("lons", "tgt_crs"),
    [
        ([170.0, -170.0], PLANAR),
        ([-140.0, -130.0], f"{PLANAR} +lon_0={REGIONAL_MERIDIAN}"),
    ],
    ids=["antimeridian", "shifted"],
)
def test_transform_mesh__zlevel_per_point_on_sliced_lines(lons, tgt_crs):
    """A per-point zlevel is refused on lines the seam slices, until #2583.

    ``slice_lines`` rebuilds the lines it splits without their point data, so the
    levels cannot follow the points through the seam. The refusal leaves the
    caller's mesh as it was, rotated back from the shifted seam.

    """
    mesh = pv.PolyData(to_cartesian(lons, [10.0, 10.0]), lines=[2, 0, 1])
    to_wkt(mesh, WGS84)
    before = mesh.copy(deep=True)

    with pytest.raises(ValueError, match="cannot yet follow lines sliced at the seam"):
        _ = transform_mesh(mesh, tgt_crs, zlevel=[1.0, 3.0])

    np.testing.assert_allclose(mesh.points, before.points, atol=1e-12)
    assert list(mesh.point_data) == list(before.point_data)

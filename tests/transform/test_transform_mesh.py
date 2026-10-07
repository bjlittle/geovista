# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.transform.transform_mesh`."""

from __future__ import annotations

import cartopy.crs as ccrs
import numpy as np
from pyproj import CRS
import pytest
import pyvista as pv

import geovista as gv
from geovista.crs import projected
from geovista.transform import transform_mesh

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

    """
    mesh = request.getfixturevalue(mesh)
    expected = transform_mesh(mesh.copy(), PLANAR, zlevel=2)
    zlevel = sequence([2] * mesh.n_points)

    result = transform_mesh(mesh.copy(), PLANAR, zlevel=zlevel)

    np.testing.assert_array_equal(result.points, expected.points)


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

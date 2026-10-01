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

import geovista as gv
from geovista.transform import transform_mesh

#: Fraction of the projection width above which a cell is considered torn.
TORN = 0.25

#: Central meridian shift that exercises the seam of a global mesh.
MERIDIAN: float = 180.0

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

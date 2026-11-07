# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.view_poi`."""

from __future__ import annotations

import cartopy.crs as ccrs
import numpy as np
import pint
import pytest

import geovista as gv
from geovista.geoplotter import GeoPlotter
from geovista.globe import Globe

UREG = pint.UnitRegistry()


def test_no_poi_warning():
    """Test warning raised for no POI."""
    p = GeoPlotter()
    wmsg = r"No point-of-interest \(POI\) is available or has been provided."
    with pytest.warns(UserWarning, match=wmsg):
        p.view_poi()


def test_flat_crs_camera():
    """Test that a flat scene gets a plan-view camera, not a globe camera.

    A geographic CRS other than :data:`geovista.crs.WGS84` renders a flat
    scene, so the camera must look down on the plane rather than be positioned
    on a ray from the origin - which leaves it edge-on to the mesh.
    See :issue:`2522`.

    """
    lons, lats = np.linspace(10, 30, 3), np.linspace(30, 50, 3)
    data = np.arange(4, dtype=float).reshape(2, 2)
    mesh = gv.Transform.from_1d(lons, lats, data=data)

    p = GeoPlotter(crs=ccrs.PlateCarree())
    p.add_mesh(mesh)
    p.view_poi()

    position = np.array(p.camera.position)
    focal_point = np.array(p.camera.focal_point)
    direction = focal_point - position

    assert focal_point == pytest.approx(p._poi)
    assert position[:2] == pytest.approx(focal_point[:2])
    assert direction[:2] == pytest.approx([0.0, 0.0])
    assert direction[2] < 0


def test_spherical_camera(lfric):
    """On a sphere, the camera looks at the POI from straight above it."""
    p = GeoPlotter()
    p.add_mesh(lfric)

    p.view_poi(x=30, y=10)

    position = np.array(p.camera.position)
    expected = gv.common.to_cartesian(30, 10)[0]
    np.testing.assert_allclose(position / np.linalg.norm(position), expected, atol=1e-6)
    np.testing.assert_allclose(p.camera.focal_point, (0, 0, 0))


@pytest.mark.parametrize("radius", [2.0, 6378137.0])
def test_the_poi_on_another_globe(radius):
    """Test the camera looks at the point-of-interest whatever the scene's globe."""
    mesh = gv.Transform.from_1d([0.0, 10.0, 20.0], [40.0, 50.0, 60.0])
    directions = []
    for globe in (Globe(), Globe(render_radius=radius)):
        p = GeoPlotter(globe=globe)
        p.add_mesh(mesh)
        p.view_poi()
        position = np.asarray(p.camera.position)
        directions.append(position / np.linalg.norm(position))
    np.testing.assert_allclose(directions[1], directions[0], atol=1e-6)


@pytest.mark.parametrize(
    ("x", "y", "named"),
    [
        (np.ma.masked, 52.0, "'x' is"),
        (np.nan, 52.0, "'x' is"),
        (-2.0, np.ma.masked, "'y' is"),
        (-2.0, np.nan, "'y' is"),
        (np.nan, np.ma.masked, "'x' and 'y' are"),
    ],
    ids=["x-masked", "x-nan", "y-masked", "y-nan", "both"],
)
def test_refuses_missing(lam_uk, x, y, named):
    """Test a missing point-of-interest is refused, naming it, and the camera stays.

    Holds positions spec §2 decision 4.

    """
    p = GeoPlotter()
    p.add_mesh(lam_uk)
    p.view_poi(x=-2.0, y=52.0)
    position = p.camera.position

    emsg = rf"point-of-interest is missing, as {named} masked or NaN"
    with pytest.raises(ValueError, match=emsg):
        p.view_poi(x=x, y=y)

    assert p.camera.position == position


@pytest.mark.parametrize(
    ("given", "named"),
    [
        ({"x": np.ma.masked}, "'x'"),
        ({"x": np.nan}, "'x'"),
        ({"y": np.nan}, "'y'"),
        ({"y": UREG.Quantity(np.nan, "degree")}, "'y'"),
    ],
    ids=["x-masked", "x-nan", "y-nan", "y-nan-quantity"],
)
def test_one_coordinate_given_missing(lam_uk, given, named):
    """Test a missing coordinate given alone is refused, naming it alone.

    The coordinate left out is filled with a present 0, so it is never named.
    Holds positions spec §2 decision 4.

    """
    p = GeoPlotter()
    p.add_mesh(lam_uk)

    with pytest.raises(ValueError, match=rf"as {named} is masked or NaN\."):
        p.view_poi(**given)


def test_refuses_infinite(lam_uk):
    """Test an infinite coordinate of the point-of-interest is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    p = GeoPlotter()
    p.add_mesh(lam_uk)

    with pytest.raises(ValueError, match=r"'x' cannot be infinite"):
        p.view_poi(x=np.inf, y=0.0)

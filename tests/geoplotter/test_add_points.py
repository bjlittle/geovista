# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_points`."""

from __future__ import annotations

from pyproj import CRS
from pyproj.exceptions import CRSError
import pytest

from geovista.crs import WGS84, from_wkt, has_wkt, to_wkt
from geovista.geoplotter import GeoPlotter


def test_style_fail():
    """Test trap of invalid style request."""
    p = GeoPlotter()
    emsg = "Invalid 'style' for 'add_points'"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(style="dolce and gabbana")


def test_no_points_fail():
    """Test trap of no spatial points provided."""
    p = GeoPlotter()
    emsg = "got neither"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points()


def test_duplicate_points_fail(mocker):
    """Test trap of duplicate spatial points provided."""
    p = GeoPlotter()
    points, xs, ys = mocker.sentinel.points, mocker.sentinel.xs, mocker.sentinel.ys
    emsg = "got both 'points', and 'xs' and 'ys'"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(points=points, xs=xs, ys=ys)


@pytest.mark.parametrize(("xs", "ys"), [(True, None), (None, True)])
def test_over_specified_points_fail(mocker, xs, ys):
    """Test trap of points and xs or ys provided."""
    p = GeoPlotter()
    points = mocker.sentinel.points
    emsg = "got both 'points', and 'xs' or 'ys'"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(points=points, xs=xs, ys=ys)


def test_points_mesh_crs_fail(sphere):
    """Test trap of crs mismatch with points mesh serialized crs as wkt."""
    p = GeoPlotter()
    emsg = "The CRS serialized as WKT on the 'points' mesh does not match"
    to_wkt(sphere, WGS84)
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(points=sphere, crs="+proj=eqc")


@pytest.mark.parametrize("crs", [None, CRS.from_user_input("+proj=eqc")])
def test_points_mesh_with_no_crs(mocker, sphere, crs):
    """Test points mesh with no serialized crs."""
    assert not has_wkt(sphere)
    p = GeoPlotter()
    actor = mocker.sentinel.actor
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh", return_value=actor)
    _ = p.add_points(sphere, crs=crs)
    p.add_mesh.assert_called_once_with(sphere, style="points", scalars=None)
    assert has_wkt(sphere)
    expected = WGS84 if crs is None else crs
    assert from_wkt(sphere) == expected


def test_crs_invalid_fail():
    """Test trap of crs validity sanity check."""
    p = GeoPlotter()
    emsg = "Invalid projection"
    with pytest.raises(CRSError, match=emsg):
        _ = p.add_points(crs="invalid")


def test_points_mesh_with_scalars(mocker, sphere):
    """Test points mesh with scalars pass-through."""
    p = GeoPlotter()
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh")
    scalars = mocker.sentinel.scalars
    _ = p.add_points(sphere, scalars=scalars)
    p.add_mesh.assert_called_once_with(sphere, style="points", scalars=scalars)


def test_texture_kwarg_pop(mocker, sphere):
    """Test defensive texture kwarg purge."""
    p = GeoPlotter()
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh")
    texture = mocker.sentinel.texture
    _ = p.add_points(sphere, texture=texture)
    p.add_mesh.assert_called_once_with(sphere, style="points", scalars=None)


@pytest.mark.parametrize(("xs", "ys"), [(None, True), (True, None)])
def test_xs_ys_incomplete_fail(xs, ys):
    """Test trap of missing spatial points."""
    p = GeoPlotter()
    emsg = "got only 'xs' or 'ys'"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(xs=xs, ys=ys)


def test_xs_ys(mocker):
    """Test xs/ys points."""
    p = GeoPlotter()
    mesh = mocker.sentinel.mesh
    _ = mocker.patch("geovista.Transform.from_points", return_value=mesh)
    actor = mocker.sentinel.actor
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh", return_value=actor)
    xs, ys = mocker.sentinel.xs, mocker.sentinel.ys
    crs, scalars = WGS84, mocker.sentinel.scalars
    radius, zlevel, zscale = (
        mocker.sentinel.radius,
        mocker.sentinel.zlevel,
        mocker.sentinel.zscale,
    )
    result = p.add_points(
        xs=xs,
        ys=ys,
        scalars=scalars,
        crs=crs,
        radius=radius,
        zlevel=zlevel,
        zscale=zscale,
    )
    assert result == actor
    from geovista.bridge import Transform  # noqa: PLC0415

    Transform.from_points.assert_called_once_with(
        xs, ys, crs=crs, radius=radius, zlevel=zlevel, zscale=zscale
    )
    p.add_mesh.assert_called_once_with(mesh, style="points", scalars=scalars)


def test_xy_ys_scalars_name_warnings(mocker):
    """Test xy/ys points invalid scalars array name warning is raised."""
    p = GeoPlotter()
    mesh = mocker.sentinel.mesh
    _ = mocker.patch("geovista.Transform.from_points", return_value=mesh)
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh")
    xs, ys = mocker.sentinel.xs, mocker.sentinel.ys
    scalars = "invalid"
    wmsg = (
        f"geovista ignoring the 'scalars' string name '{scalars}', "
        "as no 'points' mesh was provided"
    )
    with pytest.warns(UserWarning, match=wmsg):
        _ = p.add_points(xs=xs, ys=ys, scalars=scalars)

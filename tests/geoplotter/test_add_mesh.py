# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_mesh`."""

from __future__ import annotations

import cartopy.crs as ccrs
import numpy as np
from pyproj import Transformer
import pytest
import pyvista as pv

import geovista as gv
from geovista.common import RADIUS, ZLEVEL_SCALE, distance, from_cartesian
from geovista.crs import from_wkt
from geovista.geoplotter import OPACITY_BLACKLIST, GeoPlotter
from geovista.transform import transform_mesh


def test_no_opacity_kwarg(lfric, mocker):
    """Test with no opacity render request."""
    p = GeoPlotter()
    spy = mocker.spy(p, "_warn_opacity")
    p.add_mesh(lfric)
    assert spy.call_count == 0
    assert p._missing_opacity is False


@pytest.mark.parametrize("key", ["opacity", "nan_opacity"])
@pytest.mark.parametrize("value", [None, 0.5])
def test_gpu_opacity_available(lfric, mocker, key, value):
    """Test with a mock gpu supporting opacity."""
    renderer = mocker.sentinel.renderer
    version = mocker.sentinel.version
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    p = GeoPlotter()
    spy = mocker.spy(p, "add_text")
    kwargs = {key: value}
    p.add_mesh(lfric, **kwargs)
    assert spy.call_count == 0
    assert p._missing_opacity is False


@pytest.mark.parametrize("key", ["opacity"])
@pytest.mark.parametrize("value", [None, 0.5])
def test_gpu_opacity_unavailable(lfric, mocker, key, value):
    """Test with a mock gpu not supporting opacity."""
    renderer, version = OPACITY_BLACKLIST[0]
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    p = GeoPlotter()
    spy = mocker.spy(p, "add_text")
    kwargs = {key: value}
    p.add_mesh(lfric, **kwargs)
    if value is None:
        assert spy.call_count == 0
        assert p._missing_opacity is False
    else:
        assert spy.call_count == 1
        args = ("Requires GPU opacity support",)
        kwargs = {
            "position": "lower_right",
            "font_size": 7,
            "color": "red",
            "shadow": True,
        }
        spy.assert_called_once_with(*args, **kwargs)
        assert p._missing_opacity is True


def test_flat_mesh_zlevel():
    """Test that a flat mesh is not resized as a sphere.

    An already flat mesh added to a scene with the same flat CRS must not be
    radially rescaled by ``zlevel``, which would distort its lon/lat extent.
    See :issue:`2522`.

    """
    lons, lats = np.linspace(10, 30, 3), np.linspace(30, 50, 3)
    data = np.arange(4, dtype=float).reshape(2, 2)
    sphere = gv.Transform.from_1d(lons, lats, data=data)
    flat = transform_mesh(sphere, ccrs.PlateCarree())
    expected = flat.bounds[:4]

    p = GeoPlotter(crs=ccrs.PlateCarree())
    p.add_mesh(flat, zlevel=1)

    assert p.mesh.bounds[:4] == pytest.approx(expected)


def test_empty_mesh_returns_none():
    """An empty mesh is not added, and nothing is returned for it."""
    p = GeoPlotter()

    assert p.add_mesh(pv.PolyData()) is None
    assert not p.actors


def test_central_meridian_recentred(lfric):
    """A mesh is sliced and transformed for a CRS with a central meridian."""
    p = GeoPlotter(crs="+proj=robin +lon_0=180")

    actor = p.add_mesh(lfric)

    assert actor is not None
    assert from_wkt(actor.mapper.dataset) == p.crs


@pytest.mark.parametrize("zlevel", [[1, 2, 3], (1, 2, 3), np.array([1, 2, 3])])
def test_cloud_zlevel_per_point(zlevel):
    """A cloud that needs no transform is lifted by a z-level at each point.

    See :issue:`2618`.

    """
    zscale = 1
    cloud = gv.Transform.from_points([0, 10, 20], [0, 10, 20], zscale=zscale)
    p = GeoPlotter()

    actor = p.add_mesh(cloud, zlevel=zlevel)

    assert actor is not None
    expected = RADIUS + RADIUS * np.asarray(zlevel) * zscale
    assert np.allclose(distance(actor.mapper.dataset, mean=False), expected)


def test_cloud_zlevel_single_point():
    """A one point cloud is lifted by a one element z-level. See :issue:`2618`."""
    zscale = 1
    cloud = gv.Transform.from_points([0], [0], zscale=zscale)
    p = GeoPlotter()

    actor = p.add_mesh(cloud, zlevel=np.array([2]))

    assert actor is not None
    expected = RADIUS + RADIUS * 2 * zscale
    assert np.allclose(distance(actor.mapper.dataset, mean=False), expected)


def test_surface_zlevel_array():
    """A surface that needs no transform is lifted at each point, as when it does.

    See :issue:`2693`.

    """
    mesh = gv.Transform.from_1d([0, 10, 20], [0, 10, 20])
    level = np.arange(mesh.n_points)
    p = GeoPlotter()

    actor = p.add_mesh(mesh, zlevel=level)
    expected = RADIUS + RADIUS * level * ZLEVEL_SCALE
    assert np.allclose(distance(actor.mapper.dataset, mean=False), expected)


def test_cloud_zlevel_zeros_shape_fail():
    """A z-level of zeros that doesn't broadcast to a cloud is refused.

    The same cloud and z-level are refused when the cloud needs a transform.

    """
    cloud = gv.Transform.from_points([0, 10, 20], [0, 10, 20])
    p = GeoPlotter()

    emsg = r"'zlevel' with shape \(5,\) does not broadcast"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_mesh(cloud, zlevel=np.zeros(5))


def test_surface_zlevel_0d():
    """A mesh that is no cloud is lifted by a z-level given as a 0-d array."""
    mesh = gv.Transform.from_1d([0, 10, 20], [0, 10, 20])
    radius = distance(mesh)
    p = GeoPlotter()

    actor = p.add_mesh(mesh, zlevel=np.array(2))

    assert actor is not None
    expected = radius + radius * 2 * ZLEVEL_SCALE
    assert np.isclose(distance(actor.mapper.dataset), expected)


@pytest.mark.parametrize("lon_0", [0, 90])
def test_surface_zlevel_follows_the_slice(lon_0):
    """A surface the seam cuts is lifted by a z-level at each point.

    The levels vary with latitude, so a level that landed on the wrong point of
    those the seam adds would show. See :issue:`2669`.

    """
    mesh = gv.Transform.from_1d(np.linspace(-180, 180, 9), np.linspace(-90, 90, 5))
    zlevel = 1 + np.abs(from_cartesian(mesh)[:, 1]) / 90
    crs = f"+proj=eqc +lon_0={lon_0}"
    p = GeoPlotter(crs=crs)

    actor = p.add_mesh(mesh, zlevel=zlevel)

    result = actor.mapper.dataset
    assert result.n_points > mesh.n_points
    inverse = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    _, lats = inverse.transform(result.points[:, 0], result.points[:, 1])
    # the semi-major axis of the GRS80 ellipsoid of the CRS is 6378137 m
    expected = (1 + np.abs(lats) / 90) * ZLEVEL_SCALE * 6378137
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)

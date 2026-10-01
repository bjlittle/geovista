# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_mesh`."""

from __future__ import annotations

import cartopy.crs as ccrs
import numpy as np
import pytest

import geovista as gv
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

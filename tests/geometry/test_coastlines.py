# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-test for :func:`geovista.geometry.coastlines`."""

from __future__ import annotations

from geovista.common import COASTLINES_RESOLUTION
from geovista.geometry import coastlines


def test_defaults(mocker):
    """Test expected defaults are honoured."""
    mesh = mocker.sentinel.mesh
    _ = mocker.patch("geovista.geometry.fetch_coastlines", return_value=mesh)
    _ = mocker.patch("geovista.geometry.resize")
    result = coastlines()
    assert result == mesh
    from geovista.geometry import fetch_coastlines, resize

    fetch_coastlines.assert_called_once_with(resolution=COASTLINES_RESOLUTION)
    resize.assert_called_once_with(
        mesh, radius=None, zlevel=1, zscale=None, inplace=True
    )


def test_resize_kwarg_pass_thru(mocker):
    """Test kwargs are passed thru to :func:`geovista.core.resize`."""
    mesh = mocker.sentinel.mesh
    resolution = mocker.sentinel.resolution
    radius = mocker.sentinel.radius
    zscale = mocker.sentinel.zscale
    zlevel = mocker.sentinel.zlevel
    _ = mocker.patch("geovista.geometry.fetch_coastlines", return_value=mesh)
    _ = mocker.patch("geovista.geometry.resize")
    kwargs = {"radius": radius, "zscale": zscale, "zlevel": zlevel}
    result = coastlines(resolution=resolution, **kwargs)
    assert result == mesh
    from geovista.geometry import fetch_coastlines, resize

    fetch_coastlines.assert_called_once_with(resolution=resolution)
    resize.assert_called_once_with(mesh, **kwargs, inplace=True)


def test_fetch_exception(mocker):
    """Test coastlines are loaded on cache fetch failure."""
    mesh = mocker.sentinel.mesh
    _ = mocker.patch("geovista.geometry.fetch_coastlines", side_effect=ValueError)
    _ = mocker.patch("geovista.geometry.load_coastlines", return_value=mesh)
    _ = mocker.patch("geovista.geometry.resize")
    result = coastlines()
    assert result == mesh
    from geovista.geometry import fetch_coastlines, load_coastlines, resize

    assert fetch_coastlines.call_count == 1
    assert resize.call_count == 1
    load_coastlines.assert_called_once_with(resolution=COASTLINES_RESOLUTION)

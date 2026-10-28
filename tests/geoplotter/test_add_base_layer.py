# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_base_layer`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import distance
from geovista.geoplotter import BASE_ZLEVEL_SCALE, OPACITY_BLACKLIST, GeoPlotter
from geovista.globe import Globe


def test_no_opacity_kwarg(mocker):
    """Test with no opacity render request."""
    p = GeoPlotter()
    spy = mocker.spy(p, "_warn_opacity")
    p.add_base_layer()
    assert spy.call_count == 0
    assert p._missing_opacity is False


@pytest.mark.parametrize("key", ["opacity", "nan_opacity"])
@pytest.mark.parametrize("value", [None, 0.5])
def test_gpu_opacity_available(mocker, key, value):
    """Test with a mock gpu supporting opacity."""
    renderer = mocker.sentinel.renderer
    version = mocker.sentinel.version
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    p = GeoPlotter()
    spy = mocker.spy(p, "add_text")
    kwargs = {key: value}
    p.add_base_layer(**kwargs)
    assert spy.call_count == 0
    assert p._missing_opacity is False


@pytest.mark.parametrize("key", ["opacity"])
@pytest.mark.parametrize("value", [None, 0.5])
def test_gpu_opacity_unavailable(mocker, key, value):
    """Test with a mock gpu not supporting opacity."""
    renderer, version = OPACITY_BLACKLIST[0]
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    p = GeoPlotter()
    spy = mocker.spy(p, "add_text")
    kwargs = {key: value}
    p.add_base_layer(**kwargs)
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


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
def test_at_the_scenes_globe(radius):
    """The base layer is lowered beneath the scene's globe, and records it."""
    p = GeoPlotter(globe=Globe(render_radius=radius))
    drawn = p.add_base_layer().mapper.dataset
    np.testing.assert_allclose(
        distance(drawn, mean=False), radius * (1 - BASE_ZLEVEL_SCALE), rtol=1e-6
    )
    assert Globe.from_mesh(drawn) == p.globe
    drawn = p.add_base_layer(zlevel=0).mapper.dataset
    np.testing.assert_allclose(distance(drawn, mean=False), radius, rtol=1e-6)

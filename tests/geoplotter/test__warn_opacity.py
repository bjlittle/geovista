# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter._warn_opacity`."""
from __future__ import annotations

from geovista.geoplotter import OPACITY_BLACKLIST, GeoPlotter


def test_init_state():
    """Test GeoPlotter initial state."""
    plotter = GeoPlotter()
    assert plotter._missing_opacity is False


def test_gpu_opacity_available(mocker):
    """Test with a mock gpu supporting opacity."""
    renderer = mocker.sentinel.renderer
    version = mocker.sentinel.version
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    plotter = GeoPlotter()
    spy = mocker.spy(plotter, "add_text")
    plotter._warn_opacity()
    assert spy.call_count == 0
    assert plotter._missing_opacity is False


def test_gpu_opacity_unavailable(mocker):
    """Test with a mock gpu not supporting opacity."""
    renderer, version = OPACITY_BLACKLIST[0]
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    plotter = GeoPlotter()
    spy = mocker.spy(plotter, "add_text")
    plotter._warn_opacity()
    assert spy.call_count == 1
    args = ("Requires GPU opacity support",)
    kwargs = {"position": "lower_right", "font_size": 7, "color": "red", "shadow": True}
    spy.assert_called_once_with(*args, **kwargs)
    assert plotter._missing_opacity is True

"""Unit-tests for :func:`geovista.common.warn_opacity`."""
from __future__ import annotations

import pyvista

from geovista.common import OPACITY_BLACKLIST, warn_opacity


def test_gpu_opacity_available(mocker):
    """Test with a mock gpu supporting opacity."""
    renderer = mocker.sentinel.renderer
    version = mocker.sentinel.version
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    plotter = pyvista.Plotter()
    spy = mocker.spy(plotter, "add_text")
    warn_opacity(plotter)
    assert spy.call_count == 0


def test_gpu_opacity_unavailable(mocker):
    """Test with a mock gpu not supporting opacity."""
    renderer, version = OPACITY_BLACKLIST[0]
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    plotter = pyvista.Plotter()
    spy = mocker.spy(plotter, "add_text")
    warn_opacity(plotter)
    assert spy.call_count == 1
    args = ("Requires Opacity Support",)
    kwargs = {"position": "lower_right", "font_size": 7, "color": "red", "shadow": True}
    spy.assert_called_once_with(*args, **kwargs)

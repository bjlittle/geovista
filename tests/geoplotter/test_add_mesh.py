# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_mesh`."""

from __future__ import annotations

import pytest
import pyvista as pv

from geovista.geoplotter import OPACITY_BLACKLIST, GeoPlotter, WGS84


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


class DummyBBox:
    """Mock bbox with an enclosed() method to track calls."""

    def __init__(self) -> None:
        self.called = False
        self.called_with = None
        # what the bbox should return when filtering
        self.filtered_mesh = pv.PolyData([[1.0, 1.0, 1.0]])

    def enclosed(self, mesh):
        """Return filtered_mesh. Dummy method for testing."""
        self.called = True
        self.called_with = mesh
        return self.filtered_mesh

@pytest.mark.parametrize("bbox_factory", [None, DummyBBox])
def test_bbox_filtering(mocker, bbox_factory):
    """Test with bbox subsetting enabled and disabled."""
    bbox = bbox_factory() if callable(bbox_factory) else None

    # Patch mesh creation so add_base_layer() gets a predictable mesh
    input_mesh = pv.PolyData([[0.0, 0.0, 0.0]])
    mock_super = mocker.patch.object(pv.Plotter, "add_mesh",
                                     return_value="mocked")
    mocker.patch("geovista.geoplotter.from_wkt", return_value=WGS84)

    p = GeoPlotter(bbox=bbox)
    p.add_mesh(input_mesh)

    if bbox is None:
        # bbox subsetting should not be happening, assert add mesh uses the
        # original input mesh
        mock_super.assert_called_once()
        args, _ = mock_super.call_args
        assert args[0] is input_mesh
    else:
        # bbox subsetting should be happening, assert add mesh uses the
        # dummy enclosed mesh and that bbox has been
        assert bbox.called is True
        assert bbox.called_with is input_mesh
        mock_super.assert_called_once()
        args, _ = mock_super.call_args
        assert args[0] is bbox.filtered_mesh

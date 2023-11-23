# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :mod:`geovista.qt`."""
from __future__ import annotations

import pytest


def test_pyvistaqt_import():
    """Test the pyvistaqt package optional dependency.

    The test environment may or may not contain the "pyvistaqt" package.
    This test only checks that the expected exception is raised when it
    detects that the package is not already available in the test
    environment.

    """
    try:
        import pyvistaqt
    except ModuleNotFoundError:
        pyvistaqt = False

    if not pyvistaqt:
        emsg = 'please install the "pyvistaqt" and "pyqt" packages'
        with pytest.raises(ModuleNotFoundError, match=emsg):
            import geovista.qt  # noqa: F401


def test_pyvistaqt_mixin(mocker):
    """Test pyvistaqt class mixin to geovista geo classes."""
    slot = mocker.sentinel.slot

    class BackgroundPlotter:
        dummy = slot

    class MultiPlotter:
        dummy = slot

    module = mocker.MagicMock(
        BackgroundPlotter=BackgroundPlotter, MultiPlotter=MultiPlotter
    )
    mocker.patch.dict("sys.modules", pyvistaqt=module)
    import geovista.qt

    assert geovista.qt.GeoBackgroundPlotter().dummy == slot
    assert geovista.qt.GeoMultiPlotter().dummy == slot

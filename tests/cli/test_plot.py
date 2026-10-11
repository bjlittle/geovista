# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the ``geovista plot`` command."""

from __future__ import annotations

from click.testing import CliRunner
import pytest
import pyvista as pv

from geovista.cli import main
from geovista.crs import WGS84, to_wkt
from geovista.geoplotter import GeoPlotter


@pytest.mark.parametrize("axes", [False, True])
def test_axes(mocker, tmp_path, axes):
    """The axes are added only when asked for, through pyvista's add_axes."""
    fname = tmp_path / "sphere.vtk"
    sphere = pv.Sphere()
    to_wkt(sphere, WGS84)
    sphere.save(fname)
    _ = mocker.patch.object(GeoPlotter, "show")
    spy = mocker.spy(GeoPlotter, "add_axes")
    args = ["plot", str(fname), *(["--axes"] if axes else [])]

    result = CliRunner().invoke(main, args)

    assert result.exit_code == 0, result.output
    assert spy.call_count == int(axes)

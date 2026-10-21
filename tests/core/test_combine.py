# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.core.combine`."""

from __future__ import annotations

import pytest
import pyvista as pv

from geovista.core import combine


def test_single_mesh_fail():
    """Test trap of a single mesh that is not a :class:`~pyvista.PolyData`."""
    emsg = "Can only combine 'pyvista.PolyData' meshes, input mesh #1 has type"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(pv.ImageData(dimensions=(2, 2, 2)))


def test_mesh_fail():
    """Test trap of a mesh that is not a :class:`~pyvista.PolyData`."""
    emsg = "Can only combine 'pyvista.PolyData' meshes, input mesh #2 has type"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(pv.Sphere(), pv.ImageData(dimensions=(2, 2, 2)))


def test_single_mesh_pass_thru():
    """Test a single :class:`~pyvista.PolyData` is returned as it is."""
    mesh = pv.Sphere()
    assert combine(mesh) is mesh


@pytest.mark.parametrize(
    "meshes",
    [(pv.MultiBlock(),), (pv.MultiBlock(), pv.Sphere())],
    ids=["single", "first"],
)
def test_multiblock_fail(meshes):
    """Test trap of a :class:`~pyvista.MultiBlock`, which is not a dataset."""
    emsg = "Can only combine 'pyvista.PolyData' meshes, input mesh #1 has type"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(*meshes)

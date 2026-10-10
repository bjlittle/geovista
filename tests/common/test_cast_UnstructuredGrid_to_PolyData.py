# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.cast_UnstructuredGrid_to_PolyData`."""

from __future__ import annotations

import pytest
import pyvista as pv

from geovista.common import cast_UnstructuredGrid_to_PolyData


def test_converts():
    """An unstructured grid becomes the surface it describes."""
    sphere = pv.Sphere()

    result = cast_UnstructuredGrid_to_PolyData(sphere.cast_to_unstructured_grid())

    assert isinstance(result, pv.PolyData)
    assert (result.n_points, result.n_cells) == (sphere.n_points, sphere.n_cells)


def test_not_an_unstructured_grid():
    """Anything else is refused with a TypeError naming what was given."""
    with pytest.raises(
        TypeError, match=r"Expected a 'pyvista\.UnstructuredGrid', got 'PolyData'"
    ):
        _ = cast_UnstructuredGrid_to_PolyData(pv.Sphere())

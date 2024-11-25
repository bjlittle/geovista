# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.slice_lines`."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest
import pyvista as pv

from geovista.common import from_cartesian, to_cartesian
from geovista.core import slice_lines
from geovista.crs import WGS84, to_wkt
from geovista.geodesic import line
from geovista.pantry.meshes import lam_uk, lfric


@dataclass
class Kind:
    """Count of types of cell operations performed on line-segments for a mesh slice."""

    split: int = 0
    detach: int = 0


# TODO @bjlittle: Add further examples of geovista projected meshes, this requires
#                 "transform_mesh" API support.
@pytest.mark.parametrize("mesh", [pv.Plane()])
def test_projected_fail(mesh):
    """Test trap of a mesh that is projected."""
    emsg = "Cannot slice a mesh that has been projected"
    with pytest.raises(ValueError, match=emsg):
        _ = slice_lines(mesh)


@pytest.mark.parametrize("mesh", [pv.Cube(), lam_uk(), lfric()])
def test_no_lines(mesh):
    """Test nop slicing mesh with no lines."""
    result = slice_lines(mesh)
    assert id(result) == id(mesh)
    assert result.n_cells == mesh.n_cells
    assert result.n_lines == mesh.n_lines
    assert result.n_points == mesh.n_points


@pytest.mark.parametrize("n_points", [0, -1])
def test_n_points_warning(coastlines, n_points):
    """Test invalid domain for n_points warning is raised."""
    wmsg = f"geovista ignoring 'n_points={n_points}'"
    with pytest.warns(UserWarning, match=wmsg):
        _ = slice_lines(coastlines, n_points=n_points)


@pytest.mark.parametrize("copy", [False, True])
@pytest.mark.parametrize("mesh", [line(0, [90, 0, -90]), line([-135, -45, 45, 135], 0)])
def test_no_traversal_slice(copy, mesh):
    """Test a line mesh that does not traverse the antimeridian."""
    result = slice_lines(mesh, copy=copy)
    if copy:
        assert id(result) != id(mesh)
    else:
        assert id(result) == id(mesh)
    assert result == mesh


@pytest.mark.parametrize("copy", [False, True])
@pytest.mark.parametrize("mesh", [line(180, [90, 0, -90]), line(-180, [-90, 0, 90])])
def test_full_traversal_slice(copy, mesh):
    """Test a line mesh that completely traverses the antimeridian."""
    result = slice_lines(mesh, copy=copy)
    if copy:
        assert id(result) != id(mesh)
    else:
        assert id(result) == id(mesh)
    assert result == mesh


def antimeridian_count(mesh: pv.PolyData) -> int:
    """Count the number of points on the antimeridian of the mesh."""
    lonlat = from_cartesian(mesh)
    mask = np.isclose(np.abs(lonlat[:, 0]), 180)
    return np.sum(mask)


# TODO @bjlittle: investigate this failing test - thread safety? side-effect?
# @pytest.mark.parametrize(
#     "coastlines, kind",
#     [
#         ("110m", Kind(split=7, detach=0)),
#         ("50m", Kind(split=9, detach=2)),
#         ("10m", Kind(split=5, detach=6)),
#     ],
#     indirect=["coastlines"],
# )
# def test_slice_coastlines(coastlines, kind):
#     """Slice line meshes of increasing resolution."""
#     n_cells, n_points = coastlines.n_cells, coastlines.n_points
#     new_n_points = 0
#     if kind.split:
#         n_cells += kind.split
#         new = 2 * kind.split
#         n_points += new
#         new_n_points += new
#     if kind.detach:
#         new = kind.detach
#         n_points += new
#         new_n_points += new
#     start_antimeridian = antimeridian_count(coastlines)
#     result = slice_lines(coastlines)
#     assert id(result) != id(coastlines)
#     assert result.n_cells == n_cells
#     assert result.n_points == n_points
#     assert result != coastlines
#     end_antimeridian = antimeridian_count(result)
#     assert (end_antimeridian - start_antimeridian) == new_n_points


@pytest.mark.parametrize(
    ("lonlat", "pids", "kind"),
    [
        (np.array([[179, 0], [181, 0]]), np.array([[0, 1]]), Kind(split=1, detach=0)),
        (
            np.array([[179, 0], [180, 0], [181, 0]]),
            np.array([[0, 1], [1, 2]]),
            Kind(split=0, detach=1),
        ),
        (np.array([[179, 0], [180, 0]]), np.array([[0, 1]]), Kind(split=0, detach=0)),
        (np.array([[180, 0], [181, 0]]), np.array([[0, 1]]), Kind(split=0, detach=1)),
    ],
)
def test_slice_lines(lonlat, pids, kind):
    """Test line mesh slicing."""
    nlines = pids.shape[0]
    lines = np.full((nlines, 3), 2, dtype=int)
    lines[:, 1:] = pids
    points = to_cartesian(lonlat[:, 0], lonlat[:, 1])
    mesh = pv.PolyData()
    mesh.points = points
    mesh.lines = lines
    to_wkt(mesh, WGS84)

    n_cells, n_points = mesh.n_cells, mesh.n_points
    new_n_points = 0
    if kind.split:
        n_cells += kind.split
        new = 2 * kind.split
        n_points += new
        new_n_points += new
    if kind.detach:
        new = kind.detach
        n_points += new
        new_n_points += new

    prior = antimeridian_count(mesh)
    result = slice_lines(mesh)
    post = antimeridian_count(result)

    if new_n_points == 0:
        assert id(result) == id(mesh)
        assert prior == post
    else:
        assert id(result) != id(mesh)
        assert result.n_cells == n_cells
        assert result.n_points == n_points
        assert result != mesh
        assert (post - prior) == new_n_points


@pytest.mark.parametrize("coastlines", ["110m", "50m", "10m"], indirect=True)
def test_field_data(coastlines):
    """Test expected metadata populated within field-data."""
    metadata = dict(coastlines.field_data.items())
    result = slice_lines(coastlines)
    assert set(result.field_data.keys()) == set(metadata.keys())
    for key, value in metadata.items():
        assert id(result.field_data[key]) != id(value)
        np.testing.assert_array_equal(result.field_data[key], value)

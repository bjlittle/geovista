# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that heights survive the filters, and :func:`geovista.core.combine`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from geovista.bridge import Transform
from geovista.common import GV_POINT_HEIGHT, cast_UnstructuredGrid_to_PolyData
from geovista.core import (
    MeridianSlice,
    add_texture_coords,
    combine,
    slice_cells,
    slice_lines,
    slice_mesh,
)
from geovista.filters import remesh
from geovista.geodesic import BBox, line
from geovista.globe import _record_heights

if TYPE_CHECKING:
    from collections.abc import Callable

    import pyvista as pv


def _surface() -> pv.PolyData:
    """Return a global surface whose heights are 1000 times the z of each point.

    Every interpolation along a chord is linear in position, so each point of a
    mesh made from it carries 1000 times the z of its own position.

    """
    mesh = Transform.from_1d(
        np.arange(-180.0, 181.0, 30.0), np.arange(-90.0, 91.0, 30.0)
    )
    _record_heights(mesh, 1000.0 * mesh.points[:, 2])
    return mesh


def _line() -> pv.PolyData:
    """Return a line across the antimeridian, with heights as the surface has."""
    mesh = line([160.0, -160.0], [-10.0, 20.0])
    _record_heights(mesh, 1000.0 * mesh.points[:, 2])
    return mesh


#: Each function that returns a mesh made from one it was given, as a list.
CASES: dict[str, Callable[[], list[pv.PolyData]]] = {
    "slice_mesh": lambda: [slice_mesh(_surface())],
    "slice_lines": lambda: [slice_lines(_line())],
    "cast": lambda: [
        cast_UnstructuredGrid_to_PolyData(_surface().extract_cells(range(10)))
    ],
    "enclosed": lambda: [
        BBox([-40.0, 40.0, 40.0, -40.0], [-40.0, -40.0, 40.0, 40.0]).enclosed(
            _surface()
        )
    ],
    "add_texture_coords": lambda: [add_texture_coords(_surface(), antimeridian=True)],
    "remesh": lambda: list(remesh(_surface(), 15)),
    "MeridianSlice": lambda: [MeridianSlice(_surface(), 15).extract()],
}


@pytest.mark.parametrize("case", CASES.values(), ids=CASES.keys())
def test_carried(case):
    """Every point of a result carries its height, interpolated where it is new."""
    for mesh in case():
        assert mesh.n_points
        heights = mesh.point_data[GV_POINT_HEIGHT]
        assert heights.dtype == np.float64
        np.testing.assert_allclose(heights, 1000.0 * mesh.points[:, 2], atol=1e-9)
        assert mesh.active_scalars_name != GV_POINT_HEIGHT


def test_carried_by_slice_cells():
    """slice_cells carries the heights remesh cuts, at the points it moves.

    slice_cells pushes the points a cut adds out from the chords they lie on, so
    each is matched by its direction to the point remesh adds.

    """
    result = slice_cells(_surface(), meridian=15)
    reference, *_ = remesh(_surface(), 15)
    assert result.active_scalars_name != GV_POINT_HEIGHT

    def directions(mesh: pv.PolyData) -> np.ndarray:
        points = np.asarray(mesh.points, dtype=np.float64)
        return points / np.linalg.norm(points, axis=1)[:, np.newaxis]

    # the point of the reference in the direction of each point of the result
    nearest = np.argmax(directions(result) @ directions(reference).T, axis=1)
    np.testing.assert_allclose(
        result.point_data[GV_POINT_HEIGHT],
        reference.point_data[GV_POINT_HEIGHT][nearest],
        atol=1e-9,
    )


#: The cell bounds of two meshes over neighbouring longitudes.
WEST, EAST, LATS = [0.0, 10.0, 20.0], [20.0, 30.0], [0.0, 10.0]

#: A height for each point of the western mesh, and one missing.
WEST_HEIGHTS = np.array([1000.0, -4000.0, np.nan, 250.0, 0.0, -10.0])


@pytest.mark.parametrize("data", [True, False])
def test_combine_keeps_heights(data):
    """Combined heights follow each mesh's points, with 0 for one without them."""
    west = Transform.from_1d(WEST, LATS, height=WEST_HEIGHTS)
    east = Transform.from_1d(EAST, LATS)
    result = combine(west, east, data=data)
    np.testing.assert_array_equal(
        result[GV_POINT_HEIGHT], np.concatenate([WEST_HEIGHTS, np.zeros(4)])
    )
    assert result.active_scalars_name != GV_POINT_HEIGHT

    east = Transform.from_1d(EAST, LATS, height=[5.0, 6.0, 7.0, 8.0])
    result = combine(west, east, data=data)
    np.testing.assert_array_equal(
        result[GV_POINT_HEIGHT], np.concatenate([WEST_HEIGHTS, [5.0, 6.0, 7.0, 8.0]])
    )
    assert result.active_scalars_name != GV_POINT_HEIGHT


def test_a_cut_reads_heights_from_where_it_lies():
    """A point a cut adds takes its height from the triangle it lies in.

    vtkIntersectionPolyDataFilter interpolates some of the points it adds from
    the wrong points, so a missing height that the point does not lie by must
    not reach it.

    """
    mesh = _surface()
    heights = np.array(mesh.point_data[GV_POINT_HEIGHT])
    # a missing height at each point north of the equator, at 30 degrees east
    points = np.asarray(mesh.points)
    lons = np.degrees(np.arctan2(points[:, 1], points[:, 0]))
    lats = np.degrees(np.arcsin(points[:, 2]))
    missing = np.isclose(lons, 30.0) & (lats > 1) & (lats < 89)
    heights[missing] = np.nan
    _record_heights(mesh, heights)

    result, *_ = remesh(mesh, 15)
    added = result.point_data[GV_POINT_HEIGHT][mesh.n_points :]
    on_meridian = np.asarray(result.points[mesh.n_points :])
    expected = 1000.0 * on_meridian[:, 2]
    # a point the cut adds lies by a missing height only north of the equator,
    # so every point south of it, and on it, keeps a height
    finite = np.isfinite(added)
    np.testing.assert_allclose(added[finite], expected[finite], atol=1e-9)
    assert np.sum(finite) >= np.sum(on_meridian[:, 2] <= 0)

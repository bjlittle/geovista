# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that a mesh geovista makes from another carries only current fields.

See scene spec §2 decision 5 and scene spec §4.5.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from geovista.bridge import Transform
from geovista.common import (
    GV_FIELD_RADIUS,
    RETIRED_FIELDS,
    cast_UnstructuredGrid_to_PolyData,
)
from geovista.core import (
    add_texture_coords,
    combine,
    resize,
    slice_cells,
    slice_lines,
    slice_mesh,
)
from geovista.filters import remesh
from geovista.geodesic import BBox, line
from geovista.globe import Globe
from geovista.transform import transform_mesh

if TYPE_CHECKING:
    from collections.abc import Callable

    import pyvista as pv

#: The globe each mesh given is built on.
GLOBE = Globe(render_radius=2)


def _surface() -> pv.PolyData:
    """Build a surface across the antimeridian, on the globe."""
    return Transform.from_1d(
        np.linspace(-180, 180, 9), np.linspace(-60, 60, 5), globe=GLOBE
    )


def _lines() -> pv.PolyData:
    """Build a line across the antimeridian, on the globe."""
    return line([170, -170], [0, 0], globe=GLOBE)


#: Each function that returns a mesh it made from one it was given, the mesh it
#: is given, and how to call it.
CASES: dict[str, tuple[Callable[[], pv.DataSet], Callable[..., object]]] = {
    "resize": (_surface, lambda mesh: resize(mesh, zlevel=1)),
    "transform_mesh": (_surface, lambda mesh: transform_mesh(mesh, "+proj=eqc")),
    "combine": (_surface, combine),
    "add_texture_coords": (
        _surface,
        lambda mesh: add_texture_coords(mesh, antimeridian=True),
    ),
    "slice_cells": (_surface, slice_cells),
    "slice_lines": (_lines, slice_lines),
    "slice_mesh": (_surface, slice_mesh),
    "enclosed": (
        _surface,
        lambda mesh: BBox([-20, 20, 20, -20], [-20, -20, 20, 20]).enclosed(mesh),
    ),
    "call": (
        _surface,
        BBox([-20, 20, 20, -20], [-20, -20, 20, 20]),
    ),
    "cast": (
        _surface,
        lambda mesh: cast_UnstructuredGrid_to_PolyData(
            mesh.cast_to_unstructured_grid()
        ),
    ),
    "remesh": (_surface, lambda mesh: remesh(mesh, 0.0)),
}


def _meshes(result: object) -> list[pv.DataSet]:
    """Return each mesh a function returned."""
    return list(result) if isinstance(result, tuple) else [result]  # type: ignore[list-item]


@pytest.mark.parametrize("case", CASES.values(), ids=CASES.keys())
def test_only_current_fields(legacy, case):
    """Test no mesh returned carries a retired field, and the mesh given is kept."""
    build, call = case
    given = legacy(build())
    for mesh in _meshes(call(given)):
        for entry in RETIRED_FIELDS:
            assert entry.name not in getattr(mesh, f"{entry.association}_data")
        assert Globe.from_mesh(mesh) == GLOBE
    assert GV_FIELD_RADIUS in given.field_data


def test_a_cloud_is_returned_current(legacy):
    """Test a cloud, which gets no texture coordinates, comes back current."""
    given = legacy(Transform.from_points([0.0, 10.0], [0.0, 10.0], globe=GLOBE))
    result = add_texture_coords(given)
    assert result is not given
    assert GV_FIELD_RADIUS not in result.field_data
    assert Globe.from_mesh(result) == GLOBE
    assert GV_FIELD_RADIUS in given.field_data


def test_a_current_mesh_is_returned_as_is():
    """Test a mesh with no retired field is not copied only to clean it."""
    cloud = Transform.from_points([0.0, 10.0], [0.0, 10.0], globe=GLOBE)
    assert add_texture_coords(cloud) is cloud

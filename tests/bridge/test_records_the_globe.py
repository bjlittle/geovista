# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that every :mod:`geovista.bridge` builder records its globe."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from geovista.bridge import Transform
from geovista.common import GV_FIELD_RADIUS, ZLEVEL_SCALE, distance
from geovista.crs import WGS84, from_wkt
from geovista.globe import Globe
from geovista.pantry.meshes import regular_grid

if TYPE_CHECKING:
    from collections.abc import Callable

    import pyvista as pv

#: The longitudes and latitudes of a small regular grid.
LONS, LATS = [0.0, 10.0, 20.0], [0.0, 10.0]

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]

#: Each builder of the bridge, on small fixed coordinates.
BUILDERS: dict[str, Callable[..., pv.DataSet]] = {
    "from_1d": lambda **kwargs: Transform.from_1d(LONS, LATS, **kwargs),
    "from_2d": lambda **kwargs: Transform.from_2d(
        [[0.0, 10.0], [0.0, 10.0]], [[0.0, 0.0], [10.0, 10.0]], **kwargs
    ),
    "from_points": lambda **kwargs: Transform.from_points(
        [0.0, 10.0], [0.0, 10.0], **kwargs
    ),
    "from_unstructured": lambda **kwargs: Transform.from_unstructured(
        [0.0, 10.0, 10.0, 0.0],
        [0.0, 0.0, 10.0, 10.0],
        connectivity=[[0, 1, 2, 3]],
        **kwargs,
    ),
    "to_structured_grid": lambda **kwargs: Transform.to_structured_grid(
        [0.0, 10.0], [0.0, 10.0], [0.0, 1.0], **kwargs
    ),
    "call": lambda **kwargs: Transform(LONS, LATS, **kwargs)(data=np.arange(2)),
    "regular_grid": lambda **kwargs: regular_grid(resolution="r10", **kwargs),
}

#: The default globe, one at the Earth's radius, and one with every value set.
GLOBES = [
    None,
    Globe(render_radius=6378137.0),
    Globe(render_radius=2, exaggeration=20, exaggeration_below=100),
]


@pytest.mark.parametrize("globe", GLOBES, ids=["default", "earth", "set"])
@pytest.mark.parametrize("build", BUILDERS.values(), ids=BUILDERS.keys())
def test_records_the_globe(build: Callable[..., pv.DataSet], globe: Globe | None):
    """Test a builder records the globe it used, and no gvRadius."""
    expected = Globe() if globe is None else globe
    mesh = build() if globe is None else build(globe=globe)
    assert Globe.from_mesh(mesh) == expected
    assert GV_FIELD_RADIUS not in mesh.field_data
    radii = distance(mesh, mean=False)
    np.testing.assert_allclose(np.min(radii), expected.render_radius, rtol=1e-6)


@pytest.mark.parametrize("radius", RADII)
def test_a_lifted_mesh_records_its_globe(radius: float):
    """Test a mesh lifted by a z-level records its globe, not its lifted radius."""
    globe = Globe(render_radius=radius)
    surface = BUILDERS["from_unstructured"](globe=globe, zlevel=2)
    assert Globe.from_mesh(surface) == globe
    np.testing.assert_allclose(
        distance(surface, mean=False), radius * (1 + 2 * ZLEVEL_SCALE), rtol=1e-12
    )
    cloud = Transform.from_points(
        [0.0, 10.0, 20.0], [0.0, 10.0, 20.0], globe=globe, zlevel=[1, 2, 3]
    )
    assert Globe.from_mesh(cloud) == globe
    np.testing.assert_allclose(
        distance(cloud, mean=False),
        radius * (1 + np.array([1, 2, 3]) * ZLEVEL_SCALE),
        rtol=1e-12,
    )


def test_a_call_records_the_crs_and_globe():
    """Test the mesh a transform call builds carries the CRS and globe."""
    globe = Globe(render_radius=2)
    mesh = BUILDERS["call"](globe=globe)
    assert from_wkt(mesh) == WGS84
    assert Globe.from_mesh(mesh) == globe


@pytest.mark.parametrize("build", BUILDERS.values(), ids=BUILDERS.keys())
def test_radius_is_gone(build: Callable[..., pv.DataSet]):
    """Test the radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        build(radius=1.0)


def test_a_number_is_not_a_globe():
    """Test a number given as the globe is refused."""
    with pytest.raises(TypeError, match=r"geovista\.Globe"):
        Transform.from_1d(LONS, LATS, globe=2.0)

# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.pantry.meshes.regular_grid`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import GV_FIELD_RADIUS, distance
from geovista.globe import Globe
from geovista.pantry.meshes import regular_grid


def test_the_default_globe():
    """Test the grid records the default globe."""
    mesh = regular_grid(resolution="r10")
    assert Globe.from_mesh(mesh) == Globe()
    assert GV_FIELD_RADIUS not in mesh.field_data


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
def test_a_given_globe(radius):
    """Test the grid lies at, and records, the globe it is given."""
    globe = Globe(render_radius=radius)
    mesh = regular_grid(resolution="r10", globe=globe)
    assert Globe.from_mesh(mesh) == globe
    np.testing.assert_allclose(distance(mesh, mean=False), radius, rtol=1e-12)


def test_radius_is_gone():
    """Test the radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        regular_grid(resolution="r10", radius=2.0)

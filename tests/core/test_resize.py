"""Unit-tests for :func:`geovista.core.resize`."""
import operator

import numpy as np
from numpy.testing import assert_array_equal
import pytest
import pyvista as pv

from geovista.common import RADIUS
from geovista.core import calculate_radius, resize


def test_projection_fail():
    """Test trap of mesh that is not spherical."""
    mesh = pv.Plane()
    emsg = "appears to be a planar projection"
    with pytest.raises(ValueError, match=emsg):
        _ = resize(mesh)


@pytest.mark.parametrize("lfric", ["c48", "c96", "c192"], indirect=True)
def test_no_resize(lfric):
    """Test resize not performed due to no radius difference."""
    result = resize(lfric)
    assert id(result) == id(lfric)
    assert_array_equal(result.points, lfric.points)


@pytest.mark.parametrize("inplace", [False, True])
@pytest.mark.parametrize(
    "radius",
    (np.round(value, decimals=1) for value in np.linspace(RADIUS / 10, 2 * RADIUS, 20)),
)
def test_resize(lfric, radius, inplace):
    """Test resize mesh by new radius."""
    result = resize(lfric, radius=radius, inplace=inplace)
    compare = operator.eq if inplace or np.isclose(radius, RADIUS) else operator.ne
    assert compare(id(result), id(lfric))
    assert np.isclose(calculate_radius(result), radius)

"""Unit-tests for :func:`geovista.core.resize`."""
import operator

import numpy as np
from numpy.testing import assert_array_equal
import pytest
import pyvista as pv

from geovista.common import RADIUS, ZLEVEL_FACTOR
from geovista.core import distance, resize


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
    assert np.isclose(distance(result), radius)


@pytest.mark.parametrize("zlevel", range(-10, 11))
def test_resize__zlevel(lfric, zlevel):
    """Test resize mesh by new zlevel."""
    result = resize(lfric, zlevel=zlevel)
    expected = RADIUS + RADIUS * zlevel * ZLEVEL_FACTOR
    compare = operator.eq if np.isclose(expected, RADIUS) else operator.ne
    assert compare(id(result), id(lfric))
    actual = distance(result)
    assert np.isclose(actual, expected)


@pytest.mark.parametrize("zfactor", np.linspace(-1, 1))
def test_resize__zfactor(lfric, zfactor):
    """Test resize mesh by new zfactor."""
    result = resize(lfric, zlevel=1, zfactor=zfactor)
    expected = RADIUS + RADIUS * zfactor or RADIUS
    compare = operator.eq if np.isclose(expected, RADIUS) else operator.ne
    assert compare(id(result), id(lfric))
    actual = distance(result)
    assert np.isclose(actual, expected)

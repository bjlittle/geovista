"""Unit-tests for :func:`geovista.common.distance`."""
import numpy as np
import pytest

from geovista.common import GV_FIELD_RADIUS, RADIUS, distance


@pytest.mark.parametrize("origin", [np.empty((2, 2)), range(4)])
def test_origin_fail(lfric, origin):
    """Test trap of invalid origin."""
    emsg = "Require a single 1-D XYZ point"
    with pytest.raises(ValueError, match=emsg):
        _ = distance(lfric, origin=origin)


@pytest.mark.parametrize("scale", range(1, 11))
def test_distance(lfric, scale):
    """Test distance calculation of mesh."""
    mesh = lfric.scale(scale)
    result = distance(mesh)
    assert result == scale
    np.testing.assert_array_equal(mesh.field_data[GV_FIELD_RADIUS], scale)


@pytest.mark.parametrize(
    "origin", [np.random.randint(0, high=10, size=3).astype(float) for _ in range(10)]
)
def test_distance__origin(lfric, origin):
    """Test distance with mesh translated to random origin."""
    mesh = lfric.translate(origin)
    np.testing.assert_array_equal(mesh.center, origin)
    result = distance(mesh, origin=origin)
    assert np.isclose(result, RADIUS)

"""Unit-tests for :func:`geovista.common.to_lonlats`."""
import numpy as np
import pytest

from geovista.common import to_lonlats


@pytest.mark.parametrize(
    "points,emsg",
    [
        ([[[0]]], r"Require a 2D array .* got a 3D array"),
        ([[0, 1]], r"Require a 2D array .* got a 2D array with shape \(1, 2\)"),
    ],
)
def test_shape_fail(points, emsg):
    with pytest.raises(ValueError, match=emsg):
        _ = to_lonlats(points)


@pytest.mark.parametrize("stacked", [True, False])
def test_to_degrees(manydegrees, stacked):
    lonlats = to_lonlats(manydegrees.xyz, stacked=stacked)
    expected = manydegrees.expected if stacked else np.array(manydegrees.expected).T
    np.testing.assert_array_almost_equal(lonlats, expected)


@pytest.mark.parametrize("stacked", [True, False])
def test_to_radians(manyradians, stacked):
    lonlats = to_lonlats(manyradians.xyz, radians=True, stacked=stacked)
    expected = manyradians.expected if stacked else np.array(manyradians.expected).T
    np.testing.assert_array_almost_equal(lonlats, expected)


@pytest.mark.parametrize("radius", np.linspace(1.0, 0.99999))
def test_latitude_pole_arcsin_domain(radius):
    poles = [(0.0, 0.0, 1.0), (0.0, 0.0, -1.0)]
    expected = [90.0, -90.0]
    lonlat = to_lonlats(poles, radius=float(radius), stacked=False)
    np.testing.assert_array_almost_equal(lonlat[1], expected)

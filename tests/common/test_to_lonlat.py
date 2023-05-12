"""Unit-tests for :func:`geovista.common.to_lonlat`."""
import numpy as np
import pytest

from geovista.common import to_lonlat


@pytest.mark.parametrize(
    "point,emsg",
    [
        (0, r"Require a 1D array .* got a 0D array"),
        ([0], r"Require a 1D array .* got a 1D array with shape \(1,\)"),
        ([0, 1], r"Require a 1D array .* got a 1D array with shape \(2,\)"),
    ],
)
def test_shape_fail(point, emsg):
    with pytest.raises(ValueError, match=emsg):
        _ = to_lonlat(point)


def test_to_degrees(degrees):
    lonlat = to_lonlat(degrees.xyz)
    np.testing.assert_array_almost_equal(lonlat, degrees.expected)


def test_to_radians(radians):
    lonlat = to_lonlat(radians.xyz, radians=True)
    np.testing.assert_array_almost_equal(lonlat, radians.expected)

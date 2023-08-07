"""Unit-tests for :func:`geovista.transform.transform_points`."""
from __future__ import annotations

import numpy as np
import pytest

from geovista.crs import WGS84
from geovista.transform import transform_points


@pytest.mark.parametrize(
    "xbad, ybad",
    [
        (True, False),
        (False, True),
        (True, True),
    ],
)
def test_xy_dimension_fail(xbad, ybad):
    """Test trap of non-compliant xs and/or ys dimensionality."""
    xs = np.arange(size := 24)
    ys = np.arange(size)
    if xbad:
        xs = xs.reshape((2, 3, 4))
    if ybad:
        ys = ys.reshape((2, 3, 4))
    bad = xbad or ybad
    if bad:
        emsg = "Cannot transform points, 'xs' and 'ys' must be 1-D or 2-D only"
        with pytest.raises(ValueError, match=emsg):
            _ = transform_points(src_crs=WGS84, tgt_crs=WGS84, xs=xs, ys=ys)

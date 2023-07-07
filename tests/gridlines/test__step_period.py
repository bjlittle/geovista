"""Unit-tests for :func:`geovista.gridlines._step_period`."""
from __future__ import annotations

import numpy as np
import pytest

from geovista.gridlines import LATITUDE_STEP_PERIOD, LONGITUDE_STEP_PERIOD
from geovista.gridlines import _step_period as step_period


def expected(value: float, period: float) -> tuple[float, float]:
    """Calculate expected value within period."""
    count = abs(value) // period
    if value >= 0:
        result = value - (count * period)
    else:
        result = value + (count * period)

    return result


@pytest.mark.parametrize(
    "lon, lat",
    [
        [0, 0],
        [LONGITUDE_STEP_PERIOD // 2, LATITUDE_STEP_PERIOD // 2],
        [LONGITUDE_STEP_PERIOD, LATITUDE_STEP_PERIOD],
        [LONGITUDE_STEP_PERIOD * 1.5, LATITUDE_STEP_PERIOD * 1.5],
        [-LONGITUDE_STEP_PERIOD // 2, -LATITUDE_STEP_PERIOD // 2],
        [-LONGITUDE_STEP_PERIOD, -LATITUDE_STEP_PERIOD],
        [-LONGITUDE_STEP_PERIOD * 1.5, -LATITUDE_STEP_PERIOD * 1.5],
    ],
)
def test(lon, lat):
    """Test enforced sane upper bounds on graticule lon/lat step size."""
    alon, alat = step_period(lon, lat)
    elon = expected(lon, LONGITUDE_STEP_PERIOD)
    elat = expected(lat, LATITUDE_STEP_PERIOD)
    assert alon < LONGITUDE_STEP_PERIOD
    assert np.isclose(alon, elon)
    assert alat < LATITUDE_STEP_PERIOD
    assert np.isclose(alat, elat)

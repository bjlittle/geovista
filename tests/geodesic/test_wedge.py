# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the width of :func:`geovista.geodesic.wedge`."""

from __future__ import annotations

import re

import numpy as np
import pint
import pytest

from geovista.geodesic import BBox, wedge

#: A registry of its own, as a caller's would be.
UREG = pint.UnitRegistry()

#: The refusal of a width outside the open interval, formatted with the width.
WIDTH = r"in the open interval \(0, 180\), got '{}'\."


@pytest.mark.parametrize(
    ("lon1", "lon2", "width"),
    [
        (10, 10, "0"),
        (10.0, 10.0, "0.0"),
        (UREG.Quantity(10, "degree"), UREG.Quantity(10, "degree"), "0.0"),
        (UREG.Quantity(0.0, "radian"), UREG.Quantity(0.0, "radian"), "0.0"),
    ],
    ids=["ints", "floats", "degrees", "radians"],
)
def test_refuses_no_width(lon1, lon2, width):
    """Test a wedge of no width is refused, as the message of its check says."""
    with pytest.raises(ValueError, match=WIDTH.format(re.escape(width))):
        wedge(lon1, lon2)


@pytest.mark.parametrize(
    ("lon1", "lon2", "width"),
    [(0, 180, "180"), (90, -90, "180"), (0, 360, "360"), (170, -170, "340")],
    ids=["half", "reversed", "whole", "antimeridian"],
)
def test_refuses_half_a_turn_or_more(lon1, lon2, width):
    """Test a wedge 180 degrees or more wide is refused, as before.

    The width is the plain difference of the longitudes, so a wedge given as 170
    and -170 is 340 degrees wide, though it would cross the antimeridian.

    """
    with pytest.raises(ValueError, match=WIDTH.format(re.escape(width))):
        wedge(lon1, lon2)


@pytest.mark.parametrize(
    ("lon1", "lon2"),
    [(10, 10.001), (0, 179.999), (30, -30), (170, 190)],
    ids=["thin", "wide", "reversed", "antimeridian"],
)
def test_builds_inside_the_interval(lon1, lon2):
    """Test a wedge of any width inside the open interval builds, as before.

    A wedge across the antimeridian builds when its longitudes are given as 170
    and 190.

    """
    result = wedge(lon1, lon2)
    assert isinstance(result, BBox)
    assert result.mesh.n_points > 0


def test_refuses_a_missing_longitude_first():
    """Test a missing longitude is refused as missing, before the width is read.

    Its hidden value equals the other longitude, so the width would read 0.

    """
    emsg = re.escape(
        "A geodesic wedge needs both longitudes, but 'lon1' is masked or NaN."
    )
    with pytest.raises(ValueError, match=emsg):
        wedge(np.ma.masked_array(10.0, mask=True), 10.0)

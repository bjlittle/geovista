# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.samples.fvcom_tamar`."""
from __future__ import annotations

import operator

import numpy as np
import pytest

from geovista.common import RADIUS, Preference, distance
from geovista.samples import fvcom_tamar

PREFERENCES: tuple[str, str] = ("cell", "point")


@pytest.mark.parametrize("preference", ["face", "vertex"])
def test_preference_fail(preference):
    """Test trap of invalid preference."""
    expected = " or ".join([f"{item!r}" for item in PREFERENCES])
    emsg = f"Expected a preference of {expected}"
    with pytest.raises(ValueError, match=emsg):
        _ = fvcom_tamar(preference=preference)


@pytest.mark.parametrize(
    "preference",
    PREFERENCES + tuple([Preference(preference) for preference in PREFERENCES]),
)
def test_preference(preference):
    """Test mesh geometry preference."""
    result = fvcom_tamar(preference=preference)
    scalars = result.active_scalars_name
    assert (
        scalars in result.cell_data
        if Preference(preference) == Preference("cell")
        else result.point_data
    )


def test_defaults():
    """Test expected defaults are honoured."""
    result = fvcom_tamar()
    assert np.isclose(distance(result), RADIUS)
    scalars = result.active_scalars_name
    assert scalars in result.cell_data
    assert scalars not in result.point_data


@pytest.mark.parametrize("warp", [False, True])
def test_warp(warp):
    """Test warping mesh by point values."""
    result = fvcom_tamar(warp=warp)
    radius = distance(result)
    op = operator.ne if warp else operator.eq
    assert op(radius, RADIUS)


@pytest.mark.parametrize("factor", [1e-3, 1e3])
def test_warp_factor(factor):
    """Test scale of mesh warping by point values."""
    result = fvcom_tamar(warp=True, factor=factor)
    radius = distance(result)
    op = operator.gt if factor > 1 else operator.lt
    assert op(radius, RADIUS)

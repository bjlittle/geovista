# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests of missing positions given to the cartesian conversions.

A position is missing when its longitude or latitude is masked or NaN
(positions spec §2 decision 1), and a conversion carries it through as NaN in
every component (positions spec §2 decision 8).

"""

from __future__ import annotations

import numpy as np
import pint
import pytest

from geovista.common import to_cartesian, vectors_to_cartesian

#: A registry of its own, as a caller's would be.
UREG = pint.UnitRegistry()

#: The longitudes and latitudes of three positions.
LONS = np.array([0.0, 10.0, 20.0])
LATS = np.array([0.0, 10.0, 20.0])

#: The eastward, northward and upward components of a vector at each position.
VECTORS = ([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0])

#: The positions present when the second is missing.
PRESENT = [0, 2]

#: Each cartesian conversion, of the vectors at the positions `keep` too.
CONVERT = pytest.mark.parametrize(
    "convert",
    [
        lambda lons, lats, _keep=slice(None): to_cartesian(lons, lats),
        lambda lons, lats, keep=slice(None): np.column_stack(
            vectors_to_cartesian(
                lons, lats, tuple(np.asarray(c)[keep] for c in VECTORS)
            )
        ),
    ],
    ids=["to_cartesian", "vectors_to_cartesian"],
)


def masked(values, *indices: int):
    """Return `values` as a masked array, masked at each of `indices`."""
    result = np.ma.masked_array(values, dtype=float)
    for index in indices:
        result[index] = np.ma.masked
    return result


def nan(values, *indices: int):
    """Return `values` as an array, with NaN at each of `indices`."""
    result = np.array(values, dtype=float)
    for index in indices:
        result[index] = np.nan
    return result


@CONVERT
@pytest.mark.parametrize(
    ("lons", "lats"),
    [
        (masked(LONS, 1), LATS),
        (LONS, masked(LATS, 1)),
        (masked(LONS, 1), masked(LATS, 1)),
        (nan(LONS, 1), LATS),
        (LONS, nan(LATS, 1)),
        ([0.0, None, 20.0], LATS),
        (UREG.Quantity(masked(LONS, 1), "degree"), UREG.Quantity(LATS, "degree")),
    ],
    ids=[
        "lon-masked",
        "lat-masked",
        "both-masked",
        "lon-nan",
        "lat-nan",
        "lon-none",
        "quantity",
    ],
)
def test_gives_nan_for_a_missing_position(convert, lons, lats):
    """Test a missing position gives NaN in every component, the others as alone.

    Holds positions spec §2 decision 1 and positions spec §2 decision 8.

    """
    result = convert(lons, lats)
    assert np.all(np.isnan(result[1]))
    expected = convert(LONS[PRESENT], LATS[PRESENT], PRESENT)
    np.testing.assert_allclose(result[PRESENT], expected)


@CONVERT
def test_gives_nan_for_every_missing_position(convert):
    """Test positions that are all missing give NaN alone."""
    result = convert(np.full(3, np.nan), LATS)
    assert np.all(np.isnan(result))


@CONVERT
def test_reads_nomask_as_present(convert):
    """Test a masked array whose mask is nomask has no missing position."""
    result = convert(np.ma.masked_array(LONS), LATS)
    assert not np.any(np.isnan(result))


@CONVERT
@pytest.mark.parametrize("name", ["lons", "lats"])
def test_refuses_infinite(convert, name):
    """Test an infinite coordinate is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    coordinates = {"lons": LONS.copy(), "lats": LATS.copy()}
    coordinates[name][1] = np.inf
    emsg = rf"'{name}' cannot be infinite, got inf at index 1\."
    with pytest.raises(ValueError, match=emsg):
        convert(coordinates["lons"], coordinates["lats"])


@CONVERT
def test_leaves_the_arrays_given_alone(convert):
    """Test the latitudes given keep their values, whatever the longitudes."""
    lats = LATS.copy()
    convert(nan(LONS, 1), lats)
    np.testing.assert_array_equal(lats, LATS)


def test_refuses_shapes_that_do_not_pair_as_before():
    """Test coordinates of different shapes are refused as they were."""
    emsg = "Require longitudes and latitudes with same shape"
    with pytest.raises(ValueError, match=emsg):
        to_cartesian(masked(np.arange(10.0), 1), np.arange(10.0).reshape(5, 2))
    emsg = "'lons' and 'lats' do not have same shape"
    with pytest.raises(ValueError, match=emsg):
        vectors_to_cartesian(masked(LONS, 1), LATS[:2], VECTORS)


@pytest.mark.parametrize(
    ("lons", "lats"),
    [(np.nan, [30.0]), ([np.nan], 30.0), (np.ma.masked, [30.0]), (None, [30.0])],
    ids=["nan-number", "nan-array", "masked-number", "none-number"],
)
def test_to_cartesian_pairs_a_number_with_an_array_of_one(lons, lats):
    """Test a missing number beside an array of one gives NaN in every component.

    Holds positions spec §2 decision 8.

    """
    result = to_cartesian(lons, lats)
    assert result.shape == (1, 3)
    assert np.all(np.isnan(result))

# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests of missing positions given to the shapes of :mod:`geovista.geodesic`.

A position is missing when its longitude or latitude is masked or NaN
(positions spec §2 decision 1). A shape refuses one, and the points along a
geodesic carry it through as NaN (positions spec §2 decision 8).

"""

from __future__ import annotations

from typing import NoReturn
import warnings

import numpy as np
import pint
import pytest

from geovista import common, geodesic
from geovista.geodesic import BBox, line, npoints, npoints_by_idx, wedge

UREG = pint.UnitRegistry()

#: The positions of a geodesic line, one of which is made missing.
LONS = [0.0, 10.0, 20.0]
LATS = [0.0, 5.0, 10.0]

#: The corners of a bounding-box, one of which is made missing.
XS = [0.0, 10.0, 10.0, 0.0]
YS = [0.0, 0.0, 10.0, 10.0]


def masked(values, index):
    """Return `values` as a masked array, masked at `index`."""
    mask = np.zeros(len(values), dtype=bool)
    mask[index] = True
    return np.ma.masked_array(values, mask=mask)


def nan(values, index):
    """Return `values` as an array, with NaN at `index`."""
    result = np.array(values)
    result[index] = np.nan
    return result


@pytest.mark.parametrize(
    ("lons", "lats", "named"),
    [
        (masked(LONS, 1), LATS, "'lons' is"),
        (LONS, masked(LATS, 1), "'lats' is"),
        (nan(LONS, 1), LATS, "'lons' is"),
        (LONS, nan(LATS, 1), "'lats' is"),
        (masked(LONS, 1), nan(LATS, 1), "'lons' and 'lats' are"),
        (masked(LONS, 2), LATS, "'lons' is"),
    ],
    ids=["lon-masked", "lat-masked", "lon-nan", "lat-nan", "both", "lon-masked-last"],
)
def test_line_refuses(lons, lats, named):
    """Test a geodesic line with a missing position is refused, counting it.

    Holds positions spec §2 decision 5.

    """
    emsg = (
        r"A geodesic line needs every position given, but 1 of 3 is missing, "
        rf"as {named} masked or NaN\."
    )
    with pytest.raises(ValueError, match=emsg):
        line(lons, lats)


def test_line_refuses_before_any_geodesic(monkeypatch):
    """Test a geodesic line is refused before any of its geodesics is computed.

    Holds positions spec §2 decision 5.

    """

    def computed(*args: object, **kwargs: object) -> NoReturn:  # noqa: ARG001
        emsg = "a geodesic was computed for a missing position"
        raise AssertionError(emsg)

    monkeypatch.setattr("geovista.geodesic.npoints_by_idx", computed)
    with pytest.raises(ValueError, match=r"as 'lons' is masked or NaN"):
        line(nan(LONS, 1), LATS)


def test_line_refuses_a_repeated_missing_coordinate():
    """Test one missing longitude, repeated for every latitude, counts each position.

    Holds positions spec §2 decision 5.

    """
    emsg = r"but 3 of 3 are missing, as 'lons' is masked or NaN\."
    with pytest.raises(ValueError, match=emsg):
        line(np.ma.masked_array([10.0], mask=True), LATS)


def test_line_counts_before_refusing():
    """Test positions of differing counts are refused as such, a missing one or no."""
    emsg = r"Require the same number of longitudes \(3\) and latitudes \(2\)\."
    with pytest.raises(ValueError, match=emsg):
        line(masked(LONS, 1), [0.0, 5.0])


def test_line_refuses_a_masked_quantity():
    """Test a quantity of a masked array is refused as the masked array is.

    Holds positions spec §2 decision 5.

    """
    lons = UREG.Quantity(masked(LONS, 1), "degree")
    lats = UREG.Quantity(np.array(LATS), "degree")
    with pytest.raises(ValueError, match=r"as 'lons' is masked or NaN"):
        line(lons, lats)


@pytest.mark.parametrize("name", ["lons", "lats"])
def test_line_refuses_infinite(name):
    """Test an infinite coordinate of a geodesic line is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    coordinates = {"lons": list(LONS), "lats": list(LATS)}
    coordinates[name][1] = np.inf
    emsg = rf"'{name}' cannot be infinite, got inf at index 1\."
    with pytest.raises(ValueError, match=emsg):
        line(coordinates["lons"], coordinates["lats"])


def test_line_names_shapes_that_do_not_pair():
    """Test that coordinates of one size but different shapes are refused, named."""
    emsg = r"Cannot pair 'lons' of shape \(2, 2\) with 'lats' of shape \(4,\)\."
    with pytest.raises(ValueError, match=emsg):
        line(np.array([[0.0, 10.0], [20.0, 30.0]]), [0.0, 5.0, 10.0, 15.0])


@pytest.mark.parametrize(
    ("xs", "ys", "named"),
    [
        (masked(XS, 2), YS, "'xs' is"),
        (XS, masked(YS, 2), "'ys' is"),
        (nan(XS, 2), YS, "'xs' is"),
        (XS, nan(YS, 2), "'ys' is"),
        (masked(XS, 2), nan(YS, 2), "'xs' and 'ys' are"),
    ],
    ids=["xs-masked", "ys-masked", "xs-nan", "ys-nan", "both"],
)
def test_bbox_refuses(xs, ys, named):
    """Test a bounding-box with a missing corner is refused, counting it.

    Holds positions spec §2 decision 5.

    """
    emsg = (
        r"A bounding-box needs every position given, but 1 of 4 is missing, "
        rf"as {named} masked or NaN\."
    )
    with pytest.raises(ValueError, match=emsg):
        BBox(xs, ys)


def test_bbox_refuses_a_missing_closing_corner():
    """Test a closed bounding-box whose last corner is missing is refused.

    Holds positions spec §2 decision 5.

    """
    with pytest.raises(ValueError, match=r"but 1 of 5 is missing, as 'xs' is"):
        BBox(masked([*XS, 0.0], 4), [*YS, 0.0])


def test_bbox_refuses_on_a_map():
    """Test a bounding-box in a projected CRS is refused before it is transformed.

    Holds positions spec §2 decision 5.

    """
    with pytest.raises(ValueError, match=r"as 'ys' is masked or NaN"):
        BBox([0.0, 1e6, 1e6, 0.0], [0.0, 0.0, np.nan, 1e6], crs="+proj=eqc")


def test_bbox_refuses_a_masked_quantity():
    """Test a quantity of a masked array is refused as the masked array is.

    Holds positions spec §2 decision 5.

    """
    xs = UREG.Quantity(np.array(XS), "degree")
    ys = UREG.Quantity(masked(YS, 2), "degree")
    with pytest.raises(ValueError, match=r"as 'ys' is masked or NaN"):
        BBox(xs, ys)


@pytest.mark.parametrize("name", ["xs", "ys"])
def test_bbox_refuses_infinite(name):
    """Test an infinite coordinate of a bounding-box is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    coordinates = {"xs": list(XS), "ys": list(YS)}
    coordinates[name][2] = np.inf
    emsg = rf"'{name}' cannot be infinite, got inf at index 2\."
    with pytest.raises(ValueError, match=emsg):
        BBox(coordinates["xs"], coordinates["ys"])


def test_bbox_pairs_a_grid_of_corners():
    """Test that corners given as a grid pair in order, as they are counted."""
    grid = BBox(np.array([[0.0, 10.0], [10.0, 0.0]]), YS)
    np.testing.assert_allclose(grid.mesh.points, BBox(XS, YS).mesh.points)


@pytest.mark.parametrize(
    ("lon1", "lon2", "named"),
    [
        (np.ma.masked, 30.0, "'lon1' is"),
        (np.nan, 30.0, "'lon1' is"),
        (0.0, np.ma.masked, "'lon2' is"),
        (0.0, np.nan, "'lon2' is"),
        (np.nan, np.ma.masked, "'lon1' and 'lon2' are"),
    ],
    ids=["lon1-masked", "lon1-nan", "lon2-masked", "lon2-nan", "both"],
)
def test_wedge_refuses(lon1, lon2, named):
    """Test a geodesic wedge with a missing longitude is refused, naming it.

    Holds positions spec §2 decision 5.

    """
    emsg = rf"A geodesic wedge needs both longitudes, but {named} masked or NaN\."
    with pytest.raises(ValueError, match=emsg):
        wedge(lon1, lon2)


def test_wedge_refuses_a_masked_quantity():
    """Test a quantity of a masked value is refused as the masked value is.

    Holds positions spec §2 decision 5.

    """
    lon1 = UREG.Quantity(np.ma.masked_array(10.0, mask=True), "degree")
    lon2 = UREG.Quantity(30.0, "degree")
    with pytest.raises(ValueError, match=r"but 'lon1' is masked or NaN"):
        wedge(lon1, lon2)


@pytest.mark.parametrize("name", ["lon1", "lon2"])
def test_wedge_refuses_infinite(name):
    """Test an infinite longitude of a geodesic wedge is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    longitudes = {"lon1": 0.0, "lon2": 0.0}
    longitudes[name] = np.inf
    with pytest.raises(ValueError, match=rf"'{name}' cannot be infinite, got inf\."):
        wedge(longitudes["lon1"], longitudes["lon2"])


#: The ends of a geodesic, by the names npoints gives them.
ENDS = {"start_lon": -10.0, "start_lat": 20.0, "end_lon": 10.0, "end_lat": 30.0}

#: Four positions, between two of which npoints_by_idx finds points.
PATH_LONS = [0.0, 10.0, 20.0, 30.0]
PATH_LATS = [0.0, 5.0, 10.0, 15.0]


@pytest.mark.parametrize(
    "value", [np.ma.masked, np.nan, None], ids=["masked", "nan", "none"]
)
@pytest.mark.parametrize("name", list(ENDS))
def test_npoints_gives_nan_for_a_missing_end(name, value):
    """Test a missing end gives NaN at every point, with no warning.

    Holds positions spec §2 decision 1 and positions spec §2 decision 8.

    """
    ends = {**ENDS, name: value}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        glons, glats = npoints(**ends, npts=3, include_start=True, include_end=True)
    assert np.all(np.isnan(glons))
    assert np.all(np.isnan(glats))


@pytest.mark.parametrize("name", list(ENDS))
def test_npoints_refuses_infinite(name):
    """Test an infinite end is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    ends = {**ENDS, name: np.inf}
    with pytest.raises(ValueError, match=rf"'{name}' cannot be infinite, got inf\."):
        npoints(**ends)


@pytest.mark.parametrize(
    ("lons", "lats"),
    [
        (masked(PATH_LONS, 1), PATH_LATS),
        (PATH_LONS, nan(PATH_LATS, 1)),
        (
            UREG.Quantity(masked(PATH_LONS, 1), "degree"),
            UREG.Quantity(PATH_LATS, "degree"),
        ),
    ],
    ids=["lon-masked", "lat-nan", "quantity"],
)
def test_npoints_by_idx_gives_nan_for_a_missing_end(lons, lats):
    """Test a missing end gives NaN at every point, with no warning.

    Holds positions spec §2 decision 8.

    """
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        glons, glats = npoints_by_idx(lons, lats, 0, 1, npts=3)
    assert np.all(np.isnan(glons))
    assert np.all(np.isnan(glats))


def test_npoints_by_idx_reads_only_its_two_positions():
    """Test a missing or infinite position not between the ends is never read."""
    lons = [0.0, 10.0, np.nan, np.inf]
    glons, glats = npoints_by_idx(lons, PATH_LATS, 0, 1, npts=3)
    expected_lons, expected_lats = npoints(0.0, 0.0, 10.0, 5.0, npts=3)
    np.testing.assert_allclose(glons, expected_lons)
    np.testing.assert_allclose(glats, expected_lats)


@pytest.mark.parametrize("name", ["lons", "lats"])
def test_npoints_by_idx_refuses_infinite(name):
    """Test an infinite end is refused, naming the coordinate it is in."""
    coordinates = {"lons": list(PATH_LONS), "lats": list(PATH_LATS)}
    coordinates[name][1] = np.inf
    with pytest.raises(ValueError, match=rf"'{name}' cannot be infinite, got inf\."):
        npoints_by_idx(coordinates["lons"], coordinates["lats"], 0, 1)


def test_line_reads_plain_numbers_without_masked_arrays(mocker):
    """Test a line reads the ends of each pair of its vertices without masked arrays.

    It reads them once for each pair, so building a masked array for each end
    halved the speed of a line. This settles positions spec §8 item 5.
    """
    # geodesic may import the helper by name, so it is watched in both modules
    spy = mocker.MagicMock(wraps=common._missing_as_nan)
    mocker.patch.object(common, "_missing_as_nan", spy)
    mocker.patch.object(geodesic, "_missing_as_nan", spy, create=True)

    mesh = line(np.linspace(-170, 170, 20), np.zeros(20))

    assert mesh.n_points > 0
    spy.assert_not_called()

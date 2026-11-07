# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests of missing positions given to :mod:`geovista.search`.

A position is missing when its longitude or latitude is masked or NaN
(positions spec §2 decision 1).

"""

from __future__ import annotations

import numpy as np
import pint
import pytest

from geovista.search import KDTree, find_nearest_cell
from geovista.transform import transform_mesh

UREG = pint.UnitRegistry()

#: Three points-of-interest within the UK, whose second is made missing.
LONS = [-2.0, 0.0, 1.0]
LATS = [52.0, 53.0, 54.0]
SECOND = [False, True, False]

#: The ways the second point is made missing.
CASES = {
    "lon-masked": (np.ma.masked_array(LONS, mask=SECOND), LATS),
    "lat-masked": (LONS, np.ma.masked_array(LATS, mask=SECOND)),
    "both-masked": (
        np.ma.masked_array(LONS, mask=SECOND),
        np.ma.masked_array(LATS, mask=SECOND),
    ),
    "lon-nan": ([-2.0, np.nan, 1.0], LATS),
    "lat-nan": (LONS, [52.0, np.nan, 54.0]),
}


def no_neighbour(kdtree, distances, indices):
    """Assert that every answer given is that of a point with no neighbour."""
    assert np.all(np.isinf(distances))
    np.testing.assert_array_equal(indices, kdtree.n_points)


@pytest.mark.parametrize("k", [1, 3])
@pytest.mark.parametrize("case", CASES)
def test_missing_point_has_no_neighbour(lam_uk, case, k):
    """Test a missing point answers a distance of inf and the tree's point count.

    Holds positions spec §2 decision 3.

    """
    kdtree = KDTree(lam_uk)
    lons, lats = CASES[case]
    distances, indices = kdtree.query(lons, lats, k=k)
    no_neighbour(kdtree, distances[1], indices[1])


@pytest.mark.parametrize("k", [1, 3])
def test_other_points_answer_as_alone(lam_uk, k):
    """Test each present point answers what it answers when queried alone.

    Holds positions spec §2 decision 3.

    """
    kdtree = KDTree(lam_uk)
    lons, lats = CASES["lon-masked"]
    distances, indices = kdtree.query(lons, lats, k=k)

    for i in (0, 2):
        alone_distances, alone_indices = kdtree.query(LONS[i], LATS[i], k=k)
        np.testing.assert_array_equal(distances[i], alone_distances[0])
        np.testing.assert_array_equal(indices[i], alone_indices[0])


def test_beyond_the_bound(lam_uk):
    """Test a missing point answers as a point beyond distance_upper_bound does.

    Holds positions spec §2 decision 3.

    """
    kdtree = KDTree(lam_uk)
    lons, lats = CASES["lon-nan"]
    distances, indices = kdtree.query(lons, lats, distance_upper_bound=1e-9)
    no_neighbour(kdtree, distances, indices)


@pytest.mark.parametrize(("k", "shape"), [(1, (3,)), (2, (3, 2))])
def test_every_point_missing(lam_uk, k, shape):
    """Test a query of only missing points answers each with no neighbour.

    Holds positions spec §2 decision 3.

    """
    kdtree = KDTree(lam_uk)
    lons = np.ma.masked_array(LONS, mask=True)
    distances, indices = kdtree.query(lons, LATS, k=k)

    assert distances.shape == shape
    assert indices.shape == shape
    assert distances.dtype == np.float64
    assert indices.dtype == np.uint32
    no_neighbour(kdtree, distances, indices)


def test_a_tree_of_centres(lam_uk):
    """Test a tree of cell centres answers a missing point with its cell count.

    Holds positions spec §2 decision 3.

    """
    kdtree = KDTree(lam_uk, preference="center")
    lons, lats = CASES["lon-masked"]
    _, indices = kdtree.query(lons, lats)
    assert indices[1] == lam_uk.n_cells


def test_a_grid_of_points(lam_uk):
    """Test points-of-interest in a grid answer in its raveled order.

    Holds positions spec §2 decision 3.

    """
    kdtree = KDTree(lam_uk)
    grid_lons = [[-2.0, 0.0], [1.0, -1.0]]
    grid_lats = [[52.0, 53.0], [54.0, 55.0]]
    lons = np.ma.masked_array(grid_lons, mask=[[False, True], [False, False]])
    distances, indices = kdtree.query(lons, grid_lats)

    assert distances.shape == (4,)
    no_neighbour(kdtree, distances[1], indices[1])

    for i, (lon, lat) in enumerate(
        zip(np.ravel(grid_lons), np.ravel(grid_lats), strict=True)
    ):
        if i != 1:
            alone_distances, alone_indices = kdtree.query(lon, lat)
            assert distances[i] == alone_distances[0]
            assert indices[i] == alone_indices[0]


def test_a_masked_quantity(lam_uk):
    """Test a quantity of a masked array answers as the masked array does.

    Holds positions spec §2 decision 3.

    """
    kdtree = KDTree(lam_uk)
    lons = np.ma.masked_array(LONS, mask=SECOND)
    expected = kdtree.query(lons, LATS)
    result = kdtree.query(
        UREG.Quantity(lons, "degree"), UREG.Quantity(np.array(LATS), "degree")
    )
    np.testing.assert_array_equal(result[0], expected[0])
    np.testing.assert_array_equal(result[1], expected[1])
    no_neighbour(kdtree, result[0][1], result[1][1])


def test_a_masked_infinite_point(lam_uk):
    """Test an infinite value under a mask is missing, and raises no warning.

    Holds positions spec §2 decision 3.

    """
    kdtree = KDTree(lam_uk)
    lons = np.ma.masked_array([-2.0, np.inf, 1.0], mask=SECOND)
    distances, indices = kdtree.query(lons, LATS, k=2)
    no_neighbour(kdtree, distances[1], indices[1])


@pytest.mark.parametrize("name", ["lons", "lats"])
def test_infinite_refused(lam_uk, name):
    """Test an infinite longitude or latitude is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    coordinates = {"lons": list(LONS), "lats": list(LATS)}
    coordinates[name][1] = np.inf
    with pytest.raises(ValueError, match=rf"'{name}' cannot be infinite"):
        KDTree(lam_uk).query(coordinates["lons"], coordinates["lats"])


@pytest.mark.parametrize("unit", ["degree", "radian"])
@pytest.mark.parametrize("sign", [1, -1], ids=["+inf", "-inf"])
@pytest.mark.parametrize("name", ["lons", "lats"])
def test_an_infinite_quantity_refused(lam_uk, name, sign, unit):
    """Test an infinite quantity is refused, naming it, and raises no warning.

    Holds positions spec §2 decision 2.

    """
    coordinates = {"lons": np.radians(LONS), "lats": np.radians(LATS)}
    if unit == "degree":
        coordinates = {"lons": np.array(LONS), "lats": np.array(LATS)}
    coordinates[name][1] = sign * np.inf
    with pytest.raises(ValueError, match=rf"'{name}' cannot be infinite"):
        KDTree(lam_uk).query(
            UREG.Quantity(coordinates["lons"], unit),
            UREG.Quantity(coordinates["lats"], unit),
        )


#: A point-of-interest made missing in its first, second or both coordinates.
MISSING_POI = pytest.mark.parametrize(
    ("x", "y", "named"),
    [
        (np.ma.masked, 52.0, "'x' is"),
        (np.nan, 52.0, "'x' is"),
        (-2.0, np.ma.masked, "'y' is"),
        (-2.0, np.nan, "'y' is"),
        (np.nan, np.ma.masked, "'x' and 'y' are"),
    ],
    ids=["x-masked", "x-nan", "y-masked", "y-nan", "both"],
)


@MISSING_POI
def test_find_nearest_cell_refuses(lam_uk, x, y, named):
    """Test a missing point-of-interest is refused, naming its coordinates.

    Holds positions spec §2 decision 4.

    """
    emsg = rf"point-of-interest is missing, as {named} masked or NaN"
    with pytest.raises(ValueError, match=emsg):
        find_nearest_cell(lam_uk, x, y)


def test_find_nearest_cell_refuses_a_masked_quantity(lam_uk):
    """Test a quantity whose magnitude is masked is refused, naming it.

    Holds positions spec §2 decision 4.

    """
    x = UREG.Quantity(np.ma.masked_array(-2.0, mask=True), "degree")
    y = UREG.Quantity(52.0, "degree")
    with pytest.raises(ValueError, match=r"as 'x' is masked or NaN"):
        find_nearest_cell(lam_uk, x, y)


def test_find_nearest_cell_refuses_on_a_map(lam_uk):
    """Test a missing point-of-interest is refused on a projected mesh too.

    Holds positions spec §2 decision 4.

    """
    mesh = transform_mesh(lam_uk, "+proj=eqc")
    with pytest.raises(ValueError, match=r"as 'x' is masked or NaN"):
        find_nearest_cell(mesh, np.nan, 0.0)


def test_find_nearest_cell_refuses_infinite(lam_uk):
    """Test an infinite coordinate of a point-of-interest is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    with pytest.raises(ValueError, match=r"'x' cannot be infinite"):
        find_nearest_cell(lam_uk, np.inf, 52.0)


def test_find_nearest_cell_refuses_an_infinite_quantity(lam_uk):
    """Test an infinite quantity of a point-of-interest is refused, naming it.

    Holds positions spec §2 decision 2.

    """
    x = UREG.Quantity(-np.inf, "degree")
    y = UREG.Quantity(52.0, "degree")
    with pytest.raises(ValueError, match=r"'x' cannot be infinite"):
        find_nearest_cell(lam_uk, x, y)

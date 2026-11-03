# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that the public API reads angles and coordinates given as quantities.

By crs spec §2 decision 13, every physical quantity at the API boundary is given as
a plain number in its documented unit, or as a ``pint`` quantity. The builders of
:class:`geovista.bridge.Transform` are tested in "tests/bridge/test_coordinates.py",
and each function here builds what its plain call builds when given quantities.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pint
import pytest

from geovista.bridge import Transform
from geovista.common import to_cartesian, vectors_to_cartesian, wrap
from geovista.crs import WGS84
from geovista.geodesic import BBox, line, npoints, npoints_by_idx, wedge
from geovista.geoplotter import GeoPlotter
from geovista.gridlines import (
    create_meridian_labels,
    create_meridians,
    create_parallel_labels,
    create_parallels,
)
from geovista.search import KDTree, find_nearest_cell
from geovista.transform import transform_point, transform_points

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy.typing import ArrayLike

#: A registry of ``pint``'s own, apart from the one ``geovista.units`` reads with.
UREG = pint.UnitRegistry()

#: A projected CRS in metres.
ROBINSON = "+proj=robin"

#: The longitudes and latitudes of the corners of a small box, in degrees.
LONS, LATS = [0.0, 10.0, 10.0, 0.0], [0.0, 0.0, 10.0, 10.0]

#: The eastward, northward and upward components of a vector at each corner.
VECTORS = ([1.0] * 4, [1.0] * 4, [0.0] * 4)


def rad(degrees: ArrayLike) -> pint.Quantity:
    """Return an angle in degrees as a quantity in radians."""
    return UREG.Quantity(np.radians(degrees), "radian")


def deg(degrees: ArrayLike) -> pint.Quantity:
    """Return an angle in degrees as a quantity in degrees."""
    return UREG.Quantity(degrees, "degree")


@pytest.fixture
def mesh():
    """Fixture for a small mesh on the default globe."""
    return Transform.from_1d([0.0, 10.0, 20.0], [0.0, 10.0, 20.0])


def _points(result: object) -> list[np.ndarray]:
    """Return the arrays a call gives back, whatever its shape, to compare."""
    if hasattr(result, "points"):
        return [np.asarray(result.points)]
    if hasattr(result, "mesh"):
        return [np.asarray(result.mesh.points)]
    if hasattr(result, "blocks"):
        return [np.asarray(block.points) for block in result.blocks]
    if isinstance(result, tuple):
        return [array for item in result for array in _points(item)]
    if isinstance(result, list) and all(
        isinstance(item, np.ndarray) for item in result
    ):
        return result
    return [np.asarray(result, dtype=float)]


def _drawn(plotter: GeoPlotter) -> list[np.ndarray]:
    """Return the points of every mesh a plotter draws."""
    return [
        np.asarray(actor.mapper.dataset.points)
        for actor in plotter.renderer.actors.values()
        if getattr(getattr(actor, "mapper", None), "dataset", None) is not None
    ]


def _graticule(method: str, *args: object, **kwargs: object) -> list[np.ndarray]:
    """Draw a graticule with a plotter's method, and return its meshes."""
    plotter = GeoPlotter()
    getattr(plotter, method)(*args, show_labels=False, **kwargs)
    return _drawn(plotter)


#: Each function, called with angles in degrees, and with the same angles as
#: quantities in radians.
CALLS: dict[str, tuple[Callable[[], Any], Callable[[], Any]]] = {
    "transform_point": (
        lambda: transform_point(WGS84, ROBINSON, x=10.0, y=20.0),
        lambda: transform_point(WGS84, ROBINSON, x=rad(10.0), y=rad(20.0)),
    ),
    "transform_points": (
        lambda: transform_points(WGS84, ROBINSON, xs=LONS, ys=LATS),
        lambda: transform_points(WGS84, ROBINSON, xs=rad(LONS), ys=rad(LATS)),
    ),
    "BBox": (lambda: BBox(LONS, LATS), lambda: BBox(rad(LONS), rad(LATS))),
    "line": (lambda: line(LONS, LATS), lambda: line(rad(LONS), rad(LATS))),
    "npoints": (
        lambda: npoints(0.0, 0.0, 10.0, 10.0),
        lambda: npoints(rad(0.0), rad(0.0), rad(10.0), rad(10.0)),
    ),
    "npoints_by_idx": (
        lambda: npoints_by_idx(LONS, LATS, start_idx=0, end_idx=2),
        lambda: npoints_by_idx(rad(LONS), rad(LATS), start_idx=0, end_idx=2),
    ),
    "wedge": (lambda: wedge(-10.0, 10.0), lambda: wedge(rad(-10.0), rad(10.0))),
    "to_cartesian": (
        lambda: to_cartesian(LONS, LATS),
        lambda: to_cartesian(rad(LONS), rad(LATS)),
    ),
    "vectors_to_cartesian": (
        lambda: vectors_to_cartesian(LONS, LATS, vectors=VECTORS),
        lambda: vectors_to_cartesian(rad(LONS), rad(LATS), vectors=VECTORS),
    ),
    "wrap": (
        lambda: wrap([190.0, -190.0], base=-180.0, period=360.0),
        lambda: wrap(rad([190.0, -190.0]), base=rad(-180.0), period=rad(360.0)),
    ),
    "create_meridians": (
        lambda: create_meridians(
            start=-90.0, stop=90.0, step=30.0, lat_step=10.0, central_meridian=10.0
        ),
        lambda: create_meridians(
            start=rad(-90.0),
            stop=rad(90.0),
            step=rad(30.0),
            lat_step=rad(10.0),
            central_meridian=rad(10.0),
        ),
    ),
    "create_parallels": (
        lambda: create_parallels(start=-60.0, stop=60.0, step=30.0, lon_step=10.0),
        lambda: create_parallels(
            start=rad(-60.0), stop=rad(60.0), step=rad(30.0), lon_step=rad(10.0)
        ),
    ),
    "add_graticule": (
        lambda: _graticule(
            "add_graticule",
            lon_start=-90.0,
            lon_stop=90.0,
            lon_step=30.0,
            lat_start=-60.0,
            lat_stop=60.0,
            lat_step=30.0,
        ),
        lambda: _graticule(
            "add_graticule",
            lon_start=rad(-90.0),
            lon_stop=rad(90.0),
            lon_step=rad(30.0),
            lat_start=rad(-60.0),
            lat_stop=rad(60.0),
            lat_step=rad(30.0),
        ),
    ),
    "add_meridian": (
        lambda: _graticule("add_meridian", 30.0, lat_step=10.0),
        lambda: _graticule("add_meridian", rad(30.0), lat_step=rad(10.0)),
    ),
    "add_meridians": (
        lambda: _graticule("add_meridians", start=-90.0, stop=90.0, step=45.0),
        lambda: _graticule(
            "add_meridians", start=rad(-90.0), stop=rad(90.0), step=rad(45.0)
        ),
    ),
    "add_parallel": (
        lambda: _graticule("add_parallel", 30.0, lon_step=10.0),
        lambda: _graticule("add_parallel", rad(30.0), lon_step=rad(10.0)),
    ),
    "add_parallels": (
        lambda: _graticule("add_parallels", start=-60.0, stop=60.0, step=30.0),
        lambda: _graticule(
            "add_parallels", start=rad(-60.0), stop=rad(60.0), step=rad(30.0)
        ),
    ),
}


@pytest.mark.parametrize("name", list(CALLS))
def test_an_angle_builds_what_its_degrees_build(name):
    """A quantity in radians gives what its plain degrees give."""
    plain, quantity = CALLS[name]
    expected, result = _points(plain()), _points(quantity())
    assert len(result) == len(expected)
    for got, want in zip(result, expected, strict=True):
        np.testing.assert_allclose(got, want, rtol=1e-12, atol=1e-9)


@pytest.mark.parametrize(
    ("labels", "angles"),
    [
        (create_meridian_labels, [-150.0, 0.0, 30.0]),
        (create_parallel_labels, [-60.0, 0.0, 45.0]),
    ],
    ids=["meridians", "parallels"],
)
def test_labels_read_an_angle(labels, angles):
    """A quantity in radians is labelled with its degrees."""
    assert labels(rad(angles)) == labels(angles)


def test_a_projected_point_is_read_in_the_units_of_its_crs():
    """A length is read in the unit of the axes of a projected source CRS."""
    expected = transform_points(ROBINSON, WGS84, xs=[1000.0], ys=[2000.0])
    xs, ys = UREG.Quantity([1.0], "km"), UREG.Quantity([2.0], "km")
    np.testing.assert_allclose(
        transform_points(ROBINSON, WGS84, xs=xs, ys=ys), expected, rtol=1e-12
    )


def test_a_bbox_in_a_projected_crs():
    """A bounding box reads a length in the unit of the axes of its CRS."""
    xs = [0.0, 1e6, 1e6, 0.0]
    ys = [0.0, 0.0, 1e6, 1e6]
    expected = BBox(xs, ys, crs=ROBINSON).mesh.points
    qxs, qys = UREG.Quantity(xs, "m").to("km"), UREG.Quantity(ys, "m").to("km")
    np.testing.assert_allclose(
        BBox(qxs, qys, crs=ROBINSON).mesh.points, expected, rtol=1e-12
    )


@pytest.mark.parametrize("unit", ["degree", "radian"])
def test_npoints_reads_a_quantity_in_the_unit_of_its_flag(unit):
    """A quantity is read in radians with radians=True, and gives radians back."""
    expected = npoints(*np.radians([0.0, 0.0, 10.0, 10.0]), radians=True)
    given = [deg(value).to(unit) for value in (0.0, 0.0, 10.0, 10.0)]
    result = npoints(*given, radians=True)
    np.testing.assert_allclose(np.asarray(result), np.asarray(expected), rtol=1e-12)


def test_a_cell_is_found_from_a_quantity(mesh):
    """The nearest cell of a point given as quantities is that of its degrees."""
    expected = find_nearest_cell(mesh, 5.0, 5.0)
    assert find_nearest_cell(mesh, rad(5.0), rad(5.0)) == expected


def test_a_kdtree_queries_a_quantity(mesh):
    """A tree finds the points nearest an angle as it does its degrees."""
    tree = KDTree(mesh)
    expected = tree.query([5.0, 15.0], [5.0, 15.0])
    result = tree.query(rad([5.0, 15.0]), rad([5.0, 15.0]))
    for got, want in zip(result, expected, strict=True):
        np.testing.assert_allclose(got, want, rtol=1e-12)


@pytest.mark.parametrize("given", [{"x": 30.0, "y": 20.0}, {"x": 30.0}, {"y": 20.0}])
def test_view_poi_reads_a_quantity(given):
    """A point of interest given as quantities is viewed as its degrees are."""
    plotter = GeoPlotter()
    plotter.view_poi(**given)
    expected = plotter.camera.position
    plotter = GeoPlotter()
    plotter.view_poi(**{name: rad(value) for name, value in given.items()})
    np.testing.assert_allclose(plotter.camera.position, expected, rtol=1e-12)


@pytest.mark.parametrize(
    ("call", "alone"),
    [
        (lambda: to_cartesian(rad(LONS), LATS), "lons"),
        (lambda: line(LONS, rad(LATS)), "lats"),
        (lambda: transform_point(WGS84, ROBINSON, x=rad(10.0), y=20.0), "x"),
        (lambda: npoints(rad(0.0), 0.0, 10.0, 10.0), "start_lon"),
        (
            lambda: KDTree(Transform.from_1d([0, 1], [0, 1])).query(LONS, rad(LATS)),
            "lats",
        ),
    ],
    ids=["to_cartesian", "line", "transform_point", "npoints", "query"],
)
def test_one_quantity_of_a_position_alone(call, alone):
    """A coordinate given as a quantity beside a plain one is refused."""
    with pytest.raises(ValueError, match=f"got {alone!r} alone"):
        _ = call()


@pytest.mark.parametrize(
    ("call", "name"),
    [
        (lambda: wrap(LONS, base=UREG.Quantity(1.0, "km")), "base"),
        (lambda: wedge(UREG.Quantity(1.0, "km"), 10.0), "lon1"),
        (lambda: create_meridians(step=UREG.Quantity(30.0, "m")), "step"),
        (
            lambda: to_cartesian(UREG.Quantity(LONS, "m"), UREG.Quantity(LATS, "m")),
            "lons",
        ),
    ],
    ids=["wrap", "wedge", "create_meridians", "to_cartesian"],
)
def test_a_length_for_an_angle(call, name):
    """A length given for an angle is refused, naming the argument."""
    with pytest.raises(ValueError, match=f"Cannot read {name!r} as an angle"):
        _ = call()


def test_a_length_for_a_geographic_source_crs():
    """A length for a geographic source CRS is refused, naming the CRS argument."""
    xs, ys = UREG.Quantity([1.0], "km"), UREG.Quantity([2.0], "km")
    with pytest.raises(ValueError, match="'xs' is a length, but 'src_crs' measures"):
        _ = transform_points(WGS84, ROBINSON, xs=xs, ys=ys)

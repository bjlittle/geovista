# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that :mod:`geovista.bridge` builders take coordinates as quantities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pint
import pytest

from geovista.bridge import Transform

if TYPE_CHECKING:
    from collections.abc import Callable

    import pyvista as pv

#: A registry of ``pint``'s own, so that no quantity comes from the registry
#: ``geovista.units`` reads units with.
UREG = pint.UnitRegistry()

#: The cell bounds of a small regular grid, of 2 cells, in degrees.
XS, YS = np.array([0.0, 10.0, 20.0]), np.array([0.0, 10.0])

#: The heights of the levels of a structured grid, in metres.
ZS = [0.0, 1000.0]

#: The points of a small 2D mesh, of 4 cells, in degrees.
LONS_2D, LATS_2D = np.meshgrid([0.0, 10.0, 20.0], [0.0, 10.0, 20.0], indexing="xy")

#: The points of a small cloud, in degrees.
CLOUD_LONS = np.array([0.0, 10.0, 20.0, 30.0])
CLOUD_LATS = np.array([0.0, 5.0, 10.0, 15.0])

#: The points and faces of a small unstructured mesh, of 2 cells, in degrees.
UNSTRUCTURED_LONS = np.array([0.0, 10.0, 10.0, 0.0, 20.0, 20.0])
UNSTRUCTURED_LATS = np.array([0.0, 0.0, 10.0, 10.0, 0.0, 10.0])
CONNECTIVITY = [[0, 1, 2, 3], [1, 4, 5, 2]]

#: Each builder, taking its xs and ys, with the longitudes and latitudes it is
#: given here, in degrees.
BUILDERS: dict[str, tuple[Callable[..., pv.DataSet], np.ndarray, np.ndarray]] = {
    "from_1d": (Transform.from_1d, XS, YS),
    "from_2d": (Transform.from_2d, LONS_2D, LATS_2D),
    "from_points": (Transform.from_points, CLOUD_LONS, CLOUD_LATS),
    "from_unstructured": (
        lambda xs, ys, **kwargs: Transform.from_unstructured(
            xs, ys, connectivity=CONNECTIVITY, **kwargs
        ),
        UNSTRUCTURED_LONS,
        UNSTRUCTURED_LATS,
    ),
    "to_structured_grid": (
        lambda xs, ys, **kwargs: Transform.to_structured_grid(xs, ys, ZS, **kwargs),
        XS,
        YS,
    ),
    "call": (lambda xs, ys, **kwargs: Transform(xs, ys, **kwargs)(), XS, YS),
}

#: The builders that take a CRS other than WGS84.
PROJECTABLE = [name for name in BUILDERS if name != "to_structured_grid"]

#: Metres to a degree, so that the coordinates of a builder are lengths that lie
#: well within the domain of an equidistant cylindrical projection.
METRES_PER_DEGREE = 10_000.0

#: An equidistant cylindrical CRS in metres, and one in kilometres.
EQC, EQC_KM = "+proj=eqc", "+proj=eqc +units=km"


@pytest.fixture(params=list(BUILDERS))
def builder(request) -> tuple[Callable[..., pv.DataSet], np.ndarray, np.ndarray]:
    """Fixture for each builder, and the longitudes and latitudes it is given."""
    return BUILDERS[request.param]


@pytest.fixture(params=PROJECTABLE)
def projectable(request) -> tuple[Callable[..., pv.DataSet], np.ndarray, np.ndarray]:
    """Fixture for each builder that takes a projected CRS."""
    return BUILDERS[request.param]


@pytest.mark.parametrize(
    "registry",
    [UREG, pint.get_application_registry()],
    ids=["own", "application"],
)
def test_an_angle_builds_the_mesh_of_its_degrees(builder, registry):
    """An angle in radians builds the mesh its degrees build, from any registry."""
    build, lons, lats = builder
    expected = build(lons, lats).points
    xs = registry.Quantity(np.radians(lons), "radian")
    ys = registry.Quantity(np.radians(lats), "radian")
    np.testing.assert_allclose(build(xs, ys).points, expected, rtol=1e-12)


def test_degrees_are_read_exactly(builder):
    """A quantity in degrees builds the mesh of its magnitudes, to the bit."""
    build, lons, lats = builder
    expected = build(lons, lats).points
    xs, ys = UREG.Quantity(lons, "degree"), UREG.Quantity(lats, "degree")
    np.testing.assert_array_equal(build(xs, ys).points, expected)


@pytest.mark.parametrize("unit", ["degree", "radian"])
def test_an_angle_for_a_crs_declared_in_radians(projectable, in_radians, unit):
    """An angle is read in degrees for a CRS declared in radians, as pyproj takes it."""
    build, lons, lats = projectable
    crs = in_radians("EPSG:4326")
    expected = build(lons, lats, crs=crs).points
    xs = UREG.Quantity(lons, "degree").to(unit)
    ys = UREG.Quantity(lats, "degree").to(unit)
    np.testing.assert_allclose(build(xs, ys, crs=crs).points, expected, rtol=1e-12)


@pytest.mark.usefixtures("no_network")
def test_an_angle_for_a_crs_in_grads(projectable):
    """An angle is read in grads for NTF (Paris), as pyproj takes it."""
    build, lons, lats = projectable
    # a small mesh in France, east of the Paris meridian, in grads
    xs, ys = lons / 10.0, 52.0 + lats / 10.0
    expected = build(xs, ys, crs="EPSG:4807").points
    # a grad is 0.9 degrees
    qxs = UREG.Quantity(xs * 0.9, "degree")
    qys = UREG.Quantity(ys * 0.9, "degree")
    np.testing.assert_allclose(
        build(qxs, qys, crs="EPSG:4807").points, expected, rtol=1e-12
    )


@pytest.mark.parametrize(
    ("crs", "axis_metres", "unit", "unit_metres"),
    [
        (EQC, 1.0, "km", 1000.0),
        (EQC_KM, 1000.0, "m", 1.0),
        (EQC, 1.0, "ft", 0.3048),
    ],
    ids=["km-for-metres", "metres-for-km", "feet-for-metres"],
)
def test_a_length_in_the_units_of_the_crs(
    projectable, crs, axis_metres, unit, unit_metres
):
    """A length is read in the unit of the axes of a projected CRS."""
    build, lons, lats = projectable
    # the coordinates, in the unit of the axes of the crs
    xs = lons * METRES_PER_DEGREE / axis_metres
    ys = lats * METRES_PER_DEGREE / axis_metres
    expected = build(xs, ys, crs=crs).points
    # the same coordinates, in the unit of the quantity
    factor = axis_metres / unit_metres
    qxs, qys = UREG.Quantity(xs * factor, unit), UREG.Quantity(ys * factor, unit)
    np.testing.assert_allclose(build(qxs, qys, crs=crs).points, expected, rtol=1e-12)


def test_an_angle_for_a_projected_crs(projectable):
    """An angle is refused for a CRS in metres, which names the CRS to use."""
    build, lons, lats = projectable
    xs, ys = UREG.Quantity(lons, "degree"), UREG.Quantity(lats, "degree")
    emsg = r"'xs' is an angle, but 'crs' measures its axes in 'metre'.*geodetic_crs"
    with pytest.raises(ValueError, match=emsg):
        _ = build(xs, ys, crs=EQC)


def test_a_length_for_a_geographic_crs(builder):
    """A length is refused for a CRS in degrees."""
    build, lons, lats = builder
    xs, ys = UREG.Quantity(lons, "km"), UREG.Quantity(lats, "km")
    emsg = r"'xs' is a length, but 'crs' measures its axes in 'degree'"
    with pytest.raises(ValueError, match=emsg):
        _ = build(xs, ys)


def test_a_dimensionless_quantity(builder):
    """A dimensionless quantity is refused, as an angle needs an angular unit."""
    build, lons, lats = builder
    xs, ys = UREG.Quantity(lons, ""), UREG.Quantity(lats, "")
    with pytest.raises(ValueError, match="dimensionless"):
        _ = build(xs, ys)


@pytest.mark.parametrize("alone", ["xs", "ys"])
def test_one_quantity_alone(builder, alone):
    """A quantity is refused unless both the xs and the ys are quantities."""
    build, lons, lats = builder
    xs = UREG.Quantity(lons, "degree") if alone == "xs" else lons
    ys = UREG.Quantity(lats, "degree") if alone == "ys" else lats
    emsg = f"Give 'xs' and 'ys' both as pint quantities, or neither, got '{alone}'"
    with pytest.raises(ValueError, match=emsg):
        _ = build(xs, ys)


def test_a_masked_point_drops_its_faces():
    """A masked point keeps its mask, so the faces that use it are dropped."""
    mask = [False, False, False, False, True, False]
    lons = np.ma.masked_array(np.radians(UNSTRUCTURED_LONS), mask=mask)
    lats = np.ma.masked_array(np.radians(UNSTRUCTURED_LATS), mask=mask)
    xs, ys = UREG.Quantity(lons, "radian"), UREG.Quantity(lats, "radian")
    with pytest.warns(UserWarning, match="1 face that uses a missing point"):
        mesh = Transform.from_unstructured(xs, ys, connectivity=CONNECTIVITY)
    assert mesh.n_cells == 1


def test_a_masked_bound_is_refused():
    """A masked bound keeps its mask, so it is refused as a gap in its axis."""
    xs = UREG.Quantity(np.ma.masked_array(XS, mask=[False, True, False]), "degree")
    ys = UREG.Quantity(YS, "degree")
    with pytest.raises(ValueError, match="no masked bounds, got '1'"):
        _ = Transform.from_1d(xs, ys)


class _Carrier:
    """An array that carries its units as an attribute, as an xarray DataArray does."""

    units = "radian"

    def __init__(self, values: np.ndarray) -> None:
        self.values = values

    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        return np.asarray(self.values, dtype=dtype)


def test_units_carried_as_an_attribute_are_not_read(builder):
    """An array carrying its own units is read as plain numbers, as before."""
    build, lons, lats = builder
    expected = build(lons, lats).points
    mesh = build(_Carrier(lons), _Carrier(lats))
    np.testing.assert_array_equal(mesh.points, expected)

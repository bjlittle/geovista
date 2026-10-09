# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.transform.transform_mesh`."""

from __future__ import annotations

import cartopy.crs as ccrs
import numpy as np
from pyproj import CRS, Transformer
import pytest
import pyvista as pv

import geovista as gv
from geovista.common import (
    GV_POINT_ZLEVEL,
    ZLEVEL_SCALE,
    from_cartesian,
    to_cartesian,
)
from geovista.crs import WGS84, projected, to_wkt
from geovista.transform import _ZLEVEL, transform_mesh

#: Fraction of the projection width above which a cell is considered torn.
TORN = 0.25

#: Central meridian shift that exercises the seam of a global mesh.
MERIDIAN: float = 180.0

#: Longitude/latitude extent of a regional mesh, as (xmin, xmax, ymin, ymax).
REGION: tuple[float, float, float, float] = (10.0, 30.0, 30.0, 50.0)

#: Central meridian shift applied to a regional mesh.
REGIONAL_MERIDIAN: float = 45.0

#: A planar target CRS, so that a z-level is scaled into each point's z-value.
PLANAR = "+proj=eqc"

#: A second planar target CRS, for a cloud moved between planar CRSs.
ROBIN = "+proj=robin"

#: The semi-major axis of the WGS84 and GRS80 ellipsoids, in metres.
SEMI_MAJOR: float = 6378137.0

#: The semi-major axis of the Airy 1830 ellipsoid, in metres.
AIRY: float = 6377563.396

#: A geographic CRS on the WGS84 ellipsoid, with its axes declared in radians.
RADIANS = (
    'GEOGCRS["WGS 84 in radians",DATUM["World Geodetic System 1984",'
    'ELLIPSOID["WGS 84",6378137,298.257223563]],CS[ellipsoidal,2],'
    'AXIS["longitude",east,ANGLEUNIT["radian",1]],'
    'AXIS["latitude",north,ANGLEUNIT["radian",1]]]'
)

#: Whole-globe projections carrying the central meridian in assorted ways.
#:
#: Note that "LambertConformal" and "NearsidePerspective" are deliberately
#: absent, as their limited projection domain cannot accommodate a global mesh
#: at any central meridian. Their central meridian recovery is covered by
#: ``tests/crs/test_get_central_meridian.py``.
PROJECTIONS = [
    ("Mollweide", ccrs.Mollweide),
    ("Robinson", ccrs.Robinson),
    ("AlbersEqualArea", ccrs.AlbersEqualArea),
    ("EquidistantConic", ccrs.EquidistantConic),
    ("Hammer", ccrs.Hammer),
    ("PlateCarree", ccrs.PlateCarree),
]


@pytest.fixture
def global_mesh():
    """Create a 10 degree global quad mesh."""
    lons = np.arange(-180, 181, 10, dtype=float)
    lats = np.arange(-90, 91, 10, dtype=float)
    shape = (lats.size - 1, lons.size - 1)
    data = np.arange(np.prod(shape), dtype=float).reshape(shape)
    return gv.Transform.from_1d(lons, lats, data=data)


@pytest.fixture
def regional_mesh():
    """Create a regional quad mesh, clear of both the seam and the poles."""
    lon_min, lon_max, lat_min, lat_max = REGION
    lons = np.linspace(lon_min, lon_max, 3)
    lats = np.linspace(lat_min, lat_max, 3)
    data = np.arange(4, dtype=float).reshape(2, 2)
    return gv.Transform.from_1d(lons, lats, data=data)


@pytest.fixture
def cloud():
    """Create a small point cloud, which ``transform_mesh`` never slices."""
    return gv.Transform.from_points([10.0, 20.0, 30.0], [30.0, 40.0, 50.0])


@pytest.fixture
def lone_point():
    """Create a point cloud of one point."""
    return gv.Transform.from_points([10.0], [30.0])


@pytest.fixture
def lifted_cloud():
    """Create a small point cloud lifted to a different z-level at each point."""
    return gv.Transform.from_points(
        [10.0, 20.0, 30.0], [30.0, 40.0, 50.0], zlevel=[2, 3, 4], zscale=0.5
    )


def _quad(lon_min, lon_max, lat_min, lat_max) -> pv.PolyData:
    """Create a small quad mesh over the given extent, in degrees."""
    lons = np.linspace(lon_min, lon_max, 5)
    lats = np.linspace(lat_min, lat_max, 5)
    return gv.Transform.from_1d(lons, lats)


def _cell_widths(mesh) -> np.ndarray:
    """Calculate each cell width as a fraction of the projection width."""
    points, faces = mesh.points, mesh.faces.reshape(-1, 5)[:, 1:]
    xs = points[faces, 0]
    span = points[:, 0].max() - points[:, 0].min()
    return (xs.max(axis=1) - xs.min(axis=1)) / span


def _torn_cells(mesh) -> int:
    """Count cells spanning an implausible fraction of the projection width."""
    return int((_cell_widths(mesh) > TORN).sum())


@pytest.mark.parametrize(
    "projection", [p for _, p in PROJECTIONS], ids=[n for n, _ in PROJECTIONS]
)
def test_transform_mesh__seam(global_mesh, projection):
    """Test that a shifted central meridian does not tear the mesh.

    A central meridian that cannot be recovered from the target CRS is assumed
    to be 0, which cuts the mesh at the wrong seam and leaves cells stretched
    right across the projection. See :issue:`2512`.

    """
    tgt_crs = CRS.from_user_input(projection(central_longitude=MERIDIAN))
    result = transform_mesh(global_mesh, tgt_crs)

    assert _torn_cells(result) == 0


@pytest.mark.parametrize(
    "projection", [p for _, p in PROJECTIONS], ids=[n for n, _ in PROJECTIONS]
)
def test_transform_mesh__seam_invariant(global_mesh, projection):
    """Test that shifting the central meridian does not change mesh integrity.

    A correctly seamed mesh is cut in the same place relative to its central
    meridian, so the widest cell is unchanged by the shift.

    """
    unshifted = transform_mesh(global_mesh.copy(), CRS.from_user_input(projection()))
    shifted = transform_mesh(
        global_mesh.copy(), CRS.from_user_input(projection(central_longitude=MERIDIAN))
    )

    expected = _cell_widths(unshifted).max()

    assert _cell_widths(shifted).max() == pytest.approx(expected, abs=1e-6)


@pytest.mark.xfail(
    reason="rotated pole seam is pole-relative, not a scalar meridian - see gh#2512",
    strict=True,
)
def test_transform_mesh__rotated_pole_seam(global_mesh):
    """Test the known rotated pole tearing, to record the gap rather than hide it."""
    tgt_crs = CRS.from_user_input(
        ccrs.RotatedPole(pole_longitude=MERIDIAN, pole_latitude=45)
    )
    with pytest.warns(UserWarning, match="unable to determine the central meridian"):
        result = transform_mesh(global_mesh, tgt_crs)

    assert _torn_cells(result) == 0


def test_transform_mesh__flat_source(regional_mesh):
    """Test that an already flat mesh is not preprocessed as a sphere.

    A mesh transformed to a flat geographic CRS carries lon/lat points rather
    than cartesian xyz, so it must bypass the spherical seam slicing and the
    central meridian rotation. Otherwise ``rotate_z`` spins the lon/lat values
    as if they were cartesian. See :issue:`2522`.

    """
    flat = transform_mesh(regional_mesh, ccrs.PlateCarree())
    assert projected(flat)
    assert flat.bounds[:4] == pytest.approx(REGION)

    shifted = transform_mesh(
        flat, ccrs.PlateCarree(central_longitude=REGIONAL_MERIDIAN)
    )

    xmin, xmax, ymin, ymax = REGION
    expected = (xmin - REGIONAL_MERIDIAN, xmax - REGIONAL_MERIDIAN, ymin, ymax)

    assert shifted.n_points == flat.n_points
    assert shifted.bounds[:4] == pytest.approx(expected)


@pytest.mark.parametrize("mesh", ["regional_mesh", "cloud"])
@pytest.mark.parametrize("sequence", [list, tuple, np.array])
def test_transform_mesh__zlevel_per_point(request, mesh, sequence):
    """A per-point zlevel is honoured whatever form of ArrayLike carries it.

    Typing spec §3.3: the signature promises ``ArrayLike``, but before the
    conversion at the boundary a list or tuple met ``zlevel * zscale`` with
    ``TypeError``, and an array of more than one element raised ``ValueError``.
    Each point has a level of its own, so a level that landed on the wrong
    point would show. A point's z is linear in its level, offset by any level
    a cloud encodes, so it lies on the line through its z at levels 0 and 1.

    """
    mesh = request.getfixturevalue(mesh)
    base = transform_mesh(mesh.copy(), PLANAR, zlevel=0)
    unit = transform_mesh(mesh.copy(), PLANAR, zlevel=1)
    levels = np.arange(1, mesh.n_points + 1)

    result = transform_mesh(mesh.copy(), PLANAR, zlevel=sequence(levels.tolist()))

    np.testing.assert_array_equal(result.points[:, :2], unit.points[:, :2])
    zs = base.points[:, 2] + levels * (unit.points[:, 2] - base.points[:, 2])
    np.testing.assert_allclose(result.points[:, 2], zs, rtol=1e-9)


def test_transform_mesh__zlevel_numpy_scalar(regional_mesh):
    """A numpy scalar is a scalar zlevel like any other."""
    expected = transform_mesh(regional_mesh.copy(), PLANAR, zlevel=2)

    result = transform_mesh(regional_mesh.copy(), PLANAR, zlevel=np.float64(2))

    np.testing.assert_array_equal(result.points, expected.points)


def test_transform_mesh__zlevel_left_untouched(cloud):
    """The caller's zlevel is never mutated, though a cloud adds to it."""
    zlevel = np.full(cloud.n_points, 2.0)

    _ = transform_mesh(cloud.copy(), PLANAR, zlevel=zlevel)

    np.testing.assert_array_equal(zlevel, np.full(cloud.n_points, 2.0))


def test_transform_mesh__zlevel_that_cannot_broadcast(regional_mesh):
    """A zlevel of the wrong length fails before any point is written."""
    before = regional_mesh.points.copy()
    zlevel = [2] * (regional_mesh.n_points + 1)

    with pytest.raises(ValueError, match="does not broadcast to its 9 points"):
        _ = transform_mesh(
            regional_mesh, PLANAR, zlevel=zlevel, slice_connectivity=False, inplace=True
        )

    np.testing.assert_array_equal(regional_mesh.points, before)


def test_transform_mesh__no_crs():
    """A mesh without a CRS cannot be transformed.

    ``mypy`` reported this check as unreachable while ``from_wkt`` claimed always
    to return a CRS. The annotation was wrong, not the check.

    """
    with pytest.raises(ValueError, match="no coordinate reference system"):
        _ = transform_mesh(pv.Sphere(), PLANAR)


@pytest.mark.parametrize(
    ("mesh", "shape"),
    [("regional_mesh", (9, 1)), ("lone_point", (5,)), ("lone_point", (0,))],
    ids=["column", "longer", "empty"],
)
def test_transform_mesh__zlevel_that_broadcasts_only_with_the_points(
    request, mesh, shape
):
    """A zlevel must broadcast to the points, not merely with them.

    Each of these shapes broadcasts with a column of points into something
    larger, so a check of compatibility alone passes them, and the mesh is half
    written before numpy refuses the z column.

    """
    mesh = request.getfixturevalue(mesh)
    before = mesh.points.copy()

    with pytest.raises(ValueError, match="does not broadcast to its"):
        _ = transform_mesh(
            mesh,
            PLANAR,
            zlevel=np.full(shape, 2.0),
            slice_connectivity=False,
            inplace=True,
        )

    np.testing.assert_array_equal(mesh.points, before)


def test_transform_mesh__zlevel_follows_the_slice(global_mesh):
    """A per-point zlevel follows each point through the seam slicing.

    Slicing a global mesh at the seam adds points the caller never made, so a
    zlevel sized to the caller's mesh must travel with the points. The levels
    vary with latitude, so a level that landed on the wrong point would show.

    """
    lats = from_cartesian(global_mesh)[:, 1]
    zlevel = 1 + np.abs(lats) / 90
    unit = transform_mesh(global_mesh.copy(), PLANAR, zlevel=1)

    result = transform_mesh(global_mesh.copy(), PLANAR, zlevel=zlevel)

    assert result.n_points > global_mesh.n_points
    inverse = Transformer.from_crs(PLANAR, "EPSG:4326", always_xy=True)
    _, lats = inverse.transform(result.points[:, 0], result.points[:, 1])
    expected = (1 + np.abs(lats) / 90) * unit.points[0, 2]
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)


@pytest.mark.parametrize("zlevel", [0, [1]], ids=["scalar", "per-point"])
def test_transform_mesh__zlevel_carry_spares_the_callers_array(regional_mesh, zlevel):
    """An array of the caller's named as the zlevel carry is kept, and never read.

    A per-point zlevel travels through the seam slice as point data. The array it
    travels in must not displace one of the caller's that shares its name, and
    the clean-up must remove only what the transform added.

    """
    expected = transform_mesh(regional_mesh.copy(), PLANAR, zlevel=zlevel)
    data = np.arange(regional_mesh.n_points, dtype=float)
    regional_mesh.point_data[_ZLEVEL] = data

    result = transform_mesh(regional_mesh, PLANAR, zlevel=zlevel)

    np.testing.assert_array_equal(regional_mesh.point_data[_ZLEVEL], data)
    np.testing.assert_array_equal(result.point_data[_ZLEVEL], data)
    np.testing.assert_array_equal(result.points, expected.points)
    assert [name for name in result.point_data if _ZLEVEL in name] == [_ZLEVEL]


def test_transform_mesh__integer_levels_interpolate_as_floats():
    """Integer levels cross the seam as the same levels given as floats do.

    The seam slice splits each cell that straddles it, and interpolates the level
    of each point it adds, so integer levels must not be rounded on the way.

    """
    mesh = gv.Transform.from_1d(np.linspace(-170, 190, 13), np.linspace(-60, 60, 7))
    levels = np.where(from_cartesian(mesh)[:, 0] < 0, 0, 3)
    expected = transform_mesh(mesh.copy(), PLANAR, zlevel=levels.astype(float))

    result = transform_mesh(mesh.copy(), PLANAR, zlevel=levels)

    assert result.n_points > mesh.n_points
    np.testing.assert_array_equal(result.points, expected.points)


@pytest.mark.parametrize(
    ("lons", "tgt_crs"),
    [
        ([170.0, -170.0], PLANAR),
        ([-140.0, -130.0], f"{PLANAR} +lon_0={REGIONAL_MERIDIAN}"),
    ],
    ids=["antimeridian", "shifted"],
)
def test_transform_mesh__zlevel_per_point_follows_sliced_lines(lons, tgt_crs):
    """A per-point zlevel follows a line through the seam, interpolated at the split.

    Issue 2583: ``slice_lines`` rebuilt the lines it split without their point data,
    so ``transform_mesh`` refused a per-point zlevel on them. The seam falls midway
    along this line, so the two points the split adds take the mean of its levels.
    The caller's mesh is left as it was, rotated back from the shifted seam.

    """
    mesh = pv.PolyData(to_cartesian(lons, [10.0, 10.0]), lines=[2, 0, 1])
    to_wkt(mesh, WGS84)
    before = mesh.copy(deep=True)

    result = transform_mesh(mesh, tgt_crs, zlevel=[1.0, 3.0])

    expected = np.array([1.0, 3.0, 2.0, 2.0]) * ZLEVEL_SCALE * SEMI_MAJOR
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)
    np.testing.assert_allclose(mesh.points, before.points, atol=1e-12)
    assert list(mesh.point_data) == list(before.point_data)


def test_transform_mesh__zlevel_to_wgs84(regional_mesh):
    """A mesh sent to WGS84 is lifted off the sphere by its zlevel.

    Issue 2581: the planar z offset also ran for a WGS84 target, overwriting the z
    that ``to_cartesian`` had lifted, so the mesh collapsed onto the equatorial
    plane.

    """
    levels = np.arange(1, regional_mesh.n_points + 1)
    flat = transform_mesh(regional_mesh, PLANAR)

    result = transform_mesh(flat, WGS84, zlevel=levels)

    radii = np.linalg.norm(result.points, axis=1)
    np.testing.assert_allclose(radii, 1 + levels * ZLEVEL_SCALE, rtol=1e-12)
    directions = result.points / radii[:, np.newaxis]
    np.testing.assert_allclose(directions, regional_mesh.points, atol=1e-9)


def test_transform_mesh__cloud_round_trip(lifted_cloud):
    """A cloud sent to a planar CRS and back to WGS84 keeps each point's z-level.

    Issue 2581: nothing decoded the levels from the planar cloud on the way back,
    so they were lost.

    """
    result = transform_mesh(transform_mesh(lifted_cloud, PLANAR), WGS84)

    np.testing.assert_allclose(result.points, lifted_cloud.points, rtol=1e-9)
    assert GV_POINT_ZLEVEL not in result.point_data


def test_transform_mesh__cloud_between_planar_crs(lifted_cloud):
    """A cloud moved between planar CRSs keeps its z-levels, not its z-values.

    Issue 2581: the planar z of the source was added to the levels as though it
    were a level, so z was scaled twice.

    """
    expected = transform_mesh(lifted_cloud.copy(), ROBIN)

    result = transform_mesh(transform_mesh(lifted_cloud.copy(), PLANAR), ROBIN)

    np.testing.assert_allclose(result.points, expected.points, rtol=1e-9)


def test_transform_mesh__cloud_subset_keeps_its_levels(lifted_cloud):
    """Each point of a planar cloud carries its own z-level, through a subset.

    A level decoded from the planar z would depend on the extent of the cloud,
    which a subset changes, so the levels travel as point data instead.

    """
    planar = transform_mesh(lifted_cloud, PLANAR)
    subset = planar.extract_points([1, 2], adjacent_cells=False).cast_to_poly_points()

    result = transform_mesh(subset, WGS84)

    np.testing.assert_allclose(result.points, lifted_cloud.points[1:], rtol=1e-9)


def test_transform_mesh__cloud_levels_are_not_scalars(cloud):
    """The z-levels a planar cloud carries never become its active scalars.

    A cloud with no data of its own renders in a single colour, which active
    scalars would replace with a colour map of its levels.

    """
    result = transform_mesh(cloud, PLANAR)

    assert GV_POINT_ZLEVEL in result.point_data
    assert result.active_scalars_name is None


@pytest.mark.parametrize(
    ("radius", "expected"), [(None, 2.0), (3.0, 3.0)], ids=["carried", "given"]
)
def test_transform_mesh__cloud_returns_to_its_radius(radius, expected):
    """A cloud returns to WGS84 on the radius it carries, unless given another.

    Issue 2581: ``zscale`` defaulted to the cloud's own but ``radius`` did not, so
    a cloud of radius 2 came back on the unit sphere.

    """
    cloud = gv.Transform.from_points([10.0, 20.0, 30.0], [30.0, 40.0, 50.0], radius=2.0)
    planar = transform_mesh(cloud, PLANAR)

    result = transform_mesh(planar, WGS84, radius=radius)

    radii = np.linalg.norm(result.points, axis=1)
    np.testing.assert_allclose(radii, expected, rtol=1e-12)
    np.testing.assert_allclose(result.points / expected, cloud.points / 2.0, rtol=1e-9)


@pytest.mark.parametrize(
    ("override", "radius", "zscale"),
    [({"radius": 3.0}, 3.0, 0.5), ({"zscale": 0.25}, 1.0, 0.25)],
    ids=["radius", "zscale"],
)
def test_transform_mesh__cloud_carries_the_radius_and_zscale_given(
    lifted_cloud, override, radius, zscale
):
    """A cloud carries the radius or zscale that a transform to WGS84 was given.

    Later transforms decode the levels of a cloud from its radius, and default to
    its radius and zscale, so the values it carries must be those that placed it.

    """
    sphere = transform_mesh(transform_mesh(lifted_cloud, PLANAR), WGS84, **override)
    planar = transform_mesh(sphere, ROBIN)

    result = transform_mesh(planar, WGS84)

    levels = np.array([2.0, 3.0, 4.0])
    np.testing.assert_allclose(planar.point_data[GV_POINT_ZLEVEL], levels, rtol=1e-9)
    radii = np.linalg.norm(result.points, axis=1)
    np.testing.assert_allclose(radii, radius * (1 + levels * zscale), rtol=1e-9)


def test_transform_mesh__cloud_carries_the_zscale_given_in_a_planar_crs(lifted_cloud):
    """A cloud carries the zscale that a transform to a planar CRS was given."""
    planar = transform_mesh(lifted_cloud, PLANAR, zscale=0.25)

    result = transform_mesh(planar, WGS84)

    radii = np.linalg.norm(result.points, axis=1)
    np.testing.assert_allclose(radii, 1 + np.array([2.0, 3.0, 4.0]) * 0.25, rtol=1e-9)


@pytest.mark.parametrize(
    "extent",
    [(-180, 180, -90, 90), (0, 40, 30, 50), (0, 10, 40, 45), (40, 50, 30, 50)],
    ids=["global", "regional", "small", "tile"],
)
def test_transform_mesh__zlevel_ignores_the_extent(extent):
    """A level sits at one height in a planar CRS, whatever the extent of the mesh.

    Issue 2588: the offset scaled with a quarter of the mesh's own extent, so meshes
    of different sizes at the same level sat at different heights.

    """
    result = transform_mesh(_quad(*extent), PLANAR, zlevel=1)

    expected = ZLEVEL_SCALE * SEMI_MAJOR
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-12)


def test_transform_mesh__zlevel_orders_layers_across_extents():
    """A small mesh at a higher level sits above a global mesh at a lower one."""
    upper = transform_mesh(_quad(0, 10, 40, 45), PLANAR, zlevel=2)
    lower = transform_mesh(_quad(-180, 180, -90, 90), PLANAR, zlevel=1)

    assert upper.points[:, 2].min() > lower.points[:, 2].max()


def test_transform_mesh__zlevel_in_degrees_survives_a_small_extent():
    """A small mesh in a CRS measured in degrees is lifted, not left at zero."""
    result = transform_mesh(_quad(0, 3, 40, 42), "EPSG:4269", zlevel=5)

    expected = 5 * ZLEVEL_SCALE * np.degrees(1.0)
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-12)


def test_transform_mesh__cloud_feature_keeps_the_depths_of_the_whole():
    """A feature taken from a cloud sits at the depths it has in the whole cloud.

    Issue 2588: an oceanographer plotting eddies extracted from an ORCA2 cloud saw
    each feature's depths compressed, since a smaller cloud brought a smaller scale.

    """
    lons, lats = np.linspace(-60.0, 20.0, 9), np.linspace(10.0, 70.0, 9)
    depths = -np.linspace(0.0, 5000.0, 9)
    whole = gv.Transform.from_points(lons, lats, zlevel=depths, zscale=1e-5)
    part = slice(3, 5)
    feature = gv.Transform.from_points(
        lons[part], lats[part], zlevel=depths[part], zscale=1e-5
    )
    expected = transform_mesh(whole, PLANAR).points[part, 2]

    result = transform_mesh(feature, PLANAR)

    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)


def test_transform_mesh__zlevel_is_the_proportion_the_globe_gives(lifted_cloud):
    """A planar z is the proportion of the Earth's radius the sphere lifts it by."""
    lifts = np.linalg.norm(lifted_cloud.points, axis=1) - 1

    result = transform_mesh(lifted_cloud, PLANAR)

    np.testing.assert_allclose(result.points[:, 2] / SEMI_MAJOR, lifts, rtol=1e-9)


@pytest.mark.parametrize(
    ("crs", "extent", "radius"),
    [
        ("+proj=eqc +units=km", (-75, -73, 40, 41), SEMI_MAJOR / 1000),
        ("EPSG:2263", (-75, -73, 40, 41), SEMI_MAJOR / 0.3048006096012192),
        ("EPSG:4269", (-75, -73, 40, 41), np.degrees(1.0)),
        ("EPSG:7405", (-3, -1, 52, 53), AIRY),
    ],
    ids=["kilometre", "us-survey-foot", "degree", "compound"],
)
def test_transform_mesh__zlevel_in_the_units_of_the_crs(crs, extent, radius):
    """The offset is the radius of the Earth, measured in the units of the CRS."""
    result = transform_mesh(_quad(*extent), crs, zlevel=1)

    np.testing.assert_allclose(result.points[:, 2], ZLEVEL_SCALE * radius, rtol=1e-9)


def test_transform_mesh__zlevel_in_a_rotated_pole_crs():
    """A rotated pole CRS is geographic, so the offset is one radian in degrees.

    geovista cannot find the central meridian of a rotated pole CRS, and warns
    that it assumes 0, as ``test_central_meridian__rotated_pole_warns`` pins.

    """
    crs = ccrs.RotatedPole(pole_longitude=MERIDIAN, pole_latitude=45)

    with pytest.warns(UserWarning, match="central meridian"):
        result = transform_mesh(_quad(-75, -73, 40, 41), crs, zlevel=1)

    expected = ZLEVEL_SCALE * np.degrees(1.0)
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)


def test_transform_mesh__zlevel_in_a_crs_declared_in_radians():
    """A geographic CRS declared in radians is offset in degrees, as its points are.

    ``pyproj`` returns the coordinates of a geographic CRS declared in radians in
    degrees, so the radius that matches them is one radian in degrees, 57.2958,
    rather than 1.

    """
    result = transform_mesh(_quad(-75, -73, 40, 41), CRS.from_wkt(RADIANS), zlevel=1)

    xs = result.points[:, 0]
    np.testing.assert_allclose([xs.min(), xs.max()], [-75, -73], rtol=1e-12)
    expected = ZLEVEL_SCALE * np.degrees(1.0)
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-12)


def test_transform_mesh__zlevel_with_a_shifted_meridian():
    """A target CRS rebased for its central meridian keeps its ellipsoid and unit.

    ``transform_mesh`` rebuilds such a CRS with its central meridian at 0 before it
    slices. The Airy ellipsoid in kilometres differs from the defaults a rebuild
    could fall back to, so one that lost either would show here.

    """
    crs = f"{PLANAR} +ellps=airy +units=km +lon_0={REGIONAL_MERIDIAN}"

    result = transform_mesh(_quad(0, 10, 40, 45), crs, zlevel=1)

    expected = ZLEVEL_SCALE * AIRY / 1000
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-12)


def test_transform_mesh__data_above_the_coastlines_whatever_its_extent():
    """Data raised above the default level of the coastlines draws above them.

    On a planar CRS the plotter adds its base layer at zlevel -1 with a zscale of
    1e-3, and its coastlines at zlevel 3, both over the whole globe. Issue 2588: a
    small dataset at zlevel 4 still drew beneath them.

    """
    world = _quad(-180, 180, -90, 90)
    base = transform_mesh(world.copy(), PLANAR, zlevel=-1, zscale=1e-3)
    coastlines = transform_mesh(world.copy(), PLANAR, zlevel=3)

    data = transform_mesh(_quad(0, 10, 40, 45), PLANAR, zlevel=4)

    assert base.points[:, 2].max() < coastlines.points[:, 2].min()
    assert coastlines.points[:, 2].max() < data.points[:, 2].min()


def test_transform_mesh__cloud_between_units(lifted_cloud):
    """A cloud moved from metres to kilometres keeps its depths in proportion."""
    metres = transform_mesh(lifted_cloud.copy(), PLANAR)

    result = transform_mesh(metres, "+proj=eqc +units=km")

    expected = metres.points[:, 2] / 1000
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)

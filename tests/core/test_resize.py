# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.core.resize`."""

from __future__ import annotations

import operator

import numpy as np
from numpy.testing import assert_array_equal
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import (
    _GV_GLOBE_FIELDS,
    GV_FIELD_GLOBE_RENDER_RADIUS,
    GV_FIELD_RADIUS,
    GV_FIELD_ZSCALE,
    RADIUS,
    ZLEVEL_SCALE,
    distance,
    from_cartesian,
)
from geovista.core import resize
from geovista.globe import Globe
from geovista.pantry.meshes import lfric_orog

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]


def test_projection_fail():
    """Test trap of mesh that is not spherical."""
    mesh = pv.Plane()
    emsg = "Cannot resize a mesh that has been projected"
    with pytest.raises(ValueError, match=emsg):
        _ = resize(mesh)


@pytest.mark.parametrize("lfric", ["c48", "c96", "c192"], indirect=True)
def test_no_resize(lfric):
    """Test resize not performed for a mesh at, and recording, its globe."""
    Globe().to_mesh(lfric)
    result = resize(lfric)
    assert id(result) == id(lfric)
    assert_array_equal(result.points, lfric.points)


def test_records_a_globe_on_a_mesh_with_none(lfric):
    """Test a mesh that records no globe is given one, on a copy."""
    for name in _GV_GLOBE_FIELDS:
        lfric.field_data.pop(name, None)
    result = resize(lfric)
    assert id(result) != id(lfric)
    assert_array_equal(result.points, lfric.points)
    assert Globe.from_mesh(result) == Globe()
    assert GV_FIELD_GLOBE_RENDER_RADIUS not in lfric.field_data


@pytest.mark.parametrize("inplace", [False, True])
@pytest.mark.parametrize(
    "radius",
    tuple(
        np.round(value, decimals=1)
        for value in np.linspace(RADIUS / 10, 2 * RADIUS, 20)
    ),
)
def test_resize(lfric, radius, inplace):
    """Test resize mesh by new radius."""
    result = resize(lfric, globe=Globe(render_radius=radius), inplace=inplace)
    # a mesh at, and recording, the globe is returned as it is
    compare = operator.eq if inplace or radius == RADIUS else operator.ne
    assert compare(id(result), id(lfric))
    assert np.isclose(distance(result), radius)


@pytest.mark.parametrize("zlevel", range(-10, 11))
def test_resize__zlevel(lfric, zlevel):
    """Test resize mesh by new zlevel."""
    result = resize(lfric, zlevel=zlevel)
    expected = RADIUS + RADIUS * zlevel * ZLEVEL_SCALE
    # a z-level of 0 leaves the mesh at, and recording, its globe
    assert (id(result) == id(lfric)) == (zlevel == 0)
    actual = distance(result)
    assert np.isclose(actual, expected)


@pytest.mark.parametrize("zscale", np.linspace(-1, 1))
def test_resize__zscale(lfric, zscale):
    """Test resize mesh by new zscale."""
    result = resize(lfric, zlevel=1, zscale=zscale)
    expected = RADIUS + RADIUS * zscale or RADIUS
    # a radius of 0 is refused, which leaves the mesh at, and recording, its globe
    assert (id(result) == id(lfric)) == (RADIUS + RADIUS * zscale == 0)
    actual = distance(result)
    assert np.isclose(actual, expected)


def test_resize_cloud__inject_metadata(lam_uk):
    """Test inclusion of field data metadata."""
    cloud = pv.PolyData(lam_uk.points)
    assert GV_FIELD_GLOBE_RENDER_RADIUS not in cloud.field_data
    assert GV_FIELD_ZSCALE not in cloud.field_data
    result = resize(cloud)
    assert GV_FIELD_RADIUS not in result.field_data
    assert GV_FIELD_ZSCALE in result.field_data
    assert id(cloud) != id(result)
    assert Globe.from_mesh(result) == Globe()
    assert np.isclose(result[GV_FIELD_ZSCALE], ZLEVEL_SCALE)


@pytest.mark.parametrize("zlevel", range(1, 11))
def test_resize_cloud__zlevel(lam_uk_sample, zlevel):
    """Test resize cloud points by new zlevel."""
    lons, lats = lam_uk_sample
    zscale = 1
    cloud = Transform.from_points(lons, lats, zscale=zscale)
    assert Globe.from_mesh(cloud) == Globe()
    assert np.isclose(cloud[GV_FIELD_ZSCALE], zscale)
    result = resize(cloud, zlevel=zlevel)
    assert np.isclose(distance(result), RADIUS + zlevel * zscale)
    assert id(cloud) != id(result)


@pytest.mark.parametrize("zscale", np.linspace(-1, 1))
def test_resize_cloud__zscale(lam_uk_cloud, zscale):
    """Test resize cloud points by new zscale."""
    zlevel = 1
    assert Globe.from_mesh(lam_uk_cloud) == Globe()
    assert np.isclose(lam_uk_cloud[GV_FIELD_ZSCALE], ZLEVEL_SCALE)
    result = resize(lam_uk_cloud, zlevel=zlevel, zscale=zscale)
    assert np.isclose(distance(result), RADIUS + zlevel * zscale)
    assert Globe.from_mesh(result) == Globe()
    assert np.isclose(result[GV_FIELD_ZSCALE], zscale)
    assert id(lam_uk_cloud) != id(result)


@pytest.mark.parametrize("radius", np.linspace(0.5, 1.5))
def test_resize_cloud__radius(lam_uk_cloud, radius):
    """Test resize cloud points by new radius."""
    assert Globe.from_mesh(lam_uk_cloud) == Globe()
    assert np.isclose(lam_uk_cloud[GV_FIELD_ZSCALE], ZLEVEL_SCALE)
    result = resize(lam_uk_cloud, globe=Globe(render_radius=radius))
    assert np.isclose(distance(result), radius)
    assert Globe.from_mesh(result) == Globe(render_radius=radius)
    assert np.isclose(result[GV_FIELD_ZSCALE], ZLEVEL_SCALE)


@pytest.mark.parametrize("radius", RADII)
def test_resize_cloud__a_nearby_globe(radius):
    """Test a cloud resized to a globe close to its own keeps its z-levels.

    Its z-levels are read from the render radius it records, so a globe within the
    tolerance of that radius still moves its points.

    """
    zlevel = [1, 2, 3]
    cloud = Transform.from_points(
        [0, 10, 20], [0, 10, 20], globe=Globe(render_radius=radius), zlevel=zlevel
    )
    globe = Globe(render_radius=radius * 1.000009)

    result = resize(cloud, globe=globe)

    np.testing.assert_allclose(from_cartesian(result)[:, 2], zlevel)
    expected = globe.render_radius * (1 + np.asarray(zlevel) * ZLEVEL_SCALE)
    np.testing.assert_allclose(distance(result, mean=False), expected, rtol=1e-12)
    assert Globe.from_mesh(result) == globe


@pytest.mark.parametrize("zlevel", [[1, 2, 3], (1, 2, 3), np.array([1, 2, 3])])
def test_resize_cloud__zlevel_per_point(zlevel):
    """Test resize cloud points by a z-level at each point."""
    zscale = 1
    cloud = Transform.from_points([0, 10, 20], [0, 10, 20], zscale=zscale)
    result = resize(cloud, zlevel=zlevel)
    expected = RADIUS + RADIUS * np.asarray(zlevel) * zscale
    assert np.allclose(distance(result, mean=False), expected)
    assert Globe.from_mesh(result) == Globe()
    assert np.isclose(result[GV_FIELD_ZSCALE], zscale)
    assert id(cloud) != id(result)


def test_resize_cloud__zlevel_per_point_adds():
    """Test resize adds a z-level at each point to the level it carries."""
    zscale = 1
    cloud = Transform.from_points(
        [0, 10, 20], [0, 10, 20], zlevel=[1, 2, 3], zscale=zscale
    )
    result = resize(cloud, zlevel=np.array([3, 2, 1]))
    assert np.allclose(distance(result, mean=False), RADIUS + RADIUS * 4 * zscale)


def test_resize_cloud__zlevel_broadcast():
    """Test resize cloud points by a z-level that broadcasts to the points."""
    zscale = 1
    cloud = Transform.from_points([0, 10, 20], [0, 10, 20], zscale=zscale)
    result = resize(cloud, zlevel=np.array([2]))
    assert np.allclose(distance(result, mean=False), RADIUS + RADIUS * 2 * zscale)


def test_resize_cloud__zlevel_single_point():
    """Test resize a one point cloud by a one element z-level."""
    zscale = 1
    cloud = Transform.from_points([0], [0], zscale=zscale)
    result = resize(cloud, zlevel=np.array([2]))
    assert np.allclose(distance(result, mean=False), RADIUS + RADIUS * 2 * zscale)


def test_resize_cloud__zlevel_zeros(lam_uk_cloud):
    """Test resize not performed for a z-level of zero at each point."""
    result = resize(lam_uk_cloud, zlevel=np.zeros(lam_uk_cloud.n_points))
    assert id(result) == id(lam_uk_cloud)


def test_resize_cloud__zlevel_shape_fail():
    """Test trap of a z-level that does not broadcast to the cloud points."""
    cloud = Transform.from_points([0, 10, 20], [0, 10, 20])
    emsg = r"Cannot resize mesh, 'zlevel' with shape \(2,\) does not broadcast"
    with pytest.raises(ValueError, match=emsg):
        _ = resize(cloud, zlevel=[1, 2])


def test_resize__zlevel_per_point(lfric):
    """Test resize a surface by a z-level at each point, keeping where it is."""
    level = np.linspace(-10, 10, lfric.n_points)
    result = resize(lfric, zlevel=level)
    expected = RADIUS + RADIUS * level * ZLEVEL_SCALE
    assert np.allclose(distance(result, mean=False), expected)
    assert np.allclose(from_cartesian(result), from_cartesian(lfric))


def test_resize__zlevel_per_point_replaces(lfric):
    """Test a surface lifted at each point takes new levels, not the sum of both.

    A scalar z-level resizes a surface to that level whatever level it was at,
    so a z-level at each point does the same, which needs the surface's points
    read back at their own radii (#2688).

    """
    first = np.linspace(-10, 10, lfric.n_points)
    second = first[::-1]
    result = resize(resize(lfric, zlevel=first), zlevel=second)
    assert np.allclose(result.points, resize(lfric, zlevel=second).points)


@pytest.mark.parametrize("zlevel", [[1], np.array([1])])
def test_resize__zlevel_one_element(lfric, zlevel):
    """Test resize a surface alike by a scalar and a one element z-level."""
    result = resize(lfric, zlevel=zlevel)
    scalar = resize(lfric, zlevel=1)
    assert np.allclose(result.points, scalar.points)
    assert Globe.from_mesh(result) == Globe.from_mesh(scalar)


def test_resize__zlevel_per_point_zeros(lfric):
    """Test no resize of a surface already at the levels it is given."""
    Globe().to_mesh(lfric)
    result = resize(lfric, zlevel=np.zeros(lfric.n_points))
    assert id(result) == id(lfric)


def test_levels_at_each_point_keep_the_globe(lfric):
    """Test a surface at a z-level for each point records the globe they offset."""
    globe = Globe(render_radius=2, exaggeration=20)
    level = np.arange(lfric.n_points) % 3
    result = resize(lfric, globe=globe, zlevel=level)
    assert Globe.from_mesh(result) == globe
    assert GV_FIELD_RADIUS not in result.field_data
    np.testing.assert_allclose(
        distance(result, mean=False), 2 * (1 + level * ZLEVEL_SCALE), rtol=1e-6
    )


@pytest.mark.parametrize("zlevel", [0, [0]])
def test_resize__zlevel_flattens_an_uneven_surface(lfric, zlevel):
    """Test a surface lifted at each point is flattened by a scalar z-level.

    Its mean radius already matches the target, so only its points show it
    needs resizing.

    """
    lifted = resize(lfric, zlevel=np.linspace(-10, 10, lfric.n_points))
    result = resize(lifted, zlevel=zlevel)
    assert np.allclose(distance(result, mean=False), RADIUS)
    assert np.allclose(from_cartesian(result), from_cartesian(lfric))


def test_resize__zlevel_shape_fail(lfric):
    """Test trap of a z-level that does not broadcast to the points of a surface."""
    emsg = r"Cannot resize mesh, 'zlevel' with shape \(2,\) does not broadcast"
    with pytest.raises(ValueError, match=emsg):
        _ = resize(lfric, zlevel=[1, 2])


@pytest.mark.parametrize("zlevel", [0.5, np.float64(1.7), np.array(-2.5)])
def test_resize__zlevel_float(lfric, zlevel):
    """Test resize mesh by a z-level that is not a whole number."""
    result = resize(lfric, zlevel=zlevel)
    expected = RADIUS + RADIUS * float(zlevel) * ZLEVEL_SCALE
    assert np.isclose(distance(result), expected)


def test_resize_cloud__zlevel_float():
    """Test resize cloud points alike by a scalar and a one element z-level."""
    cloud = Transform.from_points([0, 10, 20], [0, 10, 20], zscale=1)
    scalar = resize(cloud, zlevel=0.5)
    array = resize(cloud, zlevel=[0.5])
    assert np.allclose(distance(scalar, mean=False), RADIUS + RADIUS * 0.5)
    assert np.allclose(scalar.points, array.points)


def test_resize__zlevel_0d(lfric):
    """Test resize mesh by a z-level given as a 0-d array."""
    result = resize(lfric, zlevel=np.array(2))
    expected = RADIUS + RADIUS * 2 * ZLEVEL_SCALE
    assert np.isclose(distance(result), expected)


@pytest.mark.parametrize("radius", RADII)
def test_records_the_globe(lfric, radius):
    """Test a mesh resized to a globe lies at, and records, it."""
    globe = Globe(render_radius=radius)
    result = resize(lfric, globe=globe)
    np.testing.assert_allclose(distance(result, mean=False), radius, rtol=1e-6)
    assert Globe.from_mesh(result) == globe
    assert GV_FIELD_RADIUS not in result.field_data


def test_records_on_a_copy():
    """Test a globe is recorded on a copy, unless in place, even if no point moves."""
    mesh = Transform.from_1d([0.0, 10.0, 20.0], [0.0, 10.0])
    globe = Globe(exaggeration=20)
    result = resize(mesh, globe=globe)
    assert result is not mesh
    assert_array_equal(result.points, mesh.points)
    assert Globe.from_mesh(result) == globe
    assert Globe.from_mesh(mesh) == Globe()
    assert resize(mesh, globe=globe, inplace=True) is mesh
    assert Globe.from_mesh(mesh) == globe


def test_defaults_to_the_globe_the_mesh_records():
    """Test a mesh is resized on the globe it records when given none."""
    globe = Globe(render_radius=2)
    mesh = Transform.from_1d([0.0, 10.0, 20.0], [0.0, 10.0], globe=globe)
    result = resize(mesh, zlevel=1)
    np.testing.assert_allclose(
        distance(result, mean=False), 2 * (1 + ZLEVEL_SCALE), rtol=1e-12
    )
    assert Globe.from_mesh(result) == globe


def test_a_mesh_with_no_globe_is_resized_to_the_default():
    """Test a mesh with no globe, as one warped by its heights, takes the default."""
    mesh = lfric_orog()
    for name in _GV_GLOBE_FIELDS:
        del mesh.field_data[name]
    mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
    mesh.warp_by_scalar(inplace=True, factor=2e-5)
    assert Globe.from_mesh(mesh) is None
    result = resize(mesh)
    np.testing.assert_allclose(distance(result, mean=False), RADIUS, rtol=1e-6)
    assert Globe.from_mesh(result) == Globe()


def test_a_number_is_not_a_globe(lfric):
    """Test a number given as the globe is refused."""
    with pytest.raises(TypeError, match=r"geovista\.Globe"):
        resize(lfric, globe=2.0)


def test_radius_is_gone(lfric):
    """Test the radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        resize(lfric, radius=2.0)


#: The cell bounds of a small grid, and its points in the order the bridge builds.
HEIGHT_XS, HEIGHT_YS = [0.0, 10.0, 20.0], [0.0, 10.0]
HEIGHT_LONS, HEIGHT_LATS = (
    np.ravel(axis) for axis in np.meshgrid(HEIGHT_XS, HEIGHT_YS, indexing="xy")
)

#: A height for each point, above and below sea level, at it, and one missing.
HEIGHTS = np.array([1000.0, -4000.0, np.nan, 250.0, 0.0, -10.0])

#: A globe that exaggerates heights above and below sea level by their own factors.
EXAGGERATED = {"exaggeration": 20, "exaggeration_below": 100}


@pytest.mark.parametrize("radius", RADII)
def test_heights_placed_by_the_formula(radius, at_heights):
    """A mesh with heights is resized to s (R + V(h)) at the new globe."""
    mesh = Transform.from_1d(HEIGHT_XS, HEIGHT_YS, height=HEIGHTS)
    globe = Globe(render_radius=radius, **EXAGGERATED)
    result = resize(mesh, globe=globe)
    np.testing.assert_allclose(
        result.points,
        at_heights(HEIGHT_LONS, HEIGHT_LATS, HEIGHTS, globe),
        rtol=1e-9,
        atol=1e-9 * radius,
    )
    assert Globe.from_mesh(result) == globe
    assert_array_equal(result.gv.height, HEIGHTS)


def test_a_new_mapping_moves_by_the_formula():
    """A new exaggeration moves points by the formula, however little."""
    earth = Globe(render_radius=6378137.0)
    mesh = Transform.from_1d(HEIGHT_XS, HEIGHT_YS, height=1.0, globe=earth)
    result = resize(mesh, globe=Globe(render_radius=6378137.0, exaggeration=2))
    moved = np.linalg.norm(result.points, axis=1) - np.linalg.norm(mesh.points, axis=1)
    np.testing.assert_allclose(moved, 1.0, atol=1e-6)


def test_heights_lift_once():
    """A mesh with heights all equal, and no globe, is lifted once."""
    mesh = Transform.from_1d(HEIGHT_XS, HEIGHT_YS, height=1000.0)
    for name in _GV_GLOBE_FIELDS:
        del mesh.field_data[name]
    assert Globe.from_mesh(mesh) is None
    result = resize(mesh)
    np.testing.assert_allclose(
        np.linalg.norm(result.points, axis=1), 1.0 + 1000.0 / 6378137.0, rtol=1e-12
    )


def test_the_same_globe_returns_the_mesh():
    """A mesh with heights that records the globe asked for is returned as given."""
    mesh = Transform.from_1d(HEIGHT_XS, HEIGHT_YS, height=HEIGHTS)
    assert resize(mesh) is mesh
    assert resize(mesh, globe=Globe()) is mesh


def test_the_same_globe_rebuilds_misplaced_points():
    """A mesh whose points disagree with its heights is rebuilt from them."""
    globe = Globe(exaggeration=20, exaggeration_below=100)
    mesh = Transform.from_1d(HEIGHT_XS, HEIGHT_YS, height=HEIGHTS, globe=globe)
    expected = mesh.points.copy()
    mesh.points = mesh.points * 1.001
    result = resize(mesh, globe=globe)
    assert result is not mesh
    np.testing.assert_allclose(result.points, expected, rtol=1e-12)


def test_a_zlevel_is_refused_with_heights():
    """A mesh with heights takes no z-level other than 0."""
    mesh = Transform.from_1d(HEIGHT_XS, HEIGHT_YS, height=HEIGHTS)
    with pytest.raises(ValueError, match="z-level"):
        resize(mesh, zlevel=1)
    assert resize(mesh, zlevel=0) is mesh


@pytest.mark.parametrize("radius", RADII)
def test_a_cloud_with_heights(radius, at_heights):
    """A cloud with heights is resized by the formula, and carries no z-level."""
    lons, lats = [0.0, 10.0, 20.0, 30.0], [0.0, 5.0, 10.0, 15.0]
    heights = HEIGHTS[:4]
    cloud = Transform.from_points(lons, lats, height=heights)
    globe = Globe(render_radius=radius, **EXAGGERATED)
    result = resize(cloud, globe=globe)
    np.testing.assert_allclose(
        result.points,
        at_heights(lons, lats, heights, globe),
        rtol=1e-9,
        atol=1e-9 * radius,
    )
    assert GV_FIELD_ZSCALE not in result.field_data


def test_missing_heights_at_sea_level():
    """A missing height is resized to the render radius."""
    mesh = Transform.from_1d(HEIGHT_XS, HEIGHT_YS, height=HEIGHTS)
    result = resize(mesh, globe=Globe(render_radius=2))
    np.testing.assert_allclose(np.linalg.norm(result.points[2]), 2.0, rtol=1e-12)

# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_mesh`."""

from __future__ import annotations

import cartopy.crs as ccrs
import numpy as np
from pyproj import Transformer
import pytest
import pyvista as pv

import geovista as gv
from geovista.bridge import Transform
from geovista.common import (
    _GV_GLOBE_FIELDS,
    GV_FIELD_RADIUS,
    GV_POINT_HEIGHT,
    RADIUS,
    ZLEVEL_SCALE,
    distance,
    from_cartesian,
)
from geovista.crs import WGS84, from_wkt, to_wkt
from geovista.geoplotter import OPACITY_BLACKLIST, GeoPlotter
from geovista.globe import Globe
from geovista.pantry.meshes import lfric_orog
from geovista.transform import transform_mesh


def test_no_opacity_kwarg(lfric, mocker):
    """Test with no opacity render request."""
    p = GeoPlotter()
    spy = mocker.spy(p, "_warn_opacity")
    p.add_mesh(lfric)
    assert spy.call_count == 0
    assert p._missing_opacity is False


@pytest.mark.parametrize("key", ["opacity", "nan_opacity"])
@pytest.mark.parametrize("value", [None, 0.5])
def test_gpu_opacity_available(lfric, mocker, key, value):
    """Test with a mock gpu supporting opacity."""
    renderer = mocker.sentinel.renderer
    version = mocker.sentinel.version
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    p = GeoPlotter()
    spy = mocker.spy(p, "add_text")
    kwargs = {key: value}
    p.add_mesh(lfric, **kwargs)
    assert spy.call_count == 0
    assert p._missing_opacity is False


@pytest.mark.parametrize("key", ["opacity"])
@pytest.mark.parametrize("value", [None, 0.5])
def test_gpu_opacity_unavailable(lfric, mocker, key, value):
    """Test with a mock gpu not supporting opacity."""
    renderer, version = OPACITY_BLACKLIST[0]
    minfo = mocker.MagicMock(renderer=renderer, version=version)
    _ = mocker.patch("pyvista.GPUInfo", return_value=minfo)
    p = GeoPlotter()
    spy = mocker.spy(p, "add_text")
    kwargs = {key: value}
    p.add_mesh(lfric, **kwargs)
    if value is None:
        assert spy.call_count == 0
        assert p._missing_opacity is False
    else:
        assert spy.call_count == 1
        args = ("Requires GPU opacity support",)
        kwargs = {
            "position": "lower_right",
            "font_size": 7,
            "color": "red",
            "shadow": True,
        }
        spy.assert_called_once_with(*args, **kwargs)
        assert p._missing_opacity is True


def test_flat_mesh_zlevel():
    """Test that a flat mesh is not resized as a sphere.

    An already flat mesh added to a scene with the same flat CRS must not be
    radially rescaled by ``zlevel``, which would distort its lon/lat extent.
    See :issue:`2522`.

    """
    lons, lats = np.linspace(10, 30, 3), np.linspace(30, 50, 3)
    data = np.arange(4, dtype=float).reshape(2, 2)
    sphere = gv.Transform.from_1d(lons, lats, data=data)
    flat = transform_mesh(sphere, ccrs.PlateCarree())
    expected = flat.bounds[:4]

    p = GeoPlotter(crs=ccrs.PlateCarree())
    p.add_mesh(flat, zlevel=1)

    assert p.mesh.bounds[:4] == pytest.approx(expected)


def test_empty_mesh_returns_none():
    """An empty mesh is not added, and nothing is returned for it."""
    p = GeoPlotter()

    assert p.add_mesh(pv.PolyData()) is None
    assert not p.actors


def test_central_meridian_recentred(lfric):
    """A mesh is sliced and transformed for a CRS with a central meridian."""
    p = GeoPlotter(crs="+proj=robin +lon_0=180")

    actor = p.add_mesh(lfric)

    assert actor is not None
    assert from_wkt(actor.mapper.dataset) == p.crs


@pytest.mark.parametrize("zlevel", [[1, 2, 3], (1, 2, 3), np.array([1, 2, 3])])
def test_cloud_zlevel_per_point(zlevel):
    """A cloud that needs no transform is lifted by a z-level at each point.

    See :issue:`2618`.

    """
    zscale = 1
    cloud = gv.Transform.from_points([0, 10, 20], [0, 10, 20], zscale=zscale)
    p = GeoPlotter()

    actor = p.add_mesh(cloud, zlevel=zlevel)

    assert actor is not None
    expected = RADIUS + RADIUS * np.asarray(zlevel) * zscale
    assert np.allclose(distance(actor.mapper.dataset, mean=False), expected)


def test_cloud_zlevel_single_point():
    """A one point cloud is lifted by a one element z-level. See :issue:`2618`."""
    zscale = 1
    cloud = gv.Transform.from_points([0], [0], zscale=zscale)
    p = GeoPlotter()

    actor = p.add_mesh(cloud, zlevel=np.array([2]))

    assert actor is not None
    expected = RADIUS + RADIUS * 2 * zscale
    assert np.allclose(distance(actor.mapper.dataset, mean=False), expected)


def test_surface_zlevel_array():
    """A surface that needs no transform is lifted at each point, as when it does.

    See :issue:`2693`.

    """
    mesh = gv.Transform.from_1d([0, 10, 20], [0, 10, 20])
    level = np.arange(mesh.n_points)
    p = GeoPlotter()

    actor = p.add_mesh(mesh, zlevel=level)
    expected = RADIUS + RADIUS * level * ZLEVEL_SCALE
    assert np.allclose(distance(actor.mapper.dataset, mean=False), expected)


def test_surface_zlevel_array_texture():
    """A textured surface that needs no transform is lifted at each point.

    Its texture coordinates add points at the antimeridian, which take the
    level of the point they duplicate.

    """
    mesh = gv.Transform.from_1d(np.linspace(-180, 180, 9), [-20, 0, 20])
    level = 1 + np.abs(from_cartesian(mesh)[:, 1]) / 90
    texture = pv.Texture(np.zeros((8, 16, 3), dtype=np.uint8))
    p = GeoPlotter()

    actor = p.add_mesh(mesh, zlevel=level, texture=texture)
    result = actor.mapper.dataset
    expected = 1 + np.abs(from_cartesian(result)[:, 1]) / 90
    assert result.n_points > mesh.n_points
    assert np.allclose(
        distance(result, mean=False), RADIUS + RADIUS * expected * ZLEVEL_SCALE
    )


@pytest.mark.parametrize("zlevel", [1, np.ones(12)])
def test_surface_zlevel_texture_cuts_cells(zlevel):
    """A textured surface is lifted whole where its seam cuts through cells.

    The cut interpolates new points along the chords of the cells it crosses,
    inside the sphere, so they are lifted with the rest, from the radius the
    surface had before the cut.

    """
    mesh = gv.Transform.from_1d([140, 160, 200, 220], [-20, 0, 20])
    texture = pv.Texture(np.zeros((8, 16, 3), dtype=np.uint8))
    p = GeoPlotter()

    actor = p.add_mesh(mesh, zlevel=zlevel, texture=texture)
    result = actor.mapper.dataset
    assert result.n_points > mesh.n_points
    assert np.allclose(distance(result, mean=False), RADIUS + RADIUS * ZLEVEL_SCALE)


def test_surface_texture_cuts_cells():
    """A textured surface at no level keeps the points its seam adds on the sphere.

    See :issue:`2708`.

    """
    mesh = gv.Transform.from_1d([140, 160, 200, 220], [-20, 0, 20])
    texture = pv.Texture(np.zeros((8, 16, 3), dtype=np.uint8))
    p = GeoPlotter()

    actor = p.add_mesh(mesh, texture=texture)
    result = actor.mapper.dataset
    assert result.n_points > mesh.n_points
    assert np.allclose(distance(result, mean=False), RADIUS)


def test_surface_zlevel_array_texture_cuts_cells():
    """A textured surface lifted at each point lifts the points its seam adds.

    Each added point takes a level between those of the points it lies between.

    """
    mesh = gv.Transform.from_1d([140, 160, 200, 220], [-20, 0, 20])
    level = 1 + np.abs(from_cartesian(mesh)[:, 1]) / 90
    texture = pv.Texture(np.zeros((8, 16, 3), dtype=np.uint8))
    p = GeoPlotter()

    actor = p.add_mesh(mesh, zlevel=level, texture=texture)
    radii = distance(actor.mapper.dataset, mean=False)
    lowest, highest = RADIUS + RADIUS * np.array([level.min(), level.max()]) * (
        ZLEVEL_SCALE
    )
    assert actor.mapper.dataset.n_points > mesh.n_points
    assert np.all(radii >= lowest - 1e-12)
    assert np.all(radii <= highest + 1e-12)


def test_cloud_zlevel_zeros_shape_fail():
    """A z-level of zeros that doesn't broadcast to a cloud is refused.

    The same cloud and z-level are refused when the cloud needs a transform.

    """
    cloud = gv.Transform.from_points([0, 10, 20], [0, 10, 20])
    p = GeoPlotter()

    emsg = r"'zlevel' with shape \(5,\) does not broadcast"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_mesh(cloud, zlevel=np.zeros(5))


def test_surface_zlevel_0d():
    """A mesh that is no cloud is lifted by a z-level given as a 0-d array."""
    mesh = gv.Transform.from_1d([0, 10, 20], [0, 10, 20])
    radius = distance(mesh)
    p = GeoPlotter()

    actor = p.add_mesh(mesh, zlevel=np.array(2))

    assert actor is not None
    expected = radius + radius * 2 * ZLEVEL_SCALE
    assert np.isclose(distance(actor.mapper.dataset), expected)


@pytest.mark.parametrize("lon_0", [0, 90])
def test_surface_zlevel_follows_the_slice(lon_0):
    """A surface the seam cuts is lifted by a z-level at each point.

    The levels vary with latitude, so a level that landed on the wrong point of
    those the seam adds would show. See :issue:`2669`.

    """
    mesh = gv.Transform.from_1d(np.linspace(-180, 180, 9), np.linspace(-90, 90, 5))
    zlevel = 1 + np.abs(from_cartesian(mesh)[:, 1]) / 90
    crs = f"+proj=eqc +lon_0={lon_0}"
    p = GeoPlotter(crs=crs)

    actor = p.add_mesh(mesh, zlevel=zlevel)

    result = actor.mapper.dataset
    assert result.n_points > mesh.n_points
    inverse = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    _, lats = inverse.transform(result.points[:, 0], result.points[:, 1])
    # the semi-major axis of the GRS80 ellipsoid of the CRS is 6378137 m
    expected = (1 + np.abs(lats) / 90) * ZLEVEL_SCALE * 6378137
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)


@pytest.mark.parametrize(
    ("crs", "lons", "lats"),
    [
        ("EPSG:27700", [-3.0, 0.0, 1.9], [51.0, 52.0, 53.0]),
        ("EPSG:27572", [-1.0, 2.0, 5.0], [45.0, 47.0, 49.0]),
    ],
)
def test_datum_at_true_positions(crs, lons, lats):
    """A surface added to a plotter takes each datum shift where it is.

    See :issue:`2714`. The NTF (Paris) datum of Lambert zone II measures in grads
    from the Paris meridian, which the surface is moved in, and projected from.

    """
    mesh = gv.Transform.from_1d(lons, lats)
    expected = gv.Transform.from_1d(lons, lats)
    p = GeoPlotter(crs=crs)

    actor = p.add_mesh(mesh)

    xyz = from_cartesian(expected)
    x, y = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(
        xyz[:, 0], xyz[:, 1]
    )
    np.testing.assert_allclose(actor.mapper.dataset.points[:, 0], x, atol=1e-3)
    np.testing.assert_allclose(actor.mapper.dataset.points[:, 1], y, atol=1e-3)


#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]


def _surface(globe: Globe | None = None) -> pv.PolyData:
    """Build a small surface on the sphere, at the globe given."""
    return gv.Transform.from_1d([0.0, 10.0, 20.0], [0.0, 10.0], globe=globe)


@pytest.mark.parametrize("radius", RADII)
def test_drawn_at_the_scenes_globe(radius):
    """A mesh on another globe is drawn at the scene's, and records it."""
    p = GeoPlotter(globe=Globe(render_radius=radius))
    drawn = p.add_mesh(_surface()).mapper.dataset
    np.testing.assert_allclose(distance(drawn, mean=False), radius, rtol=1e-12)
    assert Globe.from_mesh(drawn) == p.globe


def test_drawing_leaves_the_mesh_unchanged():
    """The mesh given keeps its points and globe when drawn at another globe."""
    mesh = _surface()
    points = mesh.points.copy()
    GeoPlotter(globe=Globe(render_radius=2)).add_mesh(mesh)
    np.testing.assert_array_equal(mesh.points, points)
    assert Globe.from_mesh(mesh) == Globe()


def test_a_cloud_keeps_its_heights_in_proportion():
    """A cloud drawn at another globe keeps its heights, in proportion."""
    levels = np.array([1, 2, 3])
    cloud = gv.Transform.from_points(
        [0.0, 10.0, 20.0], [0.0, 10.0, 20.0], zlevel=levels, zscale=0.1
    )
    drawn = GeoPlotter(globe=Globe(render_radius=2)).add_mesh(cloud).mapper.dataset
    np.testing.assert_allclose(
        distance(drawn, mean=False), 2 * (1 + 0.1 * levels), rtol=1e-12
    )


def test_a_mesh_with_no_globe_is_drawn_where_it_is():
    """A mesh warped outside geovista is drawn at its own points, with no globe."""
    mesh = lfric_orog()
    for name in _GV_GLOBE_FIELDS:
        del mesh.field_data[name]
    mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
    mesh.warp_by_scalar(inplace=True, factor=2e-5)
    drawn = GeoPlotter(globe=Globe(render_radius=2)).add_mesh(mesh).mapper.dataset
    np.testing.assert_array_equal(drawn.points, mesh.points)
    assert Globe.from_mesh(drawn) is None


@pytest.mark.parametrize("factor", [0.5, 1.05])
@pytest.mark.parametrize("radius", RADII)
def test_a_shell_is_drawn_where_it_is(radius, factor):
    """A sphere that records no globe is drawn where it is, at any radius.

    Its points lie at one radius, which reads as a globe, but a shell above or
    below the scene's globe reads the same, so only a recorded globe is scaled.

    """
    shell = pv.Sphere(radius=radius * factor)
    to_wkt(shell, WGS84)
    drawn = GeoPlotter(globe=Globe(render_radius=radius)).add_mesh(shell)
    drawn = drawn.mapper.dataset
    np.testing.assert_array_equal(drawn.points, shell.points)
    assert not set(_GV_GLOBE_FIELDS) & set(drawn.field_data)


def test_a_legacy_mesh_at_another_radius_is_scaled(legacy):
    """A mesh with a gvRadius records its globe, so is drawn at the scene's."""
    old = legacy(_surface(), radius=0.5)
    old.points = old.points * 0.5
    drawn = GeoPlotter().add_mesh(old).mapper.dataset
    np.testing.assert_allclose(distance(drawn, mean=False), 1.0, rtol=1e-12)
    assert Globe.from_mesh(drawn) == Globe()


def test_on_a_map_only_the_record_changes():
    """A projected mesh on another globe keeps its points, and records the scene's."""
    planar = transform_mesh(_surface(), "+proj=eqc")
    p = GeoPlotter(crs="+proj=eqc", globe=Globe(render_radius=2))
    drawn = p.add_mesh(planar).mapper.dataset
    np.testing.assert_allclose(drawn.points, planar.points)
    assert Globe.from_mesh(drawn) == p.globe
    assert Globe.from_mesh(planar) == Globe()


def test_a_legacy_mesh_is_drawn_cleaned(legacy):
    """A mesh saved by 0.5 is drawn with only current fields, and keeps its own."""
    old = legacy(_surface())
    drawn = GeoPlotter().add_mesh(old).mapper.dataset
    assert GV_FIELD_RADIUS not in drawn.field_data
    assert Globe.from_mesh(drawn) == Globe()
    assert GV_FIELD_RADIUS in old.field_data


def test_a_zlevel_lifts_from_the_scenes_globe():
    """A z-level lifts a mesh from the scene's render radius (call 9 of the plan)."""
    drawn = GeoPlotter().add_mesh(_surface(Globe(render_radius=2)), zlevel=1)
    np.testing.assert_allclose(
        distance(drawn.mapper.dataset, mean=False), 1 + ZLEVEL_SCALE, rtol=1e-12
    )


def test_radius_is_gone():
    """The radius keyword is refused."""
    with pytest.raises(TypeError, match="radius"):
        GeoPlotter().add_mesh(_surface(), radius=1.0)


def test_drawing_a_projected_mesh_leaves_it_unchanged():
    """A projected mesh drawn in another CRS keeps its points, CRS and globe."""
    planar = transform_mesh(_surface(Globe(render_radius=2)), "+proj=eqc")
    points, crs = planar.points.copy(), from_wkt(planar)
    GeoPlotter().add_mesh(planar)
    np.testing.assert_array_equal(planar.points, points)
    assert from_wkt(planar) == crs
    assert Globe.from_mesh(planar) == Globe(render_radius=2)


def test_heights_on_a_map_scene():
    """A mesh with heights is drawn on a map at its heights, given no z-level."""
    mesh = Transform.from_1d(
        [0.0, 10.0, 20.0], [0.0, 10.0], height=[1000.0, -4000.0, np.nan, 250, 0, -10]
    )
    p = GeoPlotter(crs="+proj=eqc", off_screen=True)
    actor = p.add_mesh(mesh)
    drawn = actor.mapper.dataset
    np.testing.assert_allclose(
        drawn.points[:, 2], np.nan_to_num(drawn[GV_POINT_HEIGHT]), rtol=1e-12
    )
    assert np.any(drawn.points[:, 2])

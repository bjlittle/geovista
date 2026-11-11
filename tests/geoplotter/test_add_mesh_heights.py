# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for heights in the scene, through :meth:`GeoPlotter.add_mesh`."""

from __future__ import annotations

import numpy as np
import pint
from pyproj import CRS
import pytest
import pyvista as pv

from geovista.bridge import Transform
from geovista.common import _GV_GLOBE_FIELDS, GV_POINT_HEIGHT
from geovista.crs import WGS84, to_wkt
from geovista.geoplotter import GeoPlotter
from geovista.globe import Globe
from geovista.transform import transform_mesh

#: A render radius of 1, and the Earth's radius.
RADII = [1.0, 6378137.0]

#: The Earth's radius of the default globe, in metres.
R = 6378137.0

#: The cell bounds of a small grid, and its points in the order the bridge builds.
XS, YS = [0.0, 10.0, 20.0], [0.0, 10.0]

#: A height for each point, above and below sea level, at it, and one missing.
HEIGHTS = np.array([1000.0, -4000.0, np.nan, 250.0, 0.0, -10.0])

#: A globe that exaggerates heights above and below sea level by their own factors.
EXAGGERATED = {"exaggeration": 20, "exaggeration_below": 100}


def _mapped(heights: np.ndarray, globe: Globe) -> np.ndarray:
    """Return V(h), worked out with numpy alone, with a missing height as 0."""
    heights = np.asarray(heights, dtype=np.float64)
    mapped = np.where(
        heights >= 0,
        globe.exaggeration * heights,
        globe.exaggeration_below * heights,
    )
    return np.where(np.isnan(heights), 0.0, mapped)


def _radii(heights: np.ndarray, globe: Globe) -> np.ndarray:
    """Return s (R + V(h)), worked out with numpy alone."""
    radius = globe.radius.m_as("m")
    return globe.render_radius * (1.0 + _mapped(heights, globe) / radius)


def _norms(mesh: pv.DataSet) -> np.ndarray:
    """Return the distance of each point of a mesh from the centre."""
    return np.linalg.norm(np.asarray(mesh.points, dtype=np.float64), axis=1)


def _drawn(plotter: GeoPlotter, mesh: pv.DataSet, **kwargs: object) -> pv.DataSet:
    """Return the mesh the scene draws."""
    return plotter.add_mesh(mesh, **kwargs).mapper.dataset


def _grid(**kwargs: object) -> pv.PolyData:
    """Return the small grid, built at the default globe."""
    return Transform.from_1d(XS, YS, **kwargs)


@pytest.mark.parametrize("radius", RADII)
def test_drawn_at_the_scenes_globe_by_the_formula(radius):
    """Heights given to add_mesh place each point at the scene's globe.

    Holds heights spec §2 decision 4.
    """
    p = GeoPlotter(globe=Globe(render_radius=radius, **EXAGGERATED))
    drawn = _drawn(p, _grid(), height=HEIGHTS)
    np.testing.assert_array_equal(drawn.gv.height.m_as("m"), HEIGHTS)
    np.testing.assert_allclose(_norms(drawn), _radii(HEIGHTS, p.globe), rtol=1e-12)
    assert Globe.from_mesh(drawn) == p.globe


@pytest.mark.parametrize("radius", RADII)
def test_depth_is_a_negative_height(radius):
    """A depth draws the points its negation as a height draws."""
    p = GeoPlotter(globe=Globe(render_radius=radius, **EXAGGERATED))
    by_depth = _drawn(p, _grid(), depth=-HEIGHTS)
    by_height = _drawn(p, _grid(), height=HEIGHTS)
    np.testing.assert_array_equal(by_depth.points, by_height.points)
    np.testing.assert_array_equal(by_depth.gv.depth.m_as("m"), -HEIGHTS)


@pytest.mark.parametrize("radius", RADII)
def test_vertical_units(radius):
    """Plain heights in the unit named, or a quantity, read back in metres."""
    p = GeoPlotter(globe=Globe(render_radius=radius))
    km = _drawn(p, _grid(), height=HEIGHTS / 1000.0, vertical_units="km")
    np.testing.assert_allclose(km.gv.height.m_as("m"), HEIGHTS, rtol=1e-12)
    ureg = pint.UnitRegistry()
    feet = _drawn(p, _grid(), height=ureg.Quantity(HEIGHTS / 0.3048, "ft"))
    np.testing.assert_allclose(feet.gv.height.m_as("m"), HEIGHTS, rtol=1e-12)
    np.testing.assert_allclose(_norms(feet), _radii(HEIGHTS, p.globe), rtol=1e-12)


@pytest.mark.parametrize("radius", RADII)
@pytest.mark.parametrize(
    ("crs", "unit"),
    [("+proj=eqc", 1.0), ("+proj=eqc +units=km", 1000.0)],
    ids=["metres", "kilometres"],
)
def test_on_a_map_by_the_formula(crs, unit, radius):
    """On a map a point given a height lies at V(h), in the unit of the map."""
    p = GeoPlotter(crs=crs, globe=Globe(render_radius=radius, **EXAGGERATED))
    drawn = _drawn(p, _grid(), height=HEIGHTS)
    heights = drawn.gv.height.m_as("m")
    np.testing.assert_array_equal(np.sort(heights), np.sort(HEIGHTS))
    np.testing.assert_allclose(
        drawn.points[:, 2], _mapped(heights, p.globe) / unit, rtol=1e-6, atol=1e-6
    )


@pytest.mark.parametrize("radius", RADII)
def test_a_mesh_without_a_globe_or_crs(radius):
    """A mesh that records nothing is placed at the scene's globe by its heights."""
    p = GeoPlotter(globe=Globe(render_radius=radius))
    with pytest.warns(UserWarning, match="no coordinate reference system"):
        drawn = _drawn(p, pv.Sphere(radius=0.5), height=1000.0)
    np.testing.assert_allclose(
        _norms(drawn), float(_radii(np.array([1000.0]), p.globe)[0]), rtol=1e-6
    )


def test_the_mesh_given_is_unchanged():
    """Heights are written to the mesh drawn, never to the mesh given."""
    mesh = _grid(data=np.arange(2.0))
    points = mesh.points.copy()
    point_keys, field_keys = list(mesh.point_data), list(mesh.field_data)
    p = GeoPlotter(globe=Globe(render_radius=2.0, exaggeration=20))
    _drawn(p, mesh, height=HEIGHTS)
    np.testing.assert_array_equal(mesh.points, points)
    assert list(mesh.point_data) == point_keys
    assert list(mesh.field_data) == field_keys
    assert GV_POINT_HEIGHT not in mesh.point_data


@pytest.mark.parametrize("data", [None, np.arange(2.0)], ids=["no data", "cells"])
def test_heights_are_never_the_active_scalars(data):
    """The heights drawn never become the active scalars of the mesh drawn."""
    mesh = _grid(data=data)
    expected = mesh.active_scalars_name
    drawn = _drawn(GeoPlotter(), mesh, height=HEIGHTS)
    assert drawn.active_scalars_name == expected
    assert drawn.active_scalars_name != GV_POINT_HEIGHT


def test_a_masked_height_is_drawn_at_sea_level():
    """A masked height reads back as NaN, and its point is drawn at sea level."""
    heights = np.ma.masked_array(np.nan_to_num(HEIGHTS), mask=[1, 0, 0, 0, 1, 0])
    p = GeoPlotter(globe=Globe(**EXAGGERATED))
    drawn = _drawn(p, _grid(), height=heights)
    expected = np.where(np.ma.getmaskarray(heights), np.nan, heights.data)
    np.testing.assert_array_equal(drawn.gv.height.m_as("m"), expected)
    np.testing.assert_allclose(_norms(drawn), _radii(expected, p.globe), rtol=1e-12)


@pytest.mark.parametrize("radius", RADII)
def test_texture_cut_points_lie_at_their_heights(radius):
    """The points the texture's seam cut adds lie at their heights too."""
    xs, ys = np.arange(-165.0, 196.0, 30.0), np.arange(-90.0, 91.0, 30.0)
    mesh = Transform.from_1d(xs, ys)
    texture = pv.Texture(np.zeros((4, 8, 3), dtype=np.uint8))
    p = GeoPlotter(globe=Globe(render_radius=radius, exaggeration=100))
    drawn = _drawn(p, mesh, height=1000.0, texture=texture)
    assert drawn.n_points > mesh.n_points
    np.testing.assert_allclose(
        _norms(drawn), float(_radii(np.array([1000.0]), p.globe)[0]), rtol=1e-6
    )


@pytest.mark.parametrize("radius", RADII)
def test_a_structured_grid_takes_heights(radius):
    """A dataset that is not cast takes heights, and is placed by them."""
    lons, lats = np.meshgrid(np.radians([0.0, 10.0, 20.0]), np.radians([0.0, 10.0]))
    x, y, z = np.cos(lats) * np.cos(lons), np.cos(lats) * np.sin(lons), np.sin(lats)
    grid = pv.StructuredGrid(x[..., None], y[..., None], z[..., None])
    to_wkt(grid, WGS84)
    p = GeoPlotter(globe=Globe(render_radius=radius, **EXAGGERATED))
    drawn = _drawn(p, grid, height=HEIGHTS)
    np.testing.assert_allclose(
        _norms(drawn), _radii(drawn.gv.height.m_as("m"), p.globe), rtol=1e-6
    )


def _ellipsoidal() -> pv.PolyData:
    """Return the small grid, recording a CRS whose height is above the ellipsoid."""
    mesh = _grid()
    to_wkt(mesh, CRS("EPSG:4979"))
    return mesh


@pytest.mark.parametrize(
    ("mesh", "kwargs", "match"),
    [
        (
            _grid(height=1.0),
            {"height": 2.0},
            r"carries heights of its own, and heights are given once, got 'height'",
        ),
        (
            _grid(height=1.0),
            {"depth": 2.0},
            r"carries heights of its own, and heights are given once, got 'depth'",
        ),
        (_grid(), {"height": 1.0, "depth": 1.0}, r"not both"),
        (_grid(), {"height": 1.0, "zlevel": 1}, r"never given together"),
        (
            Transform.from_points([0.0, 10.0], [0.0, 10.0], zlevel=1),
            {"height": 1.0},
            r"point cloud given carries z-levels other than 0",
        ),
        (_grid(), {"height": [1.0, 2.0]}, r"each of the 2 cells"),
        (_grid(), {"height": [1.0, np.inf, 0, 0, 0, 0]}, r"cannot be infinite"),
        (_grid(), {"height": [1.0, 2.0, 3.0]}, r"one for the whole mesh, got 3"),
        (_grid(), {"height": 1.0, "vertical_units": "hPa"}, r"hPa"),
        (
            _grid(),
            {"height": pint.UnitRegistry().Quantity(1.0, "m"), "vertical_units": "m"},
            r"takes no vertical_units",
        ),
        (_grid(), {"vertical_units": "m"}, r"neither was given"),
        (_ellipsoidal(), {"height": 1.0}, r"Ellipsoidal height"),
    ],
    ids=[
        "carried height",
        "carried depth",
        "height and depth",
        "zlevel",
        "cloud levels",
        "cells",
        "infinite",
        "size",
        "not a length",
        "units with a quantity",
        "units alone",
        "ellipsoidal",
    ],
)
def test_refuses(mesh, kwargs, match):
    """Each refusal names what was given.

    Holds heights spec §2 decision 5.
    """
    with pytest.raises(ValueError, match=match):
        GeoPlotter().add_mesh(mesh, **kwargs)


def test_refuses_heights_for_what_is_not_a_dataset():
    """Heights are given for the points of a mesh, which a block has not."""
    with pytest.raises(TypeError, match=r"got 'depth' with a MultiBlock"):
        GeoPlotter().add_mesh(pv.MultiBlock([_grid()]), depth=1.0)


@pytest.mark.parametrize("radius", RADII)
def test_a_cloud_on_a_map_at_level_0_takes_heights(radius):
    """A cloud transformed to a map, at a z-level of 0, is placed by its heights."""
    globe = Globe(render_radius=radius, **EXAGGERATED)
    cloud = transform_mesh(
        Transform.from_points([0.0, 10.0, 20.0], [0.0, 5.0, 10.0], globe=globe),
        "+proj=eqc",
    )
    heights = np.array([1000.0, -4000.0, 0.0])
    p = GeoPlotter(crs="+proj=eqc", globe=globe)
    drawn = _drawn(p, cloud, height=heights)
    np.testing.assert_allclose(
        drawn.points[:, 2], _mapped(heights, globe), rtol=1e-6, atol=1e-6
    )


def _mapped_cloud(dtype: type = np.float64, **kwargs: object) -> pv.PolyData:
    """Return a point cloud, with its points in the dtype, transformed to a map."""
    cloud = Transform.from_points([0.0, 10.0, 20.0], [0.0, 10.0, 5.0], **kwargs)
    cloud.points = cloud.points.astype(dtype)
    # a zscale of 0 reads its levels as 0 / 0 when the cloud is transformed
    with np.errstate(divide="ignore", invalid="ignore"):
        return transform_mesh(cloud, "+proj=eqc")


@pytest.mark.parametrize(
    ("dtype", "zscale"),
    [(np.float64, -1e-4), (np.float64, 0.0), (np.float32, None)],
    ids=["negative zscale", "zero zscale", "float32"],
)
def test_a_cloud_on_a_map_at_level_0_takes_heights_whatever_its_scale(dtype, zscale):
    """A level-0 cloud on a map takes heights, as it does on the sphere."""
    cloud = _mapped_cloud(dtype, zlevel=0, zscale=zscale)
    drawn = _drawn(GeoPlotter(crs="+proj=eqc"), cloud, height=1000.0)
    np.testing.assert_allclose(drawn.points[:, 2], 1000.0, rtol=1e-6)


@pytest.mark.parametrize("zlevel", [0.01, 1])
def test_a_cloud_on_a_map_keeps_its_level_refused(zlevel):
    """A cloud lifted on the sphere is refused heights on a map, as on the sphere."""
    with pytest.raises(ValueError, match=r"carries z-levels other than 0"):
        GeoPlotter(crs="+proj=eqc").add_mesh(_mapped_cloud(zlevel=zlevel), height=1.0)


def test_refuses_heights_for_a_flat_mesh_without_a_crs():
    """A flat mesh with no CRS has no place for its heights, so is refused."""
    with pytest.raises(ValueError, match=r"no coordinate reference system"):
        GeoPlotter().add_mesh(pv.Plane(), height=1000.0)


#: How a recorded globe differs from the scene's, one field each.
OTHERS = {
    "earth radius": {"radius": 6371000.0},
    "render radius": {"render_radius": 2.0},
    "exaggeration": {"exaggeration": 100},
    "exaggeration below": {"exaggeration_below": 5},
}


@pytest.mark.parametrize("radius", RADII)
@pytest.mark.parametrize("other", OTHERS.values(), ids=OTHERS.keys())
def test_another_globe_on_the_sphere(other, radius):
    """A mesh with heights at another globe is drawn from them at the scene's.

    Holds heights spec §2 decision 7.
    Holds globe spec §2 decision 7.
    """
    scene = {"render_radius": radius, **EXAGGERATED}
    recorded = Globe(**{**scene, **other})
    mesh = _grid(height=HEIGHTS, globe=recorded)
    p = GeoPlotter(globe=Globe(**scene))
    drawn = _drawn(p, mesh)
    np.testing.assert_allclose(_norms(drawn), _radii(HEIGHTS, p.globe), rtol=1e-12)
    assert Globe.from_mesh(drawn) == p.globe
    np.testing.assert_array_equal(drawn.gv.height.m_as("m"), HEIGHTS)


@pytest.mark.parametrize("radius", RADII)
def test_another_globe_on_a_map(radius):
    """On a map, a mesh with heights at another globe lies at the scene's V(h)."""
    recorded = Globe(render_radius=radius, exaggeration=100)
    mesh = transform_mesh(_grid(height=HEIGHTS, globe=recorded), "+proj=eqc")
    p = GeoPlotter(crs="+proj=eqc", globe=Globe(render_radius=radius))
    drawn = _drawn(p, mesh)
    np.testing.assert_allclose(
        drawn.points[:, 2], _mapped(HEIGHTS, p.globe), rtol=1e-6, atol=1e-6
    )
    np.testing.assert_array_equal(drawn.points[:, :2], mesh.points[:, :2])
    assert Globe.from_mesh(drawn) == p.globe


@pytest.mark.parametrize("radius", RADII)
@pytest.mark.parametrize("records", ["the scene's", "none"])
def test_the_scenes_globe_or_none_is_drawn_as_it_lies(records, radius):
    """A mesh with heights at the scene's globe, or at none, keeps its points."""
    globe = Globe(render_radius=radius, **EXAGGERATED)
    if records == "none":
        mesh = _grid(height=HEIGHTS, globe=Globe(render_radius=radius, exaggeration=7))
        for field in _GV_GLOBE_FIELDS:
            del mesh.field_data[field]
    else:
        mesh = _grid(height=HEIGHTS, globe=globe)
    drawn = _drawn(GeoPlotter(globe=globe), mesh)
    np.testing.assert_array_equal(drawn.points, mesh.points)


@pytest.mark.parametrize("radius", RADII)
def test_without_heights_the_ratio_stands(radius):
    """A mesh without heights at another globe is scaled by the render radii."""
    mesh = _grid(globe=Globe(render_radius=2.0 * radius))
    drawn = _drawn(GeoPlotter(globe=Globe(render_radius=radius)), mesh)
    np.testing.assert_allclose(_norms(drawn), radius, rtol=1e-12)

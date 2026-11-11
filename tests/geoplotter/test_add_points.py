# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter.add_points`."""

from __future__ import annotations

import warnings

import numpy as np
import pint
from pyproj import CRS
from pyproj.exceptions import CRSError
import pytest

from geovista.bridge import Transform
from geovista.crs import WGS84, from_wkt, has_wkt, to_wkt
from geovista.geoplotter import GeoPlotter
from geovista.globe import Globe

#: The positions of points, the second of which is made missing.
LONS = [0.0, 10.0, 20.0, 30.0]
LATS = [0.0, 5.0, 10.0, 15.0]

#: The warning of the point dropped.
DROPPED = r"dropped 1 of 4 points from the point cloud, where 'xs' is masked or NaN"


def test_style_fail():
    """Test trap of invalid style request."""
    p = GeoPlotter()
    emsg = "Invalid 'style' for 'add_points'"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(style="dolce and gabbana")


def test_no_points_fail():
    """Test trap of no spatial points provided."""
    p = GeoPlotter()
    emsg = "got neither"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points()


def test_duplicate_points_fail(mocker):
    """Test trap of duplicate spatial points provided."""
    p = GeoPlotter()
    points, xs, ys = mocker.sentinel.points, mocker.sentinel.xs, mocker.sentinel.ys
    emsg = "got both 'points', and 'xs' and 'ys'"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(points=points, xs=xs, ys=ys)


@pytest.mark.parametrize(("xs", "ys"), [(True, None), (None, True)])
def test_over_specified_points_fail(mocker, xs, ys):
    """Test trap of points and xs or ys provided."""
    p = GeoPlotter()
    points = mocker.sentinel.points
    emsg = "got both 'points', and 'xs' or 'ys'"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(points=points, xs=xs, ys=ys)


def test_points_mesh_crs_fail(sphere):
    """Test trap of crs mismatch with points mesh serialized crs as wkt."""
    p = GeoPlotter()
    emsg = "The CRS serialized as WKT on the 'points' mesh does not match"
    to_wkt(sphere, WGS84)
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(points=sphere, crs="+proj=eqc")


@pytest.mark.parametrize("crs", [None, CRS.from_user_input("+proj=eqc")])
def test_points_mesh_with_no_crs(mocker, sphere, crs):
    """Test points mesh with no serialized crs."""
    assert not has_wkt(sphere)
    p = GeoPlotter()
    actor = mocker.sentinel.actor
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh", return_value=actor)
    _ = p.add_points(sphere, crs=crs)
    p.add_mesh.assert_called_once_with(sphere, style="points", scalars=None)
    assert has_wkt(sphere)
    expected = WGS84 if crs is None else crs
    assert from_wkt(sphere) == expected


def test_crs_invalid_fail():
    """Test trap of crs validity sanity check."""
    p = GeoPlotter()
    emsg = "Invalid projection"
    with pytest.raises(CRSError, match=emsg):
        _ = p.add_points(crs="invalid")


def test_points_mesh_with_scalars(mocker, sphere):
    """Test points mesh with scalars pass-through."""
    p = GeoPlotter()
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh")
    scalars = mocker.sentinel.scalars
    _ = p.add_points(sphere, scalars=scalars)
    p.add_mesh.assert_called_once_with(sphere, style="points", scalars=scalars)


def test_texture_kwarg_pop(mocker, sphere):
    """Test defensive texture kwarg purge."""
    p = GeoPlotter()
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh")
    texture = mocker.sentinel.texture
    _ = p.add_points(sphere, texture=texture)
    p.add_mesh.assert_called_once_with(sphere, style="points", scalars=None)


@pytest.mark.parametrize(("xs", "ys"), [(None, True), (True, None)])
def test_xs_ys_incomplete_fail(xs, ys):
    """Test trap of missing spatial points."""
    p = GeoPlotter()
    emsg = "got only 'xs' or 'ys'"
    with pytest.raises(ValueError, match=emsg):
        _ = p.add_points(xs=xs, ys=ys)


def test_xs_ys(mocker):
    """Test xs/ys points."""
    p = GeoPlotter()
    mesh = mocker.sentinel.mesh
    _ = mocker.patch("geovista.Transform.from_points", return_value=mesh)
    actor = mocker.sentinel.actor
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh", return_value=actor)
    xs, ys = mocker.sentinel.xs, mocker.sentinel.ys
    crs, scalars = WGS84, mocker.sentinel.scalars
    zlevel, zscale = mocker.sentinel.zlevel, mocker.sentinel.zscale
    result = p.add_points(
        xs=xs,
        ys=ys,
        scalars=scalars,
        crs=crs,
        zlevel=zlevel,
        zscale=zscale,
    )
    assert result == actor
    from geovista.bridge import Transform  # noqa: PLC0415

    Transform.from_points.assert_called_once_with(
        xs, ys, crs=crs, globe=p.globe, zlevel=zlevel, zscale=zscale
    )
    p.add_mesh.assert_called_once_with(mesh, style="points", scalars=scalars)


def test_xy_ys_scalars_name_warnings(mocker):
    """Test xy/ys points invalid scalars array name warning is raised."""
    p = GeoPlotter()
    mesh = mocker.sentinel.mesh
    _ = mocker.patch("geovista.Transform.from_points", return_value=mesh)
    _ = mocker.patch("geovista.geoplotter.GeoPlotterBase.add_mesh")
    xs, ys = mocker.sentinel.xs, mocker.sentinel.ys
    scalars = "invalid"
    wmsg = (
        f"geovista ignoring the 'scalars' string name '{scalars}', "
        "as no 'points' mesh was provided"
    )
    with pytest.warns(UserWarning, match=wmsg):
        _ = p.add_points(xs=xs, ys=ys, scalars=scalars)


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
def test_at_the_scenes_globe(radius):
    """Points are placed on the scene's globe, and record it."""
    p = GeoPlotter(globe=Globe(render_radius=radius))
    drawn = p.add_points(xs=[0.0, 10.0], ys=[0.0, 10.0]).mapper.dataset
    np.testing.assert_allclose(np.linalg.norm(drawn.points, axis=1), radius, rtol=1e-6)
    assert Globe.from_mesh(drawn) == p.globe


def test_xs_ys_as_quantities():
    """Points given as quantities are drawn where their degrees are."""
    ureg = pint.UnitRegistry()
    p = GeoPlotter()
    expected = p.add_points(xs=[0.0, 10.0], ys=[0.0, 20.0]).mapper.dataset.points
    xs = ureg.Quantity(np.radians([0.0, 10.0]), "radian")
    ys = ureg.Quantity(np.radians([0.0, 20.0]), "radian")
    drawn = p.add_points(xs=xs, ys=ys).mapper.dataset
    np.testing.assert_allclose(drawn.points, expected, rtol=1e-12)


def scalars_of(actor):
    """Return the scalars an actor draws its points with."""
    return actor.mapper.dataset[actor.mapper.array_name]


def test_drops_a_missing_point_and_its_scalar():
    """Test a missing point is drawn without its scalar.

    Holds positions spec §2 decision 6.

    """
    xs = np.ma.masked_array(LONS, mask=[0, 1, 0, 0])
    with pytest.warns(UserWarning, match=DROPPED):
        actor = GeoPlotter().add_points(xs=xs, ys=LATS, scalars=[1.0, 2.0, 3.0, 4.0])
    drawn = actor.mapper.dataset
    expected = GeoPlotter().add_points(xs=[0.0, 20.0, 30.0], ys=[0.0, 10.0, 15.0])
    np.testing.assert_allclose(drawn.points, expected.mapper.dataset.points)
    np.testing.assert_allclose(scalars_of(actor), [1.0, 3.0, 4.0])


def test_cuts_scalars_in_the_shape_of_xs():
    """Test points in a grid drop their scalars in the same order.

    Holds positions spec §2 decision 6.

    """
    xs = np.ma.masked_array([[0.0, 10.0], [20.0, 30.0]], mask=[[0, 1], [0, 0]])
    ys = np.array([[0.0, 5.0], [10.0, 15.0]])
    scalars = np.array([[1.0, 2.0], [3.0, 4.0]])
    with pytest.warns(UserWarning, match=DROPPED):
        actor = GeoPlotter().add_points(xs=xs, ys=ys, scalars=scalars)
    assert actor.mapper.dataset.n_points == 3
    np.testing.assert_allclose(scalars_of(actor), [1.0, 3.0, 4.0])


def test_keeps_the_column_of_scalars():
    """Test scalars given as a column are drawn as those of the points kept would be.

    pyvista colours a column of scalars by their magnitude, so the drop must not
    flatten it. Holds positions spec §2 decision 6.

    """
    xs = np.ma.masked_array(LONS, mask=[0, 1, 0, 0])
    column = np.array([[-1.0], [-2.0], [-3.0], [-4.0]])
    with pytest.warns(UserWarning, match=DROPPED):
        actor = GeoPlotter().add_points(xs=xs, ys=LATS, scalars=column)
    expected = GeoPlotter().add_points(
        xs=[0.0, 20.0, 30.0], ys=[0.0, 10.0, 15.0], scalars=column[[0, 2, 3]]
    )
    np.testing.assert_allclose(scalars_of(actor), scalars_of(expected))
    np.testing.assert_allclose(actor.mapper.scalar_range, expected.mapper.scalar_range)


def test_cuts_colours():
    """Test a missing point is drawn without its colour.

    Holds positions spec §2 decision 6.

    """
    xs = np.ma.masked_array(LONS, mask=[0, 1, 0, 0])
    colours = np.array(
        [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0]], dtype=np.uint8
    )
    with pytest.warns(UserWarning, match=DROPPED):
        actor = GeoPlotter().add_points(xs=xs, ys=LATS, scalars=colours, rgb=True)
    drawn = actor.mapper.dataset
    assert drawn.n_points == 3
    np.testing.assert_array_equal(scalars_of(actor), colours[[0, 2, 3]])


def test_draws_present_points_as_before():
    """Test points that are all present are drawn with every scalar, unwarned."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        actor = GeoPlotter().add_points(xs=LONS, ys=LATS, scalars=[1.0, 2.0, 3.0, 4.0])
    drawn = actor.mapper.dataset
    assert drawn.n_points == 4
    np.testing.assert_allclose(scalars_of(actor), [1.0, 2.0, 3.0, 4.0])


@pytest.mark.parametrize(
    ("kwargs", "shape"),
    [
        ({"scalars": [1.0, 2.0, 3.0]}, r"\(3,\)"),
        ({"scalars": np.zeros((3, 3), dtype=np.uint8), "rgb": True}, r"\(3, 3\)"),
    ],
    ids=["values", "colours"],
)
def test_refuses_scalars_of_another_count(kwargs, shape):
    """Test scalars that are not one for each point given are refused, as before.

    Scalars short by the points dropped are not paired with the points kept.

    """
    xs = np.ma.masked_array(LONS, mask=[0, 1, 0, 0])
    emsg = (
        r"Require scalars with one value, or one row, for each of the 4 points "
        rf"given, got shape {shape}\."
    )
    with pytest.raises(ValueError, match=emsg):
        GeoPlotter().add_points(xs=xs, ys=LATS, **kwargs)


def test_refuses_coordinates_of_another_size():
    """Test coordinates of different sizes are refused as before, with no drop.

    Their scalars are left uncut, so the refusal is that of the transform.

    """
    xs = np.ma.masked_array(LONS, mask=[0, 1, 0, 0])
    emsg = r"'xs' and 'ys' require same length, got 4 and 3 respectively\."
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ValueError, match=emsg):
            GeoPlotter().add_points(xs=xs, ys=LATS[:3], scalars=[1.0, 2.0, 3.0, 4.0])


#: A height for each of the points, above and below sea level.
HEIGHTS = np.array([1000.0, -4000.0, 250.0, 0.0])

#: The Earth's radius of the default globe, in metres.
R = 6378137.0


def _radii(heights: np.ndarray, globe: Globe) -> np.ndarray:
    """Return s (R + V(h)), worked out with numpy alone."""
    heights = np.asarray(heights, dtype=np.float64)
    mapped = np.where(
        heights >= 0,
        globe.exaggeration * heights,
        globe.exaggeration_below * heights,
    )
    return globe.render_radius * (1.0 + mapped / R)


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
@pytest.mark.parametrize(
    "kwargs",
    [
        {"height": HEIGHTS},
        {"depth": -HEIGHTS},
        {"height": HEIGHTS / 1000.0, "vertical_units": "km"},
    ],
    ids=["height", "depth", "kilometres"],
)
def test_heights_with_xs_ys(kwargs, radius):
    """Points given heights are placed by them at the scene's globe.

    Holds heights spec §2 decision 4.
    """
    p = GeoPlotter(globe=Globe(render_radius=radius, exaggeration=20))
    drawn = p.add_points(xs=LONS, ys=LATS, **kwargs).mapper.dataset
    np.testing.assert_allclose(drawn.gv.height.m_as("m"), HEIGHTS, rtol=1e-12)
    np.testing.assert_allclose(
        np.linalg.norm(drawn.points, axis=1), _radii(HEIGHTS, p.globe), rtol=1e-12
    )


def test_heights_drop_with_a_missing_point():
    """A missing point is dropped with its height."""
    xs = np.ma.masked_array(LONS, mask=[0, 1, 0, 0])
    with pytest.warns(UserWarning, match=DROPPED):
        drawn = GeoPlotter().add_points(xs=xs, ys=LATS, height=HEIGHTS).mapper.dataset
    assert drawn.n_points == 3
    np.testing.assert_array_equal(drawn.gv.height.m_as("m"), HEIGHTS[[0, 2, 3]])


@pytest.mark.parametrize("radius", [1.0, 6378137.0])
def test_heights_with_points(radius):
    """A cloud given as points takes heights, placed at the scene's globe."""
    cloud = Transform.from_points(LONS, LATS)
    p = GeoPlotter(globe=Globe(render_radius=radius, exaggeration=20))
    drawn = p.add_points(points=cloud, height=HEIGHTS).mapper.dataset
    np.testing.assert_allclose(
        np.linalg.norm(drawn.points, axis=1), _radii(HEIGHTS, p.globe), rtol=1e-12
    )
    assert cloud.gv.height is None


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"height": HEIGHTS}, r"carries heights of its own, .* got 'height'"),
        ({"depth": HEIGHTS}, r"carries heights of its own, .* got 'depth'"),
    ],
    ids=["height", "depth"],
)
def test_refuses_heights_for_points_that_carry_them(kwargs, match):
    """Points that carry heights take no more.

    Holds heights spec §2 decision 5.
    """
    cloud = Transform.from_points(LONS, LATS, height=HEIGHTS)
    with pytest.raises(ValueError, match=match):
        GeoPlotter().add_points(points=cloud, **kwargs)


def test_refuses_heights_for_points_with_a_zlevel():
    """Points given as a mesh take no z-level with heights."""
    cloud = Transform.from_points(LONS, LATS)
    with pytest.raises(ValueError, match=r"never given together"):
        GeoPlotter().add_points(points=cloud, height=HEIGHTS, zlevel=1)

"""Unit-tests for :meth:`geovista.Transform.from_points`."""
from __future__ import annotations

import numpy as np
from pyproj import CRS, Transformer
import pytest

from geovista.bridge import NAME_POINTS, Transform
from geovista.common import GV_FIELD_CRS, GV_FIELD_RADIUS, RADIUS, to_cartesian, wrap
from geovista.crs import WGS84


def test_defaults(lam_uk_sample, wgs84_wkt):
    """Test expected defaults are honoured."""
    lons, lats = lam_uk_sample
    result = Transform.from_points(lons, lats)
    assert result[GV_FIELD_CRS] == wgs84_wkt
    assert np.isclose(result[GV_FIELD_RADIUS], RADIUS)
    assert result.n_points == lons.size
    assert result.n_points == result.n_cells


def test_to_cartesian_kwarg_pass_thru(mocker, lam_uk_sample):
    """Test kwargs are passed thru to :func:`geovista.common.to_cartesian`."""
    xyz = np.array([[1.0, 2.0, 3.0]])
    radius = 1.23
    zlevel = mocker.sentinel.zlevel
    zscale = 4.56
    to_cartesian = mocker.patch("geovista.bridge.to_cartesian", return_value=xyz)
    kwargs = {"radius": radius, "zlevel": zlevel, "zscale": zscale}
    lons, lats = lam_uk_sample
    result = Transform.from_points(lons, lats, **kwargs)
    to_cartesian.assert_called_once()
    args = to_cartesian.call_args.args
    assert len(args) == 2
    np.testing.assert_array_equal(args[0], wrap(lons))
    np.testing.assert_array_equal(args[1], lats)
    assert to_cartesian.call_args.kwargs == kwargs
    np.testing.assert_array_equal(result.points, xyz)


@pytest.mark.parametrize("name", [None, "dummy"])
def test_attach_point_data(lam_uk_sample, name):
    """Test point-cloud data is attached to mesh."""
    lons, lats = lam_uk_sample
    data = np.arange(lons.size)
    result = Transform.from_points(lons, lats, data=data, name=name)
    expected = NAME_POINTS if name is None else name
    assert expected in result.point_data
    np.testing.assert_array_equal(result[expected], data)


@pytest.mark.parametrize("proj", ["eqc", "robin", "moll"])
def test_transform_points(lam_uk_sample, wgs84_wkt, proj):
    """Test projection of native crs to wgs84."""
    lons, lats = lam_uk_sample
    crs = CRS.from_user_input(f"+proj={proj}")
    transformer = Transformer.from_crs(WGS84, crs, always_xy=True)
    xs, ys = transformer.transform(lons, lats, errcheck=True)
    result = Transform.from_points(xs, ys, crs=crs)
    assert result[GV_FIELD_CRS] == wgs84_wkt
    expected = to_cartesian(lons, lats)
    np.testing.assert_array_almost_equal(result.points, expected)

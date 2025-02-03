# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform.from_points`."""

from __future__ import annotations

import cartopy.crs as ccrs
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


def test_scalar():
    """Test scalar and single element mixture of xs/ys."""
    expected = np.array([[0.0, 0.0, 1.0]])
    np.testing.assert_array_equal(Transform.from_points(0, 90).points, expected)
    np.testing.assert_array_equal(Transform.from_points(0, [90]).points, expected)
    np.testing.assert_array_equal(Transform.from_points([0], 90).points, expected)
    np.testing.assert_array_equal(Transform.from_points([0], [90]).points, expected)


class TestVectors:
    """Check calculations on attached vectors.

    Mostly testing against previously-obtained results, but we do have examples proving
    practically correct behaviours : see src/geovista/examples/vector_data
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set useful test constants."""
        self.lats = np.array([10.0, 80.0, -70.0, 35.0])
        self.lons = np.array([5.0, 140.0, -200.0, 73])
        self.easting = 10.0e6 * np.array([1.0, 8.0, 13.0, 25.0])
        self.northing = 10.0e6 * np.array([-2.0, 5.0, 17.0, -14.0])
        self.u = np.array([10.0, 20, 15.0, 24.0])
        self.v = np.array([20.0, -17, 0.0, 33.0])
        self.w = np.array([15.0, 25, 4.0, -55.0])
        self.crs_truelatlon = WGS84
        self.crs_rotatedlatlon = ccrs.RotatedGeodetic(130.0, 65.0).to_wkt()
        self.crs_northpolar = ccrs.NorthPolarStereo().to_wkt()

    def test_basic(self):
        """Check basic operation on true-latlon uvw vectors."""
        mesh = Transform.from_points(
            xs=self.lons, ys=self.lats, vectors=(self.u, self.v, self.w)
        )
        result = mesh["vectors"].T
        expected = np.array(
            [
                [10.385, -29.006, -6.416, -41.658],
                [10.947, -1.769, -13.627, -54.169],
                [22.301, 21.668, -3.759, -4.515],
            ]
        )
        assert np.allclose(result, expected, atol=0.001)

    def test_nonarrays(self):
        """Check basic operation with lists of numbers in place of array vectors."""
        mesh = Transform.from_points(
            xs=self.lons,
            ys=self.lats,
            vectors=(list(self.u), list(self.v), list(self.w)),
        )
        result = mesh["vectors"].T
        expected = np.array(
            [
                [10.385, -29.006, -6.416, -41.658],
                [10.947, -1.769, -13.627, -54.169],
                [22.301, 21.668, -3.759, -4.515],
            ]
        )
        assert np.allclose(result, expected, atol=0.001)

    def test_basic__2d_uv(self):
        """Check operation with only 2 input component arrays (no W)."""
        mesh = Transform.from_points(
            xs=self.lons, ys=self.lats, vectors=(self.u, self.v)
        )
        result = mesh["vectors"].T
        expected = np.array(
            [
                [-4.331, -25.681, -5.13, -28.485],
                [9.659, -4.56, -14.095, -11.084],
                [19.696, -2.952, 0.0, 27.032],
            ]
        )
        assert np.allclose(result, expected, atol=0.001)

    def test_crs(self):
        """Check operation with alternate latlon-type CRS."""
        mesh = Transform.from_points(
            xs=self.lons,
            ys=self.lats,
            vectors=(self.u, self.v),
            crs=self.crs_rotatedlatlon,
        )
        result = mesh["vectors"].T
        expected = np.array(
            [
                [-0.474, -17.651, -13.786, -32.429],
                [15.592, 13.943, -5.499, 21.403],
                [16.02, -13.529, -2.168, 12.461],
            ]
        )
        assert np.allclose(result, expected, atol=0.001)

    def test__nonlatlon_crs__fail(self):
        """Check error when attempted with non-latlon CRS."""
        msg = "Cannot determine wind directions : Target CRS type is not supported.*"
        with pytest.raises(ValueError, match=msg):
            _ = Transform.from_points(
                xs=self.easting,
                ys=self.northing,
                vectors=(self.u, self.v),
                crs=self.crs_northpolar,
            )

    def test__nonlatloncrs__truelatlon__vectorscrs(self):
        """Check ok with non-latlon CRS for points but latlon vectors."""
        mesh = Transform.from_points(
            xs=self.easting,
            ys=self.northing,
            vectors=(self.u, self.v),
            crs=self.crs_northpolar,
            vectors_crs=self.crs_truelatlon,
        )
        result = mesh["vectors"].T
        expected = np.array(
            [
                [4.722, -8.267, -9.112, -4.879],
                [13.541, -24.508, -11.915, 40.408],
                [17.156, -4.472, 0.0, 2.903],
            ]
        )
        assert np.allclose(result, expected, atol=0.001)

    def test__latlon__vectorscrs(self):
        """Check operation with different specified CRS for vectors only."""
        mesh = Transform.from_points(
            xs=self.lons,
            ys=self.lats,
            vectors=(self.u, self.v),
            vectors_crs=self.crs_rotatedlatlon,
        )
        result = mesh["vectors"].T
        expected = np.array(
            [
                [-4.066, 25.821, -8.955, -38.46],
                [16.031, -2.79, -11.93, 1.87],
                [15.049, 3.804, 1.578, 13.504],
            ]
        )
        assert np.allclose(result, expected, atol=0.001)

    def test__vectors_array_name(self):
        """Check operation with alternate vectors array name."""
        mesh = Transform.from_points(
            xs=self.lons,
            ys=self.lats,
            vectors=(self.u, self.v, self.w),
            vectors_array_name="squiggle",
        )
        result = mesh["squiggle"].T
        expected = np.array(
            [
                [10.385, -29.006, -6.416, -41.658],
                [10.947, -1.769, -13.627, -54.169],
                [22.301, 21.668, -3.759, -4.515],
            ]
        )
        assert np.allclose(result, expected, atol=0.001)

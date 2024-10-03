# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform.from_tiff`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.bridge import Transform
from geovista.pantry import fetch_raster

# skip tests if rasterio package unavailable
pytest.importorskip("rasterio")

# convert to string to exercise conversion back to Path
fname: str = str(fetch_raster("bahamas_rgb.tif"))


@pytest.mark.parametrize(
    ("count", "emsg"),
    [
        (1, "Require a band index of 1"),
        (3, r"Require a band index in the closed interval \[1, 3\]"),
    ],
)
@pytest.mark.parametrize("band", [0, 4])
def test_band_fail(mocker, band, count, emsg):
    """Test out of range image band."""
    dataset = mocker.MagicMock(count=count)
    mocker.patch("rasterio.open").return_value.__enter__.return_value = dataset

    with pytest.raises(ValueError, match=emsg):
        _ = Transform.from_tiff(fname, band=band)


def test_rgb_band_fail(mocker):
    """Test rgb/rgba image bands."""
    dataset = mocker.MagicMock(count=2)
    mocker.patch("rasterio.open").return_value.__enter__.return_value = dataset

    emsg = "Require a GeoTIFF with 3 or 4 bands"
    with pytest.raises(ValueError, match=emsg):
        _ = Transform.from_tiff(fname, rgb=True)


@pytest.mark.parametrize("rgb", [True, False])
@pytest.mark.parametrize("band", [1, 2, 3])
@pytest.mark.parametrize("unit", ["m", None])
def test_rgb_band(mocker, rgb, band, unit):
    """Test band behaviour with name units substitution."""
    if rgb:
        band = 3
    crs = mocker.sentinel.crs
    data = mocker.sentinel.data
    mocked_read = mocker.MagicMock(return_value=data)
    transform = mocker.sentinel.transform
    height, width = pixels_shape = 2, 3
    n_pixels = height * width
    kwargs = {
        "count": band,
        "crs": crs,
        "height": height,
        "read": mocked_read,
        "shape": pixels_shape,
        "transform": transform,
        "units": [unit] * band,
        "width": width,
    }
    dataset = mocker.MagicMock(**kwargs)
    mocker.patch("rasterio.open").return_value.__enter__.return_value = dataset

    if rgb:
        mocked_reshape = mocker.MagicMock(return_value=data)
        mocked_dstack = mocker.patch(
            "numpy.dstack", return_value=mocker.MagicMock(reshape=mocked_reshape)
        )

    cols_flatten = mocker.sentinel.cols_flatten
    rows_flatten = mocker.sentinel.rows_flatten
    cols = mocker.MagicMock(flatten=mocker.MagicMock(return_value=cols_flatten))
    rows = mocker.MagicMock(flatten=mocker.MagicMock(return_value=rows_flatten))
    mocked_meshgrid = mocker.patch("numpy.meshgrid", return_value=(cols, rows))

    xs, ys = np.arange(n_pixels), np.arange(n_pixels)
    mocked_xy = mocker.patch("rasterio.transform.xy", return_value=(xs, ys))

    expected = mocker.sentinel.mesh
    mocked_from_2d = mocker.patch(
        "geovista.bridge.Transform.from_2d", return_value=expected
    )

    name = "Elevation [{units}]"
    actual = Transform.from_tiff(fname, name=name, band=band, rgb=rgb)

    assert actual == expected

    args = () if rgb else (band,)
    mocked_read.assert_called_once_with(*args, masked=False)

    if rgb:
        mocked_dstack.assert_called_once_with(data)
        mocked_reshape.assert_called_once_with(-1, band)

    mocked_meshgrid.assert_called_once()
    args = mocked_meshgrid.call_args.args
    assert len(args) == 2
    np.testing.assert_array_equal(args[0], np.arange(width))
    np.testing.assert_array_equal(args[1], np.arange(height))
    assert mocked_meshgrid.call_args.kwargs == {"indexing": "xy"}

    mocked_xy.assert_called_once_with(transform, rows_flatten, cols_flatten)

    expected_kwargs = {
        "data": data,
        "name": name.format(units=str(unit)),
        "crs": crs,
        "rgb": rgb,
        "radius": None,
        "zlevel": None,
        "zscale": None,
        "clean": None,
    }
    mocked_from_2d.assert_called_once()
    args = mocked_from_2d.call_args.args
    assert len(args) == 2
    assert args[0].shape == pixels_shape
    assert args[1].shape == pixels_shape
    assert mocked_from_2d.call_args.kwargs == expected_kwargs


@pytest.mark.parametrize("sieve", [True])
@pytest.mark.parametrize("rgb", [False, True])
@pytest.mark.parametrize("masked", [False, True])
def test_extract(mocker, masked, rgb, sieve):
    """Test extract behaviour with and without image masking."""
    pixels_shape = height, width = 2, 3
    n_pixels = height * width
    band = 3 if rgb else 1
    crs = mocker.sentinel.crs
    dtypes = ["uint8"] * band
    size = mocker.sentinel.size
    transform = mocker.sentinel.transform

    shape = (band, height, width)
    data = np.ma.arange(np.prod(shape)).reshape(shape)
    mask = np.zeros(shape, dtype=bool)
    if masked:
        mask[:, 1:, :] = True
    if not rgb:
        data, mask = data[0], mask[0]
    data.mask = mask
    mocked_read = mocker.MagicMock(return_value=data)

    kwargs = {
        "count": band,
        "crs": crs,
        "dtypes": dtypes,
        "height": height,
        "read": mocked_read,
        "shape": pixels_shape,
        "transform": transform,
        "width": width,
    }
    dataset = mocker.MagicMock(**kwargs)
    mocker.patch("rasterio.open").return_value.__enter__.return_value = dataset

    cols_flatten = mocker.sentinel.cols_flatten
    rows_flatten = mocker.sentinel.rows_flatten
    cols = mocker.MagicMock(flatten=mocker.MagicMock(return_value=cols_flatten))
    rows = mocker.MagicMock(flatten=mocker.MagicMock(return_value=rows_flatten))
    mocked_meshgrid = mocker.patch("numpy.meshgrid", return_value=(cols, rows))

    xs, ys = np.arange(n_pixels), np.arange(n_pixels)
    mocked_xy = mocker.patch("rasterio.transform.xy", return_value=(xs, ys))

    expected_mesh = mocker.sentinel.mesh
    mesh = expected_mesh
    mocked_extract = mocker.MagicMock(return_value=expected_mesh)
    if masked:
        mesh = mocker.MagicMock(extract_points=mocked_extract)
    mocked_from_2d = mocker.patch(
        "geovista.bridge.Transform.from_2d", return_value=mesh
    )

    mocked_sieve = mocker.patch(
        "rasterio.features.sieve",
        side_effect=lambda mask, size: mask,  # noqa: ARG005
    )

    mocked_cast = mocker.patch(
        "geovista.bridge.cast_UnstructuredGrid_to_PolyData", return_value=expected_mesh
    )

    actual = Transform.from_tiff(
        fname, band=band, rgb=rgb, sieve=sieve, size=size, extract=True
    )

    assert actual == expected_mesh

    mocked_meshgrid.assert_called_once()
    args = mocked_meshgrid.call_args.args
    assert len(args) == 2
    np.testing.assert_array_equal(args[0], np.arange(width))
    np.testing.assert_array_equal(args[1], np.arange(height))
    assert mocked_meshgrid.call_args.kwargs == {"indexing": "xy"}

    mocked_xy.assert_called_once_with(transform, rows_flatten, cols_flatten)

    if rgb:
        data = np.dstack(data).reshape(-1, band)
        mask = mask[0]

    expected_kwargs = {
        "name": None,
        "crs": crs,
        "rgb": rgb,
        "radius": None,
        "zlevel": None,
        "zscale": None,
        "clean": None,
    }
    mocked_from_2d.assert_called_once()
    args = mocked_from_2d.call_args.args
    assert len(args) == 2
    assert args[0].shape == pixels_shape
    assert args[1].shape == pixels_shape
    kwargs = mocked_from_2d.call_args.kwargs
    actual = kwargs.pop("data")
    assert kwargs == expected_kwargs
    np.testing.assert_array_equal(actual, data.data)

    if masked:
        if sieve:
            gdal_mask = (~mask).astype(dtypes[0]) * 255
            assert mocked_sieve.call_count == 1
            args = mocked_sieve.call_args.args
            assert len(args) == 1
            np.testing.assert_array_equal(args[0], gdal_mask)
            assert mocked_sieve.call_args.kwargs == {"size": size}

        assert mocked_extract.call_count == 1
        args = mocked_extract.call_args.args
        assert len(args) == 1
        np.testing.assert_array_equal(args[0], ~np.ravel(mask))
        assert mocked_extract.call_args.kwargs == {"adjacent_cells": False}

        mocked_cast.assert_called_once_with(expected_mesh)
    else:
        assert mocked_sieve.call_count == 0
        assert mocked_extract.call_count == 0
        assert mocked_cast.call_count == 0

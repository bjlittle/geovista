# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.cache.CACHE`."""

from __future__ import annotations

from pathlib import Path

import pytest

from geovista.cache import CACHE, READ_MODE, Decompress


def test_fetch():
    """Test the download of an asset."""
    asset = Path("pantry/data/lams/london.nc.bz2")
    asset_cache = CACHE.abspath / asset
    asset_cache.unlink(missing_ok=True)
    actual = CACHE.fetch(asset.as_posix())
    assert asset.name == Path(actual).name


@pytest.mark.parametrize("keyword", [False, True])
def test_fetch__parent(mocker, tmp_path, keyword):
    """Test the asset parent directory exists before pooch fetches the asset."""
    fname = "pantry/meshes/asset.vtk.bz2"
    parent = tmp_path / "pantry" / "meshes"
    _ = mocker.patch.object(CACHE, "path", tmp_path)

    def fetch(*args: object, **kwargs: object) -> str:  # noqa: ARG001
        # pooch creates a missing parent without exist_ok, so racing
        # processes fail unless it already exists
        assert parent.is_dir()
        return str(parent / "asset.vtk")

    _ = mocker.patch.object(CACHE, "_fetch", side_effect=fetch)
    args, kwargs = ((), {"fname": fname}) if keyword else ((fname,), {})
    result = CACHE.fetch(*args, **kwargs)
    assert result == str(parent / "asset.vtk")


@pytest.mark.xfail(reason="flaky read permission bits", strict=False)
def test_fetch__downloader():
    """Test downloaded asset is readable."""
    fname = "geodesic.test_BBox.test_outline.png"
    asset = Path(CACHE.fetch(f"tests/unit/{fname}"))
    assert asset.is_file()
    assert (asset.stat().st_mode & READ_MODE) == READ_MODE


@pytest.mark.xfail(reason="flaky read permission bits", strict=False)
def test_fetch__downloader__decompress():
    """Test downloaded assets (compressed and uncompressed) are readable."""
    fname, ext = "falklands.nc", "bz2"
    processor = Decompress(method="auto", name=fname)

    asset = Path(CACHE.fetch(f"pantry/data/lams/{fname}.{ext}", processor=processor))
    assert asset.is_file()
    assert (asset.stat().st_mode & READ_MODE) == READ_MODE

    asset = asset.with_name(f"{asset.name}.{ext}")
    assert asset.is_file()
    assert (asset.stat().st_mode & READ_MODE) == READ_MODE


@pytest.mark.xfail(reason="flaky HTTP 403", strict=False)
def test_fetch__no_user_agent():
    """Test the download of an asset with no user-agent header."""
    asset = Path("pantry/data/lams/polar.nc.bz2")
    asset_cache = CACHE.abspath / asset
    asset_cache.unlink(missing_ok=True)
    actual = CACHE._fetch(str(asset))
    assert asset.name == Path(actual).name

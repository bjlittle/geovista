# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.pantry.textures._fetch_texture`."""

from __future__ import annotations

from pathlib import Path

import pyvista as pv

from geovista.pantry.textures import checkerboard


def test_location():
    """Test the location of the texture in the cache is returned."""
    result = checkerboard(location=True)
    assert isinstance(result, str)
    assert Path(result).name == "uv-checker-map-4k.png"
    assert Path(result).exists()


def test_texture():
    """Test the texture is returned."""
    assert isinstance(checkerboard(), pv.Texture)

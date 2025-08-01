# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.pantry.meshes.lfric`."""

from __future__ import annotations

import pytest

from geovista.pantry.meshes import LFRIC_RESOLUTION, lfric


def test_resolution_warning(mocker):
    """Test warning raised of invalid cubed-sphere resolution request."""
    processor = mocker.sentinel.processor
    _ = mocker.patch("pooch.Decompress", return_value=processor)
    resource = mocker.sentinel.resource
    _ = mocker.patch("geovista.cache.CACHE.fetch", return_value=resource)
    mesh = mocker.sentinel.mesh
    _ = mocker.patch("pyvista.read", return_value=mesh)
    bad = "r24"
    wmsg = f"geovista detected unknown LFRic cubed-sphere resolution {bad!r}"
    with pytest.warns(UserWarning, match=wmsg):
        result = lfric(resolution=bad)

    import pooch  # noqa: PLC0415
    import pyvista as pv  # noqa: PLC0415

    from geovista.cache import CACHE  # noqa: PLC0415

    fname = f"lfric_{LFRIC_RESOLUTION}.vtk"
    pooch.Decompress.assert_called_once_with(method="auto", name=fname)
    CACHE.fetch.assert_called_once_with(
        f"pantry/meshes/{fname}.bz2", processor=processor
    )
    pv.read.assert_called_once_with(resource)
    assert result == mesh

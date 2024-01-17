# Copyright 2024, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Reusable data, images, etcetera, for supporting internal and user scripts.

Notes
-----
.. versionadded:: 0.5.0

"""
from __future__ import annotations

import pooch
import pyvista as pv

from geovista.cache import CACHE
from geovista.common import COASTLINES_RESOLUTION

__all__ = [
    "fetch_coastlines",
]


def fetch_coastlines(resolution: str | None = None) -> pv.PolyData:
    """Get the Natural Earth coastlines for the required resolution.

    If the resource is not already available in the geovista
    :data:`geovista.cache.CACHE`, then it will be downloaded from the
    :data:`geovista.cache.BASE_URL`.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m`` or ``10m``. Defaults to
        :data:`geovista.common.COASTLINES_RESOLUTION`.

    Returns
    -------
    PolyData
        The coastlines mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if resolution is None:
        resolution = COASTLINES_RESOLUTION

    fname = f"ne_coastlines_{resolution}.vtk"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"natural_earth/physical/{fname}.bz2", processor=processor)

    return pv.read(resource)

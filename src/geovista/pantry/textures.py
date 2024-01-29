# Copyright (c) 2024, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Download, cache and load image textures.

Notes
-----
.. versionadded:: 0.5.0

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import lazy_loader as lazy

from geovista.cache import CACHE

if TYPE_CHECKING:
    import pyvista as pv

    # type aliases
    TextureLike = str | pv.Texture

# lazy import third-party dependencies
pv = lazy.load("pyvista")

__all__ = [
    "blue_marble",
    "checkerboard",
    "natural_earth_1",
    "natural_earth_hypsometric",
]


def _fetch_texture(fname: str, location: bool | None = False) -> TextureLike:
    """Get the texture resource from the cache.

    If the resource is not already available in the geovista
    :data:`geovista.cache.CACHE`, then it will be downloaded from the
    :data:`geovista.cache.BASE_URL`.

    Parameters
    ----------
    fname : str
        The base file name of the resource, excluding any directory prefix.
    location : bool, default=False
        Determine whether the absolute path filename to the texture resource
        location within the cache is returned, or the actual texture.

    Returns
    -------
    str or Texture
        The PyVista texture filename or the texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    resource = CACHE.fetch(f"pantry/textures/{fname}")
    if not location:
        resource = pv.read_texture(resource)
    return resource


def blue_marble(location: bool | None = False) -> TextureLike:
    """Get the NASA Blue Marble Next Generation with topography and bathymetry texture.

    If the resource is not already available in the geovista
    :data:`geovista.cache.CACHE`, then it will be downloaded from the
    :data:`geovista.cache.BASE_URL`.

    Parameters
    ----------
    location : bool, default=False
        Determine whether the absolute path filename to the texture resource
        location within the cache is returned, or the actual texture.

    Returns
    -------
    str or Texture
        The PyVista texture filename or the texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _fetch_texture("world.topo.bathy.200412.3x5400x2700.jpg", location=location)


def checkerboard(location: bool | None = False) -> TextureLike:
    """Get the UV checker map 4K texture.

    If the resource is not already available in the geovista
    :data:`geovista.cache.CACHE`, then it will be downloaded from the
    :data:`geovista.cache.BASE_URL`.

    Parameters
    ----------
    location : bool, default=False
        Determine whether the absolute path filename to the texture resource
        location within the cache is returned, or the actual texture.

    Returns
    -------
    str or Texture
        The PyVista texture filename or the texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _fetch_texture("uv-checker-map-4k.png", location=location)


def natural_earth_1(location: bool | None = False) -> TextureLike:
    """Get the 1:50m Natural Earth texture.

    This is the Natural Earth 1 with shaded relief and water texture.

    This resource has been down-sampled to 65% of its original resolution.

    If the resource is not already available in the geovista
    :data:`geovista.cache.CACHE`, then it will be downloaded from the
    :data:`geovista.cache.BASE_URL`.

    Parameters
    ----------
    location : bool, default=False
        Determine whether the absolute path filename to the texture resource
        location within the cache is returned, or the actual texture.

    Returns
    -------
    str or Texture
        The PyVista texture filename or the texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _fetch_texture("NE1_50M_SR_W.jpg", location=location)


def natural_earth_hypsometric(location: bool | None = False) -> TextureLike:
    """Get the 1:50m Natural Earth texture.

    This is the Natural Earth cross-blended hypsometric tints with shaded relief and
    water texture.

    This resource has been down-sampled to 65% of its original resolution.

    If the resource is not already available in the geovista
    :data:`geovista.cache.CACHE`, then it will be downloaded from the
    :data:`geovista.cache.BASE_URL`.

    Parameters
    ----------
    location : bool, default=False
        Determine whether the absolute path filename to the texture resource
        location within the cache is returned, or the actual texture.

    Returns
    -------
    str or Texture
        The PyVista texture filename or the texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _fetch_texture("HYP_50M_SR_W.jpg", location=location)

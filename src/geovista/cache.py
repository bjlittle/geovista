# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Convenience functions to access, download and cache geovista resources.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from importlib.resources import files
import os

import pooch
import pyvista as pv

from .common import COASTLINES_RESOLUTION
from .config import resources

__all__ = [
    "CACHE",
    "blue_marble",
    "checkerboard",
    "fetch_coastlines",
    "natural_earth_1",
    "natural_earth_hypsometric",
    "pooch_mute",
    "reload_registry",
]

# Type aliases.
TextureLike = str | pv.Texture

#: Base URL for geovista resources.
BASE_URL: str = "https://github.com/bjlittle/geovista-data/raw/{version}/data/"

#: Pin to use the specific geovista-data repository version for geovista resources.
DATA_VERSION: str = "2024.01.1"

#: Environment variable to override pooch cache manager path.
ENV: str = "GEOVISTA_CACHEDIR"

#: Environment variable to override default geovista-data version.
GEOVISTA_DATA_VERSION: str = os.environ.get("GEOVISTA_DATA_VERSION", DATA_VERSION)

#: The number of retry attempts to download a resource.
RETRY_ATTEMPTS: int = 3

URL_DKRZ_FESOM: str = (
    "https://swift.dkrz.de/v1/dkrz_0262ea1f00e34439850f3f1d71817205/FESOM/"
    "tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc"
)

#: Cache manager for geovista resources.
CACHE: pooch.Pooch = pooch.create(
    path=resources["cache_dir"],
    base_url=BASE_URL,
    version=GEOVISTA_DATA_VERSION,
    version_dev="main",
    registry=None,
    retry_if_failed=RETRY_ATTEMPTS,
    env=ENV,
    urls={
        "tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc": URL_DKRZ_FESOM  # noqa: E501
    },
)

CACHE.load_registry(
    (files(__package__) / "registry.txt").open("r", encoding="utf-8", errors="strict")
)

#: Verbosity status of the pooch cache manager logger.
GEOVISTA_POOCH_MUTE: bool = (
    os.environ.get("GEOVISTA_POOCH_MUTE", "false").lower() == "true"
)


def _fetch_texture(fname: str, location: bool | None = False) -> TextureLike:
    """Get the texture resource from the cache.

    If the resource is not already available in the geovista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

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
    resource = CACHE.fetch(f"raster/{fname}")
    if not location:
        resource = pv.read_texture(resource)
    return resource


def blue_marble(location: bool | None = False) -> TextureLike:
    """Get the NASA Blue Marble Next Generation with topography and bathymetry texture.

    If the resource is not already available in the geovista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

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

    If the resource is not already available in the geovista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

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


def fetch_coastlines(resolution: str | None = None) -> pv.PolyData:
    """Get the Natural Earth coastlines for the required resolution.

    If the resource is not already available in the geovista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

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


def natural_earth_1(location: bool | None = False) -> TextureLike:
    """Get the 1:50m Natural Earth texture.

    This is the Natural Earth 1 with shaded relief and water texture.

    This resource has been down-sampled to 65% of its original resolution.

    If the resource is not already available in the geovista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

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

    If the resource is not already available in the geovista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

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


def pooch_mute(silent: bool = True) -> None:
    """Control the pooch cache manager logger verbosity.

    Updates the status variable :data:`GEOVISTA_POOCH_MUTE`.

    Parameters
    ----------
    silent : bool, optional
        Whether to silence or activate the pooch cache manager logger messages to the
        console.

    Notes
    -----
    .. versionadded:: 0.5.0

    """
    global GEOVISTA_POOCH_MUTE

    level = "WARNING" if silent else "NOTSET"
    pooch.utils.get_logger().setLevel(level)
    GEOVISTA_POOCH_MUTE = silent


def reload_registry(fname: str | None = None) -> None:
    """Refresh the registry of the :data:`CACHE`.

    Parameters
    ----------
    fname : str, optional
        The filename of the registry to be loaded. If ``None``, defaults to
        the ``registry.txt`` resource file packaged with geovista.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if fname is None:
        fname = (files(__package__) / "registry.txt").open(
            "r", encoding="utf-8", errors="strict"
        )
    CACHE.load_registry(fname)


# configure the pooch cache manager logger verbosity
pooch_mute(GEOVISTA_POOCH_MUTE)

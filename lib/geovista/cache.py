from importlib.resources import open_text
from typing import Optional

import pooch
import pyvista as pv

from . import config

__all__ = [
    "BASE_URL",
    "CACHE",
    "RETRY_ATTEMPTS",
    "blue_marble",
    "checkerboard",
    "fetch_coastlines",
    "reload_registry",
]

#: Base URL for GeoVista resources.
BASE_URL: str = "https://github.com/bjlittle/geovista-data/raw/main/data/"

#: Environment variable to override pooch cache manager path.
ENV = "GEOVISTA_CACHEDIR"

#: The number of retry attempts to download a resource.
RETRY_ATTEMPTS: int = 3

#: Cache manager for GeoVista resources.
CACHE: pooch.Pooch = pooch.create(
    path=config["cache_dir"],
    base_url=BASE_URL,
    registry=None,
    retry_if_failed=RETRY_ATTEMPTS,
    env=ENV,
)

CACHE.load_registry(open_text(__package__, "registry.txt"))


def blue_marble() -> pv.Texture:
    """
    Get the NASA Blue Marble Next Generation with topography and bathymetry
    texture.

    If the resource is not already available in the GeoVista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

    Returns
    -------
    Texture
        The PyVista texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = CACHE.fetch("raster/world.topo.bathy.200412.3x5400x2700.jpg")
    texture = pv.read_texture(fname)
    return texture


def checkerboard() -> pv.Texture:
    """
    Get the UV checker map 4K texture.

    If the resource is not already available in the GeoVista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

    """
    fname = CACHE.fetch("raster/uv-checker-map-4k.png")
    texture = pv.read_texture(fname)
    return texture


def fetch_coastlines(resolution: str = "110m") -> pv.PolyData:
    """
    Get the Natural Earth coastlines for the required resolution.

    If the Natural Earth coastlines resource is not already available in
    the GeoVista :data:`CACHE`, then it will be downloaded from the :data:`BASE_URL`.

    Parameters
    ----------
    resolution : str, default="110m"
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m`` or ``10m``.

    Returns
    -------
    PolyData
        The coastlines mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = CACHE.fetch(f"natural_earth/physical/ne_coastlines_{resolution}.vtk")
    mesh = pv.read(fname)
    return mesh


def reload_registry(fname: Optional[str] = None) -> None:
    """
    Refresh the registry of the :data:`CACHE`.

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
        fname = open_text(__package__, "registry.txt")
    CACHE.load_registry(fname)

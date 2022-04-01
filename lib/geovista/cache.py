"""
Provide convenience functions to access, download and cache geovista resources.

"""
from importlib.resources import open_text
import os
from typing import Optional, Union

import pooch
import pyvista as pv

from .config import resources
from .log import get_logger

__all__ = [
    "CACHE",
    "blue_marble",
    "checkerboard",
    "fetch_coastlines",
    "lfric",
    "logger",
    "natural_earth_1",
    "natural_earth_hypsometric",
    "reload_registry",
]

# Configure the logger.
logger = get_logger(__name__)

# Type aliases.
TextureLike = Union[str, pv.Texture]

#: Base URL for GeoVista resources.
BASE_URL: str = "https://github.com/bjlittle/geovista-data/raw/main/data/"

#: The default Natural Earth coastlines resolution.
DEFAULT_RESOLUTION_COASTLINES: str = "110m"

#: The default LFRic Model unstructured cubed-sphere resolution.
DEFAULT_RESOLUTION_LFRIC: str = "c96"

#: Environment variable to override pooch cache manager path.
ENV = "GEOVISTA_CACHEDIR"

#: The number of retry attempts to download a resource.
RETRY_ATTEMPTS: int = 3

#: Cache manager for GeoVista resources.
CACHE: pooch.Pooch = pooch.create(
    path=resources["cache_dir"],
    base_url=BASE_URL,
    registry=None,
    retry_if_failed=RETRY_ATTEMPTS,
    env=ENV,
)

CACHE.load_registry(open_text(__package__, "registry.txt"))

if os.environ.get("GEOVISTA_POOCH_MUTE"):
    pooch.utils.get_logger().setLevel("WARNING")


def _fetch_texture(fname: str, location: Optional[bool] = False) -> TextureLike:
    """
    Get the texture resource from cache.

    If the resource is not already available in the GeoVista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

    Parameters
    ----------
    fname : str
        The base file name of the resource, excluding any directory prefix.
    location : bool, default=False
        Determine whether the absolute path filename to the texture resource
        location within the cache is returned

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


def blue_marble(location: Optional[bool] = False) -> TextureLike:
    """
    Get the NASA Blue Marble Next Generation with topography and bathymetry
    texture.

    If the resource is not already available in the GeoVista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

    Parameters
    ----------
    location : bool, default=False
        Determine whether the absolute path filename to the texture resource
        location within the cache is returned.

    Returns
    -------
    str or Texture
        The PyVista texture filename or the texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _fetch_texture("world.topo.bathy.200412.3x5400x2700.jpg", location=location)


def checkerboard(location: Optional[bool] = False) -> TextureLike:
    """
    Get the UV checker map 4K texture.

    If the resource is not already available in the GeoVista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

    Parameters
    ----------
    location : bool, default=False
        Determine whether the absolute path filename to the texture resource
        location within the cache is returned.

    Returns
    -------
    str or Texture
        The PyVista texture filename or the texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _fetch_texture("uv-checker-map-4k.png", location=location)


def fetch_coastlines(resolution: Optional[str] = None) -> pv.PolyData:
    """
    Get the Natural Earth coastlines for the required resolution.

    If the resource is not already available in the GeoVista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the Natural Earth coastlines, which may be either
        ``110m``, ``50m`` or ``10m``. Default is
        :data:`DEFAULT_RESOLUTION_COASTLINES`.

    Returns
    -------
    PolyData
        The coastlines mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if resolution is None:
        resolution = DEFAULT_RESOLUTION_COASTLINES

    fname = f"ne_coastlines_{resolution}.vtk"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"natural_earth/physical/{fname}.bz2", processor=processor)
    mesh = pv.read(resource)
    return mesh


def lfric(resolution: Optional[str] = None) -> pv.PolyData:
    """
    Get the LFRic Model unstructured cubed-sphere at the specified resolution.

    If the resource is not already available in the GeoVista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the LFRic Model mesh. Defaults to
        :data:`DEFAULT_RESOLUTION_LFRIC`.

    Returns
    -------
    PolyData
        The LFRic mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if resolution is None:
        resolution = DEFAULT_RESOLUTION_LFRIC

    fname = f"lfric_{resolution}.vtk"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"mesh/{fname}.bz2", processor=processor)
    mesh = pv.read(resource)
    return mesh


def natural_earth_1(location: Optional[bool] = False) -> TextureLike:
    """
    Get the 1:50m Natural Earth 1 with shaded relief and water texture
    (down-sampled to 65%).

    If the resource is not already available in the GeoVista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

    Returns
    -------
    str or Texture
        The PyVista texture filename or the texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _fetch_texture("NE1_50M_SR_W.jpg", location=location)


def natural_earth_hypsometric(location: Optional[bool] = False) -> TextureLike:
    """
    Get the 1:50m Natural Earth cross-blended hypsometric tints with shaded
    relief and water texture (down-sampled to 65%).

    If the resource is not already available in the GeoVista :data:`CACHE`,
    then it will be downloaded from the :data:`BASE_URL`.

    Returns
    -------
    str or Texture
        The PyVista texture filename or the texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _fetch_texture("HYP_50M_SR_W.jpg", location=location)


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

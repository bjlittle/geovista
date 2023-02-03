"""
GeoVista
========

Cartographic rendering and mesh analytics powered by PyVista.

Provides:
  1. An agnostic bridge to transform rectilinear, curvilinear and unstructured
     geospatial data to native geo-located PyVista mesh instances
  2. Compliments PyVista with cartographic features for processing, projecting
     and rendering geo-located meshes
  3. Support for interactive 3D visulization of geo-located meshes
  4. Coordinate Reference System (CRS) support, with an awareness of Cartopy
     CRSs through the commonality of the Python interface to PROJ (PyPROJ)
     package

Notes
-----
.. versionadded:: 0.1.0

"""
import logging

from .bridge import Transform  # noqa: F401
from .cache import (  # noqa: F401
    blue_marble,
    checkerboard,
    fetch_coastlines,
    natural_earth_1,
    natural_earth_hypsometric,
)
from .common import vtk_warnings_off, vtk_warnings_on  # noqa: F401
from .core import MeridianSlice, combine, cut_along_meridian  # noqa: F401
from .crs import from_wkt, get_central_meridian, set_central_meridian  # noqa: F401
from .filters import cast_UnstructuredGrid_to_PolyData, remesh  # noqa: F401
from .geodesic import BBox, line, panel, wedge  # noqa: F401
from .geometry import get_coastlines  # noqa: F401
from .geoplotter import GeoBackgroundPlotter, GeoMultiPlotter, GeoPlotter  # noqa: F401
from .raster import wrap_texture  # noqa: F401

try:
    from ._version import version as __version__  # noqa: F401
except ModuleNotFoundError:
    __version__ = "unknown"

__all__ = ["logger"]

# let's assume this is a sane default to adopt
vtk_warnings_off()

# create a simple logger to support examples verbose diagnostics
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel("WARNING")

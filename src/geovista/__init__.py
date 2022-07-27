# pylint: disable=missing-module-docstring
from ._version import version as __version__  # noqa: F401
from .bridge import Transform  # noqa: F401
from .cache import (  # noqa: F401
    blue_marble,
    checkerboard,
    lfric,
    natural_earth_1,
    natural_earth_hypsometric,
)
from .core import MeridianSlice, combine, cut_along_meridian  # noqa: F401
from .crs import from_wkt, get_central_meridian, set_central_meridian  # noqa: F401
from .filters import cast_UnstructuredGrid_to_PolyData, remesh  # noqa: F401
from .geodesic import BBox, line, panel, wedge  # noqa: F401
from .geometry import get_coastlines  # noqa: F401
from .geoplotter import GeoBackgroundPlotter, GeoMultiPlotter, GeoPlotter  # noqa: F401
from .log import get_logger
from .raster import wrap_texture  # noqa: F401

__all__ = ["logger"]

# Configure the top level logger.
logger = get_logger(__name__)

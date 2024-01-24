# Copyright 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Cartographic rendering and mesh analytics powered by PyVista.

Provides:
  1. An agnostic bridge to transform rectilinear, curvilinear and unstructured
     geospatial data to native geolocated PyVista mesh instances
  2. Compliments PyVista with cartographic features for processing, projecting
     and rendering geolocated meshes
  3. Support for interactive 3D visualization of geolocated meshes
  4. Coordinate Reference System (CRS) support, with an awareness of Cartopy
     CRSs through the commonality of the Python interface to PROJ (PyPROJ)
     package

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

import os

from .bridge import Transform  # noqa: F401
from .common import vtk_warnings_off, vtk_warnings_on  # noqa: F401
from .core import slice_cells, slice_lines  # noqa: F401
from .crs import from_wkt, to_wkt  # noqa: F401
from .geodesic import BBox, line, panel, wedge  # noqa: F401
from .geometry import coastlines  # noqa: F401
from .geoplotter import GeoPlotter  # noqa: F401
from .pantry import fetch_coastlines  # noqa: F401
from .pantry.textures import (  # noqa: F401
    blue_marble,
    checkerboard,
    natural_earth_1,
    natural_earth_hypsometric,
)
from .report import Report  # noqa: F401

try:
    from ._version import version as __version__
except ModuleNotFoundError:
    __version__ = "unknown"

# let's assume this is a sane default to adopt
vtk_warnings_off()

#: flag when performing image testing
GEOVISTA_IMAGE_TESTING: bool = (
    os.environ.get("GEOVISTA_IMAGE_TESTING", "false").lower() == "true"
)

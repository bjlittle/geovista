# Copyright 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Cartographic rendering and mesh analytics powered by PyVista.

Provides:
  1. An agnostic bridge to transform rectilinear, curvilinear and unstructured
     geospatial data to native geolocated PyVista mesh instances.
  2. Compliments PyVista with cartographic features for processing, projecting
     and rendering geolocated meshes.
  3. Support for interactive 3D visualization of geolocated meshes.
  4. Coordinate Reference System (CRS) support, with an awareness of Cartopy
     CRSs through the commonality of the Python interface to PROJ (PyPROJ)
     package.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

import os

import lazy_loader as lazy

# lazy import submodules
(__getattr__, __dir__, __all__) = lazy.attach_stub(__name__, __file__)

try:
    from ._version import version as __version__
except ModuleNotFoundError:
    __version__ = "unknown"

#: flag when performing image testing
GEOVISTA_IMAGE_TESTING: bool = (
    os.environ.get("GEOVISTA_IMAGE_TESTING", "false").lower() == "true"
)

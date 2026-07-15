# Copyright (c) 2021, GeoVista Contributors.
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

import lazy_loader as lazy

from .themes import set_plot_theme

# submodules are lazily imported
(__getattr__, __dir__, __all__) = lazy.attach_stub(__name__, __file__)

try:
    from ._version import __version__
except ModuleNotFoundError as e:
    if e.name != f"{__name__}._version":
        raise

    try:
        from importlib.metadata import PackageNotFoundError, version

        __version__ = version("geovista")
        """The ``major.minor.patch`` version string."""
    except PackageNotFoundError:
        __version__ = "0+unknown"

set_plot_theme("geovista", bootstrap=True)

# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for how importing :mod:`geovista` registers the ``gv`` namespace."""

from __future__ import annotations

import subprocess
import sys

#: Imports geovista, then fails unless every mesh has the namespace, and
#: fails if registering it imported anything heavy.
LIGHT = """
import sys

import pyvista as pv

import geovista

assert type(pv.PolyData().gv).__name__ == "GeoVistaAccessor"
heavy = {"pyproj", "pint", "geovista.globe", "geovista.crs"} & set(sys.modules)
assert not heavy, heavy
"""


def test_importing_geovista_registers_the_namespace():
    """Test that importing geovista adds mesh.gv, and imports nothing heavy."""
    subprocess.run([sys.executable, "-c", LIGHT], check=True)  # noqa: S603

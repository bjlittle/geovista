# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for how :mod:`geovista.globe` imports ``pint``."""

from __future__ import annotations

import subprocess
import sys

#: Builds and reads a globe's plain values, then fails if ``pint`` was imported.
PLAIN = """
import sys

import pyvista as pv

from geovista.globe import Globe

globe = Globe(radius=6371000, exaggeration=20)
globe.render_radius, globe.exaggeration, globe.exaggeration_below, globe.scale
globe == Globe(), hash(globe), repr(globe)
mesh = pv.Sphere()
globe.to_mesh(mesh)
Globe.from_mesh(mesh)
Globe.from_mesh(pv.Sphere())
loaded = [name for name in sys.modules if name == "pint" or name.startswith("pint.")]
assert not loaded, loaded
"""


def test_a_globe_imports_no_pint():
    """Test that a globe imports no pint until its radius is read, even on a mesh."""
    subprocess.run([sys.executable, "-c", PLAIN], check=True)  # noqa: S603

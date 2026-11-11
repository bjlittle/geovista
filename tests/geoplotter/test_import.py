# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that drawing a scene imports no ``pint``."""

from __future__ import annotations

import subprocess
import sys

SCENE = """
import sys
import types

import geovista as gv
from geovista.globe import Globe

p = gv.GeoPlotter(off_screen=True, globe=Globe(render_radius=2))
p.add_mesh(gv.Transform.from_1d([0.0, 10.0, 20.0], [0.0, 10.0]))
p.add_graticule()
pint = sys.modules.get("pint")
loaded = sorted(name for name in sys.modules if name.startswith("pint."))
if type(pint) is types.ModuleType:
    loaded.append("pint")
assert not loaded, loaded
"""


def test_drawing_a_scene_imports_no_pint():
    """Test that a scene on a globe is drawn without importing pint."""
    subprocess.run([sys.executable, "-c", SCENE], check=True)  # noqa: S603


HEIGHTS = """
import sys
import types

import geovista as gv
from geovista.globe import Globe

p = gv.GeoPlotter(off_screen=True, globe=Globe(render_radius=2, exaggeration=20))
grid = gv.Transform.from_1d([0.0, 10.0, 20.0], [0.0, 10.0])
p.add_mesh(grid, height=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
p.add_mesh(grid, depth=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
p.add_points(xs=[0.0, 10.0], ys=[0.0, 10.0], depth=[5.0, 6.0])
p.add_mesh(gv.Transform.from_1d([0.0, 10.0], [0.0, 10.0], height=1.0, globe=Globe()))
pint = sys.modules.get("pint")
loaded = sorted(name for name in sys.modules if name.startswith("pint."))
if type(pint) is types.ModuleType:
    loaded.append("pint")
assert not loaded, loaded
"""


def test_drawing_heights_imports_no_pint():
    """Test that heights given to a scene as plain numbers import no pint."""
    subprocess.run([sys.executable, "-c", HEIGHTS], check=True)  # noqa: S603

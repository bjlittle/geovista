# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for how the :mod:`geovista.bridge` imports ``pint`` with heights."""

from __future__ import annotations

import subprocess
import sys

PLAIN = """
import sys
import types

from geovista.bridge import Transform

mesh = Transform.from_1d([0, 10], [0, 10], height=[[1.0, 2.0], [3.0, 4.0]])
cloud = Transform.from_points([0, 10], [0, 10], depth=[5.0, 6.0])
mesh.gv.height, mesh.gv.depth, cloud.gv.height, cloud.gv.depth

# geovista.units binds pint lazily, so only a pint that has run counts
pint = sys.modules.get("pint")
loaded = sorted(name for name in sys.modules if name.startswith("pint."))
if type(pint) is types.ModuleType:
    loaded.append("pint")
assert not loaded, loaded
"""


def test_plain_heights_import_no_pint():
    """Test that heights given as plain numbers never import pint."""
    subprocess.run([sys.executable, "-c", PLAIN], check=True)  # noqa: S603

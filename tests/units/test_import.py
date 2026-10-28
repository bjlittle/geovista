# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for how :mod:`geovista.units` imports ``pint``."""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys

import pint

import geovista
from geovista import units

#: The top-level packages only :mod:`geovista.units` may import, so that
#: replacing ``pint-cf`` touches one module (globe spec §4.2).
UNITS_ONLY = {"lark", "pint", "pint_cf"}

#: Converts plain numbers, then fails if any ``pint`` module was loaded.
PLAIN = """
import sys
import types

import numpy as np

import geovista.units as units

units.to_metres(1.0)
units.to_metres(np.ones(3))
units.to_degrees(1.0)
# geovista.units binds pint lazily, so only a pint that has run counts
pint = sys.modules.get("pint")
loaded = sorted(name for name in sys.modules if name.startswith("pint."))
if type(pint) is types.ModuleType:
    loaded.append("pint")
assert not loaded, loaded
"""


def test_plain_numbers_never_import_pint():
    """Test that converting plain numbers never imports pint, which is slow."""
    subprocess.run([sys.executable, "-c", PLAIN], check=True)  # noqa: S603


def test_one_registry_serves_every_call():
    """Test that the registry is built once, since each costs 60 ms."""
    assert units._registry() is units._registry()


def test_only_units_imports_pint():
    """Test that no module but geovista.units imports pint, pint-cf or lark."""
    package = Path(geovista.__file__).parent
    importers = set()
    for path in package.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            else:
                continue
            if any(name.split(".")[0] in UNITS_ONLY for name in names):
                importers.add(path.relative_to(package).as_posix())
    assert importers == {"units.py"}


def test_the_quantity_alias_resolves():
    """Test that the Quantity alias resolves to pint's quantity at runtime."""
    assert units.Quantity.__value__ is pint.Quantity

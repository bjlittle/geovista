# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Guards that every radius became a globe (scene spec §4.2 and scene spec §4.3)."""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

import pytest

import geovista
from geovista.common import get_modules

#: The package source, whose modules the guards read.
PACKAGE = Path(geovista.__file__).parent

#: The private functions of scene spec §3.1 that took a radius.
PRIVATE = [
    ("geoplotter", "_lfric_mesh"),
    ("geoplotter", "GeoPlotterBase._add_graticule_labels"),
    ("geodesic", "BBox._generate_bbox_mesh"),
    ("transform", "_record_zlevels"),
]


def _callables(module: object) -> list[tuple[str, object]]:
    """Return each public function and method a module defines, by name."""
    found = []
    for name, value in vars(module).items():
        if name.startswith("_") or getattr(value, "__module__", None) != getattr(
            module, "__name__", None
        ):
            continue
        if inspect.isclass(value):
            for attr, member in vars(value).items():
                if (not attr.startswith("_") or attr in ("__init__", "__call__")) and (
                    inspect.isfunction(member) or isinstance(member, classmethod)
                ):
                    found.append((f"{name}.{attr}", member))
        elif callable(value):
            found.append((name, value))
    return found


def _parameters(function: object) -> list[str]:
    """Return the parameter names of a function, or none for a builtin."""
    if isinstance(function, classmethod):
        function = function.__func__
    try:
        return list(inspect.signature(function).parameters)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return []


def test_no_function_takes_a_radius():
    """Test no public function or method of geovista takes a radius, but the globe."""
    offenders = []
    for name in get_modules("geovista"):
        if name == "__main__":
            continue
        try:
            module = importlib.import_module(f"geovista.{name}")
        except ModuleNotFoundError as error:
            # an optional dependency, such as pyvistaqt for geovista.qt
            if error.name and not error.name.startswith("geovista"):
                continue
            raise
        offenders.extend(
            f"geovista.{name}.{qualname}"
            for qualname, function in _callables(module)
            if "radius" in _parameters(function)
        )
    assert offenders == ["geovista.globe.Globe.__init__"]


@pytest.mark.parametrize(("module", "qualname"), PRIVATE)
def test_no_private_function_of_the_census_takes_a_radius(module, qualname):
    """Test the private functions that took a radius take none."""
    value: object = importlib.import_module(f"geovista.{module}")
    for part in qualname.split("."):
        value = getattr(value, part)
    assert "radius" not in _parameters(value)


def test_only_the_globe_reads_gvradius():
    """Test only common, which retires it, and globe, which reads it, name gvRadius."""
    naming = set()
    for path in sorted(PACKAGE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            named = (isinstance(node, ast.Name) and node.id == "GV_FIELD_RADIUS") or (
                isinstance(node, ast.alias) and node.name == "GV_FIELD_RADIUS"
            )
            if named:
                naming.add(path.relative_to(PACKAGE).as_posix())
    assert naming == {"common.py", "globe.py"}

# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Policy gate that every test that renders carries the ``image`` marker.

Rendering needs a display or a GPU, and segfaults without one, taking its
``pytest-xdist`` worker down with it. ``pytest -m "not image"`` is how a
contributor without either runs the suite, which is only safe if every test
that draws is marked ``image``. CI renders under a virtual display, so a
missing marker never fails there (#2596).

A test draws when it calls one of :data:`DRAWING`, or an ``export_*`` method,
directly or through a function or fixture defined in the same module. It is
marked when ``image`` decorates the test or its class, or the module's
``pytestmark`` holds it. The ``example`` marker selects the gallery image
tests, a subset of the ``image`` tests, so it must never appear without
``image``.

The corpus is every module beneath ``tests``, read as source and never
imported, so this module needs no display and never skips. A test that only
appears to draw is exempt in :data:`EXEMPT`, with the reason beside it.

"""

from __future__ import annotations

import ast
from pathlib import Path

TESTS = Path(__file__).parent
"""The root of the corpus."""

DRAWING: frozenset[str] = frozenset({"plot", "render", "screenshot", "show"})
"""Method names whose call renders, in addition to any ``export_*`` method."""

EXEMPT: dict[str, str] = {}
"""Tests, as ``"<path>::<name>"``, that only appear to draw, with the reason."""


def _draws(name: str) -> bool:
    """Determine whether a call to the method `name` renders."""
    return name in DRAWING or name.startswith("export_")


def _marks(decorators: list[ast.expr]) -> set[str]:
    """Return the names of the ``pytest.mark`` markers among `decorators`."""
    result = set()
    for decorator in decorators:
        node = decorator.func if isinstance(decorator, ast.Call) else decorator
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        parts.reverse()
        if len(parts) == 3 and parts[:2] == ["pytest", "mark"]:
            result.add(parts[2])
    return result


def _module_marks(tree: ast.Module) -> set[str]:
    """Return the markers applied to the whole module by ``pytestmark``."""
    result = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark"
            for target in node.targets
        ):
            value = node.value
            values = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
            result |= _marks(values)
    return result


def _functions(tree: ast.Module) -> dict[str, tuple[ast.FunctionDef, set[str]]]:
    """Map each function of the module to its node and its class's markers."""
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = (node, set())
        elif isinstance(node, ast.ClassDef):
            marks = _marks(node.decorator_list)
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result.setdefault(member.name, (member, marks))
    return result


def _renders(name: str, functions: dict[str, tuple[ast.FunctionDef, set[str]]]) -> bool:
    """Determine whether `name` draws, itself or through the module's functions.

    A function reaches another by calling it by name, or by taking it as a
    fixture through a parameter of the same name.

    """
    seen: set[str] = set()
    pending = [name]
    while pending:
        current = pending.pop()
        if current in seen or current not in functions:
            continue
        seen.add(current)
        node, _ = functions[current]
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute) and _draws(child.func.attr):
                    return True
                if isinstance(child.func, ast.Name):
                    pending.append(child.func.id)
        pending.extend(arg.arg for arg in node.args.args)
    return False


def violations(source: str, path: str) -> list[str]:
    """Return one message for each test of the module that breaks the policy.

    Parameters
    ----------
    source : str
        The source of the test module.
    path : str
        The path of the module, used in the messages and to look up exemptions.

    Returns
    -------
    list of str
        The messages, empty when the module keeps to the policy.

    """
    tree = ast.parse(source)
    module = _module_marks(tree)
    functions = _functions(tree)
    result = []

    for name, (node, inherited) in functions.items():
        if not name.startswith("test"):
            continue
        marks = module | inherited | _marks(node.decorator_list)
        key = f"{path}::{name}"
        if "example" in marks and "image" not in marks:
            result.append(f"{key} is marked example but not image")
        elif "image" not in marks and key not in EXEMPT and _renders(name, functions):
            result.append(f"{key} renders but is not marked image")

    return result


UNMARKED = "x.py::test_a renders but is not marked image"
"""The violation reported for the fixtures' unmarked test that draws."""

EXAMPLE_ONLY = "x.py::test_a is marked example but not image"
"""The violation reported for the fixtures' gallery test without the marker."""


def test_unmarked_renders():
    """Test a test that draws without the marker is caught."""
    source = "def test_a(plotter):\n    plotter.show()\n"
    assert violations(source, "x.py") == [UNMARKED]


def test_marked_renders():
    """Test a test that draws and carries the marker passes."""
    source = (
        "import pytest\n\n"
        "@pytest.mark.image\n"
        "def test_a(plotter):\n    plotter.screenshot()\n"
    )
    assert violations(source, "x.py") == []


def test_export():
    """Test any ``export_*`` method counts as drawing."""
    source = "def test_a(plotter):\n    plotter.export_vtksz()\n"
    assert violations(source, "x.py") == [UNMARKED]


def test_through_helper():
    """Test drawing through a function of the module is caught."""
    source = (
        "def draw(plotter):\n    plotter.render()\n\n"
        "def test_a(plotter):\n    draw(plotter)\n"
    )
    assert violations(source, "x.py") == [UNMARKED]


def test_through_fixture():
    """Test drawing through a fixture of the module is caught."""
    source = (
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def shown():\n    plotter.show()\n\n"
        "def test_a(shown):\n    pass\n"
    )
    assert violations(source, "x.py") == [UNMARKED]


def test_class_mark():
    """Test the marker on the class of a test counts."""
    source = (
        "import pytest\n\n"
        "@pytest.mark.image\n"
        "class TestA:\n    def test_a(self, plotter):\n        plotter.show()\n"
    )
    assert violations(source, "x.py") == []


def test_module_mark():
    """Test the marker in the module's ``pytestmark`` counts."""
    source = (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.slow, pytest.mark.image]\n\n"
        "def test_a(plotter):\n    plotter.show()\n"
    )
    assert violations(source, "x.py") == []


def test_example_without_image():
    """Test the gallery marker is never used without the image marker."""
    source = (
        "import pytest\n\n"
        "@pytest.mark.example\n"
        "def test_a(module):\n    module.main()\n"
    )
    assert violations(source, "x.py") == [EXAMPLE_ONLY]


def test_not_drawing():
    """Test a test that draws nothing needs no marker."""
    source = "def test_a(mesh):\n    assert mesh.n_points\n"
    assert violations(source, "x.py") == []


def test_corpus():
    """Test the corpus holds image tests that draw, so the gate is not vacuous."""
    drawing = 0
    for path in TESTS.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module = _module_marks(tree)
        functions = _functions(tree)
        for name, (node, inherited) in functions.items():
            marks = module | inherited | _marks(node.decorator_list)
            if name.startswith("test") and "image" in marks:
                drawing += _renders(name, functions)
    assert drawing >= 20


def test_exemptions_exist():
    """Test each exemption names a test that exists, so none goes stale."""
    for key in EXEMPT:
        path, name = key.split("::")
        functions = _functions(ast.parse((TESTS.parent / path).read_text()))
        assert name in functions, key


def test_policy():
    """Test every test in the repository keeps to the policy."""
    result = []
    for path in sorted(TESTS.rglob("*.py")):
        relative = path.relative_to(TESTS.parent).as_posix()
        result += violations(path.read_text(encoding="utf-8"), relative)
    assert result == []

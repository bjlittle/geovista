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

A test draws when it calls one of :data:`DRAWING` or an ``export_*`` method, or
a drawing function imported by name, such as ``from pyvista import plot``. It
may do so directly, through a method of its own class, through a function of
the module, or through a fixture of its class, an enclosing class or the
module. It is marked when ``image`` decorates the test or an enclosing class,
or the ``pytestmark`` of the module or an enclosing class holds it. As pytest
does, only a ``test*`` function within ``Test*`` classes, if any, is a test,
and each is named by its classes, so tests of the same name in different
classes stay apart. The ``example`` marker selects the gallery image tests, a
subset of the ``image`` tests, so it must never appear without ``image``.

The corpus is every module beneath ``tests``, read as source and never
imported, so this module needs no display and never skips. A test that only
appears to draw is exempt in :data:`EXEMPT`, with the reason beside it.

"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

TESTS = Path(__file__).parent
"""The root of the corpus."""

DRAWING: frozenset[str] = frozenset({"plot", "render", "screenshot", "show"})
"""Method names whose call renders, in addition to any ``export_*`` method."""

EXEMPT: dict[str, str] = {}
"""Tests, as pytest names them (``"<path>::<class>::<name>"``), that only appear
to draw, each with the reason."""


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


def _scope_marks(body: list[ast.stmt]) -> set[str]:
    """Return the markers a module or class body applies through ``pytestmark``."""
    result = set()
    for node in body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark"
            for target in node.targets
        ):
            value = node.value
            values = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
            result |= _marks(values)
    return result


@dataclass(frozen=True)
class _Function:
    """A function of a test module, within its enclosing classes."""

    node: ast.FunctionDef | ast.AsyncFunctionDef
    scope: tuple[str, ...]
    marks: frozenset[str]

    @property
    def name(self) -> str:
        """The name of the function qualified by its classes, as pytest gives it."""
        return "::".join((*self.scope, self.node.name))

    @property
    def collected(self) -> bool:
        """Whether pytest collects the function as a test."""
        return self.node.name.startswith("test") and all(
            name.startswith("Test") for name in self.scope
        )


def _functions(tree: ast.Module) -> dict[tuple[tuple[str, ...], str], _Function]:
    """Map each function of the module, keyed by its scope and name.

    Each carries the markers of the module and of its enclosing classes, through
    their decorators or ``pytestmark``.

    """
    result = {}

    def visit(body: list[ast.stmt], scope: tuple[str, ...], marks: set[str]) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result[(scope, node.name)] = _Function(node, scope, frozenset(marks))
            elif isinstance(node, ast.ClassDef):
                inner = marks | _marks(node.decorator_list) | _scope_marks(node.body)
                visit(node.body, (*scope, node.name), inner)

    visit(tree.body, (), _scope_marks(tree.body))
    return result


def _drawing_imports(tree: ast.Module) -> set[str]:
    """Return the names bound to a drawing function imported by name."""
    return {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if _draws(alias.name)
    }


def _renders(
    function: _Function,
    functions: dict[tuple[tuple[str, ...], str], _Function],
    imported: set[str],
) -> bool:
    """Determine whether `function` draws, itself or through the module.

    A function reaches a method of its own class through ``self`` or ``cls``, a
    function of the module by calling it by name, and a fixture of its class,
    an enclosing class or the module through a parameter of the same name.

    """
    seen: set[tuple[tuple[str, ...], str]] = set()
    pending = [function]

    def fixture(scope: tuple[str, ...], name: str) -> _Function | None:
        for depth in range(len(scope), -1, -1):
            if (found := functions.get((scope[:depth], name))) is not None:
                return found
        return None

    while pending:
        current = pending.pop()
        key = (current.scope, current.node.name)
        if key in seen:
            continue
        seen.add(key)
        for child in ast.walk(current.node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            if isinstance(func, ast.Attribute):
                owner = func.value
                if isinstance(owner, ast.Name) and owner.id in ("self", "cls"):
                    method = functions.get((current.scope, func.attr))
                    if method is not None:
                        pending.append(method)
                        continue
                if _draws(func.attr):
                    return True
            elif isinstance(func, ast.Name):
                if func.id in imported:
                    return True
                if (helper := functions.get(((), func.id))) is not None:
                    pending.append(helper)
        found = (fixture(current.scope, arg.arg) for arg in current.node.args.args)
        pending.extend(item for item in found if item is not None)
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
    functions = _functions(tree)
    imported = _drawing_imports(tree)
    result = []

    for function in functions.values():
        if not function.collected:
            continue
        marks = function.marks | _marks(function.node.decorator_list)
        key = f"{path}::{function.name}"
        if "example" in marks and "image" not in marks:
            result.append(f"{key} is marked example but not image")
        elif (
            "image" not in marks
            and key not in EXEMPT
            and _renders(function, functions, imported)
        ):
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


def test_same_name_in_classes():
    """Test a test is told apart from one of the same name in another class."""
    source = (
        "import pytest\n\n"
        "@pytest.mark.image\n"
        "class TestMarked:\n"
        "    def test_show(self, plotter):\n        plotter.show()\n\n"
        "class TestUnmarked:\n"
        "    def test_show(self, plotter):\n        plotter.show()\n"
    )
    assert violations(source, "x.py") == [
        "x.py::TestUnmarked::test_show renders but is not marked image"
    ]


def test_through_method():
    """Test drawing through a method of the test's own class is caught."""
    source = (
        "class TestA:\n"
        "    def draw(self, plotter):\n        plotter.show()\n\n"
        "    def test_a(self, plotter):\n        self.draw(plotter)\n"
    )
    assert violations(source, "x.py") == [
        "x.py::TestA::test_a renders but is not marked image"
    ]


def test_through_class_fixture():
    """Test drawing through a fixture of the test's own class is caught."""
    source = (
        "import pytest\n\n"
        "class TestA:\n"
        "    @pytest.fixture\n"
        "    def shown(self, plotter):\n        plotter.show()\n\n"
        "    def test_a(self, shown):\n        pass\n"
    )
    assert violations(source, "x.py") == [
        "x.py::TestA::test_a renders but is not marked image"
    ]


@pytest.mark.parametrize(
    "imports",
    ["from pyvista import plot as draw", "from pyvista.plotting import plot as draw"],
)
def test_imported_drawing(imports):
    """Test calling a drawing function imported by name is caught."""
    source = f"{imports}\n\ndef test_a(mesh):\n    draw(mesh)\n"
    assert violations(source, "x.py") == [UNMARKED]


@pytest.mark.parametrize(
    "assignment",
    ["pytest.mark.image", "[pytest.mark.slow, pytest.mark.image]"],
)
def test_class_pytestmark(assignment):
    """Test the marker in the class's ``pytestmark`` counts."""
    source = (
        "import pytest\n\n"
        f"class TestA:\n    pytestmark = {assignment}\n\n"
        "    def test_a(self, plotter):\n        plotter.show()\n"
    )
    assert violations(source, "x.py") == []


def test_enclosing_class_mark():
    """Test the marker on an enclosing class counts for a nested class."""
    source = (
        "import pytest\n\n"
        "@pytest.mark.image\n"
        "class TestOuter:\n"
        "    class TestInner:\n"
        "        def test_a(self, plotter):\n            plotter.show()\n"
    )
    assert violations(source, "x.py") == []


def test_not_drawing():
    """Test a test that draws nothing needs no marker."""
    source = "def test_a(mesh):\n    assert mesh.n_points\n"
    assert violations(source, "x.py") == []


def test_corpus():
    """Test the corpus holds image tests that draw, so the gate is not vacuous."""
    drawing = 0
    for path in TESTS.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions = _functions(tree)
        imported = _drawing_imports(tree)
        for function in functions.values():
            marks = function.marks | _marks(function.node.decorator_list)
            if function.collected and "image" in marks:
                drawing += _renders(function, functions, imported)
    assert drawing >= 20


def test_exemptions_exist():
    """Test each exemption names a test that exists, so none goes stale."""
    for key in EXEMPT:
        path, name = key.split("::", maxsplit=1)
        tree = ast.parse((TESTS.parent / path).read_text(encoding="utf-8"))
        assert name in {function.name for function in _functions(tree).values()}, key


def test_policy():
    """Test every test in the repository keeps to the policy."""
    result = []
    for path in sorted(TESTS.rglob("*.py")):
        relative = path.relative_to(TESTS.parent).as_posix()
        result += violations(path.read_text(encoding="utf-8"), relative)
    assert result == []

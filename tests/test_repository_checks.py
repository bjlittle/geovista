# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that every repository check is documented, and that its failures say where.

Each module that holds the repository to a rule of ``geovista``'s own declares the
name of its section on the repository checks page, as ``CHECK``. A failure of such
a check ends with a link to that section, which says why the rule exists and how
to declare an exception to it.

See "docs/src/developer/specs/2026-10-23-repository-checks-design.md".

"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

#: The section of the repository checks page that documents this check.
CHECK = "repository-checks"

#: The repository root.
REPO = Path(__file__).parents[1]

#: The module holding the text of the breadcrumb.
BREADCRUMB = REPO / ".github" / "scripts" / "breadcrumb.py"

#: A check module for "pytester" to run: one failure, one setup error, one skip
#: and one pass, so that each kind of report is seen.
DEMO = """
import pytest

CHECK = "demo"


@pytest.fixture
def broken():
    raise RuntimeError("setup fails")


def test_fails():
    assert 1 == 2


def test_errors(broken):
    pass


def test_skips():
    pytest.skip("skipped")


def test_passes():
    pass
"""


@pytest.fixture(scope="module")
def breadcrumb() -> ModuleType:
    """Load the breadcrumb module, which is no importable module."""
    spec = importlib.util.spec_from_file_location("breadcrumb", BREADCRUMB)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_breadcrumb_names_the_section(breadcrumb):
    """The breadcrumb is the text of checks spec §3.3, naming the section."""
    assert breadcrumb.breadcrumb("image-marker") == (
        "Why this check exists, and how to declare an exception:\n"
        "https://geovista.readthedocs.io/en/latest/developer/checks.html"
        "#gv-developer-checks-image-marker"
    )


def test_breadcrumb_needs_no_dependency():
    """The changelog workflow runs its script with "click" and "towncrier" alone."""
    tree = ast.parse(BREADCRUMB.read_text(encoding="utf-8"))
    imported = {
        alias.name.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported <= set(sys.stdlib_module_names) | {"__future__"}


@pytest.mark.parametrize("workers", [[], ["-n", "2"]], ids=["serial", "xdist"])
def test_hook_adds_the_breadcrumb(pytester, monkeypatch, workers):
    """A failure and an error in a check module end with its breadcrumb.

    A skip and a pass do not. Every CI test job runs under "pytest-xdist", so the
    breadcrumb must also survive a report's trip from a worker.

    """
    pytester.makepyfile(test_demo=DEMO)
    monkeypatch.setenv("PYTHONPATH", str(REPO))
    result = pytester.runpytest_subprocess(
        "-p", "tests.conftest", "-p", "no:cacheprovider", *workers
    )
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert result.stdout.str().count("#gv-developer-checks-demo") == 2


def test_hook_ignores_a_module_without_check(pytester, monkeypatch):
    """A failure in a module that declares no check carries no breadcrumb."""
    pytester.makepyfile(test_plain=DEMO.replace('CHECK = "demo"', ""))
    monkeypatch.setenv("PYTHONPATH", str(REPO))
    result = pytester.runpytest_subprocess(
        "-p", "tests.conftest", "-p", "no:cacheprovider"
    )
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert "gv-developer-checks-" not in result.stdout.str()

# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Policy gate that every local sphinx extension declares its parallel safety.

An extension that does not is assumed unsafe, so ``sphinx-build --jobs`` warns
and reads serially, which fails the build under ``--fail-on-warning``. The
extensions are discovered from ``docs/src/_ext``, so a new one is governed the
day it lands.

"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import NoReturn

try:
    import sphinx
except ImportError:
    sphinx = None

EXT = Path(__file__).parents[2] / "docs" / "src" / "_ext"


def _extensions() -> list[Path]:
    """Find each module in ``docs/src/_ext`` that defines a sphinx ``setup``."""
    return sorted(
        path
        for path in EXT.glob("*.py")
        if any(
            isinstance(node, ast.FunctionDef) and node.name == "setup"
            for node in ast.parse(path.read_text(encoding="utf-8")).body
        )
    )


def test_discovered():
    """Test the discovery finds the extensions, so the gate is not vacuous."""
    assert {path.stem for path in _extensions()} >= {
        "intersphinx_resilience",
        "readingtime",
    }


@pytest.mark.parametrize("path", _extensions(), ids=lambda path: path.stem)
def test_parallel_safe(
    path: Path,
    mocker,
    monkeypatch,
    require: Callable[[str], NoReturn],
):
    """Test the extension declares it is safe for parallel reading and writing."""
    if sphinx is None:
        require("sphinx is not installed")

    # an extension may import a sibling by bare name, as a build does
    monkeypatch.syspath_prepend(str(EXT))
    name = f"{path.stem}_parallel_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)

    metadata = module.setup(mocker.Mock())

    assert isinstance(metadata, dict)
    assert metadata.get("parallel_read_safe") is True
    assert metadata.get("parallel_write_safe") is True

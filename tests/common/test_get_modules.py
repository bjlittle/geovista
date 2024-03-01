# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.get_modules`."""

from __future__ import annotations

import importlib
from os import sep
from pathlib import Path

from geovista.common import get_modules


def test_package_walk():
    """Test walk of examples package for all underlying example modules."""
    package = "geovista.examples"
    result = get_modules(package)

    module = importlib.import_module(package)
    path = Path(module.__path__[0])
    fnames = path.rglob("*.py")
    expected = [
        str(fname.relative_to(path)).replace(".py", "").replace(sep, ".")
        for fname in fnames
        if fname.name != "__init__.py"
    ]

    assert result == sorted(expected)

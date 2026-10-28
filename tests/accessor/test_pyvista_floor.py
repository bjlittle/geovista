# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests that every ``pyvista`` geovista admits keys ``mesh.gv`` to its mesh.

``pyvista`` 0.48 cached an accessor in the mesh's instance dict, which
``copy.copy`` shares, so a copy read the original's globe and CRS: measured on
``pyvista`` 0.48.4 with VTK 9.7.1 on 2026-10-28. 0.49.0 keys the cache to the
mesh, so the floor is 0.49.0 wherever ``pyvista`` is pinned.
"""

from __future__ import annotations

from pathlib import Path
import tomllib

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
import pytest
import yaml

ROOT = Path(__file__).parents[2]

#: The first ``pyvista`` that keys a cached accessor to its mesh.
SAFE = Version("0.49.0")

#: The first and last ``pyvista`` 0.48 releases, which share it with a copy.
UNSAFE = [Version("0.48.0"), Version("0.48.4")]


def _pip() -> SpecifierSet:
    """Return the pip requirement on pyvista."""
    path = ROOT / "requirements" / "pypi-core.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.split("#")[0].strip()
        if text and (requirement := Requirement(text)).name == "pyvista":
            return requirement.specifier
    pytest.fail(f"no pyvista in {path.name}")


def _pixi() -> SpecifierSet:
    """Return the pixi dependency on pyvista."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return SpecifierSet(tomllib.loads(text)["tool"]["pixi"]["dependencies"]["pyvista"])


def _conda() -> SpecifierSet:
    """Return the conda environment export's dependency on pyvista."""
    path = ROOT / "requirements" / "geovista.yml"
    for entry in yaml.safe_load(path.read_text(encoding="utf-8"))["dependencies"]:
        name, _, spec = str(entry).partition(" ")
        if name == "pyvista":
            return SpecifierSet(spec.replace(" ", ""))
    pytest.fail(f"no pyvista in {path.name}")


@pytest.mark.parametrize("read", [_pip, _pixi, _conda], ids=["pip", "pixi", "conda"])
def test_every_pyvista_admitted_keys_the_cache_to_its_mesh(read):
    """Test that no pyvista 0.48 is admitted, and 0.49.0 is."""
    spec = read()
    assert SAFE in spec
    assert not [version for version in UNSAFE if version in spec]

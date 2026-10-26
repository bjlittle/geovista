# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that the pixi manifest admits every version the pip requirements admit.

GeoVista declares its dependencies twice: once for ``pip``, in the
"requirements/pypi-*.txt" files that "pyproject.toml" reads dynamically, and
once for ``pixi``, in the dependency tables of its manifest. ``dependabot``
watches only the former, so when it raises a ceiling there the pixi one has to
follow by hand. A pixi ceiling left behind is silent: the lock never reaches the
new release, so the environments that CI tests in never meet the version a
``pip`` user may install.

The pixi ceilings are often looser than the pip ones, as ``semver`` pins them
on the major version rather than the minor, so the rule is that each pixi
ceiling admits at least what its pip counterpart admits, not that the two are
equal. These tests read the source tree as text, and so never skip.

"""

from __future__ import annotations

from functools import cache
from pathlib import Path
import tomllib
from typing import Any

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

#: The section of the repository checks page that documents this check.
CHECK = "dependency-ceilings"

#: The repository root, holding the manifest and the requirements.
ROOT = Path(__file__).parents[1]
#: The manifest declaring the pixi dependency tables.
PYPROJECT = ROOT / "pyproject.toml"
#: The pip requirements, which "dependabot" keeps current.
REQUIREMENTS = sorted((ROOT / "requirements").glob("pypi-*.txt"))

#: The pixi tables of a feature, or of the workspace, that declare dependencies.
TABLES = ("dependencies", "pypi-dependencies")

#: The pip name of a package that conda-forge distributes under another name.
RENAMED = {"h3": "h3-py"}

#: How to bring a pixi ceiling into line, ending each failure.
REMEDY = (
    "Raise the pixi ceiling in pyproject.toml to match, then run "
    '"pixi update <package>", since "pixi lock" alone keeps the locked version.'
)


@cache
def _pixi() -> dict[str, dict[str, str]]:
    """Map each pixi dependency to its version spec, keyed by the declaring table.

    A dependency declared as a table, such as one with an ``extras`` key, keeps
    its version under ``version``. One with none at all is given an empty spec.

    """
    pixi = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["pixi"]
    tables: dict[str, dict[str, Any]] = {
        name: pixi[name] for name in TABLES if name in pixi
    }
    for feature, body in pixi.get("feature", {}).items():
        for name in TABLES:
            if name in body:
                tables[f"feature.{feature}.{name}"] = body[name]

    declared: dict[str, dict[str, str]] = {}
    for table, dependencies in tables.items():
        for package, spec in dependencies.items():
            version = spec.get("version", "") if isinstance(spec, dict) else spec
            declared.setdefault(canonicalize_name(package), {})[table] = version
    return declared


@cache
def _pip() -> dict[str, dict[str, str]]:
    """Map each pip requirement to its version spec, keyed by the declaring file.

    A line naming another file, or the package itself with extras, as
    "pypi-optional-all.txt" does, declares no dependency of its own.

    """
    declared: dict[str, dict[str, str]] = {}
    for path in REQUIREMENTS:
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.partition("#")[0].strip()
            if not text or text.startswith("-"):
                continue
            requirement = Requirement(text)
            package = canonicalize_name(requirement.name)
            if package == "geovista":
                continue
            package = RENAMED.get(package, package)
            declared.setdefault(package, {})[path.name] = str(requirement.specifier)
    return declared


def _ceiling(spec: str) -> Version | None:
    """Return the exclusive upper bound of the spec, or ``None`` for no bound.

    Raises
    ------
    ValueError
        If the spec bounds the version some other way, such as ``<=`` or
        ``==``, whose ceiling this comparison would have to guess at.

    """
    bounds = []
    for specifier in SpecifierSet(spec):
        if specifier.operator in ("<=", "==", "===", "~=") or (
            specifier.operator == "<" and "*" in specifier.version
        ):
            emsg = f"cannot read a ceiling from {specifier}"
            raise ValueError(emsg)
        if specifier.operator == "<":
            bounds.append(Version(specifier.version))
    return min(bounds) if bounds else None


def _unreadable() -> dict[str, str]:
    """Return each compared spec whose ceiling cannot be read.

    Only a package declared on both sides is compared, so the conda syntax of a
    pixi-only one, such as the ``3.13.*`` pin of ``python``, is never read.

    """
    unreadable: dict[str, str] = {}
    for side in (_pip(), _pixi()):
        for package, specs in side.items():
            if package not in _pip() or package not in _pixi():
                continue
            for where, spec in specs.items():
                try:
                    _ceiling(spec)
                except ValueError as error:
                    unreadable[f"{package} ({where})"] = str(error)
    return unreadable


def test_the_requirements_declare_dependencies():
    """Every comparison below derives from them, so none survives an empty set."""
    assert _pip(), f"no dependencies read from {[path.name for path in REQUIREMENTS]}"


def test_every_ceiling_is_one_the_gate_can_read():
    """A ceiling the gate cannot read is one it would wave through unchecked."""
    unreadable = _unreadable()

    assert not unreadable, f"ceilings this check cannot compare: {unreadable}"


def test_every_pip_requirement_is_a_pixi_dependency():
    """Without one, no environment that CI tests in installs the package at all."""
    missing = {
        package: sorted(files)
        for package, files in _pip().items()
        if package not in _pixi()
    }

    assert not missing, (
        f"pip requirements with no pixi dependency: {missing}. Add each to the "
        "pixi table of its feature, or to RENAMED if conda-forge names it otherwise."
    )


def test_every_pixi_ceiling_admits_the_pip_ceiling():
    """Otherwise the lock never reaches a release a ``pip`` user may install."""
    behind: dict[str, dict[str, str]] = {}
    for package, files in _pip().items():
        for file, spec in files.items():
            ceiling = _ceiling(spec)
            for table, pinned in _pixi().get(package, {}).items():
                bound = _ceiling(pinned)
                if bound is not None and (ceiling is None or bound < ceiling):
                    behind[package] = {file: spec, table: pinned}

    assert not behind, f"pixi ceilings behind the pip ones: {behind}. {REMEDY}"

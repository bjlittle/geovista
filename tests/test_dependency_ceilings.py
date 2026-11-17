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

from packaging.specifiers import SpecifierSet
from packaging.version import Version

#: The section of the repository checks page that documents this check.
CHECK = "dependency-ceilings"

#: The declarations of each side, as the fixtures "pip_specs" and "pixi_specs"
#: of "tests/conftest.py" read them: each package to its spec in each place.
Specs = dict[str, dict[str, str]]

#: How to bring a pixi ceiling into line, ending each failure.
REMEDY = (
    "Raise the pixi ceiling in pyproject.toml to match, then run "
    '"pixi update <package>", since "pixi lock" alone keeps the locked version.'
)


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


def _unreadable(pip: Specs, pixi: Specs) -> dict[str, str]:
    """Return each compared spec whose ceiling cannot be read.

    Only a package declared on both sides is compared, so the conda syntax of a
    pixi-only one, such as the ``3.13.*`` pin of ``python``, is never read.

    """
    unreadable: dict[str, str] = {}
    for side in (pip, pixi):
        for package, specs in side.items():
            if package not in pip or package not in pixi:
                continue
            for where, spec in specs.items():
                try:
                    _ceiling(spec)
                except ValueError as error:
                    unreadable[f"{package} ({where})"] = str(error)
    return unreadable


def test_the_requirements_declare_dependencies(pip_specs):
    """Every comparison below derives from them, so none survives an empty set."""
    assert pip_specs, "no dependencies read from requirements/pypi-*.txt"


def test_every_ceiling_is_one_the_gate_can_read(pip_specs, pixi_specs):
    """A ceiling the gate cannot read is one it would wave through unchecked."""
    unreadable = _unreadable(pip_specs, pixi_specs)

    assert not unreadable, f"ceilings this check cannot compare: {unreadable}"


def test_every_pip_requirement_is_a_pixi_dependency(pip_specs, pixi_specs):
    """Without one, no environment that CI tests in installs the package at all."""
    missing = {
        package: sorted(files)
        for package, files in pip_specs.items()
        if package not in pixi_specs
    }

    assert not missing, (
        f"pip requirements with no pixi dependency: {missing}. Add each to the "
        "pixi table of its feature, or to RENAMED in tests/conftest.py if "
        "conda-forge names it otherwise."
    )


def test_every_pixi_ceiling_admits_the_pip_ceiling(pip_specs, pixi_specs):
    """Otherwise the lock never reaches a release a ``pip`` user may install."""
    behind: dict[str, dict[str, str]] = {}
    for package, files in pip_specs.items():
        for file, spec in files.items():
            ceiling = _ceiling(spec)
            for table, pinned in pixi_specs.get(package, {}).items():
                bound = _ceiling(pinned)
                if bound is not None and (ceiling is None or bound < ceiling):
                    behind[package] = {file: spec, table: pinned}

    assert not behind, f"pixi ceilings behind the pip ones: {behind}. {REMEDY}"

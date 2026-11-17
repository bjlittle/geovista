# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that every pip requirement declares the floor its pixi declaration does.

GeoVista declares each dependency twice, for ``pip`` in "requirements/pypi-*.txt"
and for ``pixi`` in the dependency tables of "pyproject.toml". CI resolves the
``pixi`` floors in the ``floors`` environment, so a ``pip`` floor that differs
from its ``pixi`` one promises users releases that no job installs
(floors spec §4.4). ``dependabot`` moves the ``pip`` side alone: its grouped bump
in #2219 raised floors to the newest release, and #2226 then dropped most of them.

A floor is compared as a version, so ``0.4`` and ``0.4.0`` agree. Only a package
declared on both sides is compared, as a ``pixi`` declaration with no ``pip``
counterpart, such as ``python``, has no ``pip`` floor to hold. These tests read
the source tree as text, and so never skip.

"""

from __future__ import annotations

from contextlib import suppress

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version
import pytest

#: The section of the repository checks page that documents this check.
CHECK = "dependency-floors"

#: The declarations of each side, as the fixtures "pip_specs" and "pixi_specs"
#: of "tests/conftest.py" read them: each package to its spec in each place.
Specs = dict[str, dict[str, str]]

#: How to bring a floor into line, ending each failure.
REMEDY = (
    "Put the floor back where a dependabot pull request moved it, or raise it on "
    'both sides in one commit and run "pixi lock". A floor lowered also needs '
    '"pixi update --environment floors <package>".'
)

#: The operators bounding a version from below other than by ">=", whose floor
#: this comparison would have to guess at.
UNREADABLE = frozenset({">", "==", "===", "~="})


def _floor(spec: str) -> Version | None:
    """Return the floor of the spec, its one ``>=``, or ``None`` for no floor.

    A ceiling or an excluded release, as ``<``, ``<=`` or ``!=``, does not bear
    on the floor.

    Raises
    ------
    ValueError
        If the spec cannot be parsed, as the conda syntax ``1.7.*``, or bounds
        the version from below some other way, as ``>``, ``==`` or ``~=``, or
        more than once.

    """
    try:
        specifiers = SpecifierSet(spec)
    except InvalidSpecifier as error:
        emsg = f"cannot read a floor from {spec!r}"
        raise ValueError(emsg) from error

    floors = []
    for specifier in specifiers:
        if specifier.operator in UNREADABLE:
            emsg = f"cannot read a floor from {specifier}"
            raise ValueError(emsg)
        if specifier.operator == ">=":
            floors.append(Version(specifier.version))

    if len(floors) > 1:
        emsg = f"cannot read one floor from {spec!r}"
        raise ValueError(emsg)
    return floors[0] if floors else None


def _readable(places: dict[str, str]) -> dict[str, Version | None]:
    """Return the floor at each place, leaving out a spec ``_unreadable`` reports."""
    floors: dict[str, Version | None] = {}
    for where, spec in places.items():
        with suppress(ValueError):
            floors[where] = _floor(spec)
    return floors


def _floorless(pip: Specs) -> dict[str, list[str]]:
    """Return each package with the files that declare it without a floor."""
    floorless: dict[str, list[str]] = {}
    for package, files in pip.items():
        missing = sorted(
            file for file, floor in _readable(files).items() if floor is None
        )
        if missing:
            floorless[package] = missing
    return floorless


def _unreadable(pip: Specs, pixi: Specs) -> dict[str, str]:
    """Return each spec whose floor cannot be read, keyed by package and place.

    Every ``pip`` requirement is read, and the ``pixi`` declarations of each
    package it names, so the conda syntax of a pixi-only one, such as the
    ``3.13.*`` pin of ``python``, is never read.

    """
    unreadable: dict[str, str] = {}
    for package, files in pip.items():
        for where, spec in {**files, **pixi.get(package, {})}.items():
            try:
                _floor(spec)
            except ValueError as error:
                unreadable[f"{package} ({where})"] = str(error)
    return unreadable


def _disagreements(pip: Specs, pixi: Specs) -> dict[str, dict[str, str]]:
    """Return each package declared on both sides whose floors differ.

    Each maps to its floor at every place, ``"none"`` where it has none.

    """
    disagreements: dict[str, dict[str, str]] = {}
    for package, files in pip.items():
        if package not in pixi:
            continue
        floors = _readable({**files, **pixi[package]})
        if len(set(floors.values())) > 1:
            disagreements[package] = {
                where: "none" if floor is None else str(floor)
                for where, floor in floors.items()
            }
    return disagreements


def test_every_pip_requirement_declares_a_floor(pip_specs):
    """A line without one admits every release on PyPI (floors spec §2 decision 5)."""
    floorless = _floorless(pip_specs)

    assert not floorless, f"pip requirements without a floor: {floorless}. {REMEDY}"


def test_every_floor_is_one_the_check_can_read(pip_specs, pixi_specs):
    """A floor the check cannot read is one it would wave through (floors spec §4.4)."""
    unreadable = _unreadable(pip_specs, pixi_specs)

    assert not unreadable, f"floors this check cannot compare: {unreadable}. {REMEDY}"


def test_every_floor_is_the_same_on_both_sides(pip_specs, pixi_specs):
    """CI resolves the floor a user is promised (floors spec §2 decision 5)."""
    disagreements = _disagreements(pip_specs, pixi_specs)

    assert not disagreements, f"floors that differ: {disagreements}. {REMEDY}"


def test_a_requirement_without_a_floor_is_reported():
    """Demonstrates the first clause of floors spec §4.4."""
    pip = {"pooch": {"pypi-core.txt": "<1.10"}}

    assert _floorless(pip) == {"pooch": ["pypi-core.txt"]}


def test_a_floor_unlike_the_pixi_one_is_reported():
    """Demonstrates the second clause of floors spec §4.4, across the two sides."""
    pip = {"numpy": {"pypi-core.txt": ">=2.2.6,<2.6"}}
    pixi = {"numpy": {"dependencies": ">=2.2.5,<3"}}

    assert _disagreements(pip, pixi) == {
        "numpy": {"pypi-core.txt": "2.2.6", "dependencies": "2.2.5"}
    }


def test_pip_files_that_disagree_are_reported():
    """Demonstrates the second clause of floors spec §4.4, across two pip files."""
    pip = {
        "towncrier": {
            "pypi-optional-docs.txt": ">=24.8.0,<26.10",
            "pypi-optional-test.txt": ">=24.7.0,<26.10",
        }
    }
    pixi = {"towncrier": {"feature.docs.dependencies": ">=24.8.0,<27"}}

    assert _disagreements(pip, pixi) == {
        "towncrier": {
            "pypi-optional-docs.txt": "24.8.0",
            "pypi-optional-test.txt": "24.7.0",
            "feature.docs.dependencies": "24.8.0",
        }
    }


@pytest.mark.parametrize(
    ("pip", "pixi", "where"),
    [
        pytest.param(">2.2,<2.6", ">=2.2.6,<3", "numpy (pypi-core.txt)", id="greater"),
        pytest.param("==2.2.6", ">=2.2.6,<3", "numpy (pypi-core.txt)", id="equal"),
        pytest.param("~=2.2", ">=2.2.6,<3", "numpy (pypi-core.txt)", id="compatible"),
        pytest.param("==2.*", ">=2.2.6,<3", "numpy (pypi-core.txt)", id="wildcard"),
        pytest.param("===2.2.6", ">=2.2.6,<3", "numpy (pypi-core.txt)", id="arbitrary"),
        pytest.param(">=2.2,>=2.3", ">=2.2.6,<3", "numpy (pypi-core.txt)", id="two"),
        pytest.param(">=2.2.6,<2.6", "2.2.*", "numpy (dependencies)", id="conda"),
    ],
)
def test_a_floor_the_check_cannot_read_is_reported(pip, pixi, where):
    """Demonstrates the third clause of floors spec §4.4, on either side."""
    unreadable = _unreadable(
        {"numpy": {"pypi-core.txt": pip}}, {"numpy": {"dependencies": pixi}}
    )

    assert list(unreadable) == [where]


def test_a_pixi_only_dependency_is_not_compared():
    """Demonstrates the fourth clause of floors spec §4.4, beside a compared package.

    ``python`` has a floor this check cannot read, and ``setuptools`` one with no
    ``pip`` counterpart to equal, so reading either would report it.
    """
    pip = {"numpy": {"pypi-core.txt": ">=2.2.6,<2.6"}}
    pixi = {
        "numpy": {"dependencies": ">=2.2.6,<3"},
        "python": {"feature.py313.dependencies": "3.13.*"},
        "setuptools": {"dependencies": ">=80.9.0,<81"},
    }

    assert _unreadable(pip, pixi) == {}
    assert _disagreements(pip, pixi) == {}


def test_a_pixi_declaration_without_a_floor_is_reported():
    """A pixi table that drops its floor is not passed over."""
    pip = {"numpy": {"pypi-core.txt": ">=2.2.6,<2.6"}}
    pixi = {"numpy": {"dependencies": "<3"}}

    assert _disagreements(pip, pixi) == {
        "numpy": {"pypi-core.txt": "2.2.6", "dependencies": "none"}
    }


def test_floors_written_differently_agree():
    """The same version written to a different precision is the same floor."""
    pip = {"lazy-loader": {"pypi-core.txt": ">=0.4,<0.7"}}
    pixi = {"lazy-loader": {"dependencies": ">=0.4.0,<0.7"}}

    assert _disagreements(pip, pixi) == {}


def test_an_exclusion_leaves_the_floor_readable():
    """An excluded release beside a floor neither moves nor hides it."""
    assert _floor(">=1.0,!=1.2,<2") == Version("1.0")


def test_a_second_file_without_a_floor_is_named():
    """A package declared in two files is reported in the one missing its floor."""
    pip = {
        "towncrier": {
            "pypi-optional-docs.txt": ">=24.8.0,<26.10",
            "pypi-optional-test.txt": "<26.10",
        }
    }

    assert _floorless(pip) == {"towncrier": ["pypi-optional-test.txt"]}

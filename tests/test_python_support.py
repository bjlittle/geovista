# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that every declaration of Python support agrees with the others.

GeoVista states which versions of Python it supports in several places at once:
the trove classifiers and ``requires-python`` in "pyproject.toml", a ``pyXYZ``
pixi feature and a solve-group of environments for each one, the unsuffixed
environments that must always track the newest of them, the conda environment
exported from those, and the matrices of the workflows that build and test
them. Nothing in the tooling ties those together, so a version bump that
reaches six of them and misses the seventh leaves the repository advertising
one thing and testing another, with both halves perfectly valid on their own
terms.

These tests take the classifiers as the statement of intent and hold the rest
to it. They read the source tree as text and need neither a built artefact, a
network nor any particular interpreter, so unlike the matrix they police they
never skip.

"""

from __future__ import annotations

from functools import cache
from pathlib import Path
import re
import tomllib
from typing import Any

import pytest
import yaml

#: The repository root, holding the manifest and the workflows.
ROOT = Path(__file__).parents[1]
#: The manifest declaring the classifiers, the floor and the pixi environments.
PYPROJECT = ROOT / "pyproject.toml"
#: The workflows naming a pixi environment or a bare interpreter version.
WORKFLOWS = ROOT / ".github" / "workflows"
#: The conda environment file "ci-locks.yml" exports from the "geovista"
#: environment, and so the one version a reader installing by hand will get.
EXPORT = ROOT / "requirements" / "geovista.yml"

#: A trove classifier naming a supported minor version.
CLASSIFIER = re.compile(r"^Programming Language :: Python :: (\d+\.\d+)$")
#: A pixi feature, and the environment suffix built from it, e.g. "py313".
FEATURE = re.compile(r"^py(\d{3,})$")
#: The "python" pin of a "pyXYZ" feature, e.g. "3.13.*".
PIN = re.compile(r"^(\d+\.\d+)\.\*$")
#: The same pin as the export carries it, e.g. "python 3.13.*". The export also
#: carries the "requires-python" floor, which is deliberately looser.
EXPORTED = re.compile(r"^python (\d+\.\d+)\.\*$")
#: The matrix value a workflow interpolates into an environment name. Matched
#: rather than compared, since the braces take optional interior whitespace.
PLACEHOLDER = re.compile(r"\$\{\{\s*matrix\.version\s*\}\}")
#: Any remaining expression, which cannot be resolved without a running job.
EXPRESSION = "${{"

#: The solve-group of the unsuffixed environments, which are named for what
#: they hold rather than for a version, and so track the newest supported one.
PRIMARY = "default"

#: The workflows whose matrix must carry every supported version, because they
#: are what makes the support claim true. The rest build on one version
#: deliberately, and are held only to naming an environment that exists.
EXHAUSTIVE = ("ci-tests.yml", "ci-wheels.yml")
#: The workflow installing the published wheel, which selects an interpreter by
#: version rather than a pixi environment by feature.
PYPI = "ci-tests-pypi.yml"


@cache
def _manifest() -> dict[str, Any]:
    """Return the parsed manifest, read once for the whole module."""
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


@cache
def _workflow(name: str) -> dict[str, Any]:
    """Return the parsed workflow, read once per name."""
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _order(version: str) -> tuple[int, ...]:
    """Sort "3.9" below "3.13", which string ordering does not."""
    return tuple(int(part) for part in version.split("."))


def _classifiers() -> set[str]:
    """Return the minor versions the package advertises."""
    return {
        match.group(1)
        for classifier in _manifest()["project"]["classifiers"]
        if (match := CLASSIFIER.match(classifier))
    }


def _features() -> dict[str, str | None]:
    """Map each "pyXYZ" feature to the version it pins, or to ``None``."""
    features = _manifest()["tool"]["pixi"]["feature"]
    pinned: dict[str, str | None] = {}
    for name, table in features.items():
        if not FEATURE.match(name):
            continue
        pin = table.get("dependencies", {}).get("python", "")
        match = PIN.match(pin) if isinstance(pin, str) else None
        pinned[name] = match.group(1) if match else None
    return pinned


@cache
def _environments() -> dict[str, dict[str, Any]]:
    """Return each declared pixi environment as a table, keyed by name.

    Pixi also accepts a bare list of features as shorthand for a table, which
    is normalised here so that the callers below need only the one shape.

    """
    declared = _manifest()["tool"]["pixi"]["environments"]
    return {
        name: body if isinstance(body, dict) else {"features": body}
        for name, body in declared.items()
    }


def _pinned(name: str) -> set[str]:
    """Return the "pyXYZ" features carried by the environment."""
    return {
        feature
        for feature in _environments()[name].get("features", [])
        if FEATURE.match(feature)
    }


def _grouped() -> dict[str, set[str]]:
    """Map each solve-group to the environments belonging to it.

    An environment declaring no solve-group solves alone, in a group of its own
    name, which is how pixi reads the omission.

    """
    groups: dict[str, set[str]] = {}
    for name, body in _environments().items():
        groups.setdefault(body.get("solve-group", name), set()).add(name)
    return groups


def _newest() -> str:
    """Return the "pyXYZ" feature pinning the newest supported version."""
    pinned = {name: version for name, version in _features().items() if version}
    return max(pinned, key=lambda name: _order(pinned[name]))


def _prefixes() -> dict[str, set[str]]:
    """Return the environment prefixes declared for each "pyXYZ" feature.

    A feature with no environments at all keeps an empty entry rather than
    dropping out, which would leave the comparison between features vacuous.

    """
    prefixes: dict[str, set[str]] = {feature: set() for feature in _features()}
    for name in _environments():
        for feature, found in prefixes.items():
            if name == feature:
                found.add("")
            elif name.endswith(f"-{feature}"):
                found.add(name.removesuffix(f"-{feature}"))
    return prefixes


def _matrices(name: str) -> dict[str, list[str]]:
    """Return the "version" matrix of each job in the workflow, keyed by job."""
    return {
        job: versions
        for job, body in _workflow(name).get("jobs", {}).items()
        if (versions := body.get("strategy", {}).get("matrix", {}).get("version"))
    }


def _requests(name: str) -> set[str]:
    """Return every pixi environment the workflow asks ``setup-pixi`` to install.

    An ``environments`` naming the version matrix is expanded over it. One
    carrying any other expression is left out, since resolving it would need a
    running job rather than the file.

    """
    found: set[str] = set()
    for body in _workflow(name).get("jobs", {}).values():
        versions = body.get("strategy", {}).get("matrix", {}).get("version", [])
        for step in body.get("steps", []):
            wanted = (step.get("with") or {}).get("environments")
            if not isinstance(wanted, str):
                continue
            expanded = {PLACEHOLDER.sub(str(version), wanted) for version in versions}
            found |= {env for env in expanded or {wanted} if EXPRESSION not in env}
    return found


def test_the_classifiers_name_a_version():
    """Every comparison below derives from them, so none survives an empty set."""
    assert _classifiers(), f"no python version classifiers in {PYPROJECT.name}"


def test_requires_python_floors_at_the_oldest_classifier():
    """A lower floor advertises a version that nothing here builds or tests."""
    oldest = min(_classifiers(), key=_order)

    assert _manifest()["project"]["requires-python"] == f">={oldest}"


def test_every_pixi_feature_pins_a_minor_version():
    """An unpinned feature would silently drop out of the comparisons below."""
    unpinned = sorted(name for name, version in _features().items() if version is None)

    assert not unpinned, f"pixi features pinning no single minor version: {unpinned}"


def test_each_pixi_feature_is_named_for_the_version_it_pins():
    """A "py313" that resolved to 3.14 would make every workflow name a lie."""
    mismatched = {
        name: version
        for name, version in _features().items()
        if version is not None and name != f"py{version.replace('.', '')}"
    }

    assert not mismatched, f"pixi features named for another version: {mismatched}"


def test_the_pixi_features_match_the_classifiers():
    """Without a feature there is no environment in which to test the claim."""
    assert set(_features().values()) == _classifiers()


def test_every_version_has_the_same_environments():
    """A version with fewer cannot be put through the same jobs as the rest."""
    prefixes = _prefixes()
    distinct = {frozenset(value) for value in prefixes.values()}

    assert len(distinct) == 1, f"environments differ between versions: {prefixes}"


def test_every_environment_carries_one_python_feature():
    """Two features would resolve one away, and none leaves the version to pixi."""
    carried = {name: sorted(_pinned(name)) for name in _environments()}
    wrong = {name: features for name, features in carried.items() if len(features) != 1}

    assert not wrong, f"environments not carrying one pyXYZ feature: {wrong}"


def test_the_primary_solve_group_tracks_the_newest_version():
    """The unsuffixed environments are the ones a bare "pixi run" reaches for."""
    primary = _grouped().get(PRIMARY, set())
    assert primary, f"no environments in the {PRIMARY!r} solve-group"

    newest = _newest()
    stale = {
        name: sorted(_pinned(name)) for name in primary if _pinned(name) != {newest}
    }

    assert not stale, f"environments behind the newest feature {newest!r}: {stale}"


def test_each_secondary_solve_group_carries_the_feature_it_names():
    """A group resolved against another version tests nothing its name claims."""
    secondary = {group: _grouped().get(group, set()) for group in _features()}
    missing = sorted(group for group, names in secondary.items() if not names)
    assert not missing, f"pixi features with no solve-group of their own: {missing}"

    mismatched = {
        name: sorted(_pinned(name))
        for group, names in secondary.items()
        for name in names
        if _pinned(name) != {group}
    }

    assert not mismatched, f"environments carrying another feature: {mismatched}"


def test_the_exported_environment_pins_the_newest_version():
    """Nothing re-exports on a bump, so a stale file outlives what made it."""
    dependencies = yaml.safe_load(EXPORT.read_text(encoding="utf-8"))["dependencies"]
    pinned = {
        match.group(1)
        for entry in dependencies
        if (match := EXPORTED.match(str(entry)))
    }
    assert pinned, f"no pinned python in {EXPORT.name}"

    assert pinned == {_features()[_newest()]}


@pytest.mark.parametrize("workflow", EXHAUSTIVE)
def test_the_matrix_carries_every_supported_version(workflow):
    """These are the jobs that make the support claim true rather than stated."""
    matrices = _matrices(workflow)
    assert matrices, f"no version matrix in {workflow}"

    for job, versions in matrices.items():
        assert set(versions) == set(_features()), f"{workflow}: {job}"


def test_the_pypi_matrix_carries_every_classifier():
    """The published wheel is installed by interpreter version, not by feature."""
    matrices = _matrices(PYPI)
    assert matrices, f"no version matrix in {PYPI}"

    for job, versions in matrices.items():
        assert set(versions) == _classifiers(), f"{PYPI}: {job}"


def test_every_workflow_names_a_declared_environment():
    """What catches a rename in a workflow pinned to one version of the matrix."""
    workflows = sorted(WORKFLOWS.glob("*.yml"))
    assert workflows, f"no workflows under {WORKFLOWS}"

    requested = {path.name: _requests(path.name) for path in workflows}
    assert any(requested.values()), "no workflow names a pixi environment"

    declared = set(_environments())
    unknown = {
        name: sorted(missing)
        for name, wanted in requested.items()
        if (missing := wanted - declared)
    }

    assert not unknown, f"workflows naming an undeclared environment: {unknown}"

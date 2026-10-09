# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that the "mypy" ratchet only ever shrinks.

GeoVista type checks in strict mode against the locked pixi environment, where
the third-party types are real. That check reports errors in 22 of the 25
library modules and in the example gallery, which cannot be corrected in one
reviewable change, so the affected modules are listed once under
``ignore_errors`` and retired one change at a time.

A ratchet with nothing holding it becomes a dumping ground. These tests read
the manifest as text and hold the list to shrinking: an entry may be removed,
and nothing may be added — a module already retired included, which is why the
baseline below is kept level with the manifest rather than left standing as a
high-water mark. They are deleted along with the override block when the last
entry goes.

See "docs/src/developer/specs/2026-10-06-type-coverage-design.md", section 3.2.

"""

from __future__ import annotations

from functools import cache
from pathlib import Path
import tomllib
from typing import TYPE_CHECKING, Any

import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Iterable

#: The repository root, holding the manifest the ratchet lives in.
ROOT = Path(__file__).parents[1]
#: The manifest declaring the "mypy" configuration and its overrides.
PYPROJECT = ROOT / "pyproject.toml"
#: The hook configuration, which must skip "mypy" on "pre-commit.ci".
PRE_COMMIT = ROOT / ".pre-commit-config.yaml"
#: The workflow carrying the coverage "pre-commit.ci" cannot provide.
WORKFLOW = ROOT / ".github" / "workflows" / "ci-typing.yml"
#: The package root, against which each ratchet entry is resolved.
SOURCE = ROOT / "src"

#: Every module "mypy" was told to ignore when the ratchet was banked, on
#: 2026-10-06. Entries come off as each change retires a module; none may be
#: added. "geovista.examples.*" is the one entry that is not a library module,
#: and goes with change 7 of the roadmap.
RATCHET_BASELINE = frozenset(
    {
        "geovista.cache",
        "geovista.cli",
        "geovista.config",
        "geovista.core",
        "geovista.crs",
        "geovista.examples.*",
        "geovista.filters",
        "geovista.geodesic",
        "geovista.geometry",
        "geovista.geoplotter",
        "geovista.gridlines",
        "geovista.pantry",
        "geovista.pantry.data",
        "geovista.pantry.meshes",
        "geovista.pantry.textures",
        "geovista.qt",
        "geovista.raster",
        "geovista.report",
        "geovista.search",
        "geovista.themes",
    }
)


def _modules(override: dict[str, Any]) -> tuple[str, ...]:
    """Return the modules an override applies to.

    Parameters
    ----------
    override : dict
        One ``[[tool.mypy.overrides]]`` block, as parsed.

    Returns
    -------
    tuple of str
        The modules named, however they were written. "mypy" accepts a bare
        string as well as an array, and the "geovista.cli" override uses one,
        so iterating the value directly would yield its characters.

    """
    module = override.get("module", ())
    return (module,) if isinstance(module, str) else tuple(module)


@cache
def _ignored() -> frozenset[str]:
    """Return every module "mypy" is told to ignore errors in.

    Returns
    -------
    frozenset of str
        Collected from *all* override blocks rather than from the ratchet
        alone, so that a second block carrying ``ignore_errors`` cannot route
        around the baseline.

    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    overrides = manifest["tool"]["mypy"].get("overrides", [])
    return frozenset(
        module
        for override in overrides
        if override.get("ignore_errors", False)
        for module in _modules(override)
    )


def _drift(
    ignored: Iterable[str], baseline: Iterable[str]
) -> tuple[frozenset[str], frozenset[str]]:
    """Return what the ratchet has gained and lost against a baseline.

    Parameters
    ----------
    ignored : iterable of str
        The modules currently carrying ``ignore_errors``.
    baseline : iterable of str
        The modules the baseline lists.

    Returns
    -------
    tuple of frozenset of str
        What was added, and what was retired. Both halves are reported: a
        baseline keeping a name the manifest has dropped is a high-water
        mark, and a high-water mark lets a retired module back in silently.

    """
    ignored, baseline = frozenset(ignored), frozenset(baseline)
    return ignored - baseline, baseline - ignored


def _commands(step: dict[str, Any]) -> tuple[str, ...]:
    """Return the commands a step really runs.

    Parameters
    ----------
    step : dict
        One workflow step, as parsed.

    Returns
    -------
    tuple of str
        One entry per line of ``run``, stripped, with blanks and comments
        dropped, so that a command matches as a whole line rather than as a
        substring: ``echo``-ing it, commenting it out or appending
        ``|| true`` then no longer reads as running it. A step carrying
        ``if`` or ``continue-on-error`` may be skipped or may fail
        harmlessly, and yields nothing — the workflow cannot be held to a
        step that need not run. Adding either deliberately means revisiting
        this test.

    """
    if "if" in step or step.get("continue-on-error"):
        return ()
    return tuple(
        line
        for raw in step.get("run", "").splitlines()
        if (line := raw.strip()) and not line.startswith("#")
    )


def _steps() -> tuple[dict[str, Any], ...]:
    """Return every step of every job in the typing workflow.

    Returns
    -------
    tuple of dict
        The steps, flattened. A job that calls a reusable workflow carries
        ``uses`` instead of ``steps``, and contributes nothing.

    """
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return tuple(
        step for job in workflow["jobs"].values() for step in job.get("steps", [])
    )


def _hook() -> dict[str, Any]:
    """Return the "local" "mypy" hook.

    Returns
    -------
    dict
        The hook, as parsed.

    """
    config = yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8"))
    hooks = [
        hook
        for repo in config["repos"]
        if repo["repo"] == "local"
        for hook in repo["hooks"]
        if hook["id"] == "mypy"
    ]
    assert hooks, "no local 'mypy' hook: is the skip still needed?"
    return hooks[0]


def _resolve(module: str) -> Path | None:
    """Return the file a ratchet entry names, if it still exists.

    Parameters
    ----------
    module : str
        A dotted module name, optionally ending in the ``.*`` wildcard.

    Returns
    -------
    Path or None
        The module file, or the package's "__init__.py", or ``None`` when the
        entry names nothing.

    """
    relative = Path(*module.removesuffix(".*").split("."))
    for candidate in (
        SOURCE / relative.with_suffix(".py"),
        SOURCE / relative / "__init__.py",
    ):
        if candidate.is_file():
            return candidate
    return None


def test_ratchet_only_shrinks():
    """An entry may be removed from the ratchet; none may be added.

    The baseline is a running copy of the list rather than a high-water
    mark, so a retirement edits both in the same change. A high-water mark
    would keep the name a retirement took out, and putting that module back
    under ``ignore_errors`` later would pass this test untouched — giving
    back the coverage the retirement won, with no diff here to review. The
    cost is one line per retirement. What it buys is that re-entry has to be
    written into a list documented as only ever shrinking, in front of a
    reviewer watching it grow.

    """
    added, retired = _drift(_ignored(), RATCHET_BASELINE)
    assert not added, f"added to the typing ratchet: {sorted(added)}"
    assert not retired, (
        f"no longer ignored: {sorted(retired)} -- take them out of "
        "RATCHET_BASELINE in this change, so they cannot come back unseen"
    )


@pytest.mark.parametrize("module", sorted(_ignored()))
def test_ratchet_entry_resolves(module):
    """Every entry names a module that still exists.

    "mypy" does not warn on an override matching nothing, so a renamed or
    deleted module leaves an entry that can never be retired.

    """
    assert _resolve(module) is not None, f"{module!r} names nothing under 'src'"


def test_ratchet_reads_a_bare_module_string():
    """A "module" written as a string yields the module, not its characters."""
    assert _modules({"module": "geovista.cli"}) == ("geovista.cli",)
    assert _modules({"module": ["geovista.qt"]}) == ("geovista.qt",)
    assert _modules({}) == ()


def test_ratchet_is_not_empty():
    """Guard the suite against passing vacuously once the list is gone.

    ``test_ratchet_only_shrinks`` is satisfied by an empty ratchet, which is
    the intended end state. Reaching it must delete this module rather than
    leave three tests quietly asserting nothing.

    """
    assert _ignored(), "the ratchet is empty: delete this module and the override"


def test_mypy_hook_is_skipped_on_pre_commit_ci():
    """The local "mypy" hook needs "pixi", which "pre-commit.ci" has not got.

    Without the skip every "pre-commit.ci" run fails with "pixi: command not
    found", which reads as infrastructure flake rather than configuration.
    The coverage moves to ".github/workflows/ci-typing.yml".

    """
    config = yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8"))
    assert _hook()["language"] == "system", "a managed environment needs no skip"
    assert "mypy" in config["ci"]["skip"]


def test_ci_typing_names_a_declared_environment():
    """The workflow's pixi environment must exist in the manifest.

    A name that does not resolve fails the job at setup, with a message about
    the environment rather than about the manifest that should have declared
    it.

    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    declared = set(manifest["tool"]["pixi"]["environments"])
    named = {
        step["with"]["environments"]
        for step in _steps()
        if "setup-pixi" in str(step.get("uses", ""))
    }
    assert named, "ci-typing.yml sets up no pixi environment"
    assert named <= declared, f"undeclared: {sorted(named - declared)}"


def test_ci_typing_runs_the_hook_command():
    """The workflow must run the command "pre-commit.ci" is skipping.

    "mypy" is skipped on "pre-commit.ci" on the understanding that this
    workflow carries it instead, and nothing else holds it to that. The step
    can be deleted, or reduced to something that always succeeds, and the skip
    then retires the check outright while both jobs stay green. So the command
    has to end an enabled step, not merely appear somewhere in its script:
    this job overrides the shell to ``bash -l {0}``, dropping the ``-e`` that
    GitHub's default carries, and a command with anything after it can then
    fail while the step succeeds. ``frozen`` is part of the command too — it
    resolves from "pixi.lock" rather than re-solving the manifest, which is
    what makes the two environments the same one.

    """
    entry = _hook()["entry"]
    endings = [script[-1] for step in _steps() if (script := _commands(step))]
    assert entry in endings, f"no enabled step ends by running {entry!r}"
    setup = [step for step in _steps() if "setup-pixi" in str(step.get("uses", ""))]
    assert all(step["with"].get("frozen") for step in setup), "install from the lock"


def test_a_retired_module_cannot_return_unnoticed():
    """A name the baseline no longer carries reads as an addition.

    This is what a high-water-mark baseline gives away. Once a module is
    cleaned and taken off ``ignore_errors``, a baseline that still lists it
    accepts it back silently — handing back the coverage the retirement won,
    with nothing in the diff for a reviewer to catch.

    """
    added, retired = _drift(
        {"geovista.bridge", "geovista.transform"}, {"geovista.bridge"}
    )
    assert added == {"geovista.transform"}
    assert not retired


def test_a_retirement_must_take_the_baseline_with_it():
    """Retiring a module without updating the baseline is itself a failure.

    The two move together, so that re-entry has to be written back into a
    list documented as only ever shrinking, where review can see it.

    """
    added, retired = _drift(
        {"geovista.bridge"}, {"geovista.bridge", "geovista.transform"}
    )
    assert retired == {"geovista.transform"}
    assert not added


@pytest.mark.parametrize(
    "step",
    [
        pytest.param({"run": 'echo "check"'}, id="echoed"),
        pytest.param({"run": "# check"}, id="commented-out"),
        pytest.param({"run": "check || true"}, id="swallowed"),
        pytest.param({"run": "check &"}, id="backgrounded"),
        pytest.param({"if": "false", "run": "check"}, id="conditional"),
        pytest.param({"continue-on-error": True, "run": "check"}, id="tolerated"),
    ],
)
def test_only_an_executed_command_counts(step):
    """A command the step does not really run must not read as run.

    Each of these keeps the text of the command in the workflow while
    disposing of its effect: ``echo`` prints it, ``#`` comments it out,
    ``|| true`` and ``&`` discard its exit status, and ``if`` or
    ``continue-on-error`` excuse the step from mattering at all. Matching
    the command as a substring of the script accepts every one of them.

    """
    assert "check" not in _commands(step)


def test_the_last_command_of_an_enabled_step_counts():
    """The command ending an enabled step is the one whose failure lands."""
    assert _commands({"run": "echo starting\ncheck\n"})[-1] == "check"


def test_ci_typing_cannot_tolerate_its_own_failure():
    """No job may carry ``continue-on-error``.

    Such a job is green whatever "mypy" reports, which is the same outcome
    as having no job at all, and no guard written against a step can see it.

    """
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    tolerated = sorted(
        name for name, job in workflow["jobs"].items() if job.get("continue-on-error")
    )
    assert not tolerated, f"green whatever happens: {tolerated}"


def test_the_ratchet_is_the_only_suppression():
    """Nothing at the top of "[tool.mypy]" may silence what the ratchet counts.

    ``test_ratchet_only_shrinks`` reads the override blocks, so a suppression
    written above them is invisible to it. A top-level ``ignore_errors``
    silences every module at once, ``disable_error_code`` silences a class of
    error everywhere, and narrowing ``files`` or filling ``exclude`` drops
    modules from the run altogether. Each leaves the ratchet list untouched,
    and each would otherwise leave the whole suite green.

    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    mypy = manifest["tool"]["mypy"]
    assert not mypy.get("ignore_errors", False), "this silences every module"
    assert not mypy.get("disable_error_code", []), "disable per module, not globally"
    assert mypy["files"] == ["src/geovista"], "the whole package is checked"
    assert mypy["exclude"] == [], "an exclude drops modules from the run"

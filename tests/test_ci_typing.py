# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that "mypy" checks the whole package, in CI as in the hook.

GeoVista type checks in strict mode against the locked pixi environment, where
the third-party types are real. The modules that once reported errors were
listed under ``ignore_errors`` and retired one change at a time, until none was
left. These tests keep it that way: no override may ignore a module's errors,
and the workflow that runs "mypy" for "pre-commit.ci" must keep running it.

See "docs/src/developer/specs/2026-10-06-type-coverage-design.md", section 3.2.

"""

from __future__ import annotations

from functools import cache
from pathlib import Path
import tomllib
from typing import Any

import pytest
import yaml

#: The repository root, holding the manifest.
ROOT = Path(__file__).parents[1]
#: The manifest declaring the "mypy" configuration and its overrides.
PYPROJECT = ROOT / "pyproject.toml"
#: The hook configuration, which must skip "mypy" on "pre-commit.ci".
PRE_COMMIT = ROOT / ".pre-commit-config.yaml"
#: The workflow carrying the coverage "pre-commit.ci" cannot provide.
WORKFLOW = ROOT / ".github" / "workflows" / "ci-typing.yml"


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
        Collected from every override block, so that no block carrying
        ``ignore_errors`` goes unseen.

    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    overrides = manifest["tool"]["mypy"].get("overrides", [])
    return frozenset(
        module
        for override in overrides
        if override.get("ignore_errors", False)
        for module in _modules(override)
    )


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


def test_no_module_ignores_errors():
    """No override may tell "mypy" to ignore a module's errors.

    The typing ratchet listed every module that reported errors under
    ``ignore_errors`` and only ever shrank, until change 7 of the roadmap
    retired its last entry. An override that brought ``ignore_errors`` back
    would hand back the coverage those changes won, in one line of the
    manifest.

    """
    assert not _ignored(), f"errors ignored in: {sorted(_ignored())}"


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


def test_a_bare_module_string_is_read_whole():
    """A "module" written as a string yields the module, not its characters."""
    assert _modules({"module": "geovista.cli"}) == ("geovista.cli",)
    assert _modules({"module": ["geovista.qt"]}) == ("geovista.qt",)
    assert _modules({}) == ()


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


def test_no_global_suppression():
    """Nothing at the top of "[tool.mypy]" may silence a module's errors.

    ``test_no_module_ignores_errors`` reads the override blocks, so a
    suppression written above them is invisible to it. A top-level
    ``ignore_errors`` silences every module at once, ``disable_error_code``
    silences a class of error everywhere, and narrowing ``files`` or filling
    ``exclude`` drops modules from the run altogether. Each would otherwise
    leave the whole suite green.

    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    mypy = manifest["tool"]["mypy"]
    assert not mypy.get("ignore_errors", False), "this silences every module"
    assert not mypy.get("disable_error_code", []), "disable per module, not globally"
    assert mypy["files"] == ["src/geovista"], "the whole package is checked"
    assert mypy["exclude"] == [], "an exclude drops modules from the run"

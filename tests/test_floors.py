# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that the jobs at the dependency floors keep to the floors spec.

The ``floors`` environment resolves each direct dependency at the lowest release
its floor admits, and the ``tests floors`` job of ``ci-tests.yml`` runs the suite
in it on every pull request (floors spec §4.3). A job that quietly stopped doing
so would stay green while testing nothing at the floors, so these tests read the
workflow and the lock as text and hold the job to what the specification says.
They also hold the workspace to a pixi able to solve that environment.

"""

from __future__ import annotations

from functools import cache
from pathlib import Path
import re
import shlex
import tomllib
from typing import Any

import yaml

#: The repository root, holding the lock and the workflows.
ROOT = Path(__file__).parents[1]
#: The workflow carrying the floors job.
WORKFLOW = ROOT / ".github" / "workflows" / "ci-tests.yml"
#: The lock, in which the floors environment is resolved.
LOCK = ROOT / "pixi.lock"
#: The manifest, declaring the pixi the workspace requires.
PYPROJECT = ROOT / "pyproject.toml"
#: The first pixi with a solve strategy, which a floors environment declares.
STRATEGY_PIXI = (0, 59, 0)
#: A floor on the pixi version, as "requires-pixi" declares it.
REQUIRES = re.compile(r">=(\d+)\.(\d+)\.(\d+)")
#: The floors environment, and the job running the suite in it.
FLOORS = "floors"
#: The check the job reports, required on "main" (floors spec §2 decision 11).
NAME = "tests floors"
#: The job whose matrix the coverage upload waits on.
TESTS = "tests"
#: The job uploading the coverage report.
COVERAGE = "coverage"
#: The environments a lock declares, up to its first package.
ENVIRONMENTS = re.compile(r"^environments:\n(.*?)^packages:", re.DOTALL | re.MULTILINE)
#: How the lock records an environment solved at its lowest (floors spec §2 decision 1).
STRATEGY = r"^      strategy: lowest-version-direct$"
#: The shell operators that would let another command decide a line's status.
SHELL = frozenset(";|&")
#: The wrapper a command of the floors job may run under, for its display.
WRAPPER = ("xvfb-run", "-a")
#: The options of "pixi run" that take the environment as their value.
ENVIRONMENT = frozenset({"-e", "--environment"})


@cache
def _workflow() -> dict[Any, Any]:
    """Return the parsed workflow, read once."""
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _triggers() -> dict[str, Any]:
    """Return the workflow's triggers, which PyYAML keys by ``True`` for "on"."""
    workflow = _workflow()
    triggers = workflow.get("on", workflow.get(True))
    return triggers if isinstance(triggers, dict) else {}


def _job(name: str = FLOORS) -> dict[str, Any]:
    """Return the named job of the workflow."""
    jobs = _workflow().get("jobs", {})
    assert name in jobs, f"no {name!r} job in {WORKFLOW.name}"
    return jobs[name]


def _commands(step: dict[str, Any]) -> list[list[str]]:
    """Return the tokens of each command the step runs.

    Each line is split as the shell reads it, so a comment is no command, and a
    line holding only one is passed over.

    """
    lines = str(step.get("run", "")).splitlines()
    return [tokens for line in lines if (tokens := shlex.split(line, comments=True))]


def _lines(name: str = FLOORS) -> list[list[str]]:
    """Return the tokens of each command the named job runs."""
    return [
        tokens for step in _job(name).get("steps", []) for tokens in _commands(step)
    ]


def _unwrapped(tokens: list[str]) -> list[str]:
    """Return the command with the wrapper, if it runs under it, taken off."""
    if tuple(tokens[: len(WRAPPER)]) == WRAPPER:
        return tokens[len(WRAPPER) :]
    return tokens


def _program(tokens: list[str]) -> list[str]:
    """Return what a command runs through pixi, with its arguments, if it does.

    The command may run under the wrapper, then is "pixi run" and its options.
    Anything else, such as an echo of that command, runs nothing through pixi,
    and returns an empty list.

    """
    tokens = _unwrapped(tokens)
    if tokens[:2] != ["pixi", "run"]:
        return []
    rest, index = tokens[2:], 0
    while index < len(rest) and rest[index].startswith("-"):
        index += 2 if rest[index] in ENVIRONMENT else 1
    return rest[index:]


def _runs_pytest(tokens: list[str]) -> bool:
    """Say whether the command runs pytest through pixi."""
    return _program(tokens)[:1] == ["pytest"]


def _suite(name: str = FLOORS) -> list[str]:
    """Return the tokens of the one command of the named job that runs pytest."""
    suites = [tokens for tokens in _lines(name) if _runs_pytest(tokens)]
    assert len(suites) == 1, f"the {name!r} job runs pytest {len(suites)} times"
    return suites[0]


def _option(tokens: list[str], flag: str) -> str | None:
    """Return the value following the flag among the tokens, if any."""
    for index, token in enumerate(tokens[:-1]):
        if token == flag:
            return tokens[index + 1]
    return None


def test_the_floors_job_runs_on_every_pull_request():
    """A floor broken by a pull request goes red on that pull request.

    Holds floors spec §2 decision 2.
    """
    triggers = _triggers()
    assert "pull_request" in triggers, f"{WORKFLOW.name} does not run on pull requests"

    filters = triggers["pull_request"] or {}
    narrowed = sorted({"branches", "paths", "paths-ignore"} & set(filters))
    assert not narrowed, f"pull requests are filtered by {narrowed}"

    assert "if" not in _job(), f"the {FLOORS!r} job runs only if {_job()['if']!r}"

    gated = [step.get("name") for step in _job()["steps"] if "if" in step]
    assert not gated, f"steps of the {FLOORS!r} job run only on a condition: {gated}"


def test_the_floors_environment_is_locked():
    """Its result changes only when a commit changes something.

    Holds floors spec §2 decision 2.
    """
    found = ENVIRONMENTS.search(LOCK.read_text(encoding="utf-8"))
    assert found, f"no environments in {LOCK.name}"
    assert re.search(rf"^  {FLOORS}:$", found[1], re.MULTILINE), (
        f"{LOCK.name} does not lock {FLOORS!r}"
    )

    installs = [
        step.get("with", {})
        for step in _job().get("steps", [])
        if str(step.get("uses", "")).startswith("prefix-dev/setup-pixi@")
    ]
    assert installs, f"the {FLOORS!r} job installs no pixi environment"
    for install in installs:
        assert install.get("environments") == FLOORS
        assert install.get("frozen") is True

    block = re.search(rf"^  {FLOORS}:\n((?:    .*\n)+)", found[1], re.MULTILINE)
    assert block, f"{LOCK.name} declares {FLOORS!r} with no body"
    assert re.search(STRATEGY, block[1], re.MULTILINE), (
        f"{LOCK.name} does not solve {FLOORS!r} at its lowest"
    )


def test_the_floors_job_runs_the_floors_environment():
    """A run in another environment would test the lock's newest releases.

    Holds floors spec §2 decision 2.
    """
    runs = [tokens for tokens in _lines() if _unwrapped(tokens)[:2] == ["pixi", "run"]]
    assert runs, f"the {FLOORS!r} job runs nothing through pixi"

    wrong = [
        " ".join(tokens)
        for tokens in runs
        if "--frozen" not in tokens
        or (_option(tokens, "-e") or _option(tokens, "--environment")) != FLOORS
    ]

    assert not wrong, f"runs not frozen in the {FLOORS!r} environment: {wrong}"


def test_the_floors_job_leaves_out_the_image_tests():
    """It runs what the "tests not image" legs of the tests matrix run.

    Its workers and their distribution are read from the tests job, so a change
    there reaches the floors too. Holds floors spec §2 decision 10.
    """
    tokens, legs = _suite(), _suite(TESTS)

    assert _option(tokens, "-m") == "not image"
    for flag in ("--numprocesses", "--dist"):
        assert _option(tokens, flag) == _option(legs, flag), flag


def test_the_suite_decides_the_job():
    """The job's result is the suite's, whatever the shell does after it.

    The workflow runs ``bash -l {0}``, which drops ``errexit``, so a step's
    status is that of its last command, and pytest must be that command, alone
    on its line, with nothing to swallow its status. A commented or an echoed
    pytest runs nothing, so it is no suite. Follows floors spec §4.3.
    """
    steps = [
        step
        for step in _job()["steps"]
        if any(_runs_pytest(tokens) for tokens in _commands(step))
    ]
    assert len(steps) == 1, f"the {FLOORS!r} job runs pytest in {len(steps)} steps"

    last = _commands(steps[0])[-1]
    assert _runs_pytest(last), f"{shlex.join(last)!r} runs after the suite"

    swallowed = [token for token in last if set(token) & SHELL]
    assert not swallowed, f"the suite's status may be swallowed by {swallowed}"


def test_the_floors_job_stands_outside_the_tests_matrix():
    """A red floor never stops the coverage report, which waits on the matrix.

    Follows floors spec §4.3.
    """
    assert "strategy" not in _job(), f"the {FLOORS!r} job carries a matrix"
    assert TESTS in _workflow()["jobs"], f"no {TESTS!r} job in {WORKFLOW.name}"

    needs = _job(COVERAGE).get("needs", [])
    needs = [needs] if isinstance(needs, str) else needs

    assert FLOORS not in needs, f"the {COVERAGE!r} job waits on {FLOORS!r}"


def test_the_floors_check_names_no_version():
    """A SPEC 0 bump leaves the branch protection requiring it unchanged.

    Holds floors spec §2 decision 11.
    """
    assert _job().get("name") == NAME


def test_the_floors_job_can_fail():
    """A job or a step allowed to fail would let a broken floor merge."""
    assert "continue-on-error" not in _job(), f"the {FLOORS!r} job may fail silently"

    lenient = [
        step.get("name") for step in _job()["steps"] if "continue-on-error" in step
    ]
    assert not lenient, f"steps of the {FLOORS!r} job may fail silently: {lenient}"


def test_the_workspace_requires_a_pixi_that_can_solve_the_floors():
    """An older pixi stops with an error, rather than misreading the lock (#2976).

    The floor is a plain minimum, and admits no pixi without ``solve-strategy``,
    which the floors environment declares (floors spec §2 decision 1).
    """
    workspace = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["pixi"]
    declared = workspace["workspace"].get("requires-pixi")
    assert declared, f"{PYPROJECT.name} declares no requires-pixi"

    floor = REQUIRES.fullmatch(declared)
    assert floor, f"requires-pixi {declared!r} is not a plain minimum"
    assert tuple(int(part) for part in floor.groups()) >= STRATEGY_PIXI

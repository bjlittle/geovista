# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that hold the jobs at the pip floors to floors spec §4.3.

The ``pypi`` job of ``ci-floors.yml`` installs geovista with its ``test`` and
``exam`` extras at their lowest from PyPI, with ``uv``, on the oldest supported
Python, and runs the suite without the image tests. The ``floors-pypi`` composite
action does the work, so that ``ci-wheels.yml`` can run it against a built wheel
(row 4 of floors spec §9). The action restores the data through the two cache
actions, which run their commands from its environment rather than through
``pixi``.

The tests run the steps' own shell, with stand-ins for ``uv``, ``pixi`` and the
other commands on the ``PATH``, so they check what the steps do rather than how
they read.

"""

from __future__ import annotations

from pathlib import Path
import re
import shlex
import shutil
import tomllib
from typing import Any

import pytest
import yaml

#: The repository root, holding the workflows.
ROOT = Path(__file__).parents[1]
#: The directory of the composite actions.
COMPOSITE = ROOT / ".github" / "workflows" / "composite"
#: The composite actions restoring the data, which take the ``pixi`` input.
CACHES = ("cartopy-cache", "geovista-cache")
#: The composite action installing a target at its pip floors and testing it.
FLOORS = "floors-pypi"
#: The step of the action creating the uv environment.
SETUP = "setup uv"
#: The step of the action installing the target at its floors.
INSTALL = "uv install"
#: The step of the action writing what it installed to the summary.
FREEZE = "uv freeze"
#: The step of the action running the suite.
TESTS = "tests floors pypi"
#: The steps of the action restoring the data, each to the cache action it uses.
RESTORES = {"cartopy cache": "cartopy-cache", "geovista cache": "geovista-cache"}
#: The workflow whose test legs the floors job follows.
CI_TESTS = ROOT / ".github" / "workflows" / "ci-tests.yml"
#: The manifest declaring the pixi environments.
PYPROJECT = ROOT / "pyproject.toml"
#: The pixi environment at the dependency floors.
ENVIRONMENT = "floors"
#: The wrapper that gives a command a display.
WRAPPER = ("xvfb-run", "-a")
#: The extras the action installs with its target.
EXTRAS = "[test,exam]"
#: A wheel, as row 4 of floors spec §9 passes the action.
WHEEL = "dist/geovista-0.6.0-py3-none-any.whl"
#: A line of the freeze.
PINNED = "numpy==2.2.6"

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None, reason="the actions' steps run under bash"
)


def _action(name: str) -> dict[str, Any]:
    """Return the parsed composite action of the given name."""
    path = COMPOSITE / name / "action.yml"
    assert path.is_file(), f"no composite action {name!r}"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _step(steps: list[dict[str, Any]], name: str) -> dict[str, Any]:
    """Return the one step of the given name."""
    found = [step for step in steps if step.get("name") == name]
    assert len(found) == 1, f"{len(found)} steps named {name!r}"
    return found[0]


@pytest.mark.parametrize("name", CACHES)
def test_the_cache_actions_run_through_pixi_by_default(name):
    """A caller that passes nothing runs the cache action as before."""
    pixi = _action(name).get("inputs", {}).get("pixi")

    assert pixi is not None, f"{name!r} takes no 'pixi' input"
    assert pixi.get("required") is False
    assert pixi.get("default") == "true"


@pytest.mark.parametrize(
    ("name", "step", "command"),
    [
        ("cartopy-cache", "refresh cartopy cache", "cartopy_feature_download"),
        ("geovista-cache", "get geovista-data version", "geovista"),
        ("geovista-cache", "refresh geovista cache", "geovista"),
    ],
)
@pytest.mark.parametrize("pixi", ["true", "false"])
def test_a_cache_action_runs_its_command_through_pixi_unless_told_not_to(
    tmp_path, stub, run_step, name, step, command, pixi
):
    """The floors job has no pixi, and runs the command from its environment."""
    body = _step(_action(name)["runs"]["steps"], step)
    log = tmp_path / "calls.log"
    for word in ("pixi", command):
        stub(word, f'printf "%s\\n" "{word} $*" >> "{log}"')
    env = {"INPUTS_PIXI": pixi, "GITHUB_OUTPUT": str(tmp_path / "output")}

    result = run_step(body, env)

    assert result.returncode == 0, result.stderr
    assert (body.get("env") or {}).get("INPUTS_PIXI") == "${{ inputs.pixi }}"
    calls = log.read_text(encoding="utf-8").splitlines()
    assert calls, f"{step!r} ran nothing"
    first = {call.split()[0] for call in calls}
    if pixi == "true":
        assert first == {"pixi"}, calls
    else:
        assert first == {command}, calls


def _floors_python() -> str:
    """Return the minor Python version the ``floors`` environment pins."""
    pixi = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["pixi"]
    features = pixi["environments"][ENVIRONMENT]["features"]
    pins = [
        pixi["feature"][name]["dependencies"]["python"]
        for name in features
        if re.fullmatch(r"py3\d+", name)
    ]
    assert len(pins) == 1, f"{len(pins)} Python features in {ENVIRONMENT!r}"
    match = re.fullmatch(r"(\d+\.\d+)\.\*", pins[0])
    assert match, f"{ENVIRONMENT!r} pins Python as {pins[0]!r}"
    return match.group(1)


def _steps() -> list[dict[str, Any]]:
    """Return the steps of the floors action."""
    return _action(FLOORS)["runs"]["steps"]


def _commands(step: dict[str, Any]) -> list[list[str]]:
    """Return the tokens of each command the step runs, passing comments over."""
    lines = str(step.get("run", "")).splitlines()
    return [tokens for line in lines if (tokens := shlex.split(line, comments=True))]


def _unwrapped(tokens: list[str]) -> list[str]:
    """Return the command with the display wrapper, if it runs under it, taken off."""
    if tuple(tokens[: len(WRAPPER)]) == WRAPPER:
        return tokens[len(WRAPPER) :]
    return tokens


def _calls(log: Path) -> list[str]:
    """Return the calls a stand-in logged, one to a line."""
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def test_the_action_installs_on_the_python_of_the_floors_environment():
    """The floors are those of the oldest supported Python (floors spec §2 decision 9).

    A SPEC 0 bump that moves the ``floors`` environment fails here until the
    action follows it.
    """
    setup = _step(_steps(), SETUP)
    given = setup.get("with", {})

    assert re.fullmatch(r"astral-sh/setup-uv@[0-9a-f]{40}", setup.get("uses", ""))
    assert str(given.get("python-version")) == _floors_python()
    assert str(given.get("activate-environment")).lower() == "true"
    assert str(given.get("enable-cache")).lower() == "false"


@pytest.mark.parametrize("target", [".", WHEEL])
def test_the_install_takes_the_extras_at_their_lowest(tmp_path, stub, run_step, target):
    """Each direct requirement resolves at its floor (floors spec §2 decision 8)."""
    install = _step(_steps(), INSTALL)
    log = tmp_path / "uv.log"
    stub("uv", f'printf "%s\\n" "$*" >> "{log}"')

    result = run_step(install, {"TARGET": target})

    assert result.returncode == 0, result.stderr
    assert (install.get("env") or {}).get("TARGET") == "${{ inputs.target }}"
    assert _calls(log) == [f"pip install --resolution lowest-direct {target}{EXTRAS}"]


@pytest.mark.parametrize(
    ("failures", "passes"), [(1, True), (99, False)], ids=["once", "always"]
)
def test_the_install_is_retried_once(tmp_path, stub, run_step, failures, passes):
    """A fault of the index is retried, and a floor that cannot install is not."""
    log = tmp_path / "uv.log"
    stub(
        "uv",
        f'printf "%s\\n" "$*" >> "{log}"\n[ "$(wc -l < "{log}")" -gt {failures} ]',
    )

    result = run_step(_step(_steps(), INSTALL), {"TARGET": "."})

    assert (result.returncode == 0) is passes, result.stderr
    assert len(_calls(log)) == 2


def test_the_freeze_is_written_to_the_summary(tmp_path, stub, run_step):
    """The versions the run installed can be read from the run's page."""
    stub("uv", f'if [ "$1 $2" = "pip freeze" ]; then echo "{PINNED}"; fi')
    summary = tmp_path / "summary.md"

    result = run_step(_step(_steps(), FREEZE), {"GITHUB_STEP_SUMMARY": str(summary)})

    assert result.returncode == 0, result.stderr
    assert PINNED in summary.read_text(encoding="utf-8").splitlines()


def test_the_action_restores_the_data_without_pixi():
    """The data is that of the other test jobs, restored from the uv environment."""
    steps = _steps()
    tests = steps.index(_step(steps, TESTS))

    for name, action in RESTORES.items():
        step = _step(steps, name)
        assert str(step.get("uses", "")).endswith(
            f".github/workflows/composite/{action}"
        ), step
        assert step.get("with") == {
            "cache_period": "${{ inputs.cache_period }}",
            "pixi": "false",
        }
        assert steps.index(step) < tests, f"{name!r} runs after the tests"


def test_the_action_leaves_out_the_image_tests():
    """No image test runs at the floors (floors spec §2 decision 10)."""
    ci_tests = yaml.safe_load(CI_TESTS.read_text(encoding="utf-8"))
    markers = ci_tests["jobs"]["tests"]["strategy"]["matrix"]["marker"]
    runs = [
        tokens
        for tokens in _commands(_step(_steps(), TESTS))
        if _unwrapped(tokens)[:1] == ["pytest"]
    ]

    assert len(runs) == 1, runs
    (tokens,) = runs
    assert tuple(tokens[: len(WRAPPER)]) == WRAPPER, tokens
    command = _unwrapped(tokens)
    assert "-m" in command, command
    marker = command[command.index("-m") + 1]
    assert marker in markers
    assert marker == "not image"


def test_the_suite_decides_the_step():
    """The step passes or fails as the suite does, and nothing follows it."""
    step = _step(_steps(), TESTS)
    commands = _commands(step)

    assert commands, f"{TESTS!r} runs nothing"
    assert _unwrapped(commands[-1])[:1] == ["pytest"], commands[-1]
    for line in str(step["run"]).splitlines():
        assert not set(line) & set(";|&"), line

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

from functools import cache
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from typing import TYPE_CHECKING, Any
import zipfile

import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

#: The repository root, holding the workflows.
ROOT = Path(__file__).parents[1]
#: The directory of the composite actions.
COMPOSITE = ROOT / ".github" / "workflows" / "composite"
#: The composite actions restoring the data, which take the ``pixi`` input.
CACHES = ("cartopy-cache", "geovista-cache")
#: The steps of ``geovista-cache`` that run ``geovista``.
GEOVISTA_STEPS = ("get geovista-data version", "refresh geovista cache")
#: A pixi environment a caller names, as ``ci-tests-lock.yml`` does.
NAMED = "test-py313"
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
#: The variables the suite needs, which the action sets rather than its caller.
SUITE_ENV = ("PYVISTA_OFF_SCREEN", "GEOVISTA_POOCH_MUTE")
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
#: The script reading the requirements a wheel declares, which the action runs.
READER = ROOT / ".github" / "scripts" / "wheel_requirements.py"
#: The requirements a wheel declares, as its METADATA writes them: its core, the
#: two extras the action installs, and an extra it does not.
REQUIRES = (
    "numpy<3,>=2.2.6",
    'pytest<10,>=8.4.0; extra == "test"',
    'pandas<4,>=2.2.3; extra == "exam"',
    'sphinx<9,>=8.2.3; extra == "docs"',
)
#: Those the action passes to uv as direct requirements beside the wheel.
DIRECT = ["numpy<3,>=2.2.6", "pytest<10,>=8.4.0", "pandas<4,>=2.2.3"]
#: The workflow running the jobs at the floors each week.
WORKFLOW = ROOT / ".github" / "workflows" / "ci-floors.yml"
#: The job installing the checkout at its pip floors.
JOB = "pypi"
#: The step reporting a failed run.
REPORT = "report failure"
#: When the report runs: a failed run of the schedule, not one started by hand.
WHEN = "${{ failure() && github.event_name == 'schedule' }}"
#: The title of the issue the report opens.
TITLE = "chore: pypi floors failure"
#: The run the report links.
RUN_URL = "https://github.com/bjlittle/geovista/actions/runs/1234"
#: The section of the testing guide describing the workflow, which the report
#: links so that its reader lands on what a failure means.
GUIDE = (
    "https://geovista.readthedocs.io/en/latest/developer/testing.html"
    "#gv-developer-testing-continuous-integration"
)
#: The workflow that builds, tests and publishes the wheel.
WHEELS = ROOT / ".github" / "workflows" / "ci-wheels.yml"
#: The job of ``ci-wheels.yml`` testing the built wheel at its pip floors.
GATE = "test-floors"
#: When the gate runs: on a ``v*`` tag, and by hand, never on a pull request.
GATE_WHEN = (
    "${{ github.event_name == 'workflow_dispatch' || (github.event_name == 'push'"
    " && startsWith(github.event.ref, 'refs/tags/v')) }}"
)
#: The step of the gate finding the wheel it tests.
FIND = "find wheel"
#: The job publishing a tag to PyPI.
RELEASE = "publish-artifacts-pypi"
#: The job publishing each push to ``main`` to Test PyPI.
TEST_PYPI = "publish-artifacts-test-pypi"
#: The job testing that the wheel installs on each supported Python.
ARTIFACTS = "test-artifacts"

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


@pytest.mark.parametrize("step", GEOVISTA_STEPS)
@pytest.mark.parametrize("pixi", ["true", "false"])
def test_the_geovista_cache_runs_in_the_pixi_environment_it_is_given(
    tmp_path, stub, run_step, step, pixi
):
    """``ci-tests-lock.yml`` names its environment, and the ``pixi`` input keeps it.

    With ``pixi`` false, the command runs from the ``PATH`` whatever the
    environment named.
    """
    body = _step(_action("geovista-cache")["runs"]["steps"], step)
    log = tmp_path / "calls.log"
    for word in ("pixi", "geovista"):
        stub(word, f'printf "%s\\n" "{word} $*" >> "{log}"')
    env = {
        "INPUTS_PIXI": pixi,
        "INPUTS_PIXI_ENVIRONMENT": NAMED,
        "GITHUB_OUTPUT": str(tmp_path / "output"),
    }

    result = run_step(body, env)

    assert result.returncode == 0, result.stderr
    given = (body.get("env") or {}).get("INPUTS_PIXI_ENVIRONMENT")
    assert given == "${{ inputs.pixi_environment }}"
    calls = _calls(log)
    assert calls, f"{step!r} ran nothing"
    prefix = f"pixi run --frozen --environment {NAMED} geovista "
    if pixi == "false":
        prefix = "geovista "
    for call in calls:
        assert call.startswith(prefix), calls


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


def test_the_install_takes_the_extras_at_their_lowest(tmp_path, stub, run_step):
    """Each direct requirement resolves at its floor (floors spec §2 decision 8)."""
    install = _step(_steps(), INSTALL)
    log = tmp_path / "uv.log"
    stub("uv", f'printf "%s\\n" "$*" >> "{log}"')

    result = run_step(install, {"TARGET": "."})

    assert result.returncode == 0, result.stderr
    assert (install.get("env") or {}).get("TARGET") == "${{ inputs.target }}"
    assert _calls(log) == [f"pip install --resolution lowest-direct .{EXTRAS}"]


def _wheel(path: Path, requires: Iterable[str]) -> Path:
    """Write a wheel whose METADATA declares the given requirements."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["Metadata-Version: 2.4", "Name: geovista", "Version: 0.6.0"]
    lines += [f"Requires-Dist: {requirement}" for requirement in requires]
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("geovista/__init__.py", "")
        archive.writestr("geovista-0.6.0.dist-info/METADATA", "\n".join(lines) + "\n")
    return path


def test_a_wheel_takes_its_own_requirements_as_direct(tmp_path, stub, run_step):
    """Each requirement the wheel declares resolves at its floor too.

    ``uv`` takes a wheel's own requirements as transitive, and so at their
    highest, so the action passes them as direct beside the wheel, to test the
    floors the wheel promises (floors spec §2 decision 7).
    """
    _wheel(tmp_path / WHEEL, REQUIRES)
    log = tmp_path / "uv.log"
    read = tmp_path / "read.log"
    # log each call, then the lines of each requirements file it is given
    stub(
        "uv",
        f'printf "%s\\n" "$*" >> "{log}"\n'
        f'while [ $# -gt 0 ]; do [ "$1" = "-r" ] && cat "$2" >> "{read}"; shift; done\n'
        "true",
    )
    env = {
        "TARGET": WHEEL,
        "GITHUB_ACTION_PATH": str(COMPOSITE / FLOORS),
        "RUNNER_TEMP": str(tmp_path),
    }

    result = run_step(_step(_steps(), INSTALL), env)

    assert result.returncode == 0, result.stderr
    (call,) = _calls(log)
    assert call.startswith(
        f"pip install --resolution lowest-direct {WHEEL}{EXTRAS} -r "
    )
    assert _calls(read) == DIRECT


@pytest.mark.parametrize(
    ("requires", "says"),
    [
        (['numpy<3,>=2.2.6; python_version < "3.14"'], "python_version"),
        (None, "METADATA"),
    ],
    ids=["marker", "no-metadata"],
)
def test_the_reader_refuses_what_it_cannot_read(tmp_path, requires, says):
    """A requirement kept or dropped by a guess would test the wrong floors."""
    wheel = tmp_path / WHEEL
    if requires is None:
        wheel.parent.mkdir(parents=True)
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr("geovista/__init__.py", "")
    else:
        _wheel(wheel, requires)

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-I", str(READER), str(wheel), "test,exam"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert not result.stdout
    assert says in result.stderr, result.stderr


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
    """The data is that of the other test jobs, restored from the uv environment.

    The cache actions run ``geovista`` and ``cartopy_feature_download`` from the
    ``PATH``, so they come after the install that puts them there.
    """
    steps = _steps()
    install = steps.index(_step(steps, INSTALL))
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
        assert install < steps.index(step), f"{name!r} runs before {INSTALL!r}"
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


def test_the_action_runs_the_suite_as_the_floors_job_does():
    """The whole suite runs, as the ``tests floors`` job of ``ci-tests.yml`` runs it.

    Row 1 of floors spec §9 defines what the ``tests not image`` legs run, so a
    suite narrowed to some of its tests, or only collected, fails here.
    """
    ci_tests = yaml.safe_load(CI_TESTS.read_text(encoding="utf-8"))
    floors = _step(ci_tests["jobs"]["floors"]["steps"], "tests floors")
    (expected,) = [
        _unwrapped(tokens)[_unwrapped(tokens).index("pytest") :]
        for tokens in _commands(floors)
        if "pytest" in tokens
    ]
    (command,) = [
        _unwrapped(tokens)
        for tokens in _commands(_step(_steps(), TESTS))
        if _unwrapped(tokens)[:1] == ["pytest"]
    ]

    assert command == expected


def test_the_suite_decides_the_step():
    """The step passes or fails as the suite does, and nothing follows it."""
    step = _step(_steps(), TESTS)
    commands = _commands(step)

    assert commands, f"{TESTS!r} runs nothing"
    assert _unwrapped(commands[-1])[:1] == ["pytest"], commands[-1]
    for line in str(step["run"]).splitlines():
        assert not set(line) & set(";|&"), line


@pytest.mark.parametrize("name", SUITE_ENV)
def test_the_action_sets_the_environment_the_suite_needs(name):
    """No caller has to set it, as ``ci-wheels.yml`` sets none (floors spec §8 item 2).

    ``pyvista`` renders off screen, and ``geovista.cache`` keeps pooch quiet.
    """
    env = _step(_steps(), TESTS).get("env") or {}

    assert name in env, f"{TESTS!r} leaves {name} to its caller"
    assert str(env[name]).lower() == "true", env[name]


@cache
def _workflow() -> dict[Any, Any]:
    """Return the parsed workflow, read once."""
    assert WORKFLOW.is_file(), f"no workflow {WORKFLOW.name!r}"
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _on(workflow: dict[Any, Any]) -> dict[str, Any]:
    """Return a workflow's triggers, which PyYAML keys by ``True`` for "on"."""
    triggers = workflow.get("on", workflow.get(True))
    return triggers if isinstance(triggers, dict) else {}


def _triggers() -> dict[str, Any]:
    """Return the triggers of ``ci-floors.yml``."""
    return _on(_workflow())


def _job() -> dict[str, Any]:
    """Return the job installing the checkout at its pip floors."""
    jobs = _workflow().get("jobs", {})
    assert JOB in jobs, f"no {JOB!r} job in {WORKFLOW.name}"
    return jobs[JOB]


def test_the_workflow_runs_each_week_and_by_hand():
    """A floor that PyPI breaks is found within the week (floors spec §4.3).

    The job runs on no pull request, so a pull request is never failed by a
    release it did not make. A trigger left from watching the job on its own
    pull request fails here.
    """
    triggers = _triggers()

    assert set(triggers) == {"schedule", "workflow_dispatch"}, set(triggers)
    (entry,) = triggers["schedule"]
    _minute, _hour, day, month, weekday = str(entry["cron"]).split()
    assert (day, month) == ("*", "*"), entry
    assert re.fullmatch(r"[0-6]", weekday), entry
    job = _job()
    assert "if" not in job, "the job does not run on every trigger"
    for step in job.get("steps", []):
        if str(step.get("uses", "")).endswith(f".github/workflows/composite/{FLOORS}"):
            assert "if" not in step, "the action does not run on every trigger"


def test_the_workflow_grants_nothing_by_default():
    """A job is granted only what it asks for."""
    assert _workflow().get("permissions") == {}


def test_the_pypi_job_may_read_and_report_and_nothing_more():
    """The job's token reads the checkout and writes the report, and no more."""
    assert _job().get("permissions") == {"contents": "read", "issues": "write"}


def test_the_pypi_job_runs_the_action_against_the_checkout():
    """Row 4 of floors spec §9 runs the same action against a built wheel."""
    steps = _job().get("steps", [])
    checkouts = [
        index
        for index, step in enumerate(steps)
        if str(step.get("uses", "")).startswith("actions/checkout@")
    ]
    runs = [
        index
        for index, step in enumerate(steps)
        if str(step.get("uses", "")).endswith(f".github/workflows/composite/{FLOORS}")
    ]

    assert len(checkouts) == 1, checkouts
    assert len(runs) == 1, runs
    assert checkouts[0] < runs[0], "the action runs before the checkout"
    given = steps[runs[0]].get("with", {})
    assert given.get("target") == "."
    assert given.get("cache_period") == "${{ env.CACHE_PERIOD }}"


def test_the_report_runs_on_a_failed_weekly_run_alone():
    """A run started by hand is watched by whoever started it."""
    steps = _job().get("steps", [])
    report = _step(steps, REPORT)

    assert " ".join(str(report.get("if", "")).split()) == WHEN
    assert steps[-1] is report, f"{REPORT!r} is not the job's last step"


@pytest.mark.parametrize(("open_issue", "verb"), [("", "create"), ("42", "comment")])
def test_the_report_opens_an_issue_or_comments_on_the_open_one(
    tmp_path, stub, run_step, open_issue, verb
):
    """Weeks of the same failure make one issue with comments, not many issues."""
    log = tmp_path / "gh.log"
    stub(
        "gh",
        f'printf "%s\\n" "$*" >> "{log}"\n'
        f'if [ "$1 $2" = "issue list" ]; then echo "{open_issue}"; fi',
    )
    env = {"REPO": "bjlittle/geovista", "RUN_URL": RUN_URL}

    result = run_step(_step(_job().get("steps", []), REPORT), env)

    assert result.returncode == 0, result.stderr
    calls = _calls(log)
    assert calls[0].startswith("issue list"), calls
    assert TITLE in calls[0]
    (written,) = [call for call in calls[1:] if call.startswith("issue ")]
    assert written.startswith(f"issue {verb}"), written
    if verb == "create":
        assert TITLE in written
        assert "--label bot" in written
    else:
        assert written.startswith("issue comment 42")

    body = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert RUN_URL in body
    assert GUIDE in body, "the report does not link the testing guide"
    assert "pixi lock" in body, "the report does not say how to raise a floor"
    for step in (INSTALL, TESTS):
        # A floor fails one of these steps, and a fault elsewhere fails any other
        assert f"`{step}`" in body, f"the report does not name the {step!r} step"


@cache
def _wheels() -> dict[Any, Any]:
    """Return the parsed ``ci-wheels.yml``, read once."""
    assert WHEELS.is_file(), f"no workflow {WHEELS.name!r}"
    return yaml.safe_load(WHEELS.read_text(encoding="utf-8"))


def _wheels_job(name: str) -> dict[str, Any]:
    """Return the job of ``ci-wheels.yml`` of the given name."""
    jobs = _wheels().get("jobs", {})
    assert name in jobs, f"no {name!r} job in {WHEELS.name}"
    return jobs[name]


def _needs(job: dict[str, Any]) -> set[str]:
    """Return the jobs a job needs."""
    needs = job.get("needs", [])
    return {needs} if isinstance(needs, str) else set(needs)


def _condition(job: dict[str, Any]) -> str:
    """Return a job's ``if``, its whitespace collapsed."""
    return " ".join(str(job.get("if", "")).split())


def test_the_wheels_can_be_run_by_hand():
    """The gate can be run before a release (floors spec §4.3)."""
    triggers = _on(_wheels())

    assert {"workflow_dispatch", "pull_request", "push"} <= set(triggers)
    assert (triggers["push"] or {}).get("tags") == ["v*"]


def test_the_gate_runs_on_a_tag_and_by_hand_alone():
    """A pull request or a push to ``main`` never waits for the floors.

    A condition left from watching the job on its own pull request fails here.
    """
    assert _condition(_wheels_job(GATE)) == GATE_WHEN


def test_the_gate_tests_the_built_wheel():
    """The wheel a release publishes is the one tested (floors spec §2 decision 7)."""
    job = _wheels_job(GATE)
    steps = job.get("steps", [])

    def index(match: Callable[[dict[str, Any]], bool]) -> int:
        found = [at for at, step in enumerate(steps) if match(step)]
        assert len(found) == 1, found
        return found[0]

    checkout = index(
        lambda step: str(step.get("uses", "")).startswith("actions/checkout@")
    )
    download = index(
        lambda step: str(step.get("uses", "")).startswith("actions/download-artifact@")
    )
    find = index(lambda step: step.get("id") == "wheel")
    run = index(
        lambda step: str(step.get("uses", "")).endswith(
            f".github/workflows/composite/{FLOORS}"
        )
    )

    assert _needs(job) == {"build-artifacts"}
    assert "permissions" not in job, job["permissions"]
    assert job.get("runs-on") == _job().get("runs-on"), "not where the floors run"
    assert checkout < download < find < run
    given = steps[download].get("with", {})
    assert given.get("pattern") == "pypi-artifacts-*"
    assert str(given.get("path")).endswith("/dist")
    assert steps[find].get("name") == FIND
    assert steps[run].get("with") == {
        "target": "${{ steps.wheel.outputs.path }}",
        "cache_period": "${{ env.CACHE_PERIOD }}",
    }


@pytest.mark.parametrize(
    ("wheels", "passes"),
    [
        ([Path(WHEEL).name], True),
        ([], False),
        ([Path(WHEEL).name, "geovista-0.6.1-py3-none-any.whl"], False),
    ],
    ids=["one", "none", "two"],
)
def test_the_gate_finds_the_one_wheel(tmp_path, run_step, wheels, passes):
    """A build that emits no wheel, or two, fails rather than testing a guess."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "geovista-0.6.0.tar.gz").write_bytes(b"")
    for name in wheels:
        (dist / name).write_bytes(b"")
    output = tmp_path / "output"
    step = dict(_step(_wheels_job(GATE).get("steps", []), FIND))
    # the workflow's "bash -l {0}" drops errexit, so the step must exit itself
    step["run"] = f"set +e\n{step['run']}"

    result = run_step(step, {"GITHUB_OUTPUT": str(output)})

    assert (result.returncode == 0) is passes, result.stdout + result.stderr
    written = output.read_text(encoding="utf-8").splitlines() if output.exists() else []
    if passes:
        assert written == [f"path=dist/{Path(WHEEL).name}"]
    else:
        assert not [line for line in written if line.startswith("path=")], written


def test_a_release_waits_for_the_floors():
    """No release reaches PyPI until its wheel passes at its floors."""
    assert _needs(_wheels_job(RELEASE)) == {ARTIFACTS, GATE}


def test_the_test_pypi_upload_does_not_wait_for_the_floors():
    """The gate is skipped on a push to ``main``, so waiting would skip the upload."""
    assert _needs(_wheels_job(TEST_PYPI)) == {ARTIFACTS}


@pytest.mark.parametrize("name", [RELEASE, TEST_PYPI])
def test_a_run_by_hand_publishes_nothing(name):
    """Only a push publishes, so the gate can be run before a release."""
    condition = _condition(_wheels_job(name))
    inner = condition.removeprefix("${{").removesuffix("}}")
    clauses = [clause.strip() for clause in inner.split("&&")]

    assert "github.event_name == 'push'" in clauses, condition
    assert "||" not in inner, condition

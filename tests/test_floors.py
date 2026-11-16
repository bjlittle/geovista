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

"""

from __future__ import annotations

from functools import cache
from pathlib import Path
import re
import shlex
from typing import Any

import yaml

#: The repository root, holding the lock and the workflows.
ROOT = Path(__file__).parents[1]
#: The workflow carrying the floors job.
WORKFLOW = ROOT / ".github" / "workflows" / "ci-tests.yml"
#: The lock, in which the floors environment is resolved.
LOCK = ROOT / "pixi.lock"
#: The floors environment, and the job running the suite in it.
FLOORS = "floors"
#: The check the job reports, required on "main" (floors spec §2 decision 11).
CHECK = "tests floors"
#: The job whose matrix the coverage upload waits on.
TESTS = "tests"
#: The job uploading the coverage report.
COVERAGE = "coverage"
#: How every "pixi run" of the floors job begins.
RUN = f"pixi run --frozen -e {FLOORS}"
#: The environments a lock declares, up to its first package.
ENVIRONMENTS = re.compile(r"^environments:\n(.*?)^packages:", re.DOTALL | re.MULTILINE)


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


def _lines() -> list[str]:
    """Return each line of shell the floors job runs, stripped."""
    return [
        line.strip()
        for step in _job().get("steps", [])
        for line in str(step.get("run", "")).splitlines()
        if line.strip()
    ]


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


def test_the_floors_job_runs_the_floors_environment():
    """A run in another environment would test the lock's newest releases.

    Holds floors spec §2 decision 2.
    """
    runs = [line for line in _lines() if "pixi run" in line]
    assert runs, f"the {FLOORS!r} job runs nothing through pixi"

    wrong = [
        line for line in runs if not line.removeprefix("xvfb-run -a ").startswith(RUN)
    ]

    assert not wrong, f"runs not in the {FLOORS!r} environment: {wrong}"


def test_the_floors_job_leaves_out_the_image_tests():
    """It runs what the "tests not image" legs of the tests matrix run.

    Holds floors spec §2 decision 10.
    """
    suites = [shlex.split(line) for line in _lines() if " pytest " in f" {line} "]
    assert len(suites) == 1, f"the {FLOORS!r} job runs pytest {len(suites)} times"

    (tokens,) = suites
    assert _option(tokens, "-m") == "not image"
    assert _option(tokens, "--numprocesses") == "logical"
    assert _option(tokens, "--dist") == "worksteal"


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
    assert _job().get("name") == CHECK


def test_the_floors_job_can_fail():
    """A job allowed to fail would let a broken floor merge."""
    assert "continue-on-error" not in _job(), f"the {FLOORS!r} job may fail silently"

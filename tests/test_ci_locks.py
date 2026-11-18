# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that a failed weekly lock update reports itself.

``ci-locks.yml`` runs ``pixi update`` each Sunday and opens a pull request with
the new lock. When the update fails, no environment's lock moves, so the failure
is reported as an issue, or a comment on the open one, rather than left as a red
run that nobody is asked to read (#2977). From 2026-09-06 to 2026-09-27 one
environment that could not be solved stalled every lock for four weeks unseen.

The tests run the workflow's own shell, with stand-ins for ``pixi`` and ``gh``
on the ``PATH``, so they check what the steps do rather than how they read.

"""

from __future__ import annotations

from functools import cache
from pathlib import Path
import shutil
from typing import Any

import pytest
import yaml

#: The repository root, holding the workflows.
ROOT = Path(__file__).parents[1]
#: The workflow refreshing the lock each week.
WORKFLOW = ROOT / ".github" / "workflows" / "ci-locks.yml"
#: The job running the update.
JOB = "pixi-update"
#: The step running ``pixi update``.
UPDATE = "refresh pixi manifest"
#: The step reporting a failed update.
REPORT = "report failure"
#: When the report runs: a failed run of the schedule, not one started by hand.
WHEN = "${{ failure() && github.event_name == 'schedule' }}"
#: The title of the issue the report opens.
TITLE = "chore: pixi lock update failure"
#: What pixi says when an environment cannot be solved, as it said in September.
ERROR = (
    "Error:   \N{MULTIPLICATION SIGN} failed to solve the pypi requirements of "
    "environment 'floors' "
    "for platform 'linux-64'"
)
#: The run the report links.
RUN_URL = "https://github.com/bjlittle/geovista/actions/runs/1234"
#: The section of the packaging guide describing the workflow, which the report
#: links so that its reader lands on what a failure means.
GUIDE = (
    "https://geovista.readthedocs.io/en/latest/developer/packaging.html"
    "#gv-developer-packaging-continuous-integration"
)

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None, reason="the workflow's steps run under bash"
)


@cache
def _workflow() -> dict[Any, Any]:
    """Return the parsed workflow, read once."""
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _job() -> dict[str, Any]:
    """Return the job running the update."""
    jobs = _workflow().get("jobs", {})
    assert JOB in jobs, f"no {JOB!r} job in {WORKFLOW.name}"
    return jobs[JOB]


def _step(name: str) -> dict[str, Any]:
    """Return the named step of the job."""
    steps = [step for step in _job().get("steps", []) if step.get("name") == name]
    assert len(steps) == 1, f"{len(steps)} steps named {name!r} in {JOB!r}"
    return steps[0]


def test_a_failed_update_keeps_pixis_error(tmp_path, stub, run_step):
    """The update still fails the step, and its error is kept for the report.

    The stand-in reports nothing moved before failing, so that only the update's
    own status can fail the step.
    """
    stub(
        "pixi",
        f'echo \'{{"environment": {{}}}}\'\necho "{ERROR}" >&2\nexit 1',
    )

    result = run_step(_step(UPDATE), {})

    assert result.returncode != 0, "a failed update passed its step"
    assert ERROR in (tmp_path / "update.err").read_text(encoding="utf-8")
    assert ERROR in result.stdout + result.stderr, "the error left the step's log"


def test_the_report_runs_on_a_failed_weekly_run_alone():
    """A run started by hand is watched by whoever started it."""
    report = _step(REPORT)

    assert " ".join(str(report.get("if", "")).split()) == WHEN
    assert _job()["steps"][-1] is report, f"{REPORT!r} is not the job's last step"


def test_the_report_may_open_an_issue_and_nothing_more():
    """The job's token is granted what the report needs, and no more."""
    assert _job().get("permissions") == {"issues": "write"}


@pytest.mark.parametrize(("open_issue", "verb"), [("", "create"), ("42", "comment")])
def test_the_report_opens_an_issue_or_comments_on_the_open_one(
    tmp_path, stub, run_step, open_issue, verb
):
    """Four stalled weeks make one issue with three comments, not four issues."""
    log = tmp_path / "gh.log"
    stub(
        "gh",
        f'printf "%s\\n" "$*" >> "{log}"\n'
        f'if [ "$1 $2" = "issue list" ]; then echo "{open_issue}"; fi',
    )
    (tmp_path / "update.err").write_text(f"{ERROR}\n  ├─▶ failed\n", encoding="utf-8")
    env = {"REPO": "bjlittle/geovista", "RUN_URL": RUN_URL}

    result = run_step(_step(REPORT), env)

    assert result.returncode == 0, result.stderr
    calls = log.read_text(encoding="utf-8").splitlines()
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
    assert ERROR in body, "the report does not quote pixi's error"
    assert GUIDE in body, "the report does not link the packaging guide"

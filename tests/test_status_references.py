# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for ``.github/scripts/check_status_references.py``.

The script asks GitHub about the work each specification status cites. These
tests stand a fixed record of that work in for GitHub, so they need no network,
which is why the resolution lives in a script rather than the unit suite.

"""

from __future__ import annotations

from datetime import date
import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

SCRIPT = (
    Path(__file__).parents[1] / ".github" / "scripts" / "check_status_references.py"
)

REPOSITORY = "bjlittle/geovista"


@pytest.fixture(scope="module")
def script() -> ModuleType:
    """Load the script, which is no importable module."""
    spec = importlib.util.spec_from_file_location("check_status_references", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # a dataclass resolves its annotations through sys.modules
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def record(script):
    """Provide the work GitHub would report, keyed by repository and number."""

    def work(kind: str, state: str, when: str | None = None) -> object:
        return script.Work(kind, state, date.fromisoformat(when) if when else None)

    known = {
        (REPOSITORY, 10): work("pull", "merged", "2026-10-07"),
        (REPOSITORY, 11): work("pull", "merged", "2026-10-09"),
        (REPOSITORY, 12): work("pull", "open"),
        (REPOSITORY, 13): work("pull", "closed", "2026-10-05"),
        (REPOSITORY, 20): work("issue", "open"),
        (REPOSITORY, 21): work("issue", "closed", "2026-10-08"),
        ("scientific-python/lazy-loader", 181): work("issue", "open"),
    }
    return lambda repository, number: known.get((repository, number))


def spec(rows: tuple[str, ...] = (), items: tuple[str, ...] = ()) -> str:
    """Write a specification holding the roadmap rows and open items given."""
    lines = ["# A specification", "", "## 4. Roadmap", ""]
    lines += ["| # | Scope | Status |", "|---|---|---|"]
    lines += [f"| {index} | Work | {row} |" for index, row in enumerate(rows, 1)]
    lines += ["", "## 8. Open items", ""]
    lines += [
        f"{index}. {item} — **A question.** An answer."
        for index, item in enumerate(items, 1)
    ]
    return "\n".join(lines) + "\n"


def check(script, record, text, **kwargs: object) -> list[str]:
    """Check the specification, reporting each fault without its location."""
    found = script.check(Path("x.md"), text, record, **kwargs)
    return [problem.split(": ", maxsplit=1)[1] for problem in found]


def test_landed(script, record):
    """Test a landed row whose pull request merged on its date passes."""
    assert (
        check(script, record, spec(rows=("✅ landed (2026-10-07, {pull}`10`)",))) == []
    )


def test_landed_unmerged(script, record):
    """Test a landed row citing a pull request that has not merged is caught."""
    text = spec(rows=("✅ landed (2026-10-07, {pull}`12`)",))
    assert check(script, record, text) == ["{pull}`12` has not merged"]


def test_landed_issue(script, record):
    """Test a landed row citing an issue rather than a pull request is caught."""
    text = spec(rows=("✅ landed (2026-10-08, {issue}`21`)",))
    assert check(script, record, text) == ["{issue}`21` is not a pull request"]


@pytest.mark.parametrize("written", ["2026-10-06", "2026-10-07", "2026-10-08"])
def test_landed_date_within_a_day(script, record, written):
    """Test a landed date within a day of the merge passes, as UTC may differ."""
    text = spec(rows=(f"✅ landed ({written}, {{pull}}`10`)",))
    assert check(script, record, text) == []


def test_landed_date(script, record):
    """Test a landed date that is not when its work merged is caught."""
    text = spec(rows=("✅ landed (2026-10-01, {pull}`10`)",))
    assert check(script, record, text) == [
        "landed on 2026-10-01, but its last pull request merged on 2026-10-07"
    ]


def test_landed_latest(script, record):
    """Test a landed row's date is that of the last of its pull requests."""
    text = spec(rows=("✅ landed (2026-10-09, {pull}`10`, {pull}`11`)",))
    assert check(script, record, text) == []


def test_missing(script, record):
    """Test a reference to work that does not exist is caught."""
    text = spec(items=("**Resolved** (2026-10-07, {issue}`99`)",))
    assert check(script, record, text) == ["{issue}`99` does not exist"]


@pytest.mark.parametrize(
    ("written", "expected"),
    [
        ("{pull}`20`", "{pull}`20` is an issue"),
        ("{issue}`10`", "{issue}`10` is a pull request"),
    ],
)
def test_role(script, record, written, expected):
    """Test a role naming the wrong kind of work is caught."""
    text = spec(items=(f"**Abandoned** (2026-10-07, {written})",))
    assert check(script, record, text) == [expected]


def test_resolved_open_issue(script, record):
    """Test an item resolved by raising an issue may cite it while it is open."""
    text = spec(items=("**Resolved** (2026-10-06, {issue}`20` and {issue}`21`)",))
    assert check(script, record, text) == []


def test_resolved_link(script, record):
    """Test a link to an issue in another repository is resolved there."""
    link = (
        "[`lazy-loader` issue 181]"
        "(https://github.com/scientific-python/lazy-loader/issues/181)"
    )
    text = spec(items=(f"**Resolved** (2026-10-07, {link})",))
    assert check(script, record, text) == []


def test_resolved_before_merge(script, record):
    """Test a resolved date may come before its pull request merged."""
    text = spec(items=("**Resolved** (2026-10-08, {pull}`11`)",))
    assert check(script, record, text) == []


@pytest.mark.parametrize(
    ("number", "expected"),
    [(12, "{pull}`12` is still open"), (13, "{pull}`13` closed without merging")],
)
def test_resolved_pull(script, record, number, expected):
    """Test an item resolved by a pull request that has not merged is caught."""
    text = spec(items=(f"**Resolved** (2026-10-07, {{pull}}`{number}`)",))
    assert check(script, record, text) == [expected]


@pytest.mark.parametrize(
    "status",
    ["✅ landed (2026-10-01, {pull}`12`)", "**Resolved** (2026-10-01, {pull}`12`)"],
)
def test_current_pull(script, record, status):
    """Test a status may cite the open pull request that writes it."""
    text = spec(rows=(status,)) if "landed" in status else spec(items=(status,))
    assert check(script, record, text, pull=12) == []


def test_current_pull_and_others(script, record):
    """Test citing the open pull request still checks the other references."""
    text = spec(rows=("✅ landed (2026-10-01, {pull}`12`, {pull}`13`)",))
    assert check(script, record, text, pull=12) == ["{pull}`13` has not merged"]


def test_abandoned(script, record):
    """Test an abandoned item need only cite work that exists."""
    text = spec(items=("**Abandoned** (2026-10-05, {pull}`13`)",))
    assert check(script, record, text) == []


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("in progress ({pull}`10`)", "in progress, but {pull}`10` has merged"),
        ("in progress ({pull}`13`)", "in progress, but {pull}`13` has closed"),
        ("not started ({issue}`21`)", "not started, but {issue}`21` has closed"),
    ],
)
def test_drift_row(script, record, status, expected):
    """Test a row whose work has since moved on is reported as drift."""
    text = spec(rows=(status,))
    assert check(script, record, text) == []
    assert check(script, record, text, drift=True) == [expected]


@pytest.mark.parametrize("state", ["Open", "Deferred"])
def test_drift_item(script, record, state):
    """Test an open item whose issue has closed is reported as drift."""
    text = spec(items=(f"**{state}** ({{issue}}`21`)",))
    assert check(script, record, text) == []
    assert check(script, record, text, drift=True) == [
        f"{state}, but {{issue}}`21` has closed"
    ]


@pytest.mark.parametrize(
    "status",
    ["in progress ({pull}`12`)", "not started ({issue}`20`)", "candidate"],
)
def test_no_drift_row(script, record, status):
    """Test a row whose work is still where it says passes."""
    assert check(script, record, spec(rows=(status,)), drift=True) == []


@pytest.mark.parametrize(
    "item", ["**Open** ({issue}`20`)", "**Open** (owned by row 2 of the roadmap)"]
)
def test_no_drift_item(script, record, item):
    """Test an open item still open, or owned by a row, passes."""
    assert check(script, record, spec(items=(item,)), drift=True) == []


@pytest.mark.parametrize(
    "status",
    [
        "not started ({issue}`20`, {pull}`10`)",
        "**Open** ({issue}`20`, {pull}`10`)",
        "**Deferred** ({issue}`20`, {pull}`13`)",
    ],
)
def test_no_drift_from_a_pull_request(script, record, status):
    """Test a status tracked by an open issue has not drifted by a pull request.

    These states are held by an issue, so a merged or closed pull request cited
    beside it as context says nothing about whether the work is still open.

    """
    text = spec(items=(status,)) if "**" in status else spec(rows=(status,))
    assert check(script, record, text, drift=True) == []


def test_drift_issue_beside_a_pull_request(script, record):
    """Test only the closed issue is reported when a pull request sits beside it."""
    text = spec(items=("**Open** ({issue}`21`, {pull}`10`)",))
    assert check(script, record, text, drift=True) == [
        "Open, but {issue}`21` has closed"
    ]


@pytest.mark.parametrize(
    "status",
    [
        "✅ landed (2026-02-30, {pull}`10`)",
        "**Resolved** (2026-02-30, {pull}`10`)",
        "**Abandoned** (2026-02-30, {issue}`20`)",
    ],
)
def test_impossible_date(script, record, status):
    """Test a date no calendar holds is a fault, and the checking carries on."""
    later = "✅ landed (2026-10-07, {pull}`12`)"
    if "**" in status:
        text = spec(rows=(later,), items=(status,))
        expected = ["{pull}`12` has not merged", "2026-02-30 is not a date"]
    else:
        text = spec(rows=(status, later))
        expected = ["2026-02-30 is not a date", "{pull}`12` has not merged"]
    assert check(script, record, text) == expected


def test_main_findings(script, capsys):
    """Test the script exits with one when a status does not hold."""
    assert script.main([], resolve=lambda _repository, _number: None) == 1
    assert "does not exist" in capsys.readouterr().out


def test_main_unexpected(script, capsys):
    """Test the script exits with two, not one, when it cannot finish checking.

    The nightly workflow opens an issue on one, so a failure of the check
    itself must never be mistaken for a finding.

    """

    def broken(_repository: str, _number: int) -> None:
        message = "unexpected"
        raise RuntimeError(message)

    assert script.main([], resolve=broken) == 2
    assert "could not finish checking" in capsys.readouterr().err


def test_specifications(script):
    """Test the borrowed parser finds the references of the real specifications.

    The script reads statuses with the grammar of ``test_spec_conventions.py``,
    so a change there that it no longer follows fails here, without a network.

    """
    found = [
        reference
        for path in script.conventions.specifications()
        for reference in script.cited(path.read_text(encoding="utf-8"))
    ]
    assert len(found) >= 10
    assert (REPOSITORY, 2565, "pull") in {
        (reference.repository, reference.number, reference.role) for reference in found
    }

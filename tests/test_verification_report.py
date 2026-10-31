# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests of the verification report, ".github/scripts/verification_report.py".

The report is a view of the ledger on demand, never a gate (ledger spec §3.8), so
these tests read a small repository of their own, in which each finding the report
can make is planted. This module sits inside the corpus the conventions test
governs, so its fixtures build their section signs and emoji rather than write them,
and cite a ``demo spec`` that no document of this repository declares.

"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

#: The repository root.
REPO = Path(__file__).parents[1]

#: The script under test.
SCRIPT = REPO / ".github" / "scripts" / "verification_report.py"

#: The section sign and the states, built rather than written.
SECTION = "\N{SECTION SIGN}"
ELLIPSIS = "\N{HORIZONTAL ELLIPSIS}"
AGREED = "\N{HANDSHAKE} Agreed"
VERIFIED = "\N{WHITE HEAVY CHECK MARK} verified"
PENDING = "\N{HOURGLASS WITH FLOWING SAND} pending"

#: Provenance a decision in force carries.
AGREEMENT = "2026-01-01, {user}`bjlittle`, {pull}`1`"


@pytest.fixture(scope="module")
def script() -> ModuleType:
    """Load the script, which is no importable module."""
    spec = importlib.util.spec_from_file_location("verification_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write(root: Path, name: str, text: str) -> None:
    """Write a file of the fixture repository."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def entry(number: int, title: str) -> str:
    """Write a decision in force."""
    return f"{number}. **{AGREED}** ({AGREEMENT}) — **{title}** Reasoning.\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Write a repository whose ledger holds every finding the report makes.

    Decision 1 is verified by a test that cites it, and cited by source too.
    Decision 2 is pending, and cited by its own specification and by a plan.
    Decision 3 is in force and cited nowhere. Decision 4 is verified by a test
    that no longer cites it.
    """
    s = SECTION
    write(
        tmp_path,
        "docs/src/developer/specs/2026-01-01-demo-design.md",
        "# Demo Specification\n\n"
        f"- **Citation prefix:** `demo spec {s}{ELLIPSIS}`\n\n"
        "(demo-spec-2)=\n## 2. Decisions\n\n"
        + entry(1, "One.")
        + entry(2, "Two.")
        + f"\n   Its second paragraph keeps {s}2 decision 2, which is no citation.\n"
        + entry(3, "Three.")
        + entry(4, "Four.")
        + f"\n(demo-spec-3)=\n## 3. Design\n\nThe design keeps {s}2 decision 2.\n\n"
        "(demo-spec-4)=\n## 4. Verification\n\n"
        "| Decision | Status | Evidence |\n|---|---|---|\n"
        f"| 1 | {VERIFIED} (2026-01-01, {{pull}}`1`) | `tests/test_demo.py` |\n"
        f"| 2 | {PENDING} | |\n"
        f"| 3 | {PENDING} | |\n"
        f"| 4 | {VERIFIED} (2026-01-01, {{pull}}`1`) | "
        "`tests/test_silent.py`, `tests/test_gone.py` |\n",
    )
    write(
        tmp_path,
        "docs/src/developer/specs/2026-01-02-lone-design.md",
        "# Lone Specification\n\n"
        f"- **Citation prefix:** `lone spec {s}{ELLIPSIS}`\n\n"
        "(lone-spec-2)=\n## 2. Decisions\n\n- **A bullet.** Not yet numbered.\n",
    )
    write(tmp_path, "src/code.py", f"# holds demo spec {s}2 decision 1\n")
    write(
        tmp_path,
        "tests/test_demo.py",
        f'"""Tests.\n\nHolds demo spec {s}2 decision 1.\n"""\n',
    )
    write(tmp_path, "tests/test_silent.py", '"""Tests that cite nothing."""\n')
    write(
        tmp_path,
        "docs/src/developer/plans/2026-01-01-demo.md",
        f"Bare {s}2 decision 1 names no document here.\n"
        f"It plans demo spec {s}2 decision 2.\n",
    )
    return tmp_path


def run(script, repo: Path, capsys, *argv: str) -> tuple[int, str]:
    """Run the report over the fixture repository, returning its exit and output."""
    code = script.main(list(argv), root=repo)
    return code, capsys.readouterr().out


def test_report_lists_each_decision_with_its_state_and_citations(script, repo, capsys):
    """Ledger spec §2 decision 11: each decision, its state, and who cites it."""
    code, out = run(script, repo, capsys)

    assert code == 0
    assert "## demo spec: Demo Specification" in out
    assert "2 of 4 decisions in force verified" in out
    one = out[out.index("### Decision 1: One.") : out.index("### Decision 2: Two.")]
    assert VERIFIED in one
    assert one.index("**source:** `src/code.py:1`") < one.index(
        "**tests:** `tests/test_demo.py:3`"
    )


def test_report_flags_a_silent_test_and_an_uncited_decision(script, repo, capsys):
    """A verified row's test that no longer cites it, and a decision cited nowhere."""
    _, out = run(script, repo, capsys)
    findings = out[out.index("## Findings") :]

    assert (
        f"demo spec {SECTION}2 decision 4: `tests/test_silent.py` no longer" in findings
    )
    assert f"demo spec {SECTION}2 decision 3 is in force and cited nowhere" in findings
    assert (
        f"demo spec {SECTION}2 decision 4: `tests/test_gone.py` is missing" in findings
    )
    assert f"demo spec {SECTION}2 decision 1 " not in findings


def test_a_plan_citing_bare_is_counted_against_nothing(script, repo, capsys):
    """A plan owns no sections, so its bare citation names no decision."""
    _, out = run(script, repo, capsys)
    one = out[out.index("### Decision 1: One.") : out.index("### Decision 2: Two.")]
    two = out[out.index("### Decision 2: Two.") : out.index("### Decision 3: Three.")]

    assert "plans" not in one
    assert "**plans:** `docs/src/developer/plans/2026-01-01-demo.md:2`" in two


def test_a_specification_citing_its_own_decision_counts(script, repo, capsys):
    """A citation elsewhere in the specification counts; the entry itself does not."""
    _, out = run(script, repo, capsys)
    two = out[out.index("### Decision 2: Two.") : out.index("### Decision 3: Three.")]
    spec = "docs/src/developer/specs/2026-01-01-demo-design.md"

    assert f"**specifications:** `{spec}:18`" in two
    assert f"`{spec}:11`" not in two


def test_an_unknown_prefix_exits_two(script, repo, capsys):
    """A prefix that names no specification is an error, naming those that exist."""
    code = script.main(["nosuch"], root=repo)
    err = capsys.readouterr().err

    assert code == 2
    assert "demo" in err
    assert "lone" in err


def test_bulleted_decisions_are_reported_without_a_crash(script, repo, capsys):
    """A specification not yet in the ledger is reported, with no decisions to list."""
    code, out = run(script, repo, capsys, "lone")

    assert code == 0
    assert "## lone spec: Lone Specification" in out
    assert "No numbered decisions." in out


def test_the_report_appends_to_the_job_summary(script, repo, capsys, monkeypatch):
    """In CI the same Markdown is added to the job summary, after what is there."""
    summary = repo / "summary.md"
    summary.write_text("before\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    _, out = run(script, repo, capsys, "demo")

    assert summary.read_text(encoding="utf-8") == "before\n" + out


def test_main_reports_one_specification_by_prefix(script, repo, capsys):
    """A prefix narrows the report to its specification."""
    code, out = run(script, repo, capsys, "demo")

    assert code == 0
    assert "## demo spec" in out
    assert "## lone spec" not in out


def test_the_report_reads_this_repository(script, capsys):
    """The report reads the real collection, and finds the ledger specification."""
    code, out = run(script, REPO, capsys, "ledger")

    assert code == 0
    assert "## ledger spec: Decision Ledger Specification" in out


def test_code_is_source_wherever_it_sits(script, tmp_path):
    """A documentation extension is code, so its citations are listed as source."""
    root = tmp_path

    assert script.group(root / "docs/src/_ext/ext.py", root) == "source"
    assert script.group(root / ".github/workflows/ci.yml", root) == "source"
    assert script.group(root / "docs/src/page.rst", root) == "documentation"
    spec = root / "docs/src/developer/specs/2026-01-01-demo-design.md"
    index = root / "docs/src/developer/specs/index.rst"
    assert script.group(spec, root, {spec}) == "specifications"
    assert script.group(index, root, {spec}) == "documentation"
    assert script.group(root / "tests/docs/test_page.py", root) == "tests"


def test_a_verified_or_signed_off_row_with_no_evidence_is_flagged(script, repo, capsys):
    """A row that shows a decision delivered, with nothing to show it by, is flagged."""
    spec = repo / "docs/src/developer/specs/2026-01-01-demo-design.md"
    text = spec.read_text(encoding="utf-8")
    signed = "\N{WRITING HAND}\N{VARIATION SELECTOR-16} signed off"
    text = text.replace("`tests/test_demo.py` |", " |").replace(
        f"| 2 | {PENDING} | |",
        f"| 2 | {signed} (2026-01-01, {{user}}`bjlittle`, {{pull}}`1`) | |",
    )
    spec.write_text(text, encoding="utf-8")

    _, out = run(script, repo, capsys)
    findings = out[out.index("## Findings") :]

    assert f"demo spec {SECTION}2 decision 1 is verified by nothing" in findings
    assert (
        f"demo spec {SECTION}2 decision 2 is signed off with nothing said" in findings
    )


def test_unreadable_evidence_is_a_finding_not_an_abort(script, repo, capsys):
    """A test file that cannot be read is reported, and the report still prints."""
    (repo / "tests/test_demo.py").write_bytes(b'"""\xff not UTF-8."""\n')

    code, out = run(script, repo, capsys)

    assert code == 0
    assert "## Findings" in out
    assert (
        f"demo spec {SECTION}2 decision 1: `tests/test_demo.py` cannot be read" in out
    )


def test_a_plan_that_is_not_utf8_is_skipped(script, repo, capsys):
    """A plan the report cannot decode is passed over, as the corpus passes one over."""
    (repo / "docs/src/developer/plans/binary.md").write_bytes(b"\xff\xfe not UTF-8\n")

    code, out = run(script, repo, capsys)

    assert code == 0
    assert "## demo spec" in out


def test_state_lines_read_as_github_markdown(script, repo, capsys):
    """A job summary renders no MyST role, so a status reads as GitHub Markdown."""
    _, out = run(script, repo, capsys)
    one = out[out.index("### Decision 1: One.") : out.index("### Decision 2: Two.")]

    assert f"{VERIFIED} (2026-01-01, #1)" in one
    assert "{pull}" not in out


def test_a_page_is_listed_as_documentation(script, repo, capsys):
    """A citation from a documentation page is listed in its own group."""
    write(repo, "docs/src/page.rst", f"See demo spec {SECTION}2 decision 1.\n")

    _, out = run(script, repo, capsys)
    one = out[out.index("### Decision 1: One.") : out.index("### Decision 2: Two.")]

    assert "- **documentation:** `docs/src/page.rst:1`" in one


def test_a_line_citing_a_decision_twice_is_listed_once(script, repo, capsys):
    """One line is one place, however often it names the decision."""
    s = SECTION
    write(
        repo,
        "src/twice.py",
        f"# demo spec {s}2 decision 1, demo spec {s}2 decision 1\n",
    )

    _, out = run(script, repo, capsys)

    assert out.count("`src/twice.py:1`") == 1

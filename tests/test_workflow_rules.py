# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that the rules on the workflow page keep the form agents and people rely on.

The "How We Work" page in the developer guide holds the rules ``geovista`` is
developed by, for people and AI agents alike, and the root "AGENTS.md" imports
it, so that every agent session reads it. Its sections are numbered, each rule is
numbered within its section and marked with the audience it binds, and each opens
with its status, saying when, by whom and where it was agreed or retired.

These tests hold the page to that form, and "AGENTS.md" to its import. The
reader, "workflow_rules.py", is shared with the renumber guard, which compares
the page with its base branch on each pull request, so that a rule is never
deleted, moved or renumbered. Its comparison is tested here too.

"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

#: The section of the repository checks page that documents this check.
CHECK = "workflow-rules"

#: The repository root.
ROOT = Path(__file__).parents[1]
#: The reader of the page, which is no importable module.
SCRIPT = ROOT / ".github" / "scripts" / "workflow_rules.py"
#: The file every agent session reads, which imports the page.
AGENTS = ROOT / "AGENTS.md"


@pytest.fixture(scope="module")
def rules() -> ModuleType:
    """Load the reader, reusing a copy the renumber guard already registered."""
    registered = sys.modules.get("workflow_rules")
    if registered is not None and Path(registered.__file__).resolve() == SCRIPT:
        return registered
    spec = importlib.util.spec_from_file_location("workflow_rules", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_the_page_holds_its_rules_in_form(rules):
    """The workflow page holds its rules in the form of workflow rule 7.2."""
    text = (ROOT / rules.PAGE).read_text(encoding="utf-8")
    faults = rules.faults(text)
    assert not faults, f"{rules.PAGE}:\n" + "\n".join(faults)


def test_agents_md_imports_the_page(rules):
    """The root AGENTS.md imports the page, so every agent session reads it."""
    lines = AGENTS.read_text(encoding="utf-8").split("\n")
    expected = f"@{rules.PAGE.as_posix()}"
    assert expected in (line.strip() for line in lines), (
        f"AGENTS.md must import the workflow page on a line of its own, as "
        f"{expected!r}, so that every agent session reads it."
    )


AGREED = "🤝 Agreed (2026-11-01, {user}`someone`, {pull}`2000`)"
RETIRED = (
    "🗄️ Retired (2026-12-01, {user}`someone`, {pull}`3000`; agreed 2026-11-01, "
    "{pull}`2000`). It no longer holds: replaced by workflow rule 1.3."
)


def rule(key: str, status: str = AGREED, mark: str = "👥", title: str = "A Rule"):
    """Return a rule, as the page writes one."""
    return f"### {key} {mark} {title}\n\n{status}\n\nIts text."


def page(*sections: tuple[str, list[str]]) -> str:
    """Return a page of numbered sections, each a title and its rules."""
    parts = ["# Title", "Its introduction."]
    for number, (title, held) in enumerate(sections, start=1):
        parts.append(f"## {number}. {title}")
        parts.extend(held)
    return "\n\n".join(parts) + "\n"


GOOD = page(("First", [rule("1.1"), rule("1.2", mark="🤖")]), ("Second", [rule("2.1")]))


def test_a_page_in_form_passes(rules):
    """A page of numbered sections and rules, each with a status, passes."""
    assert rules.faults(GOOD) == []


def test_the_rules_are_read_with_their_status(rules):
    """Each rule is read with its number, mark, title and status."""
    _, read, faults = rules.read(GOOD)
    assert faults == []
    assert [(r.key, r.mark, r.title) for r in read] == [
        ("1.1", "👥", "A Rule"),
        ("1.2", "🤖", "A Rule"),
        ("2.1", "👥", "A Rule"),
    ]
    assert read[0].status == AGREED
    assert read[0].agreement == ("2026-11-01", "{pull}`2000`")
    assert not read[0].retired


def test_a_retired_rule_keeps_its_agreement(rules):
    """A retired rule is read as retired, with the agreement it was retired from."""
    _, (read,), _ = rules.read(page(("First", [rule("1.1", RETIRED)])))
    assert read.retired
    assert read.agreement == ("2026-11-01", "{pull}`2000`")


def test_a_retired_mark_may_lack_its_variation_selector(rules):
    """The retired mark is read with or without its variation selector."""
    status = RETIRED.replace("\N{VARIATION SELECTOR-16}", "")
    assert rules.faults(page(("First", [rule("1.1", status)]))) == []


def test_a_status_may_wrap_over_lines(rules):
    """A long status is one paragraph, however it is wrapped."""
    status = RETIRED.replace("; agreed", ";\nagreed")
    assert rules.faults(page(("First", [rule("1.1", status)]))) == []


def test_a_heading_in_a_code_block_is_no_rule(rules):
    """A rule's heading shown as an example, in a code block, is not read."""
    text = GOOD + "\n```markdown\n### 9.9 👥 An Example\n```\n"
    _, read, faults = rules.read(text)
    assert faults == []
    assert [r.key for r in read] == ["1.1", "1.2", "2.1"]


@pytest.mark.parametrize(
    "heading",
    [
        pytest.param("### A Rule With No Number", id="no-number"),
        pytest.param("### 1.2 A Rule With No Mark", id="no-mark"),
        pytest.param("### 1.2 🤝 A Rule Marked as Agreed", id="wrong-mark"),
        pytest.param("### 2 👥 A Rule With No Section", id="no-section"),
        pytest.param("### 1.02 👥 A Padded Number", id="padded"),
    ],
)
def test_a_heading_that_is_no_rule_fails(rules, heading):
    """A third-level heading that is not a numbered, marked rule fails."""
    text = GOOD.replace("### 1.2 🤖 A Rule", heading)
    faults = rules.faults(text)
    assert any("is not a rule" in fault for fault in faults)


def test_a_section_without_its_number_fails(rules):
    """A second-level heading must be a numbered section."""
    faults = rules.faults(GOOD.replace("## 2. Second", "## Second"))
    assert any("is not a section" in fault for fault in faults)


def test_sections_are_numbered_in_order(rules):
    """A section numbered out of its place fails."""
    text = GOOD.replace("## 2. Second", "## 3. Second").replace("2.1 👥", "3.1 👥")
    assert rules.faults(text) == [
        (
            "line 19: section 3 should be section 2. A new section goes at the end of "
            "the page."
        ),
    ]


def test_a_rule_numbered_for_another_section_fails(rules):
    """A rule's number begins with the number of the section it sits in."""
    faults = rules.faults(GOOD.replace("### 2.1", "### 1.3"))
    assert faults == ["line 21: rule 1.3 sits in section 2, so its number begins '2.'."]


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        pytest.param(("1.1", "1.3"), "rule 1.3 should be rule 1.2", id="gap"),
        pytest.param(("1.2", "1.1"), "rule 1.2 should be rule 1.1", id="order"),
        pytest.param(("1.1", "1.1"), "rule 1.1 should be rule 1.2", id="repeat"),
    ],
)
def test_rules_are_numbered_in_order_within_their_section(rules, keys, expected):
    """A gap, a rule out of order or a number repeated fails."""
    faults = rules.faults(page(("First", [rule(key) for key in keys])))
    assert any(expected in fault for fault in faults)


def test_a_rule_under_no_section_fails(rules):
    """A rule above the first section belongs to none."""
    text = "# Title\n\n" + rule("1.1") + "\n\n## 1. First\n"
    assert rules.faults(text) == ["line 3: rule 1.1 is under no section."]


@pytest.mark.parametrize(
    "status",
    [
        pytest.param("Its text, agreed somewhere.", id="none"),
        pytest.param("🤝 Agreed (2026-11-01, {pull}`2000`)", id="no-user"),
        pytest.param("🤝 Agreed (2026-11-01, {user}`a`, #2000)", id="bare-number"),
        pytest.param("🤝 Agreed (1 Nov 2026, {user}`a`, {pull}`2000`)", id="date"),
        pytest.param(AGREED + " Then more.", id="trailing-text"),
        pytest.param(
            "🗄️ Retired (2026-12-01, {user}`a`, {pull}`3000`). Why.", id="no-agreed"
        ),
    ],
)
def test_a_rule_without_a_status_fails(rules, status):
    """A rule must open with an agreed or a retired status, in full."""
    faults = rules.faults(page(("First", [rule("1.1", status)])))
    assert len(faults) == 1
    assert "opens with no status" in faults[0]


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("https://github.com/owner/repo/issues/181", id="issue"),
        pytest.param("https://github.com/owner/repo/pull/7", id="pull"),
    ],
)
def test_a_status_may_cite_another_projects_tracker(rules, url):
    """An issue or a pull request of another project on GitHub is a source."""
    status = AGREED.replace("{pull}`2000`", url)
    assert rules.faults(page(("First", [rule("1.1", status)]))) == []


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("https://github.com/owner/repo/", id="repository"),
        pytest.param("https://github.com/owner/repo/blob/main/README.md", id="file"),
        pytest.param("https://github.com/owner/repo/issues", id="no-number"),
        pytest.param("https://github.com/owner/repo/issues/181/files", id="beyond"),
        pytest.param("https://example.com/owner/repo/issues/181", id="not-github"),
    ],
)
def test_a_status_citing_no_tracker_entry_fails(rules, url):
    """A link that names no issue or pull request is no source (Codex, #2897)."""
    status = AGREED.replace("{pull}`2000`", url)
    faults = rules.faults(page(("First", [rule("1.1", status)])))
    assert len(faults) == 1
    assert "opens with no status" in faults[0]


def test_a_page_without_rules_fails(rules):
    """A page with no rules at all fails."""
    assert rules.faults("# Title\n\n## 1. First\n") == ["the page holds no rules."]


def test_a_rule_added_at_the_end_of_its_section_is_held(rules):
    """Adding rules and sections, and correcting a title, keeps every number."""
    title = "Mark a Roadmap Row First and Last"
    before = page(("First", [rule("1.1", title=title)]))
    after = page(
        ("First", [rule("1.1", title="Mark a Roadmap Row First, and Then Last")]),
        ("Second", [rule("2.1", AGREED.replace("2000", "2001"))]),
    )
    assert rules.held(before, after) == []


def test_retiring_a_rule_in_place_is_held(rules):
    """A rule retired in place keeps its number and its agreement."""
    after = GOOD.replace(
        f"### 2.1 👥 A Rule\n\n{AGREED}", f"### 2.1 👥 A Rule\n\n{RETIRED}"
    )
    assert after != GOOD
    assert rules.held(GOOD, after) == []


def test_a_deleted_rule_fails(rules):
    """A rule deleted, even the last, fails though the numbers still run (Codex)."""
    after = page(("First", [rule("1.1"), rule("1.2", mark="🤖")]))
    assert rules.faults(after) == []
    assert rules.held(GOOD, after) == [
        (
            "rule 2.1, 'A Rule', was removed. A rule is never deleted or moved: "
            "restore it, and retire it in place if it no longer holds."
        ),
    ]


def test_swapped_numbers_fail(rules):
    """Two rules swapping numbers, keeping their bodies, fail (Codex, #2897)."""
    first = rule("1.1", title="First")
    second = rule("1.2", AGREED.replace("2000", "2001"), title="Second")
    before = page(("First", [first, second]))
    after = page(("First", [second.replace("1.2", "1.1"), first.replace("1.1", "1.2")]))
    assert rules.faults(after) == []
    problems = rules.held(before, after)
    assert len(problems) == 2
    assert problems[0].startswith(
        "rule 1.1 was the rule agreed 2026-11-01 in {pull}`2000`, 'First', and now "
        "names one agreed 2026-11-01 in {pull}`2001`."
    )


def test_a_rule_moved_to_another_section_fails(rules):
    """A rule moved between sections leaves its number behind."""
    after = page(
        ("First", [rule("1.1")]),
        ("Second", [rule("2.1"), rule("2.2", mark="🤖")]),
    )
    assert rules.held(GOOD, after) == [
        (
            "rule 1.2, 'A Rule', was removed. A rule is never deleted or moved: "
            "restore it, and retire it in place if it no longer holds."
        ),
    ]


def test_a_retired_rule_stays_retired(rules):
    """A retired rule brought back fails: a new rule takes its place instead."""
    before = page(("First", [rule("1.1", RETIRED)]))
    assert rules.held(before, page(("First", [rule("1.1")]))) == [
        (
            "rule 1.1, 'A Rule', was retired, and stays retired. Add a new rule at the "
            "end of its section instead."
        ),
    ]


def test_rules_sharing_an_agreement_swapped_fail(rules):
    """Rules agreed in one pull request are told apart by their titles."""
    first = rule("1.1", title="Keep Specifications in the Developer Guide")
    second = rule("1.2", title="Ship a Plan With Its Implementation")
    before = page(("First", [first, second]))
    after = page(("First", [second.replace("1.2", "1.1"), first.replace("1.1", "1.2")]))
    problems = rules.held(before, after)
    assert len(problems) == 2
    assert problems[0] == (
        "rule 1.1 was 'Keep Specifications in the Developer Guide', and is now "
        "'Ship a Plan With Its Implementation', which reads as another rule. A rule "
        "keeps its number, and its title is only ever corrected: restore it, and "
        "add a new rule at the end of its section."
    )

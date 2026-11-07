# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that the rules on the workflow page keep the form agents and people rely on.

The "How We Work" page in the developer guide holds the rules ``geovista`` is
developed by, for people and AI agents alike, and the root "AGENTS.md" imports
it, so that every agent session reads it. Each rule is a heading of its own,
numbered once and for good, marked with the audience it binds, and gives where
it was agreed.

These tests read the page and "AGENTS.md" as text. They hold each rule to its
form, its numbers to a run from 1 with no gap and no repeat, and "AGENTS.md" to
its import of the page.

"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from markdown_it import MarkdownIt
import pytest

#: The section of the repository checks page that documents this check.
CHECK = "workflow-rules"

#: The repository root.
ROOT = Path(__file__).parents[1]
#: The page holding the rules, relative to the root.
PAGE = Path("docs") / "src" / "developer" / "workflow.md"
#: The file every agent session reads, which imports the page.
AGENTS = ROOT / "AGENTS.md"

#: The marks of a rule's audience: everyone, people only, and AI agents only.
AUDIENCES = ("👥", "👩", "🤖")
#: The mark of a rule that no longer holds, which keeps its number.
RETIRED = "🗄️"

#: The heading level of a rule. Every heading at that level must be one.
LEVEL = "h3"
#: The heading levels above a rule's, which end the body of the rule above them.
SECTIONS = ("h1", "h2")
#: A rule's heading: its number, its mark and its title. The retired mark is read
#: with or without the variation selector that makes it an emoji, which an editor
#: may drop.
RULE = re.compile(
    r"^(?P<number>[1-9][0-9]*)\. (?P<mark>{}|{}\uFE0F?) (?P<title>\S.*)$".format(
        "|".join(re.escape(mark) for mark in AUDIENCES),
        re.escape(RETIRED.removesuffix("\ufe0f")),
    )
)
#: Where a rule was agreed: a pull request or an issue, a design specification's
#: citation, or a link to another project's tracker on GitHub.
SOURCE = re.compile(
    r"\{(?:pull|issue)\}`\d+`|\bspec §\d|https://github\.com/[\w.-]+/[\w.-]+/"
)
#: A retired rule's record: the word, and the date it was retired.
RETIREMENT = re.compile(r"\bRetired\b.*?\b\d{4}-\d{2}-\d{2}\b", flags=re.DOTALL)


@dataclass(frozen=True)
class Rule:
    """One rule of the workflow page.

    Attributes
    ----------
    number : int
        Its number, which it keeps for good.
    mark : str
        The mark of its audience, or of its retirement.
    title : str
        Its title.
    body : str
        The text under its heading, up to the next heading.
    line : int
        The line its heading is written on.

    """

    number: int
    mark: str
    title: str
    body: str
    line: int


def _rules(text: str) -> tuple[list[Rule], list[str]]:
    """Return the rules a page holds, and a fault for each heading that is no rule.

    The page is parsed as CommonMark, so a heading inside a code block is no
    heading, and a rule's body runs from its heading to the next heading of its
    level or above.

    Parameters
    ----------
    text : str
        The page.

    Returns
    -------
    tuple of (list of Rule, list of str)
        The rules in the order written, and the faults.

    """
    lines = text.split("\n")
    tokens = MarkdownIt("commonmark").parse(text)
    headings = [
        (token.tag, token.map, tokens[index + 1].content)
        for index, token in enumerate(tokens)
        if token.type == "heading_open"
        and token.tag in (LEVEL, *SECTIONS)
        and token.map is not None
    ]

    rules: list[Rule] = []
    faults: list[str] = []
    for index, (tag, (start, end), content) in enumerate(headings):
        if tag != LEVEL:
            continue
        line = start + 1
        match = RULE.match(content)
        if match is None:
            faults.append(
                f"line {line}: '### {content}' is not a rule. A rule's heading is "
                f"'### <number>. <mark> <Title>', its mark one of "
                f"{' '.join(AUDIENCES)}, or {RETIRED} once retired."
            )
            continue
        stop = headings[index + 1][1][0] if index + 1 < len(headings) else len(lines)
        rules.append(
            Rule(
                number=int(match["number"]),
                mark=match["mark"].removesuffix("\ufe0f"),
                title=match["title"],
                body="\n".join(lines[end:stop]).strip(),
                line=line,
            )
        )
    return rules, faults


def _numbering(rules: list[Rule]) -> list[str]:
    """Return a fault for each number repeated, and for each missing from the run."""
    faults = []
    seen: dict[int, Rule] = {}
    for rule in rules:
        if rule.number in seen:
            faults.append(
                f"line {rule.line}: rule {rule.number} is numbered again, after "
                f"line {seen[rule.number].line}. A new rule takes the next free "
                "number."
            )
        seen.setdefault(rule.number, rule)

    expected = set(range(1, max(seen, default=0) + 1))
    faults.extend(
        f"rule {number} is missing. A rule that no longer holds is retired in "
        f"place, marked {RETIRED}, never deleted."
        for number in sorted(expected - seen.keys())
    )
    return faults


def _record(rule: Rule) -> str | None:
    """Return the fault in what a rule records of its source, or ``None``."""
    if rule.mark == RETIRED.removesuffix("\ufe0f"):
        if RETIREMENT.search(rule.body) is None:
            return (
                f"line {rule.line}: retired rule {rule.number} must say "
                "'Retired', with the date it was."
            )
        return None
    if SOURCE.search(rule.body) is None:
        return (
            f"line {rule.line}: rule {rule.number} names no source. Cite the "
            "pull request or issue where it was agreed, or a specification's "
            "decision."
        )
    return None


def _faults(text: str) -> list[str]:
    """Return every fault of a workflow page."""
    rules, faults = _rules(text)
    if not rules:
        return [*faults, "the page holds no rules."]
    faults.extend(_numbering(rules))
    faults.extend(fault for rule in rules if (fault := _record(rule)) is not None)
    return faults


def test_the_page_holds_its_rules_in_form():
    """The workflow page holds its rules in the form of workflow rules 25 and 26."""
    text = (ROOT / PAGE).read_text(encoding="utf-8")
    faults = _faults(text)
    assert not faults, f"{PAGE}:\n" + "\n".join(faults)


def test_agents_md_imports_the_page():
    """The root AGENTS.md imports the page, so every agent session reads it."""
    lines = AGENTS.read_text(encoding="utf-8").split("\n")
    expected = f"@{PAGE.as_posix()}"
    assert expected in (line.strip() for line in lines), (
        f"AGENTS.md must import the workflow page on a line of its own, as "
        f"{expected!r}, so that every agent session reads it."
    )


def _page(*rules: str) -> str:
    """Return a page holding the given rules, under one section."""
    return "# Title\n\n## Section\n\n" + "\n\n".join(rules) + "\n"


GOOD = "### 1. 👥 A Rule\n\nIts text ({pull}`2000`)."


def test_a_page_in_form_passes():
    """A rule of each audience, each with a source of each kind, passes."""
    text = _page(
        GOOD,
        "### 2. 👩 Another\n\nText (ledger spec §2 decision 7).",
        "### 3. 🤖 A Third\n\nText, as https://github.com/owner/repo/issues/1 did.",
    )
    assert _faults(text) == []


def test_the_rules_are_read_with_their_bodies():
    """Each rule is read with its number, mark, title and the text under it."""
    text = _page(GOOD, "### 2. 🤖 Two\n\nLine one.\nLine two ({issue}`3`).")
    rules, faults = _rules(text)
    assert faults == []
    assert [(r.number, r.mark, r.title) for r in rules] == [
        (1, "👥", "A Rule"),
        (2, "🤖", "Two"),
    ]
    assert rules[1].body == "Line one.\nLine two ({issue}`3`)."


def test_a_section_heading_ends_a_rule():
    """A section heading ends the body of the rule above it."""
    text = GOOD + "\n\n## Next\n\nNot the rule's ({pull}`1`).\n"
    (rule,), _ = _rules("# T\n\n" + text)
    assert rule.body == "Its text ({pull}`2000`)."


def test_a_heading_in_a_code_block_is_no_rule():
    """A rule's heading shown as an example, in a code block, is not read."""
    text = _page(GOOD + "\n\n```markdown\n### 9. 👥 An Example\n```")
    rules, faults = _rules(text)
    assert faults == []
    assert [rule.number for rule in rules] == [1]
    assert "An Example" in rules[0].body


@pytest.mark.parametrize(
    "heading",
    [
        pytest.param("### A Rule With No Number", id="no-number"),
        pytest.param("### 2. A Rule With No Mark", id="no-mark"),
        pytest.param("### 2. 🤝 A Rule Marked as Agreed", id="wrong-mark"),
        pytest.param("### 02. 👥 A Padded Number", id="padded"),
    ],
)
def test_a_heading_that_is_no_rule_fails(heading):
    """A third-level heading that is not a numbered, marked rule fails."""
    faults = _faults(_page(GOOD, f"{heading}\n\nText ({{pull}}`1`)."))
    assert len(faults) == 1
    assert "is not a rule" in faults[0]


def test_a_repeated_number_fails():
    """A number given to two rules fails, naming both lines."""
    faults = _faults(_page(GOOD, "### 1. 🤖 Again\n\nText ({pull}`1`)."))
    expected = (
        "line 9: rule 1 is numbered again, after line 5. A new rule takes the "
        "next free number."
    )
    assert faults == [expected]


def test_a_missing_number_fails():
    """A gap in the numbers, left by a deleted rule, fails."""
    faults = _faults(_page(GOOD, "### 3. 🤖 Three\n\nText ({pull}`1`)."))
    assert len(faults) == 1
    assert faults[0].startswith("rule 2 is missing.")


def test_numbers_need_not_follow_the_order_of_the_page():
    """A new rule in an earlier section keeps the next free number."""
    text = _page(
        "### 2. 👥 Two\n\nText ({pull}`1`).",
        GOOD,
    )
    assert _faults(text) == []


def test_a_rule_without_a_source_fails():
    """A rule naming nowhere it was agreed fails."""
    faults = _faults(_page("### 1. 👥 A Rule\n\nIts text, agreed somewhere."))
    assert len(faults) == 1
    assert "names no source" in faults[0]


@pytest.mark.parametrize(
    "body",
    [
        pytest.param("Text (#2000).", id="bare-number"),
        pytest.param("Text (spec 2).", id="no-section-sign"),
        pytest.param("Text (https://example.com/a/b/).", id="not-github"),
    ],
)
def test_a_source_that_names_nothing_checkable_fails(body):
    """A bare number, a section without its sign or a link off GitHub is no source."""
    faults = _faults(_page(f"### 1. 👥 A Rule\n\n{body}"))
    assert len(faults) == 1
    assert "names no source" in faults[0]


def test_a_retired_rule_keeps_its_number():
    """A retired rule stays in place, and its replacement takes a new number."""
    text = _page(
        GOOD,
        (
            "### 2. 🗄️ An Old Rule\n\nRetired (2026-12-01, {pull}`3000`): replaced "
            "by rule 3."
        ),
        "### 3. 👥 Its Replacement\n\nText ({pull}`3000`).",
    )
    assert _faults(text) == []


def test_a_retired_mark_may_lack_its_variation_selector():
    """The retired mark is read with or without its variation selector."""
    text = _page(
        GOOD, "### 2. \N{FILE CABINET} Old\n\nRetired (2026-12-01, {pull}`1`)."
    )
    assert _faults(text) == []


def test_a_retired_rule_must_say_when():
    """A retired rule that does not say when it was retired fails."""
    faults = _faults(_page(GOOD, "### 2. 🗄️ An Old Rule\n\nNo longer holds."))
    assert faults == [
        "line 9: retired rule 2 must say 'Retired', with the date it was."
    ]


def test_a_page_without_rules_fails():
    """A page with no rules at all fails."""
    assert _faults("# Title\n\nNothing here.\n") == ["the page holds no rules."]

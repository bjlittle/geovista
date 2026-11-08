# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Read the rules of the workflow page, and hold them to their form and their numbers.

The "How We Work" page of the developer guide holds the rules ``geovista`` is
developed by, for people and AI agents alike. Its sections are numbered, and each
rule is a heading numbered within its section, as ``### 2.4 👥 Title``, so that
``workflow rule 2.4`` always names the same rule. The first paragraph under a rule
is its status: ``🤝 Agreed`` with the date, who agreed it and where, or
``🗄️ Retired`` with the same for its retirement and then for its agreement.

Rules and sections are only ever added, at the end of their section or of the
page, and a rule that no longer holds is retired in place. Within one revision,
:func:`faults` holds the page to its form. Between two, :func:`held` holds each
rule the earlier one had to its number: one that went, or whose number now names
a different agreement, fails. The repository checks test reads the first and the
renumber guard the second, on each pull request.

"""

from __future__ import annotations

from dataclasses import dataclass
import difflib
from pathlib import Path
import re

from markdown_it import MarkdownIt

#: The page, relative to the repository root.
PAGE = Path("docs") / "src" / "developer" / "workflow.md"

#: How alike a rule's title must stay to the one it had, for a correction and not
#: another rule, as the renumber guard pairs a renamed section: two rules agreed
#: in one pull request share an agreement, and only their titles tell them apart.
LIKENESS = 0.6

#: The marks of a rule's audience: everyone, people only, and AI agents only.
AUDIENCES = ("👥", "👩", "🤖")
#: The variation selector that makes a character an emoji, which an editor may drop.
VS16 = "\N{VARIATION SELECTOR-16}"

#: A section's heading, its number and title.
SECTION = re.compile(r"^(?P<number>[1-9][0-9]*)\. (?P<title>\S.*)$")
#: A rule's heading: its section, its number within it, its audience and title.
RULE = re.compile(
    r"^(?P<section>[1-9][0-9]*)\.(?P<number>[1-9][0-9]*) "
    r"(?P<mark>{}) (?P<title>\S.*)$".format("|".join(map(re.escape, AUDIENCES)))
)

#: A date, as ISO 8601 writes it.
DATE = r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
#: Who agreed or retired a rule.
USER = r"\{user\}`[\w-]+`"
#: Where a rule was agreed: a pull request or an issue of this repository, or an
#: issue or a pull request of another project on GitHub, ending at its number.
REF = (
    r"\{(?:pull|issue)\}`[0-9]+`"
    r"|https://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull)/[0-9]+(?![\w/.-])"
)
#: An agreed rule's status, the whole of its paragraph.
AGREED = re.compile(rf"🤝 Agreed \((?P<date>{DATE}), {USER}, (?P<ref>{REF})\)")
#: A retired rule's status, which its reason follows in the same paragraph.
RETIRED = re.compile(
    rf"🗄{VS16}? Retired \({DATE}, {USER}, \{{pull\}}`[0-9]+`; "
    rf"agreed (?P<date>{DATE}), (?P<ref>{REF})\)(?=$|[.:] )"
)


@dataclass(frozen=True)
class Rule:
    """One rule of the workflow page.

    Attributes
    ----------
    section : int
        The number of the section its heading names.
    number : int
        Its number within that section.
    mark : str
        The mark of its audience.
    title : str
        Its title.
    status : str
        Its status paragraph, its lines joined by single spaces.
    line : int
        The line its heading is written on.

    """

    section: int
    number: int
    mark: str
    title: str
    status: str
    line: int

    @property
    def key(self) -> str:
        """The number a citation names it by, as ``2.4``."""
        return f"{self.section}.{self.number}"

    @property
    def retired(self) -> bool:
        """Whether the rule no longer holds."""
        return RETIRED.match(self.status) is not None

    @property
    def agreement(self) -> tuple[str, str] | None:
        """When and where the rule was agreed, or ``None`` if its status says not."""
        match = AGREED.fullmatch(self.status) or RETIRED.match(self.status)
        return None if match is None else (match["date"], match["ref"])


def _status(lines: list[str], start: int, stop: int) -> str:
    """Return the first paragraph between two lines, its lines joined by spaces."""
    paragraph: list[str] = []
    for line in lines[start:stop]:
        if line.strip():
            paragraph.append(line.strip())
        elif paragraph:
            break
    return " ".join(paragraph)


def read(text: str) -> tuple[list[tuple[int, int, str]], list[Rule], list[str]]:
    """Return the sections and rules of a page, and a fault for each malformed heading.

    The page is parsed as CommonMark, so a heading inside a code block is no
    heading.

    Parameters
    ----------
    text : str
        The page.

    Returns
    -------
    tuple
        The sections, each as its number, the line of its heading and its title;
        the rules; and the faults, all in the order written.

    """
    lines = text.split("\n")
    tokens = MarkdownIt("commonmark").parse(text)
    headings = [
        (token.tag, token.map, tokens[index + 1].content)
        for index, token in enumerate(tokens)
        if token.type == "heading_open"
        and token.tag in ("h1", "h2", "h3")
        and token.map is not None
    ]

    sections: list[tuple[int, int, str]] = []
    rules: list[Rule] = []
    faults: list[str] = []
    for index, (tag, (start, end), content) in enumerate(headings):
        line = start + 1
        if tag == "h2":
            if (section := SECTION.match(content)) is None:
                faults.append(
                    f"line {line}: '## {content}' is not a section. A section's "
                    "heading is '## <number>. <Title>'."
                )
            else:
                sections.append((int(section["number"]), line, section["title"]))
        elif tag == "h3":
            if (rule := RULE.match(content)) is None:
                faults.append(
                    f"line {line}: '### {content}' is not a rule. A rule's heading "
                    f"is '### <section>.<number> <mark> <Title>', its mark one of "
                    f"{' '.join(AUDIENCES)}."
                )
                continue
            stop = headings[index + 1][1][0] if index + 1 < len(headings) else None
            rules.append(
                Rule(
                    section=int(rule["section"]),
                    number=int(rule["number"]),
                    mark=rule["mark"],
                    title=rule["title"],
                    status=_status(lines, end, stop or len(lines)),
                    line=line,
                )
            )
    return sections, rules, faults


def faults(text: str) -> list[str]:
    """Return every fault of one revision of the page.

    Parameters
    ----------
    text : str
        The page.

    Returns
    -------
    list of str
        Each fault, naming its line.

    """
    sections, rules, found = read(text)
    if not rules:
        return [*found, "the page holds no rules."]

    for place, (number, line, _) in enumerate(sections, start=1):
        if number != place:
            found.append(
                f"line {line}: section {number} should be section {place}. A new "
                "section goes at the end of the page."
            )

    # each rule belongs to the section its heading sits under
    expected: dict[int, int] = {}
    for rule in rules:
        under = [number for number, line, _ in sections if line < rule.line]
        if not under:
            found.append(f"line {rule.line}: rule {rule.key} is under no section.")
            continue
        section = under[-1]
        if rule.section != section:
            found.append(
                f"line {rule.line}: rule {rule.key} sits in section {section}, so "
                f"its number begins '{section}.'."
            )
            continue
        place = expected.get(section, 0) + 1
        expected[section] = place
        if rule.number != place:
            found.append(
                f"line {rule.line}: rule {rule.key} should be rule {section}.{place}. "
                "A new rule goes at the end of its section, and a rule is never "
                "deleted or moved."
            )
        if rule.agreement is None:
            found.append(
                f"line {rule.line}: rule {rule.key} opens with no status. Write "
                "'🤝 Agreed (<date>, {user}`<handle>`, {pull}`<number>`)', or "
                "'🗄️ Retired (<date>, {user}`<handle>`, {pull}`<number>`; agreed "
                "<date>, {pull}`<number>`)' and why."
            )
    return found


def held(before: str, after: str) -> list[str]:
    """Return a fault for each rule of an earlier revision that a later one broke.

    A rule keeps its number for good, so each rule of ``before`` must still be in
    ``after`` under the same number, agreed when and where it was, with a title
    still like the one it had, and a retired rule stays retired. Its title and
    text may be corrected, but not replaced.

    Parameters
    ----------
    before : str
        The page as it was, on the base branch.
    after : str
        The page as it is now.

    Returns
    -------
    list of str
        Each fault, naming the rule.

    """
    _, was, _ = read(before)
    _, now, _ = read(after)
    current = {rule.key: rule for rule in now}
    problems = []
    for rule in was:
        if rule.agreement is None:
            continue
        found = current.get(rule.key)
        if found is None:
            problems.append(
                f"rule {rule.key}, '{rule.title}', was removed. A rule is never "
                "deleted or moved: restore it, and retire it in place if it no "
                "longer holds."
            )
        elif found.agreement != rule.agreement:
            problems.append(
                f"rule {rule.key} was the rule agreed {_when(rule)}, '{rule.title}', "
                f"and now names one agreed {_when(found)}. A rule keeps its number: "
                "restore it, and add a new rule at the end of its section."
            )
        elif _likeness(rule.title, found.title) < LIKENESS:
            problems.append(
                f"rule {rule.key} was '{rule.title}', and is now '{found.title}', "
                "which reads as another rule. A rule keeps its number, and its title "
                "is only ever corrected: restore it, and add a new rule at the end "
                "of its section."
            )
        elif rule.retired and not found.retired:
            problems.append(
                f"rule {rule.key}, '{rule.title}', was retired, and stays retired. "
                "Add a new rule at the end of its section instead."
            )
    return problems


def _likeness(before: str, after: str) -> float:
    """Return how alike two titles are, from 0 to 1."""
    return difflib.SequenceMatcher(None, before.casefold(), after.casefold()).ratio()


def _when(rule: Rule) -> str:
    """Return when and where a rule was agreed, for a message."""
    agreement = rule.agreement
    return "nowhere" if agreement is None else f"{agreement[0]} in {agreement[1]}"

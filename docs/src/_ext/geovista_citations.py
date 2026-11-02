# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""The grammar of a citation of a design specification section, decision, item or row.

What a citation is, and which anchor it names, is defined here once, and
nowhere else (citation spec §4.1). So is what a decision is, how one is cited,
and how a specification's ledger of them reads (ledger spec §3.1), what an
item and a roadmap row are, and how each is cited (items spec §3.1), and how an
open item's entry reads (items spec §3.2). The conventions test,
``tests/test_spec_conventions.py``, reads the repository with it, and the
build-time transform and the renumber guard of the citation links design will
import it too, so that no two readers can disagree about what a citation is.

It is a plain module rather than a Sphinx extension, so it defines no ``setup``.
``docs/src/_ext`` is on ``sys.path`` for the whole build, which is why its name
carries the ``geovista_`` prefix. A test or a script loads it by path, and must
register it in ``sys.modules`` before executing it, as the dataclasses below
resolve their annotations through it.

Nothing here needs ``sphinx``, a build or a network. A numbered list is read with
``markdown-it-py``, the parser MyST is built on, so that its items are the ones the
build names. The module sits inside the corpus it governs, so it builds the section
sign rather than write it.

"""

from __future__ import annotations

from dataclasses import dataclass
import functools
from pathlib import Path
import re
from typing import TYPE_CHECKING

from markdown_it import MarkdownIt

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from markdown_it.rules_block import StateBlock

#: The repository root, beneath which the corpus is derived.
REPO = Path(__file__).parents[3]

#: The published specifications.
SPECS = REPO / "docs" / "src" / "developer" / "specs"

#: The section sign, built rather than written: see the module docstring.
SECTION = "\N{SECTION SIGN}"

#: The ellipsis a citation prefix is declared with.
ELLIPSIS = "\N{HORIZONTAL ELLIPSIS}"

#: The trees the walk never enters, because what they hold is generated, fetched
#: or frozen rather than written. A directory whose name opens with a dot holds
#: tooling state and is never entered either, save ".github".
PRUNED = (
    "build",  # written by a wheel or sdist build
    "dist",  # written by a wheel or sdist build
    "htmlcov",  # written by coverage
    "docs/_build",  # written by sphinx
    "docs/image_cache",  # written by the documentation image tests
    "docs/src/developer/plans",  # frozen, and so outside the rules (docs spec §3.5)
    "docs/src/generated",  # written by sphinx-gallery
    "docs/src/reference/generated",  # written by sphinx-autoapi
    "docs/src/tags",  # written by sphinx-tags
    "test_images",  # written by the image tests
    "test_images_failed",  # written by the image tests
    "tests/plotting/unit_image_cache",  # image baselines fetched from geovista-data
)

#: The pruned trees that are tracked, and so present in a fresh clone.
TRACKED = ("docs/src/developer/plans",)

ANCHOR = re.compile(r"^\((?P<slug>[a-z][a-z-]*?)-(?P<num>\d+(?:-\d+)*)\)=\s*$")
HEADING = re.compile(r"^#{2,6}\s+(?P<num>\d+(?:\.\d+)*)\.?\s+(?P<title>\S.*?)\s*$")
FENCE = re.compile(r"^\s*(?P<rail>`{3,}|~{3,})(?P<info>.*)$")
#: The MyST directives whose body is code rather than prose, and so goes unread.
CODE_DIRECTIVES = frozenset(
    {
        "code",
        "code-block",
        "code-cell",
        "literalinclude",
        "math",
        "mermaid",
        "raw",
        "sourcecode",
    }
)
#: An inline code span, and the role it completes when one is written against it.
SPAN = re.compile(
    r"(?P<role>\{[\w:-]+\}|:[\w:-]+:)?"
    r"(?<!`)(?P<ticks>`+)(?!`)(?P<body>.+?)(?<!`)(?P=ticks)(?!`)"
)
TARGETED = re.compile(r"^(?P<text>.*?)\s*<(?P<target>[^<>]+)>$")
LABEL = re.compile(
    r"^(?P<prefix>[a-z][a-z-]*?)-(?P<num>\d+(?:-\d+)*)"
    r"(?:-decision-(?P<decision>\d+)|-item-(?P<item>\d+)|-row-(?P<row>\d+[a-z]?))?$"
)
SEPARATOR = re.compile(r"[^\S\n]*[,/][^\S\n]*")

#: The variation selector an emoji may carry, and may be typed without.
VS16 = "\N{VARIATION SELECTOR-16}"

#: The states of a decision (ledger spec §3.2, §3.3), as the specification spells
#: them, built by name: see the module docstring.
AGREED = "\N{HANDSHAKE} Agreed"
RETIRED = f"\N{FILE CABINET}{VS16} Retired"

#: The states of a decision's verification (ledger spec §3.4).
PENDING = "\N{HOURGLASS WITH FLOWING SAND} pending"
VERIFIED = "\N{WHITE HEAVY CHECK MARK} verified"
SIGNED_OFF = f"\N{WRITING HAND}{VS16} signed off"
LEDGER_RETIRED = f"\N{FILE CABINET}{VS16} retired"

#: The states of an open item (items spec §3.2), built by name.
OPEN = "\N{BLACK QUESTION MARK ORNAMENT} Open"
DEFERRED = f"\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}{VS16} Deferred"
RESOLVED = "\N{CHEQUERED FLAG} Resolved"
ABANDONED = "\N{NO ENTRY SIGN} Abandoned"
GRADUATED = "\N{GRADUATION CAP} Graduated"
ITEMED_STATES = (OPEN, DEFERRED, RESOLVED, ABANDONED, GRADUATED)

#: The parts of an open item's provenance: where it was found, the row that owes
#: it, each row it moved from, and the issue that tracks it, in that order.
FOUND = "\N{RIGHT-POINTING MAGNIFYING GLASS}"
OWED = "\N{DIRECT HIT}"
MOVED = f"\N{LEFTWARDS BLACK ARROW}{VS16}"
TICKET = "\N{TICKET}"
PARTS = (FOUND, OWED, MOVED, TICKET)

#: What separates the parts of an item's provenance.
DOT = " \N{MIDDLE DOT} "

#: The titles of the sections holding the decisions, their ledger and the items.
DECISIONS = "Decisions"
VERIFICATION = "Verification"
OPEN_ITEMS = "Open Items"

#: The header of the ledger, cell by cell.
LEDGER_HEADER = ("Decision", "Status", "Evidence")

#: The number an item of a numbered list opens with, as ``4.``, and the space after.
MARKER = re.compile(r"^[ \t]*\d+[.)][ \t]*")

#: A line MyST reads as a block of its own, which ends a paragraph above it with no
#: blank line between: a target, a comment, a block break, or a footnote.
MYST_LINE = re.compile(r"\(.+\)=\s*$|%|\+(?:[ \t]*\+){2,}|\[\^[^\]\s]+\]:")

#: A bold run, which may hold an emphasised word, as ``**A *very* big title.**``.
BOLD = re.compile(r"\*\*(?P<text>.+?)\*\*", flags=re.DOTALL)
#: The bold run an item opens with when it carries a state, ``**Open**`` in the
#: grammar of docs spec §3.6, or its emoji first in that of items spec §3.2.
STATED = re.compile(r"\W*(?:Open|Deferred|Resolved|Abandoned|Graduated)")
#: The dashes an item's state and provenance are parted from its title by.
DASHES = " -\N{EN DASH}\N{EM DASH}"
#: The issue a ticket names, and the row a graduated item's settlement ends with.
ISSUE = re.compile(r"\{issue\}`(?P<number>\d+)`")
GRADUATES = re.compile(r"(?:^|[\s,])to\s+(?P<row>rows?\s.*?)\s*$")

#: A table cell boundary: a pipe, unless escaped.
PIPE = re.compile(r"(?<!\\)\|")

#: The first cell of a roadmap row: its number, which may carry a letter, as ``6a``.
ROW_NUMBER = re.compile(r"[0-9]+[a-z]?")


@dataclass(frozen=True)
class Citation:
    """One citation, as written and as resolved.

    Attributes
    ----------
    text : str
        The citation exactly as written.
    slug : str or None
        The anchor it names, or ``None`` for a bare section number written in a
        file that owns no sections.
    start, end : int
        Where it is written in the text scanned, so that ``text`` is
        ``source[start:end]``, and a reader replacing it knows what to split.
    ends : tuple of str
        The anchor of a range's far end, as ``rows 3 to 11 of §10`` names row 11,
        each to be checked as ``slug`` is; empty for a citation of one thing.

    """

    text: str
    slug: str | None
    start: int
    end: int
    ends: tuple[str, ...] = ()


@dataclass(frozen=True)
class Namespace:
    """What the specifications declare, and the grammar derived from it.

    Attributes
    ----------
    anchors : frozenset of str
        Every anchor declared, e.g. ``typing-spec-3-2``.
    owners : dict
        The prefix each specification owns, keyed by its path.
    signed : re.Pattern
        A citation carrying its section sign, with any decision, item or row it
        names.
    unsigned : re.Pattern
        A known prefix and a section number with no sign between them.

    """

    anchors: frozenset[str]
    owners: dict[Path, str]
    signed: re.Pattern[str]
    unsigned: re.Pattern[str]

    @property
    def prefixes(self) -> set[str]:
        """The prefixes the anchors carry, e.g. ``typing-spec``."""
        return {match["prefix"] for a in self.anchors if (match := LABEL.match(a))}


@dataclass(frozen=True)
class Decision:
    """One decision of a specification, as its entry is written.

    Attributes
    ----------
    number : int
        Its number in the list, which it keeps (ledger spec §2 decision 2).
    line : int
        The line its entry opens on.
    state : str or None
        :data:`AGREED` or :data:`RETIRED`, or ``None`` for an entry with no state.
    carried : str
        The parenthetical after the state, without its parentheses.
    title : str
        The bold title, read whole although it wraps.
    body : str
        The text after the title, its lines joined by single spaces.

    """

    number: int
    line: int
    state: str | None
    carried: str
    title: str
    body: str


@dataclass(frozen=True)
class Item:
    """One open item of a specification, as its entry is written (items spec §3.2).

    Attributes
    ----------
    number : int
        Its number in the list, as written.
    line : int
        The line its entry opens on.
    state : str or None
        One of :data:`ITEMED_STATES`, or ``None`` for an entry with none, such as
        one still in the grammar of docs spec §3.6.
    settled : str
        The date and reference a settled item leads its parenthetical with, or
        ``""`` when it is open or deferred, or leads with a part.
    found : str
        What follows :data:`FOUND`: the date and pull request it surfaced in, or
        ``""`` when it carries none.
    owed : str or None
        What follows :data:`OWED`, the row that owes it, as ``row 5 of §10``.
    moves : tuple of str
        What follows each :data:`MOVED`, in the order written.
    issue : int or None
        The issue :data:`TICKET` names, or ``None`` when it names none.
    graduated : str or None
        The row a graduated item became, as its settlement ends ``to row N of §M``.
    title : str
        The bold title, read whole although it wraps.
    body : str
        The text after the title, its lines joined by single spaces.
    carried : str
        The parenthetical after the state, without its parentheses, which
        :func:`provenance` splits into its parts.

    """

    number: int
    line: int
    state: str | None
    settled: str
    found: str
    owed: str | None
    moves: tuple[str, ...]
    issue: int | None
    graduated: str | None
    title: str
    body: str
    carried: str = ""


@dataclass(frozen=True)
class LedgerRow:
    """One row of a specification's Verification table.

    Attributes
    ----------
    cell : str
        The first cell as written, which names the decision.
    line : int
        The line the row is written on.
    status : str
        The Status cell.
    evidence : str
        The Evidence cell.

    """

    cell: str
    line: int
    status: str
    evidence: str

    @property
    def decision(self) -> int | None:
        """The decision the row is for, or ``None`` when its first cell is no number."""
        # ASCII digits only: "²" is a digit to str.isdigit, and no int() reads it
        return int(self.cell) if re.fullmatch(r"[0-9]+", self.cell) else None


@dataclass(frozen=True)
class Listed:
    """One top-level numbered item of a section, which a citation can name.

    Attributes
    ----------
    section : str
        The number of the section holding it, as ``4.4``.
    number : int
        Its number in the list, by its place, as the build numbers it.
    line : int
        The line its entry opens on.
    title : str or None
        The bold title after any state, read whole although it wraps, or ``None``
        for an item with no title, such as a step of a procedure.
    body : str
        The text after the title, or after the state and its parenthetical when
        it has none, its lines joined by single spaces.

    """

    section: str
    number: int
    line: int
    title: str | None
    body: str


@dataclass(frozen=True)
class Row:
    """One row of a roadmap table, which a citation can name.

    Attributes
    ----------
    section : str
        The number of the section holding the table, as ``10``.
    row : str
        Its first cell, the row's number, which may carry a letter, as ``6a``.
    line : int
        The line the row is written on.
    scope : str
        The Scope cell.
    status : str
        The Status cell.

    """

    section: str
    row: str
    line: int
    scope: str
    status: str


@dataclass(frozen=True)
class Numbered:
    """One item of a top-level numbered list, as MyST reads it.

    Attributes
    ----------
    heading : int
        The line of the numbered heading the list sits under, or 0 before one.
    section : str or None
        That heading's number, as ``4.4``, or ``None`` before one.
    title : str or None
        That heading's title, or ``None`` before one.
    index : int
        Which of the section's numbered lists holds it, from 0 for the first.
    written : int
        Its number as written.
    number : int
        Its number by its place: its list's start, plus the items before it.
    line : int
        The line it opens on.
    end : int
        The last line it runs to.
    text : str
        Its text, less its number and any fenced code, its lines stripped and
        joined by single spaces.

    """

    heading: int
    section: str | None
    title: str | None
    index: int
    written: int
    number: int
    line: int
    end: int
    text: str


def cells(line: str) -> list[str]:
    """Split a table row into its cells, keeping an escaped pipe within its cell.

    The row is split first, and only then are its outer separators dropped, so an
    escaped pipe ending the last cell is never mistaken for one.
    """
    parts = PIPE.split(line.strip())
    if parts and not parts[0].strip():
        parts = parts[1:]
    if len(parts) > 1 and not parts[-1].strip():
        parts = parts[:-1]
    return [cell.strip() for cell in parts]


def state_of(written: str, states: Iterable[str]) -> str | None:
    """Read the state ``written`` opens with, with or without its variation selector.

    Parameters
    ----------
    written : str
        The text, e.g. a Status cell or the bold run an entry opens with.
    states : iterable of str
        The states it may open with, spelled as the specification spells them.

    Returns
    -------
    str or None
        The state in its canonical spelling, or ``None`` if it opens with none.

    """
    plain = written.replace(VS16, "")
    return next((s for s in states if plain.startswith(s.replace(VS16, ""))), None)


def decision_anchor(slug: str, number: int) -> str:
    """Spell the anchor of a decision, e.g. ``heights-spec-2-decision-3``."""
    return f"{slug}-2-decision-{number}"


def _member(slug: str, section: str, kind: str, label: str) -> str:
    """Spell the anchor of an item or a row of the section numbered ``section``."""
    return f"{slug}-{section.replace('.', '-')}-{kind}-{label.lower()}"


def item_anchor(slug: str, section: str, number: int) -> str:
    """Spell the anchor of an item, e.g. ``scene-spec-4-4-item-2``."""
    return _member(slug, section, "item", str(number))


def row_anchor(slug: str, section: str, row: str) -> str:
    """Spell the anchor of a roadmap row, e.g. ``typing-spec-4-row-6a``."""
    return _member(slug, section, "row", row)


def balanced(text: str) -> str:
    """Read the parenthetical ``text`` opens with, balanced so a link survives."""
    text = text.lstrip()
    if not text.startswith("("):
        return ""
    depth = 0
    for index, char in enumerate(text):
        depth += {"(": 1, ")": -1}.get(char, 0)
        if depth == 0:
            return text[1:index]
    return text[1:]


def _section(text: str, number: str, title: str) -> list[tuple[int, str]]:
    """Read the lines of the section numbered ``number`` and titled ``title``."""
    found: list[tuple[int, str]] = []
    inside = False
    for line_number, line in read_lines(text):
        heading = HEADING.match(line)
        if heading is not None:
            inside = heading["num"] == number and heading["title"] == title
            if not inside and found:
                break
            continue
        if inside:
            found.append((line_number, line))
    return found


def _myst_line(state: StateBlock, start: int, end: int, silent: bool) -> bool:  # noqa: ARG001, FBT001
    """Read a line MyST reads as a block of its own (:data:`MYST_LINE`).

    MyST adds each to CommonMark as a block able to end a paragraph, and so a
    list, which is all that is read of it here.
    """
    if state.sCount[start] - state.blkIndent >= 4:
        # a line of an indented code block
        return False
    line = state.src[state.bMarks[start] + state.tShift[start] : state.eMarks[start]]
    if MYST_LINE.match(line) is None:
        return False
    if not silent:
        state.push("myst_line", "", 0).map = [start, start + 1]
        state.line = start + 1
    return True


#: The parser a numbered list is read with: CommonMark with tables, as MyST's is,
#: and the lines MyST reads as blocks of their own.
MARKDOWN = MarkdownIt("commonmark").enable("table")
MARKDOWN.block.ruler.before(
    "blockquote",
    "myst_line",
    _myst_line,
    {"alt": ["paragraph", "reference", "blockquote", "list"]},
)


@functools.lru_cache(maxsize=64)
def numbered(text: str) -> tuple[Numbered, ...]:
    """Read every item of each top-level numbered list, as MyST reads it.

    The lists are read by the parser MyST is built on, so where a list ends, and
    which items it holds, is never decided here: a line written flush straight
    after an item's paragraph is more of it, a list interrupts a paragraph only if
    it opens at 1, and a ``1.`` after a blank line continues the list already
    open, all as CommonMark has it. Each item is numbered by its place, as the
    build numbers it, and keeps the number written too. A list is placed under the
    numbered heading before it, whatever headings without a number come between.

    Parameters
    ----------
    text : str
        The specification.

    Returns
    -------
    tuple of Numbered
        In the order written.

    """
    lines = text.splitlines()
    prose = {number for number, _ in read_lines(text)}
    found: list[Numbered] = []
    heading, section, title = 0, None, None
    index, start, offset, inside = -1, 1, 0, False
    for token in MARKDOWN.parse(text):
        if token.type == "heading_open" and token.level == 0 and token.map:
            match = HEADING.match(lines[token.map[0]])
            if match is not None:
                heading, section, title = token.map[0] + 1, match["num"], match["title"]
                index = -1
        elif token.type == "ordered_list_open" and token.level == 0:
            index, offset, inside = index + 1, 0, True
            start = int(token.attrGet("start") or 1)
        elif token.type == "ordered_list_close" and token.level == 0:
            inside = False
        elif token.type == "list_item_open" and inside and token.level == 1:
            first, last = token.map[0] + 1, token.map[1]
            opening = lines[first - 1]
            parts = [opening[MARKER.match(opening).end() :]]
            parts += [
                lines[n - 1].strip()
                for n in range(first + 1, last + 1)
                if n in prose and lines[n - 1].strip()
            ]
            found.append(
                Numbered(
                    heading=heading,
                    section=section,
                    title=title,
                    index=index,
                    written=int(token.info),
                    number=start + offset,
                    line=first,
                    end=last,
                    text=" ".join(parts),
                )
            )
            offset += 1
    return tuple(found)


def _first_list(text: str, wanted: Callable[[re.Match[str]], bool]) -> list[Numbered]:
    """Read the first numbered list under the first numbered heading ``wanted``."""
    first = next(
        (
            number
            for number, line in read_lines(text)
            if (heading := HEADING.match(line)) is not None and wanted(heading)
        ),
        None,
    )
    return [
        entry
        for entry in numbered(text)
        if first is not None and entry.heading == first and entry.index == 0
    ]


def decision_entries(text: str) -> list[Numbered]:
    """Read the items of a specification's Decisions, its second section's list."""
    return _first_list(
        text, lambda heading: (heading["num"], heading["title"]) == ("2", DECISIONS)
    )


def decisions(text: str) -> list[Decision]:
    """Read the decisions of a specification: the numbered items of its Decisions.

    An entry is an item of the section's first numbered list, as
    :func:`numbered` reads it, so a title or a parenthetical that wraps is read
    whole. A bulleted item is not a decision, since it has no number to be cited
    by.

    Parameters
    ----------
    text : str
        The specification.

    Returns
    -------
    list of Decision
        In the order written, or empty when its second section is not Decisions.

    """
    found = []
    for entry in decision_entries(text):
        number, line, joined = entry.written, entry.line, entry.text
        runs = list(BOLD.finditer(joined))
        state = state_of(runs[0]["text"], (AGREED, RETIRED)) if runs else None
        carried = ""
        if state is not None:
            carried = balanced(joined[runs[0].end() :])
            runs = runs[1:]
        title = runs[0]["text"].strip() if runs else ""
        body = joined[runs[0].end() :].strip() if runs else joined.strip()
        found.append(Decision(number, line, state, carried, title, body))
    return found


def provenance(carried: str) -> list[tuple[str | None, str]]:
    """Split an item's parenthetical into its parts, each read by its emoji.

    Parameters
    ----------
    carried : str
        The parenthetical, without its parentheses, its lines joined.

    Returns
    -------
    list of tuple of (str or None, str)
        Each part in the order written: the emoji of :data:`PARTS` it opens with,
        with or without its variation selector, or ``None`` for a part opening
        with none, such as a settled item's date and reference; and what follows.

    """
    found: list[tuple[str | None, str]] = []
    if not carried.strip():
        return found
    for part in re.split(rf"\s*{DOT.strip()}\s*", carried.strip()):
        plain = part.replace(VS16, "")
        kind = next((p for p in PARTS if plain.startswith(p.replace(VS16, ""))), None)
        rest = plain[len(kind.replace(VS16, "")) :] if kind else part
        found.append((kind, rest.strip()))
    return found


def _titled(text: str, title: str) -> list[tuple[int, str]]:
    """Read the lines of the first section titled ``title``, whatever its case.

    A heading in headline style and one in sentence case name the same section.
    """
    found: list[tuple[int, str]] = []
    inside = False
    for number, line in read_lines(text):
        heading = HEADING.match(line)
        if heading is not None:
            if inside:
                break
            inside = heading["title"].casefold() == title.casefold()
            continue
        if inside:
            found.append((number, line))
    return found


def items(text: str) -> list[Item]:
    """Read the open items of a specification, in the grammar of items spec §3.2.

    The items are the numbered entries of its Open Items section, whatever its
    number and its case, as :func:`numbered` reads its first list, so a title or
    a parenthetical that wraps is read whole. A part is read by its emoji,
    whatever it holds, so that a rule can say what is wrong with it.

    Parameters
    ----------
    text : str
        The specification.

    Returns
    -------
    list of Item
        In the order written, or empty when it has no Open Items section.

    """
    found = []
    entries = _first_list(
        text, lambda heading: heading["title"].casefold() == OPEN_ITEMS.casefold()
    )
    for entry in entries:
        number, line, rest = entry.written, entry.line, entry.text
        opening = BOLD.match(rest)
        state = state_of(opening["text"].strip(), ITEMED_STATES) if opening else None
        carried = ""
        if opening is not None and state is not None:
            rest = rest[opening.end() :].lstrip()
            carried = balanced(rest)
            if rest.startswith("("):
                rest = rest[len(carried) + 2 :]
            rest = rest.lstrip(DASHES)
        written = provenance(carried)
        settled = ""
        if state in (RESOLVED, ABANDONED, GRADUATED) and written and not written[0][0]:
            settled = written[0][1]
        graduated = GRADUATES.search(settled) if state == GRADUATED else None
        ticket = next((said for kind, said in written if kind == TICKET), "")
        issue = ISSUE.fullmatch(ticket)
        titled = BOLD.match(rest)
        found.append(
            Item(
                number=number,
                line=line,
                state=state,
                settled=settled,
                found=next((said for kind, said in written if kind == FOUND), ""),
                owed=next((said for kind, said in written if kind == OWED), None),
                moves=tuple(said for kind, said in written if kind == MOVED),
                issue=int(issue["number"]) if issue else None,
                graduated=graduated["row"] if graduated else None,
                title=titled["text"].strip() if titled else "",
                body=(rest[titled.end() :] if titled else rest).strip(),
                carried=carried,
            )
        )
    return found


def _entry(section: str, number: int, line: int, joined: str) -> Listed:
    """Read an item's title and body, past the state and parenthetical it opens with."""
    rest = joined
    opening = BOLD.match(rest)
    if opening is not None and STATED.fullmatch(opening["text"].strip()):
        rest = rest[opening.end() :].lstrip()
        if rest.startswith("("):
            rest = rest[len(balanced(rest)) + 2 :]
        rest = rest.lstrip(DASHES)
    title = None
    titled = BOLD.match(rest)
    if titled is not None:
        title = titled["text"].strip()
        rest = rest[titled.end() :]
    return Listed(section, number, line, title, rest.strip())


def listed(text: str) -> list[Listed]:
    """Read the items of a specification: the first numbered list of each section.

    Only the top-level items of a section's first numbered list are its items, so a
    second list, such as the steps of a procedure under its design, names nothing
    a citation can reach, and a citation of one past the first list's end fails
    rather than linking the wrong item. The lists are read by :func:`numbered`, as
    MyST reads them, and each item is numbered by its place, matching the anchor
    the build gives it. The Decisions are no items, since a decision is cited only
    as one (ledger spec §2 decision 1).

    Parameters
    ----------
    text : str
        The specification.

    Returns
    -------
    list of Listed
        In the order written.

    """
    return [
        _entry(entry.section, entry.number, entry.line, entry.text)
        for entry in numbered(text)
        if entry.section is not None
        and entry.index == 0
        and (entry.section, entry.title) != ("2", DECISIONS)
    ]


def roadmap_header(header: list[str]) -> bool:
    """Decide whether a table's header is a roadmap's: ``#``, ``Scope`` and ``Status``.

    A Verification table has a Status column too, so a roadmap is read by its whole
    header (ledger spec §3.6), which a type coverage roadmap extends with ``Lines``.
    """
    return bool(header) and header[0] == "#" and {"Scope", "Status"} <= set(header)


def rows(text: str) -> list[Row]:
    """Read the rows of every roadmap table of a specification, wherever it sits.

    A row is read only if its first cell is a row number, as ``7`` or ``6a``, so a
    cell written otherwise, as ``**7**`` or ``7.``, names no anchor.

    Parameters
    ----------
    text : str
        The specification.

    Returns
    -------
    list of Row
        In the order written, each with the number of the section holding it.

    """
    found: list[Row] = []
    table: list[tuple[int, str]] = []
    section: str | None = None
    for number, line in [*read_lines(text), (0, "")]:
        if line.startswith("|"):
            table.append((number, line))
            continue
        if table:
            header = cells(table[0][1])
            if section is not None and roadmap_header(header):
                scope, status = header.index("Scope"), header.index("Status")
                for written, row in table[2:]:
                    parts = [*cells(row), *[""] * len(header)]
                    # a cell such as "**1**" names no row, and the conventions
                    # test reports it where it is written
                    if ROW_NUMBER.fullmatch(parts[0]):
                        found.append(
                            Row(section, parts[0], written, parts[scope], parts[status])
                        )
            table = []
        heading = HEADING.match(line)
        if heading is not None:
            section = heading["num"]
    return found


def ledger(text: str) -> list[LedgerRow] | None:
    """Read a specification's Verification table, or ``None`` if it has none.

    The table is the first under the section titled Verification whose header is
    :data:`LEDGER_HEADER`, so a table of any other kind is never read as one.

    Parameters
    ----------
    text : str
        The specification.

    Returns
    -------
    list of LedgerRow or None
        Its rows in order, the header and the divider skipped.

    """
    lines: list[tuple[int, str]] = []
    title = None
    for number, line in read_lines(text):
        heading = HEADING.match(line)
        if heading is not None:
            title = heading["title"]
        elif title == VERIFICATION:
            lines.append((number, line))
    table: list[tuple[int, list[str]]] = []
    for number, line in [*lines, (0, "")]:
        if line.startswith("|"):
            table.append((number, cells(line)))
            continue
        if table:
            if tuple(table[0][1]) == LEDGER_HEADER:
                return [
                    LedgerRow(row[0], number, *[*row, "", ""][1:3])
                    for number, row in table[2:]
                ]
            table = []
    return None


#: The states of a Verification row, in the order the summary counts them.
SUMMARISED = (
    VERIFIED,
    SIGNED_OFF,
    PENDING,
    LEDGER_RETIRED,
)


def summary(statuses: Iterable[str]) -> str:
    """Count each state of a ledger, as the line under its table reads.

    Parameters
    ----------
    statuses : iterable of str
        The Status cells, each opening with its state.

    Returns
    -------
    str
        Each state's emoji and count, then how many decisions in force are
        verified, as ledger spec §3.4 spells it.

    """
    counts = dict.fromkeys(SUMMARISED, 0)
    total = 0
    for status in statuses:
        total += 1
        state = state_of(status.strip(), SUMMARISED)
        if state is not None:
            counts[state] += 1
    verified, signed, _, retired = counts.values()
    tally = " · ".join(f"{state.split()[0]} {count}" for state, count in counts.items())
    return (
        f"{tally}: {verified + signed} of {total - retired} decisions in force verified"
    )


def specifications(specs: Path = SPECS) -> list[Path]:
    """Gather every markdown document in the collection, sorted."""
    return sorted(specs.glob("*.md"))


def entered(name: str) -> bool:
    """Decide whether the walk enters a directory of this name, wherever it sits."""
    if name == "__pycache__" or name.endswith(".egg-info"):
        return False
    return not name.startswith(".") or name == ".github"


def foreign(path: Path) -> bool:
    """Decide whether a directory is another tree: a virtualenv, or a repository.

    Both can sit in a checkout under any name, ``venv`` and a nested worktree
    among them, and what they hold is not this repository's to govern.
    """
    return (path / "pyvenv.cfg").is_file() or (path / ".git").exists()


def corpus(repo: Path = REPO) -> dict[Path, str]:
    """Gather every file the conventions govern, with its text.

    Parameters
    ----------
    repo : Path, optional
        The repository root. It defaults to this repository's; a test passes a
        tree of its own.

    Returns
    -------
    dict
        The text of every UTF-8 file beneath ``repo`` outside :data:`PRUNED`,
        keyed by path. A file that is not UTF-8 is not text, and is dropped.

    """
    found: dict[Path, str] = {}
    for here, dirs, files in repo.walk():
        relative = here.relative_to(repo)
        dirs[:] = [
            name
            for name in dirs
            if entered(name)
            and (relative / name).as_posix() not in PRUNED
            and not foreign(here / name)
        ]
        for name in files:
            path = here / name
            try:
                found[path] = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
    return dict(sorted(found.items()))


def holds_code(info: str) -> bool:
    """Decide whether a fence with this info string holds code rather than prose."""
    if not info.startswith("{"):
        return True
    return info[1:].partition("}")[0] in CODE_DIRECTIVES


def read_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield the lines of markdown that are not code.

    A fence holds code, and its lines are skipped, unless it opens a MyST
    directive whose body is rendered prose, such as ``{note}``, whose lines are
    read; a fence nested inside one is code again. The opening rail is
    remembered rather than counted, as in ``tephpy``'s citation grammar: a block
    opened with four backticks may quote one opened with three, so a fence
    closes only on a rail of the same character, at least as long, and carrying
    no info string. A backtick fence's info string cannot hold a backtick, so a
    line opening with inline code opens nothing.

    Parameters
    ----------
    text : str
        The document.

    Yields
    ------
    tuple of (int, str)
        The 1-indexed line number, and the line.

    """
    opened: list[tuple[str, bool]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        fence = FENCE.match(line)
        if fence is not None and not (fence["rail"][0] == "`" and "`" in fence["info"]):
            rail, info = fence["rail"], fence["info"].strip()
            if (
                opened
                and not info
                and rail[0] == opened[-1][0][0]
                and len(rail) >= len(opened[-1][0])
            ):
                opened.pop()
                continue
            if not opened or not opened[-1][1]:
                opened.append((rail, holds_code(info)))
                continue
        if not any(code for _, code in opened):
            yield number, line


def source_lines(path: Path, text: str) -> Iterator[tuple[int, str]]:
    """Yield the numbered lines of a file, less the fenced code of markdown."""
    if path.suffix == ".md":
        yield from read_lines(text)
    else:
        yield from enumerate(text.splitlines(), start=1)


def prose(line: str) -> tuple[str, list[tuple[str, str]]]:
    """Blank the inline code in a line, collecting the roles it completes.

    A role is a name written against a single-backtick span, ``{ref}`` in MyST
    and ``:ref:`` in reStructuredText. Anything else in backticks is code. A role
    quoted inside a longer span is code too, which is how a specification shows a
    disagreeing role without committing one.

    Parameters
    ----------
    line : str
        The line.

    Returns
    -------
    tuple of (str, list)
        The line with every span blanked to spaces, so columns survive; and each
        role found, as its name and its body.

    """
    roles: list[tuple[str, str]] = []

    def blank(match: re.Match[str]) -> str:
        if match["role"] is not None and len(match["ticks"]) == 1:
            roles.append((match["role"].strip("{}:"), match["body"]))
        return " " * len(match[0])

    return SPAN.sub(blank, line), roles


def alternation(prefixes: Iterable[str]) -> str:
    """Spell the prefixes as an alternation, longest first, hyphens as whitespace.

    With no prefix it is ``(?!)``, which never matches, because an empty
    alternation would match everywhere.
    """
    forms = sorted(prefixes, key=len, reverse=True)
    return "|".join(form.replace("-", r"[^\S\n]+") for form in forms) or "(?!)"


#: A section number, as ``4.4``.
NUMBER = r"\d+(?:\.\d+)*"

#: Whitespace within a line, as a citation may not span one.
GAP = r"[^\S\n]+"

#: The number of an item or a row, which may carry a letter, as ``6a``.
MEMBER = r"\d+[a-z]?(?![\w-])"


def _led(group: str) -> str:
    """Spell the optional words before a citation naming its item or row.

    ``item 9 of``, ``row 5 of``, and a range of either, ``rows 3 to 11 of`` or
    ``rows 6a and 6b of``, each group's name opening with ``group``.
    """
    return (
        rf"(?:(?<![\w-])(?P<{group}lead>items?|rows?){GAP}(?P<{group}first>{MEMBER})"
        rf"(?:{GAP}(?:to|and){GAP}(?P<{group}last>{MEMBER}))?{GAP}of{GAP})?"
    )


def _trailed(group: str) -> str:
    """Spell the optional words after a citation naming its decision or item.

    ``decision 3`` or ``item 9``, read only when no item or row was named before
    the citation. A word and then whitespace, so ``decisions`` and ``items`` never
    match, and a plural names no one of them.
    """
    return (
        rf"(?({group}lead)|(?:{GAP}(?:decision{GAP}(?P<{group}decision>\d+)"
        rf"|item{GAP}(?P<{group}item>\d+))(?!\d))?)"
    )


def namespace(specs: Iterable[Path]) -> Namespace:
    """Read the anchors the specifications declare, and derive the grammar.

    The prefixes are derived rather than declared: a citation form is an anchor's
    prefix with its hyphens read back as whitespace. A prefix must start a word,
    and a citation may not span a line.

    A citation of a section may name a decision, ``§2 decision 3``, or an item,
    ``§8 item 9``, after it, or an item or a row before it, as ``item 9 of §8`` and
    ``row 5 of §10``. A range of either names both ends, as ``rows 3 to 11 of §10``
    and ``rows 6a and 6b of §4`` do (items spec §3.1).

    Parameters
    ----------
    specs : iterable of Path
        The specifications.

    Returns
    -------
    Namespace
        The anchors, their owners, and the citation patterns.

    """
    anchors: set[str] = set()
    owners: dict[Path, str] = {}
    for spec in specs:
        text = spec.read_text(encoding="utf-8")
        for _, line in read_lines(text):
            match = ANCHOR.match(line)
            if match is not None:
                anchors.add(f"{match['slug']}-{match['num']}")
                owners.setdefault(spec, match["slug"])
        # the anchors of a decision, an item and a row are generated by the build,
        # not written, so they are derived here from the entries themselves
        # (ledger spec §3.1, items spec §3.1)
        if spec in owners:
            owner = owners[spec]
            anchors.update(decision_anchor(owner, d.number) for d in decisions(text))
            anchors.update(
                item_anchor(owner, i.section, i.number) for i in listed(text)
            )
            anchors.update(row_anchor(owner, r.section, r.row) for r in rows(text))
    known = alternation({LABEL.match(a)["prefix"] for a in anchors})
    return Namespace(
        anchors=frozenset(anchors),
        owners=owners,
        signed=re.compile(
            _led("")
            + rf"(?<![\w-])(?P<prefix>{known})[^\S\n]*{SECTION}(?P<num>{NUMBER})"
            + _trailed("")
            + "|"
            + _led("bare_")
            + rf"{SECTION}(?P<bare>{NUMBER})"
            + _trailed("bare_"),
            flags=re.IGNORECASE,
        ),
        unsigned=re.compile(
            rf"(?<![\w-])(?P<prefix>{known})[^\S\n]+(?P<num>{NUMBER})",
            flags=re.IGNORECASE,
        ),
    )


def scan(
    source: str, pattern: re.Pattern[str], owner: str | None
) -> Iterator[Citation]:
    """Yield each citation in a line, resolved to the anchor it names.

    A prefix carries across a run joined by a comma or a solidus, and no further,
    so a bare section number opening the next sentence falls back to the
    containing document rather than inheriting the namespace before it.

    Parameters
    ----------
    source : str
        The text, with its code already blanked.
    pattern : re.Pattern
        The signed citation pattern of a :class:`Namespace`.
    owner : str or None
        The prefix of the document the text is in, or ``None`` when it owns no
        sections.

    Yields
    ------
    Citation
        One per citation, in the order written.

    """
    carried: str | None = None
    end = 0
    for match in pattern.finditer(source):
        joined = carried is not None and SEPARATOR.fullmatch(
            source[end : match.start()]
        )
        end = match.end()
        group = "" if match["prefix"] is not None else "bare_"
        if match["prefix"] is not None:
            carried = re.sub(r"\s+", "-", match["prefix"].lower())
            number = match["num"]
        elif joined:
            number = match["bare"]
        elif owner is not None:
            carried, number = owner, match["bare"]
        else:
            carried = None
            yield Citation(match[0], None, match.start(), match.end())
            continue
        slug = f"{carried}-{number.replace('.', '-')}"
        ends: tuple[str, ...] = ()
        lead, last = match[f"{group}lead"], match[f"{group}last"]
        if lead is not None:
            kind = lead.lower().removesuffix("s")
            ends = () if last is None else (_member(carried, number, kind, last),)
            slug = _member(carried, number, kind, match[f"{group}first"])
        elif match[f"{group}decision"] is not None:
            slug = f"{slug}-decision-{match[f'{group}decision']}"
        elif match[f"{group}item"] is not None:
            slug = item_anchor(carried, number, int(match[f"{group}item"]))
        yield Citation(match[0], slug, match.start(), match.end(), ends)


def cited_row(text: str, owner: str | None, names: Namespace) -> str | None:
    """Read ``text`` as one row's citation, as an item names its owner or graduation.

    The row may be another specification's, which the caller decides on.

    Parameters
    ----------
    text : str
        What the part holds, as ``row 5 of §10`` or ``row 5 of crs spec §10``.
    owner : str or None
        The prefix of the specification the part is written in.
    names : Namespace
        The namespace the citation is read in.

    Returns
    -------
    str or None
        The anchor of the row it names, whichever specification owns it, or
        ``None`` unless the whole of ``text`` is one citation of one row.

    """
    source = prose(text)[0].strip()
    found = list(scan(source, names.signed, owner))
    if len(found) != 1 or found[0].text != source or found[0].ends:
        return None
    label = LABEL.match(found[0].slug or "")
    return found[0].slug if label is not None and label["row"] is not None else None


def section_role(kind: str, body: str, names: Namespace) -> tuple[str, str] | None:
    """Read a role as a reference to a section: its display text and its target.

    ``None`` unless the role is a ``ref`` whose target carries a specification's
    prefix.
    """
    targeted = TARGETED.match(body)
    target = targeted["target"] if targeted else body.strip()
    label = LABEL.match(target)
    if kind != "ref" or label is None or label["prefix"] not in names.prefixes:
        return None
    return (targeted["text"] if targeted else ""), target

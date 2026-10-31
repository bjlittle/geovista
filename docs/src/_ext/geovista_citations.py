# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""The grammar of a citation of a design specification section, or decision.

What a citation is, and which anchor it names, is defined here once, and
nowhere else (citation spec §4.1). So is what a decision is, how one is cited,
and how a specification's ledger of them reads (ledger spec §3.1). The conventions test,
``tests/test_spec_conventions.py``, reads the repository with it, and the
build-time transform and the renumber guard of the citation links design will
import it too, so that no two readers can disagree about what a citation is.

It is a plain module rather than a Sphinx extension, so it defines no ``setup``.
``docs/src/_ext`` is on ``sys.path`` for the whole build, which is why its name
carries the ``geovista_`` prefix. A test or a script loads it by path, and must
register it in ``sys.modules`` before executing it, as the dataclasses below
resolve their annotations through it.

Nothing here needs ``sphinx``, a build or a network. The module sits inside the
corpus it governs, so it builds the section sign rather than write it.

"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

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
    r"^(?P<prefix>[a-z][a-z-]*?)-(?P<num>\d+(?:-\d+)*)(?:-decision-(?P<decision>\d+))?$"
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

#: The titles of the sections holding the decisions and their ledger.
DECISIONS = "Decisions"
VERIFICATION = "Verification"

#: The header of the ledger, cell by cell.
LEDGER_HEADER = ("Decision", "Status", "Evidence")

#: A top-level numbered item, and the bold runs an entry opens with.
NUMBERED = re.compile(r"^(?P<number>\d+)\.\s+(?P<body>.*)$")
#: A bold run, which may hold an emphasised word, as ``**A *very* big title.**``.
BOLD = re.compile(r"\*\*(?P<text>.+?)\*\*", flags=re.DOTALL)

#: A table cell boundary: a pipe, unless escaped.
PIPE = re.compile(r"(?<!\\)\|")


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

    """

    text: str
    slug: str | None
    start: int
    end: int


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
        A citation carrying its section sign.
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


def cells(line: str) -> list[str]:
    """Split a table row into its cells, keeping an escaped pipe within its cell."""
    return [cell.strip() for cell in PIPE.split(line.strip().strip("|"))]


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


def decisions(text: str) -> list[Decision]:
    """Read the decisions of a specification: the numbered items of its Decisions.

    An entry runs from its number to the next top-level line, so a title or a
    parenthetical that wraps is read whole. A bulleted item is not a decision,
    since it has no number to be cited by.

    Parameters
    ----------
    text : str
        The specification.

    Returns
    -------
    list of Decision
        In the order written, or empty when its second section is not Decisions.

    """
    entries: list[tuple[int, int, list[str]]] = []
    for number, line in _section(text, "2", DECISIONS):
        item = NUMBERED.match(line)
        if item is not None:
            entries.append((int(item["number"]), number, [item["body"]]))
        elif entries and line[:1].isspace() and line.strip():
            entries[-1][2].append(line.strip())
        elif line.strip() and entries:
            # the list has ended, at the first line written flush after it
            break
    found = []
    for number, line, parts in entries:
        joined = " ".join(parts)
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


def namespace(specs: Iterable[Path]) -> Namespace:
    """Read the anchors the specifications declare, and derive the grammar.

    The prefixes are derived rather than declared: a citation form is an anchor's
    prefix with its hyphens read back as whitespace. A prefix must start a word,
    and a citation may not span a line.

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
        # a decision's anchor is generated by the build, not written, so it is
        # derived here from the entries themselves (ledger spec §3.1)
        if spec in owners:
            anchors.update(
                decision_anchor(owners[spec], entry.number) for entry in decisions(text)
            )
    known = alternation({LABEL.match(a)["prefix"] for a in anchors})
    number = r"\d+(?:\.\d+)*"
    # "decision" and then whitespace, so "decisions" never matches
    decided = r"(?:[^\S\n]+decision[^\S\n]+(?P<{}>\d+)(?!\d))?"
    return Namespace(
        anchors=frozenset(anchors),
        owners=owners,
        signed=re.compile(
            rf"(?<![\w-])(?P<prefix>{known})[^\S\n]*{SECTION}(?P<num>{number})"
            + decided.format("decision")
            + rf"|{SECTION}(?P<bare>{number})"
            + decided.format("bare_decision"),
            flags=re.IGNORECASE,
        ),
        unsigned=re.compile(
            rf"(?<![\w-])(?P<prefix>{known})[^\S\n]+(?P<num>{number})",
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
        if match["prefix"] is not None:
            carried = re.sub(r"\s+", "-", match["prefix"].lower())
            number, decided = match["num"], match["decision"]
        elif joined:
            number, decided = match["bare"], match["bare_decision"]
        elif owner is not None:
            carried, number = owner, match["bare"]
            decided = match["bare_decision"]
        else:
            carried = None
            yield Citation(match[0], None, match.start(), match.end())
            continue
        slug = f"{carried}-{number.replace('.', '-')}"
        if decided is not None:
            slug = f"{slug}-decision-{decided}"
        yield Citation(match[0], slug, match.start(), match.end())


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

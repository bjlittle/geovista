# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""The grammar of a citation of a design specification section.

What a citation is, and which anchor it names, is defined here once, and
nowhere else (citation spec §4.1). The conventions test,
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
LABEL = re.compile(r"^(?P<prefix>[a-z][a-z-]*?)-(?P<num>\d+(?:-\d+)*)$")
SEPARATOR = re.compile(r"[^\S\n]*[,/][^\S\n]*")


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

    """

    text: str
    slug: str | None


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
        for _, line in read_lines(spec.read_text(encoding="utf-8")):
            match = ANCHOR.match(line)
            if match is not None:
                anchors.add(f"{match['slug']}-{match['num']}")
                owners.setdefault(spec, match["slug"])
    known = alternation({LABEL.match(a)["prefix"] for a in anchors})
    number = r"\d+(?:\.\d+)*"
    return Namespace(
        anchors=frozenset(anchors),
        owners=owners,
        signed=re.compile(
            rf"(?<![\w-])(?P<prefix>{known})[^\S\n]*{SECTION}(?P<num>{number})"
            rf"|{SECTION}(?P<bare>{number})",
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
            number = match["num"]
        elif joined:
            number = match["bare"]
        elif owner is not None:
            carried, number = owner, match["bare"]
        else:
            carried = None
            yield Citation(match[0], None)
            continue
        yield Citation(match[0], f"{carried}-{number.replace('.', '-')}")


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

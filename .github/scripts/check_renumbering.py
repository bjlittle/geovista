# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Guard the citations of a specification section against its renumbering.

A specification may insert a section where it belongs, and every section after
it takes a new number. A citation written against the old number still resolves,
to whatever the number names now, and nothing else notices. So, on a pull request,
this compares each specification it changes with the one on its base branch,
pairs every section with its counterpart, and fails on any line the pull request
did not touch that still cites a section which moved or went. With "--fix" it
rewrites the citations of the moved ones. With "--audit" it compares every
citation in the repository with the specification as it stood when the citing
line was written, which finds one that arrived by a branch older than the
renumber. The design is the citation links design, citation spec §4.5.

Numbered items and roadmap rows are cited by number too, in forms no grammar
reads, so they are held to being appended: one that moves or goes fails.

The citations are read with the grammar of "docs/src/_ext/geovista_citations.py",
which the conventions test and the documentation build share.

"""

from __future__ import annotations

from dataclasses import dataclass
import difflib
import importlib.util
from pathlib import Path
import re
import sys
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from types import ModuleType

#: The section of the repository checks page that documents this check.
CHECK = "spec-renumbering"

#: The repository root.
ROOT = Path(__file__).parents[2]

#: How alike the text of two sections must be to pair them, once their titles
#: have failed to: enough that a renamed section finds itself, and two that merely
#: share a subject do not.
LIKENESS = 0.6


def _load(path: Path, name: str) -> ModuleType:
    """Load a module by path, reusing a copy already registered from it."""
    registered = sys.modules.get(name)
    if registered is not None and Path(registered.__file__).resolve() == path.resolve():
        return registered
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


#: The citation grammar, shared with the conventions test and the build.
grammar = _load(
    ROOT / "docs" / "src" / "_ext" / "geovista_citations.py", "geovista_citations"
)

#: The link a finding ends with, to this check's section.
breadcrumb = _load(Path(__file__).parent / "breadcrumb.py", "breadcrumb")


@dataclass(frozen=True)
class Section:
    """One numbered section of a specification.

    Attributes
    ----------
    anchor : str
        Its anchor, e.g. ``typing-spec-3-2``.
    title : str
        Its heading, less the number.
    body : str
        The text beneath the heading, up to the next anchor, less any code.

    """

    anchor: str
    title: str
    body: str


@dataclass(frozen=True)
class Fate:
    """What became of a section on the base branch.

    Attributes
    ----------
    kind : {"kept", "moved", "removed"}
        Kept under its own anchor, moved to another, or gone.
    anchor : str or None
        The anchor it is under now, or ``None`` when it was removed.
    title : str
        Its title on the base branch, which a finding names it by.

    """

    kind: Literal["kept", "moved", "removed"]
    anchor: str | None
    title: str


def sections(text: str) -> dict[str, Section]:
    """Read a specification's sections, keyed by anchor, in the order written."""
    found: dict[str, Section] = {}
    lines = [line for _, line in grammar.read_lines(text)]
    current: tuple[str, str] | None = None
    body: list[str] = []
    for index, line in enumerate(lines):
        anchor = grammar.ANCHOR.match(line)
        heading = (
            grammar.HEADING.match(lines[index + 1]) if index + 1 < len(lines) else None
        )
        if anchor is not None and heading is not None:
            if current is not None:
                found[current[0]] = Section(*current, "\n".join(body).strip())
            current, body = (f"{anchor['slug']}-{anchor['num']}", heading["title"]), []
            continue
        if current is not None and not grammar.HEADING.match(line):
            body.append(line)
    if current is not None:
        found[current[0]] = Section(*current, "\n".join(body).strip())
    return found


def _plain(title: str) -> str:
    """Spell a title without case or punctuation, as a title style sweep leaves it."""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def pair(base: dict[str, Section], head: dict[str, Section]) -> dict[str, Fate]:
    """Pair each section on the base branch with its counterpart, if it has one.

    Sections pair by title first, then those left over by the likeness of their
    text, best pair first, which is what finds a section renamed as it moved.

    Parameters
    ----------
    base, head : dict
        The sections of the specification on the base branch and now.

    Returns
    -------
    dict
        The fate of each section on the base branch, keyed by its anchor there.

    """
    paired: dict[str, str] = {}
    free = list(head)
    for anchor, section in base.items():
        titled = [
            other
            for other in free
            if _plain(head[other].title) == _plain(section.title)
        ]
        if titled:
            chosen = anchor if anchor in titled else titled[0]
            paired[anchor] = chosen
            free.remove(chosen)
    likely = sorted(
        (
            (
                difflib.SequenceMatcher(None, base[old].body, head[new].body).ratio(),
                old,
                new,
            )
            for old in base
            if old not in paired and base[old].body
            for new in free
            if head[new].body
        ),
        reverse=True,
    )
    for likeness, old, new in likely:
        if likeness < LIKENESS:
            break
        if old not in paired and new in free:
            paired[old] = new
            free.remove(new)
    fates: dict[str, Fate] = {}
    for anchor, section in base.items():
        new = paired.get(anchor)
        if new is None:
            fates[anchor] = Fate("removed", None, section.title)
        else:
            fates[anchor] = Fate(
                "kept" if new == anchor else "moved", new, section.title
            )
    return fates


#: An item of a numbered list, opening at the left margin.
ITEM = re.compile(r"^(?P<number>\d+)\.\s+(?P<rest>\S.*)$")

#: A run of bold text, which may wrap.
BOLD = re.compile(r"\*\*(?P<text>.+?)\*\*", flags=re.DOTALL)

#: The statuses an open item opens with, before its title.
STATES = frozenset({"Open", "Resolved", "Deferred", "Abandoned"})

#: The header of a roadmap table: its number, its scope, and somewhere a status.
ROADMAP = re.compile(r"^\|\s*#\s*\|\s*Scope\s*\|.*\bStatus\s*\|")


def numbered_items(text: str) -> dict[str, dict[str, Section]]:
    """Read every numbered item opening with a bold title, by section and number.

    Each is read as a :class:`Section` keyed by its number, titled by its bold
    title, the one after its status if it opens with one, with its text as the
    body, so that items pair as sections do.
    """
    found: dict[str, dict[str, Section]] = {}
    lines = [line for _, line in grammar.read_lines(text)]
    current = None
    for index, line in enumerate(lines):
        anchor = grammar.ANCHOR.match(line)
        if anchor is not None:
            current = f"{anchor['slug']}-{anchor['num']}"
            continue
        item = ITEM.match(line)
        if current is None or item is None or not item["rest"].startswith("**"):
            continue
        body = [item["rest"]]
        for following in lines[index + 1 :]:
            if not following[:1].isspace() or not following.strip():
                break
            body.append(following.strip())
        joined = " ".join(body)
        bolds = [match["text"].replace("\n", " ") for match in BOLD.finditer(joined)]
        title = bolds[1] if bolds[0] in STATES and len(bolds) > 1 else bolds[0]
        number = item["number"]
        found.setdefault(current, {})[number] = Section(number, title, joined)
    return found


def roadmap_rows(text: str) -> dict[str, Section]:
    """Read every row of a roadmap table, keyed by its number and titled by scope."""
    found: dict[str, Section] = {}
    inside = False
    for _, line in grammar.read_lines(text):
        if ROADMAP.match(line):
            inside = True
            continue
        if not line.startswith("|"):
            inside = False
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if inside and cells and not set(cells[0]) <= set("-: "):
            found[cells[0]] = Section(cells[0], cells[1], cells[1])
    return found


def _split(old: str, new: str | None) -> bool:
    """Say whether row ``old`` became ``new`` by splitting, as 6 into 6a."""
    return new is not None and re.fullmatch(rf"{re.escape(old)}[a-z]", new) is not None


def frozen(base_text: str, head_text: str) -> list[str]:
    """Report each numbered item and roadmap row that moved or went.

    Parameters
    ----------
    base_text, head_text : str
        The specification on the base branch and now.

    Returns
    -------
    list of str
        One message per item or row whose number now names another, or nothing.

    """
    problems: list[str] = []
    fates = pair(sections(base_text), sections(head_text))
    base_items, head_items = numbered_items(base_text), numbered_items(head_text)
    for anchor, listed in base_items.items():
        fate = fates.get(anchor)
        if fate is None or fate.anchor is None:
            continue
        for number, item in pair(listed, head_items.get(fate.anchor, {})).items():
            if item.kind == "moved":
                problems.append(
                    f'{fate.title}, item {number} "{listed[number].title}" is now '
                    f"item {item.anchor}: append an item rather than insert it"
                )
            elif item.kind == "removed":
                problems.append(
                    f'{fate.title}, item {number} "{listed[number].title}" was '
                    "removed: mark it as no longer applying, in place"
                )
    base_rows, head_rows = roadmap_rows(base_text), roadmap_rows(head_text)
    for number, row in pair(base_rows, head_rows).items():
        split = any(_split(number, other) for other in head_rows)
        if row.kind == "moved" and not _split(number, row.anchor):
            problems.append(
                f'roadmap row {number} "{base_rows[number].title}" is now row '
                f"{row.anchor}: append a row rather than insert it"
            )
        elif row.kind == "removed" and not split:
            problems.append(
                f'roadmap row {number} "{base_rows[number].title}" was removed'
            )
    return problems


@dataclass(frozen=True)
class Finding:
    """A citation, on a line the pull request did not touch, of a section that left.

    Attributes
    ----------
    path : Path
        The citing file.
    line : int
        The citing line, 1-indexed.
    cited : str
        The citation as written.
    fate : Fate
        What became of the section it was written against.
    old : str
        The anchor it names, which no longer holds that section.

    """

    path: Path
    line: int
    cited: str
    fate: Fate
    old: str


def _number(anchor: str) -> str:
    """Spell an anchor's section number, as ``typing-spec-3-2`` is ``3.2``."""
    return grammar.LABEL.match(anchor)["num"].replace("-", ".")


def _citations(
    path: Path, line: str, names: object
) -> list[tuple[int, int, str, str, str]]:
    """Find a line's citations, as their span, text, anchor and kind of writing.

    A plain citation spans its text; a role spans its body, between the
    backticks, so that a rewrite can turn its display and its target together.
    """
    found: list[tuple[int, int, str, str, str]] = []
    plain, _ = grammar.prose(line)
    owner = names.owners.get(path)
    found.extend(
        (citation.start, citation.end, citation.text, citation.slug, "plain")
        for citation in grammar.scan(plain, names.signed, owner)
        if citation.slug is not None
    )
    for match in grammar.SPAN.finditer(line):
        if match["role"] is None or len(match["ticks"]) != 1:
            continue
        role = grammar.section_role(match["role"].strip("{}:"), match["body"], names)
        if role is not None:
            shown, target = role
            found.append(
                (
                    match.start("body"),
                    match.end("body"),
                    shown or target,
                    target,
                    "role",
                )
            )
    return found


def stale(
    texts: dict[Path, str],
    fates: dict[str, Fate],
    names: object,
    changed: dict[Path, set[int]],
) -> list[Finding]:
    """Find each untouched citation of a section that moved or went.

    Parameters
    ----------
    texts : dict
        The corpus, each file's text keyed by its path.
    fates : dict
        What became of each section of the specifications that changed.
    names : Namespace
        The citation grammar of the specifications as they are now.
    changed : dict
        The lines the pull request changed, keyed by path.

    Returns
    -------
    list of Finding
        In the order of the corpus and of each file's lines.

    """
    findings: list[Finding] = []
    for path, text in texts.items():
        touched = changed.get(path, set())
        for number, line in grammar.source_lines(path, text):
            if number in touched:
                continue
            for _, _, cited, anchor, _ in _citations(path, line, names):
                fate = fates.get(anchor)
                if fate is not None and fate.kind != "kept":
                    findings.append(Finding(path, number, cited, fate, anchor))
    return findings


def describe(finding: Finding, root: Path, now: dict[str, Section]) -> str:
    """Say what a stale citation was written against, and what became of it."""
    where = (
        finding.path.relative_to(root)
        if finding.path.is_relative_to(root)
        else (finding.path)
    )
    head = (
        f'{where.as_posix()}:{finding.line}: {finding.cited} was "{finding.fate.title}"'
    )
    if finding.fate.kind == "moved":
        return f"{head}, which is now {grammar.SECTION}{_number(finding.fate.anchor)}"
    sign = f"{grammar.SECTION}{_number(finding.old)}"
    later = now.get(finding.old)
    return f"{head}, which was removed; {sign} is " + (
        f'now "{later.title}"' if later is not None else "no longer a section"
    )


def rewrite(
    text: str, path: Path, fates: dict[str, Fate], names: object, lines: set[int]
) -> str:
    """Move each citation of a moved section, on the lines given, to its new number.

    A citation of a removed section has no new number, and is left as written.
    """
    out = text.splitlines(keepends=True)
    for number, line in grammar.source_lines(path, text):
        if number not in lines:
            continue
        edits = []
        for start, end, _, anchor, kind in _citations(path, line, names):
            fate = fates.get(anchor)
            if fate is None or fate.kind != "moved":
                continue
            new = _number(fate.anchor)
            if kind == "plain":
                replaced = re.sub(r"\d+(?:\.\d+)*$", new, line[start:end])
            else:
                targeted = grammar.TARGETED.match(line[start:end])
                shown = re.sub(r"\d+(?:\.\d+)*$", new, targeted["text"])
                replaced = f"{shown} <{fate.anchor}>"
            edits.append((start, end, replaced))
        edited = line
        for start, end, replaced in sorted(edits, reverse=True):
            edited = edited[:start] + replaced + edited[end:]
        ending = out[number - 1][len(out[number - 1].rstrip("\r\n")) :]
        out[number - 1] = edited + ending
    return "".join(out)

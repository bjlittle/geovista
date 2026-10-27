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

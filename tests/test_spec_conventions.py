# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests holding the design specifications to their conventions.

Each assertion is one item of the list in docs spec §3.5, and the triggers are
the roadmap's, in docs spec §4. A specification keys an anchor to every numbered
heading, a citation carries its section sign and names an anchor that exists, a
``{ref}`` role displays the section it opens, and a status names the work that
produced it.

The corpus is derived from the repository rather than declared, so a file is
governed from the day it lands rather than from the day somebody remembers to
list it. It is every UTF-8 file beneath the repository root, less the trees in
:data:`PRUNED`, each named with its reason. Nothing here needs ``sphinx``, a
build or a network, so like ``tests/docs/test_readingtime_coverage.py`` this
module never skips.

Each rule is a function of a file and its text returning one message per fault,
so that a fixture can show the rule firing and the repository test show it
holding. Code is skipped, fenced and inline, which is what lets a specification
quote the rules it is held to. This module sits inside its own corpus, so its
fixtures build the section sign rather than write it, and cite a ``demo spec``
that no document declares. Either, written literally, would be a citation it
governs.

"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

#: The repository root, beneath which the corpus is derived.
REPO = Path(__file__).parents[1]

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
            if entered(name) and (relative / name).as_posix() not in PRUNED
        ]
        for name in files:
            path = here / name
            try:
                found[path] = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
    return dict(sorted(found.items()))


def read_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield the lines of markdown that sit outside a fenced code block.

    The opening rail is remembered rather than counted, as in ``tephpy``'s
    citation grammar: a block opened with four backticks may quote one opened
    with three, so a fence closes only on a rail of the same character, at least
    as long, and carrying no info string.

    Parameters
    ----------
    text : str
        The document.

    Yields
    ------
    tuple of (int, str)
        The 1-indexed line number, and the line.

    """
    rail: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        fence = FENCE.match(line)
        if fence is not None:
            found = fence["rail"]
            if rail is None:
                rail = found
                continue
            if (
                found[0] == rail[0]
                and len(found) >= len(rail)
                and not fence["info"].strip()
            ):
                rail = None
                continue
        if rail is None:
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


def where(path: Path, number: int) -> str:
    """Locate a line as ``path:line``, relative to the repository when inside it."""
    name = path.relative_to(REPO) if path.is_relative_to(REPO) else path
    return f"{name.as_posix()}:{number}"


@pytest.fixture(scope="module")
def specs() -> list[Path]:
    """Gather the specifications of this repository."""
    return specifications()


@pytest.fixture(scope="module")
def names(specs) -> Namespace:
    """Read the namespace those specifications declare."""
    return namespace(specs)


@pytest.fixture(scope="module")
def texts() -> dict[Path, str]:
    """Gather the corpus of this repository."""
    return corpus()


def demo(tmp_path: Path, body: str) -> tuple[Path, Namespace]:
    """Write a specification declaring the ``demo spec`` prefix, and read it."""
    path = tmp_path / "2026-01-01-demo-design.md"
    banner = f"- **Citation prefix:** `demo spec {SECTION}{ELLIPSIS}`\n\n"
    path.write_text(banner + body, encoding="utf-8")
    return path, namespace([path])


DEMO = "(demo-spec-1)=\n## 1. Purpose\n\n(demo-spec-2)=\n## 2. Design\n"


def test_fenced_blocks_are_skipped():
    """A fence quoting a shorter fence stays open across the inner rail."""
    text = "a\n````markdown\n```\n(demo-spec-9)=\n```\n````\nb\n"

    assert [line for _, line in read_lines(text)] == ["a", "b"]


def test_inline_code_is_blanked_and_roles_are_collected():
    """A role quoted inside a longer span is code, not a role."""
    line = (
        f"{{ref}}`{SECTION}1 <demo-spec-1>` and "
        f"`` {{ref}}`{SECTION}2 <demo-spec-1>` `` and ``demo spec 3``"
    )

    plain, roles = prose(line)

    assert roles == [("ref", f"{SECTION}1 <demo-spec-1>")]
    assert plain.strip(" and") == ""
    assert len(plain) == len(line)


def test_a_prefix_carries_across_a_run_and_no_further(tmp_path):
    """A comma or solidus joins a run; a full stop ends it."""
    _, names = demo(tmp_path, DEMO)
    text = f"demo spec {SECTION}1, {SECTION}2. Then {SECTION}1."

    assert [c.slug for c in scan(text, names.signed, None)] == [
        "demo-spec-1",
        "demo-spec-2",
        None,
    ]
    assert [c.slug for c in scan(text, names.signed, "other-spec")][-1] == (
        "other-spec-1"
    )


def test_a_section_sign_without_a_number_is_no_citation(tmp_path):
    """Legal style puts a space after the sign; a citation never does."""
    _, names = demo(tmp_path, DEMO)
    text = f"{SECTION} 5, {SECTION}{ELLIPSIS} and demo spec {SECTION}x"

    assert list(scan(text, names.signed, None)) == []


def test_only_markdown_fences_are_skipped():
    """A reStructuredText code block is read, so a counterexample there is code."""
    text = ".. code-block:: text\n\n    demo spec 1\n"

    assert list(source_lines(Path("page.rst"), text))[-1] == (3, "    demo spec 1")


def test_corpus_reads_the_tree_it_is_given(tmp_path):
    """The walk prunes tooling state and the named trees, and drops binaries."""
    for name in (".git", ".github", "docs/_build", "docs/src/developer/plans", "src"):
        (tmp_path / name).mkdir(parents=True)
        (tmp_path / name / "file.txt").write_text("text\n", encoding="utf-8")
    (tmp_path / "src" / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")

    found = {path.relative_to(tmp_path).as_posix() for path in corpus(tmp_path)}

    assert found == {".github/file.txt", "src/file.txt"}


def test_the_collection_is_not_empty(specs):
    """A gate that finds no specification passes by never having looked."""
    found = {spec.name for spec in specs}

    assert "2026-10-06-published-specs-design.md" in found
    assert "2026-10-06-type-coverage-design.md" in found


def test_the_corpus_holds_a_member_of_every_area_it_governs(texts):
    """Membership rather than a count, which would need re-measuring."""
    found = {path.relative_to(REPO).as_posix() for path in texts}

    for member in (
        ".github/workflows/ci-typing.yml",
        ".pre-commit-config.yaml",
        "docs/src/conf.py",
        "docs/src/developer/specs/2026-10-06-type-coverage-design.md",
        "pyproject.toml",
        "src/geovista/__init__.py",
        "tests/test_spec_conventions.py",
    ):
        assert member in found, f"{member} is missing from the corpus"


def test_the_corpus_excludes_the_pruned_trees(texts):
    """The plans above all: they are frozen, so a rule they fail stays failed."""
    found = {path.relative_to(REPO).as_posix() for path in texts}

    for name in PRUNED:
        assert not any(path.startswith(f"{name}/") for path in found), name


@pytest.mark.parametrize("name", PRUNED)
def test_every_pruned_name_is_well_formed(name):
    """A slash at either end would make the comparison silently prune nothing."""
    assert not name.startswith("/"), f"{name} has a leading slash"
    assert not name.endswith("/"), f"{name} has a trailing slash"
    if name in TRACKED:
        assert (REPO / name).is_dir(), f"{name} is tracked but is not a directory"


def test_the_namespace_holds_what_the_rules_read(specs, names):
    """Every rule below would pass on an empty namespace, so this one does not."""
    roles = [
        kind
        for spec in specs
        for _, line in read_lines(spec.read_text(encoding="utf-8"))
        for kind, _ in prose(line)[1]
    ]

    assert {"docs-spec-3-5", "typing-spec-3-4"} <= names.anchors
    assert {"docs-spec", "typing-spec"} <= names.prefixes
    assert "ref" in roles

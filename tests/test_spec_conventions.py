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


#: The banner line a specification declares its citation prefix on.
DECLARED = re.compile(
    rf"\*\*Citation prefix:\*\*\s*`(?P<prefix>[^`]+?)\s*{SECTION}{ELLIPSIS}`"
)


def pairing(path: Path, text: str) -> list[str]:
    """Find each numbered heading with no anchor, and each anchor with no heading."""
    lines = dict(read_lines(text))
    problems = []
    for number, line in lines.items():
        if HEADING.match(line) and not ANCHOR.match(lines.get(number - 1, "")):
            problems.append(f"{where(path, number)}: a numbered heading, unanchored")
        if ANCHOR.match(line) and not HEADING.match(lines.get(number + 1, "")):
            problems.append(f"{where(path, number)}: an anchor with no heading beneath")
    return problems


def keying(path: Path, text: str) -> list[str]:
    """Find each anchor keyed to the wrong section or carrying the wrong prefix."""
    lines = dict(read_lines(text))
    problems = []
    slugs = set()
    for number, line in lines.items():
        anchor = ANCHOR.match(line)
        if anchor is None:
            continue
        slugs.add(anchor["slug"])
        heading = HEADING.match(lines.get(number + 1, ""))
        if heading is not None and anchor["num"].replace("-", ".") != heading["num"]:
            problems.append(
                f"{where(path, number)}: anchor {anchor['slug']}-{anchor['num']} "
                f"sits above section {heading['num']}"
            )
    declared = next(
        (match for line in lines.values() if (match := DECLARED.search(line))), None
    )
    if declared is None:
        problems.append(f"{where(path, 1)}: no citation prefix is declared")
    elif slugs != {re.sub(r"\s+", "-", declared["prefix"].lower())}:
        problems.append(
            f"{where(path, 1)}: declares {declared['prefix']!r}, "
            f"but its anchors carry {sorted(slugs)}"
        )
    return problems


def shared(names: Namespace) -> list[str]:
    """Find each prefix that more than one specification owns."""
    owned = list(names.owners.values())
    return sorted({prefix for prefix in owned if owned.count(prefix) > 1})


def test_pairing_finds_each_unanchored_heading_and_stranded_anchor(tmp_path):
    """Both directions, because each catches a fault the other cannot see."""
    path, _ = demo(tmp_path, "## 1. Purpose\n\n(demo-spec-2)=\n\nprose\n")

    problems = pairing(path, path.read_text(encoding="utf-8"))

    assert [p.split(": ", 1)[1] for p in problems] == [
        "a numbered heading, unanchored",
        "an anchor with no heading beneath",
    ]


def test_keying_finds_a_drifted_anchor_and_a_foreign_prefix(tmp_path):
    """An anchor above the wrong heading still resolves, so only keying sees it."""
    body = "(demo-spec-1)=\n## 2. Design\n\n(other-spec-3)=\n## 3. X\n"
    path, _ = demo(tmp_path, body)

    problems = keying(path, path.read_text(encoding="utf-8"))

    assert len(problems) == 2
    assert "sits above section 2" in problems[0]
    assert "but its anchors carry" in problems[1]


def test_a_copied_specification_sharing_its_prefix_is_caught(tmp_path):
    """A copy that keeps its template's anchors keeps its prefix too."""
    first, _ = demo(tmp_path, DEMO)
    copy = tmp_path / "2026-01-02-copy-design.md"
    copy.write_text(first.read_text(encoding="utf-8"), encoding="utf-8")

    assert shared(namespace([first, copy])) == ["demo-spec"]


def test_every_specification_declares_a_prefix_of_its_own(names):
    """Two documents sharing a prefix would share every anchor too."""
    assert shared(names) == []


@pytest.mark.parametrize("spec", specifications(), ids=lambda path: path.name)
def test_every_numbered_heading_pairs_with_an_anchor(spec):
    """Pairing (item 1)."""
    problems = pairing(spec, spec.read_text(encoding="utf-8"))

    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("spec", specifications(), ids=lambda path: path.name)
def test_every_anchor_is_keyed_to_its_heading(spec):
    """Keying (item 2)."""
    problems = keying(spec, spec.read_text(encoding="utf-8"))

    assert not problems, "\n".join(problems)


def resolution(path: Path, text: str, names: Namespace) -> list[str]:
    """Find each citation naming an anchor that does not exist."""
    owner = names.owners.get(path)
    problems = []
    for number, line in source_lines(path, text):
        for citation in scan(prose(line)[0], names.signed, owner):
            if citation.slug is None:
                problems.append(
                    f"{where(path, number)}: {citation.text} names no document, "
                    "and this file owns no sections"
                )
            elif citation.slug not in names.anchors:
                problems.append(
                    f"{where(path, number)}: {citation.text} names {citation.slug}, "
                    "which no specification declares"
                )
    return problems


def form(path: Path, text: str, names: Namespace) -> list[str]:
    """Find each citation written without its section sign."""
    return [
        f"{where(path, number)}: {match[0]!r} has no section sign"
        for number, line in source_lines(path, text)
        for match in names.unsigned.finditer(prose(line)[0])
    ]


def paragraphs(lines: Iterable[tuple[int, str]]) -> Iterator[list[tuple[int, str]]]:
    """Group numbered lines into the runs a line wrap can join.

    A blank line ends a run, and so does a gap in the numbering, which is where a
    fence was skipped: joining across either would pair lines a reader never sees
    together.
    """
    run: list[tuple[int, str]] = []
    previous = 0
    for number, line in lines:
        if run and (not line.strip() or number != previous + 1):
            yield run
            run = []
        if line.strip():
            run.append((number, line))
        previous = number
    if run:
        yield run


def wrapped(path: Path, text: str, names: Namespace) -> list[str]:
    """Find each citation a line break separated from the prefix it should carry.

    The scan reads a line at a time, so a run wrapped after its comma reads its
    tail as a bare section number, which in a specification resolves, silently,
    to the containing document. Only a citation whose anchor changes when the wrap
    is undone is reported, as in ``tephpy``; a paragraph whose citation count
    changes cannot be paired, and is passed over.
    """
    owner = names.owners.get(path)
    problems = []
    for run in paragraphs(source_lines(path, text)):
        written = [
            (number, citation)
            for number, line in run
            for citation in scan(prose(line)[0], names.signed, owner)
        ]
        joined = " ".join(prose(line)[0].strip() for _, line in run)
        undone = list(scan(joined, names.signed, owner))
        if len(written) != len(undone):
            continue
        problems.extend(
            f"{where(path, number)}: {citation.text} reads as {citation.slug} here, "
            f"{unwrapped.slug} unwrapped"
            for (number, citation), unwrapped in zip(written, undone, strict=True)
            if citation.slug != unwrapped.slug
        )
    return problems


def test_resolution_finds_each_dangling_and_ownerless_citation(tmp_path):
    """A citation outside the collection must carry its prefix."""
    _, names = demo(tmp_path, DEMO)
    source = tmp_path / "module.py"
    text = f"# demo spec {SECTION}2 and demo spec {SECTION}7, then {SECTION}1\n"

    problems = resolution(source, text, names)

    assert len(problems) == 2
    assert "demo-spec-7, which no specification declares" in problems[0]
    assert "this file owns no sections" in problems[1]


def test_form_finds_each_citation_without_its_sign(tmp_path):
    """The sign is what separates a citation from a sentence holding a number."""
    _, names = demo(tmp_path, DEMO)
    text = "# demo spec 2.1, and ``demo spec 9`` quoted as code\n"

    problems = form(tmp_path / "module.py", text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        "'demo spec 2.1' has no section sign"
    ]


def test_wrapped_finds_a_run_that_a_line_break_cuts(tmp_path):
    """Both anchors exist, so only the wrap check sees the wrong one opened."""
    other = tmp_path / "2026-01-02-other-design.md"
    other.write_text(
        f"- **Citation prefix:** `other spec {SECTION}{ELLIPSIS}`\n\n"
        "(other-spec-2)=\n## 2. Other\n",
        encoding="utf-8",
    )
    path, _ = demo(tmp_path, DEMO + f"\nSee other spec {SECTION}2,\n{SECTION}2 too.\n")

    problems = wrapped(path, path.read_text(encoding="utf-8"), namespace([path, other]))

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"{SECTION}2 reads as demo-spec-2 here, other-spec-2 unwrapped"
    ]


def test_every_citation_resolves(texts, names):
    """Resolution (item 3)."""
    problems = [
        p for path, text in texts.items() for p in resolution(path, text, names)
    ]

    assert not problems, "\n".join(problems)


def test_no_citation_run_wraps_a_line(texts, names):
    """A run may not wrap, or its tail silently cites the containing document."""
    problems = [p for path, text in texts.items() for p in wrapped(path, text, names)]

    assert not problems, "\n".join(problems)


def test_every_citation_carries_its_sign(texts, names):
    """Form (item 4)."""
    problems = [p for path, text in texts.items() for p in form(path, text, names)]

    assert not problems, "\n".join(problems)


#: A role opened on a line that does not close it.
OPENED = re.compile(r"(?:\{ref\}|:ref:)`")


def agreement(path: Path, text: str, names: Namespace) -> list[str]:
    """Find each section role whose display text names another section."""
    owner = names.owners.get(path)
    problems = []
    for number, line in source_lines(path, text):
        plain, roles = prose(line)
        if OPENED.search(plain):
            problems.append(f"{where(path, number)}: a role broken across lines")
        for kind, body in roles:
            targeted = TARGETED.match(body)
            target = targeted["target"] if targeted else body.strip()
            label = LABEL.match(target)
            if kind != "ref" or label is None or label["prefix"] not in names.prefixes:
                continue
            display = targeted["text"] if targeted else ""
            cited = list(scan(display, names.signed, owner))
            if [c.slug for c in cited] != [target] or cited[0].text != display:
                problems.append(
                    f"{where(path, number)}: {display!r} displayed, {target} opened"
                )
            elif target not in names.anchors:
                problems.append(
                    f"{where(path, number)}: {target} is no specification's anchor"
                )
    return problems


def test_agreement_finds_a_role_opening_another_section(tmp_path):
    """Both strings of a role can be well formed and still disagree."""
    roles = (
        f"\nSee {{ref}}`{SECTION}1 <demo-spec-1>` and "
        f"{{ref}}`{SECTION}1 <demo-spec-2>` and {{ref}}`demo-spec-2`, and\n"
        f"{{ref}}`{SECTION}2\n<demo-spec-2>` broken.\n"
    )
    path, names = demo(tmp_path, DEMO + roles)

    problems = agreement(path, path.read_text(encoding="utf-8"), names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"'{SECTION}1' displayed, demo-spec-2 opened",
        "'' displayed, demo-spec-2 opened",
        "a role broken across lines",
    ]


def test_every_section_role_displays_its_target(texts, names):
    """Agreement (item 5)."""
    problems = [p for path, text in texts.items() for p in agreement(path, text, names)]

    assert not problems, "\n".join(problems)


LANDED = "\N{WHITE HEAVY CHECK MARK} landed"
#: The roadmap states and the open-item states of docs spec §3.6.
ROW_STATES = (LANDED, "in progress", "not started", "candidate")
ITEM_STATES = ("Resolved", "Abandoned", "Deferred", "Open")
TERMINAL = frozenset({LANDED, "Resolved", "Abandoned"})
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
#: A role naming work in this repository, or a link to an issue or pull request in
#: another.
REFERENCE = re.compile(
    r"\{(?:issue|pull)\}`\d+`"
    r"|\]\(https://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull)/\d+\)"
)
ITEM = re.compile(r"^\d+\.\s+\*\*(?P<state>[^*]+)\*\*(?P<rest>.*)$")


def sections(text: str) -> dict[str, list[tuple[int, str]]]:
    """Group a specification's lines by the title of the section holding them."""
    found: dict[str, list[tuple[int, str]]] = {}
    title = None
    for number, line in read_lines(text):
        heading = HEADING.match(line)
        if heading is not None:
            title = heading["title"]
            found.setdefault(title, [])
        elif title is not None:
            found[title].append((number, line))
    return found


def carried(rest: str) -> str:
    """Read the parenthetical a status opens with, balanced so a link survives."""
    text = rest.lstrip()
    if not text.startswith("("):
        return ""
    depth = 0
    for index, char in enumerate(text):
        depth += {"(": 1, ")": -1}.get(char, 0)
        if depth == 0:
            return text[1:index]
    return text[1:]


def statuses(text: str) -> Iterator[tuple[int, str]]:
    """Yield each roadmap Status cell, and each open item with its lines joined."""
    found = sections(text)
    rows = [(n, line) for n, line in found.get("Roadmap", []) if line.startswith("|")]
    if rows:
        cells = [cell.strip() for cell in rows[0][1].strip().strip("|").split("|")]
        column = cells.index("Status")
        for number, line in rows[2:]:
            yield number, line.strip().strip("|").split("|")[column].strip()
    item: list[str] = []
    start = 0
    for number, line in [*found.get("Open items", []), (0, "")]:
        if ITEM.match(line) or not line.strip():
            if item:
                yield start, " ".join(item)
            item, start = ([line.strip()], number) if ITEM.match(line) else ([], 0)
        elif item:
            item.append(line.strip())


def status(path: Path, text: str) -> list[str]:
    """Find each status outside the vocabulary, or terminal and unevidenced."""
    problems = []
    for number, written in statuses(text):
        item = ITEM.match(written)
        if item is not None:
            state, rest = item["state"].strip(), item["rest"]
            states = ITEM_STATES
        else:
            state = next((s for s in ROW_STATES if written.startswith(s)), written)
            rest, states = written[len(state) :], ROW_STATES
        if state not in states:
            problems.append(f"{where(path, number)}: {state!r} is not a status")
        elif state in TERMINAL:
            evidence = carried(rest)
            if not (DATE.search(evidence) and REFERENCE.search(evidence)):
                problems.append(
                    f"{where(path, number)}: {state} carries no date and reference"
                )
    return problems


def test_status_finds_an_unknown_state_and_unevidenced_terminals(tmp_path):
    """A terminal status needs its date and its reference, and nothing else does."""
    roadmap = (
        "(demo-spec-1)=\n## 1. Roadmap\n\n| # | Status |\n|---|---|\n"
        f"| 1 | {LANDED} (2026-01-01, {{pull}}`1`) |\n"
        f"| 2 | {LANDED} (2026-01-01) |\n| 3 | shipped |\n| 4 | candidate |\n\n"
        "(demo-spec-2)=\n## 2. Open items\n\n"
        "1. **Resolved** (2026-01-01, [x](https://github.com/o/r/issues/1)) - **A.**\n"
        "2. **Resolved** (no date,\n   {issue}`2`) - **B.**\n"
        "3. **Open** - **C.**\n"
    )
    path, _ = demo(tmp_path, roadmap)

    problems = status(path, path.read_text(encoding="utf-8"))

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"{LANDED} carries no date and reference",
        "'shipped' is not a status",
        "Resolved carries no date and reference",
    ]


@pytest.mark.parametrize("spec", specifications(), ids=lambda path: path.name)
def test_every_status_is_in_the_vocabulary_and_evidenced(spec):
    """Status (item 7)."""
    text = spec.read_text(encoding="utf-8")
    problems = status(spec, text)

    assert list(statuses(text)), f"{spec.name} has no roadmap and no open items"
    assert not problems, "\n".join(problems)

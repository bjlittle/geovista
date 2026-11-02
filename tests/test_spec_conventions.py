# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests holding the design specifications to their conventions.

Each assertion is one item of the list in docs spec §3.5, and the triggers are
the roadmap's, in docs spec §4. A specification keys an anchor to every numbered
heading, a citation carries its section sign and names an anchor that exists, a
section is cited in plain text rather than by a role, and a status names the work
that produced it.

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

import ast
import contextlib
from datetime import date
from fnmatch import fnmatch
import importlib.util
import io
from pathlib import Path
import re
import sys
import tokenize
import tomllib
from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping
    from types import ModuleType

#: The section of the repository checks page that documents this check.
CHECK = "spec-conventions"

#: The repository root, beneath which the corpus is derived.
REPO = Path(__file__).parents[1]

#: The published specifications.
SPECS = REPO / "docs" / "src" / "developer" / "specs"

#: The citation grammar, shared with the documentation build, and loaded by path
#: as "docs/src/_ext" is no package.
GRAMMAR = REPO / "docs" / "src" / "_ext" / "geovista_citations.py"


def _load(path: Path) -> ModuleType:
    """Load the grammar, registered first, as its dataclasses look it up by name.

    A copy already registered from the same file is reused, since a second load
    would be a second module, whose dataclasses never equal the first's.
    """
    registered = sys.modules.get("geovista_citations")
    if registered is not None and Path(registered.__file__).resolve() == path.resolve():
        return registered
    spec = importlib.util.spec_from_file_location("geovista_citations", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


citations = _load(GRAMMAR)

SECTION = citations.SECTION
ELLIPSIS = citations.ELLIPSIS
PRUNED = citations.PRUNED
TRACKED = citations.TRACKED
ANCHOR = citations.ANCHOR
HEADING = citations.HEADING
FENCE = citations.FENCE
LABEL = citations.LABEL
Citation = citations.Citation
Namespace = citations.Namespace
specifications = citations.specifications
corpus = citations.corpus
read_lines = citations.read_lines
source_lines = citations.source_lines
prose = citations.prose
namespace = citations.namespace
scan = citations.scan
section_role = citations.section_role
alternation = citations.alternation
NUMBER = citations.NUMBER
GAP = citations.GAP
MEMBER = citations.MEMBER


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
    """Pairing (item 1).

    Holds docs spec §2 decision 3.
    """
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
                continue
            # a range names both its ends, and each is checked (items spec §3.1)
            problems.extend(
                f"{where(path, number)}: {citation.text} names {slug}, "
                "which no specification declares"
                for slug in (citation.slug, *citation.ends)
                if slug not in names.anchors
            )
    return problems


def form(path: Path, text: str, names: Namespace) -> list[str]:
    """Find each citation written without its section sign."""
    return [
        f"{where(path, number)}: {match[0]!r} has no section sign"
        for number, line in source_lines(path, text)
        for match in names.unsigned.finditer(prose(line)[0])
    ]


#: The blockquote markers opening a line of markdown, nested ones included, and
#: the marker of a list item that opens with a quote.
QUOTE = re.compile(
    r"^[^\S\n]*(?P<item>(?:[-*+]|\d{1,9}[.)])[^\S\n]+)?(?P<markers>(?:>[^\S\n]?)+)"
)

#: The suffixes of the files whose comments open at a ``#`` and run to the line end.
COMMENTED = frozenset({".cfg", ".py", ".pyi", ".sh", ".toml", ".yaml", ".yml"})

#: Where a comment opens outside Python: a ``#`` that opens the line or follows a
#: space, which is what YAML and TOML require of one.
HASH = re.compile(r"(?:^|(?<=[^\S\n]))#")

#: The marker that opens the text of a comment, ``#:`` included.
MARKER = re.compile(r"#+:?[^\S\n]?")


def comment_columns(path: Path, text: str) -> dict[int, int]:
    """Find the column each comment opens at, by line, in a file that has them.

    Python is tokenized, so a ``#`` inside a string opens nothing. Any other
    commented file, and a Python file that does not tokenize, falls back on
    :data:`HASH`.
    """
    if path.suffix not in COMMENTED:
        return {}
    if path.suffix in {".py", ".pyi"}:
        with contextlib.suppress(tokenize.TokenError, SyntaxError):
            return {
                token.start[0]: token.start[1]
                for token in tokenize.generate_tokens(io.StringIO(text).readline)
                if token.type == tokenize.COMMENT
            }
    return {
        number: found.start()
        for number, line in enumerate(text.splitlines(), start=1)
        if (found := HASH.search(line)) is not None
    }


def paragraphs(
    lines: Iterable[tuple[int, str]],
    *,
    markdown: bool = False,
    comments: Mapping[int, int] | None = None,
) -> Iterator[list[tuple[int, str]]]:
    """Group numbered lines into the runs a line wrap can join.

    A blank line ends a run, and so does a gap in the numbering, which is where a
    fence was skipped: joining across either would pair lines a reader never sees
    together. Markdown is read without its blockquote markers, which a reader
    never sees either. A quote that opens or deepens starts a block of its own, and
    so does a list item opening with one, so either ends the run; a line quoted
    less deeply continues it, as a lazy continuation line does. Elsewhere a comment,
    found at the column ``comments`` gives for its line, is read without its ``#``.
    It is a text apart from the code beside it, so a run ends where comment gives
    way to code or code to comment, and a comment trailing a line of code opens a
    run that the comment lines below it continue.
    """
    run: list[tuple[int, str]] = []
    previous = depth = 0
    commented = False
    for number, line in lines:
        pieces, level, item = [(line, False)], 0, False
        if markdown:
            if (quote := QUOTE.match(line)) is not None:
                pieces = [(line[quote.end() :], False)]
                level, item = quote["markers"].count(">"), quote["item"] is not None
        elif comments and number in comments:
            column = comments[number]
            found = MARKER.match(line, column)
            note = (line[found.end() if found else column :], True)
            pieces = [(line[:column], False), note] if line[:column].strip() else [note]
        for text, comment in pieces:
            if run and (
                not text.strip()
                or number != previous + 1
                or level > depth
                or item
                or comment != commented
            ):
                yield run
                run = []
            if text.strip():
                depth = max(depth, level) if run else level
                run.append((number, text))
            previous, commented = number, comment
    if run:
        yield run


def runs(path: Path, text: str) -> Iterator[list[tuple[int, str]]]:
    """Group the lines of a file into paragraphs, as its syntax has them read."""
    return paragraphs(
        source_lines(path, text),
        markdown=path.suffix == ".md",
        comments=comment_columns(path, text),
    )


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
    for run in runs(path, text):
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
            f"{where(path, number)}: {citation.text} reads as "
            f"{citation.slug or 'no document'} here, {unwrapped.slug} unwrapped"
            for (number, citation), unwrapped in zip(written, undone, strict=True)
            if citation.slug != unwrapped.slug
        )
    return problems


#: The dash of a range, with no space on either side, though a line may break there.
DASH = re.compile(r"\n?[-\N{EN DASH}\N{EM DASH}]\n?")

#: A far end written after the dash of a range as a number, with no section sign.
SIGNLESS = re.compile(rf"{DASH.pattern}(?P<num>\d+(?:\.\d+)*)\b")


def ranged(path: Path, text: str, names: Namespace) -> list[str]:
    """Find each range whose far end is not a citation in its own right.

    A dash is no separator, so the run ends at it and a bare far end means the
    containing document, which in a specification resolves without complaint, while
    a far end written as a plain number is no citation at all, and nothing resolves
    it. Each end of a range is therefore a citation of its own, the rule ``tephpy``
    writes down and does not check. A paragraph is read whole, so a range a wrap
    has split is still a range: the dash opens one when nothing but a line break
    stands between it and either end. A space anywhere in that gap, one that ends a
    line included, makes the dash punctuation. The indentation that opens a line
    does not count, since a list item, a quote and a docstring all indent their
    continuation lines. Scanning with no owner leaves a citation unresolved unless
    a prefix was written on it or carried to it, which is what tells the ends apart.
    """
    problems = []
    for run in runs(path, text):
        source = "\n".join(prose(line)[0].lstrip() for _, line in run)
        previous: tuple[re.Match[str], Citation] | None = None
        for match, citation in zip(
            names.signed.finditer(source),
            scan(source, names.signed, None),
            strict=True,
        ):
            if previous is not None:
                before, near = previous
                if (
                    near.slug is not None
                    and match["bare"] is not None
                    and DASH.fullmatch(source[before.end() : match.start()])
                ):
                    span = source[before.start() : match.end()]
                    number = run[0][0] + source.count("\n", 0, match.start())
                    problems.append(
                        f"{where(path, number)}: {span!r} opens at {near.slug}, "
                        "and its far end has no prefix"
                    )
            signless = SIGNLESS.match(source, match.end())
            if signless is not None:
                span = source[match.start() : signless.end()]
                number = run[0][0] + source.count("\n", 0, signless.start("num"))
                problems.append(
                    f"{where(path, number)}: {span!r} ends without a section sign"
                )
            previous = match, citation
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


def test_resolution_checks_both_ends_of_a_range(tmp_path):
    """A range names its far end too, so a far end past the roadmap is reported.

    Holds items spec §2 decision 10.
    """
    roadmap = "| # | Scope | Status |\n|---|---|---|\n| 1 | x | candidate |\n"
    _, names = demo(tmp_path, f"{DEMO}\n{roadmap}")
    text = f"# rows 1 to 2 of demo spec {SECTION}2, row 1 of {SECTION}2\n"

    problems = resolution(tmp_path / "module.py", text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        (
            f"rows 1 to 2 of demo spec {SECTION}2 names demo-spec-2-row-2, "
            "which no specification declares"
        )
    ]


def test_form_finds_each_citation_without_its_sign(tmp_path):
    """The sign is what separates a citation from a sentence holding a number."""
    _, names = demo(tmp_path, DEMO)
    text = "# demo spec 2.1, and ``demo spec 9`` quoted as code\n"

    problems = form(tmp_path / "module.py", text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        "'demo spec 2.1' has no section sign"
    ]


#: The word an item, a row or a decision is named by, singular only: a plural names
#: no one of them.
KIND = r"decision|item|row"


def near_misses(path: Path, text: str, names: Namespace) -> list[str]:
    """Find a citation in a form the grammar does not read (items spec §7 item 1).

    None of the three forms below is linked or checked, so each reads as prose rather
    than a citation, and review passes it by. A known prefix followed directly by
    ``row``, ``item`` or ``decision`` carries no section sign at all; a section sign
    followed by a comma and one of those words carries one the grammar cannot read
    past the comma; and ``decision`` named with its section after ``of`` uses the word
    order the grammar accepts only for an item or a row. Each is reported with the
    citation it should become, read without regard to case, as a sentence may open on
    one. An item or a row read after the comma is not reported if it opens a citation
    of its own, naming its section after ``of``, since the comma there only parts two
    citations in a list.

    Parameters
    ----------
    path : Path
        The file.
    text : str
        Its text.
    names : Namespace
        The known prefixes.

    Returns
    -------
    list of str
        One message per fault, located with :func:`where`.

    """
    known = alternation(names.prefixes)
    missing_sign = re.compile(
        rf"(?<![\w-])(?P<prefix>{known}){GAP}"
        rf"(?P<kind>{KIND}){GAP}(?P<member>{MEMBER})",
        flags=re.IGNORECASE,
    )
    comma_form = re.compile(
        rf"{SECTION}(?P<num>{NUMBER}),[^\S\n]*(?P<kind>{KIND}){GAP}(?P<member>{MEMBER})",
        flags=re.IGNORECASE,
    )
    # an item or a row after the comma may open a citation of its own, as
    # ``row 6 of §9`` does in ``§8, row 6 of §9``: that comma only parts two
    # citations in a list, so each member is read ahead before it is reported
    pre_form = re.compile(
        rf"{GAP}of{GAP}(?:{known}[^\S\n]*)?{SECTION}{NUMBER}", flags=re.IGNORECASE
    )
    decision_of = re.compile(
        rf"\bdecision{GAP}(?P<member>{MEMBER}){GAP}of{GAP}"
        rf"(?:(?P<prefix>{known})[^\S\n]*)?{SECTION}(?P<num>{NUMBER})",
        flags=re.IGNORECASE,
    )
    problems = []
    for number, line in source_lines(path, text):
        plain, _ = prose(line)
        for match in missing_sign.finditer(plain):
            kind = match["kind"].lower()
            fix = f"{match['prefix']} {SECTION}{ELLIPSIS} {kind} {match['member']}"
            problems.append(
                f"{where(path, number)}: {match[0]!r} carries no section sign at "
                f"all; write it as {fix!r}, with the section it names"
            )
        for match in comma_form.finditer(plain):
            kind = match["kind"].lower()
            if kind != "decision" and pre_form.match(plain, match.end()):
                continue
            if kind == "row":
                fix = f"row {match['member']} of {SECTION}{match['num']}"
            else:
                fix = f"{SECTION}{match['num']} {kind} {match['member']}"
            problems.append(
                f"{where(path, number)}: {match[0]!r} is a near-miss citation; "
                f"write {fix!r}"
            )
        for match in decision_of.finditer(plain):
            prefix = f"{match['prefix']} " if match["prefix"] else ""
            fix = f"{prefix}{SECTION}{match['num']} decision {match['member']}"
            problems.append(
                f"{where(path, number)}: {match[0]!r} is a near-miss citation; "
                f"write {fix!r}"
            )
    return problems


def test_near_misses_finds_each_form(tmp_path):
    """One of each near miss, beside three valid forms already read as citations.

    Holds items spec §2 decision 10.
    """
    _, names = demo(tmp_path, DEMO)
    text = (
        f"# demo spec item 9.\n"
        f"# demo spec {SECTION}2, item 3.\n"
        f"# decision 1 of demo spec {SECTION}2.\n"
        f"# Valid: demo spec {SECTION}2 item 3, item 3 of demo spec {SECTION}2, "
        f"and demo spec {SECTION}2 decision 1.\n"
    )
    path = tmp_path / "module.py"

    problems = near_misses(path, text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        (
            f"'demo spec item 9' carries no section sign at all; write it as "
            f"'demo spec {SECTION}{ELLIPSIS} item 9', with the section it names"
        ),
        f"'{SECTION}2, item 3' is a near-miss citation; write '{SECTION}2 item 3'",
        (
            f"'decision 1 of demo spec {SECTION}2' is a near-miss citation; "
            f"write 'demo spec {SECTION}2 decision 1'"
        ),
    ]


def test_near_misses_rewrites_a_comma_row_before_its_section(tmp_path):
    """A row never trails its section, so the fix reorders rather than drop a comma."""
    _, names = demo(tmp_path, DEMO)
    text = f"# See {SECTION}2, row 3 of the roadmap.\n"

    problems = near_misses(tmp_path / "module.py", text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"'{SECTION}2, row 3' is a near-miss citation; write 'row 3 of {SECTION}2'"
    ]


def test_near_misses_comma_form_reads_any_case(tmp_path):
    """A sentence may open on the word, as the corpus does, so case must not matter."""
    _, names = demo(tmp_path, DEMO)
    text = f"# {SECTION}8, Item 3 opens a sentence, and {SECTION}9, ROW 6 too.\n"

    problems = near_misses(tmp_path / "module.py", text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"'{SECTION}8, Item 3' is a near-miss citation; write '{SECTION}8 item 3'",
        f"'{SECTION}9, ROW 6' is a near-miss citation; write 'row 6 of {SECTION}9'",
    ]


def test_near_misses_passes_a_list_of_valid_citations(tmp_path):
    """A row or an item opening its own citation after a comma is no near miss."""
    _, names = demo(tmp_path, DEMO)
    text = (
        f"# item 3 of demo spec {SECTION}8, row 6 of demo spec {SECTION}9, "
        f"and decision 1 of demo spec {SECTION}2.\n"
    )

    problems = near_misses(tmp_path / "module.py", text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        (
            f"'decision 1 of demo spec {SECTION}2' is a near-miss citation; "
            f"write 'demo spec {SECTION}2 decision 1'"
        )
    ]


def test_no_citation_is_a_near_miss(texts, names):
    """Settles items spec §7 item 1 (#2804): every near-miss in the corpus is fixed."""
    problems = [
        p for path, text in texts.items() for p in near_misses(path, text, names)
    ]

    assert not problems, "\n".join(problems)


def paired(tmp_path: Path, body: str) -> tuple[Path, Namespace]:
    """Write the demonstration with ``body`` appended, beside a second specification."""
    other = tmp_path / "2026-01-02-other-design.md"
    other.write_text(
        f"- **Citation prefix:** `other spec {SECTION}{ELLIPSIS}`\n\n"
        "(other-spec-2)=\n## 2. Other\n",
        encoding="utf-8",
    )
    path, _ = demo(tmp_path, f"{DEMO}\n{body}\n")

    return path, namespace([path, other])


def rewrapped(tmp_path: Path, body: str) -> list[str]:
    """Run the wrap check over the demonstration with ``body`` appended to it."""
    path, names = paired(tmp_path, body)

    problems = wrapped(path, path.read_text(encoding="utf-8"), names)

    return [p.split(": ", 1)[1] for p in problems]


@pytest.mark.parametrize(
    "body",
    [
        f"See other spec {SECTION}2,\n{SECTION}2 too.",
        f"> See other spec {SECTION}2,\n> {SECTION}2 too.",
        f">> See other spec {SECTION}2,\n> > {SECTION}2 too.",
        f"> See other spec {SECTION}2,\n{SECTION}2 too.",
        f"- > See other spec {SECTION}2,\n  > {SECTION}2 too.",
    ],
    ids=["paragraph", "quote", "nested", "lazy", "listed"],
)
def test_wrapped_finds_a_run_that_a_line_break_cuts(tmp_path, body):
    """Both anchors exist, so only the wrap check sees the wrong one opened."""
    assert rewrapped(tmp_path, body) == [
        f"{SECTION}2 reads as demo-spec-2 here, other-spec-2 unwrapped"
    ]


@pytest.mark.parametrize(
    "body",
    [
        f"> See other spec {SECTION}2,\n>\n> {SECTION}2 too.",
        f"See other spec {SECTION}2,\n> {SECTION}2 too.",
        f"> See other spec {SECTION}2,\n>> {SECTION}2 too.",
        f"- > See other spec {SECTION}2,\n- > {SECTION}2 too.",
    ],
    ids=["quoted-paragraphs", "quote-opens", "quote-deepens", "next-item"],
)
def test_wrapped_joins_no_lines_that_markdown_keeps_apart(tmp_path, body):
    """A quote opening or deepening starts a block, so no run continues into it."""
    assert rewrapped(tmp_path, body) == []


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (
            f"See other spec {SECTION}2\N{EN DASH}{SECTION}1.",
            f"'other spec {SECTION}2\N{EN DASH}{SECTION}1' opens at other-spec-2",
        ),
        (
            f"See other spec {SECTION}2-{SECTION}1.",
            f"'other spec {SECTION}2-{SECTION}1' opens at other-spec-2",
        ),
        (
            f"See other spec {SECTION}2\N{EM DASH}{SECTION}1.",
            f"'other spec {SECTION}2\N{EM DASH}{SECTION}1' opens at other-spec-2",
        ),
        (
            f"See other spec {SECTION}2, {SECTION}3\N{EN DASH}{SECTION}1.",
            f"'{SECTION}3\N{EN DASH}{SECTION}1' opens at other-spec-3",
        ),
        (
            f"See other spec {SECTION}2\N{EN DASH}\n{SECTION}1.",
            f"'other spec {SECTION}2\N{EN DASH}\\n{SECTION}1' opens at other-spec-2",
        ),
        (
            f"See other spec {SECTION}2\n\N{EN DASH}{SECTION}1.",
            f"'other spec {SECTION}2\\n\N{EN DASH}{SECTION}1' opens at other-spec-2",
        ),
        (
            f"> See other spec {SECTION}2\N{EN DASH}\n> {SECTION}1.",
            f"'other spec {SECTION}2\N{EN DASH}\\n{SECTION}1' opens at other-spec-2",
        ),
        (
            f"See other spec {SECTION}2\N{EN DASH}\n {SECTION}1.",
            f"'other spec {SECTION}2\N{EN DASH}\\n{SECTION}1' opens at other-spec-2",
        ),
        (
            f"- See other spec {SECTION}2\N{EN DASH}\n  {SECTION}1.",
            f"'other spec {SECTION}2\N{EN DASH}\\n{SECTION}1' opens at other-spec-2",
        ),
    ],
    ids=[
        "en-dash",
        "hyphen",
        "em-dash",
        "carried",
        "split-after",
        "split-before",
        "quoted-split",
        "indented-continuation",
        "listed-continuation",
    ],
)
def test_ranged_finds_a_far_end_without_its_prefix(tmp_path, body, expected):
    """A dash ends the run, so a bare far end falls back to the demonstration."""
    path, names = paired(tmp_path, body)

    problems = ranged(path, path.read_text(encoding="utf-8"), names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"{expected}, and its far end has no prefix"
    ]


def test_ranged_reports_a_split_range_where_its_far_end_is(tmp_path):
    """The line reported holds the far end, which is the one to change."""
    path, names = paired(tmp_path, f"See other spec {SECTION}2\N{EN DASH}\n{SECTION}1.")

    problems = ranged(path, path.read_text(encoding="utf-8"), names)

    assert [p.split(": ", 1)[0].rsplit(":", 1)[1] for p in problems] == ["10"]


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (
            f"See other spec {SECTION}2\N{EN DASH}1.",
            f"'other spec {SECTION}2\N{EN DASH}1'",
        ),
        (f"See other spec {SECTION}2-1.", f"'other spec {SECTION}2-1'"),
        (f"See {SECTION}1\N{EN DASH}2.", f"'{SECTION}1\N{EN DASH}2'"),
        (
            f"See other spec {SECTION}2\N{EN DASH}\n1.",
            f"'other spec {SECTION}2\N{EN DASH}\\n1'",
        ),
    ],
    ids=["prefixed", "hyphen", "bare", "split"],
)
def test_ranged_finds_a_far_end_without_its_section_sign(tmp_path, body, expected):
    """A number after a range's dash is a far end that no other rule can see."""
    path, names = paired(tmp_path, body)

    problems = ranged(path, path.read_text(encoding="utf-8"), names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"{expected} ends without a section sign"
    ]


@pytest.mark.parametrize(
    "body",
    [
        f"See other spec {SECTION}2\N{EN DASH}other spec {SECTION}2.",
        f"See {SECTION}1\N{EN DASH}{SECTION}2.",
        f"See other spec {SECTION}2 \N{EM DASH} {SECTION}1 explains why.",
        f"See other spec {SECTION}2 \N{EN DASH} {SECTION}1 explains why.",
        f"See other spec {SECTION}2\N{EN DASH}\nother spec {SECTION}2.",
        f"See other spec {SECTION}2 \N{EN DASH}\n{SECTION}1 explains why.",
        f"See other spec {SECTION}2\N{EN DASH}\n\n{SECTION}1 opens a paragraph.",
        f"See other spec {SECTION}2-style rules.",
        f"See other spec {SECTION}2 \n\N{EN DASH}{SECTION}1 explains why.",
        f"See other spec {SECTION}2\N{EN DASH} \n{SECTION}1 explains why.",
        f"See other spec {SECTION}2\N{EN DASH}  \n{SECTION}1 explains why.",
    ],
    ids=[
        "both-ends",
        "bare",
        "spaced-em-dash",
        "spaced-en-dash",
        "split-whole",
        "split-spaced",
        "paragraphs",
        "hyphenated-word",
        "space-before-break",
        "space-after-dash",
        "hard-break",
    ],
)
def test_ranged_passes_a_range_written_whole_and_a_dash_as_punctuation(tmp_path, body):
    """A prefix on both ends, a bare range and a spaced dash are all well formed."""
    path, names = paired(tmp_path, body)

    assert ranged(path, path.read_text(encoding="utf-8"), names) == []


@pytest.mark.parametrize(
    ("name", "opening"),
    [
        ("module.py", "#"),
        ("module.py", "#:"),
        ("workflow.yml", "#"),
        ("module.py", "x = 1  #"),
        ("workflow.yml", "key: value  #"),
    ],
    ids=["python", "python-attribute", "yaml", "python-trailing", "yaml-trailing"],
)
def test_ranged_reads_a_comment_without_its_marker(tmp_path, name, opening):
    """A far end with no sign is no citation, so only the range check can see it."""
    _, names = paired(tmp_path, "")
    text = f"{opening} See other spec {SECTION}2\N{EN DASH}\n# 1 for both.\n"

    problems = ranged(tmp_path / name, text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"'other spec {SECTION}2\N{EN DASH}\\n1' ends without a section sign"
    ]


def test_wrapped_reads_a_comment_without_its_marker(tmp_path):
    """Outside the specifications a wrapped tail names no document at all."""
    _, names = paired(tmp_path, "")
    text = f"# See other spec {SECTION}2,\n# {SECTION}2 too.\n"

    problems = wrapped(tmp_path / "module.py", text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"{SECTION}2 reads as no document here, other-spec-2 unwrapped"
    ]


@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("workflow.yml", f"# See other spec {SECTION}2\N{EN DASH}\n1: one\n"),
        ("workflow.yml", f"# See other spec {SECTION}2\N{EN DASH}\n#\n# 1 for both.\n"),
        ("workflow.yml", f"key: v  # See other spec {SECTION}2\N{EN DASH}\n1: one\n"),
        (
            "module.py",
            f'x = """a # See other spec {SECTION}2\N{EN DASH}\n# 1 for both."""\n',
        ),
    ],
    ids=["code-follows", "bare-marker", "trailing-then-code", "hash-in-a-string"],
)
def test_ranged_joins_no_comment_to_code_or_across_a_bare_marker(tmp_path, name, text):
    """Comment and code are separate texts, and a ``#`` in a string opens no comment."""
    _, names = paired(tmp_path, "")

    assert ranged(tmp_path / name, text, names) == []


def test_every_citation_resolves(texts, names):
    """Resolution (item 3)."""
    problems = [
        p for path, text in texts.items() for p in resolution(path, text, names)
    ]

    assert not problems, "\n".join(problems)


def test_no_citation_run_wraps_a_line(texts, names):
    """Form (item 4): a wrapped run's tail silently cites the containing document."""
    problems = [p for path, text in texts.items() for p in wrapped(path, text, names)]

    assert not problems, "\n".join(problems)


def test_every_range_carries_its_prefix_on_both_ends(texts, names):
    """Form (item 4): a range's bare far end silently cites the containing document."""
    problems = [p for path, text in texts.items() for p in ranged(path, text, names)]

    assert not problems, "\n".join(problems)


def test_every_citation_carries_its_sign(texts, names):
    """Form (item 4).

    Holds docs spec §2 decision 4.
    """
    problems = [p for path, text in texts.items() for p in form(path, text, names)]

    assert not problems, "\n".join(problems)


#: A role opened on a line that does not close it.
OPENED = re.compile(r"(?:\{ref\}|:ref:)`")


def full_citation(target: str) -> str:
    """Spell an anchor as a citation carrying its prefix, as ``docs spec §3.2``."""
    label = LABEL.match(target)
    return (
        f"{label['prefix'].replace('-', ' ')} {SECTION}{label['num'].replace('-', '.')}"
    )


def suggestions(
    line: str, roles: list[tuple[re.Match[str], str, str]], names: Namespace, owner
) -> list[tuple[str, str, str]]:
    """Choose the plain citation each section role on a line should become.

    The roles are followed together, as an author following the advice would
    write them, and with the line's plain citations, since a role becoming a
    citation can carry its prefix into whatever comes next, a role or a plain
    citation alike. Each is its own text where, the line written so, that names
    its own section, and otherwise its full form, which nothing carried can
    change; so the choice settles once the full forms stop growing.

    Returns
    -------
    list of tuple of str
        For each role, and for each plain citation that must change, whether it
        is a ``role`` or ``plain``, its text as written, and its text to write.

    """
    items = [
        (m.start(), m.end(), display, target, "role") for m, display, target in roles
    ]
    items += [
        (c.start, c.end, c.text, c.slug, "plain")
        for c in scan(prose(line)[0], names.signed, owner)
        if c.slug is not None
    ]
    items.sort()
    chosen = [text or full_citation(target) for _, _, text, target, _ in items]
    while True:
        out, spans, cursor = [], [], 0
        for (start, end, _, target, _), text in zip(items, chosen, strict=True):
            out.append(line[cursor:start])
            begin = sum(map(len, out))
            out.append(text)
            spans.append((begin, begin + len(text), target))
            cursor = end
        out.append(line[cursor:])
        found = {
            (c.start, c.end, c.slug)
            for c in scan(prose("".join(out))[0], names.signed, owner)
        }
        wrong = [
            index
            for index, span in enumerate(spans)
            if span not in found and chosen[index] != full_citation(span[2])
        ]
        if not wrong:
            break
        for index in wrong:
            chosen[index] = full_citation(spans[index][2])
    return [
        (kind, text, written)
        for (_, _, text, _, kind), written in zip(items, chosen, strict=True)
        if kind == "role" or written != text
    ]


def section_roles(path: Path, text: str, names: Namespace) -> list[str]:
    """Find each role naming a section, which a plain citation replaces.

    A role is two strings, its display text and its target, which can disagree
    while each reads well. A plain citation is one string, which the build links
    to the section it names, so a section is cited in plain text. A role naming a
    label that is no section, such as a page's, is not a citation, and stays.
    Each is reported with the plain citation it should become, chosen with the
    line's other roles so that following every suggestion links each section.
    """
    owner = names.owners.get(path)
    problems = []
    for number, line in source_lines(path, text):
        plain, _ = prose(line)
        if OPENED.search(plain):
            problems.append(f"{where(path, number)}: a role broken across lines")
        roles = []
        for match in citations.SPAN.finditer(line):
            if match["role"] is None or len(match["ticks"]) != 1:
                continue
            role = section_role(match["role"].strip("{}:"), match["body"], names)
            if role is not None:
                roles.append((match, *role))
        chosen = suggestions(line, roles, names, owner) if roles else []
        for kind, cited, written in chosen:
            problems.append(
                f"{where(path, number)}: write {written!r} as plain text, "
                "which the build links"
                if kind == "role"
                else f"{where(path, number)}: then write {cited!r} as {written!r}, "
                "or it inherits the prefix before it"
            )
    return problems


def crossed(path: Path, text: str) -> list[str]:
    """Find each line of a specification that a code span crosses.

    Code is blanked a line at a time, so a span wrapped across a line break leaves
    a stray backtick on either side, and on the second line that backtick pairs
    with the next one, hiding whatever citation or role follows it from the
    grammar. A span therefore opens and closes on one line, which this makes loud.
    """
    return [
        f"{where(path, number)}: a code span crosses a line break"
        for number, line in read_lines(text)
        if "`" in prose(line)[0]
    ]


def test_section_roles_finds_each_role_naming_a_section(tmp_path):
    """A role is two strings that can disagree; a plain citation is one."""
    roles = "".join(
        [
            f"\nSee {{ref}}`{SECTION}1 <demo-spec-1>` and ",
            f":ref:`demo spec {SECTION}2 <demo-spec-2>`, ",
            "not {ref}`the gallery <gallery>` ",
            f"nor demo spec {SECTION}1, and\n",
            f"{{ref}}`{SECTION}2\n<demo-spec-2>` broken.\n",
        ]
    )
    path, names = demo(tmp_path, DEMO + roles)

    problems = section_roles(path, path.read_text(encoding="utf-8"), names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"write '{SECTION}1' as plain text, which the build links",
        f"write 'demo spec {SECTION}2' as plain text, which the build links",
        "a role broken across lines",
    ]


def test_section_roles_suggests_the_citation_its_target_needs(tmp_path):
    """Followed literally, the suggestion must link the role's own section."""
    other = tmp_path / "2026-01-02-other-design.md"
    other.write_text(
        f"- **Citation prefix:** `other spec {SECTION}{ELLIPSIS}`\n\n"
        "(other-spec-1)=\n## 1. Other\n",
        encoding="utf-8",
    )
    path, _ = demo(
        tmp_path,
        DEMO + f"\nSee {{ref}}`{SECTION}1 <other-spec-1>` and :ref:`demo-spec-2`.\n",
    )
    names = namespace([path, other])

    problems = section_roles(path, path.read_text(encoding="utf-8"), names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"write 'other spec {SECTION}1' as plain text, which the build links",
        f"write 'demo spec {SECTION}2' as plain text, which the build links",
    ]


@pytest.mark.parametrize("joined", [", ", "/"])
def test_section_roles_suggests_in_the_context_of_its_run(tmp_path, joined):
    """A bare number after another specification's citation inherits its prefix."""
    other = tmp_path / "2026-01-02-other-design.md"
    other.write_text(
        f"- **Citation prefix:** `other spec {SECTION}{ELLIPSIS}`\n\n"
        "(other-spec-1)=\n## 1. Other\n",
        encoding="utf-8",
    )
    line = f"\nSee other spec {SECTION}1{joined}{{ref}}`{SECTION}1 <demo-spec-1>`.\n"
    path, _ = demo(tmp_path, DEMO + line)
    names = namespace([path, other])

    problems = section_roles(path, path.read_text(encoding="utf-8"), names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"write 'demo spec {SECTION}1' as plain text, which the build links",
    ]


@pytest.mark.parametrize("joined", [", ", "/"])
def test_section_roles_suggests_a_lines_citations_together(tmp_path, joined):
    """Followed together, the suggestions must each still link their own section."""
    other = tmp_path / "2026-01-02-other-design.md"
    other.write_text(
        f"- **Citation prefix:** `other spec {SECTION}{ELLIPSIS}`\n\n"
        "(other-spec-1)=\n## 1. Other\n",
        encoding="utf-8",
    )
    first = f"{{ref}}`other spec {SECTION}1 <other-spec-1>`"
    line = f"\nSee {first}{joined}{{ref}}`{SECTION}1 <demo-spec-1>`.\n"
    path, _ = demo(tmp_path, DEMO + line)
    names = namespace([path, other])

    problems = section_roles(path, path.read_text(encoding="utf-8"), names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"write 'other spec {SECTION}1' as plain text, which the build links",
        f"write 'demo spec {SECTION}1' as plain text, which the build links",
    ]


@pytest.mark.parametrize("joined", [", ", "/"])
def test_section_roles_keeps_a_plain_citation_after_a_role_naming_its_section(
    tmp_path, joined
):
    """A role becoming a citation must not carry its prefix into the plain one after."""
    other = tmp_path / "2026-01-02-other-design.md"
    other.write_text(
        f"- **Citation prefix:** `other spec {SECTION}{ELLIPSIS}`\n\n"
        "(other-spec-1)=\n## 1. Other\n",
        encoding="utf-8",
    )
    line = f"\nSee {{ref}}`Elsewhere <other-spec-1>`{joined}{SECTION}1.\n"
    path, _ = demo(tmp_path, DEMO + line)
    names = namespace([path, other])

    problems = section_roles(path, path.read_text(encoding="utf-8"), names)

    tail = (
        f"then write '{SECTION}1' as 'demo spec {SECTION}1', or it inherits "
        "the prefix before it"
    )
    assert [p.split(": ", 1)[1] for p in problems] == [
        f"write 'other spec {SECTION}1' as plain text, which the build links",
        tail,
    ]


def test_no_role_names_a_section(texts, names):
    """Plain text (item 5): a section is cited as one string, which the build links.

    Holds citation spec §2 decision 5.
    """
    problems = [
        p for path, text in texts.items() for p in section_roles(path, text, names)
    ]

    assert not problems, "\n".join(problems)


def test_crossed_finds_a_code_span_wrapped_across_lines(tmp_path):
    """The stray backtick on the second line would hide the role that follows."""
    body = DEMO + f"\nA `wrapped\nspan` then {{ref}}`{SECTION}1 <demo-spec-2>`.\n"
    path, _ = demo(tmp_path, body)

    problems = crossed(path, path.read_text(encoding="utf-8"))

    assert [p.split(": ", 1)[1] for p in problems] == [
        "a code span crosses a line break",
        "a code span crosses a line break",
    ]


@pytest.mark.parametrize("spec", specifications(), ids=lambda path: path.name)
def test_no_code_span_in_a_specification_crosses_a_line(spec):
    """The grammar reads a line at a time, so a span must close where it opens."""
    problems = crossed(spec, spec.read_text(encoding="utf-8"))

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
#: A top-level list item, numbered or bulleted.
ITEM = re.compile(r"^(?:\d+\.|[-*])\s+(?P<body>.*)$")
#: The bold state an open item opens with.
STATE = re.compile(r"^\*\*(?P<state>[^*]+)\*\*(?P<rest>.*)$")


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


def dated(written: str) -> date | None:
    """Read an ISO date, or None when it has the shape but no calendar holds it."""
    try:
        return date.fromisoformat(written)
    except ValueError:
        return None


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


def roadmap_header(cells: list[str]) -> bool:
    """Decide whether a table's header is a roadmap's: ``#``, ``Scope`` and ``Status``.

    A Verification table has a Status column too, so a roadmap is read by its whole
    header (ledger spec §3.6), which a type coverage roadmap extends with ``Lines``.
    """
    return bool(cells) and cells[0] == "#" and {"Scope", "Status"} <= set(cells)


def statuses(text: str) -> Iterator[tuple[int, str, str]]:
    """Yield every roadmap Status cell, and every open item with its lines joined.

    A cell is read from any table whose header names a Status column, wherever
    the table sits, and the table ends where its rows do. An open item is any
    top-level list item under "Open Items", however its heading is cased, numbered
    or bulleted, so an item that has lost its state is reported rather than passed
    over.

    Parameters
    ----------
    text : str
        The specification.

    Yields
    ------
    tuple of (int, str, str)
        The line the status opens on; ``"row"`` or ``"item"``; and the status.

    """
    table: list[tuple[int, str]] = []
    for number, line in [*read_lines(text), (0, "")]:
        if line.startswith("|"):
            table.append((number, line))
            continue
        if table:
            cells = citations.cells(table[0][1])
            if roadmap_header(cells):
                column = cells.index("Status")
                for row, written in table[2:]:
                    found = citations.cells(written)
                    yield row, "row", found[column] if column < len(found) else ""
            table = []
    item: list[str] = []
    start = 0
    # matched without regard to case, as a heading in headline style and one in
    # sentence case name the same section, and missing it would stop its check
    items = [
        line
        for title, lines in sections(text).items()
        if title.casefold() == "open items"
        for line in lines
    ]
    for number, line in [*items, (0, "")]:
        opened = ITEM.match(line)
        if opened or not line.strip():
            if item:
                yield start, "item", " ".join(item)
            item, start = ([opened["body"].strip()], number) if opened else ([], 0)
        elif item:
            item.append(line.strip())


def status(path: Path, text: str, *, unitemed: bool | None = None) -> list[str]:
    """Find each status outside the vocabulary, or terminal and unevidenced.

    An open item is read in the grammar of docs spec §3.6 only while its
    specification waits to be brought into that of items spec §3.2, as
    :data:`UNITEMED` says unless ``unitemed`` does; after that, the rules of
    items spec §3.7 hold it instead.
    """
    if unitemed is None:
        unitemed = path.name in UNITEMED
    problems = []
    for number, kind, written in statuses(text):
        if kind == "item" and not unitemed:
            continue
        if kind == "row":
            state = next((s for s in ROW_STATES if written.startswith(s)), written)
            rest, states = written[len(state) :], ROW_STATES
        else:
            bold = STATE.match(written)
            if bold is None:
                problems.append(f"{where(path, number)}: an open item with no status")
                continue
            state, rest, states = bold["state"].strip(), bold["rest"], ITEM_STATES
        if state not in states:
            problems.append(f"{where(path, number)}: {state!r} is not a status")
        elif state in TERMINAL:
            evidence = carried(rest)
            stamp = DATE.search(evidence)
            if not (stamp and REFERENCE.search(evidence)):
                problems.append(
                    f"{where(path, number)}: {state} carries no date and reference"
                )
            elif dated(stamp[0]) is None:
                problems.append(
                    f"{where(path, number)}: {state} carries {stamp[0]}, "
                    "which is not a date"
                )
    return problems


def test_status_finds_an_unknown_state_and_unevidenced_terminals(tmp_path):
    """A terminal status needs its date and its reference, and nothing else does."""
    roadmap = (
        "(demo-spec-1)=\n## 1. Roadmap\n\n| # | Scope | Status |\n|---|---|---|\n"
        f"| 1 | a | {LANDED} (2026-01-01, {{pull}}`1`) |\n"
        f"| 2 | b | {LANDED} (2026-01-01) |\n| 3 | c | shipped |\n"
        "| 4 | d | candidate |\n\n"
        "(demo-spec-2)=\n## 2. Open Items\n\n"
        "1. **Resolved** (2026-01-01, [x](https://github.com/o/r/issues/1)) - **A.**\n"
        "2. **Resolved** (no date,\n   {issue}`2`) - **B.**\n"
        "3. **Open** - **C.**\n"
    )
    path, _ = demo(tmp_path, roadmap)

    problems = status(path, path.read_text(encoding="utf-8"), unitemed=True)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"{LANDED} carries no date and reference",
        "'shipped' is not a status",
        "Resolved carries no date and reference",
    ]


@pytest.mark.parametrize("title", ["Open Items", "Open items"])
def test_statuses_reads_open_items_whatever_their_case(title):
    """An open item is read under its heading however the heading is cased.

    The specifications title their headings in headline style, as the title
    style of the documentation guide says, and a heading written before it was
    adopted is in sentence case. Either way its items are statuses, and missing
    them would silently stop their check.

    """
    text = f"(demo-spec-8)=\n## 8. {title}\n\n1. **Open** - **An item.**\n"

    assert [kind for _, kind, _ in statuses(text)] == ["item"]


def test_status_finds_a_date_no_calendar_holds(tmp_path):
    """A date of the right shape is still no date if no calendar holds it."""
    roadmap = (
        "(demo-spec-1)=\n## 1. Roadmap\n\n| # | Scope | Status |\n|---|---|---|\n"
        f"| 1 | a | {LANDED} (2026-02-30, {{pull}}`1`) |\n"
        f"| 2 | b | {LANDED} (2026-02-28, {{pull}}`1`) |\n\n"
        "(demo-spec-2)=\n## 2. Open Items\n\n"
        "1. **Resolved** (2026-13-01, {issue}`2`) - **A.**\n"
    )
    path, _ = demo(tmp_path, roadmap)

    problems = status(path, path.read_text(encoding="utf-8"), unitemed=True)

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"{LANDED} carries 2026-02-30, which is not a date",
        "Resolved carries 2026-13-01, which is not a date",
    ]


def test_status_reads_bullets_and_a_roadmap_wherever_it_sits(tmp_path):
    """A bullet is an item, an item with no state is reported, a roadmap is read.

    A roadmap is read by its header wherever it sits, and only by its header, so
    a Verification table is never mistaken for one.
    """
    body = (
        "(demo-spec-1)=\n## 1. Plan and status\n\n"
        "| # | Scope | Status |\n|---|---|---|\n| 1 | a | shipped |\n\n"
        "| Decision | Status | Evidence |\n|---|---|---|\n| 1 | shipped | |\n\n"
        "(demo-spec-2)=\n## 2. Open Items\n\n"
        "- **shipped** - **A.**\n"
        "- **Resolved** (no date) - **B.**\n"
        "* plain text, its state forgotten\n"
    )
    path, _ = demo(tmp_path, body)

    problems = status(path, path.read_text(encoding="utf-8"), unitemed=True)

    assert [p.split(": ", 1)[1] for p in problems] == [
        "'shipped' is not a status",
        "'shipped' is not a status",
        "Resolved carries no date and reference",
        "an open item with no status",
    ]


def test_both_kinds_of_status_are_read(specs):
    """Either reader could find nothing and pass, so each must find something."""
    kinds = {
        kind
        for spec in specs
        for _, kind, _ in statuses(spec.read_text(encoding="utf-8"))
    }

    assert kinds == {"row", "item"}


@pytest.mark.parametrize("spec", specifications(), ids=lambda path: path.name)
def test_every_status_is_in_the_vocabulary_and_evidenced(spec):
    """Status (item 7).

    Holds docs spec §2 decision 7.
    """
    text = spec.read_text(encoding="utf-8")
    problems = status(spec, text)

    assert list(statuses(text)), f"{spec.name} has no roadmap and no open items"
    assert not problems, "\n".join(problems)


def front_matter(text: str) -> str:
    """Read the YAML front matter a markdown document opens with, if any."""
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    return text[4:end] if end != -1 else ""


def toctree(index: str) -> list[str]:
    """Read, in order, the documents the toctree of a page lists."""
    lines = index.splitlines()
    entries = []
    for line in lines[lines.index(".. toctree::") + 1 :]:
        if line.strip() and not line.startswith(" "):
            break
        entry = line.strip()
        if entry and not entry.startswith(":"):
            entries.append(entry)
    return entries


#: What a row of the namespace table opens with for each generation below its root,
#: and the branch it ends with (docs spec §3.7).
INDENT = "|indent|"
BRANCH = "└─"

#: A row of the namespace table: its marker, its prefix and its document.
ROW = re.compile(
    rf"\*\s+-\s+(?P<marker>(?:{re.escape(INDENT)}\s+)*(?:{BRANCH}\s+)?)"
    rf"``(?P<prefix>[^`]+?)\s*{SECTION}{ELLIPSIS}``\s*\n"
    r"\s+-\s+:doc:`(?P<doc>[^`]+)`"
)


def namespace_table(index: str) -> dict[str, str]:
    """Read the document each prefix names in the index's namespace table."""
    return {match["prefix"]: match["doc"] for match in ROW.finditer(index)}


def table_rows(index: str) -> list[tuple[str, str]]:
    """Read, in order, the marker and the prefix of each row of the namespace table."""
    return [
        (" ".join(match["marker"].split()), match["prefix"])
        for match in ROW.finditer(index)
    ]


def marker(depth: int) -> str:
    """Write the marker of a row at a depth below its root, which has none."""
    return " ".join([*[INDENT] * (depth - 1), BRANCH]) if depth else ""


#: The banner lines a specification records its family on, and the line they retired.
LINEAGE = "Lineage"
CHILDREN = "Children"
RETIRED = "Parent spec"

#: What separates the generations of a lineage, built rather than written, since
#: ruff reads the character as a mistyped angle bracket.
ARROW = "\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}"

#: A part of a family line: a link to a specification, this specification in bold,
#: or the text between them, as ``(kind, words, target)``.
Part = tuple[str, str, str]


def banner_lines(text: str) -> list[tuple[int, str, list[Part]]]:
    """Read each family line of a banner, with its line number, label and parts.

    The banner is parsed as CommonMark, so a line that wraps or a link written with
    a title reads the same as one that does not.
    """
    found = []
    for token in MarkdownIt("commonmark").parse(text):
        children = [
            child
            for child in token.children or []
            if child.type != "text" or child.content
        ]
        opening = [child.type for child in children[:3]]
        if token.type != "inline" or opening != ["strong_open", "text", "strong_close"]:
            continue
        label = children[1].content.removesuffix(":")
        if label not in {LINEAGE, CHILDREN, RETIRED}:
            continue
        parts: list[Part] = []
        inner: list[str] | None = None
        target = ""
        for child in children[3:]:
            # A line break carries no content, but renders as the space it stands for.
            words = " " if child.type in {"softbreak", "hardbreak"} else child.content
            if child.type in {"link_open", "strong_open"}:
                inner, target = [], str(child.attrs.get("href", ""))
            elif child.type in {"link_close", "strong_close"} and inner is not None:
                kind = "link" if child.type == "link_close" else "self"
                parts.append((kind, " ".join("".join(inner).split()), target))
                inner = None
            elif inner is not None:
                inner.append(words)
            elif parts and parts[-1][0] == "text":
                parts[-1] = ("text", parts[-1][1] + words, "")
            else:
                parts.append(("text", words, ""))
        found.append((token.map[0] + 1, label, parts))
    return found


def members(parts: list[Part], separator: str) -> list[Part] | None:
    """Read the links and bold of a family line, or None if text sits out of place.

    Text may only separate two members, and only as the separator given, so the line
    opens and closes with a member.
    """
    parts = list(parts)
    for end in (0, -1):
        while parts and parts[end][0] == "text" and not parts[end][1].strip():
            parts.pop(end)
    named, between = parts[0::2], parts[1::2]
    if (
        len(named) != len(between) + 1
        or any(part[0] == "text" for part in named)
        or any(part[0] != "text" or part[1].strip() != separator for part in between)
    ):
        return None
    return named


def families(texts: Mapping[Path, str]) -> tuple[dict[str, list[str]], list[str]]:
    """Read the lineage of each specification, and find where its family lines disagree.

    Each specification carries one Lineage line, its ancestors linked from the root
    down and itself last in bold, and one Children line, its direct children linked
    in order of prefix, or the word none. Its lineage extends its parent's by itself,
    and its children are exactly the specifications whose lineage names it as parent.

    Parameters
    ----------
    texts : mapping of Path to str
        The specifications, each with its text.

    Returns
    -------
    tuple
        The lineage of each prefix, root first, and one message per fault.

    """
    prefixes = {
        path: match["prefix"]
        for path, text in texts.items()
        if (match := DECLARED.search(text)) is not None
    }
    owners = {prefix: path.name for path, prefix in prefixes.items()}
    lineages: dict[str, list[str]] = {}
    stated: dict[str, tuple[Path, int, list[str]]] = {}
    problems = []

    def linked(path: Path, number: int, part: Part) -> str:
        if owners.get(part[1]) != part[2]:
            problems.append(
                f"{where(path, number)}: links {part[1]!r} to {part[2]!r}, "
                f"which is {owners.get(part[1])!r}"
            )
        return part[1]

    for path, prefix in prefixes.items():
        lines = banner_lines(texts[path])
        labels = [label for _, label, _ in lines]
        for number, label, _ in lines:
            if label == RETIRED:
                problems.append(f"{where(path, number)}: {RETIRED} is now {LINEAGE}")
        problems.extend(
            f"{where(path, 1)}: carries {labels.count(label)} {label} lines, not 1"
            for label in (LINEAGE, CHILDREN)
            if labels.count(label) != 1
        )
        for number, label, parts in lines:
            if label == LINEAGE and labels.count(LINEAGE) == 1:
                chain = members(parts, ARROW)
                if chain is None or chain[-1] != ("self", prefix, ""):
                    problems.append(
                        f"{where(path, number)}: a lineage links its ancestors, "
                        f"root first, separated by {ARROW}, and ends with **{prefix}**"
                    )
                    continue
                ancestors = [linked(path, number, part) for part in chain[:-1]]
                if any(part[0] != "link" for part in chain[:-1]):
                    problems.append(f"{where(path, number)}: an ancestor is not linked")
                lineages[prefix] = [*ancestors, prefix]
            elif label == CHILDREN and labels.count(CHILDREN) == 1:
                words = "".join(part[1] for part in parts).strip()
                if words == "none":
                    stated[prefix] = (path, number, [])
                    continue
                listed = members(parts, ",")
                if listed is None or any(part[0] != "link" for part in listed):
                    problems.append(
                        f"{where(path, number)}: children are links separated by "
                        "commas, or the word none"
                    )
                    continue
                stated[prefix] = (
                    path,
                    number,
                    [linked(path, number, p) for p in listed],
                )

    step = f" {ARROW} "
    for prefix, lineage in lineages.items():
        if len(lineage) > 1 and lineages.get(lineage[-2]) != lineage[:-1]:
            parent = lineages.get(lineage[-2], ["(none)"])
            problems.append(
                f"{owners[prefix]}: its lineage {step.join(lineage)} does not extend "
                f"its parent's, {step.join(parent)}"
            )
    for prefix, (path, number, children) in stated.items():
        expected = sorted(
            child
            for child, lineage in lineages.items()
            if len(lineage) > 1 and lineage[-2] == prefix
        )
        if children != expected:
            problems.append(
                f"{where(path, number)}: lists children {children}, "
                f"where the lineages make them {expected}"
            )
    return lineages, problems


def family_rows(lineages: Mapping[str, list[str]]) -> list[tuple[str, str]]:
    """Order the rows of the namespace table, each child under its parent.

    Roots run in order of prefix, and so does each family's set of siblings.
    """
    rows = []

    def descend(prefix: str, depth: int) -> None:
        rows.append((marker(depth), prefix))
        for child in sorted(
            child
            for child, lineage in lineages.items()
            if len(lineage) > 1 and lineage[-2] == prefix
        ):
            descend(child, depth + 1)

    for root in sorted(
        prefix for prefix, lineage in lineages.items() if len(lineage) == 1
    ):
        descend(root, 0)
    return rows


def member(prefix: str, lineage: str, children: str) -> str:
    """Write the banner of a specification with the family lines given."""
    return (
        f"- **Citation prefix:** `{prefix} {SECTION}{ELLIPSIS}`\n"
        f"- **{LINEAGE}:** {lineage}\n"
        f"- **{CHILDREN}:** {children}\n"
    )


def chain(*prefixes: str) -> str:
    """Write a lineage: each ancestor linked, root first, and the last in bold."""
    *ancestors, last = prefixes
    links = [f"[{prefix}]({prefix.replace(' ', '-')}.md)" for prefix in ancestors]
    return f" {ARROW} ".join([*links, f"**{last}**"])


def collection(*banners: str) -> dict[Path, str]:
    """Name each banner after its prefix, as a specification of a collection."""
    return {
        Path(f"{DECLARED.search(text)['prefix'].replace(' ', '-')}.md"): text
        for text in banners
    }


#: A family of three generations, and a specification of its own.
DEMO_FAMILY = (
    member("demo spec", chain("demo spec"), "[kin spec](kin-spec.md)"),
    member("kin spec", chain("demo spec", "kin spec"), "[tot spec](tot-spec.md)"),
    member("tot spec", chain("demo spec", "kin spec", "tot spec"), "none"),
    member("lone spec", chain("lone spec"), "none"),
)


def test_families_read_a_family_that_agrees():
    """A lineage per generation, and children that name exactly those below."""
    lineages, problems = families(collection(*DEMO_FAMILY))

    assert not problems
    assert lineages["tot spec"] == ["demo spec", "kin spec", "tot spec"]
    assert family_rows(lineages) == [
        ("", "demo spec"),
        (BRANCH, "kin spec"),
        (f"{INDENT} {BRANCH}", "tot spec"),
        ("", "lone spec"),
    ]


@pytest.mark.parametrize(
    ("index", "replacement", "fault"),
    [
        (
            2,
            member("tot spec", chain("kin spec", "tot spec"), "none"),
            "does not extend its parent's",
        ),
        (
            0,
            member("demo spec", "**demo spec**", "none"),
            "where the lineages make them",
        ),
        (
            3,
            member("lone spec", "**lone spec**", "[kin spec](kin-spec.md)"),
            "where the lineages make them",
        ),
        (
            1,
            member(
                "kin spec",
                f"[demo spec](lone-spec.md) {ARROW} **kin spec**",
                "[tot spec](tot-spec.md)",
            ),
            "which is 'demo-spec.md'",
        ),
        (
            1,
            member(
                "kin spec",
                "[demo spec](demo-spec.md) / **kin spec**",
                "[tot spec](tot-spec.md)",
            ),
            f"separated by {ARROW}",
        ),
        (
            1,
            member(
                "kin spec",
                f"[demo spec](demo-spec.md) {ARROW} **demo spec**",
                "[tot spec](tot-spec.md)",
            ),
            "ends with **kin spec**",
        ),
        (
            3,
            (
                f"- **Citation prefix:** `lone spec {SECTION}{ELLIPSIS}`\n"
                "- **Parent spec:** none\n"
            ),
            "Parent spec is now Lineage",
        ),
        (
            3,
            member("lone spec", f"**lone spec** {ARROW}", "none"),
            "ends with **lone spec**",
        ),
        (
            0,
            member("demo spec", chain("demo spec"), "[kin spec](kin-spec.md),"),
            "separated by commas",
        ),
    ],
    ids=[
        "skipped-generation",
        "missing-child",
        "stranger",
        "wrong-link",
        "separator",
        "not-itself",
        "retired",
        "trailing-arrow",
        "trailing-comma",
    ],
)
def test_families_find_each_line_that_disagrees(index, replacement, fault):
    """Each family line is checked against the lineages, in both directions."""
    banners = list(DEMO_FAMILY)
    banners[index] = replacement
    _, problems = families(collection(*banners))

    assert any(fault in problem for problem in problems), problems


@pytest.mark.parametrize("wrap", ["\n  ", "  \n  "], ids=["softbreak", "hardbreak"])
@pytest.mark.parametrize(
    ("index", "replacement"),
    [
        (
            2,
            member(
                "tot spec",
                f"[demo{{wrap}}spec](demo-spec.md) {ARROW} [kin spec](kin-spec.md) "
                f"{ARROW} **tot spec**",
                "none",
            ),
        ),
        (3, member("lone spec", "**lone{wrap}spec**", "none")),
        (
            1,
            member(
                "kin spec",
                chain("demo spec", "kin spec"),
                "[tot{wrap}spec](tot-spec.md)",
            ),
        ),
    ],
    ids=["wrapped-ancestor", "wrapped-self", "wrapped-child"],
)
def test_families_read_a_prefix_wrapped_across_lines(index, replacement, wrap):
    """A line break inside a prefix reads as the space CommonMark renders."""
    banners = list(DEMO_FAMILY)
    banners[index] = replacement.replace("{wrap}", wrap)
    _, problems = families(collection(*banners))

    assert not problems, problems


def test_families_read_siblings_in_order_of_prefix():
    """A Children line out of order is a fault, as the table rows would be."""
    banners = (
        member(
            "demo spec",
            "**demo spec**",
            "[kin spec](kin-spec.md), [ark spec](ark-spec.md)",
        ),
        member("kin spec", chain("demo spec", "kin spec"), "none"),
        member("ark spec", chain("demo spec", "ark spec"), "none"),
    )
    lineages, problems = families(collection(*banners))

    assert problems == [
        (
            "demo-spec.md:3: lists children ['kin spec', 'ark spec'], "
            "where the lineages make them ['ark spec', 'kin spec']"
        )
    ]
    assert [prefix for _, prefix in family_rows(lineages)] == [
        "demo spec",
        "ark spec",
        "kin spec",
    ]


def test_table_rows_read_the_marker_of_each_generation():
    """The marker is read as written, so a row at the wrong depth is seen."""
    index = "\n".join(
        f"    * - {mark}``{prefix} {SECTION}{ELLIPSIS}``\n      - :doc:`{prefix}`"
        for mark, prefix in [
            ("", "demo spec"),
            (f"{BRANCH} ", "kin spec"),
            (f"{INDENT} {BRANCH} ", "tot spec"),
        ]
    )

    assert table_rows(index) == [
        ("", "demo spec"),
        (BRANCH, "kin spec"),
        (f"{INDENT} {BRANCH}", "tot spec"),
    ]


def test_every_family_line_agrees(specs):
    """Family (item 8): the Lineage and Children lines agree across the collection."""
    _, problems = families({spec: spec.read_text(encoding="utf-8") for spec in specs})

    assert not problems, "\n".join(problems)


def test_the_index_groups_each_family_under_its_root(specs):
    """Family (item 8): the namespace table puts each child under its parent."""
    index = (SPECS / "index.rst").read_text(encoding="utf-8")
    lineages, _ = families({spec: spec.read_text(encoding="utf-8") for spec in specs})

    assert table_rows(index) == family_rows(lineages)


def test_front_matter_is_read_only_where_a_document_opens():
    """A rule quoted further down a page is not the page's front matter."""
    assert front_matter("---\norphan: true\n---\n\n# Title\n") == "orphan: true"
    assert front_matter("# Title\n\n---\norphan: true\n---\n") == ""


def test_no_specification_is_an_orphan(specs):
    """A specification is reached through the index, never left unlisted.

    Holds docs spec §2 decision 1.
    """
    orphans = [
        spec.name
        for spec in specs
        if "orphan: true" in front_matter(spec.read_text(encoding="utf-8"))
    ]

    assert not orphans, f"{orphans} still carry orphan: true"


def test_the_index_lists_every_specification(specs):
    """The toctree is the only way a reader reaches a specification."""
    index = (SPECS / "index.rst").read_text(encoding="utf-8")

    assert toctree(index) == [spec.stem for spec in specs]


def test_the_index_names_every_prefix(names):
    """The namespace table and the banners agree on which prefix is whose."""
    index = (SPECS / "index.rst").read_text(encoding="utf-8")
    declared = {
        prefix.replace("-", " "): spec.stem for spec, prefix in names.owners.items()
    }

    assert namespace_table(index) == declared


#: The check of the rendered output that row 4 of docs spec §4 pairs with the
#: transform, and the task that runs it in CI.
OUTPUT_GATE = REPO / "tests" / "docs" / "test_rendered_citations.py"
OUTPUT_TASK = "tests-docs-browser"

#: The transform that links citations at build time.
TRANSFORM = "geovista_citation_xrefs"


def registered(conf: str) -> set[str]:
    """Read every extension a sphinx ``conf.py`` registers, however it does so."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(conf)):
        value = None
        if isinstance(node, ast.Assign | ast.AugAssign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == "extensions" for t in targets):
                value = node.value
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            owner = node.func.value
            if node.func.attr == "setup_extension" or (
                node.func.attr in {"append", "extend", "insert"}
                and isinstance(owner, ast.Name)
                and owner.id == "extensions"
            ):
                value = ast.Tuple(elts=node.args)
        if value is not None:
            found |= {
                leaf.value
                for leaf in ast.walk(value)
                if isinstance(leaf, ast.Constant) and isinstance(leaf.value, str)
            }
    return found


def test_registered_reads_every_way_an_extension_is_added():
    """A list, an append and a setup call all register an extension."""
    conf = (
        'extensions = ["sphinx.ext.intersphinx"]\n'
        'extensions.append("geovista_citation_xrefs")\n'
        'app.setup_extension("sphinx_gallery.gen_gallery")\n'
    )

    assert registered(conf) == {
        "sphinx.ext.intersphinx",
        "geovista_citation_xrefs",
        "sphinx_gallery.gen_gallery",
    }


def test_registered_reads_an_annotated_list_and_an_insert():
    """A refactor of conf.py must not leave the watch reading nothing."""
    conf = 'extensions: list[str] = ["a"]\nextensions.insert(0, "b")\n'

    assert registered(conf) == {"a", "b"}


def test_row_4_pairs_the_transform_with_its_output_gate():
    """Triggers (item 6): a transform the output gate does not check.

    Every citation is plain text since the hand-written roles collapsed, so every
    citation link on the site is the transform's, and this holds it in place.
    """
    conf = (REPO / "docs" / "src" / "conf.py").read_text(encoding="utf-8")
    extensions = registered(conf)
    manifest = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    task = manifest["tool"]["pixi"]["feature"]["geovista"]["tasks"][OUTPUT_TASK]
    workflow = REPO / ".github" / "workflows" / "ci-tests-docs.yml"

    assert "myst_nb" in extensions, "the watch reads none of conf.py's extensions"
    assert TRANSFORM in extensions, f"{TRANSFORM} is not registered in conf.py"
    assert OUTPUT_GATE.is_file(), f"{OUTPUT_GATE.name} is missing"
    assert "tests/docs" in task["cmd"], f"{OUTPUT_TASK} no longer runs tests/docs"
    assert OUTPUT_TASK in workflow.read_text(encoding="utf-8"), (
        f"{workflow.name} no longer runs {OUTPUT_TASK}"
    )


#: Ledger (item 9 of docs spec §3.5): the states of ledger spec §3.2, §3.3, §3.4, from
#: the grammar, which builds them by name.
AGREED = citations.AGREED
RETIRED_STATE = citations.RETIRED
PENDING = citations.PENDING
VERIFIED = citations.VERIFIED
SIGNED_OFF = citations.SIGNED_OFF
LEDGER_RETIRED = citations.LEDGER_RETIRED
LEDGER_STATES = (PENDING, VERIFIED, SIGNED_OFF, LEDGER_RETIRED)
decisions = citations.decisions
ledger = citations.ledger
state_of = citations.state_of
decision_anchor = citations.decision_anchor
Decision = citations.Decision

#: The specifications not yet in the ledger, each with the row of ledger spec §8
#: that brings it in. Each of those rows shortens this, and the last empties it.
UNLEDGERED = {
    "2026-10-26-globe-heights-layers-design.md": 6,
    "2026-10-27-globe-scene-design.md": 6,
    "2026-10-28-heights-as-data-design.md": 6,
}

#: The roles a provenance carries.
USER = re.compile(r"\{user\}`(?P<login>[^`]+)`")
PULL = re.compile(r"\{pull\}`\d+`")


def entry(number: int, state: str, carried: str, title: str = "A decision.") -> str:
    """Write a decision's entry, state first."""
    return f"{number}. **{state}** ({carried}) — **{title}** Its reasoning.\n"


#: Provenance that a decision in force carries.
AGREEMENT = "2026-01-01, {user}`bjlittle`, {pull}`1`"


def ledgered(
    tmp_path: Path, entries: str, rows: str, roadmap: str = "| 1 | a | not started |\n"
) -> tuple[Path, Namespace]:
    """Write a ``demo spec`` with decisions, a roadmap and a Verification table."""
    return demo(
        tmp_path,
        "(demo-spec-1)=\n## 1. Purpose\n\n"
        f"(demo-spec-2)=\n## 2. Decisions\n\n{entries}\n"
        "(demo-spec-3)=\n## 3. Roadmap\n\n| # | Scope | Status |\n|---|---|---|\n"
        f"{roadmap}\n"
        "(demo-spec-4)=\n## 4. Verification\n\n"
        f"| Decision | Status | Evidence |\n|---|---|---|\n{rows}",
    )


def faults(problems: list[str]) -> list[str]:
    """Drop the place each problem names, keeping what it says."""
    return [problem.split(": ", 1)[1] for problem in problems]


def ledger_entries(path: Path, text: str) -> list[str]:
    """Find each fault in a specification's decisions (ledger spec §3.6)."""
    titles = {
        heading["num"]: heading["title"]
        for _, line in read_lines(text)
        if (heading := HEADING.match(line))
    }
    if titles.get("2") != citations.DECISIONS:
        return [f"{where(path, 1)}: its second section is not titled Decisions"]
    found = decisions(text)
    problems = []
    lines = citations._section(text, "2", citations.DECISIONS)
    if any(re.match(r"^[-*]\s", line) for _, line in lines):
        problems.append(
            f"{where(path, 1)}: a decision is a bullet, not a numbered entry"
        )
    if not found:
        problems.append(
            f"{where(path, 1)}: its Decisions section holds no numbered decision"
        )
    numbers = [d.number for d in found]
    if numbers != list(range(1, len(found) + 1)):
        problems.append(f"{where(path, 1)}: decisions are numbered {numbers}")
    for d in found:
        at = where(path, d.line)
        agreed, _, history = d.carried.partition("; agreed ")
        if d.state is None:
            problems.append(f"{at}: decision {d.number} opens with no state")
        elif not (DATE.search(agreed) and USER.search(agreed) and PULL.search(agreed)):
            problems.append(f"{at}: decision {d.number} carries no date, user and pull")
        elif not d.title:
            problems.append(f"{at}: decision {d.number} has no title")
        elif d.state == RETIRED_STATE and not (
            DATE.search(history) and PULL.search(history)
        ):
            problems.append(f"{at}: decision {d.number} is retired with no agreement")
        problems += [
            f"{at}: decision {d.number} carries {bad}, which is not a date"
            for bad in undated(d.carried)
        ]
    return problems


def undated(evidence: str) -> list[str]:
    """Find each date of the right shape that no calendar holds."""
    return [match[0] for match in DATE.finditer(evidence) if dated(match[0]) is None]


def opened(status: str) -> tuple[str | None, str]:
    """Read a ledger state and the parenthetical it carries."""
    state = state_of(status, LEDGER_STATES)
    if state is None:
        return None, ""
    plain = status.replace(citations.VS16, "")
    rest = plain[len(state.replace(citations.VS16, "")) :]
    return state, rest


def ledger_table(path: Path, text: str) -> list[str]:
    """Find each fault in a Verification table, item 3 of ledger spec §3.6."""
    titles = [h["title"] for _, line in read_lines(text) if (h := HEADING.match(line))]
    if not titles or titles[-1] != citations.VERIFICATION:
        return [f"{where(path, 1)}: its last section is not titled Verification"]
    rows = ledger(text)
    if rows is None:
        return [f"{where(path, 1)}: its Verification section holds no ledger"]
    problems = []
    expected = len(decisions(text))
    seen: set[int] = set()
    for row in rows:
        at = where(path, row.line)
        if row.decision is None:
            problems.append(f"{at}: a row names {row.cell!r}, not a decision")
            continue
        if row.decision in seen:
            problems.append(f"{at}: decision {row.decision} has a second row")
        elif not 1 <= row.decision <= expected:
            problems.append(
                f"{at}: a row names decision {row.decision}, which no entry holds"
            )
        elif seen and row.decision < max(seen):
            problems.append(f"{at}: decision {row.decision} is out of order")
        seen.add(row.decision)
        state, rest = opened(row.status)
        evidence = carried(rest)
        if state is None:
            problems.append(f"{at}: {row.status!r} is not a ledger state")
        elif state == PENDING and rest.strip():
            problems.append(
                f"{at}: decision {row.decision} is pending, and carries more"
            )
        elif state in (VERIFIED, LEDGER_RETIRED) and not (
            DATE.search(evidence) and PULL.search(evidence)
        ):
            problems.append(f"{at}: decision {row.decision} carries no date and pull")
        elif state == SIGNED_OFF and not (
            DATE.search(evidence) and USER.search(evidence) and PULL.search(evidence)
        ):
            problems.append(
                f"{at}: decision {row.decision} carries no date, user and pull"
            )
        elif state == SIGNED_OFF and not row.evidence.strip():
            problems.append(
                f"{at}: decision {row.decision} is signed off, and says nothing of "
                "what was checked"
            )
        problems += [
            f"{at}: decision {row.decision} carries {bad}, which is not a date"
            for bad in undated(evidence)
        ]
    problems += [
        f"{where(path, 1)}: decision {number} has no row"
        for number in range(1, expected + 1)
        if number not in seen
    ]
    return problems


def ledger_retirements(path: Path, text: str) -> list[str]:
    """Find each decision retired in one section only, item 4 of ledger spec §3.6."""
    rows = {row.decision: row for row in ledger(text) or []}
    problems = []
    for d in decisions(text):
        row = rows.get(d.number)
        if row is None:
            continue
        if (d.state == RETIRED_STATE) != (opened(row.status)[0] == LEDGER_RETIRED):
            problems.append(
                f"{where(path, row.line)}: decision {d.number} is retired in one "
                "section and not the other"
            )
    return problems


def cites(path: Path, anchor: str, names: Namespace) -> bool:
    """Decide whether a file cites the anchor, in its prose or its comments."""
    owner = names.owners.get(path)
    for _, line in source_lines(path, path.read_text(encoding="utf-8")):
        if any(c.slug == anchor for c in scan(prose(line)[0], names.signed, owner)):
            return True
    return False


def is_test(name: str) -> bool:
    """Decide whether a path names a test file: ``tests/``, and ``test_*.py``.

    A specification cites its own decisions, so a file that merely cites one is
    no evidence it was delivered (ledger spec §2 decision 6).
    """
    path = Path(name)
    return path.parts[:1] == ("tests",) and fnmatch(path.name, "test_*.py")


def ledger_evidence(
    path: Path, text: str, names: Namespace, root: Path = REPO
) -> list[str]:
    """Find each verified row whose test is missing or silent (ledger spec §3.6)."""
    owner = names.owners.get(path)
    problems = []
    for row in ledger(text) or []:
        if opened(row.status)[0] != VERIFIED or row.decision is None:
            continue
        at = where(path, row.line)
        files = re.findall(r"`([^`]+)`", row.evidence)
        if not files:
            problems.append(f"{at}: decision {row.decision} is verified by nothing")
        anchor = decision_anchor(owner, row.decision)
        for name in files:
            test = root / name
            if not is_test(name):
                problems.append(f"{at}: {name} is not a test file")
            elif not test.is_file():
                problems.append(f"{at}: {name} does not exist")
            elif not cites(test, anchor, names):
                problems.append(f"{at}: {name} does not cite decision {row.decision}")
    return problems


def roadmap_rows(text: str) -> dict[str, str]:
    """Read each roadmap row's Status, keyed by its number."""
    found: dict[str, str] = {}
    table: list[list[str]] = []
    for _, line in [*read_lines(text), (0, "")]:
        if line.startswith("|"):
            table.append(citations.cells(line))
            continue
        if table and roadmap_header(table[0]):
            column = table[0].index("Status")
            found.update(
                {row[0]: row[column] for row in table[2:] if column < len(row)}
            )
        table = []
    return found


def ledger_complete(path: Path, text: str) -> list[str]:
    """Find a pending decision once the roadmap is done, item 7 of ledger spec §3.6."""
    rows = roadmap_rows(text)
    if any(s.startswith(("in progress", "not started")) for s in rows.values()):
        return []
    problems = []
    for row in ledger(text) or []:
        if opened(row.status)[0] != PENDING:
            continue
        named = re.search(r"\brow (\d+) of\b", row.evidence)
        if named and rows.get(named[1], "").startswith("candidate"):
            continue
        problems.append(
            f"{where(path, row.line)}: decision {row.decision} is pending, and no "
            "row of the roadmap is left to deliver it"
        )
    return problems


def ledger_replacements(
    path: Path, text: str, names: Namespace, decided: Mapping[str, Decision]
) -> list[str]:
    """Find a retirement replaced by one not in force, item 8 of ledger spec §3.6."""
    owner = names.owners.get(path)
    found = [(d.line, d.body) for d in decisions(text) if d.state == RETIRED_STATE]
    found += [(r.line, r.evidence) for r in ledger(text) or [] if r.status]
    problems = []
    for line, written in found:
        for said in re.finditer(r"\breplaced by\b", written, flags=re.IGNORECASE):
            after = written[said.end() :]
            cited = next(scan(prose(after)[0], names.signed, owner), None)
            label = LABEL.match(cited.slug) if cited and cited.slug else None
            # only a decision can replace a decision; a section is prose
            if label is None or label["decision"] is None:
                continue
            problems += replaced(path, line, cited, decided)
    return problems


def replaced(
    path: Path, line: int, cited: Citation, decided: Mapping[str, Decision]
) -> list[str]:
    """Report a replacement that is no decision, or not one in force."""
    at = where(path, line)
    replacement = decided.get(cited.slug)
    if replacement is None:
        return [f"{at}: replaced by {cited.text}, no decision"]
    if replacement.state != AGREED:
        return [f"{at}: replaced by {cited.text}, which is not in force"]
    return []


def test_ledger_entries_finds_a_gap_a_missing_state_and_missing_provenance(tmp_path):
    """Ledger spec §2 decision 2, ledger spec §2 decision 4: numbered, state first."""
    entries = (
        entry(1, AGREED, "2026-01-01, {pull}`1`")
        + "3. **No state.** Its reasoning.\n"
        + entry(4, RETIRED_STATE, AGREEMENT)
        + entry(5, AGREED, AGREEMENT)
    )
    path, _ = ledgered(tmp_path, entries, "")

    assert faults(ledger_entries(path, path.read_text(encoding="utf-8"))) == [
        "decisions are numbered [1, 3, 4, 5]",
        "decision 1 carries no date, user and pull",
        "decision 3 opens with no state",
        "decision 4 is retired with no agreement",
    ]


def test_ledger_entries_wants_a_second_section_titled_decisions(tmp_path):
    """Ledger spec §2 decision 1: the citation names the second section, its home."""
    path, _ = demo(tmp_path, "(demo-spec-2)=\n## 2. Design\n\n1. **One.** First.\n")

    assert faults(ledger_entries(path, path.read_text(encoding="utf-8"))) == [
        "its second section is not titled Decisions"
    ]


def test_ledger_table_wants_the_last_section_and_a_row_per_decision(tmp_path):
    """Ledger spec §2 decision 5, ledger spec §2 decision 10: one row each, last."""
    entries = entry(1, AGREED, AGREEMENT) + entry(2, AGREED, AGREEMENT)
    entries += entry(3, AGREED, AGREEMENT)
    rows = f"| 1 | {PENDING} | |\n| two | {PENDING} | |\n"
    path, _ = ledgered(tmp_path, entries, rows)
    text = path.read_text(encoding="utf-8")

    assert faults(ledger_table(path, text)) == [
        "a row names 'two', not a decision",
        "decision 2 has no row",
        "decision 3 has no row",
    ]
    assert faults(ledger_table(path, text + "\n(demo-spec-5)=\n## 5. After\n")) == [
        "its last section is not titled Verification"
    ]


def test_ledger_entries_wants_numbered_decisions(tmp_path):
    """Ledger spec §2 decision 2: a bullet has no number, so it cannot be cited."""
    bulleted = f"- **{AGREED}** ({AGREEMENT}) — **A.** Its reasoning.\n"
    path, _ = ledgered(tmp_path, bulleted, "")

    assert faults(ledger_entries(path, path.read_text(encoding="utf-8"))) == [
        "a decision is a bullet, not a numbered entry",
        "its Decisions section holds no numbered decision",
    ]


def test_ledger_table_reports_an_extra_or_repeated_row_at_its_line(tmp_path):
    """Review Focus 5 of its plan: each stray row is reported where it is written."""
    entries = entry(1, AGREED, AGREEMENT) + entry(2, AGREED, AGREEMENT)
    rows = f"| 1 | {PENDING} | |\n| 1 | {PENDING} | |\n| 2 | {PENDING} | |\n"
    rows += f"| 3 | {PENDING} | |\n"
    path, _ = ledgered(tmp_path, entries, rows)
    text = path.read_text(encoding="utf-8")
    second, third = ledger(text)[1].line, ledger(text)[3].line

    assert ledger_table(path, text) == [
        f"{where(path, second)}: decision 1 has a second row",
        f"{where(path, third)}: a row names decision 3, which no entry holds",
    ]


def test_ledger_states_carry_what_they_must(tmp_path):
    """Ledger spec §2 decision 9: each state, and what its parenthetical holds."""
    entries = "".join(entry(n, AGREED, AGREEMENT) for n in range(1, 5))
    rows = (
        f"| 1 | {VERIFIED} ({{pull}}`1`) | `x.py` |\n"
        f"| 2 | {SIGNED_OFF} (2026-01-01, {{pull}}`1`) | Checked. |\n"
        f"| 3 | {PENDING} (2026-01-01) | |\n"
        "| 4 | shipped | |\n"
    )
    path, _ = ledgered(tmp_path, entries, rows)

    assert faults(ledger_table(path, path.read_text(encoding="utf-8"))) == [
        "decision 1 carries no date and pull",
        "decision 2 carries no date, user and pull",
        "decision 3 is pending, and carries more",
        "'shipped' is not a ledger state",
    ]


def test_ledger_retirements_agree_in_both_sections(tmp_path):
    """Ledger spec §2 decision 3: a retired decision stays, retired in both places."""
    retired = f"{AGREEMENT}; agreed 2026-01-01, {{pull}}`1`"
    entries = entry(1, RETIRED_STATE, retired) + entry(2, AGREED, AGREEMENT)
    rows = (
        f"| 1 | {VERIFIED} (2026-01-01, {{pull}}`1`) | `x.py` |\n"
        f"| 2 | {LEDGER_RETIRED} (2026-01-01, {{pull}}`1`) | |\n"
    )
    path, _ = ledgered(tmp_path, entries, rows)

    assert faults(ledger_retirements(path, path.read_text(encoding="utf-8"))) == [
        "decision 1 is retired in one section and not the other",
        "decision 2 is retired in one section and not the other",
    ]


def test_ledger_evidence_must_exist_and_cite_its_decision(tmp_path):
    """Ledger spec §2 decision 6: a test is evidence only if it cites the decision."""
    entries = entry(1, AGREED, AGREEMENT) + entry(2, AGREED, AGREEMENT)
    entries += entry(3, AGREED, AGREEMENT)
    rows = (
        f"| 1 | {VERIFIED} (2026-01-01, {{pull}}`1`) | `tests/test_cites.py` |\n"
        f"| 2 | {VERIFIED} (2026-01-01, {{pull}}`1`) | `tests/test_gone.py` |\n"
        f"| 3 | {VERIFIED} (2026-01-01, {{pull}}`1`) | `tests/test_cites.py` |\n"
    )
    path, names = ledgered(tmp_path, entries, rows)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_cites.py").write_text(
        f'"""Holds demo spec {SECTION}2 decision 1."""\n', encoding="utf-8"
    )

    problems = ledger_evidence(
        path, path.read_text(encoding="utf-8"), names, root=tmp_path
    )

    assert faults(problems) == [
        "tests/test_gone.py does not exist",
        "tests/test_cites.py does not cite decision 3",
    ]


def test_ledger_complete_once_the_roadmap_is(tmp_path):
    """Ledger spec §2 decision 8: a done roadmap leaves no decision pending."""
    entries = entry(1, AGREED, AGREEMENT) + entry(2, AGREED, AGREEMENT)
    rows = f"| 1 | {PENDING} | |\n| 2 | {PENDING} | row 2 of {SECTION}3 |\n"
    roadmap = f"| 1 | a | {LANDED} (2026-01-01, {{pull}}`1`) |\n| 2 | b | candidate |\n"
    path, _ = ledgered(tmp_path, entries, rows, roadmap)
    text = path.read_text(encoding="utf-8")

    assert faults(ledger_complete(path, text)) == [
        "decision 1 is pending, and no row of the roadmap is left to deliver it"
    ]
    open_roadmap = text.replace("| 2 | b | candidate |", "| 2 | b | not started |")
    assert ledger_complete(path, open_roadmap) == []


def test_ledger_replacement_must_be_in_force(tmp_path):
    """Ledger spec §2 decision 3: what replaces a retired decision is in force."""
    retired = f"{AGREEMENT}; agreed 2026-01-01, {{pull}}`1`"
    entries = (
        f"1. **{RETIRED_STATE}** ({retired}) — **One.** "
        f"replaced by {SECTION}2 decision 2.\n"
        f"2. **{RETIRED_STATE}** ({retired}) — **Two.** "
        f"replaced by {SECTION}2 decision 9.\n"
    )
    path, names = ledgered(tmp_path, entries, "")
    text = path.read_text(encoding="utf-8")
    decided = {decision_anchor("demo-spec", d.number): d for d in decisions(text)}

    assert faults(ledger_replacements(path, text, names, decided)) == [
        f"replaced by {SECTION}2 decision 2, which is not in force",
        f"replaced by {SECTION}2 decision 9, no decision",
    ]


def test_ledger_replacement_reads_any_case_and_only_decisions(tmp_path):
    """Ledger spec §2 decision 3: any case names a replacement; a section never does."""
    retired = f"{AGREEMENT}; agreed 2026-01-01, {{pull}}`1`"
    entries = (
        f"1. **{RETIRED_STATE}** ({retired}) — **One.** It was replaced by "
        f"{SECTION}3's rule; replaced by {SECTION}2 decision 2.\n"
        + entry(2, AGREED, AGREEMENT)
    )
    rows = (
        f"| 1 | {LEDGER_RETIRED} (2026-01-01, {{pull}}`1`) | "
        f"Replaced by {SECTION}2 decision 9 |\n| 2 | {PENDING} | |\n"
    )
    path, names = ledgered(tmp_path, entries, rows)
    text = path.read_text(encoding="utf-8")
    decided = {decision_anchor("demo-spec", d.number): d for d in decisions(text)}

    assert faults(ledger_replacements(path, text, names, decided)) == [
        f"replaced by {SECTION}2 decision 9, no decision"
    ]


@pytest.fixture(scope="module")
def decided(specs, names) -> dict[str, Decision]:
    """Map each decision's anchor in the collection to its entry."""
    return {
        decision_anchor(names.owners[spec], d.number): d
        for spec in specs
        if spec in names.owners
        for d in decisions(spec.read_text(encoding="utf-8"))
    }


@pytest.mark.parametrize(
    "spec",
    [s for s in specifications() if s.name not in UNLEDGERED],
    ids=lambda path: path.name,
)
def test_every_ledgered_specification_holds_its_ledger(spec, names, decided):
    """Ledger (item 9): ledger spec §2 decision 13, every rule on every ledger."""
    text = spec.read_text(encoding="utf-8")
    problems = (
        ledger_entries(spec, text)
        + ledger_table(spec, text)
        + ledger_retirements(spec, text)
        + ledger_evidence(spec, text, names)
        + ledger_complete(spec, text)
        + ledger_replacements(spec, text, names, decided)
    )

    assert not problems, "\n".join(problems)


def test_unledgered_names_specifications_still_waiting(specs):
    """An exemption cannot outlive the row of ledger spec §8 that ends it."""
    names = {spec.name for spec in specs}
    rows = roadmap_rows(
        (SPECS / "2026-10-30-decision-ledger-design.md").read_text(encoding="utf-8")
    )

    assert set(UNLEDGERED) <= names
    assert not [
        name for name, row in UNLEDGERED.items() if rows[str(row)].startswith(LANDED)
    ]


def test_ledger_evidence_must_be_a_test_file(tmp_path):
    """Ledger spec §2 decision 6: evidence is a test, not any file that cites one."""
    entries = entry(1, AGREED, AGREEMENT)
    rows = f"| 1 | {VERIFIED} (2026-01-01, {{pull}}`1`) | `docs/cites.md` |\n"
    path, names = ledgered(tmp_path, entries, rows)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "cites.md").write_text(
        f"Holds demo spec {SECTION}2 decision 1.\n", encoding="utf-8"
    )

    problems = ledger_evidence(
        path, path.read_text(encoding="utf-8"), names, root=tmp_path
    )

    assert faults(problems) == ["docs/cites.md is not a test file"]


def test_ledger_dates_are_calendar_dates(tmp_path):
    """Ledger spec §2 decision 4: a date of the right shape that no calendar holds."""
    retired = "2026-02-30, {user}`bjlittle`, {pull}`1`; agreed 2026-13-01, {pull}`1`"
    entries = entry(1, AGREED, "2026-02-30, {user}`bjlittle`, {pull}`1`")
    entries += entry(2, RETIRED_STATE, retired)
    rows = (
        f"| 1 | {VERIFIED} (2026-02-30, {{pull}}`1`) | `x.py` |\n"
        f"| 2 | {LEDGER_RETIRED} (2026-02-30, {{pull}}`1`) | |\n"
    )
    path, _ = ledgered(tmp_path, entries, rows)
    text = path.read_text(encoding="utf-8")

    assert faults(ledger_entries(path, text)) == [
        "decision 1 carries 2026-02-30, which is not a date",
        "decision 2 carries 2026-02-30, which is not a date",
        "decision 2 carries 2026-13-01, which is not a date",
    ]
    assert faults(ledger_table(path, text)) == [
        "decision 1 carries 2026-02-30, which is not a date",
        "decision 2 carries 2026-02-30, which is not a date",
    ]


def test_ledger_sign_off_says_what_was_checked(tmp_path):
    """Ledger spec §2 decision 6: a sign-off says what the reviewer checked."""
    entries = entry(1, AGREED, AGREEMENT)
    rows = f"| 1 | {SIGNED_OFF} (2026-01-01, {{user}}`bjlittle`, {{pull}}`1`) | |\n"
    path, _ = ledgered(tmp_path, entries, rows)

    assert faults(ledger_table(path, path.read_text(encoding="utf-8"))) == [
        "decision 1 is signed off, and says nothing of what was checked"
    ]


def test_statuses_reads_past_an_escaped_pipe():
    """A scope may hold an escaped pipe, which does not move the Status column."""
    text = (
        "(demo-spec-1)=\n## 1. Roadmap\n\n| # | Scope | Status |\n|---|---|---|\n"
        "| 1 | a \\| b | not started |\n"
    )

    assert [status for _, _, status in statuses(text)] == ["not started"]
    assert roadmap_rows(text) == {"1": "not started"}


def test_ledger_entries_wants_a_title(tmp_path):
    """Ledger spec §2 decision 2: an untitled decision has nothing to be paired by."""
    entries = f"1. **{AGREED}** ({AGREEMENT}) — Its reasoning, untitled.\n"
    path, _ = ledgered(tmp_path, entries, "")

    assert faults(ledger_entries(path, path.read_text(encoding="utf-8"))) == [
        "decision 1 has no title"
    ]


def test_ledger_rules_read_states_without_their_variation_selector(tmp_path):
    """Ledger spec §2 decision 9: a state typed without U+FE0F is the same state."""
    plain = citations.VS16
    retired = f"{AGREEMENT}; agreed 2026-01-01, {{pull}}`1`"
    entries = entry(1, RETIRED_STATE.replace(plain, ""), retired)
    entries += entry(2, AGREED, AGREEMENT)
    rows = (
        f"| 1 | {LEDGER_RETIRED.replace(plain, '')} (2026-01-01, {{pull}}`1`) | |\n"
        f"| 2 | {SIGNED_OFF.replace(plain, '')} (2026-01-01, {{user}}`bjlittle`, "
        "{pull}`1`) | Checked. |\n"
    )
    path, _ = ledgered(tmp_path, entries, rows)
    text = path.read_text(encoding="utf-8")

    assert ledger_entries(path, text) == []
    assert ledger_table(path, text) == []
    assert ledger_retirements(path, text) == []


#: Open Items (items spec §3.7): the states and parts of items spec §3.2, from the
#: grammar, which builds them by name.
OPEN = citations.OPEN
DEFERRED = citations.DEFERRED
RESOLVED = citations.RESOLVED
ABANDONED = citations.ABANDONED
GRADUATED = citations.GRADUATED
ITEMED_STATES = citations.ITEMED_STATES
SETTLED = (RESOLVED, ABANDONED, GRADUATED)
FOUND = citations.FOUND
OWED = citations.OWED
MOVED = citations.MOVED
TICKET = citations.TICKET
DOT = citations.DOT
items = citations.items
Item = citations.Item
Row = citations.Row
row_anchor = citations.row_anchor

#: The specifications whose open items are not yet in the grammar of
#: items spec §3.2, each with the row of items spec §8 that brings it in, and read
#: until then in that of docs spec §3.6 by :func:`status`. Each of those rows
#: shortens this, and the last empties it.
UNITEMED = {
    "2026-10-06-type-coverage-design.md": 3,
    "2026-10-23-globe-first-crs-design.md": 4,
    "2026-10-26-globe-heights-layers-design.md": 5,
    "2026-10-27-globe-scene-design.md": 5,
    "2026-10-28-heights-as-data-design.md": 5,
    "2026-10-30-decision-ledger-design.md": 5,
}

#: Where an item was found, the row that owes it, and the issue that tracks it.
FOUND_AT = f"{FOUND} 2026-01-01, {{pull}}`1`"
OWED_BY = f"{OWED} row 2 of {SECTION}2"
TICKETED = f"{TICKET} {{issue}}`5`"


def entry_item(number: int, state: str, *parts: str, title: str = "An item.") -> str:
    """Write an open item's entry, state first and its parts separated."""
    return f"{number}. **{state}** ({DOT.join(parts)}) — **{title}** Its reasoning.\n"


def graduation(row: int) -> str:
    """Write the date and pull request of a graduation to ``row``, and the row."""
    return f"2026-01-01, {{pull}}`1`, to row {row} of {SECTION}2"


def moved(row: int, day: str = "2026-01-02") -> str:
    """Write the part recording a move from ``row``."""
    return f"{MOVED} row {row}, {day}, {{pull}}`2`"


#: A roadmap whose first row has landed and whose others have not.
ROADMAP = (
    f"| 1 | a | {LANDED} (2026-01-01, {{pull}}`1`) |\n"
    "| 2 | b | not started |\n| 3 | c | candidate: a trigger |\n"
)


def itemed(
    tmp_path: Path, entries: str, roadmap: str = ROADMAP
) -> tuple[Path, Namespace]:
    """Write a ``demo spec`` with a roadmap in its second section and open items."""
    return demo(
        tmp_path,
        "(demo-spec-1)=\n## 1. Purpose\n\n"
        "(demo-spec-2)=\n## 2. Roadmap\n\n| # | Scope | Status |\n|---|---|---|\n"
        f"{roadmap}\n"
        f"(demo-spec-3)=\n## 3. Open Items\n\nThe items.\n\n{entries}",
    )


#: What a move records: the row it left, then its date and pull request.
MOVE = re.compile(rf"row{GAP}{MEMBER},")
#: Any markdown heading, numbered or not, and how deep it sits.
ANY_HEADING = re.compile(r"^(?P<depth>#{1,6})\s+(?P<title>\S.*?)\s*$")


def own_row(path: Path, text: str, cited: str, names: Namespace) -> Row | str:
    """Find the row of a specification's own roadmap that ``cited`` names.

    The citation is read by the grammar, as every citation is, so that this rule
    and the build can never disagree about which row it names.

    Parameters
    ----------
    path : Path
        The specification.
    text : str
        Its text.
    cited : str
        The citation, as ``row 5 of §10``, which may carry the specification's own
        prefix.
    names : Namespace
        The namespace it is read in.

    Returns
    -------
    Row or str
        The row, or what is wrong with the citation, completing "which ...".

    """
    owner = names.owners.get(path)
    slug = citations.cited_row(cited, owner, names)
    if slug is None:
        return "names no row"
    if LABEL.match(slug)["prefix"] != owner:
        return "is another specification's"
    row = next(
        (
            r
            for r in citations.rows(text)
            if row_anchor(owner, r.section, r.row) == slug
        ),
        None,
    )
    return "does not exist" if row is None else row


def entry_faults(item: Item) -> list[str]:
    """Say what is wrong with the parts of an item's parenthetical, if anything."""
    written = citations.provenance(item.carried)
    settled = item.state in SETTLED
    faults = []
    if settled:
        lead = written[0][1] if written and written[0][0] is None else ""
        written = written[1:] if lead else written
        if item.state == GRADUATED:
            if not (DATE.search(lead) and PULL.search(lead) and item.graduated):
                faults.append("graduates with no date, pull and row")
        elif not (DATE.search(lead) and REFERENCE.search(lead)):
            faults.append("is settled with no date and reference")
    kinds = [kind for kind, _ in written]
    faults += [
        f"carries {said!r}, which is no part" for kind, said in written if not kind
    ]
    if FOUND not in kinds:
        faults.append(f"carries no {FOUND}")
    elif not (DATE.search(item.found) and PULL.search(item.found)):
        faults.append("was found with no date and pull")
    if not settled:
        faults += [f"carries no {part}" for part in (OWED, TICKET) if part not in kinds]
    elif OWED in kinds:
        faults.append(f"is settled, and still carries {OWED}")
    ticket = next((said for kind, said in written if kind == TICKET), None)
    if ticket is not None and item.issue is None:
        faults.append(f"carries {TICKET} {ticket}, which is no issue")
    faults += [
        f"carries {part} twice"
        for part in (FOUND, OWED, TICKET)
        if kinds.count(part) > 1
    ]
    ranks = [citations.PARTS.index(kind) for kind in kinds if kind]
    if ranks != sorted(ranks):
        faults.append("carries its parts out of order")
    return faults


def item_entries(path: Path, text: str) -> list[str]:
    """Find each fault in an item's entry, item 1 of items spec §3.7.

    Each item of the Open Items section is a numbered entry opening with a state,
    and its parenthetical carries the parts its state needs, in order: every item
    where it was found, an open or deferred one the row that owes it and its
    issue, and a settled one its date and reference first. A settled item carries
    its issue only if it has one, as one settled before items spec §3.2 may lead
    with the issue or link that settled it instead (docs spec §3.6).
    """
    titles = [h["title"] for _, line in read_lines(text) if (h := HEADING.match(line))]
    if citations.OPEN_ITEMS.casefold() not in {title.casefold() for title in titles}:
        return [f"{where(path, 1)}: it has no Open Items section"]
    found = items(text)
    opened = {item.line for item in found}
    problems = unreached(path, text)
    for number, line in citations._titled(text, citations.OPEN_ITEMS):
        if ITEM.match(line) is None or number in opened:
            continue
        if line.startswith(("-", "*")):
            problems.append(
                f"{where(path, number)}: an item is a bullet, not a numbered entry"
            )
        else:
            problems.append(
                f"{where(path, number)}: an item written after its list has ended"
            )
    numbers = [item.number for item in found]
    if numbers != list(range(1, len(found) + 1)):
        problems.append(f"{where(path, 1)}: items are numbered {numbers}")
    for item in found:
        at = where(path, item.line)
        if item.state is None:
            problems.append(f"{at}: item {item.number} opens with no state")
        elif not item.title:
            problems.append(f"{at}: item {item.number} has no title")
        else:
            problems += [f"{at}: item {item.number} {f}" for f in entry_faults(item)]
            problems += [
                f"{at}: item {item.number} carries {bad}, which is not a date"
                for bad in undated(item.carried)
            ]
    return problems


def unreached(path: Path, text: str) -> list[str]:
    """Find a heading that puts items beyond the reach of :func:`items`.

    The items are those of the first section titled Open Items, up to its next
    heading, so a subsection of it, or a second section of that title, would hold
    items no rule reads.
    """
    problems = []
    depth: int | None = None
    seen = False
    for number, line in read_lines(text):
        heading = ANY_HEADING.match(line)
        if heading is None:
            continue
        level = len(heading["depth"])
        numbered = HEADING.match(line)
        title = numbered["title"] if numbered else heading["title"]
        if depth is not None and level > depth:
            problems.append(
                f"{where(path, number)}: a heading inside Open Items, under which "
                "items go unread"
            )
            continue
        depth = None
        if title.casefold() == citations.OPEN_ITEMS.casefold():
            if seen:
                problems.append(
                    f"{where(path, number)}: a second Open Items section, whose items "
                    "go unread"
                )
            seen, depth = True, level
    return problems


def item_owed(path: Path, text: str, names: Namespace) -> list[str]:
    """Find an item owed by no row, or by one landed, item 2 of items spec §3.7.

    This is the landing gate of items spec §3.5: a row may not land while an open
    or deferred item still names it.
    """
    problems = []
    for item in items(text):
        if item.state not in (OPEN, DEFERRED) or item.owed is None:
            continue
        row = own_row(path, text, item.owed, names)
        if isinstance(row, str):
            why = row
        elif row.status.startswith(LANDED):
            why = "has landed"
        else:
            continue
        problems.append(
            f"{where(path, item.line)}: item {item.number} is owed by {item.owed}, "
            f"which {why}"
        )
    return problems


def item_moves(path: Path, text: str) -> list[str]:
    """Find an item moved too often or not at all, item 3 of items spec §3.7."""
    problems = []
    for item in items(text):
        at = where(path, item.line)
        count = len(item.moves)
        if count > 2:
            problems.append(
                f"{at}: item {item.number} carries {count} {MOVED}, and must settle "
                "or graduate instead"
            )
        elif item.state == OPEN and count:
            problems.append(
                f"{at}: item {item.number} is open, and carries {MOVED}: it is deferred"
            )
        elif item.state == DEFERRED and not count:
            problems.append(
                f"{at}: item {item.number} is deferred, and carries no {MOVED}"
            )
        problems += [
            f"{at}: item {item.number} carries {MOVED} {move}, which is not a row, "
            "date and pull"
            for move in item.moves
            if not (MOVE.match(move) and DATE.search(move) and PULL.search(move))
        ]
    return problems


def item_graduated(path: Path, text: str, names: Namespace) -> list[str]:
    """Find a graduation to a row not citing its issue, items spec §3.7 item 4.

    The item's issue moves with it to the row it became (items spec §3.6), so
    that the row cites it.
    """
    problems = []
    for item in items(text):
        if item.state != GRADUATED or item.graduated is None:
            continue
        at = where(path, item.line)
        if item.issue is None:
            problems.append(
                f"{at}: item {item.number} graduates with no {TICKET} for its row "
                "to cite"
            )
            continue
        row = own_row(path, text, item.graduated, names)
        cited = f"{{issue}}`{item.issue}`"
        if isinstance(row, str):
            why = row
        elif cited not in f"{row.scope} {row.status}":
            why = f"does not cite {cited}"
        else:
            continue
        problems.append(
            f"{at}: item {item.number} graduates to {item.graduated}, which {why}"
        )
    return problems


def item_issues(texts: Mapping[Path, str]) -> list[str]:
    """Find an issue cited by two items, item 5 of items spec §3.7.

    The rule runs across the collection, since an item of one specification may
    not share its issue with one of another.
    """
    first: dict[int, str] = {}
    problems = []
    for path, text in texts.items():
        for item in items(text):
            if item.issue is None:
                continue
            at = where(path, item.line)
            if item.issue in first:
                problems.append(
                    f"{at}: item {item.number} cites {{issue}}`{item.issue}`, as "
                    f"{first[item.issue]} does"
                )
            else:
                first[item.issue] = at
    return problems


def test_items_reads_each_part_of_an_entry():
    """Items spec §3.2: the state, each part, and the title, wrapped or not."""
    text = (
        "(demo-spec-7)=\n## 7. Open items\n\n"
        f"1. **{DEFERRED}** ({FOUND_AT} {DOT.strip()}\n"
        f"   {OWED_BY} {DOT.strip()} {moved(1)} {DOT.strip()} {TICKETED})\n"
        "   — **A deferred\n   item.** Its reasoning.\n"
        f"2. **{GRADUATED}** (2026-02-01, {{pull}}`3`, to row 3 of {SECTION}2"
        f"{DOT}{FOUND_AT}) — **A graduated item.**\n"
    )

    deferred, graduated = items(text)

    assert deferred == Item(
        number=1,
        line=4,
        state=DEFERRED,
        settled="",
        found="2026-01-01, {pull}`1`",
        owed=f"row 2 of {SECTION}2",
        moves=("row 1, 2026-01-02, {pull}`2`",),
        issue=5,
        graduated=None,
        title="A deferred item.",
        body="Its reasoning.",
        carried=deferred.carried,
    )
    assert graduated.state == GRADUATED
    assert graduated.settled == f"2026-02-01, {{pull}}`3`, to row 3 of {SECTION}2"
    assert graduated.graduated == f"row 3 of {SECTION}2"
    assert (graduated.owed, graduated.issue, graduated.moves) == (None, None, ())


def test_items_reads_states_and_parts_without_their_variation_selector():
    """Items spec §3.2: an emoji typed without U+FE0F is the same state or part."""
    plain = citations.VS16
    text = "(demo-spec-7)=\n## 7. Open Items\n\n" + entry_item(
        1,
        DEFERRED.replace(plain, ""),
        FOUND_AT,
        OWED_BY,
        moved(1).replace(plain, ""),
        TICKETED,
    )

    (deferred,) = items(text)

    assert deferred.state == DEFERRED
    assert len(deferred.moves) == 1


def test_item_entries_finds_an_entry_missing_its_found(tmp_path):
    """Items spec §3.7 item 1: each state carries the parts it needs, in order.

    Holds items spec §2 decision 2, items spec §2 decision 3, items spec §2 decision 4.
    """
    entries = (
        entry_item(1, OPEN, OWED_BY, TICKETED)
        + entry_item(2, OPEN, FOUND_AT, OWED_BY)
        + entry_item(3, OPEN, FOUND_AT, TICKETED)
        + entry_item(4, OPEN, FOUND_AT, TICKETED, OWED_BY)
        + entry_item(5, OPEN, FOUND_AT, OWED_BY, "a note", TICKETED)
        + entry_item(6, OPEN, f"{FOUND} 2026-01-01", OWED_BY, TICKETED)
        + entry_item(7, OPEN, FOUND_AT, OWED_BY, f"{TICKET} {{pull}}`5`")
        + entry_item(8, RESOLVED, FOUND_AT, TICKETED)
        + entry_item(9, RESOLVED, "2026-01-01, {pull}`1`", FOUND_AT, OWED_BY)
        + entry_item(10, GRADUATED, "2026-01-01, {pull}`1`", FOUND_AT)
    )
    path, _ = itemed(tmp_path, entries)

    assert faults(item_entries(path, path.read_text(encoding="utf-8"))) == [
        f"item 1 carries no {FOUND}",
        f"item 2 carries no {TICKET}",
        f"item 3 carries no {OWED}",
        "item 4 carries its parts out of order",
        "item 5 carries 'a note', which is no part",
        "item 6 was found with no date and pull",
        f"item 7 carries {TICKET} {{pull}}`5`, which is no issue",
        "item 8 is settled with no date and reference",
        f"item 9 is settled, and still carries {OWED}",
        "item 10 graduates with no date, pull and row",
    ]


def test_item_entries_passes_a_settled_item_without_its_issue(tmp_path):
    """Items spec §3.2: an item settled before it keeps its history, with no issue.

    Holds items spec §2 decision 4.
    """
    entries = (
        entry_item(1, RESOLVED, "2026-01-01, {issue}`3`", FOUND_AT)
        + entry_item(2, ABANDONED, "2026-01-01, [x](https://github.com/o/r/pull/1)")
        + entry_item(3, RESOLVED, "2026-01-01, {pull}`1`", FOUND_AT, TICKETED)
    )
    path, _ = itemed(tmp_path, entries)
    text = path.read_text(encoding="utf-8")

    assert faults(item_entries(path, text)) == [f"item 2 carries no {FOUND}"]
    fixed = text.replace("pull/1)", f"pull/1){DOT}{FOUND_AT}")
    assert item_entries(path, fixed) == []


def test_item_entries_wants_numbered_titled_items_in_one_list(tmp_path):
    """Items spec §3.2: a numbered entry, with a title, in the section's list.

    Holds items spec §2 decision 1.
    """
    entries = (
        f"1. **{OPEN}** ({FOUND_AT}{DOT}{OWED_BY}{DOT}{TICKETED}) — Untitled.\n"
        + entry_item(3, OPEN, FOUND_AT, OWED_BY, TICKETED)
        + f"\nA paragraph.\n\n- **{OPEN}** ({FOUND_AT}) — **A bullet.**\n"
        + entry_item(4, OPEN, FOUND_AT, OWED_BY, TICKETED)
    )
    path, _ = itemed(tmp_path, entries)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    first = next(n for n, line in enumerate(lines, 1) if line.startswith("1. "))
    bullet = lines.index(f"- **{OPEN}** ({FOUND_AT}) — **A bullet.**") + 1

    assert item_entries(path, text) == [
        f"{where(path, bullet)}: an item is a bullet, not a numbered entry",
        f"{where(path, bullet + 1)}: an item written after its list has ended",
        f"{where(path, 1)}: items are numbered [1, 3]",
        f"{where(path, first)}: item 1 has no title",
    ]
    gaps = text.replace("## 3. Open Items", "## 3. Gaps")
    assert faults(item_entries(path, gaps)) == ["it has no Open Items section"]


@pytest.mark.parametrize(
    "after",
    [
        "(demo-spec-3-1)=\n### 3.1 More\n\n",
        "(demo-spec-4)=\n## 4. Open items\n\n",
    ],
    ids=["subsection", "second-section"],
)
def test_item_entries_reports_items_no_rule_reads(tmp_path, after):
    """Review Focus 4 of its plan: no item sits where :func:`items` cannot read it.

    An item under a subsection of Open Items, or under a second section of that
    title, would pass every rule unread, as :func:`status` reads only the items
    of a specification that :data:`UNITEMED` names.
    """
    entries = entry_item(1, OPEN, FOUND_AT, OWED_BY, TICKETED)
    hidden = "1. **Open** - **Unread.**\n"
    path, _ = itemed(tmp_path, f"{entries}\n{after}{hidden}")
    text = path.read_text(encoding="utf-8")
    heading = next(
        n
        for n, line in enumerate(text.splitlines(), 1)
        if line.startswith("#") and n > items(text)[0].line
    )
    expected = (
        "a heading inside Open Items, under which items go unread"
        if after.count("#") == 3
        else "a second Open Items section, whose items go unread"
    )

    assert item_entries(path, text) == [f"{where(path, heading)}: {expected}"]


def test_item_owed_names_a_row_that_has_not_landed(tmp_path):
    """Items spec §3.7 item 2, the landing gate of items spec §3.5.

    Holds items spec §2 decision 3, items spec §2 decision 5.
    """
    entries = (
        entry_item(1, OPEN, FOUND_AT, f"{OWED} row 1 of {SECTION}2", TICKETED)
        + entry_item(2, OPEN, FOUND_AT, f"{OWED} row 9 of {SECTION}2", TICKETED)
        + entry_item(3, OPEN, FOUND_AT, f"{OWED} row 2 of other spec {SECTION}2")
        + entry_item(4, OPEN, FOUND_AT, f"{OWED} the next release", TICKETED)
        + entry_item(5, DEFERRED, FOUND_AT, OWED_BY, moved(1), TICKETED)
        + entry_item(6, OPEN, FOUND_AT, f"{OWED} row 3 of demo spec {SECTION}2")
        + entry_item(7, OPEN, FOUND_AT, f"{OWED} row 6a of {SECTION}2", TICKETED)
        + entry_item(8, OPEN, FOUND_AT, f"{OWED} row 1 of Demo Spec {SECTION}2")
        + entry_item(9, OPEN, FOUND_AT, f"{OWED} rows 2 to 3 of {SECTION}2")
    )
    lettered = f"| 6a | d | {LANDED} (2026-01-01, {{pull}}`1`) |\n"
    path, _ = itemed(tmp_path, entries, ROADMAP + lettered)
    other = tmp_path / "2026-01-02-other-design.md"
    other.write_text(
        "(other-spec-2)=\n## 2. Roadmap\n\n| # | Scope | Status |\n|---|---|---|\n"
        "| 2 | b | not started |\n",
        encoding="utf-8",
    )
    names = namespace([path, other])
    others = "another specification's"

    assert faults(item_owed(path, path.read_text(encoding="utf-8"), names)) == [
        f"item 1 is owed by row 1 of {SECTION}2, which has landed",
        f"item 2 is owed by row 9 of {SECTION}2, which does not exist",
        f"item 3 is owed by row 2 of other spec {SECTION}2, which is {others}",
        "item 4 is owed by the next release, which names no row",
        f"item 7 is owed by row 6a of {SECTION}2, which has landed",
        f"item 8 is owed by row 1 of Demo Spec {SECTION}2, which has landed",
        f"item 9 is owed by rows 2 to 3 of {SECTION}2, which names no row",
    ]


def test_item_moves_wants_one_or_two_for_a_deferred_item(tmp_path):
    """Items spec §3.7 item 3: none while open, one or two when deferred, not three.

    Holds items spec §2 decision 6, items spec §2 decision 7.
    """
    entries = (
        entry_item(1, DEFERRED, FOUND_AT, OWED_BY, TICKETED)
        + entry_item(2, DEFERRED, FOUND_AT, OWED_BY, moved(1), TICKETED)
        + entry_item(3, DEFERRED, FOUND_AT, OWED_BY, moved(1), moved(1), TICKETED)
        + entry_item(
            4, DEFERRED, FOUND_AT, OWED_BY, moved(1), moved(1), moved(1), TICKETED
        )
        + entry_item(5, OPEN, FOUND_AT, OWED_BY, moved(1), TICKETED)
        + entry_item(6, DEFERRED, FOUND_AT, OWED_BY, f"{MOVED} row 1", TICKETED)
    )
    path, _ = itemed(tmp_path, entries)

    assert faults(item_moves(path, path.read_text(encoding="utf-8"))) == [
        f"item 1 is deferred, and carries no {MOVED}",
        f"item 4 carries 3 {MOVED}, and must settle or graduate instead",
        f"item 5 is open, and carries {MOVED}: it is deferred",
        f"item 6 carries {MOVED} row 1, which is not a row, date and pull",
    ]


def test_item_graduated_names_a_row_that_cites_its_issue(tmp_path):
    """Items spec §3.7 item 4: the row an item became carries its issue.

    Holds items spec §2 decision 7.
    """
    roadmap = ROADMAP + "| 4 | An item, {issue}`5` | not started |\n"
    entries = (
        entry_item(1, GRADUATED, graduation(4), FOUND_AT, TICKETED)
        + entry_item(2, GRADUATED, graduation(3), FOUND_AT, TICKETED)
        + entry_item(3, GRADUATED, graduation(8), FOUND_AT, TICKETED)
        + entry_item(4, GRADUATED, graduation(4), FOUND_AT)
    )
    path, names = itemed(tmp_path, entries, roadmap)
    text = path.read_text(encoding="utf-8")

    assert faults(item_graduated(path, text, names)) == [
        f"item 2 graduates to row 3 of {SECTION}2, which does not cite {{issue}}`5`",
        f"item 3 graduates to row 8 of {SECTION}2, which does not exist",
        f"item 4 graduates with no {TICKET} for its row to cite",
    ]


def test_item_issues_finds_two_items_citing_one_issue(tmp_path):
    """Items spec §3.7 item 5: one issue per item, across the collection.

    Holds items spec §2 decision 2.
    """
    first = itemed(tmp_path, entry_item(1, OPEN, FOUND_AT, OWED_BY, TICKETED))[0]
    second = tmp_path / "2026-01-02-other-design.md"
    second.write_text(
        "(other-spec-8)=\n## 8. Open Items\n\n"
        + entry_item(1, OPEN, FOUND_AT, OWED_BY, f"{TICKET} {{issue}}`6`")
        + entry_item(2, RESOLVED, "2026-01-01, {pull}`1`", FOUND_AT, TICKETED)
        + entry_item(3, OPEN, FOUND_AT, OWED_BY, f"{TICKET} {{issue}}`7`"),
        encoding="utf-8",
    )
    texts = {path: path.read_text(encoding="utf-8") for path in (first, second)}
    (cited,) = items(texts[first])
    repeated = items(texts[second])[1]

    expected = f"item 2 cites {{issue}}`5`, as {where(first, cited.line)} does"

    assert item_issues(texts) == [f"{where(second, repeated.line)}: {expected}"]


def test_each_grammar_is_read_where_the_other_is_expected(tmp_path):
    """Review Focus 4 of its plan: neither grammar passes unread in the other's place.

    An item in the grammar of docs spec §3.6 has no state to the rules of
    items spec §3.7, and an item in that of items spec §3.2 has no status to the
    rule of docs spec §3.6, which reads the specifications :data:`UNITEMED` names.

    Holds items spec §2 decision 9.
    """
    old = "1. **Open** ({issue}`5`) — **An item.** Its reasoning.\n"
    new = entry_item(1, OPEN, FOUND_AT, OWED_BY, TICKETED)
    path, _ = itemed(tmp_path, old)
    text = path.read_text(encoding="utf-8")

    assert faults(item_entries(path, text)) == ["item 1 opens with no state"]
    assert status(path, text, unitemed=True) == []
    assert faults(status(path, text.replace(old, new), unitemed=True)) == [
        f"{OPEN!r} is not a status"
    ]
    assert item_entries(path, text.replace(old, new)) == []
    assert status(path, text) == []


@pytest.mark.parametrize(
    "spec",
    [s for s in specifications() if s.name not in UNITEMED],
    ids=lambda path: path.name,
)
def test_every_itemed_specification_holds_its_items(spec, names):
    """Open Items (item 10): items spec §3.7, every rule on every item.

    Holds items spec §2 decision 9.
    """
    text = spec.read_text(encoding="utf-8")
    problems = (
        item_entries(spec, text)
        + item_owed(spec, text, names)
        + item_moves(spec, text)
        + item_graduated(spec, text, names)
    )

    assert not problems, "\n".join(problems)


def test_no_two_items_cite_one_issue(specs):
    """Open Items (item 10): items spec §3.7 item 5, across the collection."""
    texts = {
        spec: spec.read_text(encoding="utf-8")
        for spec in specs
        if spec.name not in UNITEMED
    }
    problems = item_issues(texts)

    assert not problems, "\n".join(problems)


def test_unitemed_names_specifications_still_waiting(specs):
    """An exemption cannot outlive the row of items spec §8 that ends it."""
    names = {spec.name for spec in specs}
    rows = roadmap_rows(
        (SPECS / "2026-11-02-open-items-design.md").read_text(encoding="utf-8")
    )

    assert set(UNITEMED) <= names
    assert not [
        name for name, row in UNITEMED.items() if rows[str(row)].startswith(LANDED)
    ]

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

import ast
import contextlib
from dataclasses import dataclass
from datetime import date
import io
from pathlib import Path
import re
import tokenize
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

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


def test_prose_inside_a_directive_fence_is_read():
    """An admonition renders its body, so the body is prose and is read."""
    text = "a\n```{note}\nb\n```\nc\n"

    assert [line for _, line in read_lines(text)] == ["a", "b", "c"]


def test_code_inside_a_directive_fence_stays_skipped():
    """A code block nested in an admonition is still code."""
    text = "````{note}\nb\n```python\n(demo-spec-9)=\n```\nc\n````\nd\n"

    assert [line for _, line in read_lines(text)] == ["b", "c", "d"]


def test_a_directive_whose_body_is_code_is_skipped():
    """A code-block directive is a fence by another name."""
    text = "```{code-block} python\n(demo-spec-9)=\n```\nb\n"

    assert [line for _, line in read_lines(text)] == ["b"]


def test_inline_code_opening_a_line_is_no_fence():
    """A backtick fence's info string cannot hold a backtick."""
    text = "```x``` opens the line\nb\n"

    assert [line for _, line in read_lines(text)] == ["```x``` opens the line", "b"]


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
    for name, marker in (("venv", "pyvenv.cfg"), ("htmlcov", "x"), ("nested", ".git")):
        (tmp_path / name).mkdir()
        (tmp_path / name / marker).write_text("home = /usr\n", encoding="utf-8")
        (tmp_path / name / "file.txt").write_text("text\n", encoding="utf-8")

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


def test_form_finds_each_citation_without_its_sign(tmp_path):
    """The sign is what separates a citation from a sentence holding a number."""
    _, names = demo(tmp_path, DEMO)
    text = "# demo spec 2.1, and ``demo spec 9`` quoted as code\n"

    problems = form(tmp_path / "module.py", text, names)

    assert [p.split(": ", 1)[1] for p in problems] == [
        "'demo spec 2.1' has no section sign"
    ]


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
    """Form (item 4)."""
    problems = [p for path, text in texts.items() for p in form(path, text, names)]

    assert not problems, "\n".join(problems)


#: A role opened on a line that does not close it.
OPENED = re.compile(r"(?:\{ref\}|:ref:)`")


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


def agreement(path: Path, text: str, names: Namespace) -> list[str]:
    """Find each section role whose display text names another section."""
    owner = names.owners.get(path)
    problems = []
    for number, line in source_lines(path, text):
        plain, roles = prose(line)
        if OPENED.search(plain):
            problems.append(f"{where(path, number)}: a role broken across lines")
        for kind, body in roles:
            role = section_role(kind, body, names)
            if role is None:
                continue
            display, target = role
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


def crossed(path: Path, text: str) -> list[str]:
    """Find each line of a specification that a code span crosses.

    Code is blanked a line at a time, so a span wrapped across a line break leaves
    a stray backtick on either side, and on the second line that backtick pairs
    with the next one, hiding whatever role follows it from the agreement rule. A
    span therefore opens and closes on one line, which this makes loud.
    """
    return [
        f"{where(path, number)}: a code span crosses a line break"
        for number, line in read_lines(text)
        if "`" in prose(line)[0]
    ]


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
    """Agreement reads a line at a time, so a span must close where it opens."""
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


def statuses(text: str) -> Iterator[tuple[int, str, str]]:
    """Yield every roadmap Status cell, and every open item with its lines joined.

    A cell is read from any table whose header names a Status column, wherever
    the table sits, and the table ends where its rows do. An open item is any
    top-level list item under "Open items", numbered or bulleted, so an item that
    has lost its state is reported rather than passed over.

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
            cells = [cell.strip() for cell in table[0][1].strip().strip("|").split("|")]
            if "Status" in cells:
                column = cells.index("Status")
                for row, written in table[2:]:
                    found = [
                        cell.strip() for cell in written.strip().strip("|").split("|")
                    ]
                    yield row, "row", found[column] if column < len(found) else ""
            table = []
    item: list[str] = []
    start = 0
    for number, line in [*sections(text).get("Open items", []), (0, "")]:
        opened = ITEM.match(line)
        if opened or not line.strip():
            if item:
                yield start, "item", " ".join(item)
            item, start = ([opened["body"].strip()], number) if opened else ([], 0)
        elif item:
            item.append(line.strip())


def status(path: Path, text: str) -> list[str]:
    """Find each status outside the vocabulary, or terminal and unevidenced."""
    problems = []
    for number, kind, written in statuses(text):
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


def test_status_finds_a_date_no_calendar_holds(tmp_path):
    """A date of the right shape is still no date if no calendar holds it."""
    roadmap = (
        "(demo-spec-1)=\n## 1. Roadmap\n\n| # | Status |\n|---|---|\n"
        f"| 1 | {LANDED} (2026-02-30, {{pull}}`1`) |\n"
        f"| 2 | {LANDED} (2026-02-28, {{pull}}`1`) |\n\n"
        "(demo-spec-2)=\n## 2. Open items\n\n"
        "1. **Resolved** (2026-13-01, {issue}`2`) - **A.**\n"
    )
    path, _ = demo(tmp_path, roadmap)

    problems = status(path, path.read_text(encoding="utf-8"))

    assert [p.split(": ", 1)[1] for p in problems] == [
        f"{LANDED} carries 2026-02-30, which is not a date",
        "Resolved carries 2026-13-01, which is not a date",
    ]


def test_status_reads_bullets_and_any_status_table(tmp_path):
    """A bullet is an item, an item with no state is reported, any table is read."""
    body = (
        "(demo-spec-1)=\n## 1. Plan and status\n\n| # | Status |\n|---|---|\n"
        "| 1 | shipped |\n\n"
        "(demo-spec-2)=\n## 2. Open items\n\n"
        "- **shipped** - **A.**\n"
        "- **Resolved** (no date) - **B.**\n"
        "* plain text, its state forgotten\n"
    )
    path, _ = demo(tmp_path, body)

    problems = status(path, path.read_text(encoding="utf-8"))

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
    """Status (item 7)."""
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


def namespace_table(index: str) -> dict[str, str]:
    """Read the document each prefix names in the index's namespace table."""
    pattern = re.compile(
        rf"\*\s+-\s+``(?P<prefix>[^`]+?)\s*{SECTION}{ELLIPSIS}``\s*\n"
        r"\s+-\s+:doc:`(?P<doc>[^`]+)`"
    )
    return {match["prefix"]: match["doc"] for match in pattern.finditer(index)}


def test_front_matter_is_read_only_where_a_document_opens():
    """A rule quoted further down a page is not the page's front matter."""
    assert front_matter("---\norphan: true\n---\n\n# Title\n") == "orphan: true"
    assert front_matter("# Title\n\n---\norphan: true\n---\n") == ""


def test_no_specification_is_an_orphan(specs):
    """A specification is reached through the index, never left unlisted."""
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


#: Citations outside the specifications past which rows 2 to 4 of the roadmap
#: activate: five times the seven there were when the threshold was set.
CEILING = 35

#: The entry point by which the rendered-output gate of row 4 is wired in.
OUTPUT_GATE = "check_rendered_citations"


def outside(texts: dict[Path, str], names: Namespace) -> int:
    """Count the citations in every governed file that is not a specification.

    A section role counts as one. It is a citation written by hand, and retiring
    those is half of what row 2 buys.
    """
    count = 0
    for path, text in texts.items():
        if path in names.owners:
            continue
        for _, line in source_lines(path, text):
            plain, roles = prose(line)
            count += sum(1 for _ in scan(plain, names.signed, None))
            count += sum(
                section_role(kind, body, names) is not None for kind, body in roles
            )
    return count


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


def test_outside_counts_a_section_role_as_a_citation(tmp_path):
    """Row 2 retires the hand-written roles, so they count toward its trigger."""
    _, names = demo(tmp_path, DEMO)
    texts = {
        tmp_path / "guide.md": f"See {{ref}}`demo spec {SECTION}2 <demo-spec-2>`.\n"
        * CEILING,
        tmp_path / "guide.rst": f"See :ref:`demo spec {SECTION}1 <demo-spec-1>`.\n",
        tmp_path / "other.md": "See {ref}`the gallery <gallery>`.\n",
    }

    assert outside(texts, names) == CEILING + 1


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


def test_rows_2_to_4_wait_until_the_corpus_outgrows_review(texts, names):
    """Triggers (item 6): the scale at which the citation machinery is wanted."""
    count = outside(texts, names)

    assert count > 0, "no citation outside the specifications: the count is vacuous"
    assert count <= CEILING, (
        f"{count} citations outside the specifications, past {CEILING}: rows 2 "
        "to 4 of docs spec §4 have activated. Build them, or raise the ceiling "
        "there with the reason."
    )


def test_row_4_pairs_the_transform_with_its_output_gate():
    """Triggers (item 6): a transform the output gate does not check."""
    conf = (REPO / "docs" / "src" / "conf.py").read_text(encoding="utf-8")
    extensions = registered(conf)
    transforms = {name for name in extensions if "citation" in name}

    assert "myst_nb" in extensions, "the watch reads none of conf.py's extensions"
    wiring = [REPO / "pyproject.toml", *(REPO / ".github" / "workflows").glob("*.yml")]
    wired = any(OUTPUT_GATE in path.read_text(encoding="utf-8") for path in wiring)

    assert wired or not transforms, (
        f"{sorted(transforms)} registered without {OUTPUT_GATE}: row 4 of "
        "docs spec §4 is due."
    )

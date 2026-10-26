# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests of the citation grammar shared by the conventions test and the build.

The grammar is ``docs/src/_ext/geovista_citations.py``, a plain module rather
than an extension, loaded here by path as ``reading.py`` is. This module sits
inside the corpus the grammar governs, so its fixtures build the section sign
rather than write it, and cite a ``demo spec`` that no document declares.

"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from types import ModuleType

#: The grammar, beside the extensions that will import it.
GRAMMAR = (
    Path(__file__).parents[2] / "docs" / "src" / "_ext" / "geovista_citations.py"
).resolve()

#: The section sign, built rather than written: see the module docstring.
SECTION = "\N{SECTION SIGN}"

#: The ellipsis a citation prefix is declared with.
ELLIPSIS = "\N{HORIZONTAL ELLIPSIS}"

#: A specification of two sections, under the ``demo spec`` prefix.
DEMO = "(demo-spec-1)=\n## 1. Purpose\n\n(demo-spec-2)=\n## 2. Design\n"


@pytest.fixture(scope="module")
def citations() -> ModuleType:
    """Load the grammar by path, or reuse the copy already registered from it.

    A build imports the grammar by name, and so finds whichever copy is
    registered. Loading it again would make a second, whose dataclasses never
    equal the first's, so a copy registered from the same file is reused.

    Returns
    -------
    ModuleType
        The loaded module.

    """
    registered = sys.modules.get("geovista_citations")
    if registered is not None and Path(registered.__file__).resolve() == GRAMMAR:
        return registered
    spec = importlib.util.spec_from_file_location("geovista_citations", GRAMMAR)
    module = importlib.util.module_from_spec(spec)
    # registered before it is executed, as "dataclass" resolves the annotations
    # of a module compiled with "from __future__ import annotations" by looking
    # the module up by name
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def demo(tmp_path: Path, body: str, citations: ModuleType) -> tuple[Path, Any]:
    """Write a specification declaring the ``demo spec`` prefix, and read it."""
    path = tmp_path / "2026-01-01-demo-design.md"
    banner = f"- **Citation prefix:** `demo spec {SECTION}{ELLIPSIS}`\n\n"
    path.write_text(banner + body, encoding="utf-8")
    return path, citations.namespace([path])


def test_the_grammar_is_one_module_however_it_is_loaded(citations, monkeypatch):
    """The conventions test, this fixture and a build's import share one module.

    A second load by path would be a second copy, whose dataclasses never equal
    the first's, and a plain import would return whichever registered last.
    """
    path = Path(__file__).parents[1] / "test_spec_conventions.py"
    spec = importlib.util.spec_from_file_location("conventions_under_test", path)
    conventions = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = conventions
    spec.loader.exec_module(conventions)
    monkeypatch.syspath_prepend(str(GRAMMAR.parent))
    imported = importlib.import_module("geovista_citations")

    assert conventions.citations is citations
    assert imported is citations
    assert conventions.Citation("x", None, 0, 1) == citations.Citation("x", None, 0, 1)


def test_the_default_roots_are_this_repository(citations):
    """The module finds the repository from its own path, as a build needs it to."""
    assert citations.SPECS == citations.REPO / "docs" / "src" / "developer" / "specs"
    assert (citations.REPO / "pyproject.toml").is_file()


def test_fenced_blocks_are_skipped(citations):
    """A fence quoting a shorter fence stays open across the inner rail."""
    text = "a\n````markdown\n```\n(demo-spec-9)=\n```\n````\nb\n"

    assert [line for _, line in citations.read_lines(text)] == ["a", "b"]


def test_prose_inside_a_directive_fence_is_read(citations):
    """An admonition renders its body, so the body is prose and is read."""
    text = "a\n```{note}\nb\n```\nc\n"

    assert [line for _, line in citations.read_lines(text)] == ["a", "b", "c"]


def test_code_inside_a_directive_fence_stays_skipped(citations):
    """A code block nested in an admonition is still code."""
    text = "````{note}\nb\n```python\n(demo-spec-9)=\n```\nc\n````\nd\n"

    assert [line for _, line in citations.read_lines(text)] == ["b", "c", "d"]


def test_a_directive_whose_body_is_code_is_skipped(citations):
    """A code-block directive is a fence by another name."""
    text = "```{code-block} python\n(demo-spec-9)=\n```\nb\n"

    assert [line for _, line in citations.read_lines(text)] == ["b"]


def test_inline_code_opening_a_line_is_no_fence(citations):
    """A backtick fence's info string cannot hold a backtick."""
    text = "```x``` opens the line\nb\n"

    assert [line for _, line in citations.read_lines(text)] == [
        "```x``` opens the line",
        "b",
    ]


def test_inline_code_is_blanked_and_roles_are_collected(citations):
    """A role quoted inside a longer span is code, not a role."""
    line = (
        f"{{ref}}`{SECTION}1 <demo-spec-1>` and "
        f"`` {{ref}}`{SECTION}2 <demo-spec-1>` `` and ``demo spec 3``"
    )

    plain, roles = citations.prose(line)

    assert roles == [("ref", f"{SECTION}1 <demo-spec-1>")]
    assert plain.strip(" and") == ""
    assert len(plain) == len(line)


def test_a_prefix_carries_across_a_run_and_no_further(tmp_path, citations):
    """A comma or solidus joins a run; a full stop ends it."""
    _, names = demo(tmp_path, DEMO, citations)
    text = f"demo spec {SECTION}1, {SECTION}2. Then {SECTION}1."

    assert [c.slug for c in citations.scan(text, names.signed, None)] == [
        "demo-spec-1",
        "demo-spec-2",
        None,
    ]
    assert [c.slug for c in citations.scan(text, names.signed, "other-spec")][-1] == (
        "other-spec-1"
    )


def test_a_citation_knows_where_it_is_written(tmp_path, citations):
    """Each citation's place slices its text back out, which the transform splits on."""
    _, names = demo(tmp_path, DEMO, citations)
    text = f"See demo spec {SECTION}1, {SECTION}2 and {SECTION}1."

    found = list(citations.scan(text, names.signed, "other-spec"))

    assert [text[c.start : c.end] for c in found] == [c.text for c in found]
    assert [c.start for c in found] == sorted({c.start for c in found})
    assert len(found) == 3


def test_a_section_sign_without_a_number_is_no_citation(tmp_path, citations):
    """Legal style puts a space after the sign; a citation never does."""
    _, names = demo(tmp_path, DEMO, citations)
    text = f"{SECTION} 5, {SECTION}{ELLIPSIS} and demo spec {SECTION}x"

    assert list(citations.scan(text, names.signed, None)) == []


def test_only_markdown_fences_are_skipped(citations):
    """A reStructuredText code block is read, so a counterexample there is code."""
    text = ".. code-block:: text\n\n    demo spec 1\n"

    assert list(citations.source_lines(Path("page.rst"), text))[-1] == (
        3,
        "    demo spec 1",
    )


def test_corpus_reads_the_tree_it_is_given(tmp_path, citations):
    """The walk prunes tooling state and the named trees, and drops binaries."""
    for name in (".git", ".github", "docs/_build", "docs/src/developer/plans", "src"):
        (tmp_path / name).mkdir(parents=True)
        (tmp_path / name / "file.txt").write_text("text\n", encoding="utf-8")
    (tmp_path / "src" / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
    for name, marker in (("venv", "pyvenv.cfg"), ("htmlcov", "x"), ("nested", ".git")):
        (tmp_path / name).mkdir()
        (tmp_path / name / marker).write_text("home = /usr\n", encoding="utf-8")
        (tmp_path / name / "file.txt").write_text("text\n", encoding="utf-8")

    found = {
        path.relative_to(tmp_path).as_posix() for path in citations.corpus(tmp_path)
    }

    assert found == {".github/file.txt", "src/file.txt"}

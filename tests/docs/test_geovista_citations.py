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
    """A comma or solidus joins a run; a full stop ends it.

    Holds docs spec §2 decision 5.
    """
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


#: The states of ledger spec §3.2, §3.3, §3.4, built by name: see the module docstring.
HANDSHAKE = "\N{HANDSHAKE}"
CABINET = "\N{FILE CABINET}\N{VARIATION SELECTOR-16}"

#: A specification whose decisions are numbered, as ledger spec §3.1 asks.
DECIDED = (
    "(demo-spec-1)=\n## 1. Purpose\n\n(demo-spec-2)=\n## 2. Decisions\n\n"
    "1. **One.** First.\n2. **Two.** Second.\n3. **Three.** Third.\n\n"
    "(demo-spec-3)=\n## 3. Design\n"
)


def test_a_decision_citation_names_its_decision(tmp_path, citations):
    """The citation of ledger spec §2 decision 1 names the decision, not its section."""
    _, names = demo(tmp_path, DECIDED, citations)
    text = f"see demo spec {SECTION}2 decision 3."

    found = list(citations.scan(text, names.signed, None))

    assert [(c.text, c.slug) for c in found] == [
        (f"demo spec {SECTION}2 decision 3", "demo-spec-2-decision-3")
    ]


def test_a_bare_decision_citation_means_its_own_document(tmp_path, citations):
    """Within a specification, a bare decision is its own, as a bare section is."""
    _, names = demo(tmp_path, DECIDED, citations)

    found = list(citations.scan(f"{SECTION}2 decision 3", names.signed, "demo-spec"))

    assert [c.slug for c in found] == ["demo-spec-2-decision-3"]


def test_a_prefix_carries_to_a_decision_in_a_run(tmp_path, citations):
    """A comma carries the prefix to a decision as it does to a section."""
    _, names = demo(tmp_path, DECIDED, citations)
    text = f"demo spec {SECTION}3, {SECTION}2 decision 1"

    assert [c.slug for c in citations.scan(text, names.signed, None)] == [
        "demo-spec-3",
        "demo-spec-2-decision-1",
    ]


def test_decisions_plural_is_a_citation_of_the_section(tmp_path, citations):
    """A plural names no one decision, so it stays a citation of the section."""
    _, names = demo(tmp_path, DECIDED, citations)
    text = f"demo spec {SECTION}2 decisions 1 and 3"

    found = list(citations.scan(text, names.signed, None))

    assert [(c.text, c.slug) for c in found] == [
        (f"demo spec {SECTION}2", "demo-spec-2")
    ]


def test_decisions_reads_state_provenance_title_and_body(citations):
    """An entry is read state first, its title whole although it wraps."""
    text = (
        "(demo-spec-2)=\n## 2. Decisions\n\n"
        "1. **One.** First.\n"
        f"2. **{HANDSHAKE} Agreed** (2026-10-28, {{user}}`bjlittle`, {{pull}}`2771`) — "
        "**A missing height\n   is no height.** A masked height\n   is NaN.\n"
    )

    first, second = citations.decisions(text)

    assert (first.number, first.state, first.title, first.body) == (
        1,
        None,
        "One.",
        "First.",
    )
    assert second.number == 2
    assert second.line == 5
    assert second.state == citations.AGREED
    assert second.carried == "2026-10-28, {user}`bjlittle`, {pull}`2771`"
    assert second.title == "A missing height is no height."
    assert second.body == "A masked height is NaN."


def test_a_state_is_read_without_its_variation_selector(citations):
    """A state typed without U+FE0F is the same state, spelled as the spec spells it."""
    states = (citations.AGREED, citations.RETIRED)

    assert citations.state_of("\N{FILE CABINET} Retired (2026-10-30)", states) == (
        citations.RETIRED
    )
    assert citations.state_of(f"{CABINET} Retired", states) == citations.RETIRED
    assert citations.state_of("Open", states) is None


def test_decisions_ignores_bullets_and_other_sections(citations):
    """Only the numbered items of a second section titled Decisions are decisions."""
    bulleted = "(demo-spec-2)=\n## 2. Decisions\n\n- **One.** First.\n"
    elsewhere = "(demo-spec-3)=\n## 3. Decisions\n\n1. **One.** First.\n"

    assert citations.decisions(bulleted) == []
    assert citations.decisions(elsewhere) == []


def test_namespace_declares_an_anchor_per_decision(tmp_path, citations):
    """Each decision has an anchor, though no line of the source declares one."""
    _, names = demo(tmp_path, DECIDED, citations)

    assert {f"demo-spec-2-decision-{n}" for n in (1, 2, 3)} <= names.anchors
    assert "demo-spec-2-decision-4" not in names.anchors
    assert citations.decision_anchor("demo-spec", 2) == "demo-spec-2-decision-2"


def test_ledger_reads_the_verification_table(citations):
    """The ledger is the table headed Decision, Status and Evidence, and no other."""
    rows = (
        "| Decision | Status | Evidence |\n|---|---|---|\n"
        "| 1 | \N{HOURGLASS WITH FLOWING SAND} pending | |\n"
        "| 2 | \N{WHITE HEAVY CHECK MARK} verified (2026-10-30, {pull}`1`) | `x.py` |\n"
    )
    text = f"(demo-spec-10)=\n## 10. Verification\n\n{rows}"
    other = (
        "(demo-spec-10)=\n## 10. Verification\n\n"
        "| # | Scope | Status |\n|---|---|---|\n"
    )

    found = citations.ledger(text)

    assert [(row.decision, row.line) for row in found] == [(1, 6), (2, 7)]
    assert found[0].status == citations.PENDING
    assert found[1].evidence == "`x.py`"
    assert citations.ledger(other) is None


def test_a_row_naming_a_superscript_names_no_decision(citations):
    """Review Focus 5 of its plan: a cell no int() reads is reported, never a crash."""
    row = citations.LedgerRow("\N{SUPERSCRIPT TWO}", 1, "", "")

    assert row.decision is None


def test_cells_keep_an_escaped_pipe(citations):
    """A table cell may hold a pipe, escaped, and is not cut short at it (#2787)."""
    assert citations.cells("| 1 | a \\| b | c |") == ["1", "a \\| b", "c"]


def test_ledger_keeps_an_escaped_pipe_in_its_evidence(citations):
    """The Evidence cell is read whole, pipe and all (#2787)."""
    text = (
        "(demo-spec-10)=\n## 10. Verification\n\n"
        "| Decision | Status | Evidence |\n|---|---|---|\n"
        "| 1 | \N{HOURGLASS WITH FLOWING SAND} pending | a \\| b |\n"
    )

    assert citations.ledger(text)[0].evidence == "a \\| b"


def test_decisions_reads_a_title_with_emphasis_inside(citations):
    """A title holding an emphasised word is read whole, as the guard reads it."""
    text = "(demo-spec-2)=\n## 2. Decisions\n\n1. **A *very* big title.** Reasoning.\n"

    assert citations.decisions(text)[0].title == "A *very* big title."


@pytest.mark.parametrize(
    "row", ["| 1 | x | a \\||", "| 1 | x | a \\|"], ids=["closed", "unclosed"]
)
def test_cells_keep_an_escaped_pipe_ending_the_row(citations, row):
    """Only the outer pipes are separators, so a last cell's escaped pipe stays."""
    assert citations.cells(row) == ["1", "x", "a \\|"]


def test_cells_keep_an_empty_last_cell(citations):
    """An empty cell is a cell, and only the separators beyond it are dropped."""
    assert citations.cells("| 1 | |") == ["1", ""]


def test_summary_counts_each_state(citations):
    """The summary line under a Verification table is the grammar's, for every reader.

    The build writes it, and so does the verification report, which runs without
    Sphinx (ledger spec §3.8).
    """
    statuses = [
        citations.VERIFIED,
        citations.VERIFIED,
        citations.VERIFIED,
        citations.PENDING,
        citations.LEDGER_RETIRED,
        citations.SIGNED_OFF,
    ]

    assert citations.summary(statuses).endswith(": 4 of 5 decisions in force verified")
    assert citations.summary(statuses).startswith(f"{citations.VERIFIED.split()[0]} 3")

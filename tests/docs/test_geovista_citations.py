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

from datetime import date
import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence
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
        f"| {SECTION}2 decision 1 | \N{HOURGLASS WITH FLOWING SAND} pending | |\n"
        f"| {SECTION}2 decision 2 | \N{WHITE HEAVY CHECK MARK} verified "
        "(2026-10-30, {pull}`1`) | `x.py` |\n"
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
    row = citations.LedgerRow(f"{SECTION}2 decision \N{SUPERSCRIPT TWO}", 1, "", "")

    assert row.decision is None


@pytest.mark.parametrize(
    ("cell", "decision"),
    [
        (f"{SECTION}2 decision 3", 3),
        (f"{SECTION}2 decision 12", 12),
        ("3", None),
        ("decision 3", None),
        (f"{SECTION}3 decision 3", None),
        (f"{SECTION}2 decisions 3", None),
        (f"{SECTION}2 decision 3 and 4", None),
        (f"demo spec {SECTION}2 decision 3", None),
        (f"**{SECTION}2 decision 3**", None),
    ],
    ids=[
        "citation",
        "two-digits",
        "bare",
        "no-section",
        "other-section",
        "plural",
        "two",
        "prefixed",
        "bold",
    ],
)
def test_a_row_names_its_decision_by_its_citation(citations, cell, decision):
    """Ledger spec §2 decision 17: a row names its decision as its citation, alone."""
    assert citations.LedgerRow(cell, 1, "", "").decision == decision


def test_cells_keep_an_escaped_pipe(citations):
    """A table cell may hold a pipe, escaped, and is not cut short at it (#2787)."""
    assert citations.cells("| 1 | a \\| b | c |") == ["1", "a \\| b", "c"]


def test_ledger_keeps_an_escaped_pipe_in_its_evidence(citations):
    """The Evidence cell is read whole, pipe and all (#2787)."""
    text = (
        "(demo-spec-10)=\n## 10. Verification\n\n"
        "| Decision | Status | Evidence |\n|---|---|---|\n"
        f"| {SECTION}2 decision 1 | \N{HOURGLASS WITH FLOWING SAND} pending "
        "| a \\| b |\n"
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


#: A specification whose design section holds two numbered lists, and whose
#: roadmap numbers a row with a letter, as the typing spec's does.
LISTED = (
    "(demo-spec-1)=\n## 1. Purpose\n\n"
    "(demo-spec-2)=\n## 2. Decisions\n\n"
    "1. **One.** First.\n2. **Two.** Second.\n3. **Three.** Third.\n\n"
    "(demo-spec-3)=\n## 3. Design\n\n"
    "1. **A step.** Taken first.\n2. Then another,\n   wrapped.\n\n"
    "Between the lists.\n\n"
    "1. A second list.\n2. Its second item.\n3. Its third item.\n\n"
    "(demo-spec-4)=\n## 4. Roadmap\n\n"
    "| # | Scope | Status |\n|---|---|---|\n"
    "| 6a | The first half | not started |\n"
    "| 6b | The second half | not started |\n"
    "| 7 | The rest | candidate |\n"
)


def test_an_item_is_cited_either_way(tmp_path, citations):
    """Both orders name one anchor, within a specification and across them.

    Holds items spec §2 decision 10.
    """
    _, names = demo(tmp_path, LISTED, citations)
    text = f"demo spec {SECTION}3 item 2 and item 2 of demo spec {SECTION}3"
    bare = f"{SECTION}3 item 2 and item 2 of {SECTION}3"

    found = list(citations.scan(text, names.signed, None))
    own = list(citations.scan(bare, names.signed, "demo-spec"))

    assert [c.text for c in found] == [
        f"demo spec {SECTION}3 item 2",
        f"item 2 of demo spec {SECTION}3",
    ]
    assert {c.slug for c in [*found, *own]} == {"demo-spec-3-item-2"}
    assert [c.text for c in own] == [f"{SECTION}3 item 2", f"item 2 of {SECTION}3"]
    assert "demo-spec-3-item-2" in names.anchors
    assert citations.item_anchor("demo-spec", "3", 2) == "demo-spec-3-item-2"
    assert citations.item_anchor("scene-spec", "4.4", 2) == "scene-spec-4-4-item-2"


def test_a_row_range_names_both_ends(tmp_path, citations):
    """Review Focus 2: a range across a lettered row names, and declares, each end.

    Holds items spec §2 decision 10.
    """
    _, names = demo(tmp_path, LISTED, citations)
    text = f"rows 6a to 7 of demo spec {SECTION}4, Rows 6A and 6b of {SECTION}4"

    first, second = citations.scan(text, names.signed, None)

    assert first.text == f"rows 6a to 7 of demo spec {SECTION}4"
    assert (first.slug, first.ends) == ("demo-spec-4-row-6a", ("demo-spec-4-row-7",))
    assert (second.slug, second.ends) == ("demo-spec-4-row-6a", ("demo-spec-4-row-6b",))
    assert {"demo-spec-4-row-6a", "demo-spec-4-row-6b", "demo-spec-4-row-7"} <= (
        names.anchors
    )
    assert citations.row_anchor("typing-spec", "4", "6a") == "typing-spec-4-row-6a"


def test_a_single_citation_has_no_far_end(tmp_path, citations):
    """Only a range has a far end, so a section, an item and a row have none."""
    _, names = demo(tmp_path, LISTED, citations)
    text = f"demo spec {SECTION}3, {SECTION}3 item 1, row 7 of {SECTION}4"

    assert [c.ends for c in citations.scan(text, names.signed, None)] == [(), (), ()]


def test_a_decision_is_never_cited_as_an_item(tmp_path, citations):
    """Review Focus 3: an item of the Decisions is cited only as a decision."""
    _, names = demo(tmp_path, LISTED, citations)
    text = f"demo spec {SECTION}2 item 3 and item 3 of demo spec {SECTION}2"

    found = list(citations.scan(text, names.signed, None))

    assert [c.slug for c in found] == ["demo-spec-2-item-3", "demo-spec-2-item-3"]
    assert "demo-spec-2-item-3" not in names.anchors
    assert "demo-spec-2-decision-3" in names.anchors


def test_an_item_label_is_read_alike_in_either_order(tmp_path, citations):
    """Items spec §7 item 5: ``item 9a`` names one anchor, before or after.

    The trailing form read the number as digits alone, so it linked item 9 and
    left a stray letter, where the leading form read ``9a`` and named nothing.
    """
    _, names = demo(tmp_path, LISTED, citations)
    text = f"demo spec {SECTION}3 item 2a and item 2a of demo spec {SECTION}3"

    found = list(citations.scan(text, names.signed, None))

    assert [c.text for c in found] == [
        f"demo spec {SECTION}3 item 2a",
        f"item 2a of demo spec {SECTION}3",
    ]
    assert {c.slug for c in found} == {"demo-spec-3-item-2a"}


@pytest.mark.parametrize(
    "inner",
    [
        "[a link {} its text](https://example.com)",
        "[a [nested] link {} its text](https://github.com/bjlittle/geovista/pull/1)",
        "[a `]` {} b](https://github.com/bjlittle/geovista/pull/1)",
        "[a `[` {} b](https://github.com/bjlittle/geovista/pull/1)",
        "[a ``]`` {} b](https://github.com/bjlittle/geovista/pull/1)",
        "a code span, `a {} b`",
        "a code span of two, ``a {} b``",
        "a code span of four, ````a {} b````",
    ],
)
def test_a_middle_dot_inside_a_link_or_code_parts_nothing(citations, inner):
    """Items spec §7 item 9: only a middle dot in the open separates parts."""
    dot = citations.DOT.strip()
    carried = (
        f"{citations.FOUND} 2026-01-01, {inner.format(dot)}"
        f"{citations.DOT}{citations.TICKET} {{issue}}`5`"
    )

    parts = citations.provenance(carried)

    assert parts == [
        (citations.FOUND, f"2026-01-01, {inner.format(dot)}"),
        (citations.TICKET, "{issue}`5`"),
    ]


def test_a_list_after_an_unnumbered_subheading_is_not_anchored(tmp_path, citations):
    """Items spec §7 item 10: the grammar anchors what the build anchors.

    The build names only a numbered section's direct children, and a heading
    with no number opens a subsection of its own, so a list after one is no
    list of the numbered section, whether or not a list came before it.
    """
    after = "(demo-spec-3)=\n## 3. Design\n\n### Notes\n\n1. A step.\n2. Another.\n"
    before = (
        "(demo-spec-3)=\n## 3. Design\n\n1. The first.\n\n"
        "### Notes\n\n1. A later step.\n"
    )

    assert citations.listed(after) == []
    assert [(i.section, i.number) for i in citations.listed(before)] == [("3", 1)]
    _, names = demo(tmp_path, after, citations)
    assert "demo-spec-3-item-1" not in names.anchors


def test_only_the_first_list_of_a_section_is_anchored(tmp_path, citations):
    """Review Focus 1: an item past the first list's end names nothing."""
    _, names = demo(tmp_path, LISTED, citations)

    (cited,) = citations.scan(f"{SECTION}3 item 3", names.signed, "demo-spec")

    assert {"demo-spec-3-item-1", "demo-spec-3-item-2"} <= names.anchors
    assert cited.slug == "demo-spec-3-item-3"
    assert cited.slug not in names.anchors
    assert [(i.section, i.number) for i in citations.listed(LISTED)] == [
        ("3", 1),
        ("3", 2),
    ]


def test_listed_reads_titled_and_untitled_items(citations):
    """A title is the bold run after any state, and an item without one has none."""
    question = "\N{BLACK QUESTION MARK ORNAMENT}"
    text = (
        "(demo-spec-4)=\n## 4. Design\n\n"
        "(demo-spec-4-1)=\n### 4.1 Steps\n\n"
        "1. **A titled\n   step.** Its body.\n"
        "2. An untitled step, with **bold** inside.\n\n"
        "(demo-spec-7)=\n## 7. Open Items\n\n"
        "1. **Open** ({issue}`1`) — **An old-grammar item.** Its reasoning.\n"
        f"2. **{question} Open** (\N{RIGHT-POINTING MAGNIFYING GLASS} 2026-11-02) — "
        "**A new-grammar item.** Its reasoning.\n"
        "3. **Resolved** (2026-11-02, {pull}`2`) — settled, untitled.\n"
        "```text\n4. **Quoted.** In a fence.\n```\n"
    )

    found = citations.listed(text)

    assert [(i.section, i.number, i.line, i.title) for i in found] == [
        ("4.1", 1, 7, "A titled step."),
        ("4.1", 2, 9, None),
        ("7", 1, 14, "An old-grammar item."),
        ("7", 2, 15, "A new-grammar item."),
        ("7", 3, 16, None),
    ]
    assert found[0].body == "Its body."
    assert found[1].body == "An untitled step, with **bold** inside."
    assert found[2].body == "Its reasoning."


def test_rows_reads_every_roadmap_and_no_other_table(citations):
    """A roadmap is read by its header, wherever it sits; a ledger is no roadmap."""
    text = LISTED + (
        "\n(demo-spec-5)=\n## 5. Verification\n\n"
        "| Decision | Status | Evidence |\n|---|---|---|\n| 1 | pending | |\n"
    )

    found = citations.rows(text)

    assert [(r.section, r.row, r.scope, r.status) for r in found] == [
        ("4", "6a", "The first half", "not started"),
        ("4", "6b", "The second half", "not started"),
        ("4", "7", "The rest", "candidate"),
    ]
    assert [r.line for r in found] == [29, 30, 31]


@pytest.mark.parametrize("cell", ["**1**", "~~3~~", "7.", "one"])
def test_rows_passes_over_a_row_not_numbered_as_one(tmp_path, citations, cell):
    """A first cell that is no row number names no row, and crashes nothing.

    The conventions test reports such a cell where it is written, so passing over
    it here keeps the build, the suites and the checks running until it is fixed.
    """
    body = LISTED.replace("| 7 | The rest |", f"| {cell} | The rest |")

    _, names = demo(tmp_path, body, citations)

    assert [r.row for r in citations.rows(body)] == ["6a", "6b"]
    assert "demo-spec-4-row-6b" in names.anchors


def test_a_label_reads_an_item_and_a_row_anchor(tmp_path, citations):
    """Every anchor carries a prefix a reader can find, items and rows included."""
    _, names = demo(tmp_path, LISTED, citations)

    assert names.prefixes == {"demo-spec"}
    assert citations.LABEL.match("typing-spec-4-row-6a")["row"] == "6a"
    assert citations.LABEL.match("scene-spec-4-4-item-2")["num"] == "4-4"


def test_a_wrapped_number_continuing_a_paragraph_is_no_item(tmp_path, citations):
    """A list interrupts a paragraph only if it opens at 1, as in CommonMark."""
    body = (
        "(demo-spec-1)=\n## 1. Purpose\n\n"
        "(demo-spec-9)=\n## 9. Roadmap\n\n"
        "Prose that tracks rows 1 to\n4. Rows 2 to 4 each build on row 1.\n\n"
        "(demo-spec-10)=\n## 10. Steps\n\n"
        "Prose before a list.\n1. A step.\n2. Another.\n"
    )
    _, names = demo(tmp_path, body, citations)

    assert [(i.section, i.number) for i in citations.listed(body)] == [
        ("10", 1),
        ("10", 2),
    ]
    assert "demo-spec-9-item-4" not in names.anchors


def test_a_restarted_list_is_numbered_by_position(tmp_path, citations):
    """A "1." restarting a list after a blank line is still that list to MyST.

    MyST merges it exactly as CommonMark does, and the build names every item by
    its position, ``start`` plus its offset in the merged list
    (``DecisionTargets``/``ItemTargets``), never by the digit restarting it.
    Review round 1 found ``listed()`` disagreeing, reading the digit instead and
    silently giving the third item the first item's anchor.
    """
    body = (
        "(demo-spec-1)=\n## 1. Purpose\n\n"
        "(demo-spec-6)=\n## 6. Items\n\n"
        "1. **One.** First.\n2. **Two.** Second.\n\n"
        "1. **Three.** Restarted, but the same list.\n"
    )
    _, names = demo(tmp_path, body, citations)

    found = citations.listed(body)

    assert [(i.section, i.number) for i in found] == [("6", 1), ("6", 2), ("6", 3)]
    assert found[2].title == "Three."
    assert {"demo-spec-6-item-1", "demo-spec-6-item-2", "demo-spec-6-item-3"} <= (
        names.anchors
    )


#: A list whose first item runs on to a line written flush beneath it, with no
#: blank line between: a lazy continuation of the item's paragraph, in CommonMark.
LAZY = (
    "(demo-spec-1)=\n## 1. Purpose\n\n"
    "(demo-spec-6)=\n## 6. Items\n\n"
    "1. **Alpha.** First item.\nMore of the first item.\n2. **Beta.** Second item.\n"
)


def test_a_lazy_line_continues_its_item(tmp_path, citations):
    """A flush line straight after an item's text is more of it, as MyST reads it.

    So the item after it is still the list's, and has its anchor.
    """
    _, names = demo(tmp_path, LAZY, citations)

    found = citations.listed(LAZY)

    assert [(i.section, i.number, i.title) for i in found] == [
        ("6", 1, "Alpha."),
        ("6", 2, "Beta."),
    ]
    assert found[0].body == "First item. More of the first item."
    assert "demo-spec-6-item-2" in names.anchors


def test_a_lazy_line_continues_a_decision_and_an_open_item(citations):
    """The Decisions and the Open Items are read as the build reads any list."""
    decided = LAZY.replace("## 6. Items", "## 2. Decisions").replace("-6)", "-2)")
    itemed = LAZY.replace("## 6. Items", "## 6. Open Items")

    one, two = citations.decisions(decided)
    first, second = citations.items(itemed)
    whole = "First item. More of the first item."

    assert (one.title, one.body, two.number, two.title) == ("Alpha.", whole, 2, "Beta.")
    assert (first.title, first.body, second.number, second.title) == (
        "Alpha.",
        whole,
        2,
        "Beta.",
    )


@pytest.mark.parametrize(
    "line",
    [
        "# A heading",
        "- A bullet.",
        "* A bullet.",
        "> A quote.",
        "---",
        "* * *",
        "1) Another list.",
        "<div>",
        "<!-- A comment. -->",
        "(demo-target)=",
        "% A comment.",
        "+++",
        "[^1]: A footnote.",
    ],
)
def test_a_block_written_flush_after_an_item_ends_its_list(citations, line):
    """A block that interrupts a paragraph ends the list instead, as MyST reads it."""
    text = LAZY.replace("More of the first item.", line)

    assert [i.title for i in citations.listed(text)] == ["Alpha."]
    assert len(citations.decisions(text.replace("## 6. Items", "## 2. Decisions"))) == 1
    assert len(citations.items(text.replace("## 6. Items", "## 6. Open Items"))) == 1


@pytest.mark.parametrize(
    "line", ["#hashtag", "<span>Inline.</span>", ":::", "$$", "===", "| a | b |"]
)
def test_a_line_that_opens_no_block_continues_its_item(citations, line):
    """Only a block able to interrupt a paragraph ends one, as MyST reads it."""
    text = LAZY.replace("More of the first item.", line)

    assert [i.title for i in citations.listed(text)] == ["Alpha.", "Beta."]


#: A list whose first item ends in an indented code block, then a line written
#: flush beneath the code, which no open paragraph takes in, so the list ends there.
CODED = (
    "(demo-spec-1)=\n## 1. Purpose\n\n"
    "(demo-spec-3)=\n## 3. Items\n\n"
    "1. **Alpha.** First.\n\n       print(123)\nOutside the list.\n\n"
    "2. **Beta.** Second.\n"
)


def test_a_flush_line_after_an_items_code_ends_its_list(tmp_path, citations):
    """Only a paragraph takes a lazy line in, so Beta opens a second list.

    The build names only the first list's items, so the grammar must declare no
    anchor for Beta, and a citation of item 2 fails as the build's does.
    """
    _, names = demo(tmp_path, CODED, citations)
    decided = CODED.replace("## 3. Items", "## 2. Decisions").replace("-3)", "-2)")
    itemed = CODED.replace("## 3. Items", "## 3. Open Items")

    assert [(i.number, i.title) for i in citations.listed(CODED)] == [(1, "Alpha.")]
    assert "demo-spec-3-item-2" not in names.anchors
    assert [d.title for d in citations.decisions(decided)] == ["Alpha."]
    assert [i.title for i in citations.items(itemed)] == ["Alpha."]


#: The cells a specification's status reads, spelled by name (docs spec §3.8).
NOT_STARTED_CELL = "\N{CLIPBOARD} not started"
COMPLETE_CELL = "\N{WHITE HEAVY CHECK MARK} complete"
PROGRESS = "\N{CONSTRUCTION SIGN}"
CANDIDATES = " \N{MIDDLE DOT} \N{ELECTRIC LIGHT BULB}"


def landed(citations: ModuleType) -> str:
    """Return a landed row's Status cell, as a roadmap writes one."""
    return f"{citations.LANDED} (2026-11-09, {{pull}}`2917`)"


@pytest.mark.parametrize(
    ("counts", "expected"),
    [
        ({"not_started": 2}, NOT_STARTED_CELL),
        ({"landed": 1, "not_started": 1}, f"{PROGRESS} 1 of 2 rows"),
        ({"landed": 2}, COMPLETE_CELL),
        ({"landed": 1, "candidate": 1}, f"{COMPLETE_CELL}{CANDIDATES} 1"),
        (
            {"landed": 2, "not_started": 4, "candidate": 4},
            f"{PROGRESS} 2 of 6 rows{CANDIDATES} 4",
        ),
        ({"candidate": 2}, "\N{ELECTRIC LIGHT BULB} 2"),
        ({}, "\N{EM DASH}"),
    ],
    ids=[
        "not-started",
        "in-progress",
        "complete",
        "complete-with-candidates",
        "in-progress-with-candidates",
        "only-candidates",
        "no-roadmap",
    ],
)
def test_roadmap_status_sums_each_state(citations, counts, expected):
    """A specification's status sums its roadmap into one cell.

    Holds docs spec §2 decision 8.
    """
    cells = {
        "landed": landed(citations),
        "not_started": citations.NOT_STARTED,
        "candidate": citations.CANDIDATE,
    }
    statuses = [cells[state] for state, count in counts.items() for _ in range(count)]

    assert citations.roadmap_status(statuses) == expected


def test_roadmap_status_counts_a_row_in_progress_as_not_landed(citations):
    """A row in progress has begun, but has not landed yet, and one row is a row."""
    statuses = [f"{citations.IN_PROGRESS} ({{pull}}`2917`)"]

    assert citations.roadmap_status(statuses) == f"{PROGRESS} 0 of 1 row"


def test_roadmap_status_reads_a_variation_selector(citations):
    """A state is read with or without its variation selector."""
    statuses = ["\N{WHITE HEAVY CHECK MARK}\N{VARIATION SELECTOR-16} landed"]

    assert citations.roadmap_status(statuses) == COMPLETE_CELL


def test_roadmap_status_counts_an_unknown_state_as_not_landed(citations):
    """A cell opening with no state has not landed, which the conventions refuse."""
    statuses = [landed(citations), "landed"]

    assert citations.roadmap_status(statuses) == f"{PROGRESS} 1 of 2 rows"


#: An ordering's opener in a Scope cell (order spec §4.1), built by name.
LINKED = " \N{MIDDLE DOT} \N{LINK SYMBOL}"


def test_split_scope_returns_the_scope_alone_without_orderings(citations):
    """A scope with no ordering is its own text, and has no clause."""
    assert citations.split_scope("The lift") == ("The lift", [])


def test_split_scope_splits_each_ordering(citations):
    """The first opener ends the scope, and each opens one ordering."""
    scope = f"The lift{LINKED} after row 2{LINKED} with row 2 of layers spec {SECTION}9"

    assert citations.split_scope(scope) == (
        "The lift",
        ["after row 2", f"with row 2 of layers spec {SECTION}9"],
    )


def test_split_scope_skips_code(citations):
    """An opener quoted in code is the scope's text."""
    scope = f"Show `{LINKED.strip()} after row 1` in a cell"

    assert citations.split_scope(scope) == (scope, [])


def test_split_scope_reads_a_variation_selector(citations):
    """The emoji reads with its variation selector as without."""
    scope = f"The lift{LINKED}\N{VARIATION SELECTOR-16} after row 1"

    assert citations.split_scope(scope) == ("The lift", ["after row 1"])


@pytest.mark.parametrize(
    ("clause", "relation", "target"),
    [
        ("after row 1", "after", "row 1"),
        (
            f"before row 5 of globe spec {SECTION}9",
            "before",
            f"row 5 of globe spec {SECTION}9",
        ),
        ("with row 2", "with", "row 2"),
        (
            f"with or after row 3 of globe spec {SECTION}9",
            "with or after",
            f"row 3 of globe spec {SECTION}9",
        ),
        ("before 0.6", "before", "0.6"),
    ],
    ids=["after", "before", "with", "with-or-after", "release"],
)
def test_ordering_reads_each_relation(citations, clause, relation, target):
    """Each of the four relations is read with its target."""
    assert citations.ordering(clause) == citations.Ordering(relation, target)


@pytest.mark.parametrize("clause", ["needs row 1", "after", "afterwards row 1", ""])
def test_ordering_refuses_another_word(citations, clause):
    """A clause opening with no relation, or naming no target, is no ordering."""
    assert citations.ordering(clause) is None


@pytest.mark.parametrize(
    ("version", "matched"),
    [("0.6", True), ("0.6.1", True), ("0", False), ("v0.6", False), ("0.6.1.2", False)],
)
def test_release_reads_two_or_three_numbers(citations, version, matched):
    """A release is a version of two or three numbers (order spec §4.4)."""
    assert (citations.RELEASE.fullmatch(version) is not None) is matched


#: The states of a roadmap row and an ordering's opener, built rather than written.
LANDED = "\N{WHITE HEAVY CHECK MARK} landed"
IN_PROGRESS = "\N{CONSTRUCTION SIGN} in progress"
NOT_STARTED = "\N{CLIPBOARD} not started"
CANDIDATE = "\N{ELECTRIC LIGHT BULB} candidate"
LINKED = " \N{MIDDLE DOT} \N{LINK SYMBOL}"


def roadmaps(
    tmp_path: Path,
    citations: ModuleType,
    mine: Sequence[tuple[str, str]],
    theirs: Sequence[tuple[str, str]] = (("Theirs", NOT_STARTED),),
) -> tuple[dict[Path, str], Any]:
    """Write a demo and an other specification, each a roadmap in its second section.

    Each row is its scope and its status, numbered from 1 in the order given.
    """

    def roadmap(slug: str, rows: Sequence[tuple[str, str]]) -> str:
        table = "".join(
            f"| {n} | {scope} | {status} |\n"
            for n, (scope, status) in enumerate(rows, start=1)
        )
        return (
            f"({slug}-1)=\n## 1. Purpose\n\n({slug}-2)=\n## 2. Roadmap\n\n"
            f"| # | Scope | Status |\n|---|---|---|\n{table}"
        )

    tmp_path.mkdir(parents=True, exist_ok=True)
    other = tmp_path / "2026-01-02-other-design.md"
    other.write_text(
        f"- **Citation prefix:** `other spec {SECTION}{ELLIPSIS}`\n\n"
        + roadmap("other-spec", theirs),
        encoding="utf-8",
    )
    path, _ = demo(tmp_path, roadmap("demo-spec", mine), citations)
    texts = {p: p.read_text(encoding="utf-8") for p in (path, other)}
    return texts, citations.namespace([path, other])


def demo_row(row: int | str) -> str:
    """Spell the anchor of a row of the demo specification's roadmap."""
    return f"demo-spec-2-row-{row}"


def other_row(row: int | str) -> str:
    """Spell the anchor of a row of the other specification's roadmap."""
    return f"other-spec-2-row-{row}"


def test_ordering_edges_reads_each_relation_as_an_edge(tmp_path, citations):
    """Each relation is one edge, its first row landing first, and a release none.

    ``after`` and ``before`` are the same edge read from either row, ``with`` is
    its pair in order of anchor, and ``with or after`` keeps its direction.
    """
    texts, names = roadmaps(
        tmp_path,
        citations,
        [
            ("One", NOT_STARTED),
            (f"Two{LINKED} after row 1{LINKED} before 0.6", NOT_STARTED),
            (f"Three{LINKED} before row 1 of other spec {SECTION}2", NOT_STARTED),
            (f"Four{LINKED} with row 1 of other spec {SECTION}2", NOT_STARTED),
            (f"Five{LINKED} with or after row 1 of other spec {SECTION}2", NOT_STARTED),
        ],
    )

    edges = [
        (edge.kind, edge.first, edge.second)
        for edge in citations.ordering_edges(texts, names)
    ]

    assert edges == [
        ("after", demo_row(1), demo_row(2)),
        ("after", demo_row(3), other_row(1)),
        ("with", *sorted((demo_row(4), other_row(1)))),
        ("with or after", other_row(1), demo_row(5)),
    ]


def test_ordering_edges_records_where_each_is_written(tmp_path, citations):
    """An edge carries the row and clause that write it, for its faults to name."""
    texts, names = roadmaps(
        tmp_path,
        citations,
        [("One", NOT_STARTED), (f"Two{LINKED} after row 1", NOT_STARTED)],
    )

    (edge,) = citations.ordering_edges(texts, names)

    assert edge.path.name.startswith("2026-01-01")
    assert edge.row.row == "2"
    assert edge.clause == "after row 1"


def test_landed_on_reads_a_date_and_its_pull_requests(citations):
    """A landed row's date and pull requests; any other state has not landed."""
    assert citations.landed_on(f"{LANDED} (2026-11-03, {{pull}}`7`)") == (
        date(2026, 11, 3),
        {("bjlittle/geovista", 7)},
    )
    assert citations.landed_on(NOT_STARTED) is None
    assert citations.landed_on(f"{IN_PROGRESS} ({{pull}}`7`)") is None


def test_row_statuses_reads_every_roadmap_by_anchor(tmp_path, citations):
    """Each row's status, keyed by its anchor, in every specification."""
    texts, names = roadmaps(
        tmp_path,
        citations,
        [("One", NOT_STARTED), ("Two", CANDIDATE)],
        [("Theirs", LANDED)],
    )

    assert citations.row_statuses(texts, names) == {
        demo_row(1): NOT_STARTED,
        demo_row(2): CANDIDATE,
        other_row(1): LANDED,
    }


def test_landing_together_groups_the_rows_a_loop_forces_into_one_pr(
    tmp_path, citations
):
    """A chain of with and a loop of with or after are each one group; after is not."""
    texts, names = roadmaps(
        tmp_path,
        citations,
        [
            ("One", NOT_STARTED),
            (f"Two{LINKED} with row 1", NOT_STARTED),
            (f"Three{LINKED} with row 2", NOT_STARTED),
            (f"Four{LINKED} with or after row 5", NOT_STARTED),
            (f"Five{LINKED} with or after row 4{LINKED} after row 3", NOT_STARTED),
        ],
    )

    groups = citations.landing_together(citations.ordering_edges(texts, names))

    assert groups[demo_row(1)] == [demo_row(2), demo_row(3)]
    assert groups[demo_row(3)] == [demo_row(1), demo_row(2)]
    assert groups[demo_row(4)] == [demo_row(5)]
    assert demo_row(6) not in groups


def test_row_citation_names_a_row_by_its_anchor(citations):
    """A row's anchor reads back as the citation that names it."""
    assert citations.row_citation("crs-spec-10-row-6a") == (
        f"row 6a of crs spec {SECTION}10"
    )
    assert citations.row_citation("ledger-spec-3-8-row-2") == (
        f"row 2 of ledger spec {SECTION}3.8"
    )


def ready(tmp_path, citations, mine, theirs=(("Theirs", LANDED),)) -> set[str]:
    """Read which rows of two roadmaps are ready to start."""
    texts, names = roadmaps(tmp_path, citations, mine, theirs)
    return citations.ready_rows(
        citations.ordering_edges(texts, names), citations.row_statuses(texts, names)
    )


def test_ready_rows_finds_a_row_whose_rows_before_it_have_landed(tmp_path, citations):
    """A row not started, after rows that have all landed, can start.

    Holds diagram spec §2 decision 5.
    """
    found = ready(
        tmp_path,
        citations,
        [
            ("One", LANDED),
            (f"Two{LINKED} after row 1", NOT_STARTED),
            (f"Three{LINKED} after row 2", NOT_STARTED),
        ],
    )

    assert found == {demo_row(2)}


def test_ready_rows_reads_with_or_after_and_before(tmp_path, citations):
    """A with or after, or a before written on the row landing first, waits too."""
    mine = [
        ("One", LANDED),
        (f"Two{LINKED} with or after row 1", NOT_STARTED),
        (f"Three{LINKED} before row 1 of other spec {SECTION}2", LANDED),
    ]
    theirs = [("Theirs", NOT_STARTED)]

    assert ready(tmp_path, citations, mine, theirs) == {demo_row(2), other_row(1)}

    mine = [(scope, NOT_STARTED) for scope, _ in mine]
    found = ready(tmp_path / "waiting", citations, mine, theirs)
    assert demo_row(2) not in found
    assert other_row(1) not in found


def test_ready_rows_reads_the_rows_landing_together(tmp_path, citations):
    """A row with another that still waits is not ready (diagram spec §3.4).

    Holds diagram spec §2 decision 5.
    """
    found = ready(
        tmp_path,
        citations,
        [(f"Mine{LINKED} with row 1 of other spec {SECTION}2", NOT_STARTED)],
        [(f"Theirs{LINKED} after row 2", NOT_STARTED), ("Before", NOT_STARTED)],
    )

    assert found == {other_row(2)}


@pytest.mark.parametrize("state", [IN_PROGRESS, f"{CANDIDATE}: a trigger"])
def test_ready_rows_holds_back_a_row_landing_with_one_begun_or_waiting(
    tmp_path, citations, state
):
    """A row landing with one in progress, or with a candidate, is not ready.

    It can land only in that row's pull request (diagram spec §4.3).
    """
    found = ready(
        tmp_path,
        citations,
        [(f"Mine{LINKED} with row 1 of other spec {SECTION}2", NOT_STARTED)],
        [("Theirs", state)],
    )

    assert found == set()


def test_ready_rows_needs_a_row_not_started(tmp_path, citations):
    """Only a row not started is ready, and one with no ordering waits on nothing."""
    found = ready(
        tmp_path,
        citations,
        [
            ("One", IN_PROGRESS),
            ("Two", LANDED),
            ("Three", f"{CANDIDATE}: a trigger"),
            ("Four", NOT_STARTED),
        ],
    )

    assert found == {demo_row(4)}


def labels(tmp_path, citations, *scopes: str, width: int = 40) -> list[str]:
    """Read the label of each row of the demo roadmap, in order."""
    texts, names = roadmaps(
        tmp_path, citations, [(scope, NOT_STARTED) for scope in scopes]
    )
    found = citations.row_labels(texts, names, width=width)
    return [found[demo_row(n)] for n in range(1, len(scopes) + 1)]


def test_row_labels_opens_with_the_row_and_its_scope(tmp_path, citations):
    """A label is the row's number and its scope, its orderings left to the arrows."""
    found = labels(
        tmp_path, citations, "One", f"Tiers on the globe{LINKED} after row 1"
    )

    assert found == ["1: One", "2: Tiers on the globe"]


def test_row_labels_cuts_a_long_scope(tmp_path, citations):
    """A scope longer than the width is cut, and says so."""
    (found,) = labels(tmp_path, citations, "a" * 60)

    assert found == "1: " + "a" * 40 + "\N{HORIZONTAL ELLIPSIS}"


def test_row_labels_escapes_what_mermaid_reads(tmp_path, citations):
    """Review Focus 1 of its plan: a quote, a hash or a role cannot break a diagram.

    A role reads as its target, an issue or pull request as ``#N``, and code and
    emphasis read as their text.
    """
    found = labels(
        tmp_path,
        citations,
        'The work of {issue}`7`, with "quotes"',
        "**Bold**, `snake_case` and _em_",
    )

    assert found == [
        "1: The work of #35;7, with #quot;quotes#quot;",
        "2: Bold, snake_case and em",
    ]

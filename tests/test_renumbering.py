# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for ``.github/scripts/check_renumbering.py``.

The script compares each specification a pull request changes with the one on
its base branch, and fails on an untouched citation of a section that moved or
went. Its core reads text, so most of these tests write two small specifications
and compare them. This module sits inside the corpus the citation grammar
governs, so it builds the section sign rather than write it, and cites a ``demo
spec`` that no document declares.

"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

#: The script under test, which is no importable module.
SCRIPT = Path(__file__).parents[1] / ".github" / "scripts" / "check_renumbering.py"

#: The section sign, built rather than written: see the module docstring.
SECTION = "\N{SECTION SIGN}"


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    """Load the script, registered first, as its dataclasses resolve through it."""
    spec = importlib.util.spec_from_file_location("check_renumbering", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def spec(*parts: tuple[str, str, str]) -> str:
    """Write a ``demo spec`` of the given sections, each a number, title and body."""
    lines = [f"- **Citation prefix:** `demo spec {SECTION}\N{HORIZONTAL ELLIPSIS}`", ""]
    for number, title, body in parts:
        depth = "#" * (2 + number.count("."))
        heading = f"{number}." if "." not in number else number
        lines += [
            f"(demo-spec-{number.replace('.', '-')})=",
            f"{depth} {heading} {title}",
        ]
        lines += ["", body, ""]
    return "\n".join(lines)


#: The text of three sections, distinct enough that none resembles another.
PURPOSE = "Why the design exists, and for whom, and what it replaces in the tree."
DESIGN = "The pairing of sections by title and then by the likeness of their text."
TESTING = "Small specifications are written and compared, one change at a time."


def fates(guard, base: str, head: str) -> dict[str, tuple[str, str | None]]:
    """Pair two specifications, as each base anchor's kind and new anchor."""
    paired = guard.pair(guard.sections(base), guard.sections(head))
    return {anchor: (fate.kind, fate.anchor) for anchor, fate in paired.items()}


BASE = spec(
    ("1", "Purpose", PURPOSE), ("2", "Design", DESIGN), ("3", "Testing", TESTING)
)


def test_sections_are_read_by_anchor_with_their_title_and_text(guard):
    """Each anchor keys its heading's title and the text beneath it."""
    found = guard.sections(BASE)

    assert list(found) == ["demo-spec-1", "demo-spec-2", "demo-spec-3"]
    assert found["demo-spec-2"].title == "Design"
    assert DESIGN in found["demo-spec-2"].body
    assert TESTING not in found["demo-spec-2"].body


def test_a_specification_that_is_unchanged_keeps_every_section(guard):
    """The ordinary edit: nothing moves."""
    assert fates(guard, BASE, BASE) == {
        "demo-spec-1": ("kept", "demo-spec-1"),
        "demo-spec-2": ("kept", "demo-spec-2"),
        "demo-spec-3": ("kept", "demo-spec-3"),
    }


def test_a_renamed_section_is_kept(guard):
    """Its number is unchanged, so every citation still names it."""
    head = spec(
        ("1", "Purpose", PURPOSE), ("2", "Pairing", DESIGN), ("3", "Testing", TESTING)
    )

    assert fates(guard, BASE, head)["demo-spec-2"] == ("kept", "demo-spec-2")


def test_titles_differing_in_case_and_punctuation_pair(guard):
    """A title style sweep renames nothing a citation depends on."""
    head = spec(
        ("1", "purpose!", PURPOSE), ("2", "DESIGN", DESIGN), ("3", "Testing.", TESTING)
    )

    assert {kind for kind, _ in fates(guard, BASE, head).values()} == {"kept"}


def test_a_section_inserted_before_two_moves_both(guard):
    """Inserting a section renumbers every one after it."""
    new = (
        "2",
        "Scope",
        "What the design covers, and what it leaves to others to settle.",
    )
    head = spec(
        ("1", "Purpose", PURPOSE),
        new,
        ("3", "Design", DESIGN),
        ("4", "Testing", TESTING),
    )

    assert fates(guard, BASE, head) == {
        "demo-spec-1": ("kept", "demo-spec-1"),
        "demo-spec-2": ("moved", "demo-spec-3"),
        "demo-spec-3": ("moved", "demo-spec-4"),
    }


def test_a_section_deleted_from_the_middle_is_removed_and_its_successor_moves(guard):
    """The deleted section's number now names the one after it."""
    head = spec(("1", "Purpose", PURPOSE), ("2", "Testing", TESTING))

    assert fates(guard, BASE, head) == {
        "demo-spec-1": ("kept", "demo-spec-1"),
        "demo-spec-2": ("removed", None),
        "demo-spec-3": ("moved", "demo-spec-2"),
    }


def test_a_section_inserted_while_another_is_renamed_pairs_each(guard):
    """A section moved and renamed at once is paired by its text."""
    new = (
        "2",
        "Scope",
        "What the design covers, and what it leaves to others to settle.",
    )
    head = spec(
        ("1", "Purpose", PURPOSE),
        new,
        ("3", "Pairing", DESIGN),
        ("4", "Testing", TESTING),
    )

    assert fates(guard, BASE, head) == {
        "demo-spec-1": ("kept", "demo-spec-1"),
        "demo-spec-2": ("moved", "demo-spec-3"),
        "demo-spec-3": ("moved", "demo-spec-4"),
    }


def test_a_section_rewritten_past_recognition_and_renamed_is_removed(guard):
    """With neither title nor text to go by, its citations are the author's to check."""
    head = spec(
        ("1", "Purpose", PURPOSE),
        (
            "2",
            "Mechanism",
            "Nothing of the earlier wording survives this complete rewrite.",
        ),
        ("3", "Testing", TESTING),
    )

    assert fates(guard, BASE, head)["demo-spec-2"] == ("removed", None)


def test_a_subsection_is_a_section_of_its_own(guard):
    """Subsections carry anchors, so they move and pair like any other section."""
    base = spec(("1", "Purpose", PURPOSE), ("1.1", "Design", DESIGN))
    head = spec(
        ("1", "Purpose", PURPOSE),
        ("1.1", "Scope", "Covered."),
        ("1.2", "Design", DESIGN),
    )

    assert fates(guard, base, head)["demo-spec-1-1"] == ("moved", "demo-spec-1-2")


def items(*entries: str) -> str:
    """Write a numbered list of open items, one line or two apiece."""
    return "\n".join(f"{number}. {entry}" for number, entry in enumerate(entries, 1))


def roadmap(*rows: tuple[str, str]) -> str:
    """Write a roadmap table of the given rows, each a number and a scope."""
    lines = ["| # | Scope | Status |", "|---|---|---|"]
    return "\n".join(lines + [f"| {n} | {scope} | not started |" for n, scope in rows])


ONE = "**Open** — **The first question.**\n   It needs an answer."
TWO = (
    "**Resolved** (2026-10-01, {pull}`1`) — **The second\n"
    "   question, wrapped.** Answered."
)
THREE = "**Open** — **The third question.** Still open."


def frozen(guard, base_items: str, head_items: str) -> list[str]:
    """Compare two specifications whose eighth section holds the given text."""
    base = spec(("1", "Purpose", PURPOSE), ("8", "Open Items", base_items))
    head = spec(("1", "Purpose", PURPOSE), ("8", "Open Items", head_items))
    return guard.frozen(base, head)


def test_an_item_appended_passes(guard):
    """Appending gives no item a new number."""
    assert frozen(guard, items(ONE, TWO), items(ONE, TWO, THREE)) == []


def test_an_item_inserted_mid_list_fails_naming_the_items_it_moved(guard):
    """Every item after it takes a new number, and a citation of one goes stale."""
    problems = frozen(guard, items(ONE, TWO), items(ONE, THREE, TWO))

    assert len(problems) == 1
    assert "item 2" in problems[0]
    assert "item 3" in problems[0]
    assert "The second question, wrapped." in problems[0]


def test_an_item_whose_title_is_edited_passes(guard):
    """It pairs with itself by its text, under the same number."""
    edited = "**Open** — **The first question, put better.**\n   It needs an answer."

    assert frozen(guard, items(ONE, TWO), items(edited, TWO)) == []


def test_an_item_whose_status_changes_passes(guard):
    """Resolving an item is the commonest edit there is."""
    resolved = ONE.replace("**Open**", "**Resolved** (2026-10-02, {pull}`2`)")

    assert frozen(guard, items(ONE, TWO), items(resolved, TWO)) == []


def test_an_item_removed_fails(guard):
    """Its number would name the item after it."""
    assert len(frozen(guard, items(ONE, TWO, THREE), items(ONE, THREE))) == 2


def test_a_numbered_list_without_bold_titles_is_not_frozen(guard):
    """The steps of a procedure are not cited by number."""
    assert (
        frozen(guard, "1. First.\n2. Second.", "1. Zeroth.\n2. First.\n3. Second.")
        == []
    )


def test_a_row_appended_passes(guard):
    """Appending a row gives none a new number."""
    base = roadmap(("1", "The grammar"), ("2", "The transform"))
    head = roadmap(("1", "The grammar"), ("2", "The transform"), ("3", "The guard"))

    assert frozen(guard, base, head) == []


def test_a_row_inserted_mid_table_fails(guard):
    """A row cited as "row 2" would name the newcomer."""
    base = roadmap(("1", "The grammar"), ("2", "The transform"))
    head = roadmap(("1", "The grammar"), ("2", "The guard"), ("3", "The transform"))

    problems = frozen(guard, base, head)

    assert len(problems) == 1
    assert "row 2" in problems[0]
    assert "row 3" in problems[0]


def test_a_row_split_into_lettered_rows_passes(guard):
    """Row 6 of the type coverage roadmap became 6a to 6c, and kept its number."""
    base = roadmap(("5", "The mesh"), ("6", "The library"), ("7", "The gallery"))
    head = roadmap(
        ("5", "The mesh"),
        ("6a", "The library, first part"),
        ("6b", "The library, second part"),
        ("6c", "The library, last part"),
        ("7", "The gallery"),
    )

    assert frozen(guard, base, head) == []


def test_a_row_removed_fails(guard):
    """Its number would be free for the next row to take."""
    base = roadmap(("1", "The grammar"), ("2", "The transform"))

    assert len(frozen(guard, base, roadmap(("1", "The grammar")))) == 1


def test_a_roadmap_with_more_columns_is_read(guard):
    """The type coverage roadmap counts lines between its scope and status."""
    header = "| # | Scope | Lines | Status |\n|---|---|---:|---|\n"
    table = header + "| 6a | The library | 40 | done |"

    assert list(guard.roadmap_rows(table)) == ["6a"]
    assert guard.roadmap_rows(table)["6a"].title == "The library"


#: A section inserted at 2, moving Design to 3 and Testing to 4.
INSERTED = spec(
    ("1", "Purpose", PURPOSE),
    ("2", "Scope", "What the design covers, and what it leaves to others to settle."),
    ("3", "Design", DESIGN),
    ("4", "Testing", TESTING),
)


@pytest.fixture
def renumbered(guard, tmp_path):
    """Provide the specification after a section is inserted, and its namespace."""
    path = tmp_path / "2026-01-01-demo-design.md"
    path.write_text(INSERTED, encoding="utf-8")
    names = guard.grammar.namespace([path])
    fates = guard.pair(guard.sections(BASE), guard.sections(INSERTED))
    return path, names, fates


def test_an_untouched_citation_of_a_moved_section_is_stale(guard, tmp_path, renumbered):
    """Written against the old layout, it now names the newcomer."""
    spec_path, names, fates = renumbered
    code = tmp_path / "code.py"
    texts = {spec_path: INSERTED, code: f"# see demo spec {SECTION}2\n"}

    (finding,) = guard.stale(texts, fates, names, {})

    assert (finding.path, finding.line, finding.cited) == (
        code,
        1,
        f"demo spec {SECTION}2",
    )
    assert finding.fate.anchor == "demo-spec-3"


def test_a_citation_on_a_changed_line_is_the_authors_to_have_checked(
    guard, tmp_path, renumbered
):
    """A line the pull request changed passes."""
    spec_path, names, fates = renumbered
    code = tmp_path / "code.py"
    texts = {spec_path: INSERTED, code: f"# see demo spec {SECTION}2\n"}

    assert guard.stale(texts, fates, names, {code: {1}}) == []


def test_a_bare_citation_inside_the_specification_and_a_role_are_read(
    guard, tmp_path, renumbered
):
    """Inside its own document a citation needs no prefix, and a role is a citation."""
    spec_path, names, fates = renumbered
    text = INSERTED + f"\nSee {SECTION}3 and {{ref}}`{SECTION}2 <demo-spec-2>`.\n"
    page = tmp_path / "page.rst"
    texts = {
        spec_path: text,
        page: f"See :ref:`demo spec {SECTION}2 <demo-spec-2>`.\n",
    }

    found = {(f.path.name, f.cited) for f in guard.stale(texts, fates, names, {})}

    assert found == {
        (spec_path.name, f"{SECTION}3"),
        (spec_path.name, f"{SECTION}2"),
        ("page.rst", f"demo spec {SECTION}2"),
    }


def test_a_citation_of_a_kept_section_is_not_stale(guard, tmp_path, renumbered):
    """Section 1 kept its number."""
    spec_path, names, fates = renumbered
    texts = {spec_path: INSERTED, tmp_path / "code.py": f"# demo spec {SECTION}1\n"}

    assert guard.stale(texts, fates, names, {}) == []


def test_a_removed_section_is_described_by_what_its_number_names_now(guard, tmp_path):
    """The reader is told what the stale citation now opens."""
    head = spec(("1", "Purpose", PURPOSE), ("2", "Testing", TESTING))
    path = tmp_path / "2026-01-01-demo-design.md"
    path.write_text(head, encoding="utf-8")
    names = guard.grammar.namespace([path])
    fates = guard.pair(guard.sections(BASE), guard.sections(head))
    code = tmp_path / "code.py"
    texts = {path: head, code: f"# demo spec {SECTION}2, {SECTION}3\n"}

    found = guard.stale(texts, fates, names, {})
    described = [guard.describe(f, tmp_path, guard.sections(head)) for f in found]

    removed = (
        f'code.py:1: demo spec {SECTION}2 was "Design", which was removed; '
        f'{SECTION}2 is now "Testing"'
    )
    moved = f'code.py:1: {SECTION}3 was "Testing", which is now {SECTION}2'
    assert described == [removed, moved]


def test_rewrite_moves_a_citation_on_the_lines_named_and_no_others(
    guard, tmp_path, renumbered
):
    """The fix touches only the untouched lines it was asked to, and a run's rest."""
    _, names, fates = renumbered
    text = f"# demo spec {SECTION}2, {SECTION}1/{SECTION}3\n# demo spec {SECTION}2\n"

    fixed = guard.rewrite(text, tmp_path / "code.py", fates, names, {1})

    assert (
        fixed
        == f"# demo spec {SECTION}3, {SECTION}1/{SECTION}4\n# demo spec {SECTION}2\n"
    )


def test_rewrite_turns_a_roles_display_and_target_together(guard, renumbered):
    """A role carries the number twice, and both must move."""
    spec_path, names, fates = renumbered
    text = f"See {{ref}}`{SECTION}2 <demo-spec-2>` and :ref:`x <demo-spec-3>`.\n"

    fixed = guard.rewrite(text, spec_path, fates, names, {1})

    assert (
        fixed == f"See {{ref}}`{SECTION}3 <demo-spec-3>` and :ref:`x <demo-spec-4>`.\n"
    )


def test_rewrite_leaves_a_removed_sections_citation_for_the_author(guard, tmp_path):
    """A removed section has no new number to take."""
    head = spec(("1", "Purpose", PURPOSE), ("2", "Testing", TESTING))
    path = tmp_path / "2026-01-01-demo-design.md"
    path.write_text(head, encoding="utf-8")
    names = guard.grammar.namespace([path])
    fates = guard.pair(guard.sections(BASE), guard.sections(head))
    text = f"# demo spec {SECTION}2 and demo spec {SECTION}3\n"

    fixed = guard.rewrite(text, tmp_path / "code.py", fates, names, {1})

    assert fixed == f"# demo spec {SECTION}2 and demo spec {SECTION}2\n"

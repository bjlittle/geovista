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

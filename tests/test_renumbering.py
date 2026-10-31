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


#: Where a repository keeps its specifications.
SPECS = Path("docs") / "src" / "developer" / "specs"

#: The specification the repositories below hold, by name.
NAME = "2026-01-01-demo-design.md"


def git(root: Path, *args: str) -> str:
    """Run git in ``root`` as nobody in particular, signing nothing."""
    import subprocess  # noqa: PLC0415

    identity = ["-c", "user.name=test", "-c", "user.email=test@example.com"]
    command = ["git", *identity, "-c", "commit.gpgsign=false", *args]
    done = subprocess.run(  # noqa: S603
        command, cwd=root, capture_output=True, text=True, check=True
    )
    return done.stdout


def commit(root: Path, files: dict[str, str], message: str) -> None:
    """Write the files given, relative to ``root``, and commit them."""
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(root, "add", "--all")
    git(root, "commit", "--quiet", "--message", message)


@pytest.fixture
def repo(tmp_path) -> Path:
    """Provide a repository whose main branch holds a specification and a citation."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "--quiet", "--initial-branch", "main")
    commit(
        root,
        {
            str(SPECS / NAME): BASE,
            "src/code.py": f"# see demo spec {SECTION}2\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}3.\n",
            "src/other.py": "# nothing cited\n",
        },
        "start",
    )
    git(root, "switch", "--quiet", "--create", "work")
    return root


def run(guard, root: Path, *args: str, capsys) -> tuple[int, str]:
    """Run the guard against ``main``, returning its exit code and its output."""
    code = guard.main(["--base", "main", *args], root=root)
    return code, capsys.readouterr().out


def test_a_renumber_leaving_a_citation_behind_fails(guard, repo, capsys):
    """The pull request moves Design, and code.py still cites its old number."""
    commit(repo, {str(SPECS / NAME): INSERTED}, "insert")

    code, out = run(guard, repo, capsys=capsys)

    assert code == 1
    assert f'src/code.py:1: demo spec {SECTION}2 was "Design", which is now' in out
    assert f'CHANGELOG.rst:1: demo spec {SECTION}3 was "Testing"' in out
    assert "gv-developer-checks-spec-renumbering" in out


def test_a_renumber_that_updates_its_citations_passes(guard, repo, capsys):
    """Every citation of what moved is on a line the pull request changed.

    Holds citation spec §2 decision 3.
    """
    commit(
        repo,
        {
            str(SPECS / NAME): INSERTED,
            "src/code.py": f"# see demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "insert",
    )

    assert run(guard, repo, capsys=capsys)[0] == 0


def test_fix_rewrites_the_stale_citations_and_nothing_else(guard, repo, capsys):
    """Released entries included: a stale link is worth nothing.

    Holds citation spec §2 decision 4.
    """
    commit(repo, {str(SPECS / NAME): INSERTED}, "insert")
    other = (repo / "src" / "other.py").read_text(encoding="utf-8")

    code, _ = run(guard, repo, "--fix", capsys=capsys)

    assert code == 0
    assert (repo / "src/code.py").read_text() == f"# see demo spec {SECTION}3\n"
    assert (repo / "CHANGELOG.rst").read_text() == (
        f"Released: see demo spec {SECTION}4.\n"
    )
    assert (repo / "src" / "other.py").read_text(encoding="utf-8") == other
    assert run(guard, repo, capsys=capsys)[0] == 0


def test_a_renumbered_item_fails(guard, repo, capsys):
    """Items are appended, never inserted."""
    commit(
        repo,
        {str(SPECS / NAME): spec(("1", "Items", items(ONE, TWO)))},
        "items",
    )
    git(repo, "switch", "--quiet", "main")
    git(repo, "merge", "--quiet", "--ff-only", "work")
    git(repo, "switch", "--quiet", "--create", "more")
    commit(repo, {str(SPECS / NAME): spec(("1", "Items", items(ONE, THREE, TWO)))}, "x")

    code, out = run(guard, repo, capsys=capsys)

    assert code == 1
    assert "item 2" in out
    assert "is now item 3" in out


def test_the_audit_finds_a_citation_older_than_the_renumber(guard, repo, capsys):
    """Written on a branch made before the renumber, and merged after it."""
    git(repo, "switch", "--quiet", "main")
    git(repo, "switch", "--quiet", "--create", "late")
    commit(repo, {"src/late.py": f"# see demo spec {SECTION}3\n"}, "late citation")
    git(repo, "switch", "--quiet", "main")
    commit(
        repo,
        {
            str(SPECS / NAME): INSERTED,
            "src/code.py": f"# see demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "renumber, citations updated",
    )
    git(repo, "merge", "--quiet", "--no-edit", "late")

    code, out = run(guard, repo, "--audit", capsys=capsys)

    assert code == 1
    assert f'src/late.py:1: demo spec {SECTION}3 was "Testing", which is now' in out
    assert "src/code.py" not in out

    commit(repo, {"src/late.py": f"# see demo spec {SECTION}4\n"}, "fixed")

    assert run(guard, repo, "--audit", capsys=capsys)[0] == 0


def test_a_base_that_does_not_exist_cannot_be_checked(guard, repo, capsys):
    """A failure to compare is never taken for a finding."""
    assert guard.main(["--base", "nowhere"], root=repo) == 2
    capsys.readouterr()


def test_the_guard_runs_on_every_pull_request_and_audits_each_night():
    """Any pull request can add a citation, so the guard cannot wait for a spec."""
    import yaml  # noqa: PLC0415

    root = SCRIPT.parents[2]
    workflow = yaml.safe_load(
        (root / ".github" / "workflows" / "ci-citations.yml").read_text(
            encoding="utf-8"
        )
    )
    # YAML 1.1 reads the bare key "on" as the boolean True
    triggers = workflow.get("on", workflow.get(True))
    jobs = workflow["jobs"]

    def steps(job: str) -> str:
        return yaml.safe_dump(jobs[job]["steps"], width=10_000)

    assert triggers["pull_request"] is None or "paths" not in triggers["pull_request"]
    assert "schedule" in triggers
    assert "fetch-depth: 0" in steps("renumbering")
    assert "check_renumbering.py --base" in steps("renumbering")
    assert "fetch-depth: 0" in steps("audit")
    assert "check-spec-renumbering audit" in steps("audit")


#: Design's text, grown fourfold, as a living section grows over several changes.
GROWN = " ".join(
    [DESIGN, *(f"Further measured detail, number {n}." for n in range(12))]
)


def test_the_audit_follows_a_section_renamed_then_grown(guard, repo, capsys):
    """Each change is one the pairing reads; the two together are not."""
    git(repo, "switch", "--quiet", "main")
    renamed = spec(
        ("1", "Purpose", PURPOSE), ("2", "Pairing", DESIGN), ("3", "Testing", TESTING)
    )
    commit(repo, {str(SPECS / NAME): renamed}, "rename")
    grown = spec(
        ("1", "Purpose", PURPOSE), ("2", "Pairing", GROWN), ("3", "Testing", TESTING)
    )
    commit(repo, {str(SPECS / NAME): grown}, "grow")

    code, out = run(guard, repo, "--audit", capsys=capsys)

    assert code == 0, out


def test_the_audit_judges_an_older_line_from_its_baseline(
    guard, repo, capsys, monkeypatch
):
    """History before the hand audit was checked by hand, and is not judged again."""
    git(repo, "switch", "--quiet", "main")
    rewritten = spec(
        ("1", "Purpose", PURPOSE),
        ("2", "Mechanism", "Nothing of the earlier wording survives this rewrite."),
        ("3", "Testing", TESTING),
    )
    commit(repo, {str(SPECS / NAME): rewritten}, "rename and rewrite at once")
    baseline = git(repo, "rev-parse", "HEAD").strip()

    assert run(guard, repo, "--audit", capsys=capsys)[0] == 1

    monkeypatch.setattr(guard, "AUDITED", baseline)

    assert run(guard, repo, "--audit", capsys=capsys)[0] == 0


def test_an_item_resolved_and_reworded_in_place_passes(guard):
    """Resolving an item rewrites its status, its title's tense and its text."""
    before = "**Open** — **Nothing proves the references point at real work.**"
    after = (
        "**Resolved** (2026-10-09, {pull}`9`) — **Nothing proved the references "
        "pointed at real work.**\n   A script now asks GitHub about each one, and "
        "the nightly job reports what has moved on, which closes the question."
    )

    assert frozen(guard, items(ONE, before, THREE), items(ONE, after, THREE)) == []


def test_a_row_rescoped_in_place_passes(guard):
    """A row's scope is rewritten as its work is planned, under the same number."""
    base = roadmap(("1", "The grammar"), ("2", "The globe model"), ("3", "Heights"))
    head = roadmap(
        ("1", "The grammar"),
        ("2", "The globe model, and units through pint and pint-cf"),
        ("3", "Heights"),
    )

    assert frozen(guard, base, head) == []


def test_a_section_sharing_its_title_pairs_with_the_one_whose_text_it_has(guard):
    """Two subsections titled alike: delete the first, and the second moves up."""
    first = "Covers the first design and nothing of the second."
    second = "Covers the testing of the second, a different matter."
    base = spec(
        ("3", "Design", DESIGN),
        ("3.1", "Scope", first),
        ("4", "Testing", TESTING),
        ("4.1", "Scope", second),
    )
    head = spec(("3", "Testing", TESTING), ("3.1", "Scope", second))

    found = fates(guard, base, head)

    assert found["demo-spec-3-1"] == ("removed", None)
    assert found["demo-spec-4-1"] == ("moved", "demo-spec-3-1")


def test_a_pull_request_adding_a_citation_older_than_a_renumber_fails(
    guard, repo, capsys
):
    """As CI checks it: GitHub's merge of the branch into a main renumbered since.

    The repository squash-merges, so once merged the citation's history is gone,
    and only the pull request can be checked against when it was written.
    """
    git(repo, "switch", "--quiet", "main")
    git(repo, "switch", "--quiet", "--create", "late")
    commit(repo, {"src/late.py": f"# see demo spec {SECTION}3\n"}, "late citation")
    git(repo, "switch", "--quiet", "main")
    commit(
        repo,
        {
            str(SPECS / NAME): INSERTED,
            "src/code.py": f"# see demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "renumber, citations updated",
    )
    git(repo, "switch", "--quiet", "--detach", "main")
    git(repo, "merge", "--quiet", "--no-ff", "--no-edit", "late")

    code, out = run(guard, repo, capsys=capsys)

    assert code == 1
    assert f'src/late.py:1: demo spec {SECTION}3 was "Testing", which is now' in out


def test_fix_rewrites_a_citation_older_than_a_renumber(guard, repo, capsys):
    """Its section's new number comes from where the citation was written."""
    git(repo, "switch", "--quiet", "main")
    git(repo, "switch", "--quiet", "--create", "late")
    commit(repo, {"src/late.py": f"# see demo spec {SECTION}3\n"}, "late citation")
    git(repo, "switch", "--quiet", "main")
    commit(
        repo,
        {
            str(SPECS / NAME): INSERTED,
            "src/code.py": f"# see demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "renumber, citations updated",
    )
    git(repo, "switch", "--quiet", "late")
    git(repo, "merge", "--quiet", "--no-edit", "main")

    code, _ = run(guard, repo, "--fix", capsys=capsys)

    assert code == 0
    assert (repo / "src" / "late.py").read_text() == f"# see demo spec {SECTION}4\n"


def test_fix_rewrites_a_lines_citations_from_its_original_text(guard, repo, capsys):
    """Two moved sections on one line: a number just written is not read again."""
    git(repo, "switch", "--quiet", "main")
    commit(repo, {"src/code.py": f"# see demo spec {SECTION}2/{SECTION}3\n"}, "both")
    git(repo, "switch", "--quiet", "--create", "insert")
    commit(repo, {str(SPECS / NAME): INSERTED}, "insert")

    code, _ = run(guard, repo, "--fix", capsys=capsys)

    assert code == 0
    assert (repo / "src" / "code.py").read_text() == (
        f"# see demo spec {SECTION}3/{SECTION}4\n"
    )


def test_a_sibling_branchs_edits_do_not_rewind_a_section(guard, repo, capsys):
    """Main renames and grows Design while the branch cites it and edits Purpose."""
    git(repo, "switch", "--quiet", "main")
    git(repo, "switch", "--quiet", "--create", "late")
    commit(repo, {"src/late.py": f"# see demo spec {SECTION}2\n"}, "cite design")
    edited = spec(
        ("1", "Purpose", PURPOSE + " Edited."),
        ("2", "Design", DESIGN),
        ("3", "Testing", TESTING),
    )
    commit(repo, {str(SPECS / NAME): edited}, "edit purpose")
    git(repo, "switch", "--quiet", "main")
    renamed = spec(
        ("1", "Purpose", PURPOSE), ("2", "Pairing", DESIGN), ("3", "Testing", TESTING)
    )
    commit(repo, {str(SPECS / NAME): renamed}, "rename")
    grown = spec(
        ("1", "Purpose", PURPOSE), ("2", "Pairing", GROWN), ("3", "Testing", TESTING)
    )
    commit(repo, {str(SPECS / NAME): grown}, "grow")
    git(repo, "switch", "--quiet", "--detach", "main")
    git(repo, "merge", "--quiet", "--no-ff", "--no-edit", "late")

    code, out = run(guard, repo, capsys=capsys)

    assert code == 0, out


def test_items_removed_with_their_section_are_reported(guard):
    """Deleting the section that holds them removes every item in it."""
    base = spec(("1", "Purpose", PURPOSE), ("2", "Items", items(ONE, TWO)))
    head = spec(("1", "Purpose", PURPOSE))

    problems = guard.frozen(base, head)

    assert len(problems) == 2
    assert all("removed" in problem for problem in problems)


def test_a_baseline_the_branch_has_not_reached_is_not_used(
    guard, repo, capsys, monkeypatch
):
    """A baseline ahead of the commit being judged would follow it backwards."""
    git(repo, "switch", "--quiet", "main")
    commit(repo, {"src/cite.py": f"# demo spec {SECTION}2\n"}, "cite design")
    cited = git(repo, "rev-parse", "HEAD").strip()
    rewritten = spec(
        ("1", "Purpose", PURPOSE),
        ("2", "Mechanism", "Nothing of the earlier wording survives this rewrite."),
        ("3", "Testing", TESTING),
    )
    commit(repo, {str(SPECS / NAME): rewritten}, "rename and rewrite at once")
    monkeypatch.setattr(guard, "AUDITED", git(repo, "rev-parse", "HEAD").strip())
    git(repo, "switch", "--quiet", "--detach", cited)

    code = guard.main(["--base", f"{cited}~1"], root=repo)
    out = capsys.readouterr().out

    assert code == 0, out


def test_a_line_citing_a_section_its_own_pull_request_rewrote_passes(
    guard, repo, capsys
):
    """The pull request renames and rewrites Design, and cites it as it now stands."""
    rewritten = spec(
        ("1", "Purpose", PURPOSE),
        ("2", "Mechanism", "Nothing of the earlier wording survives this rewrite."),
        ("3", "Testing", TESTING),
    )
    commit(
        repo,
        {
            str(SPECS / NAME): rewritten,
            "src/code.py": f"# see demo spec {SECTION}2, the mechanism\n",
        },
        "rewrite design, and cite it",
    )

    code, out = run(guard, repo, capsys=capsys)

    assert code == 0, out


def test_a_branch_that_took_a_renumber_by_cherry_pick_cites_by_it(guard, repo, capsys):
    """The branch already uses main's numbering, so its citation is correct."""
    git(repo, "switch", "--quiet", "main")
    commit(
        repo,
        {
            str(SPECS / NAME): INSERTED,
            "src/code.py": f"# see demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "renumber, citations updated",
    )
    renumber = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "switch", "--quiet", "work")
    commit(repo, {"src/other.py": "# unrelated\n"}, "unrelated")
    git(repo, "cherry-pick", renumber)
    commit(repo, {"src/new.py": f"# see demo spec {SECTION}3, the design\n"}, "cite")
    git(repo, "switch", "--quiet", "--detach", "main")
    git(repo, "merge", "--quiet", "--no-ff", "--no-edit", "work")

    code, out = run(guard, repo, capsys=capsys)

    assert code == 0, out
    assert run(guard, repo, "--fix", capsys=capsys)[0] == 0
    assert (repo / "src" / "new.py").read_text() == (
        f"# see demo spec {SECTION}3, the design\n"
    )


def test_an_unclosed_bold_title_is_read_without_failing(guard):
    """An item mid-edit, its bold not yet closed, is no item to freeze."""
    text = spec(("8", "Open Items", "1. **An unclosed title.\n2. **Fine.**"))

    assert list(guard.numbered_items(text)["demo-spec-8"]) == ["2"]


def test_a_table_row_of_one_cell_is_read_without_failing(guard):
    """A roadmap row mid-edit has its number and nothing else yet."""
    table = "| # | Scope | Status |\n|---|---|---|\n| 1 | The grammar | done |\n| 2 |"

    assert list(guard.roadmap_rows(table)) == ["1", "2"]


def test_two_numbered_lists_in_a_section_are_kept_apart(guard):
    """The second list numbers from 1 again, and must not overwrite the first."""
    lists = items(ONE, TWO) + "\n\nThen another list.\n\n" + items(THREE)
    found = guard.numbered_items(spec(("8", "Open Items", lists)))["demo-spec-8"]

    assert [section.title for section in found.values()] == [
        "The first question.",
        "The second question, wrapped.",
        "The third question.",
    ]


@pytest.mark.parametrize(
    "setting",
    [
        ["diff.mnemonicPrefix", "true"],
        ["diff.noprefix", "true"],
        ["diff.external", "false"],
    ],
)
def test_local_diff_settings_do_not_change_what_reads_as_changed(
    guard, repo, capsys, setting
):
    """A user's own diff configuration must not make a changed line look untouched."""
    git(repo, "config", *setting)
    commit(
        repo,
        {
            str(SPECS / NAME): INSERTED,
            "src/code.py": f"# see demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "insert, citations updated",
    )

    code, out = run(guard, repo, capsys=capsys)

    assert code == 0, out


def test_a_changed_line_in_a_path_with_a_space_is_read(guard, repo, capsys):
    """Git marks such a path with a tab on its diff header."""
    commit(repo, {"src/my code.py": f"# see demo spec {SECTION}2\n"}, "cite")
    git(repo, "switch", "--quiet", "main")
    git(repo, "merge", "--quiet", "--ff-only", "work")
    git(repo, "switch", "--quiet", "--create", "again")
    commit(
        repo,
        {
            str(SPECS / NAME): INSERTED,
            "src/code.py": f"# see demo spec {SECTION}3\n",
            "src/my code.py": f"# see demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "insert, citations updated",
    )

    code, out = run(guard, repo, capsys=capsys)

    assert code == 0, out


def test_an_untracked_file_counts_as_changed(guard, repo, capsys):
    """A file not yet added is the author's own, written against the new layout."""
    commit(
        repo,
        {
            str(SPECS / NAME): INSERTED,
            "src/code.py": f"# see demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "insert, citations updated",
    )
    (repo / "src" / "new.py").write_text(f"# see demo spec {SECTION}3\n")

    code, out = run(guard, repo, capsys=capsys)

    assert code == 0, out


def test_rewrite_turns_a_role_with_a_bare_target_and_one_not_numbered(
    guard, renumbered
):
    """A role naming only its target, or showing words, still has a target to move."""
    spec_path, names, fates = renumbered
    text = "See {ref}`demo-spec-2` and {ref}`the design <demo-spec-2>`.\n"

    fixed = guard.rewrite(text, spec_path, fates, names, {1})

    assert fixed == "See {ref}`demo-spec-3` and {ref}`the design <demo-spec-3>`.\n"


def test_a_specification_renamed_keeps_its_sections(guard, repo, capsys):
    """Renaming its file moves no section, so no citation goes stale."""
    git(repo, "mv", str(SPECS / NAME), str(SPECS / "2026-01-01-renamed-design.md"))
    git(repo, "commit", "--quiet", "--message", "rename")

    code, out = run(guard, repo, capsys=capsys)

    assert code == 0, out


def test_the_audit_shows_each_revision_once(guard, repo, capsys, monkeypatch):
    """Chains from different commits share their later revisions."""
    git(repo, "switch", "--quiet", "main")
    commit(repo, {"src/one.py": f"# demo spec {SECTION}1\n"}, "one")
    commit(repo, {"src/two.py": f"# demo spec {SECTION}1\n"}, "two")
    commit(
        repo,
        {
            str(SPECS / NAME): INSERTED,
            "src/code.py": f"# demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "insert",
    )
    shown: list[str] = []
    real = guard.git

    def counting(root: Path, *args: str) -> str:
        if args[0] == "show":
            shown.append(args[1])
        return real(root, *args)

    monkeypatch.setattr(guard, "git", counting)

    assert run(guard, repo, "--audit", capsys=capsys)[0] == 0
    assert len(shown) == len(set(shown)), "a revision was shown more than once"


def test_a_removed_section_is_reported_through_the_command_line(guard, repo, capsys):
    """The report names what a removed section's number holds now."""
    commit(
        repo,
        {str(SPECS / NAME): spec(("1", "Purpose", PURPOSE), ("2", "Testing", TESTING))},
        "remove design",
    )

    code, out = run(guard, repo, capsys=capsys)

    assert code == 1
    assert (
        f'src/code.py:1: demo spec {SECTION}2 was "Design", which was removed; ' in out
    )


def test_the_last_section_removed_still_reports_its_items(guard, repo, capsys):
    """A specification left with no anchor is still the file it was."""
    git(repo, "switch", "--quiet", "main")
    commit(repo, {str(SPECS / NAME): spec(("8", "Open Items", items(ONE, TWO)))}, "x")
    git(repo, "switch", "--quiet", "--force-create", "work")
    retired = spec() + "\nThis specification no longer applies.\n"
    commit(repo, {str(SPECS / NAME): retired}, "remove the last section")

    code, out = run(guard, repo, capsys=capsys)

    assert code == 1
    assert 'item 1 "The first question." was removed with its section' in out


@pytest.mark.parametrize("audit", [False, True], ids=["pull-request", "audit"])
def test_a_citation_older_than_a_specification_renamed_and_renumbered_fails(
    guard, repo, capsys, audit
):
    """The specification is found by the prefix it owns at each revision."""
    git(repo, "switch", "--quiet", "main")
    git(repo, "switch", "--quiet", "--create", "late")
    commit(repo, {"src/late.py": f"# see demo spec {SECTION}2\n"}, "late citation")
    git(repo, "switch", "--quiet", "main")
    renamed = SPECS / "2026-01-01-renamed-design.md"
    git(repo, "mv", str(SPECS / NAME), str(renamed))
    git(repo, "commit", "--quiet", "--message", "rename")
    commit(
        repo,
        {
            str(renamed): INSERTED,
            "src/code.py": f"# see demo spec {SECTION}3\n",
            "CHANGELOG.rst": f"Released: see demo spec {SECTION}4.\n",
        },
        "renumber, citations updated",
    )
    git(repo, "switch", "--quiet", "late")
    git(repo, "merge", "--quiet", "--no-edit", "main")

    code, out = run(guard, repo, *(["--audit"] if audit else []), capsys=capsys)

    assert code == 1
    assert f'src/late.py:1: demo spec {SECTION}2 was "Design", which is now' in out


#: Decisions in the form of ledger spec §3.2, their states built by name.
AGREED = "\N{HANDSHAKE} Agreed"
FIRST = (
    f"**{AGREED}** (2026-10-30, {{user}}`bjlittle`, {{pull}}`1`) — **The first.** A."
)
SECOND = (
    f"**{AGREED}** (2026-10-30, {{user}}`bjlittle`, {{pull}}`1`) — **The second.** B."
)
THIRD = (
    f"**{AGREED}** (2026-10-30, {{user}}`bjlittle`, {{pull}}`1`) — **The third.** C."
)


def test_a_decision_inserted_mid_list_fails_naming_it(guard):
    """Ledger spec §2 decision 2: a decision keeps its number, read by its title."""
    base = spec(("1", "Purpose", PURPOSE), ("2", "Decisions", items(FIRST, SECOND)))
    head = spec(
        ("1", "Purpose", PURPOSE), ("2", "Decisions", items(FIRST, THIRD, SECOND))
    )

    problems = guard.frozen(base, head)

    assert len(problems) == 1
    assert "The second." in problems[0]
    assert AGREED not in problems[0]


def test_a_decision_with_a_wrapped_title_is_named_whole(guard):
    """A decision's title that wraps is read whole, past its state (#2787)."""
    wrapped = (
        f"**{AGREED}** (2026-10-30, {{user}}`bjlittle`, {{pull}}`1`) — **The second,\n"
        "   wrapped.** B."
    )
    base = spec(("1", "Purpose", PURPOSE), ("2", "Decisions", items(FIRST, wrapped)))
    head = spec(
        ("1", "Purpose", PURPOSE), ("2", "Decisions", items(FIRST, THIRD, wrapped))
    )

    problems = guard.frozen(base, head)

    assert len(problems) == 1
    assert "The second, wrapped." in problems[0]


def test_a_roadmap_scope_keeps_an_escaped_pipe(guard):
    """A row is titled by its whole scope, escaped pipe and all (#2787)."""
    text = spec(("4", "Roadmap", roadmap(("1", "a \\| b"))))

    assert guard.roadmap_rows(text)["1"].title == "a \\| b"

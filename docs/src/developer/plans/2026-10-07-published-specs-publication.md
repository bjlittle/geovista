---
orphan: true
---

# published specs change 1 — publication and conventions

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** publish `geovista`'s design specifications under a developer-guide index, keep the
frozen plans out of the build, give every citation its section sign, and land
`tests/test_spec_conventions.py`, which holds the specifications to their conventions and
asserts the roadmap's triggers.

**Architecture:** `conf.py` excludes `developer/plans/**`, and the reading-time gate's
`EXCLUDED_DIRS` follows it under a test that checks `conf.py` really does. A new
`developer/specs/index.rst` carries the toctree and the namespace table, reached from a
Specifications card. The test module derives its corpus by walking the repository, less a
tuple of pruned trees, and reads it with a citation grammar adapted from `tephpy`'s
`docs/src/_ext/tephpy_citations.py`. Each rule is a function of a file and its text that
returns one message per fault, so a fixture shows the rule firing and the repository test
shows it holding.

**Tech Stack:** Sphinx with MyST, sphinx-design cards, `pytest`, `ruff`, and `re`, `ast` and
`dataclasses` from the standard library.

**Spec:** `docs/src/developer/specs/2026-10-06-published-specs-design.md`, cited throughout
as `docs spec §…`. This plan implements change 1 of docs spec §4, tracked by issue #2566.

## Global Constraints

- **Copyright header.** Every Python file opens with the four-line BSD header of the root
  `AGENTS.md`, then `from __future__ import annotations`. Both are ruff-enforced.
- **ruff.** Line length 88; `select = ["ALL"]` with preview rules opt-in; the NumPy
  docstring convention, so every function has a docstring whose summary is imperative
  (D401). `test*.py` is excused only `ANN001`, `ANN201` and `SLF001`. Run `ruff format` on
  the module before every commit: the hook rejects a commit it had to reformat.
- **pytest.** `--doctest-modules` is on, so no `>>>` in a docstring;
  `filterwarnings = ["error", ...]`; strict markers. Run through
  `pixi run --frozen -e geovista`.
- **The module never skips.** `tests/AGENTS.md`: a source-tree policy gate has nothing to
  skip on and must not acquire one.
- **The module sits inside its own corpus.** Never write a literal section sign followed by
  a digit in it except as a real citation that resolves. Fixtures build the sign from
  `SECTION` and cite the `demo spec` prefix, which no specification declares.
- **Cite sparingly from the module.** Every citation outside the specifications counts
  toward the ceiling of thirty-five that rows 2 to 4 of docs spec §4 watch. The module as
  planned carries six; the whole repository, fifteen.
- **Commit through the environment**, whose `pre-commit` the hook needs:
  `pixi run --frozen -e geovista git commit`. End every message with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **`PR` and `TODAY`.** `PR` is the number of the pull request opened in Task 0, and
  `TODAY` the ISO date the step is done. Substitute both wherever this plan writes them.
- **Specifications are humanized prose wrapped at 92 columns**, and the edits below keep
  both. The changelog fragment and the pull request description are humanized too; this
  plan is not.
- **This plan is frozen once its pull request merges.** Until then it may be corrected in
  place, with the reason in the commit message.

## Corrections this plan makes to the specification

Writing the plan against the tree turned up places where docs spec and the work disagree.
Each is corrected in the task that owns it, and the two that change a rule are recorded in
docs spec §8 under its own status grammar.

1. **Row 2's trigger fired on its own document** (decided with Bill on 2026-10-07). It
   counted citation prefixes and failed past one, but the specification declares the second,
   `docs spec`, and change 1 cites it from live files. A wrong prefix is also the one
   mistake the transform cannot catch, since both anchors exist. Rows 2 to 4 now share a
   scale trigger: citations outside the collection above thirty-five. Task 8; §8 item 5.
2. **The status rule could not cite another repository.** §3.5 item 7 asked for an
   `{issue}` or `{pull}` role, and the type coverage specification resolves its §8 item 4
   against `lazy-loader` issue 181 by link. A link to an issue or pull request elsewhere
   now counts. Task 6; §8 item 4.
3. **The corpus is every text file, not four named areas.** `tephpy` records a glob-named
   corpus missing files; §3.5 is reworded to what the test does. Task 2.
4. **`Spec §3.2` is a `tephpy`-ism.** `tephpy` has a bare `spec` prefix and `geovista` does
   not, so the case rule's example becomes `Typing spec §3.2`. Task 2.
5. **Counts that decay.** The role counts in §3.4 and §5 (fourteen, thirty-four,
   forty-eight) were stale at sixty-three and would stale again; they go. Task 5.
6. **Publication is asserted too.** No specification carries `orphan: true`, the index
   lists every specification, and its table names every declared prefix. §3.5 gains the
   sentence. Task 7.
7. **"A fifth card".** The developer index already shows five cards, the half-width
   Codecraft card among them. The Specifications card joins Codecraft in a second
   two-column grid, and the specification says "a card". Task 7.
8. **§8 item 1 is re-homed** from #2566, which this pull request closes, to row 2, whose
   transform retires the roles and the assertion with them. Task 9.

Two departures from `tephpy` are deliberate. The corpus is a pruned walk rather than
`git ls-files`, because `tephpy` then has to skip without a `.git`, which `geovista`
forbids, and docs spec §3.5 says to follow the reading-time gate, which walks. And the
grammar lives in the test module rather than in `docs/src/_ext`, because nothing else reads
it until row 2 lands; row 3 is where it moves.

## Review Focus

The failure modes docs spec implies that no rule of §3.5 exercises, most likely first. Each
line names the test that pins it, in the task that owns the code.

1. **A citation run wrapped across a line in a specification.** docs spec §3.2 forbids it;
   read a line at a time, the tail becomes a bare section number and resolves, silently, to
   the containing document. Reported by `wrapped`:
   `test_wrapped_finds_a_run_that_a_line_break_cuts` and
   `test_no_citation_run_wraps_a_line`, Task 4.
2. **A `{ref}` role broken across lines.** The line-based reader never sees it whole, so it
   would escape Agreement. Reported as "a role broken across lines":
   `test_agreement_finds_a_role_opening_another_section`, Task 5.
3. **A copied specification that keeps its template's prefix.** Two documents would share
   every anchor. `shared` and
   `test_a_copied_specification_sharing_its_prefix_is_caught`, Task 3.
4. **A section sign that is not a citation**: legal style puts a space after it, and a
   declaration writes an ellipsis. `test_a_section_sign_without_a_number_is_no_citation`,
   Task 2.
5. **Code outside markdown is read as text.** Only markdown fences are skipped, so a
   counterexample in a reStructuredText code block or a notebook fails loudly rather than
   passing silently; quote one inline instead. `test_only_markdown_fences_are_skipped`
   pins it, Task 2.

---

### Task 0: The branch, the plan, and the pull request

**Files:**
- Create: `docs/src/developer/plans/2026-10-07-published-specs-publication.md` (this plan)

**Interfaces:**
- Produces: `PR`, the number of the pull request every later task cites.

- [ ] **Step 1: Branch from an up-to-date `main`.**

```bash
git switch main && git pull --ff-only
git switch -c docs/spec-conventions
```

- [ ] **Step 2: Commit the plan, and check it builds and passes the hooks while it is still a built page.**

Until Task 1 excludes `developer/plans/**`, sphinx builds this plan as an orphan and the reading-time gate governs it, which is why it carries `orphan: true` and a banner.

```bash
git add docs/src/developer/plans/2026-10-07-published-specs-publication.md
pixi run --frozen -e geovista pre-commit run --files \
  docs/src/developer/plans/2026-10-07-published-specs-publication.md
pixi run --frozen -e geovista pytest tests/docs/test_readingtime_coverage.py -q
pixi run --frozen -e geovista git commit -F - <<'EOF'
docs: add the plan for change 1 of the published-specs roadmap

The plan for docs spec §4's change 1: publish the specifications under an
index, keep the frozen plans out of the build, sign every citation, and land
tests/test_spec_conventions.py. It is committed first for review, and the
implementation follows on top of it in the same pull request.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: hooks pass; the reading-time suite passes.

- [ ] **Step 3: Push and open the pull request; record its number as `PR`.**

```bash
git push -u origin docs/spec-conventions
gh pr create --base main --head docs/spec-conventions \
  --title "docs: publish the design specifications and hold them to their conventions" \
  --label agentic --label "type: documentation" --body-file <body>
```

The body, humanized:

```markdown
## 🚀 Pull Request

### Description

Change 1 of the published-specs roadmap (docs spec §4). It publishes the design specifications under a developer-guide index, keeps the implementation plans out of the build, puts the section sign into every citation, and lands `tests/test_spec_conventions.py` to hold the specifications to their conventions.

The plan is committed first for review, as `geovista` does with plans, and the implementation lands on top of it here: `docs/src/developer/plans/2026-10-07-published-specs-publication.md`.

Writing it turned up two rules in the specification that needed changing, and both changes are recorded in its §8:

- Row 2's trigger counted citation prefixes and failed once there were two, but the specification declares the second itself, so it would have fired the moment this change landed. Rows 2 to 4 now share a scale trigger: they activate when citations outside the collection pass thirty-five.
- The status rule accepted only `{issue}` and `{pull}` roles, while the type coverage specification resolves one of its items against an issue in `lazy-loader`. A link to an issue or pull request in another repository now counts.

Each task's code and its expected test output come from a dry run against `main` at `b894f66e`, which finished with 145 tests passing in the two suites, 2,505 across the non-image run, and a docs build with no warnings.

Closes #2566

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

- [ ] **Step 4: Correct issue #2566, whose body predates the measurements in docs spec §9.**

It says `tephpy`'s machinery serves 833 citations across more than ten namespaces and that `geovista` has five; the measured figures are 1,096 outside `docs/` across nineteen, and seven. It also ends on a `docs spec §…` placeholder. Edit the body to the measured figures and a link to the published specification, with a one-line correction note at the top, and comment that it was corrected and why.

- [ ] **Step 5: Stop for Bill's review of the plan. Do not start Task 1 until he has reviewed it.**

### Task 1: Withhold the plans from the build

**Files:**
- Modify: `docs/src/conf.py` (`exclude_patterns`)
- Modify: `tests/docs/test_readingtime_coverage.py` (`EXCLUDED_DIRS`, one new test)
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (roadmap row 1)

**Interfaces:**
- Produces: `"developer/plans/**"` in `exclude_patterns`, and `"developer/plans"` in `EXCLUDED_DIRS`, which `tests/test_spec_conventions.py` mirrors in its own `PRUNED` from Task 2.

- [ ] **Step 1: Write the failing test.**

In `tests/docs/test_readingtime_coverage.py`, add after `test_the_autoapi_templates_are_excluded_by_the_build_too`:

```python
def test_the_plans_are_excluded_by_the_build_too():
    """A plan the gate skips and sphinx still builds would publish unbannered."""
    conf = (DOCS / "conf.py").read_text(encoding="utf-8")

    assert '"developer/plans/**"' in conf
```

- [ ] **Step 2: Run it, and watch it fail.**

```bash
pixi run --frozen -e geovista pytest tests/docs/test_readingtime_coverage.py -q -k plans_are_excluded
```

Expected: `1 failed`, an `AssertionError` on `'"developer/plans/**"' in conf`.

- [ ] **Step 3: Exclude the plans in `docs/src/conf.py`.**

Replace:

```text
    "Thumbs.db",
    "reference/generated/api/index.rst",
```

with:

```text
    "Thumbs.db",
    # a plan records what was intended before implementation and is not updated
    # afterwards, so a published one would be wrong by design (docs spec §3.1)
    "developer/plans/**",
    "reference/generated/api/index.rst",
```

- [ ] **Step 4: Reword the comment over `EXCLUDED_DIRS`, which now holds a tree somebody writes.**

Replace:

```text
#: The trees holding no page anybody writes. This is a different thing from an
#: exemption: "EXEMPT" below is for pages somebody could have put a banner on
#: and should not.
```

with:

```text
#: The trees holding no page sphinx publishes as written: generated by a tool,
#: or, for the plans, withheld from the build. This is a different thing from
#: an exemption: "EXEMPT" below is for pages somebody could have put a banner
#: on and should not.
```

- [ ] **Step 5: Name the plans in `EXCLUDED_DIRS`.**

Replace:

```text
    "_static",  # sphinx excludes "html_static_path" from document discovery
```

with:

```text
    "_static",  # sphinx excludes "html_static_path" from document discovery
    "developer/plans",  # frozen, and excluded by "conf.py" (docs spec §3.1)
```

- [ ] **Step 6: Run the reading-time suite.**

```bash
pixi run --frozen -e geovista pytest tests/docs/test_readingtime_coverage.py -q
```

Expected: `96 passed`. Both plans are now outside the gate's corpus, so this plan's banner no longer counts and `test_every_excluded_tree_exists[developer/plans]` passes.

- [ ] **Step 7: Mark roadmap row 1 in progress, with this pull request.**

In `docs/src/developer/specs/2026-10-06-published-specs-design.md`, replace:

```text
| 1 | Publication, the `§` form, and `tests/test_spec_conventions.py` | not started ({issue}`2566`) |
```

with:

```text
| 1 | Publication, the `§` form, and `tests/test_spec_conventions.py` | in progress ({pull}`PR`) |
```

- [ ] **Step 8: Format, then commit.**

```bash
pixi run --frozen -e geovista ruff format docs/src/conf.py tests/docs/test_readingtime_coverage.py
git add docs/src/conf.py \
  tests/docs/test_readingtime_coverage.py \
  docs/src/developer/specs/2026-10-06-published-specs-design.md
pixi run --frozen -e geovista git commit -F - <<'EOF'
docs: keep the implementation plans out of the build

A plan records what was intended before implementation and is not updated
afterwards, so a published one would be wrong by design (docs spec §3.1).
conf.py now excludes developer/plans/**, and the reading-time gate drops the
tree from its corpus to match, under a test that reads conf.py rather than
trusting the tuple. Roadmap row 1 is in progress.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: every hook passes; a hook that modifies a file fails the commit, so re-add and commit again.

### Task 2: The corpus and its grammar

**Files:**
- Create: `tests/test_spec_conventions.py`
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§3.2 case rule, §3.5 corpus)

**Interfaces:**
- Produces, for every later task: `REPO`, `SPECS`, `SECTION`, `ELLIPSIS`, `PRUNED`,
  `TRACKED`; the patterns `ANCHOR`, `HEADING`, `FENCE`, `SPAN`, `TARGETED`, `LABEL`,
  `SEPARATOR`; `Citation(text: str, slug: str | None)`;
  `Namespace(anchors: frozenset[str], owners: dict[Path, str], signed: re.Pattern[str],
  unsigned: re.Pattern[str])` with `prefixes -> set[str]`;
  `specifications(specs: Path = SPECS) -> list[Path]`;
  `corpus(repo: Path = REPO) -> dict[Path, str]`;
  `read_lines(text) -> Iterator[tuple[int, str]]`;
  `source_lines(path, text) -> Iterator[tuple[int, str]]`;
  `prose(line) -> tuple[str, list[tuple[str, str]]]`;
  `namespace(specs) -> Namespace`; `scan(source, pattern, owner) -> Iterator[Citation]`;
  `where(path, number) -> str`; the fixtures `specs`, `names` and `texts`; and for fixtures,
  `demo(tmp_path, body) -> tuple[Path, Namespace]` and `DEMO`.

- [ ] **Step 1: Create `tests/test_spec_conventions.py` with its head and its tests, and nothing between them.**

`````python
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
`````

- [ ] **Step 2: Run it, and watch it fail.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `6 failed, 11 passed, 4 errors`: `NameError` for `corpus`, `demo`, `prose` and `read_lines`, and fixture errors for `specs`, `names` and `texts`. The eleven that pass are the `PRUNED` shape checks, which need nothing else.

- [ ] **Step 3: Insert the definitions between the `SEPARATOR` pattern and `def test_fenced_blocks_are_skipped`, with two blank lines either side.**

```python
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
```

- [ ] **Step 4: Run it again.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `21 passed`.

- [ ] **Step 5: Bring docs spec into line with the grammar and the corpus (1 of 2).**

Replace exactly this text, which occurs once:

```text
Three details of the form. The word `spec` is matched without regard to case, so a sentence
may open with `Spec §3.2`. Where several sections are cited together the prefix carries
```

with:

```text
Three details of the form. The prefix is matched without regard to case, so a sentence may
open with `Typing spec §3.2`. Where several sections are cited together the prefix carries
```

- [ ] **Step 6: Bring docs spec into line with the grammar and the corpus (2 of 2).**

Replace exactly this text, which occurs once:

```text
The corpus is the specifications and the live repository: source, tests, configuration and
workflows. `developer/plans/` is outside it, for the reason it is outside the build: a plan
is frozen, so a rule it fails is a rule it cannot be edited to satisfy. The one plan in the
repository today holds nine citations written before this document existed, and the honest
treatment of them is the same as the honest treatment of the plan, which is to leave it
saying what it said. A plan's citations are read by a person, who has the specification in
front of them.
```

with:

```text
The corpus is every text file in the repository, the specifications among them, less the
trees that are generated, fetched or frozen. Naming the areas instead would miss whatever
nobody thought to name. `developer/plans/` is outside it, for the reason it is outside the
build: a plan is frozen, so a rule it fails is a rule it cannot be edited to satisfy. The
first plan in the repository holds nine citations written before this document existed,
and the honest treatment of them is the same as the honest treatment of the plan, which is
to leave it saying what it said. A plan's citations are read by a person, who has the
specification in front of them.
```

- [ ] **Step 7: Format, then commit.**

```bash
pixi run --frozen -e geovista ruff format tests/test_spec_conventions.py
git add tests/test_spec_conventions.py \
  docs/src/developer/specs/2026-10-06-published-specs-design.md
pixi run --frozen -e geovista git commit -F - <<'EOF'
tests: read the specifications' citations the way tephpy does

The corpus is every UTF-8 file in the repository, less the trees in PRUNED,
and the grammar follows tephpy's: prefixes derived from the anchors, runs
joined by a comma or a solidus, fences closed only by their own rail, and
inline code blanked, a role written against a span collected. docs spec §3.5
now describes that corpus, and §3.2's example of the case rule names a prefix
geovista has.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: every hook passes; a hook that modifies a file fails the commit, so re-add and commit again.

### Task 3: Pairing and keying

**Files:**
- Modify: `tests/test_spec_conventions.py`
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§3.3)

**Interfaces:**
- Consumes: Task 2's grammar, fixtures, `demo` and `DEMO`.
- Produces: `DECLARED`; `pairing(path, text) -> list[str]`; `keying(path, text) -> list[str]`; `shared(names) -> list[str]`.

- [ ] **Step 1: Append the tests to `tests/test_spec_conventions.py`.**

```python
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
```

- [ ] **Step 2: Run them, and watch them fail.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `8 failed, 21 passed`, every failure a `NameError` for `pairing`, `keying` or `shared`.

- [ ] **Step 3: Insert the definitions above the first test just added, `test_pairing_finds_each_unanchored_heading_and_stranded_anchor`.**

```python
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
```

- [ ] **Step 4: Run them again.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `29 passed`. Both specifications already pair and key every anchor.

- [ ] **Step 5: Record that the assertion has landed.**

Replace exactly this text, which occurs once:

```text
The type coverage specification already satisfies this, thirteen anchors against thirteen
numbered headings. What change 1 of {ref}`§4 <docs-spec-4>` adds is the assertion, so the
next document is governed rather than merely well written.
```

with:

```text
Both specifications satisfy it, and change 1 of {ref}`§4 <docs-spec-4>` added the
assertion, so the next document is governed rather than merely well written.
```

- [ ] **Step 6: Format, then commit.**

```bash
pixi run --frozen -e geovista ruff format tests/test_spec_conventions.py
git add tests/test_spec_conventions.py \
  docs/src/developer/specs/2026-10-06-published-specs-design.md
pixi run --frozen -e geovista git commit -F - <<'EOF'
tests: hold every numbered heading to a keyed anchor

Pairing reads both directions, a heading with no anchor and an anchor with
no heading, and keying checks the number and the prefix, against the one
each specification declares in its banner. A copied specification that kept
its template's prefix is caught too.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: every hook passes; a hook that modifies a file fails the commit, so re-add and commit again.

### Task 4: Resolution, the wrap, and the section sign

**Files:**
- Modify: `tests/test_spec_conventions.py`
- Modify: `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/ci-typing.yml` (seven citations)
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md` (§3.4's quotation of `pyproject.toml`)
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§3.2)

**Interfaces:**
- Consumes: Task 2's grammar.
- Produces: `resolution`, `form`, `wrapped(path, text, names) -> list[str]`, and `paragraphs(lines) -> Iterator[list[tuple[int, str]]]`.

- [ ] **Step 1: Append the tests to `tests/test_spec_conventions.py`.**

```python
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
```

- [ ] **Step 2: Run them, and watch them fail.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `6 failed, 29 passed`, `NameError` for `resolution`, `form` and `wrapped`.

- [ ] **Step 3: Insert the definitions above `test_resolution_finds_each_dangling_and_ownerless_citation`.**

```python
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
```

- [ ] **Step 4: Run them again, and watch the repository fail the form rule.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `1 failed, 34 passed`. `test_every_citation_carries_its_sign` lists exactly seven:

```text
.github/workflows/ci-typing.yml:52: 'typing spec 3.1' has no section sign
.pre-commit-config.yaml:11: 'typing spec 3.1' has no section sign
.pre-commit-config.yaml:58: 'typing spec 3.1' has no section sign
pyproject.toml:87: 'typing spec 3.1' has no section sign
pyproject.toml:96: 'typing spec 3.1' has no section sign
pyproject.toml:108: 'typing spec 3.4' has no section sign
pyproject.toml:119: 'typing spec 3.2' has no section sign
```

- [ ] **Step 5: Sign the seven.**

```bash
sed -i 's/typing spec 3\./typing spec §3./g' \
  pyproject.toml .pre-commit-config.yaml .github/workflows/ci-typing.yml
git diff --stat -- pyproject.toml .pre-commit-config.yaml .github/workflows/ci-typing.yml
```

Expected: `3 files changed, 7 insertions(+), 7 deletions(-)`.

- [ ] **Step 6: Edit `docs/src/developer/specs/2026-10-06-type-coverage-design.md`.**

Replace exactly this text, which occurs once:

```text
# typing spec 3.4 -- two "pyvista" stub defects, both verified against the
```

with:

```text
# typing spec §3.4 -- two "pyvista" stub defects, both verified against the
```

- [ ] **Step 7: Edit `docs/src/developer/specs/2026-10-06-published-specs-design.md`.**

Replace exactly this text, which occurs once:

```text
The section sign is required. All seven of `geovista`'s existing citations were written
without it, as `typing spec 3.1`, and change 1 of {ref}`§4 <docs-spec-4>` adds it to each.
The sign is what separates a citation from an ordinary sentence containing a version
number, and a citation a transform cannot recognise renders as dead text rather than as a
link. Writing the seven correctly now costs seven edits; leaving them costs a silent gap in
whatever is built on top.
```

with:

```text
The section sign is required. All seven of `geovista`'s first citations were written
without it, as `typing spec 3.1`, until change 1 of {ref}`§4 <docs-spec-4>` added it to
each. The sign is what separates a citation from an ordinary sentence containing a version
number, and a citation a transform cannot recognise renders as dead text rather than as a
link. Writing the seven correctly cost seven edits; leaving them would have cost a silent
gap in whatever is built on top.
```

- [ ] **Step 8: Run the module again.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `35 passed`.

- [ ] **Step 9: Format, then commit.**

```bash
pixi run --frozen -e geovista ruff format tests/test_spec_conventions.py
git add tests/test_spec_conventions.py \
  pyproject.toml \
  .pre-commit-config.yaml \
  .github/workflows/ci-typing.yml \
  docs/src/developer/specs/2026-10-06-type-coverage-design.md \
  docs/src/developer/specs/2026-10-06-published-specs-design.md
pixi run --frozen -e geovista git commit -F - <<'EOF'
tests: hold every citation to an anchor and to its section sign

Resolution fails a citation naming no anchor, and a bare section number in a
file that owns no sections. The wrap check catches a run cut by a line break,
whose tail otherwise resolves, silently, to the containing document. And the
form rule found the seven citations written as typing spec 3.1, which now
carry the sign; §3.4 of the type coverage spec quotes pyproject.toml, so its
quotation gains it too.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: every hook passes; a hook that modifies a file fails the commit, so re-add and commit again.

### Task 5: Agreement

**Files:**
- Modify: `tests/test_spec_conventions.py`
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§3.4, §5)

**Interfaces:**
- Consumes: Task 2's grammar.
- Produces: `OPENED`; `agreement(path, text, names) -> list[str]`.

- [ ] **Step 1: Append the tests to `tests/test_spec_conventions.py`.**

```python
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
```

- [ ] **Step 2: Run them, and watch them fail.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `2 failed, 35 passed`, `NameError` for `agreement`.

- [ ] **Step 3: Insert the definitions above `test_agreement_finds_a_role_opening_another_section`.**

```python
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
```

- [ ] **Step 4: Run them again.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `37 passed`. Every section role in the two specifications displays the section it opens, and none is broken across lines.

- [ ] **Step 5: Retire the role counts, which decay (1 of 3).**

Replace exactly this text, which occurs once:

```text
A specification names its own sections constantly — fourteen times in the type coverage
specification, thirty-four in this one — and does it with a hand-written role:
```

with:

```text
A specification names its own sections constantly, and does it with a hand-written role:
```

- [ ] **Step 6: Retire the role counts, which decay (2 of 3).**

Replace exactly this text, which occurs once:

```text
Converting all forty-eight to plain text now was the alternative, and it is rejected
```

with:

```text
Converting them all to plain text now was the alternative, and it is rejected
```

- [ ] **Step 7: Retire the role counts, which decay (3 of 3).**

Replace exactly this text, which occurs once:

```text
  wrong section, which no gate can see. It is tolerated for the existing forty-eight only
  because an assertion closes it and the transform retires it.
```

with:

```text
  wrong section, which no gate can see. It is tolerated for the existing roles only because
  an assertion closes it and the transform retires it.
```

- [ ] **Step 8: Format, then commit.**

```bash
pixi run --frozen -e geovista ruff format tests/test_spec_conventions.py
git add tests/test_spec_conventions.py \
  docs/src/developer/specs/2026-10-06-published-specs-design.md
pixi run --frozen -e geovista git commit -F - <<'EOF'
tests: hold every section role to the section it displays

A {ref} role carries two strings, and the display can name one section while
the target opens another with both well formed. Agreement reads the display
as a citation and requires it to resolve to the target, and reports a role
broken across lines, which a line-based reader would otherwise never check.
The role counts in docs spec §3.4 and §5 go, having already gone stale.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: every hook passes; a hook that modifies a file fails the commit, so re-add and commit again.

### Task 6: Status

**Files:**
- Modify: `tests/test_spec_conventions.py`
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§3.5 item 7, §8 item 4)

**Interfaces:**
- Consumes: Task 2's grammar.
- Produces: `LANDED`, `ROW_STATES`, `ITEM_STATES`, `TERMINAL`, `DATE`, `REFERENCE`, `ITEM`; `sections(text)`; `carried(rest) -> str`; `statuses(text) -> Iterator[tuple[int, str]]`; `status(path, text) -> list[str]`.

- [ ] **Step 1: Append the tests to `tests/test_spec_conventions.py`.**

```python
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
```

- [ ] **Step 2: Run them, and watch them fail.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `3 failed, 37 passed`, `NameError` for `LANDED` and `status`.

- [ ] **Step 3: Insert the definitions above `test_status_finds_an_unknown_state_and_unevidenced_terminals`.**

```python
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
```

- [ ] **Step 4: Run them again.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `40 passed`. Eight statuses are read in docs spec and twelve in the type coverage specification, whose §8 item 4 cites `lazy-loader` by link.

- [ ] **Step 5: Widen the reference rule in docs spec, and record why (1 of 2).**

Replace exactly this text, which occurs once:

```text
7. **Status.** Every roadmap Status cell and every open item opens with a word from the
   vocabulary of {ref}`§3.6 <docs-spec-3-6>`, and every terminal status carries an ISO date
   and at least one `{issue}` or `{pull}` reference. This is the one rule a specification
   breaks by *not* editing it: a row goes stale by the work landing elsewhere, so the check
   has to read the column rather than the diff.
```

with:

```text
7. **Status.** Every roadmap Status cell and every open item opens with a word from the
   vocabulary of {ref}`§3.6 <docs-spec-3-6>`, and every terminal status carries an ISO date
   and at least one reference: an `{issue}` or `{pull}` role, or a link to an issue or pull
   request in another repository. This is the one rule a specification breaks by *not*
   editing it: a row goes stale by the work landing elsewhere, so the check has to read the
   column rather than the diff.
```

- [ ] **Step 6: Widen the reference rule in docs spec, and record why (2 of 2).**

Replace exactly this text, which occurs once:

```text
   the admission the rule in {ref}`§2 <docs-spec-2>` asks for.
```

with:

```text
   the admission the rule in {ref}`§2 <docs-spec-2>` asks for.
4. **Resolved** (TODAY, {pull}`PR`) — **The status rule accepted only this
   repository's roles.** The seventh assertion of {ref}`§3.5 <docs-spec-3-5>` asked a
   terminal status for an `{issue}` or `{pull}` role, and the type coverage specification
   resolves one of its open items against an issue in `lazy-loader`, which neither role
   can name. A link to an issue or pull request in another repository now counts as the
   reference, so a decision settled elsewhere is cited where it was settled.
```

- [ ] **Step 7: Format, then commit.**

```bash
pixi run --frozen -e geovista ruff format tests/test_spec_conventions.py
git add tests/test_spec_conventions.py \
  docs/src/developer/specs/2026-10-06-published-specs-design.md
pixi run --frozen -e geovista git commit -F - <<'EOF'
tests: hold every status to the vocabulary and its evidence

A roadmap Status cell and an open item open with a word from docs spec §3.6,
and a terminal one carries a date and a reference in its parenthetical. A
link to an issue or pull request in another repository now counts as the
reference, since the type coverage spec resolves an item against
lazy-loader; §8 records the change.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: every hook passes; a hook that modifies a file fails the commit, so re-add and commit again.

### Task 7: Publication

**Files:**
- Create: `docs/src/developer/specs/index.rst`
- Create: `docs/src/_static/images/icons/specifications.svg`
- Modify: `docs/src/developer/index.rst` (a card, a toctree entry)
- Modify: `docs/src/_static/color.css` (the title icon)
- Modify: `tests/docs/test_readingtime_coverage.py` (`EXEMPT`)
- Modify: `tests/test_spec_conventions.py`
- Modify: both specifications (front matter, banners, §3.1, §3.5, §6)

**Interfaces:**
- Consumes: `Namespace.owners`, from Task 2.
- Produces: `front_matter(text) -> str`, `toctree(index) -> list[str]`, `namespace_table(index) -> dict[str, str]`.

- [ ] **Step 1: Append the tests to `tests/test_spec_conventions.py`.**

```python
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
```

- [ ] **Step 2: Run them, and watch them fail.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `4 failed, 40 passed`: `NameError` for `front_matter`, and `FileNotFoundError` for `docs/src/developer/specs/index.rst`.

- [ ] **Step 3: Insert the definitions above `test_front_matter_is_read_only_where_a_document_opens`.**

```python
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
```

- [ ] **Step 4: Run them again, and watch the repository fail them.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `3 failed, 41 passed`: both specifications "still carry orphan: true", and the index does not exist.

- [ ] **Step 5: Create `docs/src/developer/specs/index.rst`.**

```rst
.. include:: ../../common.txt

.. _gv-developer-specs:
.. _tippy-gv-developer-specs:

:fa:`compass-drafting` Specifications
=====================================

These are ``geovista``'s design specifications. Each is a living document,
maintained alongside the code it describes rather than archived behind it, so
read it as current. Where a specification and the code disagree, the
specification is what gets corrected, and the disagreement is worth reporting
as a defect in it.

The repository cites them by section. You will meet ``typing spec §3.2`` in
``pyproject.toml`` and ``docs spec §3.1`` in ``conf.py``, and each names a
section on one of the pages below. The prefix names the document, and it is
load-bearing: ``typing spec §3.2`` and ``docs spec §3.2`` are unrelated sections
of different documents.

.. list-table::
    :header-rows: 1
    :widths: 25 75

    * - Citation
      - Document
    * - ``docs spec §…``
      - :doc:`2026-10-06-published-specs-design`
    * - ``typing spec §…``
      - :doc:`2026-10-06-type-coverage-design`

A new specification chooses a prefix unique across this collection, declares it
in its own header banner, and joins the table above and the toctree.

.. note::

    The implementation plans derived from these specifications are tracked in
    the repository under `docs/src/developer/plans
    <https://github.com/bjlittle/geovista/tree/main/docs/src/developer/plans>`__,
    but deliberately not published here. A plan records what was intended
    before implementation and is not updated afterwards.

.. toctree::
    :hidden:

    2026-10-06-published-specs-design
    2026-10-06-type-coverage-design
```

- [ ] **Step 6: Create `docs/src/_static/images/icons/specifications.svg`.**

Font Awesome Free 6.7.2's `compass-drafting`, fetched from `https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.7.2/svgs/solid/compass-drafting.svg`, with the `fill` of the other card icons added and its licence comment kept; `LICENSE.txt` beside it already carries the CC BY 4.0 notice.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="#80d050"><!--! Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free (Icons: CC BY 4.0, Fonts: SIL OFL 1.1, Code: MIT License) Copyright 2024 Fonticons, Inc. --><path d="M352 96c0 14.3-3.1 27.9-8.8 40.2L396 227.4c-23.7 25.3-54.2 44.1-88.5 53.6L256 192c0 0 0 0 0 0s0 0 0 0l-68 117.5c21.5 6.8 44.3 10.5 68.1 10.5c70.7 0 133.8-32.7 174.9-84c11.1-13.8 31.2-16 45-5s16 31.2 5 45C428.1 341.8 347 384 256 384c-35.4 0-69.4-6.4-100.7-18.1L98.7 463.7C94 471.8 87 478.4 78.6 482.6L23.2 510.3c-5 2.5-10.9 2.2-15.6-.7S0 501.5 0 496l0-55.4c0-8.4 2.2-16.7 6.5-24.1l60-103.7C53.7 301.6 41.8 289.3 31.2 276c-11.1-13.8-8.8-33.9 5-45s33.9-8.8 45 5c5.7 7.1 11.8 13.8 18.2 20.1l69.4-119.9c-5.6-12.2-8.8-25.8-8.8-40.2c0-53 43-96 96-96s96 43 96 96zm21 297.9c32.6-12.8 62.5-30.8 88.9-52.9l43.7 75.5c4.2 7.3 6.5 15.6 6.5 24.1l0 55.4c0 5.5-2.9 10.7-7.6 13.6s-10.6 3.2-15.6 .7l-55.4-27.7c-8.4-4.2-15.4-10.8-20.1-18.9L373 393.9zM256 128a32 32 0 1 0 0-64 32 32 0 1 0 0 64z"/></svg>
```

- [ ] **Step 7: Edit `2026-10-06-published-specs-design.md`.**

In `docs/src/developer/specs/2026-10-06-published-specs-design.md`, replace:

```text
---
orphan: true
---

# geovista
```

with:

```text
# geovista
```

- [ ] **Step 8: Edit `2026-10-06-type-coverage-design.md`.**

In `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, replace:

```text
---
orphan: true
---

# geovista
```

with:

```text
# geovista
```

- [ ] **Step 9: Edit `2026-10-06-published-specs-design.md`.**

In `docs/src/developer/specs/2026-10-06-published-specs-design.md`, replace:

```text
- **Published:** not yet. It carries `orphan: true` for the same reason the type coverage
  specification does, and change 1 of {ref}`§4 <docs-spec-4>` takes the marker off both.
  Unlike the identical note there, this one is not left to memory: {issue}`2566` tracks it
```

with:

```text
- **Published:** in the specifications index, since change 1 of {ref}`§4 <docs-spec-4>`
  took `orphan: true` off this document and the type coverage specification together
```

- [ ] **Step 10: Edit `2026-10-06-type-coverage-design.md`.**

In `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, replace:

```text
- **Published:** built, but not yet listed. `myst_parser` registers `.md` of its own
  accord, whatever `source_suffix` in `conf.py` names, so `sphinx` reads and renders this
  file today. No toctree holds it, which warns as `toc.not_included` and fails
  `--fail-on-warning`, so it carries `orphan: true` until the specs tree gains an index.
  That marker comes off with the same change. `tests/docs/test_readingtime_coverage.py`
  globs `*.md` and governs the page regardless, which it passes
```

with:

```text
- **Published:** in the specifications index, since change 1 of
  {ref}`docs spec §4 <docs-spec-4>` took off the `orphan: true` it carried while nothing
  listed it
```

- [ ] **Step 11: Edit `2026-10-06-published-specs-design.md`.**

In `docs/src/developer/specs/2026-10-06-published-specs-design.md`, replace:

```text
├── index.rst       a fifth card, and a toctree entry
```

with:

```text
├── index.rst       a card, and a toctree entry
```

- [ ] **Step 12: Edit `2026-10-06-published-specs-design.md`.**

In `docs/src/developer/specs/2026-10-06-published-specs-design.md`, replace:

```text
Code is skipped, both fenced and inline. That is not a refinement
```

with:

```text
It also holds the publication of {ref}`§3.1 <docs-spec-3-1>` in place: no specification
carries `orphan: true`, the index's toctree lists every specification, and its namespace
table names every declared prefix.

Code is skipped, both fenced and inline. That is not a refinement
```

- [ ] **Step 13: Edit `2026-10-06-published-specs-design.md`.**

In `docs/src/developer/specs/2026-10-06-published-specs-design.md`, replace:

```text
`tests/test_spec_conventions.py` holds {ref}`§3.2 <docs-spec-3-2>` to
{ref}`§3.5 <docs-spec-3-5>`, and the roadmap triggers of {ref}`§4 <docs-spec-4>`.
```

with:

```text
`tests/test_spec_conventions.py` holds {ref}`§3.1 <docs-spec-3-1>` to
{ref}`§3.6 <docs-spec-3-6>`, and the roadmap triggers of {ref}`§4 <docs-spec-4>`.
```

- [ ] **Step 14: Exempt the index from the reading-time banner: it is a landing page.**

In `tests/docs/test_readingtime_coverage.py`, replace:

```text
    "developer/index.rst",  # section landing page
```

with:

```text
    "developer/index.rst",  # section landing page
    "developer/specs/index.rst",  # section landing page: a table and a toctree
```

- [ ] **Step 15: Brand the title icon green, as docs/AGENTS.md requires of a new `:fa:` icon.**

In `docs/src/_static/color.css`, replace:

```text
.fa-comments,
```

with:

```text
.fa-comments,
.fa-compass-drafting,
```

- [ ] **Step 16: Add the card, beside Codecraft in a grid of its own.**

In `docs/src/developer/index.rst`, replace:

```text
.. card:: Codecraft 🚧
    :class-title: custom-title
    :class-body: custom-body
    :link: gv-developer-codecraft
    :link-type: ref
    :img-top: ../_static/images/icons/codecraft.svg
    :class-img-top: dark-light
    :class-card: sd-rounded-3
    :width: 50%
    :margin: 4 4 auto auto

    Maintenance guidelines.
```

with:

```text
.. grid:: 1 1 2 2
    :gutter: 2

    .. grid-item-card:: Specifications
        :class-title: custom-title
        :class-body: custom-body
        :link: gv-developer-specs
        :link-type: ref
        :img-top: ../_static/images/icons/specifications.svg
        :class-img-top: dark-light
        :class-card: sd-rounded-3

        Living design documents.

    .. grid-item-card:: Codecraft 🚧
        :class-title: custom-title
        :class-body: custom-body
        :link: gv-developer-codecraft
        :link-type: ref
        :img-top: ../_static/images/icons/codecraft.svg
        :class-img-top: dark-light
        :class-card: sd-rounded-3

        Maintenance guidelines.
```

- [ ] **Step 17: Add the index to the developer toctree.**

In `docs/src/developer/index.rst`, replace:

```text
    codecraft
```

with:

```text
    codecraft
    specs/index
```

- [ ] **Step 18: Run both suites.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py -q
```

Expected: `142 passed`.

- [ ] **Step 19: Build the documentation, and check what it published.**

```bash
cd docs && pixi run --frozen -e docs sphinx-build -b html --fail-on-warning \
  -D plot_docstring=False -D plot_gallery=False \
  -D plot_inline=False -D plot_tutorial=False \
  -d _build/doctrees src _build/html && cd ..
ls docs/_build/html/developer/specs/*.html
test ! -e docs/_build/html/developer/plans && echo 'plans unpublished'
grep -o 'fa fa-compass-drafting' docs/_build/html/developer/specs/index.html | head -1
```

Expected: `build succeeded` with no warning; three pages, the index and both specifications; `plans unpublished`; and `fa fa-compass-drafting`.

- [ ] **Step 20: Format, then commit.**

```bash
pixi run --frozen -e geovista ruff format tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py
git add tests/test_spec_conventions.py \
  tests/docs/test_readingtime_coverage.py \
  docs/src/developer/specs/index.rst \
  docs/src/_static/images/icons/specifications.svg \
  docs/src/developer/index.rst \
  docs/src/_static/color.css \
  docs/src/developer/specs/2026-10-06-published-specs-design.md \
  docs/src/developer/specs/2026-10-06-type-coverage-design.md
pixi run --frozen -e geovista git commit -F - <<'EOF'
docs: publish the design specifications

developer/specs/index.rst says what the collection is, maps each citation
prefix to its document, and holds the toctree; a Specifications card beside
Codecraft reaches it from the developer guide. Both specifications lose
orphan: true, and the tests now fail if one is ever orphaned again, missing
from the toctree, or absent from the namespace table.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: every hook passes; a hook that modifies a file fails the commit, so re-add and commit again.

### Task 8: The roadmap triggers

**Files:**
- Modify: `tests/test_spec_conventions.py`
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§4, §8 item 5)

**Interfaces:**
- Consumes: `scan`, `prose`, `source_lines` and `Namespace.owners`.
- Produces: `CEILING`, `OUTPUT_GATE`; `outside(texts, names) -> int`; `registered(conf) -> set[str]`.

- [ ] **Step 1: Append the tests to `tests/test_spec_conventions.py`.**

```python
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
    transforms = {name for name in registered(conf) if "citation" in name}
    wiring = [REPO / "pyproject.toml", *(REPO / ".github" / "workflows").glob("*.yml")]
    wired = any(OUTPUT_GATE in path.read_text(encoding="utf-8") for path in wiring)

    assert wired or not transforms, (
        f"{sorted(transforms)} registered without {OUTPUT_GATE}: row 4 of "
        "docs spec §4 is due."
    )
```

- [ ] **Step 2: Run them, and watch them fail.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `3 failed, 44 passed`, `NameError` for `outside` and `registered`.

- [ ] **Step 3: Insert the definitions above `test_registered_reads_every_way_an_extension_is_added`, and add `import ast` as the first of the standard-library imports.**

```python
#: Citations outside the specifications past which rows 2 to 4 of the roadmap
#: activate: five times the seven there were when the threshold was set.
CEILING = 35

#: The entry point by which the rendered-output gate of row 4 is wired in.
OUTPUT_GATE = "check_rendered_citations"


def outside(texts: dict[Path, str], names: Namespace) -> int:
    """Count the citations in every governed file that is not a specification."""
    return sum(
        1
        for path, text in texts.items()
        if path not in names.owners
        for _, line in source_lines(path, text)
        for _ in scan(prose(line)[0], names.signed, None)
    )


def registered(conf: str) -> set[str]:
    """Read every extension a sphinx ``conf.py`` registers, however it does so."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(conf)):
        value = None
        if isinstance(node, ast.Assign | ast.AugAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == "extensions" for t in targets):
                value = node.value
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            owner = node.func.value
            if node.func.attr == "setup_extension" or (
                node.func.attr in {"append", "extend"}
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
```

- [ ] **Step 4: Run them again.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
```

Expected: `47 passed`. Fifteen citations stand outside the specifications: the seven signed in Task 4, one each in `conf.py` and the reading-time gate, and six in this module. No extension registered in `conf.py` names a citation transform.

- [ ] **Step 5: Rewrite rows 2 to 4, and record why (1 of 2).**

Replace exactly this text, which occurs once:

```text
Rows 2 to 5 are candidates rather than scheduled work. `geovista` has seven citations in
one namespace, against `tephpy`'s 1,096 across nineteen, and the machinery those rows
describe is roughly 2,075 lines ({ref}`§9 <docs-spec-9>`). Building it now would be
engineering ahead of the need. Each row therefore names the condition that ends that
objection, and change 1 asserts every condition that can be observed:

- **Row 2** activates when a second citation prefix enters the namespace. One prefix cannot
  be got wrong; two can, and {ref}`§3.2 <docs-spec-3-2>` says what a reader who drops one
  gets. *Asserted:* the test fails when the prefix count exceeds one, naming this row.
- **Row 3** activates with row 2, sharing its grammar. `tephpy` keeps one definition of
  what a citation is for exactly this reason, two definitions being a disagreement that is
  silent in both directions. It activates independently when the corpus outgrows review.
  *Asserted:* the test fails when the citation count exceeds thirty-five, five times
  today's and the point at which reading them all stops being something anyone does.
- **Row 4** activates with row 2, as its converse. The input gate cannot tell whether the
  transform ran at all, and the output gate cannot tell a right target from a wrong one.
  *Asserted:* the test fails when a transform extension is registered in `conf.py` and the
  output gate is not wired into a task, which is the pairing rather than either half.
```

with:

```text
Rows 2 to 5 are candidates rather than scheduled work. When this specification was written
`geovista` had seven citations in one namespace, against `tephpy`'s 1,096 across nineteen,
and the machinery those rows describe is roughly 2,075 lines ({ref}`§9 <docs-spec-9>`).
Building it now would be engineering ahead of the need. Each row therefore names the
condition that ends that objection, and change 1 asserts every condition that can be
observed:

- **Rows 2 to 4** activate together, when the corpus outgrows review. What the transform of
  row 2 buys is a link for every plain-text citation and the retirement of the hand-written
  roles, and both grow with the number of citations. Row 3 shares its grammar, `tephpy`
  keeping one definition of a citation because two would disagree silently in both
  directions, and row 4 checks its output. *Asserted:* the test fails when the citations
  outside the specification collection exceed thirty-five, five times the seven there were
  when this was written and the point at which reading them all stops being something
  anyone does.
- **Row 4** carries a pairing of its own. The input gate cannot tell whether the transform
  ran at all, and the output gate cannot tell a right target from a wrong one. *Asserted:*
  the test fails when a transform extension is registered in `conf.py` and the output gate
  is not wired into a task, which is the pairing rather than either half.
```

- [ ] **Step 6: Rewrite rows 2 to 4, and record why (2 of 2).**

Replace exactly this text, which occurs once:

```text
   reference, so a decision settled elsewhere is cited where it was settled.
```

with:

```text
   reference, so a decision settled elsewhere is cited where it was settled.
5. **Resolved** (TODAY, {pull}`PR`) — **Row 2's trigger fired on its own
   document.** It counted citation prefixes and failed past one, and this specification
   declares the second, `docs spec`, cited from the type coverage specification and from
   the files change 1 touches. The count also measured the wrong thing. A wrong prefix is
   the one mistake the transform cannot catch, since both anchors exist and either
   resolves, while what row 2 buys grows with the number of citations. Rows 2 to 4 now
   share the scale trigger of {ref}`§4 <docs-spec-4>`, decided while planning change 1.
```

- [ ] **Step 7: Format, then commit.**

```bash
pixi run --frozen -e geovista ruff format tests/test_spec_conventions.py
git add tests/test_spec_conventions.py \
  docs/src/developer/specs/2026-10-06-published-specs-design.md
pixi run --frozen -e geovista git commit -F - <<'EOF'
tests: watch the roadmap's triggers

Rows 2 to 4 of docs spec §4 activate together once citations outside the
collection pass thirty-five, and row 4 carries its own pairing: a citation
transform registered in conf.py without the output gate wired in fails. Row
2's old trigger counted prefixes and failed past one, but this specification
declares the second itself; §8 records the change.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: every hook passes; a hook that modifies a file fails the commit, so re-add and commit again.

### Task 9: The living text, the changelog, and the guides

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§4, §8 item 1)
- Modify: `docs/AGENTS.md`, `tests/AGENTS.md`
- Create: `changelog/PR.contributor.rst`

- [ ] **Step 1: Edit `docs/src/developer/specs/2026-10-06-published-specs-design.md`.**

Replace exactly this text, which occurs once:

```text
Change 1 is committed work. It creates `docs/src/developer/specs/index.rst`, adds
`developer/plans/**` to `exclude_patterns` and to the reading-time gate's `EXCLUDED_DIRS`,
gives `docs/src/developer/index.rst` its fifth card and toctree entry, removes `orphan:
true` from both specifications, adds the section sign to the seven existing citations, and
lands the test of {ref}`§3.5 <docs-spec-3-5>`.
```

with:

```text
Change 1 created `docs/src/developer/specs/index.rst`, added `developer/plans/**` to
`exclude_patterns` and to the reading-time gate's `EXCLUDED_DIRS`, gave
`docs/src/developer/index.rst` a card and a toctree entry, removed `orphan: true` from both
specifications, added the section sign to the seven existing citations, and landed the
test of {ref}`§3.5 <docs-spec-3-5>`. Two of this document's rules changed on the way, and
{ref}`§8 <docs-spec-8>` records both.
```

- [ ] **Step 2: Edit `docs/src/developer/specs/2026-10-06-published-specs-design.md`.**

Replace exactly this text, which occurs once:

```text
1. **Open** ({issue}`2566`) — **The `{ref}` agreement assertion assumes the display text is
   the section number.** `` {ref}`§3.1 <typing-spec-3-1>` `` is the only form in use, and a
   role displaying a section's title instead would fail the check while being correct. Both
   specifications write it the one way today. If a second form becomes wanted, the
   assertion widens; it is not widened in advance for a form nobody has asked for.
```

with:

```text
1. **Open** (owned by row 2 of {ref}`§4 <docs-spec-4>`) — **The `{ref}` agreement
   assertion assumes the display text is the section number.**
   `` {ref}`§3.1 <typing-spec-3-1>` `` is the only form in use, and a role displaying a
   section's title instead would fail the check while being correct. Both specifications
   write it the one way today. If a second form becomes wanted, the assertion widens; it is
   not widened in advance for a form nobody has asked for. Row 2 owns it because the
   transform retires the roles, and this assertion with them.
```

- [ ] **Step 3: Update `docs/AGENTS.md` within its 199 lines.**

Replace:

```text
⚠️ **A `.md` page is built the day it lands.** `myst_parser` registers `.md` itself,
whatever `source_suffix` names, so it warns `toc.not_included` and fails the build
unless a toctree holds it, a page `.. include::`s it, or it sets `orphan: true` (#2564).
```

with:

```text
⚠️ **A `.md` page is built the day it lands**: `myst_parser` registers `.md` itself, so it
fails on `toc.not_included` unless a toctree holds it or it is `orphan: true` (#2564). A
spec never is (`tests/test_spec_conventions.py`), and `developer/plans/` is never built.
```

Expected afterwards: `wc -l` still reports 199.

- [ ] **Step 4: Update `tests/AGENTS.md` within its 199 lines.**

Replace:

```text
⚠️ **A source-tree policy gate has nothing to skip on, and must not acquire
one.** `test_readingtime_coverage.py` reads `docs/src` as *text* and
`test_python_support.py` reads `pyproject.toml` beside the workflow matrices, so
neither needs sphinx, a build nor a browser. Both *derive* what they govern from
the tree rather than listing it, so a new page or `pyXYZ` feature is covered the
day it lands and an exemption must be declared with its reason. Guard such a gate
on nothing: a skip retires the rule in silence. The `reading` fixture comes from
`tests/docs/conftest.py`, shared with `test_readingtime.py`.
```

with:

```text
⚠️ **A source-tree policy gate has nothing to skip on, and must not acquire
one.** `test_readingtime_coverage.py`, `test_python_support.py` and
`test_spec_conventions.py` read the tree as *text*, needing no sphinx, build nor
browser, and *derive* what they govern rather than list it, so a new page, `pyXYZ`
feature or spec is covered the day it lands and an exemption carries its reason.
Guard such a gate on nothing: a skip retires the rule in silence. A gate reading
its own source builds its counterexamples, as `SECTION = "\N{SECTION SIGN}"` does.
The `reading` fixture comes from `tests/docs/conftest.py`.
```

Expected afterwards: `wc -l` still reports 199.

- [ ] **Step 5: Write the changelog fragment, `changelog/PR.contributor.rst`, and check it.**

```rst
The design specifications are now published. ``developer/specs/index.rst``
lists them under a new Specifications card in the developer guide, with a table
of the citation prefix each one owns, and both lose the ``orphan: true`` they
carried while nothing listed them. The implementation plans stay in the
repository but out of the build, since a plan records what was intended and is
not updated once the work lands.

``tests/test_spec_conventions.py`` holds them to their conventions: an anchor
keyed to every numbered heading, a section sign in every citation, a ``{ref}``
role that displays the section it opens, and a status that names the work behind
it. Its corpus is every text file in the repository, so a specification, or a
citation of one, is governed from the day it lands. It also watches the roadmap.
The citation machinery ``tephpy`` built becomes due once citations outside the
collection pass thirty-five, and the test fails at that point instead of leaving
the decision to somebody's memory.

The seven ``typing spec 3.1`` citations gained their section sign. Two of the
publication specification's own rules changed on the way: row 2's trigger
counted citation prefixes and fired on the very document that declared it, and
the status rule could not cite an issue in another repository. (:user:`claude`)
```

```bash
pixi run --frozen -e docs python .github/scripts/changelog.py PR "changelog/PR.contributor.rst"
```

Expected: the script's success line.

- [ ] **Step 6: Run both suites, then the non-image suite and the hooks.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py -q
pixi run --frozen -e geovista pytest -m "not image" -q
pixi run --frozen -e geovista pre-commit run --files $(git diff --name-only main)
```

Expected: `145 passed`; the non-image suite as on `main` with no failure (the dry run read 2,505 passed); every hook passing.

- [ ] **Step 7: Commit.**

```bash
git add docs/src/developer/specs/2026-10-06-published-specs-design.md \
  docs/AGENTS.md \
  tests/AGENTS.md \
  changelog/PR.contributor.rst
pixi run --frozen -e geovista git commit -F - <<'EOF'
docs: bring the living text up to date with change 1

docs spec §4 now says what change 1 did rather than what it would do, and §8
item 1 moves from #2566, which this closes, to row 2, whose transform
retires the roles it is about. The guides learn the specs index, the
excluded plans, and a gate that builds its own counterexamples.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: every hook passes; a hook that modifies a file fails the commit, so re-add and commit again.

- [ ] **Step 8: Push, and watch CI.**

```bash
git push
```

Expected: every check green; confirm a red one's `conclusion` through the API before debugging it, since `gh pr checks` shows a cancelled run as a failure.

### Task 10: Landing

- [ ] **Step 1: When Bill approves, mark row 1 landed.**

In `docs/src/developer/specs/2026-10-06-published-specs-design.md`, replace `` in progress ({pull}`PR`) `` in row 1 with `` ✅ landed (TODAY, {pull}`PR`) ``. If `TODAY` is no longer the date that §8 items 4 and 5 carry, re-date those two as well: a status's date is the day the state changed.

- [ ] **Step 2: Run the module, commit, and push.**

```bash
pixi run --frozen -e geovista pytest tests/test_spec_conventions.py -q
git add docs/src/developer/specs/2026-10-06-published-specs-design.md
pixi run --frozen -e geovista git commit -F - <<'EOF'
docs: mark change 1 of the published-specs roadmap landed

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git push
```

Expected: `47 passed`.

- [ ] **Step 3: After the merge, sync `main` and prune the merged branch's tracking ref.**

```bash
git switch main && git pull --ff-only
git remote prune origin --dry-run && git remote prune origin
```

## Done when

- `tests/test_spec_conventions.py` holds the seven assertions of docs spec §3.5, the
  publication checks, the wrap check and the triggers, and never skips.
- The two specifications are listed by `developer/specs/index.rst`, reached from the
  Specifications card, and carry no `orphan: true`.
- `developer/plans/**` is neither built nor governed by the reading-time gate.
- Every citation outside the specifications carries its sign and resolves.
- docs spec §8 records both rule changes with this pull request, and §4's row 1 reads
  `✅ landed`.
- CI is green, and #2566 closes with the merge.

## After the final review

The whole-branch review returned "with fixes": no critical findings, four important and six
minor. Three of the minors were re-graded important by their effect, each being a silent
loss of coverage or an untrue passage, and all seven were fixed in one pass, every code
fix's test watched failing first. The module therefore differs from the code blocks above
where these landed.

| finding | fix | commit |
|---|---|---|
| prose inside a MyST directive fence went unread, and so did the rest of a document after a line opening with inline triple-backtick code | fences nest, a directive's body is read unless the directive holds code, and a backtick fence's info string cannot hold a backtick | `54d8aaea` |
| bulleted open items, items without a bold state, and Status tables under other headings went unread | every top-level list item under "Open items" is read and a missing state reported; every table with a Status column is read | `7f94565e` |
| a code span wrapped across lines hid the roles after it from agreement | a wrapped span in a specification fails, and the two in docs spec were rewrapped | `d9ca5b72` |
| a `venv/`, `htmlcov/` or nested worktree entered the corpus | a directory holding `pyvenv.cfg` or `.git` is left alone, and `htmlcov` is pruned | `b4039197` |
| row 4's watch could read nothing from `conf.py` and pass | annotated assignments and `insert` are read, and `myst_nb` must be found | `9807cafa` |
| docs spec §6 and §8 item 2 described the retired trigger | rewritten | `2b010f6e` |

Three minors are deferred to Bill: a run wrapped inside a blockquote escapes the wrap
check; `docs/AGENTS.md` dropped "a page includes it" as a way out of `toc.not_included`;
and a range written as `typing spec §3.2–§3.4` cites the containing document's §3.4,
which the bare-means-local rule of docs spec §3.2 covers but nothing warns about.

## After the Codex review

The Codex review of the pull request raised two P2 findings, and both were fixed with a test
watched failing first. The first is the blockquote minor above, so two minors remain
deferred.

| finding | fix | commit |
|---|---|---|
| a run wrapped inside a blockquote escaped the wrap check | markdown is joined without its quote markers, while a quote that opens or deepens, or a list item opening with one, still ends the run | `3af73ae4` |
| the roadmap's count blanked every role, so a hand-written section role never counted toward the ceiling | a section role counts as one citation, and docs spec §4 says so | `5e41bf8e` |

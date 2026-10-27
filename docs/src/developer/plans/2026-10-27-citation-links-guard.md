# Citation Links Row 3: The Renumber Guard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fail a pull request that moves or removes a specification section while an untouched line still cites its old number, rewrite those citations with `--fix`, catch the ones that arrive by an older branch with a nightly audit, and hold numbered items and roadmap rows to being appended.

**Architecture:** One script, `.github/scripts/check_renumbering.py`, declaring `CHECK = "spec-renumbering"`. Its core is pure functions over text: read a specification's sections, items and rows; pair the base branch's with the pull request's; classify each as kept, moved or removed; find the citations of the moved and removed ones; rewrite the moved. A thin git layer feeds them: the base branch's specifications and the lines a pull request changed in pull-request mode, and each citing line's last commit in the nightly audit. It reads citations with `docs/src/_ext/geovista_citations.py`. `ci-spec-status.yml` runs it on pull requests and each night.

**Tech Stack:** Python 3.13+, git, `difflib`, pytest, pixi, GitHub Actions.

**Spec:** `docs/src/developer/specs/2026-10-26-citation-links-design.md`, `citation spec §4.5`, `§4.6`, `§6` and row 3 of `§9`.

## Global Constraints

- Sections pair by title first, compared case and punctuation aside, then the leftovers by the similarity of their text (`difflib.SequenceMatcher(...).ratio() >= 0.6`, best pair first). A section paired under its own anchor is kept, under another is moved, and unpaired is removed (`citation spec §4.5`).
- An untouched citation of a moved or removed section fails. A line the pull request changed passes. `--fix` rewrites only citations of moved sections; a removed one is left for the author.
- Frozen are every numbered item opening with a bold title, keyed by that title (the second bold run after a status), and every row of a table headed `#`, `Scope`, `Status`, keyed by its scope. A moved or removed one fails, except a row `N` replaced by rows `Na`, `Nb` and so on, which is a split (`citation spec §4.6`).
- The corpus is the conventions test's, `geovista_citations.corpus()`, less the plans; `CHANGELOG.rst` and changelog fragments are in it.
- Exit codes follow `check_status_references.py`: 0 clean, 1 findings followed by the breadcrumb, 2 when the check could not finish.
- Load the grammar by path, reusing a copy already registered (`tests/AGENTS.md`).
- Commit through `pixi run --frozen -e geovista git commit`.

## Review Focus

1. **A renamed and moved section.** It pairs by text, not title; Task 2 tests it, and Task 7 tries one on the real repository.
2. **A deletion in the middle.** The section after it moves, and the deleted one's old number now names its successor; both must be reported (Task 2, Task 4).
3. **Roles until row 4.** Until the collapse, most citations in the specifications are `{ref}` roles; the guard reads them, and `--fix` rewrites their display and target together (Task 4).
4. **The base branch in CI.** A shallow checkout has no base to compare; the job fetches it (Task 6).
5. **A first audit on the real history.** The audit compares every citation with history it has never been run on; Task 7 runs it and reads every finding.

---

### Task 1: Commit This Plan

- [ ] **Step 1:** Commit this file alone, push, open the draft pull request (`agentic`, `type: testing`, `type: documentation`), and pause for review.

### Task 2: Sections, and How They Pair

**Files:**
- Create: `.github/scripts/check_renumbering.py`
- Create: `tests/test_renumbering.py`

**Interfaces:**
- Produces: `Section(anchor: str, title: str, body: str)`; `sections(text: str) -> dict[str, Section]`, keyed by anchor, reading only lines `read_lines` keeps; `Fate(kind: Literal["kept", "moved", "removed"], anchor: str | None, title: str)`, where `anchor` is the new anchor of a moved section; `pair(base: dict[str, Section], head: dict[str, Section]) -> dict[str, Fate]`, keyed by base anchor.

- [ ] **Step 1: Write the failing tests**, each on two small specifications under the `demo spec` prefix, with the section sign built: an unchanged spec keeps every section; a renamed section is kept; a section inserted before two others moves both; a section deleted from the middle is removed and the one after it moves; a section inserted while another is renamed pairs each correctly; a section rewritten past recognition and renamed is removed; titles differing only in case or punctuation pair.
- [ ] **Step 2:** Run `pixi run --frozen -e test pytest -p no:pretty tests/test_renumbering.py`. Expected: fails, no script.
- [ ] **Step 3:** Write the script's header, docstring, `CHECK`, the grammar loader, `Section`, `sections`, `Fate` and `pair`.
- [ ] **Step 4:** Run the tests. Expected: pass.
- [ ] **Step 5:** Commit `"tests: pair a specification's sections across a change"`.

### Task 3: Items and Rows Are Appended

**Interfaces:**
- Produces: `Numbered(section: str, number: str, key: str)`; `numbered_items(text: str) -> dict[tuple[str, str], Numbered]` (items, keyed by section anchor and number); `roadmap_rows(text: str) -> dict[str, Numbered]` (rows, keyed by `#`); `frozen(base_text: str, head_text: str) -> list[str]`, one message per item or row moved or removed.

- [ ] **Step 1: Write the failing tests:** an item appended passes; an item inserted mid-list fails, naming the items it moved; an item whose title is edited passes; a status changed from `**Open**` to `**Resolved**` passes; a numbered list without bold titles is ignored; a row appended passes; a row inserted mid-table fails; a row `6` replaced by `6a`, `6b` and `6c` passes; a row removed fails; a wrapped bold title is read whole.
- [ ] **Step 2:** Run them. Expected: fail.
- [ ] **Step 3:** Implement, pairing items and rows with the pairing of Task 2 applied to their keys.
- [ ] **Step 4:** Run them. Expected: pass.
- [ ] **Step 5:** Commit `"tests: hold numbered items and roadmap rows to being appended"`.

### Task 4: Citations of What Moved, and the Fix

**Interfaces:**
- Consumes: `pair`, `Fate`, the grammar's `scan`, `prose`, `section_role`, `source_lines`, `namespace`.
- Produces: `Finding(path: Path, line: int, cited: str, fate: Fate, old: str)`; `stale(texts: dict[Path, str], fates: dict[str, Fate], names, changed: dict[Path, set[int]]) -> list[Finding]`; `rewrite(text: str, path: Path, fates: dict[str, Fate], names, lines: set[int]) -> str`; `describe(finding: Finding, root: Path) -> str`, in the form `src/geovista/crs.py:42: crs spec §3.3 was "Domains", which is now §3.4`, or `... which was removed; §3.5 is now "Caps"`.

- [ ] **Step 1: Write the failing tests:** an untouched plain citation of a moved section is found; one on a changed line is not; a bare citation inside the moved section's own specification is found; a role's citation is found; a citation of a kept section is not; a citation of a removed section is found and described with what its number names now; `rewrite` turns `demo spec §2` into `demo spec §3` on the named lines only, turns a role's display and target together, leaves a removed section's citation alone, and leaves a run's other citations as they were.
- [ ] **Step 2:** Run them. Expected: fail.
- [ ] **Step 3:** Implement. A citation's position comes from `Citation.start` and `end`; a role is rewritten by its own pattern, ``{ref}`...§N <slug>` `` and its reStructuredText form.
- [ ] **Step 4:** Run them. Expected: pass.
- [ ] **Step 5:** Commit `"tests: find and fix the citations of a moved section"`.

### Task 5: Git, the Command Line and the Audit

**Interfaces:**
- Produces: `changed_lines(repo: Path, base: str) -> dict[Path, set[int]]` from `git diff --unified=0 <merge-base>...HEAD`; `at(repo: Path, ref: str, path: Path) -> str | None`; `audit(repo: Path, texts, names) -> list[Finding]`, comparing each citing line's specification at the commit that last wrote the line (`git blame --porcelain`) with the specification now; `main(argv: list[str] | None = None) -> int`, with `--base REF` (default `origin/main`), `--fix` and `--audit`.

- [ ] **Step 1: Write the failing tests** against small git repositories the tests build with `git init` and commits: a renumber with an untouched citation fails with the finding and the breadcrumb, exit 1; the same with the citation updated passes, exit 0; `--fix` rewrites the citation, and a `CHANGELOG.rst` citing it, and nothing else; a renumbered item fails; `--audit` finds a citation added on a branch made before a renumber and merged after it, and passes once fixed; a base that does not exist exits 2.
- [ ] **Step 2:** Run them. Expected: fail.
- [ ] **Step 3:** Implement. Git runs in the repository given, with `--no-pager`; a git failure is exit 2, never a finding.
- [ ] **Step 4:** Run them. Expected: pass.
- [ ] **Step 5:** Commit `"tests: run the renumber guard on a pull request, and audit main each night"`.

### Task 6: Wiring

**Files:**
- Modify: `pyproject.toml` (a `check-spec-renumbering` task in the `test` feature, taking `fix` or `audit`)
- Modify: `.github/workflows/ci-spec-status.yml`
- Modify: `docs/src/developer/checks.rst`, `tests/test_status_references.py`

- [ ] **Step 1:** A `renumbering` job runs on pull requests, checking out with `fetch-depth: 0` and running the task against `origin/${{ github.base_ref }}`. The nightly job runs the audit beside the drift check and opens a `bot` issue, "chore: specification citation drift", on a finding, as the drift check does. The paths filter adds the script.
- [ ] **Step 2:** Extend `test_the_workflow_runs_when_anything_the_script_reads_changes` to the guard: every file it loads is in the filter. Run it red first.
- [ ] **Step 3:** The checks page gets a row under "A CI Job Failed" and a section, Specification Renumbering, with its rule, why, what enforces it, what to do (`pixi run -e test check-spec-renumbering fix`), and no exception. Run `tests/test_repository_checks.py`. Expected: pass.
- [ ] **Step 4:** Commit `"ci: run the renumber guard, and its audit each night"`.

### Task 7: The Real Repository

- [ ] **Step 1:** Run the task against `origin/main` on this branch. Expected: clean.
- [ ] **Step 2:** Run `--audit` on the whole repository. Expected: clean, or each finding read and fixed in the source.
- [ ] **Step 3:** In a scratch worktree, insert a section into a real specification, run the guard, confirm it names the moved citations, run `fix`, and confirm the conventions test passes. Then move and rename one section, and confirm it pairs. Remove the worktree.
- [ ] **Step 4:** Run `pixi run --frozen -e test tests-unit "not image"`. Expected: no failures.

### Task 8: Record and Land

- [ ] **Step 1:** Write `changelog/<PR>.internal.rst`, crediting `:user:`claude``, and check it with `.github/scripts/changelog.py`.
- [ ] **Step 2:** Final review on Opus; fix Critical and Important findings red first; record the review at the end of this plan; raise an `agentic` issue for anything deferred.
- [ ] **Step 3: The landed row, last.** Row 3 of `citation spec §9` becomes `✅ landed (<date>, {pull}`<PR>`)`. Run `check-spec-status <PR>`, commit, push, and mark the pull request ready.

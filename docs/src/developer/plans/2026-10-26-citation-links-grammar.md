# Citation Links Row 1: One Grammar — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the citation grammar out of `tests/test_spec_conventions.py` into `docs/src/_ext/geovista_citations.py`, with no change in behaviour, so that the transform (row 2) and the renumber guard (row 3) can import the same definition.

**Architecture:** A plain module in `docs/src/_ext`, with no Sphinx `setup()`, like `reading.py`. The conventions test loads it by path, registering it in `sys.modules` before executing it, and binds the moved names at module level, so its rules, and `.github/scripts/check_status_references.py`, which loads the test module, keep working unchanged. The grammar's own tests move to `tests/docs/test_geovista_citations.py`.

**Tech Stack:** Python 3.13+, pytest (import mode `importlib`), pixi.

**Spec:** `docs/src/developer/specs/2026-10-26-citation-links-design.md`, `citation spec §4.1`, roadmap row 1 of `citation spec §9`.

## Global Constraints

- The ceiling: on `main` at the time of writing, 68 citations sit outside the specifications against `CEILING = 70`. The grammar module and its tests are outside the collection, so **this PR may add at most two citations net**. Write examples in docstrings inside inline code (double backticks), which the grammar skips. Run the count in Task 3, Step 4.
- No literal section sign in a test or the module: build it, as `SECTION = "\N{SECTION SIGN}"` does (`tests/AGENTS.md`).
- Every new Python file opens with the copyright header and `from __future__ import annotations` (`AGENTS.md`).
- Behaviour is unchanged: no regex, constant or function body changes as it moves.
- Commit through `pixi run --frozen -e geovista git commit`, so the pre-commit hook runs.

## Review Focus

1. **A dataclass in a path-loaded module.** `Citation` and `Namespace` are dataclasses under `from __future__ import annotations`, so loading without registering in `sys.modules` first raises `AttributeError` at class creation. Task 3's loader registers first; Task 2's fixture does too.
2. **The status script.** `.github/scripts/check_status_references.py` loads `tests/test_spec_conventions.py` by path and reads `specifications` from it. Task 3, Step 5 runs it.
3. **The default roots.** `REPO` and `SPECS` move into the module and are computed from its own path (`parents[3]`). A wrong index governs the wrong tree; the existing vacuity tests (`test_the_corpus_holds_a_member_of_every_area_it_governs`, `test_the_collection_is_not_empty`) fail on it, and must still run against the real repository.
4. **Two loads, two classes.** If the module is loaded under two names, its dataclasses exist twice. Both loaders use the one name, `geovista_citations`.
5. **The ceiling.** See Global Constraints.

---

### Task 1: Commit This Plan

**Files:**
- Create: `docs/src/developer/plans/2026-10-26-citation-links-grammar.md`

- [ ] **Step 1: Commit the plan alone, push, and open the draft pull request** (labels `agentic`, `type: testing`), then pause for review.

```bash
git add docs/src/developer/plans/2026-10-26-citation-links-grammar.md
pixi run --frozen -e geovista git commit -m "docs: plan row 1 of the citation links design"
```

### Task 2: The Grammar Module and Its Tests

**Files:**
- Create: `docs/src/_ext/geovista_citations.py`
- Create: `tests/docs/test_geovista_citations.py`
- Modify: `tests/test_spec_conventions.py` (remove the ten grammar tests at lines 434-526)

**Interfaces:**
- Produces, in `geovista_citations`, verbatim from `tests/test_spec_conventions.py`:
  - constants `REPO` (`Path(__file__).parents[3]`), `SPECS`, `SECTION`, `ELLIPSIS`, `PRUNED`, `TRACKED`, `ANCHOR`, `HEADING`, `FENCE`, `CODE_DIRECTIVES`, `SPAN`, `TARGETED`, `LABEL`, `SEPARATOR`
  - dataclasses `Citation(text: str, slug: str | None)` and `Namespace(anchors, owners, signed, unsigned)` with its `prefixes` property
  - `specifications(specs: Path = SPECS) -> list[Path]`, `entered(name: str) -> bool`, `foreign(path: Path) -> bool`, `corpus(repo: Path = REPO) -> dict[Path, str]`, `holds_code(info: str) -> bool`, `read_lines(text: str) -> Iterator[tuple[int, str]]`, `source_lines(path: Path, text: str) -> Iterator[tuple[int, str]]`, `prose(line: str) -> tuple[str, list[tuple[str, str]]]`, `alternation(prefixes: Iterable[str]) -> str`, `namespace(specs: Iterable[Path]) -> Namespace`, `scan(source: str, pattern: re.Pattern[str], owner: str | None) -> Iterator[Citation]`, `section_role(kind: str, body: str, names: Namespace) -> tuple[str, str] | None` (now at line 1208)

- [ ] **Step 1: Move the ten grammar tests** (`test_fenced_blocks_are_skipped` through `test_corpus_reads_the_tree_it_is_given`) into `tests/docs/test_geovista_citations.py` unchanged, apart from reaching the grammar through a module-scoped fixture:

```python
@pytest.fixture(scope="module")
def citations() -> ModuleType:
    """Load the grammar by path, registered first, as a build would import it."""
```

Each test takes `citations` and calls `citations.read_lines(...)` and so on. The file defines its own `demo(tmp_path, body, citations)` and `DEMO`, as the conventions test does, and builds `SECTION` and `ELLIPSIS` rather than writing them. Add one test the move needs:

```python
def test_the_default_roots_are_this_repository(citations):
    assert citations.SPECS == citations.REPO / "docs" / "src" / "developer" / "specs"
    assert (citations.REPO / "pyproject.toml").is_file()
```

- [ ] **Step 2: Run the new file and see it fail**

Run: `pixi run --frozen -e test pytest -p no:pretty tests/docs/test_geovista_citations.py`
Expected: every test errors, as `docs/src/_ext/geovista_citations.py` does not exist.

- [ ] **Step 3: Create `docs/src/_ext/geovista_citations.py`** with the names of the Interfaces block, cut from `tests/test_spec_conventions.py` with their comments and docstrings. Its module docstring says what it is and who imports it (the conventions test today; the transform and guard of `citation spec §4.2` and `§4.5` later), citing at most one section outside inline code.

- [ ] **Step 4: Run the new file and see it pass**

Run: `pixi run --frozen -e test pytest -p no:pretty tests/docs/test_geovista_citations.py`
Expected: 11 passed.

Task 3 makes the conventions test import the module, so commit the two together at the end of Task 3.

### Task 3: The Conventions Test Imports the Grammar

**Files:**
- Modify: `tests/test_spec_conventions.py`

**Interfaces:**
- Consumes: everything Task 2 produces.
- Produces: the same module-level names as today, so `check_status_references.py` and every rule in the file run unchanged.

- [ ] **Step 1: Replace the moved definitions with a load and bindings.** Delete the cut code, add

```python
#: The citation grammar, shared with the documentation build (citation spec §4.1).
GRAMMAR = REPO / "docs" / "src" / "_ext" / "geovista_citations.py"
```

and a `_load(path: Path) -> ModuleType` that registers the module as `geovista_citations` in `sys.modules` before `exec_module`, as `tests/docs/conftest.py` loads `reading.py`. Bind each moved name the rest of the file uses (`Citation = citations.Citation`, and so on), keeping `REPO` and `SPECS` as the test's own. `section_role` moves, so `agreement` and `outside` use the bound name. The comment above is the PR's one new citation outside the specifications.

- [ ] **Step 2: Run the conventions test and the grammar tests**

Run: `pixi run --frozen -e test pytest -p no:pretty tests/test_spec_conventions.py tests/docs/test_geovista_citations.py tests/test_repository_checks.py tests/test_status_references.py`
Expected: all pass, and the conventions test collects exactly ten fewer tests than it did before Task 2 (count with `--collect-only -q` before you start).

- [ ] **Step 3: Run the module's sibling gates**

Run: `pixi run --frozen -e test pytest -p no:pretty tests/docs/test_ext_parallel.py tests/docs/test_readingtime_coverage.py`
Expected: pass. `geovista_citations.py` defines no `setup`, so the parallel-safety check does not take it for an extension.

- [ ] **Step 4: Check the ceiling count**

Run, with the loader of `tests/test_spec_conventions.py`:

```bash
pixi run --frozen -e test python -c "import importlib.util,sys; s=importlib.util.spec_from_file_location('c','tests/test_spec_conventions.py'); m=importlib.util.module_from_spec(s); sys.modules['c']=m; s.loader.exec_module(m); print(m.outside(m.corpus(), m.namespace(m.specifications())))"
```

Expected: at most `main`'s count plus two, and at most 70.

- [ ] **Step 5: Run the status script, which loads the test module**

Run: `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>`
Expected: `all hold`.

- [ ] **Step 6: Commit**

```bash
git add docs/src/_ext/geovista_citations.py tests/docs/test_geovista_citations.py tests/test_spec_conventions.py
pixi run --frozen -e geovista git commit -m "tests: move the citation grammar into docs/src/_ext"
```

### Task 4: Record and Land

**Files:**
- Create: `changelog/<PR>.internal.rst`
- Modify: `docs/src/developer/checks.rst` (the Specification Conventions section's **What enforces it**)
- Modify: `docs/src/developer/specs/2026-10-26-citation-links-design.md` (row 1 of `citation spec §9`)

- [ ] **Step 1: Say where the grammar lives.** In `checks.rst`, add to **What enforces it** of Specification Conventions that the grammar the test reads is `docs/src/_ext/geovista_citations.py`, shared with the documentation build. Write the fragment, crediting `:user:`claude``, without a section sign, so it adds no citation:

Run: `pixi run -e docs python .github/scripts/changelog.py <PR> "changelog/<PR>.internal.rst"`
Expected: the fragment passes.

- [ ] **Step 2: Run the full unit suite**

Run: `pixi run --frozen -e test tests-unit "not image"`
Expected: no failures.

- [ ] **Step 3: Commit, push, and request review.**

- [ ] **Step 4: The landed row, last.** After review, set row 1 of `citation spec §9` to `✅ landed (<date>, {pull}`<PR>`)`, run `check-spec-status <PR>`, commit and push, so that approving and merging are one step. Correct the date if the merge slips a day.

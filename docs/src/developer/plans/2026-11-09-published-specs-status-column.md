# Status in the Specifications Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 7 of docs spec §4. The namespace table of the specifications index gains a Status column, which the build writes from each specification's roadmap, as docs spec §3.8 and §2 decision 8 set out.

**Architecture:** A pure function, `geovista_citations.roadmap_status`, sums the Status cells of a roadmap into one cell, beside the ledger's `summary`. A new extension, `geovista_status`, finds the index's table by its header, reads the roadmap of the document each row links with `geovista_citations.rows`, and appends the cell, recording each specification as a dependency of the index so that an incremental build re-reads it. The conventions test holds every specification's cell to an independent count of its roadmap, and a build test holds the rendered column.

**Tech Stack:** Sphinx transforms on the docutils doctree, MyST, pytest.

**Spec:** `docs/src/developer/specs/2026-10-06-published-specs-design.md` (`docs spec §…`): §2 decision 8, §3.8, §4 row 7, §6 and §10.

## Global Constraints

- The cell reads `📋 not started` when no row has landed or begun, `🚧 N of M rows` when a row has landed or begun and another has not landed, and `✅ complete` when every row has landed (docs spec §3.8).
- The count sets the rows that have landed against every row that is not a 💡 candidate, so a row in progress has not landed yet. While any candidate remains, the cell adds ` · 💡 K`, as in `✅ complete · 💡 1`. A specification whose every row is a candidate reads `💡 K`, and one without a roadmap reads `—` (§3.8).
- Open items stay out of the cell (§3.8).
- The build writes the column; the Citation and Document columns stay hand-written, and a new specification makes no edit for its status (§3.7, §3.8).
- A module in `docs/src/_ext` writes no emoji literally, and spells each by name, as `"\N{CLIPBOARD} not started"`, since it sits in the corpus it serves (#2787).
- No new public name. `mypy` runs strict over the whole package, and warnings are errors under pytest. Docstrings are NumPy style, and `.. versionchanged::` is not used.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: documentation` and `agentic`, and closes no issue.
- A test file named as evidence in §10 cites its decision, as "Holds docs spec §2 decision 8." in a test's docstring (ledger spec §3.4).

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-09 that docs spec §3.8 fixes how row 7 behaves (workflow rule 2.7). The calls are mine.

1. **The grammar owns the states and the sum.** `geovista_citations` gains `LANDED`, `IN_PROGRESS`, `NOT_STARTED` and `CANDIDATE`, spelled by name as in `tests/test_spec_conventions.py`, the tuple `ROADMAP_STATES` of the four, and `roadmap_status(statuses: Iterable[str]) -> str`. A Status cell opening with none of the four counts as a row that has not landed, and the conventions test already refuses one. `state_of` reads each state with or without its variation selector.
2. **A new extension, not the ledger's.** `docs/src/_ext/geovista_status.py` holds a `SpecStatus(SphinxTransform)`, registered in `conf.py` beside `geovista_ledger`, since docs spec owns the index and ledger spec owns the summary line.
3. **The table is found by its header.** The transform takes any table whose header reads `Citation`, `Document`, appends a `Status` header cell, a colspec of width 30 after the two that `:widths: 35 65` gives, and to each body row the cell of the document its Document cell links by `:doc:`, resolved with `sphinx.util.docname_join` and `env.doc2path`. A row that links no document gets `—`.
4. **The index re-reads when a roadmap changes.** The transform calls `env.note_dependency` for each specification it reads, and for itself and `geovista_citations`, as `LedgerSummary` does.
5. **The index says what the column is.** A sentence under the table names the three cells and the candidates, and cites docs spec §3.8.
6. **Evidence.** `tests/docs/test_geovista_citations.py` gains the tests of `roadmap_status`, `tests/docs/test_geovista_status.py` is new, with a build of a small project and the column of the real index, and `tests/test_spec_conventions.py` gains `test_every_status_sums_its_roadmap`. Each cites §2 decision 8, and §10 names the three files.
7. **One fragment, `2917.documentation.rst`.** The branch is `docs/spec-status-column-build`, and the plan is the first commit of draft pull request {pull}`2917` (workflow rule 2.3), which marks row 7 in progress (workflow rule 2.4).

## Review Focus

1. **One row, in progress.** A roadmap whose only row has begun reads `🚧 0 of 1 rows`. `test_roadmap_status_counts_a_row_in_progress_as_not_landed` (Task 1).
2. **A variation selector.** `✅️ landed`, with VS16, counts as landed. `test_roadmap_status_reads_a_variation_selector` (Task 1).
3. **A row that links no specification.** Its cell reads `—`, and the build warns of nothing. `test_a_row_linking_no_document_reads_a_dash` (Task 2).
4. **An incremental build.** A roadmap changed after a build moves the index's cell on the next build. `test_an_incremental_build_reads_a_changed_roadmap` (Task 2).
5. **Every real specification.** Each cell of the built index agrees with its specification's roadmap, and none reads `—`. `test_the_index_shows_each_specification_status` (Task 3).

---

Measured on 2026-11-09 at `b5d372d6` (`main` after {pull}`2914`): the index's table has twelve rows, each linking one specification by `:doc:`, and every specification has a roadmap. Today's cells, by a count of each roadmap: checks `✅ complete · 💡 1`, crs `🚧 1 of 14 rows · 💡 1`, globe `🚧 2 of 6 rows · 💡 4`, heights `🚧 1 of 5 rows`, scene `🚧 2 of 3 rows`, docs `🚧 5 of 6 rows · 💡 1`, which row 7 makes `✅ complete · 💡 1`, citation, ledger and items `✅ complete`, positions `🚧 6 of 7 rows`, typing `🚧 9 of 10 rows · 💡 4`, and zlevel `✅ complete`.

### Task 1: The Sum of a Roadmap

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py` (the states, `ROADMAP_STATES`, `roadmap_status`)
- Modify: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Produces: `geovista_citations.roadmap_status(statuses: Iterable[str]) -> str`, and `LANDED`, `IN_PROGRESS`, `NOT_STARTED`, `CANDIDATE`, `ROADMAP_STATES`, which Tasks 2 and 3 use.

- [ ] **Step 1: Write the tests**

Each builds its cells from the module's own states, as `f"{citations.LANDED} (2026-11-09, ...)"`.

- `test_roadmap_status_sums_each_state(statuses, expected)`, with ids `not-started` (two not started: `📋 not started`), `in-progress` (one landed, one not started: `🚧 1 of 2 rows`), `complete` (two landed: `✅ complete`), `complete-with-candidates` (one landed, one candidate: `✅ complete · 💡 1`), `in-progress-with-candidates` (two landed, four not started, four candidates: `🚧 2 of 6 rows · 💡 4`), `only-candidates` (two candidates: `💡 2`) and `no-roadmap` (none: `—`). It holds docs spec §2 decision 8.
- `test_roadmap_status_counts_a_row_in_progress_as_not_landed()`: one row in progress: `🚧 0 of 1 rows`.
- `test_roadmap_status_reads_a_variation_selector()`: `"\N{WHITE HEAVY CHECK MARK}\N{VARIATION SELECTOR-16} landed"`: `✅ complete`.
- `test_roadmap_status_counts_an_unknown_state_as_not_landed()`: one landed and one `"landed"` without its emoji: `🚧 1 of 2 rows`.

- [ ] **Step 2: Run the tests to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_citations.py -k roadmap_status`
Expected: FAIL, as `roadmap_status` does not exist.

- [ ] **Step 3: Implement Call 1**

`roadmap_status` reads each cell with `state_of(cell.strip(), ROADMAP_STATES)`, counts the landed, in progress and candidate rows, and words the cell as the Global Constraints say. Its docstring cites docs spec §3.8.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_citations.py tests/test_spec_conventions.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/src/_ext/geovista_citations.py tests/docs/test_geovista_citations.py
pixi run --frozen -e geovista git commit -m "docs: sum a roadmap into one status, as docs spec §3.8 words it"
```

### Task 2: The Column in a Build

**Files:**
- Create: `docs/src/_ext/geovista_status.py`
- Modify: `docs/src/conf.py` (the extension, beside `geovista_ledger`)
- Modify: `docs/src/developer/specs/index.rst` (the sentence under the table)
- Create: `tests/docs/test_geovista_status.py`

**Interfaces:**
- Consumes: `geovista_citations.rows(text) -> list[Row]` and `roadmap_status`, from Task 1.
- Produces: `geovista_status.SpecStatus`, and `geovista_status.setup(app) -> dict[str, object]`, `parallel_read_safe` and `parallel_write_safe`.

- [ ] **Step 1: Write the tests**

Each builds a project in `tmp_path`, as `test_a_build_writes_the_summary_under_the_table` in `tests/docs/test_geovista_ledger.py` does, with a `conf.py` naming `myst_parser` and `geovista_status`, two specifications, `one.md` with a roadmap of one landed row and one candidate and `two.md` with one landed and one not started, and an `index.rst` whose `list-table` has the header `Citation`, `Document`, a row for each by `:doc:`, and a row whose Document cell is plain text.

- `test_a_build_writes_each_status_into_the_index(tmp_path)`: the build warns of nothing; the index's table has a third header cell `Status`, and the cells `✅ complete · 💡 1`, `🚧 1 of 2 rows` and `—`, in that order. It holds docs spec §2 decision 8.
- `test_a_row_linking_no_document_reads_a_dash(tmp_path)`: the plain row's cell is `—`.
- `test_an_incremental_build_reads_a_changed_roadmap(tmp_path)`: after a build, `two.md`'s not started row lands, and a second build into the same directory shows `✅ complete` for it.
- `test_a_table_of_another_header_is_left_alone(tmp_path)`: a table headed `Name`, `Document` gains no column.
- `test_the_extension_builds_its_emoji_by_name()`: `geovista_status.py` holds no character above U+2000 but `·`, as the ledger's test does.

- [ ] **Step 2: Run the tests to watch them fail**

Run: `pixi run --frozen -e docs pytest -q -p no:randomly tests/docs/test_geovista_status.py`
Expected: FAIL, as `geovista_status` does not exist.

- [ ] **Step 3: Implement Calls 2 to 5**

`SpecStatus` follows Call 3, at the priority of `LedgerSummary`, and Call 4. `setup` registers it, with `env_version` 1. `conf.py` lists `geovista_status` after `geovista_ledger`. Under the index's table, humanized: "The Status column sums each specification's roadmap: 📋 not started, 🚧 how many of its rows have landed, or ✅ complete, with any 💡 candidates counted beside it. The build writes it, as docs spec §3.8 sets out." Each docstring cites docs spec §3.8.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e docs pytest -q -p no:randomly tests/docs/test_geovista_status.py tests/docs/test_geovista_ledger.py tests/docs/test_geovista_citations.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/src/_ext/geovista_status.py docs/src/conf.py docs/src/developer/specs/index.rst tests/docs/test_geovista_status.py
pixi run --frozen -e geovista git commit -m "docs: write each specification's status into the index"
```

### Task 3: Every Specification's Status

**Files:**
- Modify: `tests/test_spec_conventions.py`
- Modify: `tests/docs/test_geovista_status.py`

**Interfaces:**
- Consumes: `roadmap_status` and `rows`, from Task 1; the built index, from Task 2.

- [ ] **Step 1: Write the tests**

- `test_every_status_sums_its_roadmap(spec)`, over every specification: its cell, `citations.roadmap_status` of `citations.rows`, equals one counted from `roadmap_rows` and this module's own `LANDED`, `IN_PROGRESS` and `CANDIDATE`, and is not `—`. It holds docs spec §2 decision 8.
- `test_the_index_shows_each_specification_status(html_root)`, in `tests/docs/test_geovista_status.py`: `developer/specs/index.html` has a Status header, and each row's cell equals `roadmap_status` of the specification its row links. It holds docs spec §2 decision 8.

- [ ] **Step 2: Run them**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k status_sums` then the strict `sphinx-build` of `AGENTS.md` with `-E`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_status.py -k index_shows`.
Expected: PASS, as Tasks 1 and 2 are in place; break `roadmap_status`'s count to see the first fail, and drop `geovista_status` from `conf.py` to see the second fail.

- [ ] **Step 3: Commit**

```bash
git add tests/test_spec_conventions.py tests/docs/test_geovista_status.py
pixi run --frozen -e geovista git commit -m "test: hold each specification's status to its roadmap"
```

### Task 4: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§4 row 7, §6, §10)
- Modify: this plan's Follow-ups, before merge
- Create: `changelog/2917.documentation.rst`

- [ ] **Step 1: Watch each clause fail when it regresses**

Mutate one at a time, run the named tests, see them fail, and revert:
- `roadmap_status` counts candidates as rows: the `complete-with-candidates` and `in-progress-with-candidates` cases, and `test_every_status_sums_its_roadmap`;
- it counts a row in progress as landed: `test_roadmap_status_counts_a_row_in_progress_as_not_landed`;
- it drops the candidates' suffix: the `-with-candidates` cases;
- `geovista_status` is not registered: `test_the_index_shows_each_specification_status`;
- it records no dependency on a specification: `test_an_incremental_build_reads_a_changed_roadmap`.

- [ ] **Step 2: Mark the decision and the row, and add the fragment**

§6 gains, humanized: `tests/docs/test_geovista_status.py` holds the column of §3.8 in a build, and the conventions test holds each specification's status to its roadmap. In §10, §2 decision 8 becomes ``✅ verified (<DATE>, {pull}`2917`)`` with evidence `tests/docs/test_geovista_citations.py`, `tests/docs/test_geovista_status.py`, `tests/test_spec_conventions.py`, and row 7 of §4 becomes ``✅ landed (<DATE>, {pull}`2917`)``, `<DATE>` the day of this commit, corrected if the merge slips (workflow rule 2.4). `changelog/2917.documentation.rst`, humanized, says that the specifications index shows each specification's status, worked out from its roadmap, and names the row as `row 7 of docs spec §4` on one line.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py 2917 "changelog/2917.documentation.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py tests/test_renumbering.py tests/test_verification_report.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status 2917` and `pixi run --frozen -e test check-spec-renumbering`.
Expected: all pass.

- [ ] **Step 3: Commit, then run the whole suite and the docs build on that commit**

```bash
git add changelog/2917.documentation.rst
pixi run --frozen -e geovista git commit -am "docs: mark docs spec row 7 landed, verify §2 decision 8, and add the fragment"
```

Run: the strict `sphinx-build` with `-E`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/`, then `CI=true GALLIUM_DRIVER=llvmpipe pixi run --frozen -e test-py313 tests-unit` and the same with `-e test-py314`.
Expected: the build succeeds, the index shows every status, and the suites PASS with no new skips.

- [ ] **Step 4: Push, and mark the pull request ready**

Push, confirm it with `git ls-remote` (workflow rule 4.6), check `gh pr view 2917 --json closingIssuesReferences` lists none, and mark the pull request ready once the final review's fixes have landed.

## Follow-ups

None yet.

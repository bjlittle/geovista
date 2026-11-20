# Roadmap Row Order Diagrams: The Build Draws Them Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of diagram spec §9: the build draws each specification's diagram, with its key, directly under its roadmap table, and the open work of every roadmap on the specifications index, each row linking to itself, with the developer guide's account (diagram spec §4.4 to §4.6, §4.8).

**Architecture:** A new extension, `docs/src/_ext/geovista_roadmap_diagrams.py`, reads the graph once a build starts, through the grammar row 1 gave it, as `geovista_citation_xrefs` and `geovista_ledger` read their registries. A transform places a specification's diagram and key after its roadmap table, and a directive, `roadmap-open-work`, written once in the index, draws the open work. Each draws the Mermaid text of `geovista_citations.diagram` into a `sphinxcontrib.mermaid` node, so the page renders it as the Codecraft and Packaging pages' diagrams render.

**Tech Stack:** Python, Sphinx, docutils, `sphinxcontrib-mermaid`, MyST, reStructuredText, pytest.

**Spec:** `docs/src/developer/specs/2026-11-18-row-order-diagrams-design.md` (`diagram spec §…`): §2 decisions 1 to 4, 7 and 9, §4.4 to §4.6, §4.8, §6 and §9 row 2.

## Global Constraints

- **Nothing generated is committed, and no specification writes anything** for its diagram (diagram spec §2 decision 2, §4.4): the transform finds the roadmap table by its header, as `geovista_citation_xrefs` names its rows.
- **A diagram sits directly under its roadmap table**, its key directly under it (§2 decision 3, §4.2); a roadmap no ordering touches draws neither (§2 decision 9).
- **Each row links to its row's anchor** on its specification's page, the id `geovista_citation_xrefs` gives it (§4.6).
- **An extension sits in the corpus it serves**, so it spells each emoji by name, never writes one (`tests/docs/test_geovista_status.py`'s guard, #2787).
- **`setup()` returns `parallel_read_safe` and `parallel_write_safe`, and calls `env.note_dependency`** for what a page reads that sphinx does not see (`docs/AGENTS.md`); declared safety proves nothing, so a `--jobs 2` build is compared with a serial one.
- Warnings are errors. Every pixi run is `pixi run --frozen -e geovista …`; commit through the environment's `pre-commit`. The fragment credits ``(:user:`claude`)`` (workflow rule 4.9); the pull request carries `type: documentation` and `agentic`, and names {issue}`2997` without closing it.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-19 that diagram spec §9 row 2 is bounded (workflow rule 2.7). These calls are mine; the first three are **for review**.

1. **A transform for specifications, a directive for the index. For review.** §4.4 has no specification write anything, so a transform places its diagram, found by the roadmap header. The index is no specification, and §4.5 gives it a section of prose saying what ready means; a `.. roadmap-open-work::` directive in that section places its diagram where the prose is, read by anyone editing the page, where a transform would need a marker to find.
2. **The open work is `geovista_citations.open_work`. For review.** Row 1 left §4.5's rows to row 2: every row that has an ordering and has not landed, then each landed row one of them waits on or lands with, all in reading order. It joins the grammar beside `roadmap_view`, so the report could draw it later.
3. **Row 2 verifies decisions 1, 2, 3, 4, 7 and 9. For review.** Each is about the pages this row draws. Decision 6 says every diagram carries a key, and decision 8 the report's diagrams, so both wait for row 3.
4. **Every specification is a dependency of every page drawing a diagram.** A row's colour and ready read every roadmap, so an edit to any specification re-reads each specification page and the index on an incremental build; at seventeen specifications that is cheap, and anything narrower would draw stale colours.
5. **The extension reads `geovista_roadmap_specs` (`developer/specs`) and `geovista_roadmap_index` (`developer/specs/index`) from the configuration,** as `geovista_status` reads its index, so a test builds a small project of its own.
6. **The index's section is "Open Work",** after the paragraph on the Status column; the section on ordering roadmap rows gains a paragraph on the diagrams.
7. **One fragment, `3001.documentation.rst`.** The branch is `docs/diagram-spec-row2`; this plan is the first commit of draft pull request {pull}`3001`, which marks the row in progress (workflow rules 2.3, 2.4).

## Review Focus

1. **A specification with two roadmap tables**, as one moved between sections would have: the diagram, drawn once, goes under the last, so it follows every row it draws. `test_a_diagram_follows_the_last_roadmap_table` (Task 2).
2. **A table quoting a roadmap's header on a page that is no specification**, as the index's ordering section does in a code block, or any other page: nothing is drawn. `test_a_page_that_is_no_specification_draws_nothing` (Task 2).
3. **A row of another specification that its own page has not yet named**, as on a first build read in parallel: its link is a relative URI to that page and the anchor, built from names, not from the other page's doctree. `test_a_link_names_the_page_and_the_row_without_reading_it` (Task 2).
4. **An incremental build after another specification's row lands**: the first page's small row turns, and its ready rows follow. `test_an_incremental_build_redraws_after_another_specification_changes` (Task 2).
5. **A `--jobs 2` build** draws every page as a serial build does. `test_a_parallel_build_draws_as_a_serial_build` (Task 2).

---

### Task 1: The Open Work

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py` (beside `roadmap_view`)
- Test: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Produces: `open_work(edges: Sequence[Edge], statuses: Mapping[str, str]) -> list[str]` (anchors, in reading order).

- [ ] **Step 1: Write the failing tests**

- `test_open_work_draws_each_ordered_row_not_landed`: demo row 1 `✅ landed`, 2 `📋 not started` `· 🔗 after row 1`, 3 `🚧 in progress` `· 🔗 after row 2`, 4 `📋 not started` with no ordering → `[row 1, row 2, row 3]`: row 4 has no ordering, and row 1 is landed but row 2 waits on it.
- `test_open_work_draws_a_landed_row_landing_with_one_open`: a `with` between a landed row and one not started → both.
- `test_open_work_leaves_out_landed_history`: two landed rows, one after the other → `[]`.
- `test_open_work_reads_every_specification_in_reading_order`: rows of demo, then of other.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_citations.py -k open_work`
Expected: FAIL, no attribute `open_work`.

- [ ] **Step 2: Write `open_work`** per diagram spec §4.5: the anchors of `statuses` (reading order) that are in some edge and not `✅ landed`, then those landed that are an edge's `first` whose `second` is open, or either end of a `with` whose other end is open. Run: the same. Expected: PASS.
- [ ] **Step 3: Commit** — `git commit -m "feat: read the open work of every roadmap (diagram spec §4.5)"`

### Task 2: The Extension

**Files:**
- Create: `docs/src/_ext/geovista_roadmap_diagrams.py`
- Modify: `docs/src/conf.py` (`extensions`, after `geovista_status`)
- Test: `tests/docs/test_geovista_roadmap_diagrams.py`

**Interfaces:**
- Consumes: Task 1, and row 1's `ordering_edges`, `row_statuses`, `row_labels`, `roadmap_view`, `diagram`, `diagram_key`, `namespace`, `specifications`, `roadmap_header`.
- Produces: the transform `RoadmapDiagram` (priority 420, after `ItemTargets` names rows at 300 and citations link at 400); the directive `roadmap-open-work`; config values `geovista_roadmap_specs` and `geovista_roadmap_index`; each diagram and its key inside a `nodes.container` with class `roadmap-diagram`, holding two `sphinxcontrib.mermaid.mermaid` nodes, the diagram's then the key's.

- [ ] **Step 1: Write the failing tests**, over a project of `index.rst` (holding `.. roadmap-open-work::`) and `developer/specs/` with a `demo` and an `other` specification and a third with no ordering, built as `tests/docs/test_geovista_status.py` builds, with `myst_parser`, `sphinxcontrib.mermaid`, `geovista_citation_xrefs` and this extension:

- `test_a_specification_draws_its_diagram_under_its_roadmap_table`: in the doctree, the roadmap table's next sibling is the `roadmap-diagram` container, its first node's code `== diagram(rows, …)` for that roadmap and its second `== diagram_key()`. Holds diagram spec §2 decision 3 and diagram spec §2 decision 2.
- `test_a_roadmap_no_ordering_touches_draws_nothing`: the third specification's page has no `roadmap-diagram`. Holds diagram spec §2 decision 9.
- `test_a_diagram_draws_other_rows_small_in_their_own_colour`: demo's diagram classes other's row `…_small` in its state's class. Holds diagram spec §2 decision 9.
- `test_a_diagram_follows_the_last_roadmap_table` (Review Focus 1).
- `test_a_page_that_is_no_specification_draws_nothing` (Review Focus 2): a page holding a table headed `#`, `Scope`, `Status`.
- `test_a_link_names_the_page_and_the_row_without_reading_it` (Review Focus 3): demo's `click` for other's row is `"<relative uri of other>#other-spec-2-row-1"`, and the built page has an element of that id. Holds diagram spec §2 decision 7.
- `test_the_index_draws_the_open_work`: the directive's container holds `diagram(open_work(…), …)` and the key, with links. Holds diagram spec §2 decision 1 and diagram spec §2 decision 4.
- `test_an_incremental_build_redraws_after_another_specification_changes` (Review Focus 4).
- `test_a_parallel_build_draws_as_a_serial_build` (Review Focus 5): `parallel=2` and serial builds give the same `<pre class="mermaid">` text on every page.
- `test_the_extension_builds_its_emoji_by_name`.
- `test_the_real_build_draws_every_ordered_specification` (on `html_root`): each specification `roadmap_view` gives rows has one `roadmap-diagram` whose `pre` follows its roadmap table, each other has none, and the index has one.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_roadmap_diagrams.py`
Expected: FAIL, no such extension.

- [ ] **Step 2: Write the extension.** On `builder-inited`, read the specifications under `geovista_roadmap_specs`: their namespace, texts, edges, statuses and labels, and each docname's prefix. `RoadmapDiagram.apply` returns unless the docname is a specification with rows to draw; otherwise it notes this file, the grammar and every specification as dependencies, finds the last table whose header `roadmap_header` reads, and inserts the container after it. Links are `builder.get_relative_uri(docname, target) + "#" + anchor`. The directive notes the same dependencies and returns the container for the open work. `setup()` adds both config values (`"env"`), the transform and the directive, and returns `parallel_read_safe` and `parallel_write_safe`. Add the extension to `conf.py`'s `extensions`.

Run: the command of Step 1, then the strict incremental `sphinx-build`. Expected: PASS, no warning.

- [ ] **Step 3: Commit** — `git commit -m "feat: draw each roadmap's diagram, and the open work, in the build (diagram spec §4.4 to §4.6)"`

### Task 3: The Pages

**Files:**
- Modify: `docs/src/developer/specs/index.rst` (a section "Open Work" holding the directive; the ordering section's paragraph)
- Modify: `docs/AGENTS.md` (the rule in a line, under 200 lines)

- [ ] **Step 1: Write the pages**, humanized (workflow rule 3.1): "Open Work" says the diagram holds every ordered row not landed and the landed rows they wait on, that green is ready to start and what ready means (diagram spec §4.3), and that each box links to its row, then `.. roadmap-open-work::`. The ordering section adds that each specification draws its rows and orderings under its roadmap table, with a key, and that the arrows are the relations of its table. `docs/AGENTS.md`'s ordering line adds: the build draws the diagrams, under each roadmap and on the index, from the graph the checks read; nothing is written for them.

Run: the strict incremental `sphinx-build`, `tests/docs/test_geovista_roadmap_diagrams.py`, `tests/test_spec_conventions.py` and `check-spec-renumbering`. Expected: PASS, no warning.

- [ ] **Step 2: Show it** (workflow rule 3.5): screenshot a specification's roadmap and the index's Open Work, light and dark, with the headless browser of `tests/docs`, and attach them to the pull request.
- [ ] **Step 3: Commit** — `git commit -m "docs: show the open work on the specifications index, and say where the diagrams are"`

### Task 4: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-18-row-order-diagrams-design.md` (§9 row 2, §11 decisions 1, 2, 3, 4, 7, 9)
- Create: `changelog/3001.documentation.rst`

- [ ] **Step 1: Watch each clause fail when it regresses** (workflow rule 2.6): the diagram placed before the table, or after the first of two; drawn on a page that is no specification, or for a roadmap no ordering touches; another's row greyed; a link without its anchor, or absolute; the index drawing every ordered row, or none; the key left out; a dependency left unnoted, so the incremental build keeps a stale colour.
- [ ] **Step 2: Mark and settle.** Row 2 becomes ``✅ landed (<DATE>, {pull}`3001`)``, and §2 decisions 1, 2, 3, 4, 7 and 9 ``✅ verified (<DATE>, {pull}`3001`)`` with evidence `tests/docs/test_geovista_roadmap_diagrams.py`, which cites each. The fragment, humanized, names row 2 of diagram spec §9.

Run: the changelog check, the spec suites, `check-spec-status --pull 3001` with a token, `check-spec-renumbering`, the strict `sphinx-build` with `-E`, `tests/docs -m "not browser"` under `xvfb-run -a`, and `tests-unit` on `test-py314`.
Expected: PASS.

- [ ] **Step 3: Push**, confirm with `git ls-remote` (workflow rule 4.6), and ask {user}`bjlittle` to mark the pull request ready once the final review's fixes have landed.

## Follow-ups

None yet.

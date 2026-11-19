# Roadmap Row Order Diagrams: One Reading of the Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of diagram spec §9: the reading of the graph of order spec §4.5 moved from the conventions test into `geovista_citations`, with the test and the report reading through it, and the text of a diagram, its key and ready (diagram spec §4.1 to §4.3).

**Architecture:** The edges, statuses, landed dates, strongly connected parts and rows landing together move into the shared grammar unchanged, and `tests/test_spec_conventions.py` binds them by name, as it binds the rest of the grammar, keeping its rules. The grammar gains `ready_rows`, `row_labels`, `roadmap_view`, `diagram` and `diagram_key`, which write Mermaid `flowchart` text; nothing yet places a diagram on a page or in the report (rows 2 and 3).

**Tech Stack:** Python, pytest, Mermaid flowchart text.

**Spec:** `docs/src/developer/specs/2026-11-18-row-order-diagrams-design.md` (`diagram spec §…`): §2 decisions 2, 5, 6, 7 and 9, §4.1 to §4.4, §6 and §9 row 1; and order spec §4.5 and §4.6 for the reading it moves.

## Global Constraints

- **The reading moves, the rules stay** (diagram spec §4.1): `order_cycles`, `order_candidates`, `order_statuses`, `orderings_twice`, `ordering_form` and `ordering_in_prose` stay in the conventions test, and their tests stay where they are, unchanged.
- **Row 1 changes no page and no report** (diagram spec §9): the report reads the graph through the grammar, and its output is byte for byte what it was.
- Mermaid's `click … href` gives a link at its default `strict` level (diagram spec §3.4); no Mermaid configuration changes.
- Nothing type-checks `docs/src/_ext` (`docs/AGENTS.md`), so the grammar's new functions carry full annotations and NumPy docstrings anyway, as the module's do.
- No new public name in `geovista`. Warnings are errors. Every pixi run is `pixi run --frozen -e geovista …`; commit through the environment's `pre-commit`. A fixture builds its section signs and emoji, never writes them. The fragment credits ``(:user:`claude`)``; the pull request carries `type: documentation` and `agentic`, and names {issue}`2997` without closing it.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-18 that diagram spec §9 row 1 is bounded (workflow rule 2.7). These calls are mine, and the first two are **for review**.

1. **`roadmap_view` comes with row 1. For review.** It picks the rows of diagram spec §4.4, which rows 2 and 3 both draw, and neither lands after the other, so it belongs to the row they both come after. This widens row 1 by one function beyond §4.1 to §4.3 (workflow rule 1.2). The open work of §4.5 is drawn by row 2 alone, and stays there.
2. **Row 1 verifies decision 5 alone. For review.** Decision 5 (colour and ready) holds entirely in the text this row writes. Decisions 2, 6, 7 and 9 each say where a diagram is drawn or what it carries there, which rows 2 and 3 do, so they stay `⏳ pending`.
3. **Names.** The test's `named` becomes the grammar's `row_citation`, since the grammar's `listed` already parses numbered lists; the prose-joining `listed` stays in the test. `_pulls` becomes `pulls`. `ROW_STATES` is the grammar's `ROADMAP_STATES`.
4. **The key is a diagram of its own.** `diagram_key()` writes a small Mermaid `flowchart` with one sample box per colour and one sample arrow per relation, labelled in a Scope cell's words, so it is drawn by the same renderer, beneath each diagram, wherever rows 2 and 3 place one.
5. **The values.** The encoding of diagram spec §4.2 is pinned in Task 3 as exact text, so the tests hold it.
6. **One fragment, `2999.internal.rst`**, since no reader sees anything until row 2. The branch is `docs/diagram-spec-row1`; this plan is the first commit of draft pull request {pull}`2999`, which marks the row in progress (workflow rules 2.3, 2.4).

## Review Focus

1. **A scope holding a quote, a `#` or a role**, as ``The work of {issue}`7`, with "quotes"``: the label is escaped, so the diagram still parses. `test_row_labels_escapes_what_mermaid_reads` (Task 2).
2. **A roadmap whose rows carry no ordering** draws nothing, and one with an ordering draws every row, ordered or not. `test_roadmap_view_*` (Task 3).
3. **A row landing with a row in progress** is not ready, nor is one landing with a candidate. `test_ready_rows_*` (Task 2).
4. **An ordering naming a row that does not exist** (the resolution rule's fault) draws no arrow to a box that is not declared. `test_diagram_draws_no_edge_to_an_undeclared_row` (Task 3).
5. **A row numbered with a letter**, as `6a`, keeps its number in its label and an id Mermaid reads. `test_diagram_reads_a_lettered_row` (Task 3).

---

### Task 1: The Reading Moves Into the Grammar

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py` (after `ordering`)
- Modify: `tests/test_spec_conventions.py` (bind the names; delete the moved definitions and their tests)
- Modify: `.github/scripts/verification_report.py` (read the graph through `grammar`)
- Test: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Produces, in `geovista_citations`, unchanged in behaviour from the test's: `BARE_ROW`, `ordering_target(said, row, rows, owner, names) -> tuple[str | None, str | None]`, `Edge(NamedTuple: kind, first, second, path, row, clause)`, `ordering_edges(texts, names, *, releases=False) -> list[Edge]`, `PULL_ROLE`, `PULL_LINK`, `pulls(status) -> set[tuple[str, int]]`, `DATE`, `landed_on(status) -> tuple[date | None, set[tuple[str, int]]] | None`, `row_statuses(texts, names) -> dict[str, str]`, `strongly_connected(graph) -> dict[str, int]`, `no_later_than(edges) -> dict[str, list[str]]`, `landing_together(edges) -> dict[str, list[str]]`, `row_citation(anchor) -> str`.

- [ ] **Step 1: Move the tests first.** Into `tests/docs/test_geovista_citations.py`, with a helper `roadmaps(tmp_path, citations, mine, theirs=(("Theirs", NOT_STARTED),))` writing the demo and other specifications as the conventions test's `ordered` does, move `test_ordering_edges_reads_each_relation_as_an_edge`, `test_ordering_edges_records_where_each_is_written`, `test_landed_on_reads_a_date_and_its_pull_requests`, `test_row_statuses_reads_every_roadmap_by_anchor` and `test_landing_together_groups_the_rows_a_loop_forces_into_one_pr`, each calling `citations.<name>`, and add `test_row_citation_names_a_row_by_its_anchor`: `row_citation("crs-spec-10-row-6a") == "row 6a of crs spec §10"`.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_citations.py -k "ordering_edges or landed_on or row_statuses or landing_together or row_citation"`
Expected: FAIL, the grammar has no such attribute.

- [ ] **Step 2: Move the definitions** into the grammar, delete them from the conventions test, and bind each there by name (`ordering_edges = citations.ordering_edges`, `named = citations.row_citation`, …), so its rules and their tests are untouched. In the report, read `grammar.row_statuses`, `grammar.ordering_edges`, `grammar.landing_together`, `grammar.row_citation`, `grammar.ROADMAP_STATES`, `grammar.LANDED` and `grammar.IN_PROGRESS`, keeping `conventions.own_row` and `conventions.listed`.

Run: the command of Step 1, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_verification_report.py tests/docs/test_geovista_citations.py`, and `pixi run --frozen -e geovista python .github/scripts/verification_report.py` diffed against its output on `main`.
Expected: PASS, and no difference in the report.

- [ ] **Step 3: Commit** — `git commit -m "refactor: read the graph of orderings in the shared grammar (diagram spec §4.1)"`

### Task 2: Labels and Ready

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py`
- Test: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Consumes: Task 1.
- Produces: `ready_rows(edges: Sequence[Edge], statuses: Mapping[str, str]) -> set[str]`, `row_labels(texts: Mapping[Path, str], names: Namespace, width: int = 40) -> dict[str, str]` (anchor → escaped label).

- [ ] **Step 1: Write the failing tests**

- `test_ready_rows_finds_a_row_whose_rows_before_it_have_landed`: rows 1 `✅ landed`, 2 `📋 not started` `· 🔗 after row 1`, 3 `📋 not started` `· 🔗 after row 2` → `{row 2}`.
- `test_ready_rows_reads_with_or_after_and_before`: a `with or after` from a landed row, and a `before` written on a landed row, each leave the waiting row ready; from a row not landed, neither does.
- `test_ready_rows_reads_the_rows_landing_together`: row 2 `with` row 1 of other, which is `after` an other row not landed → row 2 not ready (diagram spec §3.4: heights row 5).
- `test_ready_rows_holds_back_a_row_landing_with_one_in_progress`, and `..._with_a_candidate` (diagram spec §4.3) → empty.
- `test_ready_rows_needs_a_row_not_started`: a row in progress, landed or a candidate is never ready, and a not started row with no ordering is ready.
- `test_row_labels_opens_with_the_row_and_its_scope`: `"2: Tiers on the globe"`, the ordering clauses dropped.
- `test_row_labels_cuts_a_long_scope`: a scope of 60 characters → 40 characters of it, then `…`.
- `test_row_labels_escapes_what_mermaid_reads`: ``The work of {issue}`7`, with "quotes"`` → `1: The work of #35;7, with #quot;quotes#quot;`; backticks, `*` and `_` emphasis read as their text.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_citations.py -k "ready_rows or row_labels"`
Expected: FAIL.

- [ ] **Step 2: Write them.** `ready_rows` reads diagram spec §4.3: a row is ready when `📋 not started`, no row of its group (itself and `landing_together(edges)[row]`) is `💡 candidate` or `🚧 in progress`, and every `after` or `with or after` edge into the group from outside it starts at a landed row. `row_labels` writes `f"{row.row}: {scope}"`, the scope being `split_scope(row.scope)[0]` with roles read as their target (an issue or pull request as `#N`), code and emphasis read as text, whitespace collapsed, cut at `width` with `…`, then `#` escaped as `#35;` and `"` as `#quot;`.

Run: the command of Step 1. Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "feat: read which rows are ready, and label each row (diagram spec §4.2, §4.3)"`

### Task 3: The Diagram, Its Key and a Roadmap's View

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py`
- Test: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: `roadmap_view(owner: str, edges: Sequence[Edge], statuses: Mapping[str, str]) -> tuple[list[str], set[str]]` (the rows to draw in reading order, and those drawn small); `diagram(rows: Sequence[str], edges: Sequence[Edge], statuses: Mapping[str, str], labels: Mapping[str, str], *, small: Collection[str] = (), links: Mapping[str, str] | None = None) -> str`; `diagram_key() -> str`.

The text, pinned (diagram spec §4.2):

```text
flowchart LR
  subgraph demo_spec["demo spec"]
    demo_spec_2_row_1["1: One"]
    …
  end
  demo_spec_2_row_1 --> demo_spec_2_row_2            (after)
  demo_spec_2_row_3 <==> other_spec_2_row_1          (with)
  other_spec_2_row_1 -.-> demo_spec_2_row_5          (with or after)
  classDef landed fill:#eeeeee,stroke:#bbbbbb,color:#666666
  classDef progress fill:#ffe8a3,stroke:#c99a00,color:#000000
  classDef todo fill:#ffffff,stroke:#555555,color:#000000
  classDef candidate fill:#ffffff,stroke:#999999,stroke-dasharray:4 3,color:#555555
  classDef ready fill:#d9f2d9,stroke:#2e8b2e,stroke-width:3px,color:#000000
  (each again as <name>_small, with font-size:11px)
  class demo_spec_2_row_1 landed
  click demo_spec_2_row_1 href "<link>"
```

A box's id is its anchor with `-` read as `_`; a specification's box opens in the order its first row is drawn; every class sets its fill and its text colour, so each reads on the dark theme's background as on the light one.

- [ ] **Step 1: Write the failing tests**

- `test_diagram_draws_each_state_in_its_colour`: one row of each state → each `class … <name>` line, and a ready row `ready`, not `todo`.
- `test_diagram_draws_each_relation_as_its_arrow`: `after` and `before` both `-->` from the row landing first, `with` `<==>`, `with or after` `-.->`.
- `test_diagram_boxes_each_specification`: `subgraph demo_spec["demo spec"]` … `end`, then `other_spec`.
- `test_diagram_draws_a_small_row_in_its_own_colour`: a row in `small`, landed → `landed_small`; ready → `ready_small` (diagram spec §2 decision 9).
- `test_diagram_links_each_row_given_a_link`, and none without `links`.
- `test_diagram_draws_no_edge_to_an_undeclared_row`: an edge whose row is not in `rows` is not drawn.
- `test_diagram_reads_a_lettered_row`: row `6a` → id `demo_spec_2_row_6a`, label `6a: …`.
- `test_every_class_sets_its_fill_and_text_colour`: each `classDef` carries `fill:` and `color:`.
- `test_diagram_key_names_each_relation_and_state`: the key holds `after`, `with`, `with or after`, `before`, `landed`, `in progress`, `not started`, `candidate` and `ready`, one `-->`, `<==>` and `-.->`, and the same `classDef` lines as a diagram.
- `test_roadmap_view_draws_every_row_and_the_rows_it_orders_against`: demo rows 1 to 3, row 2 `after` row 1, row 3 unordered, row 1 `with` row 1 of other → all three demo rows in order, then other's row 1, which alone is small.
- `test_roadmap_view_draws_nothing_without_an_ordering`: → `([], set())`.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_citations.py -k "diagram or roadmap_view"`
Expected: FAIL.

- [ ] **Step 2: Write `roadmap_view`, `diagram` and `diagram_key`** to the pinned text. `diagram` computes `ready_rows(edges, statuses)` over every edge it is given, and draws only the rows in `rows`.

Run: the command of Step 1, then a parse of a diagram of today's specifications by `mmdc`, as the spike rendered it (diagram spec §3.4). Expected: PASS, and `mmdc` exits 0.

- [ ] **Step 3: Commit** — `git commit -m "feat: write a diagram of the order between rows, and its key (diagram spec §4.2, §4.4)"`

### Task 4: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-18-row-order-diagrams-design.md` (§9 row 1, §11 decision 5)
- Create: `changelog/2999.internal.rst`

- [ ] **Step 1: Watch each clause fail when it regresses** (workflow rule 2.6): ready reading one row's edges and not its group's; ready letting a row in progress, or a candidate, through its group; a state drawn in another's colour; a small row greyed; `with or after` drawn solid; `before` drawn from the wrong row; a label unescaped; `roadmap_view` drawing a roadmap with no ordering; the conventions test's rules each still failing their fixtures through the moved reading.
- [ ] **Step 2: Mark and settle.** Row 1 becomes ``✅ landed (<DATE>, {pull}`2999`)``, and §2 decision 5 ``✅ verified (<DATE>, {pull}`2999`)`` with evidence `tests/docs/test_geovista_citations.py`, whose `ready_rows` and colour tests cite "diagram spec §2 decision 5". The fragment, humanized, names row 1 of diagram spec §9.

Run: the changelog check, the spec suites, `check-spec-status --pull 2999` with a token, `check-spec-renumbering`, the strict incremental `sphinx-build`, `tests/docs -m "not browser"` under `xvfb-run -a`, and `tests-unit` on `test-py314`.
Expected: PASS.

- [ ] **Step 3: Push**, confirm with `git ls-remote` (workflow rule 4.6), and ask {user}`bjlittle` to mark the pull request ready once the final review's fixes have landed.

## Follow-ups

None yet.

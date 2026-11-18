# Roadmap Row Order: the Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of order spec §9 with row 8 of items spec §8: every ordering of every roadmap read into one graph that refuses a cycle, a `not started` row waiting on a `candidate`, and a status the order contradicts (items 5 to 7 of order spec §4.5), with `landing_together` folded in, the verification report listing the rows that land with a row in progress and the items they owe (order spec §4.6), the guard's advice naming rewording ({issue}`2991`), and the pages that say so.

**Architecture:** The conventions test gains one reading of the corpus as edges, `ordering_edges`, which `orderings_twice` and three new rules share: `order_cycles`, `order_candidates` and `order_statuses`, the last absorbing `landing_together`. The verification report reads the same edges to list, for each row in progress, the rows it lands with and their open items. Each rule is a function returning one message per fault, with fixtures showing it firing and a repository test showing it holding.

**Tech Stack:** Python, pytest, MyST markdown, reStructuredText.

**Spec:** `docs/src/developer/specs/2026-11-17-row-order-design.md` (`order spec §…`): §2 decisions 7 to 10, §4.5 items 5 to 7, §4.6, §4.7, §4.8, §8 item 1 and §9 row 2; and `docs/src/developer/specs/2026-11-02-open-items-design.md` (`items spec §…`): §3.7, §7 item 15 and §8 row 8.

## Global Constraints

- **A cycle**, in one specification or across several: row 2 after row 1 and row 1 after row 2, or `with` and `before` between the same two rows (order spec §4.5 item 5).
- **A `not started` row ordered `after`, `with` or `with or after` a `candidate`** fails (item 6).
- **A status that contradicts an ordering** fails: a row `after` another is `in progress` or `landed` only once the other has landed, on its date or before and in another pull request; a row `before` another has landed by the time the other lands, likewise; a row `with` another lands in the same pull request; one `with or after` another in the same one or once the other has landed. Rows landed on the same day pass on their dates alone (item 7).
- **The report lists, for each row `in progress`, the rows that land with it and the items each owes**; the check does not fail on them (§4.6).
- A release ordering is checked for its form alone (§4.4), so it is no edge of the graph.
- No new public name. Warnings are errors. Every pixi run is `pixi run --frozen -e geovista …`; commit through the environment's `pre-commit`. The fragment credits ``(:user:`claude`)``; the pull request carries `type: documentation` and `agentic`, and closes {issue}`2955` and {issue}`2991`.
- A test file named as evidence cites its decision in a docstring, as "Holds order spec §2 decision 7." (ledger spec §3.4).

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-18 that the order spec bounds row 2 (workflow rule 2.7). The calls are mine, except the one marked **for review**.

1. **One reading of the graph.** `ordering_edges(texts, names) -> list[Edge]` reads every well-formed ordering once, as `Edge(kind, first, second, path, row, clause)`: `after` X on Y and `before` Y on X are `("after", X, Y)`, X landing first; `with` is `("with", *sorted)`; `with or after` X on Y is `("with or after", X, Y)`. A release is no edge. `orderings_twice` is rewritten onto it, its tests unchanged.
2. **A cycle is a strict edge inside a strongly connected part.** Every edge is read as "lands no later than" (`with` both ways), the parts are found by Tarjan's algorithm, and an `after` whose two rows share a part is a cycle: the rows can never land in that order. A loop of `with` or `with or after` alone is no cycle, since one pull request lands it. The fault names each row of the part.
3. **A candidate's rule reads the edge.** An `after` or `with or after` whose first row is a `candidate` and second `not started` fails, as does a `with` between a `candidate` and a `not started` row. The fault names the `not started` row.
4. **A status reads as landed, in progress or neither.** `landed_on(status) -> tuple[date, set[tuple[str, int]]] | None` reads a `landed` row's date and pull requests, by role or by link (`_pulls`). For `after`: if the second row is in progress or landed, the first has landed, and if both have, on the second's date or before and with no pull request in common. For `with`: both landed, sharing a pull request, or neither. For `with or after`: if the second has landed, the first has, on its date or before; if the second is in progress, the first has landed or is in progress. A row in another specification is read from that specification's roadmap.
5. **`landing_together` goes.** Its cases become `order_statuses`'s, in the cell form: landed together or not at all passes, landed alone or apart fails, a pull request is known by any reference, a quoted ordering and a scope still saying *landing with* hold nothing, and every specification is read. Its range and uncited cases are the form rule's already (`test_ordering_form_refuses_a_range`, `..._finds_a_word_outside_the_relations`).
6. **The report's rows landing together.** `_together_findings(spec, texts, names) -> list[str]` in `verification_report.py`: for each row of the reported specification that is `in progress`, each `with` edge naming it, and the open items the other row owes, read with `own_row` as `_item_findings` reads them. A finding is written only when the other row owes an item: "*X* is in progress and lands with *Y*, which owes *items*: its pull request must answer them."
7. **The guard names rewording** ({issue}`2991`): its remedy becomes "write it in its row's Scope cell, as `· 🔗 after row 1`, or reword it if it orders a row against something that is not a row".
8. **Decision 10 is signed off, not verified. For review.** "The developer guide teaches the form" is held by pages, which no test reads for their teaching. Proposal: {user}`bjlittle` signs it off in review, as docs spec §2 decision 6 was, and its row reads ``✍️ signed off (<DATE>, {user}`bjlittle`, {pull}`2994`)`` with what was checked. Decisions 7, 8 and 9 are verified by `tests/test_spec_conventions.py` and `tests/test_verification_report.py`.
9. **Settled together.** Items spec §7 item 15 and order spec §8 item 1 become `🏁 Resolved`, citing this pull request, which closes {issue}`2955` and {issue}`2991` (workflow rule 4.7). The seventh check of items spec §3.7 says its rule now lives in order spec §4.5 item 7.
10. **One fragment, `2994.documentation.rst`.** The branch is `docs/order-spec-row2`, and this plan is the first commit of its draft pull request (workflow rule 2.3), which marks both rows in progress (workflow rule 2.4).

## Review Focus

1. **A cycle through two specifications.** Row 1 of demo after row 1 of other, and other's row 1 after demo's: one fault. `test_order_cycles_finds_a_cycle_across_specifications` (Task 2).
2. **A `with` and a `before` between one pair.** They contradict: a cycle. `test_order_cycles_finds_with_against_before` (Task 2).
3. **Rows landed on one day by two pull requests.** `after` passes on dates alone. `test_order_statuses_passes_rows_landed_the_same_day` (Task 3).
4. **A row in progress after one not started.** Fails, since workflow rule 2.7 plans a row once the rows it depends on have merged. `test_order_statuses_finds_a_row_begun_before_its_predecessor` (Task 3).
5. **A row in progress landing with one that owes nothing.** No finding in the report. `test_together_findings_names_only_a_row_owing_items` (Task 4).

---

Measured on 2026-11-18 at `082cccd7`: 68 orderings in sixteen specifications, every one well formed, none written twice or in prose; seven `with` edges, each between rows landed by one pull request or both not started; no ordering names a `candidate`. Row 8 of items spec §8 carries `· 🔗 with row 2 of order spec §9`, so this pull request lands both.

### Task 1: The Graph's Edges

**Files:**
- Modify: `tests/test_spec_conventions.py` (beside `orderings_twice`)

**Interfaces:**
- Produces: `Edge(NamedTuple: kind: str, first: str, second: str, path: Path, row: Row, clause: str)`, `ordering_edges(texts: Mapping[Path, str], names: Namespace) -> list[Edge]`, `landed_on(status: str) -> tuple[date, set[tuple[str, int]]] | None`, `row_statuses(texts, names) -> dict[str, str]` (anchor → status).

- [ ] **Step 1: Write the failing tests**

- `test_ordering_edges_reads_each_relation_as_an_edge`: on `ordered()` rows, `after row 1` on row 2 → `("after", demo-row-1, demo-row-2)`; `before row 1 of other spec §2` on demo row 3 → `("after", demo-row-3, other-row-1)`; `with` → sorted pair; `with or after` keeps its direction; `before 0.6` gives no edge.
- `test_landed_on_reads_a_date_and_its_pull_requests`: ``✅ landed (2026-11-03, {pull}`7`)`` → `(date(2026, 11, 3), {("bjlittle/geovista", 7)})`; `📋 not started` → `None`.
- `orderings_twice`'s tests, unchanged.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k "ordering_edges or landed_on or orderings_twice"`
Expected: the new tests FAIL, not defined.

- [ ] **Step 2: Write `Edge`, `ordering_edges`, `landed_on` and `row_statuses`, and rewrite `orderings_twice` onto `ordering_edges`**

Run: the command of Step 1. Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "test: read every ordering between rows as an edge of one graph"`

### Task 2: Cycles and Candidates

**Files:**
- Modify: `tests/test_spec_conventions.py`

**Interfaces:**
- Consumes: Task 1.
- Produces: `order_cycles(texts, names) -> list[str]`, `order_candidates(texts, names) -> list[str]`.

- [ ] **Step 1: Write the fixture tests**

- `test_order_cycles_finds_a_cycle_in_one_roadmap`: rows 1 to 3, 2 after 1, 3 after 2, 1 after 3: one fault naming rows 1, 2 and 3.
- `test_order_cycles_finds_a_cycle_across_specifications`.
- `test_order_cycles_finds_with_against_before`: `with row 1 of other spec §2` and `before row 1 of other spec §2` on one row: one fault.
- `test_order_cycles_passes_a_loop_of_with`: `with` both ways through three rows of two specifications: none.
- `test_order_candidates_finds_a_row_waiting_on_a_candidate`, parametrized over `after`, `with` and `with or after`, the named row `💡 candidate: a trigger`, the other `📋 not started`: one fault naming the `not started` row.
- `test_order_candidates_passes_a_candidate_waiting_on_a_row`: a `candidate` after a `not started` row: none.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k "order_cycles or order_candidates"`
Expected: FAIL.

- [ ] **Step 2: Write the rules** as Calls 2 and 3. Run: the same. Expected: PASS.
- [ ] **Step 3: Commit** — `git commit -m "test: refuse a cycle, and a row waiting on a candidate (order spec §4.5 items 5 and 6)"`

### Task 3: Statuses, With `landing_together` Folded In

**Files:**
- Modify: `tests/test_spec_conventions.py` (`order_statuses`; `landing_together`, `landing` and their tests removed or rewritten)

**Interfaces:**
- Consumes: Task 1.
- Produces: `order_statuses(texts, names) -> list[str]`.

- [ ] **Step 1: Write the fixture tests**

- `test_order_statuses_passes_rows_landed_in_order`, `..._passes_rows_landed_the_same_day`, `..._finds_a_row_landed_before_its_predecessor` (dates reversed), `..._finds_rows_landed_by_one_pull_request` (an `after` sharing a pull request), `..._finds_a_row_begun_before_its_predecessor` (`in progress` after `not started`).
- `..._finds_a_row_landed_before_the_row_it_precedes`: `before` X on Y, X landed and Y not.
- `..._finds_with_or_after_landed_first`.
- The cases of Call 5, renamed from `test_landing_together_*`: `test_order_statuses_passes_rows_landed_together_or_not_at_all`, `..._finds_a_row_landed_alone_or_apart`, `..._knows_a_pull_request_by_any_reference`, `..._reads_no_ordering_in_code`, `..._reads_only_the_cell_form`, `..._reads_every_specification`.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k order_statuses`
Expected: FAIL.

- [ ] **Step 2: Write `order_statuses`** as Call 4, and remove `landing_together`, `landing`, `PULL_*` only if no other reader keeps them, and `test_every_row_landing_with_another_lands_with_it`.

Run: the same, then the whole module. Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "test: hold each status to the orderings of its row (order spec §4.5 item 7)"`

### Task 4: The Report of Rows Landing Together

**Files:**
- Modify: `.github/scripts/verification_report.py` (`_together_findings`, called in `report` beside `_item_findings`)
- Test: `tests/test_verification_report.py`

**Interfaces:**
- Consumes: Task 1 (`ordering_edges`, through the conventions module the report already loads).
- Produces: `_together_findings(path: Path, texts: Mapping[Path, str], names: Namespace) -> list[str]`.

- [ ] **Step 1: Write the failing tests**

- `test_together_findings_names_the_items_a_partner_owes`: demo row 1 `🚧 in progress` `· 🔗 with row 1 of other spec §2`, other row 1 owing one open item: one finding naming the item.
- `test_together_findings_reads_a_with_written_on_the_partner`: the same `with` written on the other row.
- `test_together_findings_names_only_a_row_owing_items`: the partner owes none: no finding.
- `test_together_findings_reads_only_a_row_in_progress`: the demo row `not started`: none.
- `test_report_lists_rows_landing_together`: the report's Findings carry the line. The test file's docstring cites "order spec §2 decision 8".

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_verification_report.py -k together`
Expected: FAIL.

- [ ] **Step 2: Write `_together_findings`** as Call 6. Run: the same. Expected: PASS.
- [ ] **Step 3: Commit** — `git commit -m "feat: report the rows a row in progress lands with, and their items (order spec §4.6)"`

### Task 5: The Guard's Advice, the Repository Tests and the Pages

**Files:**
- Modify: `tests/test_spec_conventions.py` (the remedy of `ordering_in_prose`; repository tests)
- Modify: `docs/src/developer/specs/index.rst`, `docs/src/developer/checks.rst`, `docs/AGENTS.md`
- Modify: `docs/src/developer/specs/2026-11-02-open-items-design.md` §3.7

- [ ] **Step 1: Write the failing tests**

- `test_ordering_in_prose_names_rewording`: a fault's text carries "reword".
- `test_no_order_cycles`, `test_no_row_waits_on_a_candidate`, `test_every_status_agrees_with_its_orderings`: each over the corpus, each citing "order spec §2 decision 7"; the last also "order spec §2 decision 9".

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k "names_rewording or no_order_cycles or waits_on_a_candidate or agrees_with"`
Expected: the first FAIL, the repository tests PASS on today's corpus.

- [ ] **Step 2: The remedy** as Call 7. **The pages**, humanized: the index's *Ordering Roadmap Rows* adds what the graph refuses and what the report shows; the checks page adds each fault of items 5 to 7 to *When it fails*, with its remedy; `docs/AGENTS.md` adds "cycles, a row waiting on a candidate, and statuses the order contradicts fail" to its ordering line, under 200 lines; items spec §3.7's seventh check says order spec §4.5 item 7 now holds its rule.

Run: the command of Step 1, the strict incremental `sphinx-build` that `docs/AGENTS.md` gives, and `pixi run --frozen -e test check-spec-renumbering`. Expected: PASS, no warning.

- [ ] **Step 3: Commit** — `git commit -m "docs: teach the graph of orderings, and name rewording in the guard's advice"`

### Task 6: Landing the Rows

**Files:**
- Modify: both specifications (§9 row 2 and §8 row 8, §11 and items spec §11, the two items), this plan's Follow-ups
- Create: `changelog/2994.documentation.rst`

- [ ] **Step 1: Watch each clause fail when it regresses** (workflow rule 2.6): an edge read without its direction; `with` read one way; a `with or after` read as strict; the cycle test reading `with` as strict; the candidate rule skipping `with`; each branch of `order_statuses` (after's date, after's pull request, in progress after not started, before, with, with or after); the report reading a row not in progress, or a partner owing nothing; the remedy losing "reword". In the repository, write a cycle and a `with` between rows landed apart.
- [ ] **Step 2: Mark and settle.** Row 2 of order spec §9 and row 8 of items spec §8 become ``✅ landed (<DATE>, {pull}`2994`)``. In order spec §11, decisions 7, 8 and 9 become ``✅ verified (<DATE>, {pull}`2994`)`` with their evidence, and decision 10 as {user}`bjlittle` decides in review (Call 8). Items spec §7 item 15 and order spec §8 item 1 become ``🏁 Resolved (<DATE>, {pull}`2994` · …)``. The fragment, humanized, names `row 2 of order spec §9` and `row 8 of items spec §8`.

Run: the changelog check, the spec suites, `check-spec-status 2994` with a token, `check-spec-renumbering`. Expected: all pass, and both specifications read `✅ complete`.

- [ ] **Step 3: The whole suite and the docs build on that commit**: the strict `sphinx-build` with `-E`, `tests/docs -m "not browser"` under `xvfb-run -a`, and `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e test-py314 tests-unit`. Expected: PASS, no new skips.

- [ ] **Step 4: Push** and confirm with `git ls-remote` (workflow rule 4.6), and ask {user}`bjlittle` to mark the pull request ready once the final review's fixes have landed.

## Follow-ups

None yet.

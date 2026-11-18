# Roadmap Row Order: the Form Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of order spec §9: an ordering between roadmap rows is written `· 🔗 <relation> <row>` in its row's Scope cell, the conventions test holds its form (items 1 to 4 of order spec §4.5), every ordering written today moves into its cell (order spec §4.7), and the developer guide teaches the form (order spec §4.8).

**Architecture:** The shared grammar, `docs/src/_ext/geovista_citations.py`, learns to split a Scope cell into its scope and its orderings, and to read one ordering. The conventions test gains three rules over that grammar (the form of one ordering, an ordering written twice, an ordering written in prose), each a function returning one message per fault with fixtures that show it firing. `landing_together` reads `🔗 with` in place of *landing with*, and the renumber guard pairs rows by their scope alone. Then the sixteen specifications are edited as Appendix A says, and the repository tests hold them.

**Tech Stack:** Python, `re`, pytest, MyST markdown, reStructuredText.

**Spec:** `docs/src/developer/specs/2026-11-17-row-order-design.md` (`order spec §…`): §2 decisions 1 to 6 and 11, §3.3, §4.1 to §4.5, §4.7, §4.8 and §9 row 1.

## Global Constraints

- An ordering is `· 🔗 <relation> <target>`: a middle dot, a space, U+1F517 (read with or without U+FE0F), a space, one of `after`, `before`, `with`, `with or after`, a space and its target (order spec §4.1, §4.2).
- The first `· 🔗` ends the scope; each later one opens another ordering (§4.1).
- A target is one row: bare `row N` names the same roadmap's row; another specification's row is cited in full, as `row 2 of layers spec §9`. A range is refused (§4.1, §2 decision 4).
- A release is `before` and a version of two or three numbers, as `0.6`; no other relation takes one, and only its form is checked (§4.4).
- An ordering is written once, on the row its reason belongs to; the same ordering read in both directions, or twice on a row, is a fault (§4.3).
- The prose guard reads the paragraphs under a roadmap, up to the next heading, and a scope before its first `· 🔗`, skipping code (§4.5 item 4).
- A module in `docs/src/_ext` spells each emoji by name, as `"\N{LINK SYMBOL}"`. No new public name. `mypy` does not read `docs/src/_ext`, but its functions carry types. Warnings are errors under pytest.
- Every pixi run is `pixi run --frozen -e geovista …`. Commit through the environment's `pre-commit`. The fragment credits ``(:user:`claude`)``; the pull request carries `type: documentation` and `agentic`, and closes no issue.
- A test file named as evidence in §11 of the order spec cites its decision in a docstring, as "Holds order spec §2 decision 3." (ledger spec §3.4).

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-17 that the order spec bounds row 1 (workflow rule 2.7), and that a sentence whose literal move would set an order nobody meant is settled with him through Appendix A. The calls are mine, except those marked **for review**, which wait on his answer before Task 5.

1. **The grammar owns the form.** `geovista_citations` gains `LINK`, `ORDERING` (`" · 🔗"`), `RELATIONS` (longest first, so `with or after` is read before `with`), `RELEASE`, a frozen dataclass `Ordering(relation: str, target: str)`, `split_scope(scope) -> tuple[str, list[str]]` and `ordering(clause) -> Ordering | None`. The renumber guard, `landing_together` and the rules all read through them, so there is one reading of a cell.
2. **Three rules, one per kind of fault.** `ordering_form(path, text, names)` holds items 1 and 2 of §4.5 on one specification. `orderings_twice(texts, names)` holds item 3 across all of them, since an ordering's other direction can sit in another specification. `ordering_in_prose(path, text)` holds item 4.
3. **An existing cited row is the resolution rule's.** A target cited in full already has to resolve under item 3 of docs spec §3.5, so `ordering_form` checks only that it is a row and not a range, and that a bare `row N` is a row of its own roadmap.
4. **An ordering is normalised to an edge for item 3.** `after` X on Y and `before` Y on X are the edge X → Y; `with` is the unordered pair; `with or after` X on Y is X ⇒ Y. Two equal edges are an ordering written twice. A release is its own edge, row → version.
5. **The guard's words** are §4.2's last column and *waits on*, as a pattern of an ordering word followed by `row` or `rows` and a number: *lands with or after*, *lands with*, *landing with*, *lands before*, *lands after*, *before*, *after*, *needs*/*need*, *once*, *planned once*, *waits on*/*wait on*. **For review:** add *follows* and *builds on*, which today's prose uses (Appendix A §2) and a new specification could write again; this widens §4.5 item 4, so the amendment rides in this pull request (workflow rule 2.1).
6. **Which row writes a `with` across specifications. For review.** §4.3 says the row that waits, and for `with` both do. Today's texts write it on the row whose work another specification's row does: heights row 5 on layers row 2, citation row 5 on items row 1. Order spec row 2 is the exception, writing it on the row that builds the work. Proposal: amend §4.3 to say so, and move `· 🔗 with row 2 of order spec §9` onto row 8 of items spec §8 (Appendix A entry 59).
7. **The CRS spec's "Rows 1 to 4 come first and in order". For review.** Row 2 there is the globe's work, "by rows 1 to 5 of globe spec §9", and lands with row 5 of globe spec §9, so a literal move holds the cutting engine (row 3) and every class behind the removal of `zlevel` and the whole layers roadmap. Proposal: row 3 `· 🔗 after row 1`, row 4 `· 🔗 after row 3`, rows 5 to 13 `· 🔗 after row 4`, row 14 after each class row (6 to 11), and row 2 ordered only by its `with`; the sentence becomes "Rows 1, 3 and 4 come first, since everything else stands on them; row 2 is the globe's, and lands with row 5 of globe spec §9." (Appendix A entries 27, 28.)
8. **Text outside a roadmap stays.** Order spec §4.7 moves the orderings under a roadmap and in its cells; one written in another section (entries 13, 19, 24, 25, 55, 56) restates one moved, or records history, and stays. The guard does not read there.
9. **Items spec §3.4's example is brought up to date**: it cites heights row 5 against row 4 of globe spec §9, which it no longer lands with (entry 45), and it is written in the old form. It becomes `· 🔗 with row 2 of layers spec §9`. The resolved items 11 and 14 of items spec §7 keep the history they record.
10. **Found on the way.** crs spec §6 and scene spec §4.3 disagree on which row the round trip of crs spec §6 landed with. It is no ordering, and is raised as an issue for its own pull request (workflow rule 4.5). Heights spec §9's "Until it lands" is stale, since row 2 has landed, and is corrected as its paragraph moves.
11. **Evidence.** `ordering_form`'s repository test holds §2 decisions 1 to 4 and 6, `orderings_twice`'s holds decision 5, and `ordering_in_prose`'s holds decision 11; §11 of the order spec names `tests/test_spec_conventions.py` for each. Decisions 7 to 10 wait on row 2.
12. **One fragment, `2990.documentation.rst`.** The branch is `docs/order-spec-row1`, and this plan is the first commit of its draft pull request (workflow rule 2.3), which marks row 1 in progress (workflow rule 2.4).

## Review Focus

1. **A roadmap of four columns.** typing spec §4 is `| # | Scope | Lines | Status |`; the scope is found by its header, never by its place. `test_ordering_form_reads_the_scope_of_a_wider_table` (Task 2).
2. **🔗 with a variation selector.** `· 🔗️ after row 1` reads as `· 🔗 after row 1`. `test_ordering_reads_a_variation_selector` (Task 1).
3. **Code in a cell.** `` `· 🔗 after row 1` `` quoted in a scope is no ordering, and the guard skips it. `test_split_scope_skips_code` (Task 1), `test_ordering_in_prose_skips_code` (Task 3).
4. **An ordering in two directions across specifications.** `before row 5 of globe spec §9` on heights row 4 and `after row 4 of heights spec §9` on globe row 5 are one ordering written twice. `test_orderings_twice_finds_both_directions_across_specifications` (Task 2).
5. **A measurement that reads as an ordering.** positions spec row 7's "as fast as before row 5" trips the guard until reworded (Appendix A §2.1). `test_ordering_in_prose_finds_a_bare_before` (Task 3), and the rewording in Task 5.

---

Measured on 2026-11-17 at `ce1a2e2e`: sixteen specifications, every roadmap read by `geovista_citations.rows`, no Scope cell holding a middle dot, and the orderings of Appendix A, which a subagent inventoried and the plan's author spot-checked against crs spec §10.

### Task 1: The Grammar of an Ordering

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py` (beside `DOT`)
- Test: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Produces: `LINK: str`, `ORDERING: str`, `RELATIONS: tuple[str, ...]`, `RELEASE: re.Pattern[str]`, `Ordering(relation: str, target: str)`, `split_scope(scope: str) -> tuple[str, list[str]]`, `ordering(clause: str) -> Ordering | None`.

- [ ] **Step 1: Write the failing tests**

- `test_split_scope_returns_the_scope_alone_without_orderings`: `split_scope("The lift")` is `("The lift", [])`.
- `test_split_scope_splits_each_ordering`: `split_scope("The lift · 🔗 after row 2 · 🔗 with row 2 of layers spec §9")` is `("The lift", ["after row 2", "with row 2 of layers spec §9"])`, the emoji built by name.
- `test_split_scope_skips_code`: a `` `· 🔗 after row 1` `` in backticks splits nothing.
- `test_ordering_reads_each_relation`, parametrized: `"after row 1"` → `Ordering("after", "row 1")`, `"before row 5 of globe spec §9"`, `"with row 2"`, `"with or after row 3 of globe spec §9"` → `Ordering("with or after", ...)`, `"before 0.6"` → `Ordering("before", "0.6")`.
- `test_ordering_refuses_another_word`: `"needs row 1"` and `"after"` (no target) → `None`.
- `test_ordering_reads_a_variation_selector`: `split_scope` reads `" · 🔗\N{VARIATION SELECTOR-16} after row 1"`.
- `test_release_reads_two_or_three_numbers`: `RELEASE.fullmatch` takes `0.6` and `0.6.1`, not `0` or `v0.6`.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_citations.py -k "split_scope or ordering or release"`
Expected: FAIL, the names not defined.

- [ ] **Step 2: Write the grammar**

`split_scope` blanks code with the module's `prose` first, as `landing_together` does, finds each `ORDERING` (with or without U+FE0F) at a top level, and returns the text before the first, stripped, and each clause after one, stripped. `ordering` matches `RELATIONS` in order at the start of a clause, followed by whitespace and a non-empty target.

Run: the command of Step 1.
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add docs/src/_ext/geovista_citations.py tests/docs/test_geovista_citations.py
git commit -m "docs: read an ordering in a roadmap's Scope cell (order spec §4.1)"
```

### Task 2: The Form of an Ordering, and an Ordering Written Twice

**Files:**
- Modify: `tests/test_spec_conventions.py` (a section after the open items rules)

**Interfaces:**
- Consumes: Task 1.
- Produces: `ordering_form(path: Path, text: str, names: Namespace) -> list[str]`, `orderings_twice(texts: Mapping[Path, str], names: Namespace) -> list[str]`.

- [ ] **Step 1: Write the fixture tests**

Each builds specifications with `demo()`, and a second with another prefix where it needs one, their roadmaps under `## 9. Roadmap`, emoji built by name.
- `test_ordering_form_passes_each_relation_and_a_release`: rows 1 to 3, row 2 `· 🔗 after row 1`, row 3 `· 🔗 with or after row 2 · 🔗 before 0.6`: no fault.
- `test_ordering_form_finds_a_word_outside_the_relations`: `· 🔗 needs row 1` and `· 🔗 after` (no target): one fault each, naming the row and the clause.
- `test_ordering_form_finds_a_row_that_does_not_exist`: `· 🔗 after row 7` in a roadmap of three rows.
- `test_ordering_form_refuses_a_range`: `· 🔗 after rows 1 to 2`.
- `test_ordering_form_refuses_a_release_on_another_relation`: `· 🔗 with 0.6` and `· 🔗 after 0.6`.
- `test_ordering_form_reads_the_scope_of_a_wider_table`: a `| # | Scope | Lines | Status |` roadmap with `· 🔗 after row 7`: one fault.
- `test_orderings_twice_finds_an_ordering_repeated_on_one_row`.
- `test_orderings_twice_finds_both_directions_across_specifications`: `before row 5 of other spec §9` on demo row 4, and `after row 4 of demo spec §9` on other row 5: one fault.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k "ordering_form or orderings_twice"`
Expected: FAIL, the rules not defined.

- [ ] **Step 2: Write the rules**

As Calls 2 to 4 say. A fault opens with `where(path, row.line)` and names the row and the clause, as `row 2: "needs row 1" is no ordering: write after, before, with or with or after, and one row`.

Run: the command of Step 1.
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_spec_conventions.py
git commit -m "test: hold the form of an ordering between rows (order spec §4.5 items 1 to 3)"
```

### Task 3: An Ordering Written in Prose

**Files:**
- Modify: `tests/test_spec_conventions.py`

**Interfaces:**
- Consumes: Task 1 (`split_scope`).
- Produces: `ORDER_WORDS: re.Pattern[str]`, `ordering_in_prose(path: Path, text: str) -> list[str]`.

- [ ] **Step 1: Write the fixture tests**

- `test_ordering_in_prose_finds_each_word_under_a_roadmap`, parametrized over each word of Call 5: a sentence under the table, as "Row 3 needs row 1.", is one fault naming the line.
- `test_ordering_in_prose_finds_one_in_a_scope_before_its_orderings`: a scope "The lift, landing with row 2 of other spec §9" is one fault; the same after a `· 🔗` is none.
- `test_ordering_in_prose_finds_a_bare_before`: "as fast as before row 5" under a roadmap is one fault.
- `test_ordering_in_prose_passes_a_word_naming_no_row`: "Row 4 needs a renderer in CI", "after {issue}`2756`", "waits on the regions design", "before 0.6 is released": none.
- `test_ordering_in_prose_skips_code`: the same words in backticks or a fence: none.
- `test_ordering_in_prose_reads_only_under_a_roadmap`: the same sentence in another section: none, and under the next heading after the roadmap's: none.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k ordering_in_prose`
Expected: FAIL.

- [ ] **Step 2: Write the rule**

`ORDER_WORDS` as Call 5, case-insensitive, an ordering word then whitespace then `rows?\s+\d`. `ordering_in_prose` reads each roadmap's Scope cells through `split_scope` and the lines under it through `read_lines` and `prose`, from the table to the next heading. A fault names the line, the words and the cell form to write instead.

Run: the command of Step 1.
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_spec_conventions.py
git commit -m "test: refuse an ordering written in prose (order spec §4.5 item 4)"
```

### Task 4: The Readers That Move With the Form

**Files:**
- Modify: `tests/test_spec_conventions.py` (`landing_together`, `LANDING_WITH`, their fixtures)
- Modify: `.github/scripts/check_renumbering.py` (`roadmap_rows`)
- Test: `tests/test_renumbering.py`

**Interfaces:**
- Consumes: Task 1.

- [ ] **Step 1: Write the failing tests**

- In `tests/test_spec_conventions.py`, the fixtures of `landing_together` write `· 🔗 with row 1 of other spec §2` in place of *landing with*, and `test_landing_together_reads_only_the_cell_form`: a scope still reading "landing with row 1 of other spec §2" holds no check.
- In `tests/test_renumbering.py`, `test_a_row_gaining_an_ordering_pairs_with_itself`: a roadmap whose row 3 scope "The lift" becomes "The lift · 🔗 after row 2" reports no row reworded or moved; and `test_roadmap_rows_titles_a_row_by_its_scope_alone`.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_renumbering.py -k "landing or ordering or scope_alone"`
Expected: FAIL.

- [ ] **Step 2: Move the readers**

`landing_together` reads each row's orderings through `split_scope` and `ordering`, keeps those whose relation is `with`, and checks them as it checks *landing with* today; `LANDING_WITH` goes. `check_renumbering.roadmap_rows` titles a row by `split_scope(row.scope)[0]`.

Run: the command of Step 1.
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_spec_conventions.py .github/scripts/check_renumbering.py tests/test_renumbering.py
git commit -m "test: read a row landing with another, and pair renumbered rows, by the cell form"
```

### Task 5: The Move

Waits on {user}`bjlittle`'s review of Appendix A and of Calls 5, 6 and 7.

**Files:**
- Modify: every specification Appendix A names, and `docs/src/developer/specs/2026-11-02-open-items-design.md` §3.4 (Call 9)
- Modify: `docs/src/developer/specs/2026-11-17-row-order-design.md` §4.3 and §4.5 item 4, if Calls 5 and 6 are agreed
- Modify: `tests/test_spec_conventions.py` (the repository tests)

- [ ] **Step 1: Write the repository tests**

- `test_every_ordering_is_well_formed(spec)`, parametrized over `specifications()`: `ordering_form` finds nothing. Holds order spec §2 decisions 1, 2, 3, 4 and 6.
- `test_no_ordering_is_written_twice()`: `orderings_twice` over the corpus finds nothing. Holds order spec §2 decision 5.
- `test_no_ordering_is_written_in_prose(spec)`: `ordering_in_prose` finds nothing. Holds order spec §2 decision 11.
- `test_the_collection_writes_orderings(specs)`: some Scope cell carries one, so the rules cannot pass by finding none.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k "every_ordering or written_twice or written_in_prose or writes_orderings"`
Expected: FAIL, naming each sentence of Appendix A still in prose.

- [ ] **Step 2: Move each ordering as Appendix A, as reviewed, says**

One specification at a time, each cell and paragraph as its entry says, with the rewordings of Appendix A §2.1. Re-run Step 1's command after each specification.

Run: then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_renumbering.py tests/test_verification_report.py`, and `pixi run --frozen -e test check-spec-renumbering`.
Expected: PASS, and the renumber guard reports no row reworded or moved.

- [ ] **Step 3: Commit**

```bash
git add docs/src/developer/specs tests/test_spec_conventions.py
git commit -m "docs: move every ordering between roadmap rows into its row's Scope cell"
```

### Task 6: The Developer Guide

**Files:**
- Modify: `docs/src/developer/specs/index.rst` (a section *Ordering Roadmap Rows* after Open Items)
- Modify: `docs/src/developer/checks.rst` (Specification Conventions)
- Modify: `docs/AGENTS.md`

- [ ] **Step 1: Write the pages**

Humanized (workflow rule 3.1). The index section shows a roadmap of three rows carrying orderings, the four relations in a table, which row writes one, a release, and that prose is refused, citing order spec §4.1 to §4.5. The checks page adds the orderings to the rule, and to *When it fails* each fault's message and its remedy. `docs/AGENTS.md` gains one line: an ordering is `· 🔗 <relation> <row>` in the Scope cell, written once, never in prose (order spec §4.1), within the 200-line limit.

Run: the strict incremental `sphinx-build` that `docs/AGENTS.md` gives, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py`.
Expected: the build succeeds with no warning, and PASS.

- [ ] **Step 2: Commit**

```bash
git add docs/src/developer/specs/index.rst docs/src/developer/checks.rst docs/AGENTS.md
git commit -m "docs: teach the form of an ordering between roadmap rows"
```

### Task 7: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-17-row-order-design.md` (§9 row 1, §11)
- Modify: this plan's Follow-ups, before merge
- Create: `changelog/2990.documentation.rst`

- [ ] **Step 1: Watch each clause fail when it regresses** (workflow rule 2.6)

Mutate one at a time, run the named tests, see them fail, and revert: `RELATIONS` lose `with or after`; `ordering` take any word; `split_scope` read code; a bare row go unchecked; a range pass; a release take `with`; `orderings_twice` read one direction; `ORDER_WORDS` lose each word; the guard read past the next heading; `landing_together` read *landing with* again; `roadmap_rows` title a row by its whole cell. In the repository, write one ordering back as prose, and one twice.

- [ ] **Step 2: Mark the decisions and the row, and add the fragment**

In §11, §2 decisions 1 to 6 and 11 become ``✅ verified (<DATE>, {pull}`2990`)`` with evidence `tests/test_spec_conventions.py`, and row 1 of §9 becomes ``✅ landed (<DATE>, {pull}`2990`)``. The fragment, humanized, says that an ordering between roadmap rows is now written in its row's Scope cell and checked, and names the row as `row 1 of order spec §9` on one line.

Run: the changelog check, the spec suites, `check-spec-status 2990` with a token, and `check-spec-renumbering`.
Expected: all pass, and the order spec reads `🚧 1 of 2 rows`.

- [ ] **Step 3: Run the whole suite and the docs build on that commit**

Run: the strict `sphinx-build` with `-E`, `tests/docs -m "not browser"` under `xvfb-run -a`, and `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e test-py314 tests-unit`.
Expected: the build succeeds, and the suites PASS with no new skips.

- [ ] **Step 4: Push, and ask for the pull request to be marked ready**

Push, confirm it with `git ls-remote` (workflow rule 4.6), raise the issue of Call 10, and ask {user}`bjlittle` to mark the pull request ready once the final review's fixes have landed.

## Follow-ups

{user}`bjlittle` approved the plan with Calls 5, 6 and 7 as proposed. Executing it, `landing_together`'s rewrite first put its `return` inside the loop over specifications, which no test caught, so `test_landing_together_reads_every_specification` was added and shown to fail with it. A wrapped paragraph under a roadmap is read whole by the guard, and the renumber guard already paired a rescoped row, so its new test is a regression test.

The final review found two Important points, both fixed with a test that failed first: a mistyped opener on a `with` (`·🔗`, `• 🔗`) hid its ordering from every check, so the guard refuses a 🔗 outside an opener; and §2 decision 5 was verified on "written once" alone, so a `before` within one roadmap is refused too. Which row a `with` across specifications belongs on stays held by review. Of its seven minor points, {user}`bjlittle` chose to fix six here: a row ordered against itself, an opener without its space after the emoji, the past tense (*landed with*), the `row N does not exist` message missing from the checks page, overlong lines, and order spec §9's prose restating its `with`. The seventh, the guard's advice for a row ordered against something else, is {issue}`2991`, order spec §8 item 1, owed by row 2.

Call 10's disagreement was fixed here, at {user}`bjlittle`'s choice: crs spec §6 now says the round trip landed with row 1 of scene spec §9 ({pull}`2761`).

## Appendix A: The Orderings, Sentence by Sentence

Inventoried on 2026-11-17 at `ce1a2e2e`. Line numbers are that commit's. Each entry's proposed cell form is what Task 5 writes, unless {user}`bjlittle`'s review of Calls 5 to 7 changes it. Entries 27 and 28 follow Call 7, and entry 59 follows Call 6.

### A.1 The Orderings

| # | Spec (prefix) | Line | Today's sentence (quoted, trimmed) | Rows ordered | Proposed cell form(s), on which row | Prose after the move (reason kept, or "delete sentence") | Flag |
|---|---|---|---|---|---|---|---|
| 1 | globe spec §9 | 666-667 | "Rows 1 to 5 come in order, and each is planned once the rows before it have landed." | globe 2 after 1, 3 after 2, 4 after 3, 5 after 4 | row 2: `· 🔗 after row 1`; row 3: `· 🔗 after row 2`; row 4: `· 🔗 after row 3`; row 5: `· 🔗 after row 4` | delete sentence | UMBRELLA: rows 2, 3 and 4 stand for scene rows 1-2, heights rows 1-2 and layers rows 1-4. Through #21 (globe 4 `with` layers 4), row 5 lands only after layers row 4, and so after layers rows 1-3 too. This looks intended, since layers §9 keeps a user's `zlevel` until globe row 5 removes it. Statuses agree: row 1 ✅ 2026-10-27 #2754, row 2 ✅ 2026-10-28 #2766, row 3 ✅ 2026-11-11 #2942, rows 4 and 5 📋 |
| 2 | globe spec §9 | 667-668 | "Row 4 needs a renderer in CI, which the image tests already have." | globe 4 / a CI renderer | none | stays as written | NOT-A-ROW |
| 3 | globe spec §9 | 669 | "Row 2 of the parent's roadmap lands with row 5 here." | crs 2 with globe 5 | on **row 2 of crs spec §10** (the row that waits, an umbrella "by rows 1 to 5 of globe spec §9"): `· 🔗 with row 5 of globe spec §9` | delete sentence (the ordering moves to another spec's table) | UMBRELLA, see #28. Left in place, it would trip the prose guard ("lands with row 5"). Statuses: both 📋 |
| 4 | globe spec §9 | 669-671 | "Rows 6 to 9 are candidates: row 6 waits on a scene with heights that a scientist shows, and rows 7 to 9 each wait on a user asking for them." | candidate triggers | none | stays | NOT-A-ROW (docs spec §2 decision 6 governs triggers) |
| 5 | heights spec §9 | 445 (scope, row 4) | "Heights from a raster band in `Transform.from_tiff`, before row 5 of globe spec §9" | heights 4 before globe 5 | row 4: scope becomes "Heights from a raster band in `Transform.from_tiff` · 🔗 before row 5 of globe spec §9". The earlier row writes it, as order spec §4.3's own example says | (scope cell; reason in #11) | Statuses: both 📋 |
| 6 | heights spec §9 | 446 (scope, row 5) | "…, in the subsurface tier, landing with row 2 of layers spec §9" | heights 5 with layers 2 | row 5: "A surface below sea level seen past a base layer given an opacity, or none, in the subsurface tier · 🔗 with row 2 of layers spec §9" | (scope cell; reason in #12) | Today it is also written in #12, #13, #22, #24 and #25. `landing_together` reads this cell today (order spec §4.7). Statuses: both 📋 |
| 7 | heights spec §9 | 448 | "Row 2 is planned once row 1 has landed." | heights 2 after 1 | row 2: `· 🔗 after row 1` | delete sentence | Statuses: row 1 ✅ 2026-10-30 #2777, row 2 ✅ 2026-11-11 #2942 |
| 8 | heights spec §9 | 452-453 | "Row 3 of globe spec §9 lands with row 2, before 0.6 is released." | globe 3 with heights 2; globe 3 before 0.6 | on **row 3 of globe spec §9**: `· 🔗 with row 2 of heights spec §9 · 🔗 before 0.6` (order spec §4.7 names this release) | delete sentence | RELEASE; UMBRELLA: globe row 3 is "by rows 1 and 2 of heights spec §9", but only row 2 lands with it. `with row 1 of heights spec §9` would CONTRADICT the statuses: heights row 1 ✅ #2777, globe row 3 ✅ #2942. Statuses for the pair: both ✅ 2026-11-11 #2942. Left in place, the sentence would trip the guard |
| 9 | heights spec §9 | 455 | "Rows 3 to 5 each wait on a row of globe spec §9." | summary | none | delete sentence | SUMMARY (order spec §4.2 quotes it as its example) |
| 10 | heights spec §9 | 455-456 | "Row 3 lands with or after row 3 of globe spec §9, which fixes a scene's globe when the scene is made." | heights 3 with-or-after globe 3 | row 3: `· 🔗 with or after row 3 of globe spec §9` | "Row 3 of globe spec §9 fixes a scene's globe when the scene is made." | Statuses: heights 3 📋, globe 3 ✅ 2026-11-11, so it can only be *after* now |
| 11 | heights spec §9 | 456-457 | "Row 4 lands before row 5 of globe spec §9, which migrates the gallery." | heights 4 before globe 5 (same as #5) | none new: #5 already writes it | "Row 5 of globe spec §9 migrates the gallery." | Today the ordering is written twice, in the scope and here |
| 12 | heights spec §9 | 457-459 | "Row 5 lands with row 2 of layers spec §9, which builds the subsurface tier and the clip that a base layer given an opacity switches off." | heights 5 with layers 2 (same as #6) | none new: #6 | "Row 2 of layers spec §9 builds the subsurface tier, and the clip that a base layer given an opacity switches off." | Duplicate of #6 |
| 13 | heights spec §8 item 3 | 414-415 | "…the subsurface tier keeps the floor beneath the sea surface (layers spec §4.1), so row 5 lands with row 2 of layers spec §9, which builds both." | heights 5 with layers 2 (same as #6) | none new: #6 | Not under a roadmap, so order spec §4.7 does not move it and the guard does not read it. Could stay. Optional rewording: "…, which row 2 of layers spec §9 builds, and row 5 lands with it." | ELSEWHERE (§8). Duplicate of #6 |
| 14 | scene spec §9 | 527 (scope, row 3) | "The release after which a retired field is refused, once row 5 of globe spec §9 adds `gvZScale` and `gvZLevel`" | scene 3 after globe 5 | row 3: "The release after which a retired field is refused · 🔗 after row 5 of globe spec §9" | the reason ("adds `gvZScale` and `gvZLevel`") is kept in #18 | Order spec §3.1 names this cell. Statuses: both 📋 |
| 15 | scene spec §9 | 530-531 | "Row 2 is planned once row 1 has landed, and after {issue}`2756`, so that the README's examples are run against it." | scene 2 after 1; scene 2 after an issue | row 2: `· 🔗 after row 1` | "Row 2 lands after {issue}`2756`, so that the README's examples are run against it." | The issue part is NOT-A-ROW and stays. Statuses: row 1 ✅ 2026-10-28 #2761, row 2 ✅ 2026-10-28 #2766. They landed on the same day, so the check passes on dates alone |
| 16 | scene spec §9 | 532 | "Row 2 of globe spec §9 lands with it." | globe 2 with scene 2 | on **row 2 of globe spec §9**: `· 🔗 with row 2 of scene spec §9` | delete sentence | UMBRELLA: globe row 2 is "by rows 1 and 2 of scene spec §9". `with row 1 of scene spec §9` would CONTRADICT the statuses (#2761 against #2766). Statuses for the pair: both ✅ 2026-10-28 #2766. Left in place, the sentence would trip the guard |
| 17 | scene spec §9 | 532-533 | "Rows 1 and 2 land before 0.6 is released, since 0.6 is the first release that writes the globe and no retired field." | scene 1, 2 before 0.6 | row 1: `· 🔗 before 0.6`; row 2: `· 🔗 before 0.6` | "0.6 is the first release that writes the globe and no retired field." | RELEASE. Both rows ✅, 0.6 not yet released |
| 18 | scene spec §9 | 533-534 | "Row 3 is planned once row 5 of globe spec §9 has added `gvZScale` and `gvZLevel` to the table of §4.5." | scene 3 after globe 5 (same as #14) | none new: #14 | "Row 5 of globe spec §9 adds `gvZScale` and `gvZLevel` to the table of §4.5, which row 3 reads." | Today written twice, in the scope and here |
| 19 | scene spec §8 item 1 | 516-517 | "…to settle once row 5 of globe spec §9 has added `gvZScale` and `gvZLevel` to the table of §4.5 ({issue}`2758`)." | item owed by scene 3 / globe 5 | none new: #14 | Stays. It is an item's own wording, outside the roadmap | ELSEWHERE (§8). It restates #14 for the item that row 3 owes; §4.7 does not move it |
| 20 | layers spec §9 | 566-567 | "Rows 1 to 4 come in order, each planned once the rows before it have landed," | layers 2 after 1, 3 after 2, 4 after 3 | row 2: `· 🔗 after row 1`; row 3: `· 🔗 after row 2`; row 4: `· 🔗 after row 3` | delete clause | Statuses: all 📋 |
| 21 | layers spec §9 | 567 | "…and together they are row 4 of globe spec §9, which lands with row 4 here." | globe 4 with layers 4 | on **row 4 of globe spec §9**: `· 🔗 with row 4 of layers spec §9` | "Together they are row 4 of globe spec §9." | UMBRELLA, harmless: globe row 4 is "by rows 1 to 4 of layers spec §9" and lands with the last of them, so through #1 globe row 5 waits on all four layers rows. Left in place, the sentence would trip the guard. Statuses: both 📋 |
| 22 | layers spec §9 | 569 | "Row 5 of heights spec §9 lands with row 2." | heights 5 with layers 2 (same as #6) | none new: #6 writes it on heights row 5 | delete sentence | Today written on both specifications. Left in place, the sentence would trip the guard and count as an ordering written twice |
| 23 | layers spec §9 | 569-570 | "Row 2 needs a renderer in CI, which the image tests already have." | layers 2 / a CI renderer | none | stays | NOT-A-ROW |
| 24 | layers spec §4.9 | 448-449 | "…is heights spec §8 item 3, owed by row 5 of heights spec §9, which lands with row 2 here." | heights 5 with layers 2 (same as #6) | none new | Could stay. Optional rewording: "…owed by row 5 of heights spec §9, which row 2 here builds." | ELSEWHERE (§4.9). Not moved by §4.7 |
| 25 | layers spec §10 | 583 | "Heights spec §8 item 3, and row 5 of heights spec §9, which lands with row 2 here." | heights 5 with layers 2 (same as #6) | none new | Could stay (References) | ELSEWHERE (§10). Not moved by §4.7 |
| 26 | crs spec §10 | 796 (scope, row 2) | "The globe model, units, heights and layers, by rows 1 to 5 of globe spec §9" | umbrella (no ordering word) | receives #3's `· 🔗 with row 5 of globe spec §9`, and #28's `· 🔗 after row 1` | (scope cell) | UMBRELLA: "by" is not one of the four relations, and the guard passes it |
| 27 | crs spec §10 | 808 (scope, row 14) | "Today's seam and transform path deleted once every class has landed, and whether an unsupported method has an escape hatch decided" | crs 14 after each class row | row 14: "Today's seam and transform path deleted, and whether an unsupported method has an escape hatch decided · 🔗 after row 6 · 🔗 after row 7 · 🔗 after row 8 · 🔗 after row 9 · 🔗 after row 10 · 🔗 after row 11" | (scope cell; reason in #29) | AMBIGUOUS: "every class" covers classes 1 to 6 (rows 6 to 11, as §4.3 line 377 says), and class 0 is row 4. `after row 4` follows transitively from #28, so it is left out here. Rows 12 and 13 are not classes and are left out. Statuses: all 📋 |
| 28 | crs spec §10 | 811-812 | "Rows 1 to 4 come first and in order, since everything else stands on them." | crs 2 after 1, 3 after 2, 4 after 3; rows 5-13 after 4 | row 2: `· 🔗 after row 1`; row 3: `· 🔗 after row 2`; row 4: `· 🔗 after row 3`; rows 5 to 13: `· 🔗 after row 4` each (row 14 transitively through #27) | "Everything else stands on rows 1 to 4." | UMBRELLA, the case order spec §4.7 names. With #3 (crs 2 `with` globe 5), a literal move holds crs row 3, the cutting engine, and so rows 4 to 14, behind globe row 5. Through #1, #21 and #5, that also puts them behind layers rows 1 to 4 and heights row 4. Order spec §4.7 says to rewrite the sentence before it moves. One reading of what was meant: rows 3 and 4 need only the landed globe model (globe row 2) and row 1, so row 3 `after row 1` and row 2 left unordered against rows 3 to 14. The maintainer to choose. AMBIGUOUS too: does "everything else" include row 15, a 💡 candidate? A candidate after a not-started row passes item 6 of §4.5 either way. Statuses: row 1 ✅ 2026-10-26 #2721, rows 2 to 14 📋, so no contradiction |
| 29 | crs spec §10 | 812-814 | "From row 4, a method whose class has not landed keeps today's path, and row 14 deletes that path once the last class row has landed (§2 decision 12)." | crs 14 after class rows (same as #27) | none new: #27 | "From row 4, a method whose class has not landed keeps today's path, which row 14 deletes (§2 decision 12)." | Duplicate of #27. The guard passes it as written ("the last class row" carries no number) |
| 30 | crs spec §10 | 814-815 | "Rows 5 to 13 may then proceed in any order that suits the early adopters, and each lands with its tests, its image baselines and a towncrier fragment." | no order among rows 5-13; "then" means after row 4 (#28) | none new | "Rows 5 to 13 may land in any order that suits the early adopters, and each lands with its tests, its image baselines and a towncrier fragment." | none |
| 31 | crs spec §10 | 816-818 | "Row 15 is a candidate, since the regions design is out of scope (§9), and the row is where the open item it would settle waits." | candidate trigger | none | stays | NOT-A-ROW |
| 32 | positions spec §9 | 407-408 | "Row 1 brings the test of §4.1, which the others use, so rows 2 to 5 each need row 1, row 6 needs none, and row 7 needs row 5." | positions 2, 3, 4, 5 after 1; 7 after 5 | rows 2, 3, 4, 5: `· 🔗 after row 1` each; row 7: `· 🔗 after row 5` | "Row 1 brings the test of §4.1, which rows 2 to 5 use, and row 6 does not." (row 7's reason is its own scope: it restores the speed row 5 cost) | Statuses: r1 ✅ 2026-11-06 #2889, r2 ✅ 11-07 #2893, r3 ✅ 11-08 #2899, r4 ✅ 11-09 #2908, r5 ✅ 11-09 #2912, r7 ✅ 11-09 #2922. Rows 5 and 7 landed on the same day, so the check passes on dates alone |
| 33 | positions spec §9 | 408 | "{issue}`2849` closes when rows 1 and 2 have landed." | an issue / rows 1, 2 | none | stays | NOT-A-ROW |
| 34 | bench spec §9 | 360-361 | "Rows 2 and 3 need row 1, and not each other." | bench 2, 3 after 1 | rows 2 and 3: `· 🔗 after row 1` each | "Rows 2 and 3 do not need each other." (or delete) | Statuses: all ✅ 2026-11-10 (#2925, #2927, #2936), so the check passes on dates alone |
| 35 | floors spec §9 | 453-454 | "Row 1 waits on {issue}`2968`." | an issue | none | stays | NOT-A-ROW |
| 36 | floors spec §9 | 454-455 | "Row 2 needs row 1, so that the floors it copies to `pip` have been shown to hold." | floors 2 after 1 | row 2: `· 🔗 after row 1` | "The floors row 2 copies to `pip` are those row 1 has shown to hold." | Statuses: r1 ✅ 2026-11-16 #2974, r2 ✅ 2026-11-17 #2985 |
| 37 | floors spec §9 | 455-456 | "Row 3 needs row 2, since `uv`'s lowest resolution means nothing until every line has a floor," | floors 3 after 2 | row 3: `· 🔗 after row 2` | "`uv`'s lowest resolution, which row 3 runs, means nothing until every line has a floor." | Statuses: r3 📋, r2 ✅ |
| 38 | floors spec §9 | 456 | "…and row 4 needs row 3, whose composite action it calls." | floors 4 after 3 | row 4: `· 🔗 after row 3` | "Row 4 calls the composite action of row 3." | Statuses: both 📋 |
| 39 | floors spec §9 | 456-457 | "Row 5 needs row 1 alone." | floors 5 after 1 | row 5: `· 🔗 after row 1` | delete sentence | Statuses: r5 📋, r1 ✅ |
| 40 | items spec §8 | 551 (scope, row 1) | "…citations of items and rows with their anchors (delivering row 5 of citation spec §9), …" | umbrella: items 1 delivers citation 5 | none here: the `with` goes on citation row 5 (#54) | (scope cell unchanged) | UMBRELLA. "delivering" is not a relation, and the guard passes it |
| 41 | items spec §8 | 560-561 | "Rows 2 to 5 each need row 1, and can land in any order after it." | items 2, 3, 4, 5 after 1 | rows 2, 3, 4, 5: `· 🔗 after row 1` each | "Rows 2 to 5 can land in any order." | Statuses: r1 ✅ 2026-11-02 #2807, r2 ✅ 11-03 #2846, r3 ✅ 11-04 #2850, r4 ✅ 11-04 #2873, r5 ✅ 11-03 #2826 |
| 42 | items spec §8 | 561-562 | "Rows 3 to 5 each raise the issues their specifications' items lack, and need {user}`bjlittle`'s judgement on the row that owes each item (§3.10)." | a person's judgement | none | stays | NOT-A-ROW |
| 43 | items spec §8 | 562-563 | "Row 7 follows row 6, as the check that settling §7 item 11 called for (§3.4)." | items 7 after 6 | row 7: `· 🔗 after row 6` | "Row 7 is the check that settling §7 item 11 called for (§3.4)." | "follows" is not in §4.2's list, so the guard would not catch this sentence if it stayed. Statuses: r6 ✅ 2026-11-04 #2878, r7 ✅ 2026-11-05 #2879 |
| 44 | items spec §8 | 563-564 | "Row 8 extends row 7's check to every ordering phrase." | items 8 / items 7? | none proposed (row 7 has landed, so `after row 7` would be true but say nothing) | stays | AMBIGUOUS: it states a scope, not plainly an order. Row 8's `with` is written on order spec row 2 (#59), so items row 8 must not write it again |
| 45 | items spec §3.4 | 239-240 | "row 5 of heights spec §9 is scoped *landing with row 4 of globe spec §9*, and the two land in one pull request, as row 6 of ledger spec §8 and row 5 of §8 did in {pull}`2826`." | heights 5 with globe 4 (stale); ledger 6 with items 5 (a past fact) | none proposed | Order spec §3.2 counts §3.4 as describing orderings in general, so §4.7 does not move it | ELSEWHERE; AMBIGUOUS. (a) The example is **stale**: heights row 5 now lands with row 2 of layers spec §9 (#6). (b) It records a landed `with` that neither roadmap writes: ledger row 6 and items row 5 both ✅ 2026-11-03 #2826. A `· 🔗 with row 6 of ledger spec §8` on items row 5 would hold, but it reads as two rows that happened to share a PR, not a dependency. The maintainer to say. The italic old form is not code, but §3.4 is outside the guard's reach |
| 46 | ledger spec §8 | 501 | "Rows 2 to 9 each need row 1." | ledger 2-9 after 1 | rows 2 to 9: `· 🔗 after row 1` each | delete sentence | Statuses: r1 ✅ 2026-10-31 #2786; r2 ✅ 10-31 #2789 and r3 ✅ 10-31 #2792 (same day, so they pass on dates alone); r4 ✅ 11-01 … r9 ✅ 11-08 |
| 47 | ledger spec §8 | 503-504 | "Rows 2 and 3 need nothing else, and can land in either order." | no ordering | none | stays | none (the guard passes "need nothing") |
| 48 | ledger spec §8 | 504-505 | "Once row 2 has merged, `status references` becomes a required check, a repository setting {user}`bjlittle` changes (§3.7)." | a repository setting after ledger 2 | none | stays in meaning but **reworded**, or the guard trips ("Once row 2"): "`status references` became a required check when {pull}`2789` merged, a repository setting {user}`bjlittle` changes (§3.7)." | NOT-A-ROW |
| 49 | ledger spec §8 | 505-507 | "Rows 4 to 6 can land in any order after row 1, but best after that change: a sign-off they record before it is held by review alone, and is checked against GitHub by the nightly run." | ledger 4, 5, 6 after 1 (same as #46); "best after" the setting | none new (#46) | "Rows 4 to 6 can land in any order, but best once `status references` is required: a sign-off they record before it is held by review alone, and is checked against GitHub by the nightly run." | AMBIGUOUS: "best after that change" is a soft preference against a setting, not a row. It should not become `after row 2`. NOT-A-ROW for that half |
| 50 | citation spec §9 | 440 | "Rows 2 to 4 each build on row 1." | citation 2, 3, 4 after 1 | rows 2, 3, 4: `· 🔗 after row 1` each | delete sentence | "build on" is not in §4.2's list. Statuses: r1 ✅ 2026-10-26 #2735, r2-r4 ✅ 2026-10-27 (#2738, #2740, #2745) |
| 51 | citation spec §9 | 440-441 | "Row 2 follows it, because the next change to cite a specification from code fails the ceiling test until row 2 lands." | citation 2 after 1 (same as #50) | none new | "Row 2 was urgent, because the next change to cite a specification from code failed the ceiling test until it landed." | AMBIGUOUS, mildly: "follows it" could be read as "comes next", ahead of rows 3 and 4, but #52 says row 3 may come before row 2, so it is just `after row 1` |
| 52 | citation spec §9 | 441-442 | "Row 3 needs only row 1, so it can come before or after row 2." | citation 3 after 1 (same as #50); no order between 2 and 3 | none new | "Rows 2 and 3 may land in either order." | As written, the sentence would trip the guard ("after row 2") although it is no ordering |
| 53 | citation spec §9 | 442 | "Row 4 needs row 2." | citation 4 after 2 | row 4: `· 🔗 after row 2` | delete sentence | Statuses: r2 ✅ 2026-10-27 #2738, r4 ✅ 2026-10-27 #2745 (same day, so it passes on dates alone) |
| 54 | citation spec §9 | 447-448 | "Row 5 landed before it fired, with row 1 of items spec §8, and the test retired with it." | citation 5 with items 1 | row 5: `· 🔗 with row 1 of items spec §8` (the delivered row writes it, as heights row 5 does) | "Row 5 landed before it fired, and the test retired with it." | UMBRELLA, harmless (items row 1 is "delivering row 5 of citation spec §9", #40). Statuses: both ✅ 2026-11-02 #2807. Whether the guard catches "landed before it fired, with row 1" depends on the regex |
| 55 | citation spec §4.7 | 349-350 | "Rows 2 and 4 of docs spec §4 land with the rows of §9 that build them." | docs 2, 4 with citation 2 | if moved: docs row 2 `· 🔗 with row 2 of citation spec §9`; docs row 4 `· 🔗 with row 2 of citation spec §9` | could stay (it describes what changed in the parent) | ELSEWHERE (§4.7): outside the eleven roadmaps of order spec §3.2, so §4.7 does not move it. AMBIGUOUS: "the rows of §9 that build them" names no row. Read from the statuses, it is row 2 (all three ✅ 2026-10-27 #2738) |
| 56 | citation spec §4.7 | 351 | "Row 3, the integrity hook, is marked landed with row 1 there" | docs 3 with docs 1 | if moved: docs row 3 `· 🔗 with row 1` | could stay | ELSEWHERE (§4.7); the same fact as #57. Statuses: both ✅ 2026-10-07 #2573 |
| 57 | docs spec §4 (note above the table) | 515-516 | "Row 3 is the conventions test of row 1, already in place, so it is marked landed with it." | docs 3 with 1 | optional: row 3 `· 🔗 with row 1` | stays (a status explanation) | AMBIGUOUS: it records why row 3 was marked landed, not a dependency. It sits under the roadmap heading, and the guard passes it ("with it"). Statuses consistent (#2573) |
| 58 | docs spec §4 | 554 | "**Rows 2 to 4** activate together, when the corpus outgrows review." | candidate trigger among docs 2-4 | none | stays (a trigger, docs spec §2 decision 6) | NOT-A-ROW; CONTRADICTS if moved literally as `with`: row 3 ✅ 2026-10-07 #2573, while rows 2 and 4 ✅ 2026-10-27 #2738 |
| 59 | order spec §9 | 331 (scope, row 2) and 333-335 | scope "… · 🔗 after row 1 · 🔗 with row 8 of items spec §8"; prose "Row 1 keeps every check reading what it moves, so it is safe to land alone. Row 2 is row 8 of items spec §8, which owes items spec §7 item 15, so the two land in one pull request." | order 2 after 1; order 2 with items 8 | already in form; nothing moves | prose stays (the guard passes it) | AMBIGUOUS: the `with` sits on the row that *builds* the work. The precedents (#6 heights row 5 with layers row 2, #54 citation row 5 with items row 1) put it on the row that *owes* it, here items row 8. Either is one ordering, and the check reads both directions. Worth a sentence in §4.3, or a move to items row 8, so that the rule of which row writes it is the same everywhere |
| 60 | typing spec §4 | 418 | "Rows 8 to 11 wait on releases upstream, so each is a `candidate` (items spec §2 decision 8)" | upstream releases | none | stays | NOT-A-ROW |
| 61 | zlevel spec §4 | 185-187 | "The image baselines live in `bjlittle/geovista-data`, so row 1 lands there first: the new images are released there, and the pull request here raises `DATA_VERSION`…" | another repository's release | none | stays | NOT-A-ROW |

### What the cells would read after the move (entries 1 to 61, without the ELSEWHERE options)

- **globe spec §9**: row 2 `· 🔗 after row 1 · 🔗 with row 2 of scene spec §9`; row 3
  `· 🔗 after row 2 · 🔗 with row 2 of heights spec §9 · 🔗 before 0.6`; row 4
  `· 🔗 after row 3 · 🔗 with row 4 of layers spec §9`; row 5 `· 🔗 after row 4`.
- **heights spec §9**: row 2 `after row 1`; row 3 `with or after row 3 of globe spec §9`;
  row 4 `before row 5 of globe spec §9`; row 5 `with row 2 of layers spec §9`.
- **scene spec §9**: row 1 `before 0.6`; row 2 `after row 1 · 🔗 before 0.6`; row 3
  `after row 5 of globe spec §9`.
- **layers spec §9**: rows 2, 3, 4 `after` the row before.
- **crs spec §10** (literal, pending the rewrite of #28): row 2 `after row 1 · 🔗 with row 5 of
  globe spec §9`; row 3 `after row 2`; row 4 `after row 3`; rows 5 to 13 `after row 4`;
  row 14 `after` rows 6 to 11.
- **positions spec §9**: rows 2 to 5 `after row 1`; row 7 `after row 5`.
- **bench spec §9**: rows 2, 3 `after row 1`.
- **floors spec §9**: row 2 `after row 1`; row 3 `after row 2`; row 4 `after row 3`; row 5
  `after row 1`.
- **items spec §8**: rows 2 to 5 `after row 1`; row 7 `after row 6`.
- **ledger spec §8**: rows 2 to 9 `after row 1`.
- **citation spec §9**: rows 2, 3, 4 `after row 1`; row 4 also `after row 2`; row 5 `with row 1
  of items spec §8`.
- Optional, from ELSEWHERE: **docs spec §4** rows 2 and 4 `with row 2 of citation spec §9`,
  row 3 `with row 1`.

That is 67 orderings in cells (19 of them in crs spec §10), 3 of them `before 0.6`, plus
3 optional ones in docs spec. None forms a cycle, and none puts a `not started` row after or
with a `candidate`. Checked against today's statuses, none contradicts (entries #8 and #16 do
only if the umbrella is moved literally, and #58 only if the trigger is moved).

### A.2 Phrases That Look Like Orderings

The guard of order spec §4.5 item 4 reads only (a) the prose under a roadmap, up to the next
heading, and (b) a Scope cell before its first `· 🔗`. It fires on a word from §4.2's last
column, or *waits on*, followed by a cited row, and it skips code. So the phrases in **2.1**
are the ones that matter. Whether a bare *before* / *after* / *once* / *with* counts, or only
the full phrases (*lands before row N*, *lands with row N*, *once row N lands*), is up to row 1's
regex. Each entry says which reading trips it.

#### A.2.1 Inside the guard's reach

| Spec | Line | Text | Trips? | Suggested rewording |
|---|---|---|---|---|
| positions spec §9, row 7 scope | 404 | "so `geodesic.line` builds as fast as before row 5 (§8 item 5)" | **Yes**, if a bare *before* + row counts. Order spec §3.2 already names this phrase as no ordering | "so `geodesic.line` builds as fast as it did before {pull}`2912` (§8 item 5)" |
| citation spec §9 | 441-442 | "so it can come before or after row 2" | **Yes** ("after row 2") | "Rows 2 and 3 may land in either order." (#52) |
| ledger spec §8 | 504 | "Once row 2 has merged, `status references` becomes a required check" | **Yes** ("Once row 2") | "`status references` became a required check when {pull}`2789` merged, …" (#48) |
| docs spec §4 | 565-566 | "The citation links design built them, and the ceiling retired with row 2 there." | Only if a bare *with* + row counts. Note too that the bare `row 2` reads as docs spec's own row 2 under order spec §2 decision 4, while it means citation spec's | "…, and the ceiling retired in {pull}`2738`." |
| citation spec §9 | 447 | "Row 5 landed before it fired, with row 1 of items spec §8" | This one is a real ordering (#54). It trips only if *landed … with* across a clause counts | moved by #54 |
| layers spec §9 | 574-575 | "A `zlevel` that a user gives keeps its meaning until row 5 of globe spec §9 removes it" | No (*until* is not in the list) | none needed; if *until* is ever added: "…keeps its meaning while `zlevel` lasts, which row 5 of globe spec §9 removes" |
| layers spec §9 | 568 | "on the globe it arrives in row 2 with the clip" | No | — |
| heights spec §9 | 448-450 | "Until it lands, a scene scales … as row 2 of scene spec §9 left it." | No. Unrelated: "Until it lands" is stale, since row 2 ✅ 2026-11-11 | — |
| crs spec §10 | 813-814 | "row 14 deletes that path once the last class row has landed" | No (no number), but it is a duplicate of #27 | reworded in #29 |
| crs spec §10 | 814 | "Rows 5 to 13 may then proceed in any order" | No | #30 |
| floors spec §9 | 457 | "Whichever of rows 3 and 5 lands first creates `ci-floors.yml`." | No (the word follows the rows) | — |
| positions spec §9 | 408 | "{issue}`2849` closes when rows 1 and 2 have landed." | No (*when*) | — |
| items spec §8, row 7 scope | 557 | "A row landing with another specification's row checked to land with it" | No (no number), but a loose *landing with … row* regex would catch it | if needed: "The check that a row landing with another lands in its pull request, §7 item 14" |
| items spec §8, row 6 scope | 556 | "the open items found while landing rows 1 and 5" | No (*landing* without *with*), unless *landing* alone is matched | "the open items found as rows 1 and 5 landed" |
| items spec §8, row 3 scope | 553 | "with the `candidate` rows they wait on" | No (no number) | — |
| citation spec §9, row 2 scope | 434 | "The transform and the output check, which land together" | No | — |
| ledger spec §8 | 503, 509-511 | "Rows 2 and 3 need nothing else"; "so it lands on its own" (rows 7, 8) | No | — |
| scene spec §9, row 3 scope | 527 | "The release after which a retired field is refused" | No (*after which*); it stays in the scope after #14 | — |
| scene spec §9 | 530-531 | "and after {issue}`2756`" | No (an issue) | — |
| heights spec §9 | 455 | "Rows 3 to 5 each wait on a row of globe spec §9." | No (no number), but SUMMARY, deleted by #9 | — |
| globe, crs, items scopes | 655-657, 796, 551 | "by rows 1 and 2 of scene spec §9", "by rows 1 to 5 of globe spec §9", "(delivering row 5 of citation spec §9)" | No (*by* and *delivering* are no relation) | — (UMBRELLA, #1, #26, #40) |
| typing spec §4, row 12 scope | 408 | "The trigger tests of rows 8 to 11 hardened" | No. It must **not** be moved as `after row 8`…`after row 11`: those rows are 💡 candidates and row 12 is 📋, which item 6 of §4.5 refuses | — |
| typing spec §4 | 418, 424-426, 430 | "wait on releases upstream"; "waits on the annotations of `Camera.zoom`"; "Item 5 waits on the floor"; "the row lands with the last" | No | — |
| globe spec §9 | 669-673 | "row 6 waits on a scene with heights…"; "rows 7 to 9 each wait on a user"; "before the default could change (§8 item 4)" | No | — |
| layers spec §9, row 7 scope | 563 | "The interim bias of row 4 removed" (💡) | No | — |
| zlevel spec §4 | 186 | "row 1 lands there first" | No | — |
| order spec §9 | 333-335 | "so it is safe to land alone"; "so the two land in one pull request" | No | — |
| bench spec §9 | 361 | "and not each other" | No | — |

**Gaps in the guard's word list.** Sentences written today use words outside §4.2's last
column: *need* (plural: bench 361, positions 408, items 560, ledger 501), *follows row N*
(items 562), *build on row N* (citation 440), *come first and in order* (crs 811), *can land
in any order after row N* (ledger 505), *activate together* (docs 554). The move deletes all of
them, but a new specification could write *follows row 3* or *builds on row 1* again, and the
guard would not catch it unless row 1 adds them.

#### A.2.2 Outside the guard's reach (not under a roadmap, not a scope): no trip, listed for completeness

- **positions spec** 233 (§4.7) "which it took from the latitude alone before row 5"; 383-391
  (§8 item 5) "about twice as slowly as before row 5", "0.16 s before row 5 and 0.36 s after
  it", "as fast as before row 5". Measurements.
- **heights spec** 36 (§1), 68 (§2 decision 6), 295-296 (§4), 308, 323 (§5): "until row 5 of
  globe spec §9 …"; 301 (§4) "{user}`bjlittle` plans to redesign `to_structured_grid` once
  row 1 lands ({issue}`2774`)". Work against a row, NOT-A-ROW, an issue.
- **scene spec** 245-247 "Every height is 0 until row 3 of globe spec §9"; 255 "stay until
  row 5 of globe spec §9"; 257 "Before row 2 it lifted a mesh"; 394-395 "until row 5 of globe
  spec §9 replaces `zlevel`"; 274 (§4.3) "The round trip of crs spec §6 lands with row 1 of §9"
  (a test, not a row).
- **crs spec** 629-630 (§6) "The test … lands with row 2 of globe spec §9, the first row to put
  something new on a mesh" (a test, not a row). This **disagrees** with scene 274, which says the
  same round trip lands with scene row 1 (#2761, not #2766). 742 (§8 item 12) "({issue}`2753`),
  which no longer has to land with row 2 of globe spec §9"; 747-748 (§8 item 13) "settled before
  row 5 of §10 lands, which §2 decision 13 also waits on".
- **zlevel spec** 15 (banner) "stays current until row 5 of globe spec §9 lands"; **globe spec**
  26 (banner) "this specification replaces when row 5 of §9 lands"; 647 (§8 item 13) "Once row 5
  removes `zlevel`".
- **ledger spec** 287-288 (§3.6) "Each of rows 4 to 6 shortens the list and row 6 empties it".
  This hints that row 6 lands last of the three, while §8 says "any order". It came true by date.
  316 (§3.7) "Once rows 1 and 2 have merged, {user}`bjlittle` adds `status references`"
  (NOT-A-ROW); 435 (§5) "the form until row 8 of §8".
- **items spec** 153 (§3.1) "deliver row 5 of citation spec §9 before its trigger"; 215-216
  (§3.3) "Row 1 of §8 creates it, a repository change {user}`bjlittle` confirms first"; 242
  (§3.4) "row 15 of crs spec §10 waits on the regions design"; 451-452 (§7 item 3) "fails a row
  that had landed before it"; 499-507 (§7 item 11) "heights spec §8 item 3 waits on row 4 of
  globe spec §9" (stale, resolved); 528-529 (§7 item 14); 536-544 (§7 item 15), which describe
  orderings in general.
- **floors spec** 137 (§2) "The maintainer adds the check to the branch protection of `main` once
  row 1 of §9 lands" (NOT-A-ROW); 275 (§4.2) "{issue}`2968` is fixed first" (restates #35);
  279-281 (§4.2) "A row that lands before row 2 raises the `pixi` floor alone": the exact phrase
  *lands before row 2*, but a condition, not an ordering, so it would trip if the guard were ever
  widened. Rewording: "Until row 2 lands, a row raises the `pixi` floor alone". 402-405 (§6) "Row 1
  of §9 lands once the `tests floors` check has passed"; 494 (§11) "added once row 1 landed".
- **bench spec** 85-86 (§2 decision 5) "no ceilings until a comparison with the base is built
  (row 4 of §9)".
- **checks spec** 44-45 "`CEILING`, the trigger of rows 2 to 4 of docs spec §4, had before it".
- **typing spec** 681 (§10) "went live in row 1 of §4 ({pull}`2565`), before any module was
  corrected"; §8 items 6, 8, 10 and 13 "wait on the same `pyvista` release" (NOT-A-ROW).
- **docs spec** 473 (§3.8) "A candidate waits on a trigger (§4)".
- **order spec** §1, §3.1, §3.2, §4.2, §4.3 and §4.7 quote the old forms in italics, not code.
  They pass, being outside the guard's reach.

### A.3 Side Observations

- **typing spec §4 has four columns**, `| # | Scope | Lines | Status |` (line 393), where order
  spec §2 decision 1 and §3.3 speak of the three-column header. The grammar of row 1 has to find
  the Scope cell by its header, not by its position.
- **Stale cross-references** a move will touch: items spec §3.4 (239) and §7 items 11 and 14
  still cite heights row 5 against row 4 of globe spec §9; it now lands with row 2 of layers
  spec §9.
- **Umbrella rows** (globe 2, 3, 4; crs 2; items 1 delivering citation 5; order 2 being items 8)
  are the sources of every UMBRELLA flag above. Order spec §4.3 says nothing about which side of
  an umbrella pair writes the `with`. The texts write it on the umbrella or the owing row
  (globe 2/3/4, crs 2, heights 5, citation 5), except order spec row 2 (#59).

A Codex review then found two more, each fixed with a test that failed first: a `before` naming its own roadmap's row in full (`row 2 of §9`, `row 2 of layers spec §9`) passed where the bare form was refused, so the same roadmap is read from the resolved anchor; and emphasis or a link around the word or the row hid an ordering from the guard, which now reads the inline markdown's text with code left out (`plain`).

# Open Items, Row 2: The Report's Roadmap and Open Items Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of items spec §8. For each specification, `verification-report` shows
its roadmap and its open items around its ledger, and reports two more findings: an item
on its last move, and an item owed by a row `in progress`.

**Architecture:** `.github/scripts/verification_report.py` already reads each
specification with the conventions test's parsers and the citation grammar. It gains a
Roadmap table from `grammar.rows`, an Open Items table from `grammar.items`, and two
findings, with each 🎯 resolved by the conventions test's `own_row`, so the report and the
suite read an item's row the same way. No new parser is written.

**Tech Stack:** Python 3.13+, pytest, pixi tasks.

**Spec:** `docs/src/developer/specs/2026-11-02-open-items-design.md` (items spec), §2
decision 12 and §3.9, with §3.5 and §3.6 for what a move and a landing mean.

## Global Constraints

- Items spec §3.9: "the Roadmap first, each row with its status, and Open Items last, each item with its state, its 🎯 and the number of times it has moved."
- Findings gain exactly two (items spec §3.9): "an item on its last move, which must settle or graduate when its row lands" and "an item owed by a row `in progress`, which that row's pull request must answer."
- "A gap the suite or GitHub already refuses is not repeated as a finding": no finding for an item with three ⬅️, for one owed by a landed row, or for a 🎯 that names no row of its own roadmap, as the suite refuses each.
- The report stays a view, never a gate (items spec §2 decision 12, ledger spec §2 decision 11): exit 0 whatever it finds, and exit 2 only as it already does.
- Status and scope cells are written through the existing `markdown()`, so `{pull}`, `{issue}` and `{user}` read as GitHub Markdown in a job summary.
- Python under `tests/` builds its emoji and section signs by name, as `tests/test_verification_report.py` already does.

## Rulings Made in Planning

- **Order.** Items spec §2 decision 12 lists "Decisions, Roadmap, Verification and Open Items", the order a specification is read in. The report gives each decision its verification state beside it, so the two can't be split around the roadmap. This plan follows §3.9, which is the design: Roadmap, then the ledger (summary line and decisions), then Open Items. If review reads decision 12 as an order to follow, the fix is to move one block.
- **Scope shown.** §3.9 asks for "each row with its status". The Roadmap table also shows the Scope, since a row number alone tells a reader nothing.
- **Last move.** An item is on its last move when it carries exactly two ⬅️ (items spec §3.6). With three, the suite already refuses it.
- **Item names.** A finding names an item as it would be cited, `items spec §7 item 11`, and an item's section is the number of its Open Items heading.

## Review Focus

1. **A specification with no roadmap or no Open Items section** (the `lone spec` fixture): it prints `No roadmap.` and `No open items.`, and doesn't crash. Test in Task 1.
2. **An item still in the grammar of docs spec §3.6** (`typing`, `crs` until rows 3 and 4): it is listed with `no state` and `—` for 🎯, and never makes a finding. Test in Task 1.
3. **Gaps the suite already refuses**: an item with three ⬅️, or one owed by a landed row, makes no finding. Test in Task 2.
4. **A 🎯 that names another specification's row, or no row**: `own_row` returns a reason string, and the item makes no finding and doesn't crash. Test in Task 2.
5. **A Scope cell carrying `{issue}` and an escaped pipe `\|`**: the role reads as `#N`, and the pipe stays escaped, so the table keeps its columns. Test in Task 1.

---

### Task 1: The Roadmap and Open Items Tables

**Files:**
- Modify: `.github/scripts/verification_report.py`
- Test: `tests/test_verification_report.py`

**Interfaces:**
- Consumes: `grammar.rows(text) -> list[Row]` (`.section`, `.row`, `.scope`, `.status`), `grammar.items(text) -> list[Item]` (`.number`, `.state`, `.title`, `.owed`, `.moves`), `grammar.headed(text)`, `grammar.OPEN_ITEMS`, the existing `markdown(status)`.
- Produces: `_roadmap(text: str) -> list[str]` and `_open_items(text: str) -> list[str]`, the Markdown lines of each block; `_items_section(text: str) -> str | None`, the number of the Open Items heading, which Task 2 uses to name an item.

- [ ] **Step 1: Extend the fixture and write the failing tests.** Append to the `demo spec` of the `repo` fixture, after its Verification table so that no earlier line moves:
  - `(demo-spec-5)=` / `## 5. Open Items`, with five items built from the part emojis by name (`FOUND`, `OWED`, `MOVED`, `TICKET` beside the states). Item 1 is ❓ Open, owed by `row 2 of §6`. Item 2 is ⏭️ Deferred, with two ⬅️, owed by `row 3 of §6`. Item 3 is ⏭️ Deferred, with three ⬅️, owed by `row 3 of §6`. Item 4 is ❓ Open, owed by `row 1 of §6`. Item 5 is 🏁 Resolved.
  - `(demo-spec-6)=` / `## 6. Roadmap`, a `| # | Scope | Status |` table: row 1 is `✅ landed (2026-01-01, {pull}`1`)`, row 2 is `in progress`, row 3 is `not started`, row 4 is `candidate`. Row 3's scope reads ``The work of {issue}`7`, with `a \| b` kept``.

  Then write these tests:
  - `test_report_shows_each_roadmap_row_with_its_status` (docstring cites `Holds items spec §2 decision 12.`): the demo section holds `### Roadmap` before the summary line, a `| # | Scope | Status |` table, the row `| 1 | … | ✅ landed (2026-01-01, #1) |`, and row 3's scope as `The work of #7, with `a \| b` kept` (Review Focus 5).
  - `test_report_shows_each_open_item_with_its_state_owed_row_and_moves` (cites decision 12): `### Open Items` comes after the last decision, as a `| Item | State | Owed by | Moves |` table, with item 2's row `| 2: <title> | ⏭️ Deferred | row 3 of §6 | 2 |` and item 5's row showing `—` for Owed by and `0` for Moves.
  - `test_a_specification_without_a_roadmap_or_items_says_so`: the `lone spec` section prints `No roadmap.` and `No open items.` (Review Focus 1).
  - `test_an_item_in_the_old_grammar_has_no_state`: a spec whose Open Items entry reads `1. **Open** — **Old.** Text.` lists it as `no state` with `—` for Owed by (Review Focus 2).
- [ ] **Step 2: Run** `pixi run --frozen -e test-py313 python -m pytest tests/test_verification_report.py -q`. Expected: the four new tests fail, and the old ones still pass.
- [ ] **Step 3: Implement.** In `report()`, under each specification's heading, write `### Roadmap` and `_roadmap(text)` first, then the existing summary and decisions, then `### Open Items` and `_open_items(text)`. Only the rows of the specification's own Roadmap section are shown, so `_roadmap` keeps the `grammar.rows` whose `section` is the number of the heading titled `Roadmap`. It writes them as a table, each cell through `markdown()`. `_open_items` writes one row per item: `<number>: <title>`, the state (or `no state`), `item.owed` (or `—`), and `len(item.moves)`. Each block writes its `No …` line when it has nothing to show.
- [ ] **Step 4: Run** the module on `test-py313` and `test-py314`. Expected: PASS. `ruff` is clean.
- [ ] **Step 5: Commit**: `ci: show each specification's roadmap and open items in the report`.

### Task 2: The Two Findings

**Files:**
- Modify: `.github/scripts/verification_report.py`
- Test: `tests/test_verification_report.py`

**Interfaces:**
- Consumes: `_items_section` (Task 1); `conventions.own_row(path, text, cited, names) -> Row | str`; `grammar.OPEN`, `grammar.DEFERRED`.
- Produces: `_item_findings(path: Path, text: str, prefix: str, names: Namespace) -> list[str]`, appended to `findings` in `report()`.

- [ ] **Step 1: Write the failing tests** against the Task 1 fixture:
  - `test_an_item_on_its_last_move_is_a_finding` (cites decision 12): Findings hold `demo spec §5 item 2 is on its last move: when row 3 of §6 lands, it must settle or graduate.`
  - `test_an_item_owed_by_a_row_in_progress_is_a_finding` (cites decision 12): Findings hold `demo spec §5 item 1 is owed by row 2 of §6, which is in progress: its pull request must answer it.`
  - `test_a_gap_the_suite_refuses_is_not_repeated`: Findings name neither item 3 (three ⬅️) nor item 4 (owed by the landed row 1), nor item 5 (Review Focus 3).
  - `test_an_item_owed_by_another_specifications_row_makes_no_finding`: an Open item owed by `row 1 of lone spec §3`, or by `row 9 of §6`, adds no finding, and the report exits 0 (Review Focus 4).
- [ ] **Step 2: Run** the module. Expected: the four new tests fail.
- [ ] **Step 3: Implement** `_item_findings`. For each ❓ Open or ⏭️ Deferred item with an `owed`, it resolves the row with `own_row` and skips the item when that returns a `str`. It writes the last-move finding when the item has exactly two ⬅️ and its row hasn't landed. It writes the in-progress finding when the row's status starts with `in progress`. Each finding is written exactly as Step 1 gives it, with the section from `_items_section` and the section sign from `grammar.SECTION`.
- [ ] **Step 4: Run** the module on both Pythons → PASS; then run `pixi run --frozen -e test verification-report` and `verification-report items` → exit 0, each specification showing its roadmap and items.
- [ ] **Step 5: Commit**: `ci: report an item on its last move, and one owed by a row in progress`.

### Task 3: The Documentation

**Files:**
- Modify: `.github/scripts/verification_report.py` (module docstring), `docs/src/developer/specs/index.rst` (**The verification report**), `docs/src/developer/packaging.rst` and `docs/src/developer/testing.rst` (the `verification-report` rows), `pyproject.toml` (the task's `description`)

- [ ] **Step 1:** Say that the report also shows each specification's roadmap and open items, and flags an item on its last move and one owed by a row in progress, citing items spec §3.9 beside ledger spec §3.8. The description becomes `Report each specification's decisions, roadmap and open items, and where each decision is cited`. Keep the grid tables' columns aligned.
- [ ] **Step 2:** Strict incremental docs build (AGENTS.md command, `-W --keep-going`) → `build succeeded`; `pixi run -e geovista pre-commit run --files <changed>` → clean. Humanize the prose.
- [ ] **Step 3: Commit**: `docs: document the report's roadmap and open items`.

### Task 4: The Ledger, and Landing

- [ ] **Step 1:** Items spec §10: decision 12 → `✅ verified (<DATE>, {pull}`<PR>`)` with `tests/test_verification_report.py`. Decision 14 → `✍️ signed off (<DATE>, {user}`bjlittle`, {pull}`<PR>`)`, with the evidence "Checked in review that the specifications index says how to raise, cite, owe, move, settle and promote an item, and that the report shows each, and that the repository checks page explains each failure the item rules raise." Decision 13 stays pending, on rows 3 and 4. Conventions suite → PASS.
- [ ] **Step 2:** `changelog/<PR>.contributor.rst` crediting `:user:`claude``, validated with `.github/scripts/changelog.py`, and humanized.
- [ ] **Step 3:** Full suite with images on `test-py313` and `test-py314`, mypy, the docs build, and `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>`. Everything holds except decision 14's sign-off, until {user}`bjlittle` adds `signed-off`. Final review.
- [ ] **Step 4 (last commit):** Items spec §8 row 2 → `✅ landed (<DATE>, {pull}`<PR>`)`. Redate everything if the merge slips past midnight UTC.

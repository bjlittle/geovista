# Decision Owners: The Row Column Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of owner spec §9: every Verification table gains a `Row` column naming the one row of its roadmap that owns each decision, the suite holds the five checks of owner spec §4.3 with `ledger_complete` retired into them, the GitHub check reads a decision's moves, and every decision of the collection names its owner (owner spec §4.7).

**Architecture:** The shared grammar, `docs/src/_ext/geovista_citations.py`, reads a Verification table by its header, `Decision`, `Row`, `Status`, `Evidence`, and a `LedgerRow` gains its Row cell, read into its owner and its moves by the item's `provenance`. The conventions test gains `ledger_owners`, one function holding the five checks, beside the ledger rules it joins, and drops `ledger_complete`. `check_status_references.py` reads each move as it reads an item's. The build's ledger extension and the test fixtures read cells by header. Then every specification's table gains the column, as Appendices A and B say, and the developer guide follows.

**Tech Stack:** Python, MyST Markdown, Sphinx, pytest.

**Spec:** `docs/src/developer/specs/2026-11-24-decision-owners-design.md` (`owner spec §…`): §2 decisions 1 to 8, 10 and 11, §4.1 to §4.4, §4.7, §4.8 and §9 row 1. Its parent, `docs/src/developer/specs/2026-10-30-decision-ledger-design.md` (`ledger spec §…`): §3.4, §3.5, §3.6, §3.7.

## Global Constraints

- **One owner per decision in force, a row of its own roadmap** (owner spec §2 decisions 3 and 6), written `row N of §M`, then any moves as ` · ⬅️ row K, YYYY-MM-DD, {pull}`P`` (owner spec §4.4).
- **A retired decision may leave its Row cell empty** (owner spec §2 decision 10).
- **A pending decision's Evidence names no row** (owner spec §4.3 item 4).
- **Naming an owner writes no move** (owner spec §4.7).
- **The plans are frozen** (owner spec §7): `docs/src/developer/plans/2026-10-30-decision-ledger-entries.md` keeps its three-column fixture.
- Warnings are errors. Every pixi run is `pixi run --frozen -e geovista …` (a worktree has no `.pixi`, so run the main checkout's environment, `<main>/.pixi/envs/geovista/bin/`); commit through that environment's `pre-commit`. The fragment credits ``(:user:`claude`)`` (workflow rule 4.9); the pull request carries `type: documentation`, `type: testing` and `agentic`.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-24 that owner spec §9 row 1 is bounded (workflow rule 2.7). These calls are mine; he agreed Calls 6, 9 and 10 on 2026-11-24, and Appendix A waits on his review before Task 4.

1. **`LedgerRow.owner: str = ""`, its last field.** A default keeps every existing construction valid. `LedgerRow.owned -> str | None` reads the part with no emoji, and `LedgerRow.moves -> tuple[str, ...]` the parts opening with `⬅️`, both through `provenance`, the item's own reader, so a decision's move and an item's are read alike.
2. **One header, read by name.** `LEDGER_HEADER = ("Decision", "Row", "Status", "Evidence")`. Until Task 4 moves the collection, `ledger` also reads `LEDGER_PREVIOUS = ("Decision", "Status", "Evidence")`, with an empty owner, so every task leaves the suite green; Task 4 drops it. The build's `geovista_ledger` and the report find the Status and Evidence cells by the header's index, not by position.
3. **The five checks are one rule, `ledger_owners`,** in `tests/test_spec_conventions.py`, item 10 of ledger spec §3.6 as this row extends it, with `own_row` reading each owner and each move. Its messages name the decision: `decision 4 is owned by no row`, `… by row 2 of layers spec §9, which is another specification's`, `… is pending, and owned by row 3 of §9, which has landed`, `… is pending, and its Evidence names a row`, `… is verified, and owned by row 6 of §9, which is not started`. A range, or two owners, is `owned by more than one row`.
4. **A move is read as an item's is**: `MOVE`, a date and a pull request, else `carries ⬅️ …, which is not a row, date and pull`; no count is held (owner spec §2 decision 7).
5. **The migration is a throwaway script**, `/tmp/owners.py`, reading Appendices A and B, never committed, as order spec row 1's move was. It adds the column to each table, writes each owner, and strips `row N of §M` and `rows N to M of §K` from each Evidence cell; the ledger spec's §3.4 example table gains the column by hand.
6. **Scene spec §2 decision 8 takes row 1 of scene spec §9. Agreed by {user}`bjlittle` on 2026-11-24.** Row 1 delivered its example, `geovista.Globe` with its radius as a quantity, but the decision was verified by {pull}`2942`, which landed heights spec row 2 and globe spec row 3, where `mesh.gv.height` and `mesh.gv.depth` became quantities. Under owner spec §2 decision 11, a delivery today would add a row to the scene roadmap; this one predates it, and row 1 delivered the promise first.
7. **Row 1 verifies decisions 1 to 8 and 10, and decision 11 is signed off**, since no test can show that a pull request adds a row: {user}`bjlittle` checks in review that the developer guide tells an author to add and land one, and adds `signed-off` (workflow rule 2.5). Decision 9 is row 2's.
8. **Owner spec §4.7's example names the wrong specification**, found while reading the owners: rows 3 to 5 are those of globe spec §2 decision 1, not heights spec §2 decision 1, which is verified. Corrected in place in Task 4, an edit that keeps the meaning.
9. **The owner of a decision spread over several rows is the first row by whose landing the whole decision holds. Agreed by {user}`bjlittle` on 2026-11-24.** Owner spec §4.2 says "the first by which it must hold", which can be read as the first row that exercises any of it. Read so, row 4 of crs spec §10 would own the coverage commitment of crs spec §2 decision 10, which only row 11 completes, and could land only by marking it verified on four classes of thirty-eight, or by moving it six times. Read as the whole decision, six pending owners move later: crs spec §2 decisions 3, 5, 8 and 10, globe spec §2 decision 1, and layers spec §2 decision 6, which leaves row 1 of layers spec §9 for row 2. A principle that holds from the row that first builds what it governs, as crs spec §2 decision 1 does from the engine, keeps that row. If agreed, owner spec §4.2 says "the first row by whose landing the whole decision holds", a clarification made in Task 4 (workflow rule 2.1).
10. **A decision delivered by no row of its roadmap gets a landed row added for it, after the fact. Agreed by {user}`bjlittle` on 2026-11-24.** Four delivered decisions have no row to own them: crs spec §2 decisions 4 and 11, principles shown by {pull}`2766` and {pull}`2754`, which did the work of row 2 of crs spec §10 before that row could land, and globe spec §2 decisions 2 and 6, which the specification's own pull request, {pull}`2732`, delivered by designing the work and recording its measurements. Owner spec §2 decision 11 asks such a pull request to add a row and land it; applied after the fact, crs spec §10 gains row 16, ``The principles of §2 decisions 4 and 11 put to use by rows 1 and 2 of globe spec §9 | ✅ landed (2026-10-28, {pull}`2754`, {pull}`2766`)``, and globe spec §9 gains row 11, ``The design itself: the work brought forward and the evidence recorded (§3.2, §3.5, §3.6) | ✅ landed (2026-10-26, {pull}`2732`)``. The alternative, owning each by the row whose scope is nearest, names a row not started for crs, which check 5 refuses, and a row that recorded nothing for globe.
11. **One fragment, `3014.documentation.rst`.** The branch is `docs/owner-spec-row1`; this plan is the first commit of draft pull request {pull}`3014`, which marks the row in progress (workflow rules 2.3, 2.4).

## Review Focus

1. **A decision in force with an empty Row cell**, as a writer adding a decision forgets the column: the fault names the decision. `test_ledger_owners_wants_an_owner_for_each_decision_in_force` (Task 2).
2. **A Row cell naming another specification's row**, as `row 2 of layers spec §9`, which reads as a citation the build links: refused, naming whose it is. `test_ledger_owners_refuses_another_specification_s_row` (Task 2).
3. **A range, as the Evidence cells write today**, `rows 3 to 5 of §9`, copied into the Row cell: refused as more than one row. `test_ledger_owners_refuses_a_range` (Task 2).
4. **A roadmap done with a decision pending on a `candidate`**: passes, as ledger spec §2 decision 8 allowed, now through the gate. `test_ledger_owners_lets_a_candidate_own_a_pending_decision` (Task 2).
5. **A move citing a pull request that never merged, or merged after the move's date**: the GitHub check names it. `test_a_decision_s_move_cites_a_pull_merged_on_its_date` (Task 3).

Measured on 2026-11-24 at `94288c88`: 17 specifications besides the owner spec, 159 decisions; 84 owners read by the pull request that landed one row of their roadmap (Appendix B), 75 read by hand (Appendix A), which three subagents drafted from the roadmaps and the plan's author reviewed. The owner spec's own 11 take the rows their Evidence names.

---

### Task 1: The Row Cell in the Grammar

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py` (`LEDGER_HEADER`, `LEDGER_PREVIOUS`, `LedgerRow`, `ledger`)
- Modify: `docs/src/_ext/geovista_ledger.py` (`_link_evidence`, `LedgerSummary.apply`: cells by header)
- Modify: `.github/scripts/verification_report.py` (only if it reads a cell by position)
- Test: `tests/docs/test_geovista_citations.py`, `tests/docs/test_geovista_ledger.py`

**Interfaces:**
- Produces: `LEDGER_HEADER: tuple[str, ...]`; `LEDGER_PREVIOUS: tuple[str, ...]` (dropped in Task 4); `LedgerRow(cell, line, status, evidence, owner="")`; `LedgerRow.owned -> str | None`; `LedgerRow.moves -> tuple[str, ...]`.

- [ ] **Step 1: Write the failing tests** in `tests/docs/test_geovista_citations.py`:
  - `test_ledger_reads_the_row_column`: a table `| Decision | Row | Status | Evidence |` with `| §2 decision 1 | row 2 of §9 · ⬅️ row 1, 2026-12-01, {pull}`3020` | ⏳ pending | |` reads `owner`, `owned == "row 2 of §9"`, `moves == ("row 1, 2026-12-01, {pull}`3020`",)`, `status == "⏳ pending"`, `evidence == ""`.
  - `test_ledger_reads_an_empty_row_cell`: `owned is None`, `moves == ()`.
  - `test_ledger_reads_a_previous_table_with_no_owner`: the three-column header still reads, `owner == ""`.
  - In `tests/docs/test_geovista_ledger.py`, the build fixture gains the column, and the summary and the evidence links still land on the Status and Evidence cells.

  Run: `pixi run --frozen -e geovista pytest -q tests/docs/test_geovista_citations.py tests/docs/test_geovista_ledger.py -k "ledger"`
  Expected: FAIL on the three new tests.

- [ ] **Step 2: Read the table by its header** in `ledger`, mapping each header name to its cell; `owned` and `moves` read `provenance(self.owner)`. The build reads Status and Evidence by the header's index.

  Run: Step 1's command, then `tests/test_spec_conventions.py tests/test_verification_report.py tests/test_status_references.py`.
  Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "feat: read the Row column of a Verification table (owner spec §4.1)"`

### Task 2: The Checks of a Decision's Owner

**Files:**
- Modify: `tests/test_spec_conventions.py` (`ledger_owners`; `ledger_complete` and its test retired; `ledgered` writes the Row column)

**Interfaces:**
- Consumes: `LedgerRow.owned`, `LedgerRow.moves` (Task 1); `own_row`, `MOVE` (existing).
- Produces: `ledger_owners(path: Path, text: str, names: Namespace) -> list[str]`.

- [ ] **Step 1: Write the failing tests**, each cited to its decision and broken clause by clause (workflow rule 2.6):
  - `test_ledger_owners_wants_an_owner_for_each_decision_in_force` (Review Focus 1; owner spec §2 decision 1).
  - `test_ledger_owners_refuses_a_range` and `…_refuses_two_owners` (Review Focus 3; §2 decision 3).
  - `test_ledger_owners_refuses_another_specification_s_row` and `…_refuses_a_row_that_does_not_exist`, for an owner and for a move (Review Focus 2; §2 decision 6).
  - `test_ledger_owners_refuses_a_pending_decision_owned_by_a_landed_row` (the gate; §2 decision 4).
  - `test_ledger_owners_refuses_a_row_named_in_a_pending_evidence` (§4.3 item 4).
  - `test_ledger_owners_refuses_a_delivered_decision_owned_by_a_row_not_started`, passing for `🚧 in progress` and `✅ landed` (§4.3 item 5; §2 decision 1).
  - `test_ledger_owners_lets_a_candidate_own_a_pending_decision` (Review Focus 4; §2 decision 8), with every other row landed.
  - `test_ledger_owners_lets_a_retired_decision_keep_or_leave_its_owner` (§2 decision 10).
  - `test_ledger_owners_reads_a_move_and_holds_no_count`: three well-formed moves pass; one with no date or pull fails (§2 decision 7).

  Run: `pixi run --frozen -e geovista pytest -q tests/test_spec_conventions.py -k "ledger_owners"`
  Expected: FAIL, `ledger_owners` undefined.

- [ ] **Step 2: Write `ledger_owners`** with the messages of Call 3, and retire `ledger_complete` and `test_ledger_complete_once_the_roadmap_is`, whose case `test_ledger_owners_lets_a_candidate_own_a_pending_decision` now holds. `ledgered` writes `| Decision | Row | Status | Evidence |`, and every fixture row gains its cell. `ledger_owners` is not yet in `test_every_ledgered_specification_holds_its_ledger`: Task 4 adds it with the owners.

  Run: `pixi run --frozen -e geovista pytest -q tests/test_spec_conventions.py`
  Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "test: hold each decision to the row that owns it (owner spec §4.3)"`

### Task 3: A Move's Pull Request, Against GitHub

**Files:**
- Modify: `.github/scripts/check_status_references.py` (`check_ledger`)
- Test: `tests/test_status_references.py`

**Interfaces:**
- Consumes: `LedgerRow.moves` (Task 1); `_resolved`, `_unmerged` (existing).

- [ ] **Step 1: Write the failing tests**: `test_a_decision_s_move_cites_a_pull_merged_on_its_date` (Review Focus 5) — a move citing an unmerged pull, a pull merged after the move's date, and an issue each fault, as `test_an_items_pull_request_has_merged` holds an item's; `test_a_decision_s_move_may_cite_the_pull_being_checked` passes with `--pull`.

  Run: `pixi run --frozen -e geovista pytest -q tests/test_status_references.py -k "move"`
  Expected: FAIL.

- [ ] **Step 2: Read each row's moves in `check_ledger`** as `check_items` reads an item's, with `"moved"`.

  Run: `pixi run --frozen -e geovista pytest -q tests/test_status_references.py`
  Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "feat: check a decision's move against GitHub (owner spec §4.4)"`

### Task 4: Every Decision's Owner

Waits on {user}`bjlittle`'s review of Appendix A and Calls 6, 9 and 10.

**Files:**
- Modify: the Verification table of every specification under `docs/src/developer/specs/`, as Appendices A and B say; the example table of ledger spec §3.4; crs spec §10 row 16 and globe spec §9 row 11 (Call 10); owner spec §4.2 and §4.7 (Calls 8, 9)
- Modify: `docs/src/_ext/geovista_citations.py` (`LEDGER_PREVIOUS` dropped)
- Modify: `tests/test_spec_conventions.py` (`ledger_owners` joins `test_every_ledgered_specification_holds_its_ledger`)
- Modify: the three-column fixtures of `tests/test_verification_report.py`, `tests/test_status_references.py`, `tests/docs/test_geovista_citation_xrefs.py`

- [ ] **Step 1: Add `ledger_owners` to the collection's test, and drop `LEDGER_PREVIOUS`.**

  Run: `pixi run --frozen -e geovista pytest -q tests/test_spec_conventions.py -k "every_ledgered"`
  Expected: FAIL, every specification's table unread.

- [ ] **Step 2: Run `/tmp/owners.py`** (Call 5) over the collection, then add the column to ledger spec §3.4's example by hand, and the fixtures' headers.

  Run: Step 1's command, then the whole of `tests/test_spec_conventions.py`, `tests/test_renumbering.py`, `tests/test_status_references.py`, `tests/test_verification_report.py` and `tests/docs -m "not browser"`.
  Expected: PASS. `git diff --stat` touches every specification, and no Evidence cell still names a row.

- [ ] **Step 3: Commit** — `git commit -m "docs: name the row that owns every decision (owner spec §4.7)"`

### Task 5: The Developer Guide

**Files:**
- Modify: `docs/src/developer/specs/index.rst` (Decisions and Verification)
- Modify: `docs/AGENTS.md` (the specifications paragraph)
- Modify: `docs/src/developer/specs/2026-10-30-decision-ledger-design.md` (§3.4, §3.5: "Extended by a child specification")

- [ ] **Step 1: Write the guide.** "Adding a decision" writes `| §2 decision 7 | row 2 of §9 | ⏳ pending | |` and says the owner is the row whose pull request delivers it, one row of its own roadmap, kept once delivered; a new paragraph, "Owning a decision", says a row cannot land while a decision it owns is pending, that its pull request verifies, signs off, retires or moves each one, how a move is written, and that a pull request delivering a decision without landing a row adds one and lands it (owner spec §2 decision 11). `docs/AGENTS.md` gains, in its specifications paragraph: every decision names the row that delivers it in the Verification table's Row column, and a row cannot land while a decision it owns is pending (owner spec §4.3). Ledger spec §3.4 and §3.5 gain the note, in the words items spec §3.4 uses for the order spec.

  Run: the strict incremental `sphinx-build` of `AGENTS.md`, with `-W -n`, and `tests/docs -m "not browser"`.
  Expected: PASS.

- [ ] **Step 2: Commit** — `git commit -m "docs: tell an author the row that owns a decision (owner spec §4.8)"`

### Task 6: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-24-decision-owners-design.md` (§9 row 1, §11)
- Create: `changelog/3014.documentation.rst`

- [ ] **Step 1: Watch each clause fail when it regresses** (workflow rule 2.6): blank an owner, write a range, name another specification's row, land a row owning a pending decision, name a row in a pending Evidence, own a delivered decision by a row not started, strip the candidate exemption, cap the moves, and see each test of Task 2 fail; restore.
- [ ] **Step 2: Mark and settle.** Row 1 becomes ``✅ landed (<DATE>, {pull}`3014`)``; §2 decisions 1 to 8 and 10 ``✅ verified (<DATE>, {pull}`3014`)``, with `tests/test_spec_conventions.py` and, for decision 2, `tests/docs/test_geovista_citations.py`, for decision 7, `tests/test_status_references.py`; decision 11 ``✍️ signed off (<DATE>, {user}`bjlittle`, {pull}`3014`)`` with what was checked (Call 7). The fragment, humanized, names row 1 of owner spec §9.

  Run: the changelog check, the spec suites, `check-spec-status --pull 3014` with a token, `check-spec-renumbering`, the strict `sphinx-build` with `-E`, `tests/docs -m "not browser"` under `xvfb-run -a`, and `tests-unit` on `test-py314`.
  Expected: PASS.

- [ ] **Step 3: Push**, confirm with `git ls-remote` (workflow rule 4.6), and ask {user}`bjlittle` to mark the pull request ready once the final review's fixes have landed.

## Follow-ups

- crs spec §2 decision 5's last clause, `cartopy` dropped once the Natural Earth features no longer need it, belongs to no row of crs spec §10. Row 5 can show `cartopy` optional, not dropped; raised as an open item of the crs specification if {user}`bjlittle` agrees (workflow rule 2.8).

## Appendix A: The Owners Read by Hand

Each decision below was verified, signed off, retired or left pending in a way that names no one row by its pull request. `read` is an owner its roadmap names plainly; `judgement` one the reviewer should check; a Call is settled in the calls above.

| Decision | Status | Owner | Call | Why |
|---|---|---|---|---|
| checks spec §2 decision 1 | ✅ verified | row 1 | read | Row 1 "The page" (#2707) added docs/src/developer/checks.rst. |
| checks spec §2 decision 2 | ✍️ signed off | row 1 | read | Row 1 "The page, the nine CHECK names" (#2707) documents only geovista's own checks, and row 2 (third-party tools) stays a candidate. |
| checks spec §2 decision 3 | ✅ verified | row 1 | read | Row 1 "The page, the nine CHECK names" (#2707) gives every check a section, including those with no exception. |
| checks spec §2 decision 4 | ✅ verified | row 1 | read | Row 1 "the breadcrumb hook and script output" (#2707) points the breadcrumb at latest. |
| checks spec §2 decision 5 | ✅ verified | row 1 | read | Row 1 "The page ... and the gate" (#2707) wrote the page by hand and built the gate. |
| checks spec §2 decision 6 | ✅ verified | row 1 | read | Row 1 "the nine CHECK names ... and the gate" (#2707) made the gate the ninth named check. |
| checks spec §2 decision 7 | ✍️ signed off | row 1 | read | Row 1 "The page" (#2707) links to the existing write-ups and leaves them where they were. |
| checks spec §2 decision 8 | ✅ verified | row 1 | read | Row 1 "The page" (#2707) added checks.rst to EXEMPT in test_readingtime_coverage.py. |
| citation spec §2 decision 1 | ✍️ signed off | row 2 | judgement | Row 2 "The transform and the output check ... the ceiling test retires" (#2738) is the row that stopped the ceiling being raised again; the sign-off names rows 2 to 4 together, and one owner has to be picked from them. |
| citation spec §2 decision 2 | ✅ verified | row 2 | read | Row 2 "The transform and the output check" (#2738) added test_rendered_citations.py, the link check on rendered pages. |
| citation spec §2 decision 3 | ✅ verified | row 3 | read | Row 3 "The renumber guard, its fix" (#2740) added test_renumbering.py, which lets a renumber through once its citations are updated. |
| citation spec §2 decision 4 | ✅ verified | row 3 | read | Row 3 "The renumber guard, its fix" (#2740) reads and rewrites CHANGELOG.rst and the fragments; row 4's "changelog guidelines" cover the :pull: form of §4.6, a separate change. |
| citation spec §2 decision 5 | ✅ verified | row 4 | read | Row 4 "Collapsing the roles; the agreement assertion retires" (#2745). |
| citation spec §2 decision 6 | 🗄️ retired | (none) | judgement | Retired by #2786 in the same pull request that brought it into the ledger, so it was never verified or signed off and the cell can stay empty (owner spec §2 decision 10); if a negative decision counts as delivered by being honoured, row 2 "The transform" (sections-only links) would be its owner. |
| crs spec §2 decision 1 | ⏳ pending | row 3 | read | First not-landed row of rows 3 to 13; the engine "with the account of each" is where no cell is quietly dropped or wrong. |
| crs spec §2 decision 2 | ⏳ pending | row 3 | read | First not-landed row of rows 3 to 11; "The cutting engine: rotate, clip, cut a seam, densify" works on the sphere before projecting. |
| crs spec §2 decision 3 | ⏳ pending | row 14 | Call 9 | The seam and transform code is redesigned, not extended, only once row 14 deletes today's path; row 3 builds the engine it is redesigned around. |
| crs spec §2 decision 4 | ✍️ signed off | row 16 (new) | Call 10 | Shown by {pull}`2766`, scene spec row 2's work, which is crs row 2's, not started; a landed row added for it (owner spec §2 decision 11). |
| crs spec §2 decision 5 | ⏳ pending | row 5 | Call 9 | cartopy becomes optional only with row 5's "cartopy objects read without importing it"; row 3 drops shapely from the clipping. Its last clause, cartopy dropped once Natural Earth no longer needs it, belongs to no row (Follow-ups). |
| crs spec §2 decision 6 | ⏳ pending | row 4 | read | First of rows 4 to 11; "The domain registry" is the projection carrying knowledge of its own valid domain. |
| crs spec §2 decision 7 | ⏳ pending | row 5 | read | Sole row named; "The CRS interface: geovista classes, domain options, and cartopy objects" is the three ways in. |
| crs spec §2 decision 8 | ⏳ pending | row 13 | Call 9 | Data meshes are never refined from row 3 on, but the explicit opt-in that completes the decision is row 13's "Display refinement". |
| crs spec §2 decision 9 | ⏳ pending | row 12 | read | Sole row named; "Cut once, map many". |
| crs spec §2 decision 10 | ⏳ pending | row 11 | Call 9 | The commitment covers every class to cartopy parity, Spilhaus included, which row 11 completes; row 4's registry makes the unsupported fail loudly. |
| crs spec §2 decision 11 | ✍️ signed off | row 16 (new) | Call 10 | Shown by {pull}`2754`, globe spec row 1, PROJ and pyvista: crs row 2's work, not started; the same added row as decision 4. |
| crs spec §2 decision 12 | ✅ verified | row 1 | read | "The coverage test of §6, recording today's outcomes" (#2721) added tests/transform/test_projection_coverage.py, the evidence that no working use regresses. |
| crs spec §2 decision 13 | ⏳ pending | row 2 | read | First not-landed of rows 2 to 5; "The globe model, units, heights and layers" names units, though the pint units themselves already landed in globe spec row 1 (#2754). |
| crs spec §2 decision 14 | ⏳ pending | row 2 | read | First not-landed of rows 2 to 13; its scope runs "by rows 1 to 5 of globe spec §9", whose row 2 carries "the round trip of crs spec §6" of a mesh's CRS, globe and heights. |
| diagram spec §2 decision 9 | 🗄️ retired | (none) | judgement | Retired by #3001, the same pull request that landed row 2 ("The diagram under each roadmap"), before it was ever verified, so it was never delivered; row 2 is the alternative if its partial build counts. |
| docs spec §2 decision 1 | ✅ verified | row 1 | read | Row 1 "Publication" (#2573) created the specs index and excluded the plans from the build, which is the decision's promise. |
| docs spec §2 decision 2 | ✅ verified | row 1 | read | Row 1 "Publication" (#2573) added developer/plans/** to exclude_patterns and to the reading-time gate's EXCLUDED_DIRS. |
| docs spec §2 decision 3 | ✅ verified | row 1 | read | Row 1 "tests/test_spec_conventions.py" (#2573) brought in the keyed anchors with the pairing and keying assertions of §3.5. |
| docs spec §2 decision 4 | ✅ verified | row 1 | read | Row 1 "the § form" (#2573) added the sign to the seven citations and the Form assertion. |
| docs spec §2 decision 5 | ✅ verified | row 1 | judgement | Row 1 "tests/test_spec_conventions.py" (#2573) already resolved a bare §N to the containing document and failed one with no owner, though the Evidence cites test_geovista_citations.py, added by citation spec row 1 (#2735), a test from another roadmap, and row 2 "Citation cross-reference transform" is the other option. |
| docs spec §2 decision 6 | ✍️ signed off | row 1 | read | Row 1 "tests/test_spec_conventions.py" (#2573) asserts each observable candidate trigger (§3.5 item 6), and that is what the sign-off checked. |
| docs spec §2 decision 7 | ✅ verified | row 1 | read | Row 1 "tests/test_spec_conventions.py" (#2573) brought in the Status assertion (closed vocabulary, ISO date, reference); test_status_references.py came later in #2609, which landed no row. |
| floors spec §2 decision 4 | ⏳ pending | row 5 | read | Evidence empty; "The floors-docs environment (§4.1) and the docs job of ci-floors.yml" is the weekly documentation build at the floors. |
| floors spec §2 decision 6 | ⏳ pending | row 5 | judgement | Evidence empty and rows 1 to 4 landed without verifying it; row 5's "docs job of ci-floors.yml" is the last planned job whose failure a person reads, and the first not landed. |
| globe spec §2 decision 1 | ⏳ pending | row 5 | Call 9 | Layering may never move data once row 4 builds it, and row 5's "Removing zlevel and zscale" removes the last of the old mixing of the two. |
| globe spec §2 decision 2 | ✍️ signed off | row 11 (new) | Call 10 | A scope decision the specification's own pull request ({pull}`2732`) delivered by designing the work; a landed row added for it. |
| globe spec §2 decision 3 | ✍️ signed off | row 3 | read | "Heights as data: height and depth ... and to_structured_grid reading its levels as heights", by heights spec rows 1 and 2, is what the sign-off checked in #2777. |
| globe spec §2 decision 4 | 🗄️ retired | (none) | read | Retired 2026-10-27 by #2757 before any row delivered it (row 2 landed 2026-10-28), so nothing was owed. |
| globe spec §2 decision 5 | ⏳ pending | row 5 | read | Sole row named; "Removing zlevel and zscale". |
| globe spec §2 decision 6 | ✍️ signed off | row 11 (new) | Call 10 | The record of §3.5, §3.2 and §3.6 was written by the specification's own pull request ({pull}`2732`); the same added row as decision 2. |
| heights spec §2 decision 1 | ✅ verified | row 1 | read | Row 1's "Heights on a mesh: `gvHeight`" delivers it, and it was verified (2026-11-03) before row 2 landed (2026-11-11). |
| heights spec §2 decision 2 | ✅ verified | row 1 | read | Row 1's "`height=`, `depth=` ... on the bridge" and "`mesh.gv.height` and `mesh.gv.depth`" deliver it, verified before row 2 landed. |
| heights spec §2 decision 3 | ✅ verified | row 1 | read | Row 1's "missing heights" delivers it, verified before row 2 landed. |
| heights spec §2 decision 6 | ✅ verified | row 1 | read | Row 1's "the refusals of §4.4" (heights with a z-level other than 0, including `resize` and `transform_mesh`) delivers it, verified before row 2 landed. |
| heights spec §2 decision 8 | ✅ verified | row 1 | read | Row 1's "positions from heights ... through the bridge" and "`mesh.gv.height`" cover it, and #2777 changed `common.py` and the cited `tests/common/test_from_cartesian.py`. |
| heights spec §2 decision 9 | ✅ verified | row 1 | read | Row 1's "the refusals of §4.4" includes "heights for each cell", verified before row 2 landed. |
| heights spec §2 decision 10 | ✅ verified | row 1 | read | Row 1's "the refusals of §4.4" includes heights with an "Ellipsoidal height" CRS, verified before row 2 landed. |
| heights spec §2 decision 11 | ✅ verified | row 1 | read | Row 1's "`vertical_units=` on the bridge, `to_structured_grid` reading its `zs` as heights" delivers it, verified before row 2 landed. |
| layers spec §2 decision 1 | ⏳ pending | row 2 | read | Sole row named; "the camera below the surface". |
| layers spec §2 decision 2 | ⏳ pending | row 2 | read | Sole row named; "The globe: ... the horizon clip of each layer" is the default that stands in for refinement. |
| layers spec §2 decision 3 | ⏳ pending | row 1 | read | Sole row named; "Tiers: the built-in tiers, tier=, above= and below=". |
| layers spec §2 decision 4 | ⏳ pending | row 1 | read | Sole row named; "add_tier, alias_tier, GeoPlotter(tiers=...)" and "the refusals". |
| layers spec §2 decision 5 | ⏳ pending | row 2 | read | Sole row named; "the horizon clip of each layer following the camera". |
| layers spec §2 decision 6 | ⏳ pending | row 2 | Call 9 | Row 1 gives the subsurface tier and the default for depths on a map; pushing it away from the viewer on the globe arrives with row 2. |
| layers spec §2 decision 7 | ⏳ pending | row 4 | read | Sole row named; "The web: the bias written into each .vtksz of the documentation build, and the issue and pull request upstream". |
| scene spec §2 decision 1 | ✅ verified | row 2 | read | Row 2's "Every radius becomes a globe: `globe=` in place of `radius=` on the 34 functions" delivers it, and #2766 added the cited `tests/globe/test_no_radius.py`. |
| scene spec §2 decision 2 | ✅ verified | row 2 | read | Row 2's "`globe=` in place of `radius=` on the 34 functions" removes `radius=`, and #2766 added the cited `tests/globe/test_no_radius.py`. |
| scene spec §2 decision 3 | ✅ verified | row 1 | read | Row 1's "the four fields, `Globe.from_mesh` and `Globe.to_mesh`" delivers it, and #2761 added the cited `tests/globe/test_to_mesh.py`. |
| scene spec §2 decision 4 | ✅ verified | row 1 | read | Row 1's "meshes that record no globe" delivers it, and #2761 added the cited `tests/globe/test_from_mesh.py`. |
| scene spec §2 decision 6 | ✅ verified | row 1 | read | Row 1's "`sanitize_legacy` and `sanitize(legacy=...)`" delivers it, and #2761 added both cited sanitize tests. |
| scene spec §2 decision 7 | ✅ verified | row 1 | read | Row 1's "the table of retired fields" delivers it, and #2761 added the cited `tests/common/test_sanitize_legacy.py`. |
| scene spec §2 decision 8 | ✅ verified | row 1 | Call 6 | Row 1's `geovista.Globe` with its radius as a quantity delivered its example; {pull}`2942`, another specification's, verified it on `mesh.gv.height` and `mesh.gv.depth`. |
| scene spec §2 decision 9 | ✅ verified | row 1 | read | Row 1's "the `mesh.gv` namespace with `globe`, `crs` and its equality" delivers it, and #2761 added the cited `tests/accessor/test_GeoVistaAccessor.py`. |
| typing spec §2 decision 1 | ✅ verified | row 1 | read | Row 1 "The local hook, ci-typing.yml" (#2565) runs mypy against the locked pixi environment. |
| typing spec §2 decision 2 | ✍️ signed off | row 1 | read | Row 1 "The local hook, ci-typing.yml, the ratchet and its test" (#2565) put the hook live before any module was fixed, as the sign-off records. |
| typing spec §2 decision 3 | ✅ verified | row 2 | judgement | Row 2 "transform.py" (#2580) is the first row by which the boundary conversion had to hold ("established in the first two changes" per §3.3), but the Evidence test tests/bridge/test_lists.py came with row 3 "bridge.py" (#2599), and the decision's own example to_cartesian lives in common.py (row 4). |
| typing spec §2 decision 4 | ✅ verified | row 7 | read | Row 7 "examples/, its ratchet entry, and the ratchet retired" (#2681) typed the gallery and moved its defects into the configuration. |
| zlevel spec §2 decision 1 | ✅ verified | row 1 | read | The only row, "The rule in transform_mesh" (#2591), uses the Earth's radius in CRS units. |
| zlevel spec §2 decision 2 | ✅ verified | row 1 | read | The only row, "The rule in transform_mesh, its tests and docstring" (#2591), keeps zscale as the only control. |
| zlevel spec §2 decision 3 | ✍️ signed off | row 1 | read | The only row, "The rule in transform_mesh" (#2591), changed no line of geoplotter.py, as the sign-off records. |
| zlevel spec §2 decision 4 | ✅ verified | row 1 | read | The only row, "The rule in transform_mesh" (#2591), computes planar z afresh on each transform; the #2798 verification only added evidence. |

## Appendix B: The Owners Read by Pull Request

Each decision below was verified or signed off in the pull request that landed exactly one row of its own roadmap, and takes that row.

| Specification | Owner | Decisions |
|---|---|---|
| bench spec | row 1 | 1, 2, 3, 4, 6, 8 |
| bench spec | row 3 | 5, 7 |
| diagram spec | row 1 | 5 |
| diagram spec | row 2 | 1, 2, 3, 4, 7, 10 |
| diagram spec | row 3 | 6, 8 |
| docs spec | row 7 | 8 |
| docs spec | row 8 | 9 |
| floors spec | row 1 | 1, 2, 3, 9 |
| floors spec | row 2 | 5, 11 |
| floors spec | row 3 | 8 |
| floors spec | row 4 | 7, 10 |
| globe spec | row 3 | 7 |
| heights spec | row 2 | 4, 5, 7 |
| items spec | row 1 | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11 |
| items spec | row 2 | 12, 14 |
| items spec | row 3 | 8 |
| items spec | row 4 | 13 |
| ledger spec | row 1 | 1, 2, 3, 4, 5, 6, 8, 9, 10, 13, 14, 15 |
| ledger spec | row 2 | 7 |
| ledger spec | row 3 | 11 |
| ledger spec | row 6 | 12 |
| ledger spec | row 7 | 16 |
| ledger spec | row 8 | 17 |
| ledger spec | row 9 | 18 |
| order spec | row 1 | 1, 2, 3, 4, 5, 6, 11 |
| order spec | row 2 | 7, 8, 9, 10 |
| positions spec | row 1 | 3, 4 |
| positions spec | row 2 | 5 |
| positions spec | row 3 | 6 |
| positions spec | row 4 | 7 |
| positions spec | row 5 | 1, 2, 8 |
| scene spec | row 2 | 5 |

# Decision Owners: The Line Under Each Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of owner spec §9: the build names each decision's owner in a line under its entry and links each row a move left, and the verification report gives each decision's owner and each roadmap row's decisions (owner spec §4.5, §4.6), which verifies owner spec §2 decision 9.

**Architecture:** A transform in the ledger's extension, `geovista_ledger`, reads the page's Verification table through the grammar and adds under each decision's entry a paragraph naming its owner, as plain text that the citation transform then links as it links any citation. The citation extension, `geovista_citation_xrefs`, gains a transform that links the bare `row N` of each move in a Row cell to its roadmap row. The report reads the same table, writing each owner beside its decision's state, a Decisions column in its roadmap table, and a finding for a pending decision owned by a row in progress.

**Tech Stack:** Python, Sphinx and docutils transforms, MyST Markdown, pytest.

**Spec:** `docs/src/developer/specs/2026-11-24-decision-owners-design.md` (`owner spec §…`): §2 decision 9, §4.5, §4.6 and §9 row 2.

## Global Constraints

- **Nothing is written in the specification for the line** (owner spec §4.5): the build reads it from the Row column.
- **The line's words** (owner spec §4.5): **Delivered by** row N of §M once the decision is verified or signed off; **Owned by** row N of §M while it is pending; for a retired decision, **Delivered by** its owner if it has one, and nothing if not.
- **The report stays a view, never a gate** (ledger spec §3.8).
- Warnings are errors. Every pixi run is `pixi run --frozen -e geovista …` (a worktree has no `.pixi`, so run the main checkout's environment); commit through that environment's `pre-commit`; tests that render need `xvfb-run -a`. The fragment credits ``(:user:`claude`)`` (workflow rule 4.9); the pull request carries `type: documentation` and `agentic`.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-24 that owner spec §9 row 2 is bounded (workflow rule 2.7). These calls are mine.

1. **The owner is linked already.** A Row cell's `row 2 of §9` is a citation, and `CitationTransform` links every citation in a table cell, measured on 2026-11-24 at `a9c2cacb`. Only the bare `row 1` a move names is not, so the link work is the move's alone.
2. **The line is a transform of `geovista_ledger`, `DecisionOwners`, at priority 350**: after `DecisionTargets` (300) names each decision's list item, before `CitationTransform` (400). It appends to the item a paragraph of class `decision-owner`: a `nodes.strong` holding `Delivered by` or `Owned by`, then the text ` row N of §M`, which the citation transform links. It reads the page's source through `geovista_citations.ledger`, as `geovista_status` reads a roadmap.
3. **A move's row is linked by `MoveLinks` in `geovista_citation_xrefs`, at priority 405**, after `CitationTransform`, reusing its `_xref`. In each Row cell of a table headed `LEDGER_HEADER`, the `row N` after each `⬅️` links to `row_anchor(owner, roadmap section, N)`.
4. **`roadmap_section(text) -> str | None` moves into the grammar**, `geovista_citations`, where `MoveLinks` reads it; the conventions test's own binds to it.
5. **The report** writes each decision's state line as `<state> · owned by row N of §M`, or the state alone when the decision has none; gives its roadmap table a fourth column, `Decisions`, listing each row's decisions as their numbers and their states' emoji (`1 ✅, 3 ⏳`), or `—`; and finds a pending decision owned by a row in progress: `<prefix> §2 decision N is owned by row N of §M, which is in progress: its pull request must deliver it.`
6. **Row 2 verifies owner spec §2 decision 9.** One fragment, `3015.documentation.rst`; the branch is `docs/owner-spec-row2`, and this plan is the first commit of draft pull request {pull}`3015`, which marks the row in progress (workflow rules 2.3, 2.4).

## Review Focus

1. **A retired decision with no owner**: no line, and no failure. `test_no_line_under_a_retired_decision_with_no_owner` (Task 1).
2. **A Row cell with two moves, one from a lettered row** (`row 6a,`): each row it left is linked. `test_each_row_a_move_left_is_linked` (Task 2).
3. **A decision with no Verification row**, as a specification being written may have: no line, no failure. `test_no_line_under_a_decision_with_no_row` (Task 1).
4. **A page quoting a Row cell, as the specifications index does in a literal**: nothing is added or linked outside a specification's own ledger. `test_moves_are_linked_only_in_a_ledger` (Task 2).
5. **A roadmap row owning no decision, and a pending decision owned by a `candidate`**: the column shows `—`, and no finding is made. `test_report_lists_no_decision_for_a_row_owning_none` (Task 3).

---

### Task 1: The Line Under Each Decision

**Files:**
- Modify: `docs/src/_ext/geovista_ledger.py` (`DecisionOwners`, registered in `setup`)
- Modify: `docs/src/_ext/geovista_citations.py` (`roadmap_section`); `tests/test_spec_conventions.py` binds its own to it
- Test: `tests/docs/test_geovista_ledger.py`

**Interfaces:**
- Produces: `geovista_citations.roadmap_section(text: str) -> str | None`; `DecisionOwners(SphinxTransform)`, `default_priority = 350`.

- [ ] **Step 1: Write the failing tests**, over a built fixture specification with a decision of each state:
  - `test_the_line_under_a_decision_names_its_owner`: a verified and a signed-off decision read **Delivered by** row 1 of §M, a pending one **Owned by** row 2 of §M, each a link to its row's anchor; a retired one with an owner reads **Delivered by**. Holds owner spec §2 decision 9.
  - `test_no_line_under_a_retired_decision_with_no_owner` (Review Focus 1).
  - `test_no_line_under_a_decision_with_no_row` (Review Focus 3).
  - `test_the_line_is_written_by_the_build_alone`: the source holds no `Delivered by`.

  Run: `xvfb-run -a <env>/bin/python -m pytest -q tests/docs/test_geovista_ledger.py -k "line"`
  Expected: FAIL.

- [ ] **Step 2: Write `roadmap_section` in the grammar and `DecisionOwners`** as Calls 2 and 4 say.

  Run: Step 1's command, then `tests/docs -m "not browser"` and `tests/test_spec_conventions.py`.
  Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "feat: name each decision's owner under its entry (owner spec §4.5)"`

### Task 2: The Row a Move Left, Linked

**Files:**
- Modify: `docs/src/_ext/geovista_citation_xrefs.py` (`MoveLinks`, registered in `setup`)
- Test: `tests/docs/test_geovista_citation_xrefs.py`

**Interfaces:**
- Consumes: `geovista_citations.roadmap_section` (Task 1); `_xref` and `OWNERS` (existing).
- Produces: `MoveLinks(SphinxTransform)`, `default_priority = 405`.

- [ ] **Step 1: Write the failing tests:**
  - `test_each_row_a_move_left_is_linked` (Review Focus 2): a Row cell `row 3 of §9 · ⬅️ row 2, … · ⬅️ row 6a, …` renders three links, to rows 3, 2 and 6a of §9, and keeps its text.
  - `test_moves_are_linked_only_in_a_ledger` (Review Focus 4).

  Run: `xvfb-run -a <env>/bin/python -m pytest -q tests/docs/test_geovista_citation_xrefs.py -k "move"`
  Expected: FAIL.

- [ ] **Step 2: Write `MoveLinks`** as Call 3 says.

  Run: Step 1's command, then `tests/docs -m "not browser"`.
  Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "feat: link the row each move left (owner spec §4.5)"`

### Task 3: The Report's Owners

**Files:**
- Modify: `.github/scripts/verification_report.py` (`_roadmap`, the decisions loop, `_owner_findings`)
- Test: `tests/test_verification_report.py`

**Interfaces:**
- Consumes: `LedgerRow.owned`, `grammar.ledger` (existing).
- Produces: `_owner_findings(path: Path, text: str, prefix: str, names: Namespace) -> list[str]`.

- [ ] **Step 1: Write the failing tests:**
  - `test_report_gives_each_decision_its_owner`: `<state> · owned by row 1 of §3`, and the state alone for a decision with none.
  - `test_report_lists_each_row_s_decisions`: the roadmap table's `Decisions` column, `1 ✅, 3 ⏳`.
  - `test_report_lists_no_decision_for_a_row_owning_none` (Review Focus 5).
  - `test_report_finds_a_pending_decision_owned_by_a_row_in_progress`: the finding of Call 5, and none for a row not started or a `candidate`.

  Run: `<env>/bin/python -m pytest -q tests/test_verification_report.py -k "owner or decisions"`
  Expected: FAIL.

- [ ] **Step 2: Write them** as Call 5 says.

  Run: `tests/test_verification_report.py`, then the report on the collection: `<env>/bin/python .github/scripts/verification_report.py owner`.
  Expected: PASS, and owner spec's report shows row 2's decision 9 as pending and owned by it, with the finding.

- [ ] **Step 3: Commit** — `git commit -m "feat: give the report each decision's owner (owner spec §4.6)"`

### Task 4: The Guide, and Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/index.rst` (Owning a decision; The verification report)
- Modify: `docs/src/developer/specs/2026-11-24-decision-owners-design.md` (§9 row 2, §11 decision 9)
- Create: `changelog/3015.documentation.rst`

- [ ] **Step 1: Write the guide.** "Owning a decision" says the build writes the line under each decision and links each row a move left; "The verification report" says it shows each decision's owner and each row's decisions.
- [ ] **Step 2: Watch each clause fail when it regresses** (workflow rule 2.6): the line's words swapped, a retired decision with no owner given a line, the line written for a decision with no row, a move's row left unlinked, a move linked outside a ledger, the report without its owner, column or finding.
- [ ] **Step 3: Mark and settle.** Row 2 becomes ``✅ landed (<DATE>, {pull}`3015`)``; §2 decision 9 ``✅ verified (<DATE>, {pull}`3015`)`` with `tests/docs/test_geovista_ledger.py`, `tests/docs/test_geovista_citation_xrefs.py` and `tests/test_verification_report.py`. Every row then has landed, and the specification reads `✅ complete`. The fragment, humanized, names row 2 of owner spec §9.

  Run: the changelog check, the spec suites, `check-spec-status --pull 3015` with a token, `check-spec-renumbering`, the strict `sphinx-build` with `-E`, `tests/docs -m "not browser"` and `tests-unit` under `xvfb-run -a`.
  Expected: PASS.

- [ ] **Step 4: Push**, confirm with `git ls-remote` (workflow rule 4.6), and ask {user}`bjlittle` to mark the pull request ready once the final review's fixes have landed.

## Follow-ups

- An open item's move, `⬅️ row N, …` in its parenthetical, is not linked either. Items spec §3.2 asks no link of it, so it is left, and raised for discussion if {user}`bjlittle` wants it.

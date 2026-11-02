# Open Items, Row 1: The Items Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of items spec §8: items and rows become citations, an open item
carries its state, provenance, row and issue, the suite and GitHub hold every item to
them, and the docs, zlevel, checks and citation specifications and this one are brought in.

**Architecture:** The grammar module `docs/src/_ext/geovista_citations.py` learns item and
row anchors, both citation forms, and the entry of items spec §3.2, so the build, the
conventions test, the renumber guard, the status checker and the report read one
definition. Specifications not yet brought in keep the grammar of docs spec §3.6 behind a
list the test keeps, as the ledger's `UNLEDGERED` did.

**Tech Stack:** Python 3.13+, Sphinx and docutils transforms, pytest, the GitHub REST API.

**Spec:** `docs/src/developer/specs/2026-11-02-open-items-design.md` (items spec), with
ledger spec §3.1, §3.6, §3.7 for the patterns it follows.

## Global Constraints

- States, built by name: `OPEN = "\N{BLACK QUESTION MARK ORNAMENT} Open"`, `DEFERRED = f"\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}{VS16} Deferred"`, `RESOLVED = "\N{CHEQUERED FLAG} Resolved"`, `ABANDONED = "\N{NO ENTRY SIGN} Abandoned"`, `GRADUATED = "\N{GRADUATION CAP} Graduated"`; parts `FOUND = "\N{RIGHT-POINTING MAGNIFYING GLASS}"`, `OWED = "\N{DIRECT HIT}"`, `MOVED = f"\N{LEFTWARDS BLACK ARROW}{VS16}"`, `TICKET = "\N{TICKET}"`, separated by `" \N{MIDDLE DOT} "`. Each read with or without its variation selector, as the ledger's states are.
- Anchors: an item `<prefix>-spec-<section>-item-<n>` (`scene-spec-4-4-item-2`), a row `<prefix>-spec-<section>-row-<r>` (`typing-spec-4-row-6a`).
- Citation forms, all valid: `typing spec §8 item 9`, `item 9 of typing spec §8`, `§8 item 9`, `item 9 of §8`, `row 5 of §10`, `row 5 of crs spec §10`, `rows 3 to 11 of §10` (both ends checked). An item of the Decisions section is cited only as a decision (ledger spec §2 decision 1).
- The label is exactly `spec: open item`, and exists (#2804).
- Brought in by row 1: docs, zlevel, checks, citation and items specifications. `UNITEMED = {"2026-10-06-type-coverage-design.md": 3, "2026-10-23-globe-first-crs-design.md": 4, "2026-10-26-globe-heights-layers-design.md": 5, "2026-10-27-globe-scene-design.md": 5, "2026-10-28-heights-as-data-design.md": 5, "2026-10-30-decision-ledger-design.md": 5}`, the value the row of items spec §8 that brings each in.
- Row 1 settles items spec §7 item 1 (#2804) and §7 item 2 (#2806, option (b)), and lands row 5 of citation spec §9, retiring `test_row_5_waits_until_items_and_rows_are_cited_often` with `numbered`, `AFTER`, `BEFORE` and `NUMBERED_CEILING`.
- Every verified ledger row's test is shown to fail under a mutation of its decision before it is cited (`docs/AGENTS.md`).
- `<PR>` is this pull request and `<DATE>` its merge day; an agent never adds `signed-off`.

## Review Focus

1. **A section holding two numbered lists**: only the first is anchored, and a citation names an item of it; the suite reports a citation of an item past the first list's end rather than linking the wrong one. Test in Task 1.
2. **A row numbered with a letter, and a range across one** (`rows 6a to 7 of typing spec §4`): both ends resolve. Test in Task 1.
3. **An item of §2 cited as an item** (`§2 item 3`): it fails resolution, not silently links a decision. Test in Task 1.
4. **The wrong grammar in either kind of specification**: an old-grammar item in a brought-in specification is reported by `item_entries`, and a new-grammar item in an `UNITEMED` one by `status`, so neither passes unread. Test in Task 4.
5. **A labelled issue that is closed, or a pull request carrying the label**: neither is reported as uncited by the nightly run. Test in Task 6.

---

### Task 1: Item and row citations in the grammar

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py`
- Test: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Produces: `item_anchor(slug: str, section: str, number: int) -> str`; `row_anchor(slug: str, section: str, row: str) -> str`; `@dataclass(frozen=True) class Listed: section: str; number: int; line: int; title: str | None; body: str` and `listed(text: str) -> list[Listed]` (top-level numbered items of the first list of every numbered section but Decisions, outside fences, `title` the bold run after any state, else `None`); `@dataclass(frozen=True) class Row: section: str; row: str; line: int; scope: str; status: str` and `rows(text: str) -> list[Row]`; `Citation.ends: tuple[str, ...] = ()`, the far end of a range; `namespace()` adds every item and row anchor and reads every form of Global Constraints.

- [ ] **Step 1:** Write the failing tests: `test_an_item_is_cited_either_way` (`demo spec §3 item 2` and `item 2 of demo spec §3` both resolve to `demo-spec-3-item-2`); `test_a_row_range_names_both_ends` (`rows 6a to 7 of demo spec §4` → slug `demo-spec-4-row-6a`, `ends == ("demo-spec-4-row-7",)`); `test_a_decision_is_never_cited_as_an_item` (Review Focus 3); `test_only_the_first_list_of_a_section_is_anchored` (Review Focus 1); `test_listed_reads_titled_and_untitled_items`.
- [ ] **Step 2:** Run `pixi run --frozen -e test-py313 python -m pytest tests/docs/test_geovista_citations.py -q` → FAIL (names undefined).
- [ ] **Step 3:** Implement. The signed pattern gains an optional lead, `(item|row)s? N( (to|and) M)? of `, before the prefix or a bare sign, and an optional trailing `item N` beside `decision N`; `scan` builds the slug from whichever is present.
- [ ] **Step 4:** Run the module, `tests/docs/test_geovista_citation_xrefs.py` and `tests/test_spec_conventions.py` → PASS. `test_every_citation_resolves` now resolves every item and row cited in the corpus; any that names nothing is a real fault, fixed here.
- [ ] **Step 5:** Commit — `docs: read items and rows as citations`.

### Task 2: Anchors in the build

**Files:**
- Modify: `docs/src/_ext/geovista_citation_xrefs.py`
- Test: `tests/docs/test_geovista_citation_xrefs.py`, `tests/docs/test_rendered_citations.py`

**Interfaces:**
- Consumes: `item_anchor`, `row_anchor`.
- Produces: transform `ItemTargets(SphinxTransform)`, `default_priority = 300`, naming the first `enumerated_list`'s items of every section of a specification but `<owner>-2`, and each body row of a table whose header is a roadmap's.

- [ ] **Step 1:** Write failing tests that a built fixture specification carries `demo-spec-3-item-2` on its list item and `demo-spec-4-row-1` on its table row, and that a citation of each renders as a link to it.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement `ItemTargets` beside `DecisionTargets`, registered in `setup`. **Step 4:** Run, then the incremental docs build with `-W --keep-going` → PASS, and in the built page `item 9 of typing spec §8` is a link to `#typing-spec-8-item-9`.
- [ ] **Step 5:** Commit — `docs: give items and rows their anchors`.

### Task 3: Near-miss citations (settles items spec §7 item 1)

**Files:**
- Modify: `tests/test_spec_conventions.py`; `docs/src/developer/specs/2026-10-23-globe-first-crs-design.md`, `2026-10-26-globe-heights-layers-design.md`

**Interfaces:**
- Produces: `near_misses(path: Path, text: str, names: Namespace) -> list[str]`, reporting a known prefix followed by `row`, `item` or `decision` with no `§`, a section sign followed by a comma and one of them, and `decision N of §M`, each with its fix (`§8, item 3` → `§8 item 3`).

- [ ] **Step 1:** Write `test_near_misses_finds_each_form` over a fixture with one of each and three valid forms, and `test_no_citation_is_a_near_miss(texts, names)`.
- [ ] **Step 2:** Run → the fixture test FAILS (undefined); the repository test FAILS with exactly six: crs spec lines 261, 326, 591, 592 and globe spec lines 389, 427, each `§N, item M` or `§9, row 6`.
- [ ] **Step 3:** Implement; rewrite the six in the specifications without the comma (`§8 item 3`, `row 6 of §9`).
- [ ] **Step 4:** Run the conventions suite → PASS; `check-spec-renumbering` → PASS.
- [ ] **Step 5:** Commit — `tests: refuse a citation the grammar cannot read`.

### Task 4: The entry and the suite (items spec §3.2, §3.5 to §3.7)

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py`, `tests/test_spec_conventions.py`
- Test: `tests/test_spec_conventions.py`

**Interfaces:**
- Produces in the grammar: the constants of Global Constraints, `ITEMED_STATES`; `@dataclass(frozen=True) class Item: number: int; line: int; state: str | None; settled: str; found: str; owed: str | None; moves: tuple[str, ...]; issue: int | None; graduated: str | None; title: str; body: str` and `items(text: str) -> list[Item]`, reading the Open Items section, whatever its case, in the grammar of §3.2.
- Produces in the test: `UNITEMED`; `item_entries(path, text) -> list[str]` (§3.7 assertion 1), `item_owed(path, text) -> list[str]` (2, the landing gate), `item_moves(path, text) -> list[str]` (3), `item_graduated(path, text) -> list[str]` (4), `item_issues(texts: Mapping[Path, str]) -> list[str]` (5, collection-wide); `status()` reads the open items of an `UNITEMED` specification only.

- [ ] **Step 1:** Write a fixture test per rule, building every emoji by name: an entry missing 🔎, an Open item owed by a landed row, a Deferred item with no ⬅️ and one with three, a Graduated item naming a row that does not cite its issue, two items citing one issue, a settled item with no 🎫 (passes), and Review Focus 4 both ways. Add `test_every_itemed_specification_holds_its_items` and `test_unitemed_names_specifications_still_waiting`, as the ledger's tests do.
- [ ] **Step 2:** Run → FAIL (undefined).
- [ ] **Step 3:** Implement. Split the parenthesis on the middle-dot separator; the first part of a settled state is its date and reference, and of a graduated one ends `to row N of §M`.
- [ ] **Step 4:** Run → the fixtures PASS; the repository test FAILS for the five specifications not yet in the grammar (Task 7 fixes them).
- [ ] **Step 5:** Commit — `tests: hold every open item to its entry, row and issue`.

### Task 5: The renumber guard (settles items spec §7 item 2)

**Files:**
- Modify: `.github/scripts/check_renumbering.py`
- Test: `tests/test_renumbering.py`

**Interfaces:**
- Consumes: `listed`, `ITEMED_STATES`, `namespace`, `scan`.
- Produces: `numbered_items(text: str, cited: Collection[str] = frozenset()) -> dict[str, dict[str, Section]]`, reading an untitled item whose anchor is in `cited`, titled by its text; `STATES` gains the five states of §3.2.

- [ ] **Step 1:** Write `test_a_cited_untitled_item_is_frozen` (an untitled list whose second item the corpus cites, with an item inserted before it, fails naming the item), keep `test_a_numbered_list_without_bold_titles_is_not_frozen` passing when nothing cites it, and `test_an_item_title_is_read_after_its_emoji_state`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement; the guard builds `cited` from the corpus it already scans. **Step 4:** Run the module and `check-spec-renumbering` → PASS.
- [ ] **Step 5:** Commit — `ci: freeze an untitled item once something cites it`.

### Task 6: What GitHub answers (items spec §3.8)

**Files:**
- Modify: `.github/scripts/check_status_references.py`
- Test: `tests/test_status_references.py`

**Interfaces:**
- Consumes: `items`, `Item`, `UNITEMED` (via the conventions module).
- Produces: `Work.labels: frozenset[str] = frozenset()`, filled by `github()` from each answer's `labels`; `type Lister = Callable[[], list[int]]` and `labelled_issues(token: str | None = None) -> Lister`, every open issue (not pull request) carrying the label, read across pages; `check_items(path, text, resolve, *, pull=None, drift=False) -> list[str]`; `uncited(numbers: Iterable[int], texts: Mapping[Path, str]) -> list[str]`; `main(..., listed: Lister | None = None)`.

- [ ] **Step 1:** Write failing tests against fixed records: an item's issue unlabelled (`#5 carries no spec: open item label`), a pull request cited as 🎫, a ⬅️ dated two days from its merge, a 🔎 pull request still open (fails unless `pull=` it), a Deferred item whose issue closed under `drift`, `test_an_open_labelled_issue_no_item_cites_is_drift`, and Review Focus 5.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement; `main` runs `check_items` on every specification not in `UNITEMED`, and `uncited` in drift over every item of either grammar; the count line includes items' references; the module docstring gains the rules. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit — `ci: ask GitHub about every open item and its label`.

### Task 7: Bringing in five specifications (items spec §3.10)

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (5 items), `2026-10-08-planar-zlevel-design.md` (2), `2026-10-23-repository-checks-design.md` (1), `2026-11-02-open-items-design.md` (2); `tests/test_spec_conventions.py` (`UNITEMED`)

- [ ] **Step 1:** Each settled item takes 🏁 and keeps its reference first; 🔎 is the date and pull request `git log -S` finds for its title; 🎫 only where it cited an issue.
- [ ] **Step 2:** Items spec §7 items 1 and 2 become `🏁 Resolved (<DATE>, {pull}`<PR>` · 🔎 … · 🎫 …)`, item 1 found in #2803 and item 2 in this pull request, each saying what Tasks 3 and 5 delivered. Correct §3.1's sentence on the renumber guard to say it freezes a titled item, and an untitled one once cited. The pull request closes #2804 and #2806.
- [ ] **Step 3:** Conventions suite → PASS, the repository tests of Task 4 included. Commit — `docs: bring the docs, zlevel, checks, citation and items specifications in`.

### Task 8: The parents and the workflow (items spec §3.11, §3.12)

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§3.5 gains item 10, **Open Items**; §3.6 gains its note), `2026-10-30-decision-ledger-design.md` (§3.8 gains its note), `docs/src/developer/specs/index.rst`, `docs/src/developer/checks.rst`, `docs/AGENTS.md`

- [ ] **Step 1:** The notes, in the form ledger spec §3.10 used.
- [ ] **Step 2:** The index gains **Open Items** after **Decisions and Verification**: raising an item with its issue and label, citing one and a row, owing it, moving it, and settling or promoting it at a landing, an example of each state, and that an agent may add the label. The checks page gains each failure of Tasks 3 to 5 under `spec-conventions` and of Task 6 under `spec-statuses`, with its fix. `docs/AGENTS.md` extends its line on specifications by one sentence, under 200 lines.
- [ ] **Step 3:** Docs build `-W --keep-going` → PASS; humanize; commit — `docs: document open items for contributors`.

### Task 9: The ledger records row 1, and landing

- [ ] **Step 1:** Items spec §10: each of decisions 1 to 7, 9 and 10 becomes ✅ verified by the tests that hold it, cited only once a mutation of its rule fails them; a decision no test holds under mutation is proposed for sign-off instead. Decision 11, a permission, is proposed for ✍️ sign-off ("Checked in review that the index says an agent may add the label"). 8 stays pending on row 3, 12 on row 2, 13 on rows 1 to 5, 14 on rows 1 to 2. Ask {user}`bjlittle` to add `signed-off`.
- [ ] **Step 2:** Citation spec §9 row 5 → `✅ landed (<DATE>, {pull}`<PR>`)`.
- [ ] **Step 3:** `changelog/<PR>.contributor.rst`, crediting `:user:`claude``, validated; humanize.
- [ ] **Step 4:** Full suite with images, mypy, the docs build, `check-spec-status <PR>` and `drift` → all pass. Final review on `opus`.
- [ ] **Step 5 (last commit):** items spec §8 row 1 → `✅ landed (<DATE>, {pull}`<PR>`)`.

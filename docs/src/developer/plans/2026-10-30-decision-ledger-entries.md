# Decision Ledger, Row 1: The Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of ledger spec §8: decisions become citeable and anchored, every
in-ledger specification carries its decisions state first and a Verification table, the
suite holds the ledger, and the docs, citation and ledger specifications are brought in.

**Architecture:** The shared citation grammar (`docs/src/_ext/geovista_citations.py`)
learns what a decision is, how one is cited, and how a Verification table reads, so the
conventions test, the build and the renumber guard keep agreeing. The build generates
each decision's anchor (no hand-written anchors), links decision citations through the
existing transform, and writes each table's summary line. The conventions test gains
item 9, Ledger, with an explicit list of specifications not yet brought in.

**Tech Stack:** Python 3.13+, Sphinx + MyST, docutils transforms, pytest.

**Spec:** `docs/src/developer/specs/2026-10-30-decision-ledger-design.md` (ledger spec),
with its parent `docs/src/developer/specs/2026-10-06-published-specs-design.md` (docs spec).

## Global Constraints

- A decision citation is `<prefix> spec §2 decision N`, singular `decision`, one decision per citation (ledger spec §3.1).
- A decision anchor is `<prefix>-spec-2-decision-N`, e.g. `heights-spec-2-decision-3` (ledger spec §3.1).
- Decision states, exactly: `🤝 Agreed` (U+1F91D) and `🗄️ Retired` (U+1F5C4 U+FE0F). Ledger states, exactly: `⏳ pending` (U+23F3), `✅ verified` (U+2705), `✍️ signed off` (U+270D U+FE0F), `🗄️ retired` (U+1F5C4 U+FE0F). Read each with or without its U+FE0F.
- Python under `tests/` and `docs/src/_ext/` builds every emoji and section sign by name (`"\N{HANDSHAKE}"`), never literally: those files sit in the corpus they govern.
- The Verification table's header is exactly `| Decision | Status | Evidence |`; a roadmap is a table whose first header cell is `#` and that has `Scope` and `Status` cells (the type coverage roadmap adds `Lines`).
- Summary line copy, exactly: `✅ {v} · ✍️ {s} · ⏳ {p} · 🗄️ {r}: {v + s} of {n - r} decisions in force verified`, where `n` is the number of rows.
- Specifications not yet in the ledger after this row, each with the row of ledger spec §8 that brings it in: type coverage 4, planar zlevel 4, repository checks 4, globe-first CRS 5, globe heights layers 6, globe scene 6, heights as data 6.
- Provenance of a brought-in decision is the commit that first added it (ledger spec §2 decision 14). Docs spec decisions 1 to 7: `2026-10-07`, {user}`bjlittle`, {pull}`2567`. Citation spec decisions 1 to 6: `2026-10-26`, {user}`bjlittle`, {pull}`2734`.
- Specification prose: wrap at 92 columns, never wrap a citation across a line, humanize before committing; title style per `docs/src/developer/documentation.rst`.
- A citation in Python always carries its prefix, or is carried from one by a comma in the same run: a file outside the specifications owns no sections, so a bare `§2 decision 4` there fails the existing resolution rule.
- An agent never adds the `signed-off` label (ledger spec §2 decision 7). The label is created by row 2, not here.
- `docs/AGENTS.md` stays under 200 lines (it is at 199).
- `<PR>` below is this pull request's number and `<DATE>` the day it merges; fill both when known.

## Review Focus

1. **An emoji typed without its variation selector** (`🗄 Retired`, `✍ signed off`): read as the same state. Test in Task 1.
2. **A decision entry whose bold title wraps onto its second line**: its title is read whole. Test in Task 1.
3. **The 34 existing `spec §2 decision N` citations in the not-yet-ledgered crs, globe, scene and heights specifications**: they must resolve and link from this row on, because those specifications already number their decisions. Covered by the existing resolution test once Task 1 lands; Task 6 runs it.
4. **`§2 decisions 4 and 14`** (plural) is not a decision citation and must not half-match: it stays a citation of §2. Test in Task 1; the one occurrence, in the globe scene spec's References, is rewritten in Task 6.
5. **A Verification row whose first cell is not a number, or a table with a stray extra row**: reported with its line, never a crash. Test in Task 4.

---

### Task 1: The grammar of decisions, decision citations and the ledger table

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py`
- Test: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Produces, in `geovista_citations`:
  - `AGREED: str`, `RETIRED: str` (decision states, with U+FE0F where the spec has one); `PENDING`, `VERIFIED`, `SIGNED_OFF`, `LEDGER_RETIRED: str` (ledger states); `DECISIONS = "Decisions"`, `VERIFICATION = "Verification"`.
  - `def state_of(written: str, states: Iterable[str]) -> str | None` — the state `written` opens with, matching with or without U+FE0F, returned in its canonical spelling.
  - `@dataclass(frozen=True) class Decision`: `number: int`, `line: int`, `state: str | None`, `carried: str` (the parenthetical after the state, balanced, without its parentheses), `title: str`, `body: str` (the text after the title, lines joined by single spaces).
  - `def decisions(text: str) -> list[Decision]` — the top-level numbered items of the section titled `Decisions` whose heading number is `2`, in order; `[]` when there is none. Bulleted items are not decisions.
  - `@dataclass(frozen=True) class LedgerRow`: `cell: str` (first cell as written), `line: int`, `status: str`, `evidence: str`; and property `decision -> int | None`.
  - `def ledger(text: str) -> list[LedgerRow] | None` — the rows of the first table under the section titled `Verification` whose header is the one in Global Constraints; `None` when there is no such table.
  - `def decision_anchor(slug: str, number: int) -> str` — `f"{slug}-2-decision-{number}"`.
  - `namespace()` now also declares `decision_anchor(owner, n)` for each decision of each specification; `Namespace.signed` matches an optional `decision N` after a section number, in both its prefixed and bare branches; `scan()` yields that anchor as the `Citation.slug`.

- [ ] **Step 1: Write the failing tests** in `tests/docs/test_geovista_citations.py` (build `§` and emoji by name):
  - `test_a_decision_citation_names_its_decision`: in a namespace declaring `demo-spec`, `scan("see demo spec §2 decision 3.")` yields one citation, text `demo spec §2 decision 3`, slug `demo-spec-2-decision-3`.
  - `test_a_bare_decision_citation_means_its_own_document`: owner `demo-spec`, `§2 decision 3` → slug `demo-spec-2-decision-3`.
  - `test_a_prefix_carries_to_a_decision_in_a_run`: `demo spec §3, §2 decision 1` → slugs `demo-spec-3`, `demo-spec-2-decision-1`.
  - `test_decisions_plural_is_a_citation_of_the_section`: `demo spec §2 decisions 4 and 14` → one citation, text `demo spec §2`, slug `demo-spec-2`.
  - `test_decisions_reads_state_provenance_title_and_body`: an entry `3. **🤝 Agreed** (2026-10-28, {user}`bjlittle`, {pull}`2771`) — **A missing height\n   is no height.** A masked …` → `Decision(number=3, state=AGREED, carried="2026-10-28, {user}`bjlittle`, {pull}`2771`", title="A missing height is no height.", …)` (the title wraps: Review Focus 2).
  - `test_a_state_is_read_without_its_variation_selector`: `state_of("🗄 Retired (…)", (AGREED, RETIRED)) == RETIRED` (Review Focus 1).
  - `test_decisions_ignores_bullets_and_other_sections`: a bulleted Decisions list → `[]`; a numbered list under §3 → `[]`.
  - `test_namespace_declares_an_anchor_per_decision`: a spec with `(demo-spec-2)=\n## 2. Decisions\n\n1. **One.** …\n2. **Two.** …` → `demo-spec-2-decision-1` and `-2` in `namespace([spec]).anchors`.
  - `test_ledger_reads_the_verification_table`: a `## 10. Verification` section with the header and two rows → two `LedgerRow`s, `decision` 1 and 2, `status` and `evidence` stripped; a table with another header → `None`.

- [ ] **Step 2: Run them to verify they fail**

Run: `pixi run --frozen -e test-py313 python -m pytest tests/docs/test_geovista_citations.py -q`
Expected: the new tests FAIL (names undefined, or no decision slug).

- [ ] **Step 3: Implement the interfaces above in `geovista_citations.py`.** Read with `read_lines` (code is skipped), as the rest of the module does. In `namespace()`, the decision group is `(?:[^\S\n]+decision[^\S\n]+(?P<decision>\d+)(?!\d))` with a distinct group name per branch; `decision` is followed by whitespace, so `decisions` never matches. Update the module docstring to say the grammar defines decisions too (ledger spec §3.1).

- [ ] **Step 4: Run the tests to verify they pass**, and the conventions and renumbering suites to see nothing else moved

Run: `pixi run --frozen -e test-py313 python -m pytest tests/docs/test_geovista_citations.py tests/test_spec_conventions.py tests/test_renumbering.py -q -n 8`
Expected: all PASS. The existing resolution test now resolves the 34 decision citations of the crs family (Review Focus 3).

- [ ] **Step 5: Commit** — `docs: teach the citation grammar decisions and the ledger table`

### Task 2: Decision anchors in the build

**Files:**
- Modify: `docs/src/_ext/geovista_citation_xrefs.py`
- Test: `tests/docs/test_geovista_citation_xrefs.py`

**Interfaces:**
- Consumes: `geovista_citations.decision_anchor`, `OWNERS`.
- Produces: `class DecisionTargets(SphinxTransform)` with `default_priority = 300`, registered in `setup()`.

- [ ] **Step 1: Write the failing test** `test_a_build_links_a_decision_citation_to_its_decision`, following `test_a_build_links_citations_in_a_page_and_a_docstring`: alpha spec gains `(alpha-spec-2)=\n## 2. Decisions\n\n1. **One.** First.\n2. **Two.** Second.\n`; the page cites `alpha spec §2 decision 2`. Assert `warning == ""`, `'alpha-design.html#alpha-spec-2-decision-2"' in page`, and `'<li id="alpha-spec-2-decision-2"' in alpha`. Also `test_a_build_warns_of_a_citation_naming_no_decision`: the page cites `alpha spec §2 decision 9` → `"alpha-spec-2-decision-9" in warning` and `"undefined label" in warning`.

- [ ] **Step 2: Run to verify they fail**

Run: `pixi run --frozen -e geovista python -m pytest tests/docs/test_geovista_citation_xrefs.py -q -k decision`
Expected: FAIL, `undefined label: 'alpha-spec-2-decision-2'`.

- [ ] **Step 3: Implement `DecisionTargets.apply`.** For a document in `OWNERS`, find the section whose `ids` hold `f"{owner}-2"`, take its first `nodes.enumerated_list` child, and for each `list_item` at offset `k` append `decision_anchor(owner, start + k)` to its `names` and call `self.document.note_explicit_target(item, item)`. Priority 300 is after docutils' `PropagateTargets` (260), which moves the `(…-2)=` id onto the section, and before `CitationTransform` (400); a prototype at 210 found no section. The standard domain records each as an anonymous label, which the transform's explicit-title `std:ref` resolves. Note the dependency on the grammar, as `CitationTransform.apply` does.

- [ ] **Step 4: Run to verify they pass**

Run: `pixi run --frozen -e geovista python -m pytest tests/docs/test_geovista_citation_xrefs.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit** — `docs: give every decision an anchor at build time`

### Task 3: The Verification summary line

**Files:**
- Create: `docs/src/_ext/geovista_ledger.py`
- Modify: `docs/src/conf.py` (add `"geovista_ledger"` after `"geovista_citation_xrefs"` in `extensions`)
- Test: `tests/docs/test_geovista_ledger.py`

**Interfaces:**
- Consumes: the ledger states of Task 1, `geovista_citations.state_of`.
- Produces: `def summary(statuses: Iterable[str]) -> str` (the exact copy of Global Constraints) and `class LedgerSummary(SphinxTransform)` (priority 410), which appends `nodes.paragraph(classes=["ledger-summary"])` holding `summary(...)` after the Verification table of a specification. `setup()` returns `parallel_read_safe` and `parallel_write_safe` true and the transform notes `__file__` and the grammar as dependencies (`docs/AGENTS.md`).

- [ ] **Step 1: Write the failing tests**: `test_summary_counts_each_state` — statuses `[VERIFIED, VERIFIED, VERIFIED, PENDING, LEDGER_RETIRED, SIGNED_OFF]` → `"✅ 3 · ✍️ 1 · ⏳ 1 · 🗄️ 1: 4 of 5 decisions in force verified"`; `test_summary_reads_a_status_with_its_parenthetical` — `"✅ verified (2026-10-30, {pull}`1`)"` counts as verified; `test_a_build_writes_the_summary_under_the_table`, using the build helper of `tests/docs/test_geovista_citation_xrefs.py` (move it to `tests/docs/conftest.py` if both modules need it), asserting the summary text follows `</table>` in the spec's HTML and the build warns nothing.

- [ ] **Step 2: Run to verify they fail** — `pixi run --frozen -e geovista python -m pytest tests/docs/test_geovista_ledger.py -q` → FAIL, no module.

- [ ] **Step 3: Implement `summary` and `LedgerSummary`.** The transform reads the doctree, not the source: in a document in `OWNERS`, the first `nodes.table` under the section titled `Verification` whose header row reads `Decision`, `Status`, `Evidence`.

- [ ] **Step 4: Run to verify they pass**, then `pixi run --frozen -e geovista python -m pytest tests/docs/test_conf_*.py -q` to see `conf.py` still loads.

- [ ] **Step 5: Commit** — `docs: write each Verification table's summary at build time`

### Task 4: The conventions test holds the ledger (docs spec §3.5 item 9)

**Files:**
- Modify: `tests/test_spec_conventions.py`

**Interfaces:**
- Consumes: Task 1's grammar; existing `statuses`, `carried`, `DATE`, `REFERENCE`, `where`, `specifications`, `namespace`.
- Produces:
  - `statuses()` reads a roadmap only by its header (Global Constraints), so a Verification table is never read as one.
  - `UNLEDGERED: dict[str, int]` — file name to the row of ledger spec §8 that brings it in (Global Constraints).
  - Rules, each `(path: Path, text: str, ...) -> list[str]`: `ledger_entries`, `ledger_table`, `ledger_retirements`, `ledger_evidence(path, text, names)`, `ledger_complete`, `ledger_replacements(path, text, names, decided)`, where `decided: dict[str, Decision]` maps each decision anchor in the collection to its entry.

- [ ] **Step 1: Write the failing fixture tests**, one per rule, each firing on a `demo spec` built in `tmp_path` and quiet on a correct one (cite the ledger decision each holds in its docstring, so Task 6 can name these as evidence):
  - `test_ledger_entries_finds_a_gap_a_missing_state_and_missing_provenance` (ledger spec §2 decision 2, §2 decision 4): entries numbered 1, 3; an entry with no state; an Agreed entry with no `{pull}`; a Retired entry without `; agreed <date>, {pull}`.
  - `test_ledger_table_wants_the_last_section_and_a_row_per_decision` (§2 decision 5, §2 decision 10): Verification not last; rows 1, 2 for three decisions; a row whose first cell is `two` (Review Focus 5).
  - `test_ledger_states_carry_what_they_must` (§2 decision 9): `✅ verified` without a date; `✍️ signed off` without a `{user}`; `⏳ pending (2026-10-30)`.
  - `test_ledger_retirements_agree_in_both_sections` (§2 decision 3): a Retired decision whose row is verified, and the reverse.
  - `test_ledger_evidence_must_exist_and_cite_its_decision` (§2 decision 6): a verified row naming a missing file; one naming a file that does not cite the decision.
  - `test_ledger_complete_once_the_roadmap_is` (§2 decision 8): every roadmap row landed and a row pending → fault; pending naming `row 5 of §4` where row 5 is `candidate` → quiet.
  - `test_ledger_replacement_must_be_in_force` (§2 decision 3): `replaced by §2 decision 4` where 4 is Retired, or does not exist.

- [ ] **Step 2: Write the failing repository tests**:
  - `test_every_ledgered_specification_holds_its_ledger`, parametrised over `specifications()` not in `UNLEDGERED`, running every rule (cite §2 decision 13 in its docstring).
  - `test_unledgered_names_specifications_still_waiting`: each key exists, and its row in ledger spec §8 is not `✅ landed`.

- [ ] **Step 3: Run to verify they fail**

Run: `pixi run --frozen -e test-py313 python -m pytest tests/test_spec_conventions.py -q -n 8 -k ledger`
Expected: the fixture tests FAIL (rules undefined); the repository test FAILS on the docs, citation and ledger specifications, which Task 6 brings in.

- [ ] **Step 4: Implement the rules and the roadmap header.** A state's carried parenthetical must hold: Agreed — a `DATE`, at least one `{user}` role, a `{pull}` role; Retired — the same, then `; agreed `, a `DATE` and a `{pull}`; verified and retired rows — a `DATE` and a `{pull}`; signed off — a `DATE`, a `{user}` and a `{pull}`; pending — nothing. Evidence paths are the code spans of the Evidence cell, relative to the repository root. A file cites a decision when `scan()` over its prose lines yields that anchor.

- [ ] **Step 5: Run the fixture tests to verify they pass**; the repository test still fails until Task 6.

- [ ] **Step 6: Commit** — `tests: hold every ledgered specification to its ledger`

### Task 5: The renumber guard reads a decision's title past its state

**Files:**
- Modify: `.github/scripts/check_renumbering.py:228`
- Test: `tests/test_renumbering.py`

- [ ] **Step 1: Write the failing test** `test_a_decision_inserted_mid_list_fails_naming_it`, using the module's `items()` helper with entries `1. **🤝 Agreed** (…) — **One.**` …: insert a decision before the last and assert the guard names the moved decision by its title, not by `🤝 Agreed`.
- [ ] **Step 2: Run** `pixi run --frozen -e test-py313 python -m pytest tests/test_renumbering.py -q -k decision` → FAIL (title read as the state).
- [ ] **Step 3: Implement**: `STATES` also holds the grammar's `AGREED` and `RETIRED`, matched as `state_of` matches them.
- [ ] **Step 4: Run** the whole of `tests/test_renumbering.py` → PASS.
- [ ] **Step 5: Commit** — `tests: let the renumber guard read a decision's title`

### Task 6: Bring the docs, citation and ledger specifications into the ledger

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md`, `2026-10-26-citation-links-design.md`, `2026-10-30-decision-ledger-design.md`, `2026-10-27-globe-scene-design.md` (plural citation only)
- Modify: the test files named as evidence below, to cite their decisions

- [ ] **Step 1: Docs spec.** Number its seven decisions in their present order, each `N. **🤝 Agreed** (2026-10-07, {user}`bjlittle`, {pull}`2567`) — **<title as now>** <text as now>`. Add `(docs-spec-10)=\n## 10. Verification` after References with the table below, and add `docs spec §2 decision N` to each evidence file's docstring of the test that exercises it. Confirm each test really exercises its decision; where none does, make the row `✍️ signed off (<DATE>, {user}`bjlittle`, {pull}`<PR>`)` with what bjlittle checked, and raise it in the pull request for bjlittle's review.

| Decision | Proposed evidence |
|---|---|
| 1 | `tests/test_spec_conventions.py`, `tests/docs/test_readingtime_coverage.py` |
| 2 | `tests/docs/test_readingtime_coverage.py` |
| 3 | `tests/test_spec_conventions.py` |
| 4 | `tests/test_spec_conventions.py` |
| 5 | `tests/docs/test_geovista_citations.py` |
| 6 | `tests/test_spec_conventions.py` |
| 7 | `tests/test_spec_conventions.py`, `tests/test_status_references.py` |

- [ ] **Step 2: Citation spec.** Number its six decisions: 1 to 5 `🤝 Agreed` (2026-10-26, {user}`bjlittle`, {pull}`2734`); 6, "Sections only", `🗄️ Retired (<DATE>, {user}`bjlittle`, {pull}`<PR>`; agreed 2026-10-26, {pull}`2734`)`, text kept, then `Retired because ledger spec §2 decision 1 gives each decision an anchor and a link of its own; replaced by ledger spec §2 decision 1.` Add `(citation-spec-11)=\n## 11. Verification` after References. Proposed: 1 signed off (the machinery of rows 2 to 4 was built and the ceiling retired), 2 `tests/docs/test_rendered_citations.py`, 3 `tests/test_renumbering.py`, 4 signed off (the changelog guidelines say so), 5 `tests/test_spec_conventions.py`, 6 `🗄️ retired (<DATE>, {pull}`<PR>`)` replaced by ledger spec §2 decision 1.

- [ ] **Step 3: Ledger spec.** Replace the §10 bootstrap paragraph with its table: 1 `tests/docs/test_geovista_citations.py`, `tests/docs/test_geovista_citation_xrefs.py`; 2 `tests/test_renumbering.py`; 3, 4, 5, 6, 8, 9, 10, 13 `tests/test_spec_conventions.py`; 7, 11, 12 `⏳ pending`; 14 signed off (provenance of the docs and citation decisions checked against `git log -S`); 15 signed off (the documentation of Task 7 read in review).

- [ ] **Step 3a: Anything not delivered.** A decision whose work has landed but which no test or sign-off can honestly show is delivered stays `⏳ pending`, becomes an open item of its specification, and gets an issue labelled `agentic` (ledger spec §3.9 step 5). Raise it with bjlittle before opening the issue.

- [ ] **Step 4: Globe scene spec.** In References, `crs spec §2 decisions 4 and 14` becomes `crs spec §2 decision 4, crs spec §2 decision 14` (Review Focus 4).

- [ ] **Step 5: Run the ledger and resolution tests**

Run: `pixi run --frozen -e test-py313 python -m pytest tests/test_spec_conventions.py tests/test_renumbering.py tests/docs/test_geovista_citations.py -q -n 8`
Expected: all PASS, the repository ledger test included.

- [ ] **Step 6: Commit** — `docs: bring the docs, citation and ledger specifications into the ledger`

### Task 7: The parent's notes and the contributor documentation

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§3.2, §3.5, §3.6)
- Modify: `docs/src/developer/specs/index.rst`, `docs/src/developer/checks.rst`, `docs/AGENTS.md`

- [ ] **Step 1: Docs spec.** Add an `> **Extended by a child specification.**` note, pointing to ledger spec §3.1, §3.6 and §3.2 to §3.4 in turn, to docs spec §3.2, §3.5 and §3.6. Append to the list of docs spec §3.5 item `9. **Ledger.**`, saying what ledger spec §3.6 asserts, in one paragraph.
- [ ] **Step 2: Specifications index.** After "Statuses", add a section "Decisions and Verification" (labels `gv-developer-specs-decisions` and `tippy-gv-developer-specs-decisions`): how to add a decision (state first, provenance, a ⏳ row in the same pull request), cite one, retire one, verify one with a test that cites it, and sign one off (`✍️` row; the named reviewer adds `signed-off`, which an agent never does; row 2 of ledger spec §8 makes it a gate). Cite ledger spec §3.2 to §3.4 rather than repeating them.
- [ ] **Step 3: Checks page.** Under `spec-conventions`, add the ledger failures of ledger spec §3.6 and how to fix each.
- [ ] **Step 4: `docs/AGENTS.md`.** Fold into the existing line on citing a section: decisions are cited `<prefix> spec §2 decision N`, and an agent never adds `signed-off`. Keep the file under 200 lines.
- [ ] **Step 5: Verify**: `pixi run --frozen -e test-py313 python -m pytest tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py -q -n 8` → PASS, and the incremental docs build of `docs/AGENTS.md` with `-W --keep-going` → `build succeeded`.
- [ ] **Step 6: Commit** — `docs: document the decision ledger for contributors`

### Task 8: Landing

- [ ] **Step 1:** `changelog/<PR>.contributor.rst`, crediting `:user:`claude``; validate with `pixi run -e docs python .github/scripts/changelog.py <PR> "changelog/<PR>.contributor.rst"`.
- [ ] **Step 2:** Full suite with images (`CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e test-py313 python -m pytest tests -q -n 8`), `pixi run --frozen -e geovista mypy`, the docs build with `-W --keep-going`, and `pixi run -e geovista tests-docs-browser` (the rendered-citation gate) → all pass.
- [ ] **Step 3:** `pixi run --frozen -e test check-spec-status <PR>` → all hold.
- [ ] **Step 4 (last commit):** ledger spec §8 row 1 → `✅ landed (<DATE>, {pull}`<PR>`)`, `UNLEDGERED` unchanged; re-run Step 3; redate if the merge slips.

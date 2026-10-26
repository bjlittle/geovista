# Citation Links Row 2: The Transform and the Output Check — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Link every plain citation the documentation build renders, check the built HTML for any that did not link, and retire the ceiling test that held this row back.

**Architecture:** A Sphinx transform, `docs/src/_ext/geovista_citation_xrefs.py`, ported from tephpy's `tephpy_citation_xrefs.py`, replaces each citation in a doctree text node with a `std:ref` `pending_xref`, using the grammar of `docs/src/_ext/geovista_citations.py` (row 1). Its registry of anchors is built on `builder-inited` and fingerprinted, so parallel reads and incremental builds stay right. The output check is a `tests/docs` module, ported from tephpy's `check_rendered_citations.py`, that reads every built page with `html.parser`. The ceiling test retires, and row 5's trigger, which row 1 should have asserted and did not, is asserted.

**Tech Stack:** Python 3.13+, Sphinx, docutils, MyST, pytest, pixi.

**Spec:** `docs/src/developer/specs/2026-10-26-citation-links-design.md`, `citation spec §4.2`, `§4.3`, `§4.7` and rows 2 and 5 of `§9`. Prior art: `bjlittle/tephpy` at `29896cf`, `docs/src/_ext/tephpy_citation_xrefs.py`, `.github/scripts/check_rendered_citations.py`, `tests/test_citation_xrefs.py`, `tests/test_rendered_citations.py`.

## Global Constraints

- Citations outside the specifications stand at 69 against `CEILING = 70` until Task 5 retires the ceiling. Until then, write every example in a module, test or docstring inside inline code, or built from `SECTION = "\N{SECTION SIGN}"`.
- The transform is a port: keep tephpy's skip set (`literal`, `literal_block`, `comment`, `raw`, `reference`, `desc_signature`, `pending_xref`), its `autosummary_table` exception, its heading warning, `refwarn=True`, its fingerprint and `env-get-outdated` handler, and `parallel_read_safe` and `parallel_write_safe`.
- The output check shares no code with the grammar, and finds citations with tephpy's looser `§\s*\d+(?:\.\d+)*`.
- Any test that builds Sphinx guards on the `require` fixture of `tests/docs/conftest.py`, so it fails under `--browser-strict`, and scopes the build in `docutils_namespace()`, as `tests/docs/test_parallel_build.py` does.
- Every new Python file opens with the copyright header and `from __future__ import annotations`.
- Commit through `pixi run --frozen -e geovista git commit`.

## Review Focus

1. **Tooltips.** `sphinx_tippy` builds a tooltip payload for internal references, so every newly linked citation adds to it. `tests/docs/test_tooltips.py` must still pass on the built site (Task 6).
2. **A citation the grammar does not read.** A `§3.2` in a page that owns no sections has no prefix, so the transform leaves it, and the output check fails on it. Task 6 reads every such failure on the real site and fixes the source, never the check.
3. **A heading.** A citation in a section heading warns, which fails the build. Task 6 confirms the real site has none.
4. **The registry on an empty or broken collection.** No anchors makes the transform a no-op rather than emitting references that cannot resolve. Task 3 tests it.
5. **Incremental builds.** Renumbering a section must re-read every page on the next build. Task 3 tests the fingerprint and the outdated handler; Task 6 checks an incremental rebuild by hand.

---

### Task 1: Commit This Plan

- [ ] **Step 1:** Commit this file alone, push, open the draft pull request (`agentic`, `type: documentation`, `type: testing`), and pause for review.

### Task 2: Citations Know Where They Are

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py` (`Citation`, `scan`)
- Modify: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Produces: `Citation(text: str, slug: str | None, start: int, end: int)`, where `source[start:end] == text` for the `source` given to `scan`.

- [ ] **Step 1: Write the failing test** `test_a_citation_knows_where_it_is_written`: for `text = f"See demo spec {SECTION}1, {SECTION}2 and {SECTION}1."` scanned with owner `"other-spec"`, every citation satisfies `text[c.start:c.end] == c.text`, and the starts are increasing. Update `test_the_grammar_is_one_module_however_it_is_loaded` to build `Citation("x", None, 0, 1)`.
- [ ] **Step 2:** Run `pixi run --frozen -e test pytest -p no:pretty tests/docs/test_geovista_citations.py`. Expected: the new test fails (no `start`).
- [ ] **Step 3:** Add `start` and `end` to `Citation`, documented in its Attributes, and set them from the match in `scan`.
- [ ] **Step 4:** Run the grammar tests and `tests/test_spec_conventions.py`. Expected: all pass.
- [ ] **Step 5:** Commit `"tests: give each citation its place in the text"`.

### Task 3: The Transform

**Files:**
- Create: `docs/src/_ext/geovista_citation_xrefs.py`
- Create: `tests/docs/test_geovista_citation_xrefs.py`

**Interfaces:**
- Consumes: `geovista_citations.namespace`, `scan`, `Citation.start`/`end`, `read_lines`.
- Produces: `CitationTransform` (priority 400), `_build_registry(app)`, `_fingerprint(anchors, owners) -> str`, `_outdated(app, env, added, changed, removed) -> set[str]`, `setup(app)`, module globals `PATTERN`, `OWNERS` (docname to prefix, e.g. `"developer/specs/2026-10-06-published-specs-design": "docs-spec"`), `FINGERPRINT`, and the environment attribute `ENV_FINGERPRINT = "geovista_citation_registry"`.

- [ ] **Step 1: Write the failing tests**, porting tephpy's `tests/test_citation_xrefs.py` to geovista's names and to a `prerequisites` fixture that requires `sphinx`. They cover: a citation in prose becomes a `pending_xref` to its slug, displaying the text as written; a bare section number inside a specification resolves to that specification and outside one is left alone; a run of two becomes two references; each skipped node leaves its citation plain; a citation in an `autosummary_table` is linked; a heading citation warns and one in a table caption does not; the registry is built from `docs/src/developer/specs`; no anchors clears `PATTERN`; the fingerprint changes when an anchor or owner does, and only then; `_outdated` re-reads nothing when unchanged, every other document when changed, and nothing extra on a first build; `setup` registers the transform and both handlers and declares parallel safety.
- [ ] **Step 2:** Add one end-to-end test, `test_a_build_links_citations_in_a_page_and_a_docstring`: an in-process parallel build (`parallel=2`) of a project with two small specifications under `developer/specs`, a page citing both, and an `automodule` whose docstring cites one, asserting each citation renders as `<a class="reference internal" href="...#<slug>">` and the build warns nothing.
- [ ] **Step 3:** Run `pixi run --frozen -e geovista pytest -p no:pretty tests/docs/test_geovista_citation_xrefs.py`. Expected: fails, no module.
- [ ] **Step 4:** Create the module as a port of tephpy's, reading `docs/src/developer/specs` relative to `app.srcdir`, with geovista's owners keyed by docname. A duplicate anchor is the conventions test's to report, so the registry takes the grammar's namespace as it stands. The heading warning carries `type="geovista"`, `subtype="citation"` and names `citation spec §4.2` in inline code. Its module docstring cites `citation spec §4.2` once.
- [ ] **Step 5:** Run the transform tests and `tests/docs/test_ext_parallel.py` under `-e geovista`. Expected: all pass, and the parallel check now lists `geovista_citation_xrefs`.
- [ ] **Step 6:** Commit `"docs: link specification citations at build time"`.

### Task 4: The Output Check

**Files:**
- Create: `tests/docs/test_rendered_citations.py`

**Interfaces:**
- Produces: `class Scan(HTMLParser)` with `linked: list[tuple[str, str]]` (citation, href), `bare: list[tuple[str, str]]` (citation, placement), `nested: list[str]`, `exempt: int`; `CHECK`-less, as it is a test of the build, not a repository check.

- [ ] **Step 1: Write the failing tests** on small HTML strings, porting tephpy's `tests/test_rendered_citations.py`: a linked citation is linked; one in `<code>` or `<pre>` is exempt; a bare one is bare and placed (`title`, `nav`, `dt`, body); one under two `<a>` is nested; void elements and unclosed tags do not confuse the stack.
- [ ] **Step 2:** Run them. Expected: fail, no `Scan`.
- [ ] **Step 3:** Port `Scan`, recording each linked citation's `href` from the innermost `<a>`.
- [ ] **Step 4: Write the site tests**, each taking `html_root`: `test_every_rendered_citation_is_a_link` reads every page but `_modules/`, failing with tephpy's grouped report on any bare or nested citation; `test_a_build_links_some_citation` fails when none linked, naming the transform; `test_every_citation_link_lands_on_an_anchor_that_exists` resolves each linked `href` against its page and asserts the target page exists and holds an element with that `id`.
- [ ] **Step 5:** Run the string tests in `-e test` (no build needed). Expected: pass. The site tests skip without a build.
- [ ] **Step 6:** Commit `"tests: check the built documentation for unlinked citations"`.

### Task 5: Wiring and Retirement

**Files:**
- Modify: `docs/src/conf.py` (`extensions`)
- Modify: `tests/test_spec_conventions.py` (`CEILING`, `outside`, the ceiling and pairing tests, row 5's trigger)
- Modify: `docs/src/developer/checks.rst`, `docs/src/developer/specs/index.rst`
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§4 text, §8 item 2)

- [ ] **Step 1:** Put `"geovista_citation_xrefs"` first in `extensions`, as tephpy does.
- [ ] **Step 2: Row 5's trigger, red first.** Add `numbered(texts, names) -> int` counting, outside the specifications and reading across line breaks, citations followed by `item N` or `items N`, and those preceded by `row N of` or `rows N to M of`, and `test_row_5_waits_until_items_and_rows_are_cited_often` asserting `0 < count <= 20`. Test `numbered` on a fixture: two items, one row and one run of rows give four. Run against the repository. Expected: 6.
- [ ] **Step 3: The pairing.** `OUTPUT_GATE` becomes `"tests/docs/test_rendered_citations.py"`. `test_row_4_pairs_the_transform_with_its_output_gate` asserts that, with a citation transform registered, that file exists and `.github/workflows/ci-tests-docs.yml` runs the `tests-docs-browser` task, whose command selects `tests/docs`.
- [ ] **Step 4: Retire the ceiling.** Delete `CEILING`, `outside`, `test_outside_counts_a_section_role_as_a_citation` and `test_rows_2_to_4_wait_until_the_corpus_outgrows_review`. In `checks.rst`, Specification Conventions loses its `CEILING` sentence and says citations are links built at build time. In the docs spec, §4's paragraph on rows 2 to 4 records that they activated and were built by the child specification, and §8 item 2 becomes `**Resolved** (<date>, {pull}`<PR>`)`. `specs/index.rst` tells a reader that a citation in the documentation is a link.
- [ ] **Step 5:** Run `tests/test_spec_conventions.py`, `tests/test_repository_checks.py` and `tests/test_status_references.py`. Expected: pass.
- [ ] **Step 6:** Commit `"tests: retire the citation ceiling, and wire the transform to its check"`.

### Task 6: The Real Site

- [ ] **Step 1:** Build `html-noplot` and run `tests/docs/test_rendered_citations.py` and `tests/docs/test_tooltips.py` against it. Expected: every citation linked, every link landing, no warning. Fix any failure in the source it names.
- [ ] **Step 2:** Rebuild incrementally after renumbering a heading in a scratch copy of one specification, and confirm a page citing it is re-read. Revert.
- [ ] **Step 3:** Run `pixi run --frozen -e geovista tests-docs-browser html-gallery strict` under `xvfb-run`, as CI does. Expected: pass.
- [ ] **Step 4:** Run `pixi run --frozen -e test tests-unit "not image"`. Expected: no failures.
- [ ] **Step 5:** Commit any source fixes.

### Task 7: Record and Land

- [ ] **Step 1:** Write `changelog/<PR>.feature.rst`, crediting `:user:`claude``, and check it with `.github/scripts/changelog.py`.
- [ ] **Step 2:** Final review on Opus; fix Critical and Important findings RED first; record the review at the end of this plan; raise an `agentic` issue for anything deferred.
- [ ] **Step 3: The landed rows, last.** Row 2 of `citation spec §9`, and rows 2 and 4 of `docs spec §4`, become `✅ landed (<date>, {pull}`<PR>`)`. Run `check-spec-status <PR>`, commit, push, and mark the pull request ready.

## After the Final Review

The whole-branch review, on Opus, found the transform a faithful port of tephpy's, and confirmed with its own builds, serial and parallel, that a steady rebuild re-reads nothing, a renumbered anchor re-reads every page, and a missing anchor or a heading citation warns. On the built site it found 163 pages, 269 citations linked, 34 left as code, and none bare, nested or broken. Three Important findings and eight Minor ones.

- **Fixed:** the transform recorded no dependency on its own code or the grammar's, which `docs/AGENTS.md` asks of an extension writing doctree content, so an edit to the grammar would have left every cached page stale. `test_every_document_depends_on_the_transform_and_its_grammar` failed, then passed.
- **Fixed:** the build test that `citation spec §6` asks for, of a citation naming no anchor, was missing, and the plan had dropped it without a ruling. `test_a_build_warns_of_a_citation_naming_no_anchor` passes, and fails with `refwarn` switched off.
- **Fixed:** the repository checks design still named `CEILING` as the trigger of rows 2 to 4. It names `NUMBERED_CEILING` now.
- **Corrected:** row 5's count is 8, not the 7 Task 5 recorded. The new `OUTPUT_GATE` comment cites a row too.
- **Deferred to #2739:** the eight Minor findings, on the output check's handling of symlinks and href-less links and its failure report, the transform's heading warning, `doctest_block` and skip-set coverage, `numbered()`'s documented limits, and one overstated sentence. It also raises, for a decision, whether citation links should carry tooltips.
- **Codex round:** two P2 findings on the output check, each reproduced red first and fixed. A citation whose section sign and number inline markup set apart was read in neither run of text: text is now buffered across inline elements and read at the end of each block (`test_a_citation_split_by_inline_markup_is_still_read`, guarded by `test_a_citation_is_never_joined_across_a_block`). An `<a>` with no destination counted as a link, and a local link naming no section as landing: neither does now (`test_an_anchor_without_a_destination_is_no_link`, `test_a_local_link_naming_no_section_is_broken`). This settles half of #2739 item 2. The real build still passes, with 269 citations linked.

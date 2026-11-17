# Figures Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 8 of docs spec §4, the last row of its roadmap that is not a candidate. `tests/test_spec_conventions.py` gains the check of docs spec §3.9, which verifies §2 decision 9 and completes the specification.

**Architecture:** Two rules in the conventions test, each a function returning one message per fault, as the suite's other rules are. `figure_faults(path, text)` reads the figures a specification shows, by parsing it as CommonMark and reading each `{figure}` fence, and holds them and the folder `figures/<stem>/` beside it to §3.9. `stray_figures(specs)` holds the folder `figures/` itself: everything in it is a folder named for a specification. Fixtures show each rule firing, and the repository tests show them holding.

**Tech Stack:** pytest, `markdown-it-py` (already imported by the suite), MyST's `figure` directive.

**Spec:** `docs/src/developer/specs/2026-10-06-published-specs-design.md` (`docs spec §…`): §2 decision 9, §3.5, §3.9, §4 row 8, §6 and §10.

## Global Constraints

- A specification's figures are PNG files in `figures/<stem>/` beside it, shown with MyST's `figure` directive, each with `:alt:` text and a caption. No figure is larger than 150 KB (docs spec §3.9).
- The rules need no `sphinx`, build or network, so the suite still never skips (§3.5).
- This module sits in its own corpus: its fixtures build the section sign rather than write it, and cite `demo spec`, as the rest of the suite does.
- No new public name. Warnings are errors under pytest. Docstrings are NumPy style, and `.. versionchanged::` is not used.
- Commit through the environment's `pre-commit`, after `pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: documentation` and `agentic`, and closes no issue.
- A test named as evidence in §10 cites its decision in its docstring, as "Holds docs spec §2 decision 9." (ledger spec §3.4).

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-17 that docs spec §3.9 fixes how row 8 behaves (workflow rule 2.7), and chose that the check also hold the conventions of §3.9 that its last paragraph leaves out: the folder, PNG and caption, and a folder of figures that names no specification. The other calls are mine.

1. **The check holds all of §3.9.** Beyond the three checks §3.9 lists and its limit, a figure a specification shows sits in its own folder, every file in that folder is a PNG, every figure has a caption, and everything in `figures/` is a folder named for a specification. A folder left behind by a renamed specification would otherwise hold figures nothing shows, and nothing would see it. §3.9's last paragraph and §3.5 say so in this pull request.
2. **150 KB is 150,000 bytes**, `FIGURE_LIMIT`. The largest figure today is 57,091 bytes.
3. **A PNG is its signature.** A file is a PNG when its name ends `.png` and it opens with the eight bytes of the PNG signature, so a JPEG renamed fails.
4. **A figure is a `{figure}` fence.** `shown(text)` parses the specification as CommonMark and reads each fence whose info string opens `{figure}`, as MyST does, with its line from `token.map`. It reads a directive's options in both forms MyST accepts, `:alt: …` lines and a `---` YAML block, and the caption as the first paragraph after them. It reads into the body of any other directive fence too, since MyST renders a figure nested in a `{note}`, but not into a code fence or a directive whose body is not markdown: `code`, `code-block`, `code-cell`, `sourcecode`, `literalinclude`, `eval-rst`, `mermaid` and `math`. A figure quoted inside a code fence is a demonstration, as §3.5 says of code.
5. **A figure is named relative to its specification.** Its target must read `figures/<stem>/<file>.png`, with `<stem>` the specification's own. A target in another specification's folder, an absolute path or a `..` fails as outside its own folder.
6. **One rule for a specification, one for the folder.** `figure_faults(path, text)` reports, for each figure shown, one outside its own folder, one that does not exist, and one without `:alt:` text or a caption, and for each file in `figures/<stem>/`, at any depth, one no figure shows, one that is not a PNG and one past the limit. `stray_figures(specs)` reports each entry of `figures/` that is a file, or a folder whose name is no specification's stem. A file shown twice is no fault.
7. **The suite asserts it is not vacuous** (§3.5): `test_the_collection_shows_figures` fails if no specification shows a figure, as one does today.
8. **Evidence.** `test_every_specification_keeps_its_figures` and `test_no_folder_of_figures_is_stray` cite §2 decision 9, and §10 names `tests/test_spec_conventions.py`.
9. **One fragment, `2980.documentation.rst`.** The branch is `docs/spec-figures-check`, and the plan is the first commit of draft pull request {pull}`2980` (workflow rule 2.3), which marks row 8 in progress (workflow rule 2.4).

## Review Focus

1. **A figure nested in another directive.** It is read, and one quoted in a code fence is not. `test_shown_reads_a_nested_figure_and_skips_a_quoted_one` (Task 1).
2. **Options in a YAML block.** `alt` there counts as `:alt:` does. `test_shown_reads_options_in_either_form` (Task 1).
3. **The limit's edge.** 150,000 bytes passes and 150,001 fails. `test_figure_faults_finds_a_file_over_the_limit` (Task 1).
4. **A renamed specification.** Its old folder fails as stray. `test_stray_figures_finds_a_folder_naming_no_specification` (Task 1).

---

Measured on 2026-11-17 at `21dc7bfb` (`main` after {pull}`2978`): fifteen specifications, one of which, the layers spec, shows figures: ten `{figure}` fences in backticks, each with `:alt:`, `:width:` and a caption, showing the ten PNG files of `figures/2026-11-12-layers-design/`, 37,424 to 57,091 bytes at the largest three. `figures/` holds that folder alone. `docs/src/conf.py` enables no MyST extension, so a figure is a backtick fence; colon fences are not parsed.

### Task 1: The Rules

**Files:**
- Modify: `tests/test_spec_conventions.py` (a section after the index's publication tests)

**Interfaces:**
- Produces: `FIGURES`, `FIGURE_LIMIT`, `PNG`, `NOT_MARKDOWN` (the directives of Call 4 whose body is not read), a frozen dataclass `Figure(line: int, target: str, alt: str, caption: str)`, `shown(text: str) -> list[Figure]`, `figure_faults(path: Path, text: str) -> list[str]` and `stray_figures(specs: Path = SPECS) -> list[str]`.

- [ ] **Step 1: Write the fixture tests**

Each writes a specification with `demo()` and its figures beside it in `tmp_path / "figures" / "2026-01-01-demo-design"`, a PNG being the signature and padding:

- `test_figure_faults_passes_a_figure_kept_as_section_3_9_says`: one figure, shown with `:alt:` and a caption: no fault.
- `test_figure_faults_finds_a_file_no_figure_shows`: a second PNG in the folder, and one in a folder beneath it.
- `test_figure_faults_finds_a_figure_that_does_not_exist`.
- `test_figure_faults_finds_a_figure_without_alt_text_or_a_caption`: no `:alt:`, an empty `:alt:`, and no caption.
- `test_figure_faults_finds_a_figure_outside_its_own_folder`: a target in another specification's folder, an absolute one, and one through `..`.
- `test_figure_faults_finds_a_file_that_is_not_a_png`: a `.jpg`, and a `.png` without the signature.
- `test_figure_faults_finds_a_file_over_the_limit`: 150,001 bytes fails and 150,000 passes.
- `test_shown_reads_options_in_either_form`: `:alt:` lines and a YAML block read the same.
- `test_shown_reads_a_nested_figure_and_skips_a_quoted_one`: a figure inside a four-backtick `{note}` is read; one inside a four-backtick `markdown` fence and one inside `{code-block}` are not.
- `test_stray_figures_finds_a_folder_naming_no_specification`: a folder for a stem no specification has, and a loose file in `figures/`.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k "figure or shown"`
Expected: FAIL, the rules not yet written.

- [ ] **Step 2: Write the rules**

As Calls 4 to 6 describe. Each message opens with `where(path, line)`, the line of the fence for a figure shown and 1 for a file in the folder, and says what is wrong in the words of §3.9, as `figures/…/x.png: shown by no figure`.

Run: the command of Step 1.
Expected: PASS.

- [ ] **Step 3: Write the repository tests**

- `test_every_specification_keeps_its_figures(spec)`, parametrized over `specifications()`: `figure_faults` finds nothing. Holds docs spec §2 decision 9.
- `test_no_folder_of_figures_is_stray()`: `stray_figures()` finds nothing. Holds docs spec §2 decision 9.
- `test_the_collection_shows_figures(specs)`: at least one figure is shown across the collection.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_spec_conventions.py
git commit -m "test: hold the figures of each specification to docs spec §3.9"
```

### Task 2: The Specification and the Checks Page

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§3.5, §3.9, §6)
- Modify: `docs/src/developer/checks.rst` (Specification Conventions)

- [ ] **Step 1: Say what the check holds**

Humanized (workflow rule 3.1): §3.9's last paragraph lists every check of Call 6, the limit read as 150,000 bytes. §3.5 gains item 11, **Figures**, naming the same. §6 says the conventions test holds §3.1 to §3.9. The Specification Conventions section of `checks.rst` adds to its rule that a specification's figures sit in its own folder, are shown with alt text and a caption, and are PNG files of 150 KB or less.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_renumbering.py`, then `pixi run --frozen -e test check-spec-renumbering`.
Expected: PASS.

- [ ] **Step 2: Commit**

```bash
git add docs/src/developer/specs/2026-10-06-published-specs-design.md docs/src/developer/checks.rst
git commit -m "docs: say what the figures check of docs spec §3.9 holds"
```

### Task 3: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§4 row 8, §10)
- Modify: this plan's Follow-ups, before merge
- Create: `changelog/2980.documentation.rst`

- [ ] **Step 1: Watch each clause fail when it regresses** (workflow rule 2.6)

Mutate one at a time, run the named tests, see them fail, and revert:
- the folder's files are not compared with the figures shown: `..._finds_a_file_no_figure_shows`;
- a missing figure passes: `..._finds_a_figure_that_does_not_exist`;
- `:alt:` is not read, and an empty one passes: `..._without_alt_text_or_a_caption`;
- the caption is not read: the same;
- a target outside its own folder passes: `..._outside_its_own_folder`;
- the signature is not read: `..._not_a_png`;
- the limit is `>=`, and then off by one the other way: `..._over_the_limit`;
- `shown` does not read into a directive, and then reads into a code fence: `test_shown_reads_a_nested_figure_and_skips_a_quoted_one`;
- `stray_figures` returns nothing: `test_stray_figures_finds_a_folder_naming_no_specification`;
- in the repository, the `:alt:` of one layers spec figure is deleted, and a stray folder is added: `test_every_specification_keeps_its_figures` and `test_no_folder_of_figures_is_stray`.

- [ ] **Step 2: Mark the decision and the row, and add the fragment**

In §10, §2 decision 9 becomes ``✅ verified (<DATE>, {pull}`2980`)`` with evidence `tests/test_spec_conventions.py`, and row 8 of §4 becomes ``✅ landed (<DATE>, {pull}`2980`)``, `<DATE>` the day of this commit, corrected if the merge slips (workflow rule 2.4). `changelog/2980.documentation.rst`, humanized, says that the conventions test now holds a specification's figures, and names the row as `row 8 of docs spec §4` on one line.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py 2980 "changelog/2980.documentation.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py tests/test_renumbering.py tests/test_verification_report.py`, then `check-spec-status 2980` with a token, and `pixi run --frozen -e test check-spec-renumbering`.
Expected: all pass, and the docs spec's status sums to `✅ complete · 💡 1`.

- [ ] **Step 3: Commit, then run the whole suite and the docs build on that commit**

Run: the strict incremental `sphinx-build` with `-E`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/ -m "not browser"` under `xvfb-run -a`, then `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e test-py314 tests-unit`.
Expected: the build succeeds, the index shows the docs spec complete, and the suites PASS with no new skips.

- [ ] **Step 4: Push, and ask for the pull request to be marked ready**

Push, confirm it with `git ls-remote` (workflow rule 4.6), check `gh pr view 2980 --json closingIssuesReferences` lists none, and ask {user}`bjlittle` to mark it ready once the final review's fixes have landed.

## Follow-ups

None yet.

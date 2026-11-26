# Figures Read as MyST Reads Them Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 9 of docs spec §4: the figures check of docs spec §3.9 reads a figure's options and caption as MyST does, for the forms of item 6 of docs spec §8, which settles that item and {issue}`2983`.

**Architecture:** Three changes to the figures section of `tests/test_spec_conventions.py`. `directive_options` cuts the option block out of a figure's body as myst-parser does, and a new `option_values` reads it as MyST's own option parser does. A new `caption` reads the body with a CommonMark parser that knows MyST's `%` comments, and takes its first block only when that is a paragraph, as docutils' `Figure` does. `figure_faults` reports every fault of a figure, and names `{figure}` for a file nothing shows.

**Tech Stack:** pytest, `markdown-it-py` and `pyyaml`, both direct dependencies of the `test` feature.

**Spec:** `docs/src/developer/specs/2026-10-06-published-specs-design.md` (`docs spec §…`): §3.5 item 11, §3.9, §4 row 9 and §8 item 6.

## Global Constraints

- The conventions test needs no `sphinx`, build or network, and never skips (§3.5). `myst-parser` is in the `docs` feature alone, and `mdit-py-plugins` reaches the `test` environment only through `memray` → `textual`, so neither is imported.
- `markdown-it-py >=3.0.0` and `pyyaml >=6.0.3`, the `test` feature's floors: `StateBlock.is_code_block` and `yaml.BaseLoader` exist at both.
- This module sits in its own corpus: its fixtures build the section sign rather than write it, as the rest of the suite does.
- No new public name. Warnings are errors under pytest. Docstrings are NumPy style.
- Commit through the environment's `pre-commit`, after `pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: documentation`, `type: testing` and `agentic`, and closes {issue}`2983`.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-25 that row 9 is bounded, MyST's own reading fixing each form (workflow rule 2.7), and chose a hand-written reader of MyST's option grammar, once PyYAML's `BaseLoader` alone was measured failing four of the eleven figures on `main`. The other calls are mine.

1. **MyST is the reference, measured.** Every expected value below was read from myst-parser 5.1.0, the `docs` lock, on 2026-11-25, by putting each form through `myst_parser.docutils_.Parser` and its `options_to_items`. The spike is attached to the pull request.
2. **The block is cut as MyST cuts it** (`_parse_directive_options` in `myst_parser/parsers/directives.py`). A body opening `---` loses its first line, and its block runs to the first line opening with three or more dashes, dedented, the content following that line; with no such line the rest is all block and there is no content. Otherwise a body whose first non-blank character is `:` gives the block each leading line that opens `:` but not `:::`, once leading space and that colon are stripped. Any other body has no options.
3. **Values are read as MyST reads them.** A key opens at column 0 and ends at the first `:` followed by a space, a tab or the end of the line; the lines indented beneath it, and blank ones, belong to its value. A value opening with a quote, `|` or `>` is read by `yaml.load` with `BaseLoader`, which agrees with MyST there, since MyST's parser takes those scanners from PyYAML. Any other value is plain, read by hand: each line stripped and cut at a `#` that opens it or follows a space, then joined with spaces. Here MyST is laxer than YAML, so a colon inside the value, or a value opening with `` ` ``, `[`, `@` or `%`, is text. A block MyST cannot read, as text before any key or a quote left open, reads as no options, as MyST reads it (it warns, and the strict docs build fails).
4. **A caption is a paragraph.** docutils' `Figure` takes the first block of the body as the caption only if it is a paragraph; any other first block, a comment included, gives no caption. `caption` parses with `MYST`, a `MarkdownIt("commonmark")` with a `%` line-comment rule copied from `line_comment` in `mdit_py_plugins.myst_blocks`, registered as it is there, before `blockquote`, interrupting `paragraph`, `reference`, `blockquote` and `list`. Only that rule: MyST's `(name)=` target and `+++` break would also open a body with something other than a paragraph, but item 6 names neither.
5. **Every fault of a figure.** A target not named as `figures/<stem>/<file>`, or naming no file, no longer hides that figure's alt text and caption faults.
6. **The message names the directive:** `<file>: shown by no {figure} directive`.
7. **No decision changes.** §2 decision 9 stays verified by row 8, since row 9 corrects how its check reads, so §10 is unchanged. §3.5 item 11 and §3.9 say the check reads as MyST does, item 6 of §8 becomes `🏁 Resolved` citing this pull request (workflow rule 4.7), and row 9 is marked in the first commit and the last (workflow rule 2.4).
8. **One fragment, `3020.documentation.rst`.** The branch is `docs/spec-figures-myst`, and the plan is the first commit of draft pull request {pull}`3020` (workflow rule 2.3).

## Review Focus

1. **The figures on `main` still pass,** four of whose alt texts hold a colon: `test_every_specification_keeps_its_figures` (Task 1, Step 5).
2. **A value YAML would type** reads as its text: `:alt: 2026` and `alt: null` (Task 1, Step 1).
3. **A caption wrapped across lines** reads whole (Task 1, Step 1).
4. **An option block never closed** reads as no options and no content, so no alt text and no caption (Task 1, Step 1).

---

Measured on 2026-11-26 at `147dd63d`: eighteen specifications, two of which show figures, the layers spec ten and the diagram spec one, all written with `:alt:` lines, each caption one paragraph.

### Task 1: Reading as MyST Reads

**Files:**
- Modify: `tests/test_spec_conventions.py` (the figures section, `directive_options` to `figure_faults`, and its tests)

**Interfaces:**
- Produces: `MYST: MarkdownIt`, `line_comment(state: StateBlock, start: int, end: int, silent: bool) -> bool`, `option_values(block: str) -> dict[str, str]`, `caption(content: str) -> str`. `directive_options(body: str) -> tuple[dict[str, str], str]` keeps its signature, and `shown` fills `Figure.caption` from `caption`.

- [x] **Step 1: Write the fixture tests**

```python
@pytest.mark.parametrize(
    ("options", "alt"),
    [
        (":alt: A demo.", "A demo."),
        (':alt: "A demo."', "A demo."),
        (":alt: A demo: seen whole.", "A demo: seen whole."),
        (":alt: `code` and [a, b]", "`code` and [a, b]"),
        (":alt: 2026", "2026"),
        (":alt: A demo # a comment", "A demo"),
        ("---\nalt:\n  A demo.\n---", "A demo."),
        ("----\nalt: A demo.\n----", "A demo."),
        ("---\nalt: >-\n  A demo\n  seen whole.\n---", "A demo seen whole."),
        ("---\nalt: 'it''s a demo'\n---", "it's a demo"),
        ("---\nalt: null\n---", "null"),
        ("---\nalt:\n---", ""),
        ("---\nalt: 'unclosed\n---", ""),
    ],
)
def test_shown_reads_options_as_myst_does(options, alt):
    (item,) = shown(f"```{{figure}} figures/x/a.png\n{options}\n\nThe demo.\n```\n")
    assert item.alt == alt


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("The demo.", "The demo."),
        ("The demo,\nwrapped.", "The demo,\nwrapped."),
        ("- a legend item", ""),
        ("% a comment\n\nThe demo.", ""),
        ("%\n\nThe demo.", ""),
        ("The demo.\n   \nThe legend.", "The demo."),
        ("The demo.\n% a note\nThe legend.", "The demo."),
    ],
)
def test_shown_reads_the_caption_as_myst_does(body, expected):
    (item,) = shown(f"```{{figure}} figures/x/a.png\n:alt: A demo.\n\n{body}\n```\n")
    assert item.caption == expected


def test_shown_reads_an_unclosed_block_as_options_alone():
    (item,) = shown(
        "```{figure} figures/x/a.png\n---\nalt: A demo.\n\nThe demo.\n```\n"
    )
    assert (item.alt, item.caption) == ("", "")
```

`test_figure_faults_reports_every_fault_of_a_figure`: `figure("elsewhere/a.png", alt=None, caption="")` gives three faults, ending `not named as …/<file>`, `has no alt text` and `has no caption`, and `figure(f"{DEMO_FIGURES}/gone.png", alt=None)` gives two, `does not exist` and `has no alt text`. `test_figure_faults_finds_a_file_no_figure_shows` asserts `shown by no {figure} directive`.

- [x] **Step 2: Run them to see them fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py -k "shown or figure_faults"`
Expected: FAIL: the colon, next-line, four-dash, folded, quoted and unclosed forms, every caption but the first two, the faults hidden behind a target, and the message.

- [x] **Step 3: Write the reader**

As Calls 2 to 6 say. `option_values` returns `{}` for a block MyST cannot read, `directive_options` returns `({}, body)` for a body with no options, and `figure_faults` checks alt text and caption whatever the target. Keep the existing tests passing unchanged, the message aside.

- [x] **Step 4: Run them to see them pass**

Run: the command of Step 2.
Expected: PASS.

- [x] **Step 5: Run the whole module**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py`
Expected: PASS, `test_every_specification_keeps_its_figures` included.

- [x] **Step 6: Watch each clause fail when it regresses** (workflow rule 2.6)

Mutate one at a time, run Step 2's command, see the named test fail, and revert: the block cut at exactly `---`, not three or more dashes (four-dash case); plain values read by `BaseLoader` (colon and backtick cases); the `#` comment not cut (comment case); quoted values read by hand as their raw text (`'it''s a demo'`); the comment rule removed (`%` captions); the caption taken from any first block (list case); the target fault `continue`d again (`..._every_fault_of_a_figure`); and the old message (`..._no_figure_shows`).

- [x] **Step 7: Commit**

```bash
git add tests/test_spec_conventions.py
git commit -m "test: read a figure's options and caption as MyST does (docs spec row 9)"
```

### Task 2: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (§3.5 item 11, §3.9, §4 row 9, §8 item 6)
- Modify: this plan's checkboxes, before merge
- Create: `changelog/3020.documentation.rst`

- [x] **Step 1: Say what the check reads, settle the item, and land the row**

Humanized (workflow rule 3.1): §3.9's last paragraph and §3.5 item 11 add that the check reads a figure's options and caption as MyST does. Item 6 of §8 becomes ``🏁 Resolved (<DATE>, {pull}`3020` · 🔎 2026-11-17, {pull}`2980` · 🎫 {issue}`2983`)``, its text saying what this pull request did. Row 9 becomes ``✅ landed (<DATE>, {pull}`3020`)``, `<DATE>` the day of this commit, corrected if the merge slips. The fragment says that the conventions test reads a figure as MyST does, and names `row 9 of docs spec §4` on one line.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py 3020 "changelog/3020.documentation.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py tests/test_renumbering.py tests/docs/test_geovista_status.py`, then `pixi run --frozen -e test check-spec-renumbering`, and `check-spec-status` for 3020 with a token.
Expected: all pass, and the docs spec sums to `✅ complete · 💡 2`.

- [x] **Step 2: Commit, then build and run the suites on that commit**

Run: the strict incremental `sphinx-build` with `-E`, then `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e test-py314 tests-unit`.
Expected: the build succeeds, and the suite PASSES with no new skips.

- [x] **Step 3: Push, confirm with `git ls-remote` (workflow rule 4.6), and ask for the pull request to be marked ready**

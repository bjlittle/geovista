# Roadmap Row Order Diagrams: A Pull Request's Diagrams Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 3 of diagram spec §9: the verification report draws each specification's diagram, with its key, and a job runs it on each push to a pull request, for the specifications that pull request changes, writing it to the job summary (diagram spec §4.7), which settles §8 item 1 ({issue}`2997`).

**Architecture:** The report gains a diagram after each specification's roadmap, drawn by the grammar's `diagram` and `diagram_key` as the documentation draws them, without links (diagram spec §4.6), its key in a `<details>` block. `verification_report.py` gains `--changed FILE`, naming the specifications a diff touches. A `report` job beside the status references job of `ci-spec-status.yml` reads the pull request's diff as that job does and runs it.

**Tech Stack:** Python, GitHub Actions, Mermaid in GitHub-flavoured Markdown, pytest.

**Spec:** `docs/src/developer/specs/2026-11-18-row-order-diagrams-design.md` (`diagram spec §…`): §2 decisions 6 and 8, §4.6, §4.7, §8 item 1 and §9 row 3.

## Global Constraints

- **The report stays a view, never a gate** (ledger spec §3.8, diagram spec §4.7): it exits 0 whatever it finds, and 2 only when it cannot read a specification; the job fails only when the report cannot run.
- **The job reads the repository only, and runs on `pull_request`**, the trigger zizmor leaves alone (§4.7): `permissions: contents: read`, `persist-credentials: false`.
- **The report's diagrams carry no links** (§4.6), so no `click` lines, and no tooltips with them.
- **Every diagram carries its key** (§2 decision 6).
- Actions are pinned by commit, as the workflow's others are. Warnings are errors. Every pixi run is `pixi run --frozen -e geovista …`; commit through the environment's `pre-commit`, whose zizmor hook reads the workflow. The fragment credits ``(:user:`claude`)`` (workflow rule 4.9); the pull request carries `type: documentation` and `agentic`, and closes {issue}`2997`.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-20 that diagram spec §9 row 3 is bounded (workflow rule 2.7). These calls are mine; the first two are **for review**.

1. **The job sits in `ci-spec-status.yml`. For review.** A `report` job beside `references`, on the same `pull_request` trigger, reading the diff the same way: one workflow holds the specifications' checks and their view, and its row in the Testing page's table gains a paragraph. A workflow of its own would duplicate the trigger, the concurrency and the diff.
2. **The front matter moves into the grammar. For review.** `DIAGRAM_FRONT_MATTER` and `KEY_FRONT_MATTER` join `geovista_citations`, where the report reads them as the documentation's extension does, so a diagram is drawn alike on both. The extension keeps its names, bound to the grammar's.
3. **`--changed FILE`.** The report reads the NUL-separated paths of `git diff --name-only -z --no-renames`, as the references job writes them, and reports each specification among them that still exists, in the order of the collection; with none, it says `No specification changed.` and exits 0. The prefix argument keeps working.
4. **The key in `<details>`.** GitHub folds a `<details>` block, as the documentation folds its dropdown: `<details><summary>Key</summary>`, a blank line, the fenced key, a blank line, `</details>`.
5. **Row 3 verifies decisions 6 and 8**, and settles §8 item 1 as ``🏁 Resolved``; every row then has landed, so the specification reads `✅ complete`.
6. **One fragment, `3004.documentation.rst`.** The branch is `docs/diagram-spec-row3`; this plan is the first commit of draft pull request {pull}`3004`, which marks the row in progress (workflow rules 2.3, 2.4).

## Review Focus

1. **A change removing a specification**: its path is in the diff but its file is gone, so it is not reported, and the report does not fail. `test_main_reports_no_specification_a_change_removed` (Task 2).
2. **A change to a figure, a plan, or the index**, under the specifications' folder but no specification: no diagram is drawn for it. `test_main_reports_only_specifications_among_the_changes` (Task 2).
3. **A path with a space or a non-ASCII character**, as `git diff -z` writes it unquoted: read whole. `test_main_reads_a_changed_path_whole` (Task 2).
4. **A specification whose roadmap has no ordering** still draws its rows, as decision 10 has every roadmap draw. `test_report_draws_a_roadmap_without_an_ordering` (Task 1).
5. **The rendered summary**: GitHub's Mermaid reads the front matter and draws the diagram and the folded key. Seen on this pull request's own job summary, screenshotted (Task 4).

---

### Task 1: The Report Draws Each Diagram

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py` (`DIAGRAM_FRONT_MATTER`, `KEY_FRONT_MATTER`, moved from the extension)
- Modify: `docs/src/_ext/geovista_roadmap_diagrams.py` (bind its two names to the grammar's)
- Modify: `.github/scripts/verification_report.py` (`_diagram`, called in `report` after the roadmap)
- Test: `tests/test_verification_report.py`

**Interfaces:**
- Produces: `geovista_citations.DIAGRAM_FRONT_MATTER: str`, `geovista_citations.KEY_FRONT_MATTER: str` (the extension's present values); `_diagram(owner: str, texts: Mapping[Path, str], names: Namespace) -> list[str]` (Markdown lines).

- [ ] **Step 1: Write the failing tests**

- `test_report_draws_each_specification_s_diagram`: over the `repo` fixture, the report holds, after `### Roadmap` and its table, `### Diagram`, then a ```` ```mermaid ```` fence whose text is `DIAGRAM_FRONT_MATTER + diagram(rows, …)` for the demo roadmap, with no `click`. Holds diagram spec §2 decision 8.
- `test_report_folds_the_key_beneath_each_diagram`: `<details><summary>Key</summary>`, the fenced `KEY_FRONT_MATTER + diagram_key()`, `</details>`. Holds diagram spec §2 decision 6.
- `test_report_draws_a_roadmap_without_an_ordering` (Review Focus 4).
- `test_a_specification_without_a_roadmap_draws_no_diagram`: the `lone` specification of the fixture, which has none.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_verification_report.py -k "diagram or key"`
Expected: FAIL.

- [ ] **Step 2: Move the front matter and write `_diagram`.** `_diagram` reads the edges, statuses and labels with the grammar, takes `roadmap_view(owner, …)`, and draws `diagram(rows, edges, statuses, labels, small=small)`, no links; a roadmap with no rows gives no lines.

Run: the command of Step 1, then `tests/docs/test_geovista_roadmap_diagrams.py` and `tests/docs/test_geovista_citations.py`. Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "feat: draw each specification's diagram in the verification report (diagram spec §4.7)"`

### Task 2: The Specifications a Change Names

**Files:**
- Modify: `.github/scripts/verification_report.py` (`main`, `changed_specifications`)
- Test: `tests/test_verification_report.py`

**Interfaces:**
- Produces: `changed_specifications(paths: Iterable[str], specs: Sequence[Path], root: Path) -> list[Path]`; `main` reads `--changed FILE`.

- [ ] **Step 1: Write the failing tests**

- `test_main_reports_the_specifications_a_change_names`: a changed file naming the demo specification and `src/code.py` → the report holds demo's heading alone.
- `test_main_reports_no_specification_a_change_removed` (Review Focus 1).
- `test_main_reports_only_specifications_among_the_changes` (Review Focus 2): a figure, a plan and `index.rst` → `No specification changed.`, exit 0.
- `test_main_reads_a_changed_path_whole` (Review Focus 3).
- `test_main_still_reads_a_prefix`.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_verification_report.py -k "main_"`
Expected: FAIL.

- [ ] **Step 2: Write them.** `main` accepts `--changed FILE` or a prefix; the changed file is split on NUL, empty names dropped, each read relative to the root.

Run: the same. Expected: PASS.

- [ ] **Step 3: Commit** — `git commit -m "feat: report the specifications a change names (diagram spec §4.7)"`

### Task 3: The Job

**Files:**
- Modify: `.github/workflows/ci-spec-status.yml` (`report` job)
- Modify: `docs/src/developer/testing.rst` (the row of `ci-spec-status.yml`), `docs/src/developer/specs/index.rst` (the verification report's paragraph)
- Test: `tests/test_verification_report.py`

- [ ] **Step 1: Write the failing test** `test_the_workflow_runs_the_report_on_each_pull_request`: reading the workflow's YAML, the `report` job runs only on `pull_request`, with `permissions: {contents: read}`, checks out with `fetch-depth: 0` and `persist-credentials: false`, writes the diff with `--name-only -z --no-renames`, and runs `verification_report.py --changed`. Holds diagram spec §2 decision 8.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_verification_report.py -k workflow`
Expected: FAIL.

- [ ] **Step 2: Write the job and the pages**, humanized: the Testing row says that on a pull request the workflow also writes the verification report of the specifications it changes to its job summary, with their diagrams; the index's paragraph on the report says so.

Run: the command of Step 1, `pre-commit run --files .github/workflows/ci-spec-status.yml` (zizmor, actionlint), and the strict incremental `sphinx-build`. Expected: PASS, no finding, no warning.

- [ ] **Step 3: Commit** — `git commit -m "ci: run the verification report on each pull request (diagram spec §4.7)"`

### Task 4: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-18-row-order-diagrams-design.md` (§9 row 3, §8 item 1, §11 decisions 6 and 8)
- Create: `changelog/3004.documentation.rst`

- [ ] **Step 1: Watch each clause fail when it regresses** (workflow rule 2.6): the report without its diagram, or with links, or its key unfolded or gone; a removed specification reported, or one changed left out; the job on another trigger, or with write permission.
- [ ] **Step 2: See it on GitHub** (Review Focus 5, workflow rule 3.5): push, open this pull request's `report` job summary, check the diagram and the folded key render, and screenshot it for {user}`bjlittle`. If GitHub's Mermaid refuses the front matter, ledger a ruling and draw the report's diagrams without it.
- [ ] **Step 3: Mark and settle.** Row 3 becomes ``✅ landed (<DATE>, {pull}`3004`)``; §2 decisions 6 and 8 ``✅ verified (<DATE>, {pull}`3004`)`` with their evidence; §8 item 1 ``🏁 Resolved (<DATE>, {pull}`3004` · …)``, the pull request closing {issue}`2997` (workflow rule 4.7). The fragment, humanized, names row 3 of diagram spec §9.

Run: the changelog check, the spec suites, `check-spec-status --pull 3004` with a token, `check-spec-renumbering`, the strict `sphinx-build` with `-E`, `tests/docs -m "not browser"` under `xvfb-run -a`, and `tests-unit` on `test-py314`.
Expected: PASS, and diagram spec reads `✅ complete`.

- [ ] **Step 4: Push**, confirm with `git ls-remote` (workflow rule 4.6), and ask {user}`bjlittle` to mark the pull request ready once the final review's fixes have landed.

## Follow-ups

None yet.

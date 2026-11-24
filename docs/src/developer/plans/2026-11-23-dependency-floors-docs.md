# The Documentation Floors Job Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 5 of floors spec §9: the `floors-docs` pixi environment, the weekly `docs` job of `ci-floors.yml` that builds the documentation in it, each `docs` floor that build disproves raised, and their pages.

**Architecture:** `floors-docs` joins `[tool.pixi.environments]` beside `floors`, carrying `devs`, `docs` and the oldest version feature, solved alone at `lowest-direct`, and locked. The `docs` job of `ci-floors.yml` installs it with `--frozen` and runs the documentation's own `make` task, which builds `html-noplot` with `--fail-on-warning`. A failed scheduled run opens one issue, or comments on the open one, as the `pypi` job's report does. `tests/test_python_support.py` already holds every floors environment it finds by name, and `tests/test_ci_floors.py` holds the job.

**Tech Stack:** pixi (`solve-strategy = "lowest-direct"`), GitHub Actions (`prefix-dev/setup-pixi`), Sphinx, bash, pytest, PyYAML.

**Spec:** `docs/src/developer/specs/2026-11-15-dependency-floors-design.md` (`floors spec §…`): §2 decisions 4, 6, 9 and 10, §4.1, §4.2, §4.3 (`ci-floors.yml`'s `docs` job), §4.5 (the rows marked 5), §6, §9 row 5.

## Global Constraints

- The environment is `floors-docs = { features = ["devs", "docs", "py313"], solve-strategy = "lowest-direct" }`, after `floors` in `[tool.pixi.environments]`, with no solve-group (§4.1, §2 decision 9). It is locked with `pixi lock`, and a lowered floor is followed by `pixi update --environment floors-docs <package>` (§4.1).
- The job is `docs` in `ci-floors.yml`, named `floors docs`, on `ubuntu-22.04`, granted `contents: read` and `issues: write` alone. It checks out with `fetch-depth: 0` and `persist-credentials: false`, and installs with `prefix-dev/setup-pixi@9936258fee697aff89b3fed6ca1f80a382ef694e`, `environments: floors-docs`, `frozen: true`, `cache-write: false`.
- Its build step is named `docs floors`. It runs `xvfb-run -a pixi run --frozen -e floors-docs geovista --report`, then, as its last command, `xvfb-run -a pixi run --frozen -e floors-docs make`: the `make` task's default target, `html-noplot`, with the `Makefile`'s `--fail-on-warning` (§4.3, §2 decision 4). Neither the job nor the workflow sets `SPHINXOPTS`, which the `Makefile` reads with `?=`, so setting it would drop `--fail-on-warning`. The job restores no data, since `html-noplot` draws nothing.
- Its last step, `report failure`, runs `if: ${{ failure() && github.event_name == 'schedule' }}`. It comments on the open issue titled `chore: docs floors failure`, or opens one with the labels `bot` and `new: issue`, as the `pypi` job's report does. The body links the run and `https://geovista.readthedocs.io/en/latest/developer/documentation.html#gv-developer-documentation-continuous-integration`, calls a floor the likely cause, and says to raise it on both sides in one commit, then run `pixi lock` (§4.2).
- No job of `ci-floors.yml` carries an `if`, so each runs on every trigger. The workflow's triggers stay `schedule` and `workflow_dispatch` alone.
- Every action is pinned by its commit SHA, and an expression reaches a shell only through `env`, so `zizmor` passes. A floor is raised on both sides in one commit and followed by `pixi lock`, and the pull request names each floor it raises (§4.2).
- `pixi lock` and `pixi update` are the only commands run without `--frozen`. Warnings are errors under pytest. Every Python file carries the copyright header and `from __future__ import annotations`. `AGENTS.md` and `tests/AGENTS.md` stay under 200 lines.
- Commit through `pixi run --frozen -e geovista git commit ...`, after `pixi run --frozen -e devs pre-commit run --files <paths>`. The fragment is `changelog/3010.internal.rst`, crediting ``(:user:`claude`)``. The pull request carries `agentic`, `type: gha`, `type: testing`, `type: documentation` and `type: dependencies`, and closes no issue.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-23 that the specification fixes how row 5 behaves (workflow rule 2.7), with three calls of mine agreed then: the `docs` job reports through its own step, titled `chore: docs floors failure`, modelled on the `pypi` job's; it restores no data, since `html-noplot` draws nothing; and the pull request is tested as row 3's was, through a throwaway `pull_request` trigger that marks the trigger test `xfail(strict=True)` in the same commit, then a throwaway broken `docs` floor, both reverted, with `ci-floors.yml` run by hand once it merges. The rest are mine.

1. **The build runs under `xvfb-run -a`**, as `ci-docs.yml`'s does, so that an import reaching for a display finds one, and `geovista --report` comes first to record the versions the build ran, as the summary freeze does for the `pypi` job.
2. **The command names its environment**, `pixi run --frozen -e floors-docs make`, as §4.3 writes it, rather than leaning on what `setup-pixi` activates.
3. **The tests join `tests/test_ci_floors.py`**, which holds `ci-floors.yml`. Row 5 verifies §2 decision 4 with it and `tests/test_python_support.py`. §2 decision 6 stays pending until a failure has been read.
4. **The build is first run locally**, `pixi run --frozen -e floors-docs make`, so that a floor it disproves is raised before the first run on CI, as row 1 did for `floors`.
5. **The fragment is `internal`**, as rows 1, 3 and 4 were. A floor the build raises is named in it.
6. **The branch is `floors/row5-docs`.** The plan is the first commit of draft pull request {pull}`3010` (workflow rule 2.3), which also marks row 5 `🚧 in progress ({pull}`3010`)` (workflow rule 2.4).

## Review Focus

1. **`lowest-direct` lifting a `docs` floor.** `sphinx-book-theme` pins `pydata-sphinx-theme` exactly, so their floors may not resolve together, and the solve then lifts one in silence (§4.1). Read the lock's `floors-docs` versions against the floors after `pixi lock`, and name each lifted one in the pull request (Task 1, Step 4).
2. **A warning at an old floor.** A `docs` floor that builds but warns fails the build under `--fail-on-warning`. That is a floor the build disproves, to be raised (§4.2), not a warning to suppress (Task 1, Step 5).
3. **`SPHINXOPTS` set anywhere in the workflow.** The `Makefile` reads it with `?=`, so it would replace `--fail-on-warning` and the job would pass on warnings. `test_the_docs_job_builds_with_the_documentations_own_strictness` pins it (Task 2).
4. **A `docs` floor on Python 3.13.** The other docs environments run the newest Python alone, so a `docs` dependency whose floor has no release for 3.13 meets this environment first. `pixi lock` fails or lifts it (Task 1).
5. **The throwaway trigger left behind.** `test_the_workflow_runs_each_week_and_by_hand` fails while `pull_request` is a trigger, so the reverted state is checked by the suite, not by memory (Tasks 2 and 3).

---

### Task 1: The floors-docs Environment

**Files:**
- Modify: `pyproject.toml`, `pixi.lock`
- Modify (as found): `requirements/pypi-optional-docs.txt`, `requirements/pypi-optional-devs.txt`
- Modify: `tests/test_ci_floors.py`

**Interfaces:**
- Produces: the environment `floors-docs`, for Task 2.

- [ ] **Step 1: Write the failing test** `test_the_docs_floors_environment_carries_the_docs`: in `pyproject.toml`, `[tool.pixi.environments].floors-docs` has features `{"devs", "docs"}` plus exactly one `py3XY` feature, and `solve-strategy == "lowest-direct"` (§2 decision 4). And `test_the_docs_floors_environment_is_locked`: `pixi.lock`'s `environments` block declares `floors-docs:`, its body holding `solve-strategy: lowest-direct`, read as `tests/test_floors.py`'s `test_the_floors_environment_is_locked` reads it.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_ci_floors.py tests/test_python_support.py`. Expected: FAIL, the two new tests alone, as no `floors-docs` exists.
- [ ] **Step 3: Add the environment** to Global Constraints, with a comment naming floors spec §4.1, and run `pixi lock`.
- [ ] **Step 4: Run Step 2's command.** Expected: PASS, the floors tests of `tests/test_python_support.py` now reading `floors-docs` too. Read the lock's `floors-docs` direct dependencies against their floors, and note each lifted one (Review Focus 1). Break each clause once: drop `docs`, put `py314` for `py313`, add a solve-group, drop the strategy. Watch a test fail each time, then restore and `git checkout -- pixi.lock`.
- [ ] **Step 5: Build the documentation at the floors**, `pixi run --frozen -e floors-docs make`. If it fails at a floor, find by hand the lowest release under which it builds (§4.2), raise it in its `requirements/pypi-optional-*.txt` file and its `pixi` table in one commit naming each raised floor, run `pixi lock`, and build again. Repeat until it builds. Expected: the strict build passes.
- [ ] **Step 6: Commit** as `build: the floors-docs environment, each docs dependency at its floor (floors spec row 5)`, with any floor raised in Step 5 committed before it as its own commit.

### Task 2: The docs Job

**Files:**
- Modify: `.github/workflows/ci-floors.yml`
- Modify: `tests/test_ci_floors.py`

**Interfaces:**
- Consumes: `floors-docs` (Task 1); `stub`, `run_step`, `_step`, `_commands`, `_unwrapped`, `_workflow`, `_triggers` and `_calls` of `tests/test_ci_floors.py`.
- Produces: constants `DOCS_JOB = "docs"`, `DOCS_STEP = "docs floors"`, `DOCS_TITLE = "chore: docs floors failure"`, `DOCS_GUIDE` (the guide URL of Global Constraints); `_docs_job() -> dict[str, Any]`.

- [ ] **Step 1: Write the failing tests:**
  - `test_the_docs_job_builds_in_the_docs_floors_environment`: one step installs with `setup-pixi`, `environments == "floors-docs"` and `frozen is True`, after the one checkout; and `DOCS_STEP`'s last command, unwrapped of `xvfb-run -a`, is exactly `["pixi", "run", "--frozen", "-e", "floors-docs", "make"]`.
  - `test_the_docs_job_builds_with_the_documentations_own_strictness`: `SPHINXOPTS` appears in no `env` of the workflow, the job or any of its steps, and in no line of `DOCS_STEP`'s `run`. Its docstring says why: the `Makefile`'s `?=`.
  - `test_the_docs_build_decides_its_step`: the `make` command is `DOCS_STEP`'s last, and no line of it holds `;`, `|` or `&`.
  - `test_the_docs_job_may_read_and_report_and_nothing_more`: its `permissions == {"contents": "read", "issues": "write"}`.
  - Extend `test_the_workflow_runs_each_week_and_by_hand` so that no job of the workflow carries an `if`, and no step running `floors-pypi` or `DOCS_STEP` does.
  - `test_the_docs_report_runs_on_a_failed_weekly_run_alone`, and `test_the_docs_report_opens_an_issue_or_comments_on_the_open_one` parametrized as the `pypi` job's pair, with `DOCS_TITLE`, `DOCS_GUIDE`, `likely` and `pixi lock` in the body.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_ci_floors.py`. Expected: FAIL, as `ci-floors.yml` has no `docs` job.
- [ ] **Step 3: Add the job** to Global Constraints, after `pypi`, with the comment on its permissions the `pypi` job carries. Extend the `# Reference:` header with `prefix-dev/setup-pixi`.
- [ ] **Step 4: Run Step 2's command, and** `pixi run --frozen -e devs pre-commit run --files .github/workflows/ci-floors.yml`. Expected: PASS, `zizmor` included. Break each clause once: `-e docs` for `-e floors-docs`, `frozen: false`, `make html` for `make`, a `SPHINXOPTS: "-W"` in the workflow's `env`, `|| true` after `make`, an `if` on the job, `contents: write`, and the report on any failure. Watch each fail, then restore.
- [ ] **Step 5: Commit** as `ci: build the documentation at its floors each week in ci-floors.yml (floors spec row 5)`.

### Task 3: The First Runs

**Files:**
- Modify (throwaway, then reverted): `.github/workflows/ci-floors.yml`, `tests/test_ci_floors.py`, one `docs` floor on both sides, `pixi.lock`

- [ ] **Step 1: Run the workflow on this pull request**, as one throwaway commit: add `pull_request:` to `ci-floors.yml`'s triggers, and mark `test_the_workflow_runs_each_week_and_by_hand` `xfail(strict=True)`, with a reason naming the throwaway, since the `pypi` job runs the suite too. Commit as `ci: throwaway, run ci-floors.yml on this pull request`, and push.
- [ ] **Step 2: Read the `floors docs` run.** If the build fails at a floor that passed locally, raise it as Task 1, Step 5 does, in a commit of its own, and push. Repeat until it is green, with `floors pypi` green beside it. Ledger each run's URL.
- [ ] **Step 3: Break one floor**, as a throwaway commit: lower one `docs` floor on both sides to a release that installs on the oldest Python but fails the strict build, then `pixi update --environment floors-docs <package>` and `pixi lock`. Watch `floors docs` go red at `docs floors`, not at `setup pixi` (workflow rule 2.6). Ledger the run.
- [ ] **Step 4: Revert both throwaway commits**, the broken floor first, and push. Confirm `pixi run --frozen -e test pytest tests/test_ci_floors.py` passes, that no `pull_request` trigger remains, and that `pixi.lock` matches Task 2's.

### Task 4: The Guide and the Record

**Files:**
- Modify: `docs/src/developer/packaging.rst`, `docs/src/developer/documentation.rst`, `docs/src/developer/testing.rst`, `AGENTS.md`
- Modify: `docs/src/developer/specs/2026-11-15-dependency-floors-design.md`
- Create: `changelog/3010.internal.rst`

- [ ] **Step 1: Add `floors-docs` to `packaging.rst`'s Pixi Solve-Groups** (§4.5): the paragraph naming the one environment in no solve-group names two, the Pixi Floors Environment table gains its row (`{default}`, `{devs}`, `{docs}`, `{py3xx}`, as the `docs` environment for the **oldest** feature, each direct dependency at its floor), and the `pixi update --environment` sentence names either environment.
- [ ] **Step 2: Add the weekly build to `documentation.rst`'s Continuous Integration** (§4.5). The section has no label yet, so give it `.. _gv-developer-documentation-continuous-integration:` and its `tippy-` twin, as `testing.rst`'s carries, so that the report's link lands on it. Add a row for `ci-floors.yml` in its workflow grid, with a `|ci-floors|` badge and a `ci-floors.yml` link target beside the others. It says that the `docs` job builds `html-noplot` in the `floors-docs` environment each week with `--fail-on-warning`, that a failing scheduled run opens an issue titled `chore: docs floors failure`, or comments on the open one, whose likely cause is a `docs` floor, raised on both sides in one commit, then `pixi lock`, and that it runs by hand with `gh workflow run ci-floors.yml`. In `testing.rst`'s `ci-floors.yml` row, one sentence says the workflow also builds the documentation at its floors, linking that section.
- [ ] **Step 3: In `AGENTS.md`'s Python support line**, name `floors-docs` beside `floors` among what tracks the oldest version, and set Last Updated.
- [ ] **Step 4: Amend the specification.** §11 marks §2 decision 4 `✅ verified (<date>, {pull}`3010`)`, citing `tests/test_ci_floors.py` and `tests/test_python_support.py`, once each clause has been broken: weekly, locked, `devs` and `docs`, `html-noplot`, the build's strictness, and the issue.
- [ ] **Step 5: Write the fragment**, humanized: the weekly build at the `docs` floors, and each floor raised or lifted. Run `pixi run --frozen -e docs python .github/scripts/changelog.py 3010 "changelog/3010.internal.rst"`, then `pixi run --frozen -e docs make`. Expected: both pass, and the build is strict.
- [ ] **Step 6: Run the suite** `pixi run --frozen -e geovista pytest -m "not image" --numprocesses logical --dist worksteal`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status 3010`. Expected: both pass, judged by exit code.
- [ ] **Step 7: Commit** the guide, `AGENTS.md`, specification and fragment as `docs: the guide and the record for the documentation floors job (floors spec row 5)`. Then mark the row `✅ landed (<date>, {pull}`3010`)` in §9 as the last commit, `docs: mark row 5 of the floors spec landed` (workflow rule 2.4).

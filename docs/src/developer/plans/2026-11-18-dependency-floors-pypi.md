# The pip Floors Job Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 3 of floors spec §9: the `floors-pypi` composite action, the weekly `pypi` job of a new `ci-floors.yml` that runs it against the checkout, each `pip` floor that job disproves raised, and its page.

**Architecture:** The composite action creates a `uv` environment on the Python of the `floors` environment, installs its target with the `test` and `exam` extras under `--resolution lowest-direct`, retrying the install once, writes the freeze to the step summary, restores the data through the two cache actions, and runs the suite without the image tests. The cache actions learn to run their commands from `PATH` rather than through `pixi`. `ci-floors.yml` runs the action each week and by hand, and a failed scheduled run opens one issue, or comments on the open one. `tests/test_ci_floors.py` holds all three to the specification, running their shell steps against stand-in commands, as `tests/test_ci_locks.py` does.

**Tech Stack:** GitHub Actions (composite actions, `astral-sh/setup-uv`), `uv`, bash, pytest, PyYAML, Sphinx.

**Spec:** `docs/src/developer/specs/2026-11-15-dependency-floors-design.md` (`floors spec §…`): §2 decisions 6, 8, 9 and 10, §4.2, §4.3 (`ci-floors.yml` and the composite action), §4.5 (the row marked 3), §6, §9 row 3.

## Global Constraints

- The action is `.github/workflows/composite/floors-pypi/action.yml`, with two required inputs: `target`, what to install (`.` for the checkout, or the path of a wheel, for row 4), and `cache_period`, passed to the cache actions. Its steps are named `setup uv`, `uv install`, `uv freeze`, `cartopy cache`, `geovista cache` and `tests floors pypi`.
- `setup uv` is `astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2  # v10.3.3` (released 2026-10-28), with `python-version` the minor version the `floors` environment's version feature pins (`"3.13"` today, §2 decision 9), `activate-environment: true` and `enable-cache: false`.
- `uv install` runs `uv pip install --resolution lowest-direct "${TARGET}[test,exam]"`, at most twice: the one retry is for a fault of the index (§4.3). `uv freeze` appends `uv pip freeze`, fenced, to `${GITHUB_STEP_SUMMARY}`.
- `tests floors pypi` runs `xvfb-run -a geovista --report`, then, as its last command, `xvfb-run -a pytest -m "not image" --numprocesses logical --dist worksteal`: what the `tests not image` legs of `ci-tests.yml` run (§2 decision 10). A failing test is never retried.
- `cartopy-cache` and `geovista-cache` gain an optional input `pixi`, default `"true"`. `"false"` runs `cartopy_feature_download` and `geovista` from `PATH`; today's callers pass nothing and are unchanged.
- `ci-floors.yml` runs on `schedule` (`"33 1 * * 1"`, each Monday at 01h33) and `workflow_dispatch` alone, with top-level `permissions: {}`, the `concurrency` and `defaults` of `ci-tests-pypi.yml`, and its workflow `env` (`CARTOPY_SHARE_DIR`, `GEOVISTA_POOCH_MUTE`, `PYVISTA_OFF_SCREEN`, `PY_COLORS`, `SHELLOPTS: "errexit:pipefail"`).
- Its job `pypi` is named `floors pypi`, runs on `ubuntu-22.04`, is granted `contents: read` and `issues: write` alone, checks out with `fetch-depth: 0` and `persist-credentials: false`, computes `CACHE_PERIOD` as `ci-tests.yml` does, and runs the action with `target: "."`.
- Its last step, `report failure`, runs `if: ${{ failure() && github.event_name == 'schedule' }}`. It comments on the open issue titled `chore: pypi floors failure`, or opens one with the labels `bot` and `new: issue`, as `ci-locks.yml`'s report does. The body links the run and `https://geovista.readthedocs.io/en/latest/developer/testing.html#gv-developer-testing-continuous-integration`, and says to raise the floor on both sides in one commit, then run `pixi lock` (§4.2).
- Every action is pinned by its commit SHA, and an expression reaches a shell only through `env`, so `zizmor` passes. A floor is raised on both sides in one commit and followed by `pixi lock`. The pull request names each floor it raises (§4.2).
- `pixi lock` is the only command run without `--frozen`. Warnings are errors under pytest. Every Python file carries the copyright header and `from __future__ import annotations`. `AGENTS.md` and `tests/AGENTS.md` stay under 200 lines.
- Commit through `pixi run --frozen -e geovista git commit ...`, after `pixi run --frozen -e devs pre-commit run --files <paths>`. The fragment is `changelog/2996.internal.rst`, crediting ``(:user:`claude`)``. The pull request carries `agentic`, `type: testing` and `type: documentation`, and closes no issue.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-18 that the specification fixes how row 3 behaves (workflow rule 2.7), with two calls made then: the cache actions gain an input to run without `pixi`, rather than the action copying their steps; and, since `workflow_dispatch` starts only a workflow that is on `main`, a throwaway commit adds a `pull_request` trigger to watch the job pass and fail, the pull request amends §6 to say so, and `ci-floors.yml` is run by hand once it merges. The rest are mine.

1. **`setup-uv` creates the environment**, rather than `setup-python` and a `pip install uv`. It creates and activates a virtual environment on the Python asked for, as §4.3 reads, and dependabot's `github-actions` entry already covers `/.github/workflows/composite/*`, so its SHA moves with the others.
2. **The action's Python is held to the `floors` environment's**, read from `pyproject.toml`, not to a literal. A SPEC 0 bump that moves `floors` then fails until the action follows, and the `AGENTS.md` line naming what tracks the oldest version names the action.
3. **The step runner is shared, as fixtures.** `_stub` and `_run` of `tests/test_ci_locks.py` become the fixtures `stub` and `run_step` of `tests/conftest.py`, since no test module can import another, and `tests/test_ci_locks.py` takes them.
4. **The tests are `tests/test_ci_floors.py`, with no `CHECK`**, as `tests/test_floors.py` and `tests/test_ci_locks.py` have none. Row 3 verifies §2 decision 8 with it. §2 decision 10 stays pending until row 4 adds the last job that runs the suite, and §2 decision 6 until a weekly failure has been read.
5. **The throwaway commits are reverted, not rewritten away**, so nothing is force-pushed, and the squash merge carries neither. §6 is amended for rows 3 and 5, whose workflow is new.
6. **The schedule is Monday at 01h33**, weekly, clear of the jobs that start at 00h0x, and a day after `ci-locks.yml` opens its lock pull request.
7. **The fragment is `internal`**, as row 1's was, since the job changes nothing a user installs. A floor the job raises is named in the fragment as well as in the pull request.
8. **The branch is `floors/row3-pypi`.** The plan is the first commit of draft pull request {pull}`2996` (workflow rule 2.3), which also marks row 3 `🚧 in progress ({pull}`2996`)` (workflow rule 2.4).

## Review Focus

1. **`lowest-direct` stopping at the target.** If `uv` treats only `.[test,exam]` as direct, it resolves `geovista`'s own requirements at their highest, and the job passes while testing nothing at the floors. The first green run's freeze must show each requirement at its floor, or at the lowest release that resolves (Task 4, Step 3).
2. **A wheel as the target**, as row 4 passes: `${TARGET}[test,exam]` must read `dist/geovista-0.6.0-py3-none-any.whl[test,exam]`. A case of `test_the_install_takes_the_extras_at_their_lowest` (Task 2). Whether `uv` accepts it is row 4's to measure.
3. **A composite action inside a composite action.** The callers write `uses: $/.github/...` (from #2458), and nothing here nests one yet. If the first run cannot resolve it, use `./.github/...` and ledger the ruling (Task 4, Step 2).
4. **Tests that skip at the `pip` floors.** A test that skips for a package `pip` does not install passes in silence. Compare the first green run's skips with the latest `ci-tests-pypi.yml` run's, and account for each extra one (Task 4, Step 3).
5. **The throwaway trigger left behind.** `test_the_workflow_runs_each_week_and_by_hand` fails while `pull_request` is a trigger, so the reverted state is checked by the suite, not by memory (Tasks 3 and 4).

---

### Task 1: The Cache Actions Without pixi

**Files:**
- Modify: `.github/workflows/composite/cartopy-cache/action.yml`, `.github/workflows/composite/geovista-cache/action.yml`
- Modify: `tests/conftest.py`, `tests/test_ci_locks.py`, `tests/AGENTS.md`
- Create: `tests/test_ci_floors.py`

**Interfaces:**
- Produces: in `tests/conftest.py`, the fixture `stub`, a `Callable[[str, str], None]` writing an executable `tmp_path / "bin" / name` running the given bash body, and the fixture `run_step`, a `Callable[[dict[str, Any], dict[str, str]], subprocess.CompletedProcess[str]]` running a parsed step's `run` under `bash -e -o pipefail` in `tmp_path`, with the step's literal `env`, then the caller's, and `tmp_path / "bin"` first on `PATH`. Both share the test's `tmp_path`. In `tests/test_ci_floors.py`, `_action(name: str) -> dict[str, Any]` (the parsed `composite/<name>/action.yml`) and `_step(steps: list[dict[str, Any]], name: str) -> dict[str, Any]`.

- [ ] **Step 1: Move `_stub` and `_run` into the fixtures**, and point `tests/test_ci_locks.py` at them, with no assertion changed. Run `pixi run --frozen -e test pytest tests/test_ci_locks.py`. Expected: PASS, its tests unchanged in number.
- [ ] **Step 2: Write the failing tests** in a new `tests/test_ci_floors.py`, its docstring saying it holds the jobs at the `pip` floors to floors spec §4.3:
  - `test_the_cache_actions_run_through_pixi_by_default`, parametrized over both actions: `inputs.pixi` is `{"required": False, "default": "true", ...}`.
  - `test_a_cache_action_runs_its_command_through_pixi_unless_told_not_to`, parametrized over (`cartopy-cache`, `refresh cartopy cache`, `cartopy_feature_download`), (`geovista-cache`, `get geovista-data version`, `geovista`) and (`geovista-cache`, `refresh geovista cache`, `geovista`), each with `INPUTS_PIXI` `"true"` and `"false"`. Stubs of `pixi` and of the command log their arguments, and `GITHUB_OUTPUT` is a file. Under `"true"` the log's first word is `pixi`. Under `"false"` it is the command, and `pixi` never runs.
- [ ] **Step 3: Run** `pixi run --frozen -e test pytest tests/test_ci_floors.py`. Expected: FAIL, as no action declares `pixi`.
- [ ] **Step 4: Add the input** to both actions, passed to each step's shell as `INPUTS_PIXI`. Under `"false"`, a step runs its command bare. Otherwise it runs as today, keeping `geovista-cache`'s `pixi_environment` branches.
- [ ] **Step 5: Run Step 3's command.** Expected: PASS. Break each clause once: default `pixi` to `"false"`, then make one step ignore `INPUTS_PIXI`. Watch the matching test fail each time, then restore.
- [ ] **Step 6: Name the fixtures** in `tests/AGENTS.md`'s list of the root `conftest.py`'s fixtures, then commit as `ci: let the cache actions run without pixi (floors spec row 3)`.

### Task 2: The floors-pypi Action

**Files:**
- Create: `.github/workflows/composite/floors-pypi/action.yml`
- Modify: `tests/test_ci_floors.py`

**Interfaces:**
- Consumes: `stub`, `run_step`, `_action` and `_step` (Task 1); the cache actions' `pixi` input (Task 1).
- Produces: the action and its inputs `target` and `cache_period`, as Global Constraints names them, for Task 3 and row 4.

- [ ] **Step 1: Write the failing tests:**
  - `test_the_action_installs_on_the_python_of_the_floors_environment`: `setup uv`'s `with.python-version` equals the `X.Y` of the `python` pin (`"X.Y.*"`) of the `pyXYZ` feature that `[tool.pixi.environments].floors` carries. Its `activate-environment` is true and its `uses` is pinned to a 40-character SHA.
  - `test_the_install_takes_the_extras_at_their_lowest`, parametrized over `TARGET` `.` and `dist/geovista-0.6.0-py3-none-any.whl`. A `uv` stub logs its arguments, and the log is exactly `pip install --resolution lowest-direct <TARGET>[test,exam]`.
  - `test_the_install_is_retried_once`, parametrized over a stub failing once (the step passes, two calls) and failing always (the step fails, two calls).
  - `test_the_freeze_is_written_to_the_summary`: with a `uv` stub printing `numpy==2.2.6` for `pip freeze`, the `GITHUB_STEP_SUMMARY` file holds that line.
  - `test_the_action_restores_the_data_without_pixi`: the `cartopy cache` and `geovista cache` steps use the two cache actions, with `pixi: "false"` and `cache_period: ${{ inputs.cache_period }}`, and come before `tests floors pypi`.
  - `test_the_action_leaves_out_the_image_tests`: `tests floors pypi` runs `pytest` once, under `xvfb-run -a`, with the `-m` value that one `marker` of `ci-tests.yml`'s `tests` matrix carries, `not image`.
  - `test_the_suite_decides_the_step`: that `pytest` command is the step's last, and no line of the step holds `;`, `|` or `&`.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_ci_floors.py`. Expected: FAIL, as the action does not exist.
- [ ] **Step 3: Write the action** to Global Constraints, `TARGET: ${{ inputs.target }}` reaching `uv install` through `env`, and each `run` step with `shell: bash`. Call the cache actions with the `uses:` form their callers use.
- [ ] **Step 4: Run Step 2's command.** Expected: PASS. Break each clause once: `highest` for `lowest-direct`, drop `exam`, drop the retry, `3.14` for the Python, drop `-m "not image"`, append `|| true`. Watch each fail, then restore.
- [ ] **Step 5: Commit** as `ci: install the pip floors with uv in a composite action (floors spec row 3)`.

### Task 3: The ci-floors.yml Workflow

**Files:**
- Create: `.github/workflows/ci-floors.yml`
- Modify: `tests/test_ci_floors.py`

**Interfaces:**
- Consumes: the `floors-pypi` action (Task 2); `stub` and `run_step` (Task 1).

- [ ] **Step 1: Write the failing tests**, reading triggers as `tests/test_floors.py`'s `_triggers` does (PyYAML keys `on` by `True`):
  - `test_the_workflow_runs_each_week_and_by_hand`: the triggers are exactly `schedule` and `workflow_dispatch`, with one cron whose day of month and month are `*` and whose day of week is one day.
  - `test_the_workflow_grants_nothing_by_default`: `permissions == {}`.
  - `test_the_pypi_job_may_read_and_report_and_nothing_more`: the `pypi` job's `permissions == {"contents": "read", "issues": "write"}`.
  - `test_the_pypi_job_runs_the_action_against_the_checkout`: one step uses the `floors-pypi` action, with `target: "."`, after the checkout.
  - `test_the_report_runs_on_a_failed_weekly_run_alone`, and `test_the_report_opens_an_issue_or_comments_on_the_open_one` parametrized over no open issue (`create`, titled `chore: pypi floors failure`, `--label bot`) and an open `42` (`comment 42`). They take `test_ci_locks.py`'s two report tests as their model, with a body holding the run's URL and the testing guide's.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_ci_floors.py`. Expected: FAIL, as the workflow does not exist.
- [ ] **Step 3: Write the workflow** to Global Constraints, with its `# Reference:` header in the style of `ci-tests-pypi.yml`.
- [ ] **Step 4: Run Step 2's command, and** `pixi run --frozen -e devs pre-commit run --files .github/workflows/ci-floors.yml .github/workflows/composite/*/action.yml`. Expected: PASS, `zizmor` included. Break each clause once: add `pull_request`, grant `contents: write`, run the report on any failure, and title the issue another way. Watch each fail, then restore.
- [ ] **Step 5: Commit** as `ci: run the pip floors each week in ci-floors.yml (floors spec row 3)`.

### Task 4: The First Runs

**Files:**
- Modify (throwaway, then reverted): `.github/workflows/ci-floors.yml`, one `requirements/pypi-*.txt`
- Modify (as found): `requirements/pypi-*.txt`, `pyproject.toml`, `pixi.lock`

- [ ] **Step 1: Add a throwaway `pull_request:` trigger** to `ci-floors.yml`, committed as `ci: throwaway, run ci-floors.yml on this pull request`, and push. `test_the_workflow_runs_each_week_and_by_hand` goes red meanwhile, as expected.
- [ ] **Step 2: Read the `floors pypi` run.** If the nested `uses:` fails to resolve, rule for `./.github/...` (Review Focus 3). If the install fails, or a test fails at a floor, find by hand the lowest release under which the job passes (§4.2). Raise it in `requirements/pypi-*.txt` and the `pixi` table in one commit, with each raised floor named in its message, run `pixi lock`, and push. Repeat until the job is green. Ledger each run's URL.
- [ ] **Step 3: Read the green run's freeze and log.** Each requirement sits at its floor, or at the lowest release that resolves (Review Focus 1). If `uv` resolved them at their highest, stop and ask. Account for each skip beyond the latest `ci-tests-pypi.yml` run's (Review Focus 4). Confirm `tests floors` is green on the same head, after any `pixi lock`.
- [ ] **Step 4: Break one floor**, as a throwaway commit: lower one `pip` floor alone, such as `pyvista`'s, to a release that installs on the oldest Python but fails the suite. Watch `floors pypi` go red at `tests floors pypi`, not at `uv install`, choosing another floor if the install fails (workflow rule 2.6). Ledger the run.
- [ ] **Step 5: Revert both throwaway commits**, the broken floor first, and push. Then confirm `pixi run --frozen -e test pytest tests/test_ci_floors.py` passes, and that no `pull_request` trigger remains.

### Task 5: The Guide and the Record

**Files:**
- Modify: `docs/src/developer/testing.rst`, `AGENTS.md`
- Modify: `docs/src/developer/specs/2026-11-15-dependency-floors-design.md`
- Create: `changelog/2996.internal.rst`

- [ ] **Step 1: Add a row to the Testing Workflows grid of `testing.rst`**, with a `|ci-floors|` badge and a `ci-floors.yml` link target beside the others (§4.5). It says that the `pypi` job installs `.[test,exam]` at its floors with `uv` on the oldest supported Python each week, and runs the tests without the image tests. A failing scheduled run opens an issue titled `chore: pypi floors failure`, or comments on the open one. That issue means a `pip` floor fails from PyPI, and the remedy is to raise it on both sides in one commit, then run `pixi lock`. The job runs by hand with `gh workflow run ci-floors.yml`.
- [ ] **Step 2: In `AGENTS.md`'s Python support line**, add the `floors-pypi` action to what tracks the oldest version, and set Last Updated.
- [ ] **Step 3: Amend the specification.** §4.3 says the action runs the cache actions from its `uv` environment rather than through `pixi`. §6 says rows 3 and 5 land once their job has passed, and been seen to fail, on their pull request through a throwaway `pull_request` trigger, since `workflow_dispatch` starts only a workflow that is on `main`, and that the workflow is run by hand once it merges. §11 marks §2 decision 8 `✅ verified (<date>, {pull}`2996`)`, citing `tests/test_ci_floors.py`.
- [ ] **Step 4: Write the fragment**, humanized: the weekly job at the `pip` floors, and each floor it raised. Run `pixi run --frozen -e docs python .github/scripts/changelog.py 2996 "changelog/2996.internal.rst"`, then `pixi run --frozen -e docs make`. Expected: both pass, and the build is strict.
- [ ] **Step 5: Run the suite** `pixi run --frozen -e geovista pytest -m "not image" --numprocesses logical --dist worksteal`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status 2996`. Expected: both pass, judged by exit code.
- [ ] **Step 6: Mark the row** `✅ landed (<date>, {pull}`2996`)` in §9 as the last commit (workflow rule 2.4), and commit it with the docs, `AGENTS.md` and fragment as `docs: the guide and the record for the pip floors job (floors spec row 3)`.

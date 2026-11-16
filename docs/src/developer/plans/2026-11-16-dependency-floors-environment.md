# The Floors Environment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of floors spec §9: the locked `floors` environment and the Python support test's account of it, the `tests floors` job of `ci-tests.yml`, the `pyarrow` floor it disproves raised, and its pages.

**Architecture:** `floors` joins `[tool.pixi.environments]` with the `devs`, `py313` and `test` features, `solve-strategy = "lowest-direct"` and no solve-group, and is locked in `pixi.lock`. `tests/test_python_support.py` passes a floors environment over by its name and holds each of its properties. A `floors` job of `ci-tests.yml`, outside the `tests` matrix, runs what the `tests not image` legs run, in `floors`, with `--frozen`. A new `tests/test_floors.py` holds the job to the spec.

**Tech Stack:** pixi 0.84.2 (the version `ci-locks.yml` last ran), GitHub Actions, pytest, PyYAML in the tests.

**Spec:** `docs/src/developer/specs/2026-11-15-dependency-floors-design.md` (`floors spec §…`): §2 decisions 1, 2, 3, 9, 10 and 11, §3.3, §4.1, §4.2, §4.3 (its first bullet), §4.5 (the rows marked 1), §6, §9 row 1.

## Global Constraints

- The environment is exactly `floors = { features = ["devs", "py313", "test"], solve-strategy = "lowest-direct" }`, in a block of its own after the `py314` block, since taplo sorts keys within a block (§4.1, §2 decision 9).
- `pyarrow` in `[tool.pixi.feature.devs.pypi-dependencies]` becomes `">=18.0.0,<27"`, its first release with a wheel for Python 3.13. `requirements/pypi-optional-exam.txt` is left alone, since row 2 copies the floor (§4.2).
- `pixi lock` runs under pixi 0.84.2 or later. pixi 0.81 reads the lock's `virtual-packages` as stale and re-solves all fifteen environments, so check `pixi --version` first, and stop and ask {user}`bjlittle` to run `pixi self-update` if it is older.
- The lock gains `floors` and nothing else: `git diff pixi.lock` removes no line.
- The job's check is named `tests floors`. It runs on every trigger of `ci-tests.yml`, with no `if`, no `continue-on-error` and no matrix, and the `coverage` job does not need it (§4.3, §2 decision 11).
- Actions are pinned as `ci-tests.yml` pins them: `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`, `prefix-dev/setup-pixi@9936258fee697aff89b3fed6ca1f80a382ef694e`, and the two cache composites by the same `uses:` the `tests` job writes.
- Every `pixi run` carries `--frozen`. Warnings are errors under pytest. Every Python file carries the copyright header and `from __future__ import annotations`.
- Commit through `pixi run --frozen -e geovista git commit ...`, after `pixi run --frozen -e devs pre-commit run --files <paths>`. The fragment is `changelog/2974.internal.rst`, crediting ``(:user:`claude`)``. The pull request carries `agentic`, `type: testing`, `type: gha` and `type: dependencies`, closes no issue, and names each floor it raised (§4.2).

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-16 that the specification fixes how row 1 behaves (workflow rule 2.7), with the first two calls below. The rest are mine.

1. **The job's tests go in a new `tests/test_floors.py`**, which rows 3 to 5 extend with their jobs. The environment's properties go in `tests/test_python_support.py`, as §4.1 says. `tests/test_dependency_floors.py` stays the name of row 2's check.
2. **Row 1 verifies §2 decisions 1, 2, 3 and 9.** Decision 10 stays pending until row 4 adds the last job at the floors, though Task 2's test already cites it. Decision 11 is signed off by {user}`bjlittle` in a later pull request, once the check is in the branch protection of `main`.
3. **Only `pyarrow` is raised.** A run of `floors` on 2026-11-16, from `main` at 2b525476 under pixi 0.81 in a scratch tree that declared it alone, resolved every direct dependency at its floor except three the solve lifted: click 8.2.1 to 8.3.0, netcdf4 1.7.2 to 1.7.4, rasterio 1.4.3 to 1.5.0, which §4.1 and §4.6 leave alone. The suite without the image tests then passed 5,185, and its six failures came from the scratch manifest, which declared no other environment.
4. **The job names its environment**, as `pixi run --frozen -e floors pytest ...`, rather than relying on `activate-environment` as the `tests` job does, so a test can see which environment it runs.
5. **The job uploads nothing.** With no image test, there are no failed images, and no coverage is measured at the floors.
6. **No pixi task is added.** The guide gives `pixi run --frozen -e floors tests-unit "not image"`, since `floors` carries the `test` feature.
7. **The branch is `floors/row1-environment`.** The plan is the first commit of draft pull request {pull}`2974` (workflow rule 2.3), which also marks row 1 `🚧 in progress` (workflow rule 2.4).

## Review Focus

1. **A floors job that cannot fail.** `continue-on-error` on the job would let a red floor merge. `test_the_floors_job_can_fail` (Task 2).
2. **A floors job running another environment.** A `pixi run` without `-e floors` runs the lock's newest versions under a green `tests floors`. `test_the_floors_job_runs_the_floors_environment` (Task 2).
3. **A floors environment without the core floors.** `no-default-feature = true` drops `[tool.pixi.dependencies]`, so the core floors go untested. `test_a_floors_environment_carries_the_core_dependencies` (Task 1).
4. **Coverage waiting on the floors.** `coverage` needing `floors` would let a red floor stop the report. `test_the_floors_job_stands_outside_the_tests_matrix` (Task 2).
5. **A version in the check's name.** `tests floors (py313)` would leave the branch protection naming a check that a SPEC 0 bump renames. `test_the_floors_check_names_no_version` (Task 2).

---

### Task 1: The Floors Environment

**Files:**
- Modify: `tests/test_python_support.py`
- Modify: `pyproject.toml` (`[tool.pixi.environments]`, `[tool.pixi.feature.devs.pypi-dependencies]`)
- Modify: `pixi.lock`

**Interfaces:**
- Produces: the `floors` environment, and in `tests/test_python_support.py` the constant `FLOORS = "floors"` and the helpers `_floors(name: str) -> bool` (true for `floors` and any `floors-<tier>`) and `_oldest() -> str` (the `pyXYZ` feature pinning the oldest version, as `_newest` does the newest).

- [ ] **Step 1: Write the tests**, each citing its decision in its docstring:
  - `test_there_is_a_floors_environment`: `FLOORS` is declared.
  - `test_a_floors_environment_solves_at_its_lowest` (§2 decision 1): each floors environment has `solve-strategy == "lowest-direct"`.
  - `test_a_floors_environment_carries_the_oldest_version` (§2 decision 9): `_pinned(name) == {_oldest()}`.
  - `test_a_floors_environment_solves_alone` (§2 decision 9): no `solve-group` key.
  - `test_floors_carries_the_test_environments_features` (§2 decision 3): the features of `floors` and of `test`, each without its `pyXYZ` feature, are equal.
  - `test_a_floors_environment_carries_the_core_dependencies` (Review Focus 3): no floors environment sets `no-default-feature`.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_python_support.py`. Expected: FAIL, no `floors`.
- [ ] **Step 3: Teach the existing rules the third kind.** `test_every_unversioned_environment_is_in_the_primary_solve_group` passes over `_floors(name)`, and the module docstring adds a sentence on floors environments. The other rules already pass `floors` over, since it is named for no version and solves in no version's group.
- [ ] **Step 4: Add the environment and raise `pyarrow`**, as Global Constraints give them, then `pixi --version` (0.84.2 or later), `pixi lock`, and `git diff pixi.lock | grep -c '^-[^-]'`. Expected: 0.
- [ ] **Step 5: Confirm the floors** with `pixi list --frozen -e floors '^(numpy|pyarrow|pyvista)$'`. Expected: 18.0.0, 2.2.6, 0.49.0.
- [ ] **Step 6: Run** `pixi run --frozen -e test pytest tests/test_python_support.py tests/test_ci_typing.py tests/test_dependency_ceilings.py`. Expected: PASS.
- [ ] **Step 7: Break each property** (workflow rule 2.6, §6), one at a time in the manifest only: `py314` for `py313`, the strategy removed, `solve-group = "py313"` added, `docs` for `test`, `no-default-feature = true`, and the environment renamed `floor`. Run the file under each and watch the named test fail, then restore.
- [ ] **Step 8: Commit** as `deps: lock a floors environment, and raise the pyarrow floor (floors spec row 1)`.

### Task 2: The `tests floors` Job

**Files:**
- Modify: `.github/workflows/ci-tests.yml`
- Create: `tests/test_floors.py`

**Interfaces:**
- Consumes: the `floors` environment (Task 1).
- Produces: the job `floors` of `ci-tests.yml`, named `tests floors`.

- [ ] **Step 1: Write the tests** in `tests/test_floors.py`, reading the workflow with `yaml.safe_load`, under which the key `on` reads as `True`:
  - `test_the_floors_job_runs_on_every_pull_request` (§2 decision 2): the triggers hold `pull_request` with no `paths`, `paths-ignore` or `branches`, and the job has no `if`.
  - `test_the_floors_environment_is_locked` (§2 decision 2): `pixi.lock`, read as text, declares `floors` under `environments:`, and the job's `setup-pixi` step has `environments: "floors"` and `frozen: true`.
  - `test_the_floors_job_runs_the_floors_environment` (§2 decision 2, Review Focus 2): every `pixi run` in the job's steps reads `pixi run --frozen -e floors`.
  - `test_the_floors_job_leaves_out_the_image_tests` (§2 decision 10): its `pytest` carries `-m "not image"`, `--numprocesses logical` and `--dist worksteal`, as the `tests` job's does.
  - `test_the_floors_job_stands_outside_the_tests_matrix` (§4.3, Review Focus 4): no `strategy`, and `floors` is not in `coverage`'s `needs`.
  - `test_the_floors_check_names_no_version` (§2 decision 11, Review Focus 5): its `name` is `tests floors`.
  - `test_the_floors_job_can_fail` (Review Focus 1): no `continue-on-error`.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_floors.py`. Expected: FAIL, no job.
- [ ] **Step 3: Write the job**, after `tests` and before `coverage`, with `ALLOW_PLOTTING: true`, `runs-on: "ubuntu-22.04"`, and the `tests` job's checkout, cache period, cache composites and `xvfb-run` steps, its `setup-pixi` step installing `floors`, and its last step running `xvfb-run -a geovista --report` then `xvfb-run -a pixi run --frozen -e floors pytest -m "not image" --numprocesses logical --dist worksteal`, with `PY_COLORS: "1"`.
- [ ] **Step 4: Run** the tests, `tests/test_python_support.py`, and `pixi run --frozen -e devs pre-commit run --files .github/workflows/ci-tests.yml tests/test_floors.py`, which runs `zizmor` and the workflow schema. Expected: PASS.
- [ ] **Step 5: Break each clause** (workflow rule 2.6): an `if: false`, a `-e test`, `-m image`, a `strategy`, `floors` in `coverage`'s `needs`, the name `tests floors (py313)`, `continue-on-error: true`, and `floors` dropped from the lock's text. Watch the named test fail under each, then restore.
- [ ] **Step 6: Commit** as `ci: run the suite at the floors on every pull request (floors spec row 1)`.

### Task 3: The Guide

**Files:**
- Modify: `docs/src/developer/packaging.rst` (Pixi Solve-Groups)
- Modify: `docs/src/developer/testing.rst` (Continuous Integration)

- [ ] **Step 1: Describe the environment** in Pixi Solve-Groups, after the `py3xx` groups: a short section with a table of `floors` and its features in the form of the tables above it, saying that it solves alone, each direct dependency at its floor and each transitive one at its newest, on the oldest supported Python; that `pixi lock` re-solves it when a floor moves and the weekly `pixi update` moves only its transitive dependencies; and that a floor the solve could not use shows in the lock as the version it was lifted to. It cites floors spec §4.1.
- [ ] **Step 2: Describe the job** in the `ci-tests.yml` row of the Testing Workflows table: the `tests floors` check, required on `main`, which runs the suite without the image tests in `floors`; how to run it locally, `pixi run --frozen -e floors tests-unit "not image"`; and where to raise a floor when it goes red on a bot's pull request, on the branch of a dependabot pull request, and in a pull request merged ahead of the weekly lock pull request. It cites floors spec §2 decision 11.
- [ ] **Step 3: Build** with `pixi run --frozen -e docs make`. Expected: no warning.
- [ ] **Step 4: Commit** as `docs: describe the floors environment and its check (floors spec row 1)`.

### Task 4: The Record

**Files:**
- Modify: `docs/src/developer/specs/2026-11-15-dependency-floors-design.md` (§9 row 1, §11)
- Modify: `AGENTS.md`
- Create: `changelog/2974.internal.rst`

- [ ] **Step 1: See the job fail once** (§6): push a throwaway commit lowering `pyvista` to `">=0.46.0,<0.50.0"` with its `pixi lock`, watch `tests floors` go red on {pull}`2974`, then drop it with a standalone `git push --force-with-lease=floors/row1-environment:<sha>`. If the suite passes at 0.46, go lower. Record the run in the pull request.
- [ ] **Step 2: Mark the decisions verified**: §2 decisions 1, 3 and 9 with `tests/test_python_support.py`, and §2 decision 2 with `tests/test_floors.py`, each `✅ verified (<date>, {pull}`2974`)`.
- [ ] **Step 3: Update `AGENTS.md`**, keeping it under 200 lines: the Python support line adds the floors environments to what tracks the **oldest** version, beside `mypy`, and the note added by {pull}`2972` names its cause, a local pixi older than CI's 0.84.2.
- [ ] **Step 4: Write the fragment**, humanized, and check it with `pixi run --frozen -e docs python .github/scripts/changelog.py 2974 "changelog/2974.internal.rst"`.
- [ ] **Step 5: Run** `pixi run --frozen -e test pytest tests/test_spec_conventions.py tests/test_renumbering.py tests/test_workflow_rules.py` and `pixi run --frozen -e test check-spec-status 2974`. Expected: PASS.
- [ ] **Step 6: Mark row 1 landed** in the last commit, `✅ landed (<date>, {pull}`2974`)`, once `tests floors` has passed on the pull request, and correct the date if the merge slips a day (workflow rule 2.4). Commit as `docs: land row 1 of floors spec §9`.

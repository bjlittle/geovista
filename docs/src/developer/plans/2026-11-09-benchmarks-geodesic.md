# Benchmarks and the Geodesic Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of bench spec §9: the two plugins, `benchmarks/` and its conftest with the `geodesic` benchmarks and their memory ceilings, `ci-benchmarks.yml`, the two pixi tasks, the README badge and the testing guide's section.

**Architecture:** `pytest-codspeed` and `pytest-memray` join the `test` feature. `benchmarks/` holds one module per `geovista` module, `test_geodesic.py` first, and a `conftest.py` that builds the inputs, pins VTK to one thread, registers `limit_memory` for runs without memray, and refuses under `--memray` a benchmark that carries no ceiling. Two pixi tasks run the files, one under CodSpeed without memray and one under memray without CodSpeed. `ci-benchmarks.yml` runs each in a job of its own, installed `--frozen`. A repository test holds the workflow and the manifest to the spec's decisions.

**Tech Stack:** pytest, `pytest-codspeed` (5.0.4 on conda-forge), `pytest-memray` (1.9.0), CodSpeed in simulation mode through `CodSpeedHQ/action`, pixi, GitHub Actions, PyYAML in the tests.

**Spec:** `docs/src/developer/specs/2026-11-09-benchmarks-design.md` (`bench spec §…`): §2 decisions 1 to 8, §3.3, §4.1 to §4.5, §6, §9 row 1.

## Global Constraints

- CodSpeed runs with `mode: simulation`, on `push` to `main`, on every `pull_request` with no path, branch or label filter, and on `workflow_dispatch` (§2 decisions 1 and 2).
- Every job installs the unsuffixed `test` environment with `prefix-dev/setup-pixi`, `frozen: true`, and every `pixi run` carries `--frozen` (§2 decisions 3 and 8).
- Neither job is added to the required checks of `main` (§2 decision 4).
- Each benchmark carries `@pytest.mark.limit_memory("N MB")`, its measured peak plus 20%, rounded up to a whole MiB. pytest-memray reads `MB` as 1024² bytes, a MiB (§2 decision 5).
- Inputs are built outside the measured call, from `np.random.default_rng(0)` where random, and nothing is downloaded. VTK runs on one thread, and `OMP_NUM_THREADS` is `1` (§2 decision 7).
- A run of a pull request is cancelled by a newer one, and a run of `main` never is. `codspeed` has `contents: read` and `id-token: write`, and `memory` has `contents: read` alone (§4.4).
- Actions are pinned to commits: `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`, `prefix-dev/setup-pixi@9936258fee697aff89b3fed6ca1f80a382ef694e`, and `CodSpeedHQ/action@af75f77f17a054769abefaa42fe8dc2975469b5f`, which is v5.6.3.
- Warnings are errors and markers are strict under pytest, for the benchmarks too. Every Python file carries the copyright header and `from __future__ import annotations`.
- Commit with `PATH="$PWD/.pixi/envs/geovista/bin:$PATH" git commit ...`, after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment is `changelog/2925.internal.rst` and credits ``(:user:`claude`)``. The pull request carries `agentic`, `type: performance`, `type: testing` and `type: gha`, and names {issue}`2920` without closing it, since rows 2 and 3 remain.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-09 that the specification fixes how row 1 behaves (workflow rule 2.7), with one point left to this plan: whether CodSpeed measures through `pixi run`. The calls are mine.

1. **The CodSpeed run disables memray.** pytest-memray tracks any test that carries one of its markers, with or without `--memray` (its `pytest_pyfunc_call` checks the markers first), so under CodSpeed it would run inside Valgrind. The `benchmarks` task passes `-p no:memray`, and the conftest registers `limit_memory` itself so that `--strict-markers` still accepts it. This contradicts §2 decision 3's "neither plugin acts unless its option is passed", which Task 5 corrects as an edit that keeps the decision's meaning.
2. **`pixi run` first, the interpreter if need be.** The `codspeed` job runs `pixi run --frozen -e test benchmarks`. If CodSpeed reports no result for a benchmark that way, it runs `.pixi/envs/test/bin/python -m pytest benchmarks --codspeed -p no:memray` instead, with `OMP_NUM_THREADS` from the job, and §4.4 is corrected to match in the same pull request, as {user}`bjlittle` agreed.
3. **The tasks set `OMP_NUM_THREADS=1` themselves**, through pixi's task `env`, so a local run counts as CI does. The workflow sets it too, as §4.4 says.
4. **The ceiling rule is not a repository check.** The gate of checks spec §3.4 reads `CHECK` under `tests/` and `.github/scripts/` alone, and the refusal names what to add, citing §2 decision 5. A section on the checks page can follow if contributors meet it often.
5. **`tests/test_benchmarks.py` holds the configuration.** It reads `pyproject.toml` and `ci-benchmarks.yml` with PyYAML, which parses the key `on` as `True`, and runs the conftest with `pytester` in a subprocess.
6. **Row 1's conftest builds only what row 1 uses**: the global grid's mesh and the line. Rows 2 and 3 add the point cloud and the rest.
7. **The branch is `bench/row1-geodesic`.** The plan is the first commit of draft pull request {pull}`2925` (workflow rule 2.3), which also marks row 1 `🚧 in progress` (workflow rule 2.4).

## Review Focus

1. **A memray marker under CodSpeed.** `pytest benchmarks -p no:memray` with a benchmark carrying `limit_memory` passes, with no unknown-marker error and no tracking. `test_a_ceiling_is_accepted_without_memray` (Task 2).
2. **A ceiling set on the module.** `pytestmark = pytest.mark.limit_memory("1 MB")` carries a ceiling for every benchmark in it. `test_a_ceiling_on_the_module_is_carried` (Task 2).
3. **A parametrized benchmark without a ceiling.** The refusal names every id, as `test_x[a]` and `test_x[b]`. A case of `test_memray_refuses_a_benchmark_without_a_ceiling` (Task 2).
4. **A run with neither option.** `pytest benchmarks` runs each benchmark once and refuses nothing. `test_a_plain_run_refuses_nothing` (Task 2).
5. **A local run with OpenMP on every core.** Both tasks set `OMP_NUM_THREADS` to `1`. `test_the_tasks_run_openmp_on_one_thread` (Task 2).

---

### Task 1: The Plugins

**Files:**
- Modify: `pyproject.toml` (`[tool.pixi.feature.test.dependencies]`)
- Modify: `requirements/pypi-optional-test.txt`
- Modify: `pixi.lock`

**Interfaces:**
- Produces: `pytest-codspeed` and `pytest-memray` in every environment with the `test` feature.

- [ ] **Step 1: Add the dependencies**, in order, as `pytest-codspeed = ">=5.0.4,<5.1"` and `pytest-memray = ">=1.9.0,<2"`, and `pytest-codspeed <5.1` and `pytest-memray <1.10` to the pip file, which `tests/test_dependency_ceilings.py` requires the pixi ceilings to admit.
- [ ] **Step 2: Lock**, with `pixi lock`, then confirm with `pixi list -e test pytest-codspeed` and `pixi list -e test pytest-memray`.
- [ ] **Step 3: Run** `pixi run --frozen -e test pytest tests/test_dependency_ceilings.py tests/test_python_support.py`. Expected: PASS.
- [ ] **Step 4: Commit** as `deps: add pytest-codspeed and pytest-memray to the test feature`.

### Task 2: The Conftest and the Tasks

**Files:**
- Create: `benchmarks/__init__.py`, `benchmarks/conftest.py`
- Modify: `pyproject.toml` (two tasks in `[tool.pixi.feature.test.tasks]`; `"benchmarks/*.py"` beside `"conftest.py"` in the ruff per-file ignores, if ruff asks for annotations)
- Modify: `MANIFEST.in` (`prune benchmarks`, beside `prune changelog`)
- Modify: `docs/src/developer/testing.rst` and `docs/src/developer/packaging.rst` (a row for each task in their "Pixi Tasks" tables)
- Create: `tests/test_benchmarks.py`

**Interfaces:**
- Produces: the fixtures `grid_mesh() -> pv.PolyData`, a function-scoped `Transform.from_1d` mesh of 1° cell bounds, 360 by 180 cells, with seeded cell data named `"data"`, and `line() -> tuple[np.ndarray, np.ndarray]`, a session-scoped pair of 2,000 longitudes from `np.linspace(-170, 170, 2000)` and 2,000 latitudes from `rng.uniform(-60, 60, 2000)`; the tasks `benchmarks` and `benchmarks-memory`.

- [ ] **Step 1: Write the tests** in `tests/test_benchmarks.py`, each running a copy of `benchmarks/conftest.py` with `pytester.runpytest_subprocess`:
  - `test_memray_refuses_a_benchmark_without_a_ceiling`: under `--memray`, a module with `test_bare` and a parametrized `test_x` over `a` and `b`, none with a ceiling, fails with a `UsageError` whose text holds `bench spec §2 decision 5` and each of `test_bare`, `test_x[a]` and `test_x[b]`.
  - `test_memray_accepts_a_benchmark_with_a_ceiling`: under `--memray`, `@pytest.mark.limit_memory("64 MB")` on a benchmark passes.
  - `test_a_ceiling_on_the_module_is_carried`: under `--memray`, `pytestmark = pytest.mark.limit_memory("64 MB")` passes.
  - `test_a_ceiling_is_accepted_without_memray`: with `-p no:memray --strict-markers`, a benchmark carrying a ceiling passes.
  - `test_a_plain_run_refuses_nothing`: with no option, a benchmark without a ceiling passes, and the `benchmark` fixture calls its target once.
  - `test_the_unit_suite_never_collects_the_benchmarks` (§2 decision 6): `testpaths` in `[tool.pytest.ini_options]` is `"tests"`.
  - `test_the_tasks_run_openmp_on_one_thread` (§2 decision 7): both tasks' `env` sets `OMP_NUM_THREADS` to `"1"`.
  - `test_the_codspeed_task_runs_without_memray`: the `benchmarks` task's `cmd` is `pytest benchmarks --codspeed -p no:memray`, and `benchmarks-memory`'s is `pytest benchmarks --memray`.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_benchmarks.py`. Expected: FAIL, no `benchmarks/conftest.py` and no tasks.
- [ ] **Step 3: Write `benchmarks/conftest.py`.** At import, `vtkSMPTools.Initialize(1)` from `vtkmodules.vtkCommonCore`. `pytest_configure(config)` adds the `limit_memory(memory_limit)` marker line. `pytest_collection_modifyitems(config, items)`, when `config.getoption("memray", default=False)` is true, raises `pytest.UsageError` listing each item with no `limit_memory` in `item.iter_markers()`, by `item.name`, with the message `bench spec §2 decision 5: every benchmark carries a memory ceiling, its measured peak plus 20%, rounded up to a whole MiB, as @pytest.mark.limit_memory("N MB"). None on: <names>`. Then the two fixtures of the Interfaces block, the mesh built outside any measured call.
- [ ] **Step 4: Add the tasks**, each with `env = { OMP_NUM_THREADS = "1" }` and a `description`, and their rows on both pages, and the `MANIFEST.in` prune.
- [ ] **Step 5: Run** `pixi run --frozen -e test pytest tests/test_benchmarks.py tests/test_pixi_tasks.py`, and `pipx run check-manifest` as `ci-manifest.yml` does, or `pip`-install it into a throwaway pixi environment if `pipx` is absent. Expected: PASS.
- [ ] **Step 6: Commit** as `tests: add the benchmarks conftest and its tasks (bench spec row 1)`.

### Task 3: The Geodesic Benchmarks

**Files:**
- Create: `benchmarks/test_geodesic.py`

**Interfaces:**
- Consumes: `grid_mesh` and `line` (Task 2).

- [ ] **Step 1: Write the benchmarks**, each handing one call to `benchmark`, citing §2 decision 7 in its docstring, and carrying a placeholder `@pytest.mark.limit_memory("1 GB")`:
  - `test_line(benchmark, line)`: `benchmark(geodesic.line, *line)`, asserting more points than 2,000.
  - `test_npoints(benchmark)`: `npoints(-120.0, -45.0, 150.0, 60.0, npts=10_000)`, asserting 10,000 longitudes.
  - `test_bbox_enclosed(benchmark, grid_mesh)`: `BBox([-30, 30, 30, -30], [-20, -20, 40, 40]).enclosed(grid_mesh)`, the box built outside the call, asserting at least one cell.
  - `test_wedge(benchmark)`: `wedge(0, 90)`, asserting a `BBox`.
- [ ] **Step 2: Add `test_every_benchmark_uses_the_fixture`** (§2 decision 6) to `tests/test_benchmarks.py`: every function named `test_*` in `benchmarks/test_*.py`, read with `ast`, takes a `benchmark` parameter, and there is at least one.
- [ ] **Step 3: Run** `pixi run --frozen -e test benchmarks`, then `pixi run --frozen -e test benchmarks-memory`, and read each benchmark's high watermark from memray's report. Expected: 4 passed under each.
- [ ] **Step 4: Set each ceiling** to that peak times 1.2, rounded up to a whole MiB, and record the four peaks and ceilings in the pull request.
- [ ] **Step 5: Run** `pixi run --frozen -e test benchmarks-memory` and `pixi run --frozen -e test pytest tests/test_benchmarks.py`. Expected: PASS.
- [ ] **Step 6: Commit** as `tests: benchmark the geodesic module (bench spec row 1)`.

### Task 4: The Workflow and the Badge

**Files:**
- Create: `.github/workflows/ci-benchmarks.yml`
- Modify: `README.md` (the CodSpeed badge after Codecov's in the Health row, as `[![CodSpeed](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://app.codspeed.io/bjlittle/geovista?utm_source=badge)`, keeping the table's padding)
- Modify: `tests/test_benchmarks.py`

**Interfaces:**
- Consumes: the tasks `benchmarks` and `benchmarks-memory` (Task 2).

- [ ] **Step 1: Write the tests**, reading the workflow with `yaml.safe_load`:
  - `test_codspeed_runs_in_simulation` (§2 decision 1): one step uses `CodSpeedHQ/action@` and has `with.mode == "simulation"`.
  - `test_every_pull_request_and_push_to_main_is_measured` (§2 decision 2): the triggers are `pull_request` with no `paths`, `paths-ignore` or `branches`, `push` whose `branches` holds `main`, and `workflow_dispatch`.
  - `test_a_run_of_main_is_never_cancelled` (§4.4): `cancel-in-progress` is `${{ github.event_name == 'pull_request' }}`.
  - `test_both_jobs_run_the_test_environment` (§2 decision 3): each job's `setup-pixi` step has `environments: "test"`, and both plugins are in the `test` feature.
  - `test_every_install_is_frozen` (§2 decision 8): each `setup-pixi` step has `frozen: true`, and every `pixi run` in a `run` or a `with.run` carries `--frozen`.
  - `test_the_jobs_ask_only_what_they_need` (§4.4): `codspeed` has `contents: read` and `id-token: write`, `memory` has `contents: read`, and the workflow's own `permissions` is `{}`.
- [ ] **Step 2: Run** them. Expected: FAIL, no workflow.
- [ ] **Step 3: Write `ci-benchmarks.yml`**, after `ci-typing.yml`'s form: the triggers, `concurrency` keyed on `${{ github.workflow }}-${{ github.ref }}`, `defaults.run.shell: bash -l {0}` with `SHELLOPTS: "errexit:pipefail"`, `env` with `OMP_NUM_THREADS: 1`, and the jobs `codspeed` ("codspeed benchmarks") and `memory` ("memory ceilings"), each checking out with `fetch-depth: 0` and `persist-credentials: false`.
- [ ] **Step 4: Run** the tests, and `pixi run --frozen -e geovista pre-commit run --files .github/workflows/ci-benchmarks.yml README.md`, which runs `zizmor` and the workflow schema. Expected: PASS.
- [ ] **Step 5: Commit** as `ci: run the benchmarks under CodSpeed and memray (bench spec row 1)`.

### Task 5: The Guide and the Correction

**Files:**
- Modify: `docs/src/developer/testing.rst` (a ":fa:`gauge-high` Benchmarks" section after Unit Tests)
- Modify: `docs/src/_static/color.css` (`.fa-gauge-high` in the branded list)
- Modify: `docs/src/developer/specs/2026-11-09-benchmarks-design.md` (§2 decision 3)
- Create: `changelog/2925.internal.rst`

- [ ] **Step 1: Write the section.** How to run both tasks; how to add a benchmark, a module per `geovista` module with its ceiling; how to read CodSpeed's comment and its gate, which never blocks a merge; and how to set a ceiling: run `benchmarks-memory` with a placeholder, read the high watermark, add 20%, round up to a whole MiB. It cites bench spec §2 decisions 4 and 5 and §4.5.
- [ ] **Step 2: Correct §2 decision 3**: replace "Neither plugin acts unless its option, `--codspeed` or `--memray`, is passed." with "`pytest-codspeed` acts only under `--codspeed`, and `pytest-memray` under `--memray` or on a test carrying one of its markers, so the CodSpeed run passes `-p no:memray`."
- [ ] **Step 3: Write the fragment**, saying `geovista` now benchmarks its `geodesic` module on every pull request with CodSpeed, with memory ceilings checked by pytest-memray, citing bench spec §9 by its row.
- [ ] **Step 4: Build** the documentation strictly with the incremental `sphinx-build` of `AGENTS.md`, plus `-W --keep-going`, and run `tests/docs/test_readingtime_coverage.py` and `tests/test_spec_conventions.py`. Expected: PASS.
- [ ] **Step 5: Commit** as `docs: describe the benchmarks in the testing guide (bench spec row 1)`.

### Task 6: Landing

- [ ] **Step 1: Push**, and confirm with `git ls-remote` (workflow rule 4.6). Watch `ci-benchmarks.yml`: `codspeed` must report a result for each of the four benchmarks, and `memory` must pass (§6). If `codspeed` reports none through `pixi run`, apply call 2.
- [ ] **Step 2: Break each verified clause** (workflow rule 2.6), one at a time, and watch its test fail: the mode, each trigger and a filter on `pull_request`, the environment of each job, `frozen` on each `setup-pixi` and `--frozen` on each `pixi run`, `testpaths`, and a benchmark without `benchmark`. Restore each.
- [ ] **Step 3: Mark the ledger**: §2 decisions 1, 2, 3, 6 and 8 `✅ verified`, with `tests/test_benchmarks.py` as Evidence, each test citing its decision. §2 decision 4 waits for {user}`bjlittle`'s `✍️ signed off`, which only the reviewer named adds (workflow rule 2.5); the Evidence says the jobs are absent from `main`'s required checks. §2 decisions 5 and 7 stay `⏳ pending`, owed by rows 1 to 3.
- [ ] **Step 4: Mark row 1** `✅ landed`, dated the day it merges (workflow rule 2.4), then run `pixi run -e test check-spec-status 2925`. Expected: all hold.
- [ ] **Step 5: Run the full suite**, `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e test tests-unit`, after the docs build and never during it. Expected: PASS.
- [ ] **Step 6: Commit** as `docs: land row 1 of bench spec §9`, and mark the pull request ready by asking {user}`bjlittle`.

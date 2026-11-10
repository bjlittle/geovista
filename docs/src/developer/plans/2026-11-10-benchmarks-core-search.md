# Benchmarks of the Core, the Search and the Gridlines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 3 of bench spec §9, the last: the `common`, `core`, `search` and `gridlines` benchmarks of §4.3. Settle §8 item 2 ({issue}`2928`), which row 3 owes, and §2 decisions 5 and 7, which rows 1 to 3 owe, so the specification completes and {issue}`2920` closes.

**Architecture:** The conftest gains a mesh of the cloud, for the `KDTree`. Four modules hand one call each to the `benchmark` fixture, with a ceiling measured as before. The gaps of §8 item 2 close first. Decision 7 is verified by tests, one for each of its clauses. Decision 5 carries a ceiling on every benchmark by test, and its measuring by {user}`bjlittle`'s sign-off.

**Tech Stack:** pytest, `pytest-codspeed`, `pytest-memray`, pykdtree, CodSpeed in simulation mode.

**Spec:** `docs/src/developer/specs/2026-11-09-benchmarks-design.md` (`bench spec §…`): §2 decisions 5 and 7, §4.2, §4.3, §8 item 2, §9 row 3, §11.

## Global Constraints

- Inputs are built in fixtures, outside the measured call, from `np.random.default_rng(0)`, and nothing is downloaded (§2 decision 7).
- Each benchmark carries `@pytest.mark.limit_memory("N MB")`: its peak under `pixi run --frozen -e test benchmarks-memory` plus 20%, rounded up to a whole MiB (§2 decision 5).
- Each benchmark's docstring cites `bench spec §2 decision 7`, and its name is the API it measures (§4.3).
- The `codspeed benchmarks` job takes no more than 10 minutes on the pull request; past that, the slowest input shrinks and §4.2 is corrected.
- Commit with `PATH="$PWD/.pixi/envs/geovista/bin:$PATH" git commit ...`. The fragment is `changelog/2936.internal.rst`, crediting ``(:user:`claude`)``. The pull request carries `agentic`, `type: performance` and `type: testing`, and closes {issue}`2920` and {issue}`2928`.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-10 that the specification fixes how row 3 behaves (workflow rule 2.7), with the plan choosing the two arguments it leaves open. The calls are mine.

1. **`find_nearest_cell` is asked for 12.3° east, 45.6° north**, a point inside a cell of the grid, not on an edge.
2. **`resize` is asked for `zlevel=1`**, one level above the surface, so the call moves every point.
3. **The `KDTree` is built from a mesh of the cloud**, made once a session with `Transform.from_points`, and queried with the cloud's first 10,000 positions.
4. **Sizes are read from the fixtures.** A benchmark asserts against `grid_data.size` or `cloud[0].size`, so `GRID_CELLS` and `CLOUD_POINTS` leave `test_bridge.py` and `test_transform.py`. `PROJECTIONS` names each value with `pytest.param(..., id=...)`.
5. **Decision 7 is verified clause by clause.**
   - **Built outside the measured call:** no argument of a `benchmark(...)` call is itself a call.
   - **Seeded:** every `default_rng` is given a seed.
   - **Nothing downloaded:** a plain run of the benchmarks leaves an empty `GEOVISTA_CACHEDIR` empty, with `PROJ_NETWORK=OFF`.
   - **One thread for VTK and OpenMP, and off screen:** the existing tests.
   - **Nothing rendered:** no benchmark names `Plotter`, `GeoPlotter`, `show`, `screenshot` or `plot`.
6. **Decision 5 is signed off.** A test shows every benchmark carries `limit_memory`, but none can show that a ceiling is its measured peak plus 20%. The pull request tables each peak and ceiling, and §11's Evidence says what {user}`bjlittle` checked; only the reviewer named adds `signed-off` (workflow rule 2.5).
7. **The branch is `bench/row3-core-search`.** The plan is the first commit of draft pull request {pull}`2936` (workflow rule 2.3), which marks row 3 `🚧 in progress` (workflow rule 2.4).

## Review Focus

1. **A benchmark that builds its input in the call.** `benchmark(f, np.arange(10))` fails the decision 7 test, naming the benchmark. A case of `test_every_input_is_built_outside_the_measured_call` (Task 2).
2. **An unseeded generator.** `np.random.default_rng()` in the conftest fails the seed test. A case of `test_every_generator_is_seeded` (Task 2).
3. **A benchmark that draws.** A benchmark naming `GeoPlotter` fails the rendering test. A case of `test_no_benchmark_renders` (Task 2).
4. **A single-core host.** `test_vtk_runs_on_one_thread` fails without the conftest's `Initialize(1)` on a single core too, with `VTK_SMP_MAX_THREADS=4`. Checked by mutation (Task 1).
5. **A benchmark in a subdirectory, or taking the fixture keyword-only.** `benchmark_functions` reads `benchmarks/sub/test_x.py`, accepts `def test_x(*, benchmark)`, and names a method `TestX::test_y`. Cases of `test_a_benchmark_in_a_class_is_read` (Task 1).

---

### Task 1: Close §8 Item 2

**Files:**
- Modify: `tests/test_benchmarks.py`, `benchmarks/test_bridge.py`, `benchmarks/test_transform.py`

- [ ] **Step 1: Change the tests.** `test_vtk_runs_on_one_thread` also sets `VTK_SMP_MAX_THREADS=4`, and its docstring says the test, not the benchmarks, runs on the threaded backend. `test_a_benchmark_in_a_class_is_read` writes `sub/test_sub.py` with `def test_k(*, benchmark)` beside `class TestX: def test_y(self)` and `async def test_z()`, and expects `[("sub/test_sub.py::test_k", True), ("test_mod.py::TestX::test_y", False), ("test_mod.py::test_z", False)]`.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_benchmarks.py`. Expected: FAIL on the class test.
- [ ] **Step 3: Rewrite `benchmark_functions(root: Path) -> list[tuple[str, bool]]`** over `root.rglob("test_*.py")`, naming each function by its path relative to `root` and its enclosing classes, and reading `args.args` and `args.kwonlyargs`. Read the sizes from the fixtures and name the projections, as call 4 says.
- [ ] **Step 4: Run** the tests and both tasks. Expected: PASS, 14 benchmarks each. Then mutate the conftest to `Initialize(4)` and watch `test_vtk_runs_on_one_thread` fail; restore.
- [ ] **Step 5: Commit** as `tests: close bench spec §8 item 2`.

### Task 2: Verify Decision 7

**Files:**
- Modify: `tests/test_benchmarks.py`

**Interfaces:**
- Produces: `benchmark_calls(root: Path) -> list[tuple[str, ast.Call]]`, every `benchmark(...)` call under `root` with the name of its function.

- [ ] **Step 1: Write the tests**, each citing `bench spec §2 decision 7`:
  - `test_every_input_is_built_outside_the_measured_call`: no positional, starred or keyword argument of a `benchmark(...)` call is an `ast.Call`, over `BENCHMARKS`; and on a written tree, `benchmark(f, np.arange(10))` is reported.
  - `test_every_generator_is_seeded`: every `default_rng` call under `BENCHMARKS` has an argument; and on a written tree, `default_rng()` is reported.
  - `test_nothing_is_downloaded`: `pytest benchmarks -p no:memray`, run with `GEOVISTA_CACHEDIR` set to an empty `tmp_path` and `PROJ_NETWORK=OFF`, passes and leaves the directory empty.
  - `test_no_benchmark_renders`: no name or attribute under `BENCHMARKS` is one of `Plotter`, `GeoPlotter`, `show`, `screenshot` or `plot`; and on a written tree, `GeoPlotter` is reported.
- [ ] **Step 2: Run** them. Expected: PASS on the tree as it stands, since the benchmarks already keep the decision; FAIL on each written counterexample if the helpers miss it.
- [ ] **Step 3: Commit** as `tests: verify bench spec §2 decision 7 clause by clause`.

### Task 3: The Benchmarks

**Files:**
- Modify: `benchmarks/conftest.py` (a session fixture `cloud_mesh() -> pv.PolyData`, `Transform.from_points(*cloud)`)
- Create: `benchmarks/test_common.py`, `benchmarks/test_core.py`, `benchmarks/test_search.py`, `benchmarks/test_gridlines.py`

- [ ] **Step 1: Write the benchmarks**, each with a placeholder `limit_memory("1 GB")`:
  - `test_from_cartesian(benchmark, grid_mesh)`: `from_cartesian(grid_mesh)`, asserting shape `(grid_mesh.n_points, 3)`.
  - `test_slice_mesh(benchmark, grid_mesh)`: `slice_mesh(grid_mesh)`, asserting at least `grid_data.size` cells.
  - `test_slice_cells(benchmark, grid_mesh)`: `slice_cells(grid_mesh, meridian=45.5)`, asserting at least as many cells.
  - `test_combine(benchmark, grid_mesh)`: `combine(*meshes)` over four copies made outside the call, asserting four times the cells.
  - `test_resize(benchmark, grid_mesh)`: `resize(grid_mesh, zlevel=1)`, asserting the same point count and a larger radius.
  - `test_kdtree(benchmark, cloud_mesh)`: `KDTree(cloud_mesh)`, asserting its `n_points` is `cloud_mesh.n_points`.
  - `test_kdtree_query(benchmark, cloud, cloud_mesh)`: the tree built outside the call, then `tree.query(cloud[0][:10_000], cloud[1][:10_000])`, asserting 10,000 indices, each its own point.
  - `test_find_nearest_cell(benchmark, grid_mesh)`: `find_nearest_cell(grid_mesh, 12.3, 45.6)`, asserting one cell.
  - `test_create_meridians(benchmark)` and `test_create_parallels(benchmark)`: with defaults, asserting at least one block.
- [ ] **Step 2: Run** `pixi run --frozen -e test benchmarks`, then `benchmarks-memory`, and set each ceiling. Expected: 24 passed under each, and `tests/test_benchmarks.py` passing.
- [ ] **Step 3: Commit** as `tests: benchmark the core, the search and the gridlines (bench spec row 3)`, with the peaks and ceilings.

### Task 4: Landing

- [ ] **Step 1: Push**, confirm with `git ls-remote`, and read the `codspeed benchmarks` job: under 10 minutes, and every benchmark measured. Past that, apply the shrink and correct §4.2.
- [ ] **Step 2: Mark the ledger.** §2 decision 7 `✅ verified`, with `tests/test_benchmarks.py`, after breaking each of its clauses and watching its test fail (workflow rule 2.6). §2 decision 5 stays `⏳ pending` until {user}`bjlittle` signs it off. §8 item 2 `🏁 Resolved`, and row 3 `✅ landed`, dated the day it merges.
- [ ] **Step 3: Write the fragment**, then run `pixi run -e test check-spec-status 2936`, the strict incremental docs build, and the full suite after it. Expected: PASS.
- [ ] **Step 4: Commit** as `docs: land row 3 of bench spec §9`, push, and ask {user}`bjlittle` to mark the pull request ready and sign off §2 decision 5.

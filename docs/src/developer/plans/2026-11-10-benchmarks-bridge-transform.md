# Benchmarks of the Bridge and the Transforms Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of bench spec §9, the `bridge` and `transform` benchmarks of §4.3, and settle §8 item 1 ({issue}`2926`), which row 2 owes.

**Architecture:** The conftest gains the inputs of §4.2 that row 1 left out: the global grid's bounds in 1-D and 2-D, its cells as nodes and connectivity, and a cloud of 100,000 points. `benchmarks/test_bridge.py` and `benchmarks/test_transform.py` hand one call each to the `benchmark` fixture, with a memory ceiling measured as row 1's were. First, the five gaps of §8 item 1 are closed in the conftest, its tests and §4.2.

**Tech Stack:** pytest, `pytest-codspeed`, `pytest-memray`, pyproj, CodSpeed in simulation mode.

**Spec:** `docs/src/developer/specs/2026-11-09-benchmarks-design.md` (`bench spec §…`): §2 decisions 5 to 7, §4.2, §4.3, §8 item 1, §9 row 2.

## Global Constraints

- Inputs are built in fixtures, outside the measured call, from `np.random.default_rng(0)` where random; nothing is downloaded (§2 decision 7).
- Each benchmark carries `@pytest.mark.limit_memory("N MB")`: its peak under `pixi run --frozen -e test benchmarks-memory`, which traces Python's allocators, plus 20%, rounded up to a whole MiB (§2 decision 5).
- Each benchmark's docstring cites `bench spec §2 decision 7`, and its name is the API it measures, as `test_from_1d` (§4.3).
- The `codspeed benchmarks` job of `ci-benchmarks.yml` takes no more than 10 minutes on the pull request. Past that, the oversized inputs shrink and §4.2 is corrected to match (call 3).
- Commit with `PATH="$PWD/.pixi/envs/geovista/bin:$PATH" git commit ...`. The fragment is `changelog/2927.internal.rst`, crediting ``(:user:`claude`)``. The pull request carries `agentic`, `type: performance` and `type: testing`, closes {issue}`2926`, and names {issue}`2920` without closing it, since row 3 remains.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-10 that the specification fixes how row 2 behaves (workflow rule 2.7), with a 10-minute ceiling on the CodSpeed job. The calls are mine.

1. **The refusal is read from the node id.** It names `item.nodeid`, considers only items whose path lies under the conftest's directory, and reads memray's switch as pytest-memray does, from the option or the `memray` ini key, with `value_or_ini` from `pytest_memray.utils`.
2. **The fixture test walks the whole tree.** `test_every_benchmark_uses_the_fixture` reads every `FunctionDef` and `AsyncFunctionDef` named `test_*` with `ast.walk`, so a method of a `Test…` class counts.
3. **Shrink only on evidence.** If the job passes 10 minutes, the benchmark taking the longest under simulation is shrunk first, the cloud to 10,000 points or the grid to 2°, and §4.2's table is corrected in the same pull request, as {user}`bjlittle` agreed.
4. **`from_unstructured` is given what a reader of UGRID gives it**: the node longitudes and latitudes of the global grid's mesh and its `regular_faces`, both built in a session fixture from `grid_mesh`'s own build.
5. **`name` is not passed.** Each bridge benchmark passes `data` alone, as the default name serves.
6. **The branch is `bench/row2-bridge-transform`.** The plan is the first commit of draft pull request {pull}`2927` (workflow rule 2.3), which marks row 2 `🚧 in progress` (workflow rule 2.4).

## Review Focus

1. **A benchmark named twice.** `test_x` in two modules, both without a ceiling, is refused naming both node ids. A case of `test_memray_refuses_a_benchmark_without_a_ceiling` (Task 1).
2. **A unit test beside the benchmarks.** `pytest --memray benchmarks tests/x.py`, with a test in `tests/x.py` that has no ceiling, refuses nothing for it. `test_the_refusal_keeps_to_the_benchmarks` (Task 1).
3. **A benchmark in a class.** `class TestX` with `def test_y(self)` taking no `benchmark` fails the fixture test. A case of `test_every_benchmark_uses_the_fixture`'s helper, run on a written tree (Task 1).
4. **A projection's point at infinity.** `transform_points` to Robinson, Mollweide and Plate Carrée maps every point of the cloud to a finite value. Asserted in `test_transform_points` (Task 3).
5. **A transform that leaves cells behind.** `transform_mesh` keeps at least the grid's cell count, as slicing at the antimeridian only adds. Asserted in `test_transform_mesh` (Task 3).

---

### Task 1: Close the Gaps of §8 Item 1

**Files:**
- Modify: `benchmarks/conftest.py`, `tests/test_benchmarks.py`
- Modify: `docs/src/developer/specs/2026-11-09-benchmarks-design.md` (§4.2's example)

**Interfaces:**
- Produces: `bare(items: Iterable[pytest.Item], root: Path) -> list[str]` in `benchmarks/conftest.py`, the node ids of the items under `root` carrying no ceiling; `benchmark_functions(root: Path) -> list[tuple[str, bool]]` in `tests/test_benchmarks.py`, each `test_*` function under `root` with whether it takes `benchmark`.

- [ ] **Step 1: Write the tests.**
  - `test_memray_refuses_a_benchmark_without_a_ceiling` gains a second module, `test_more.py`, with its own `test_bare`, and asserts both `test_bare.py::test_bare` and `test_more.py::test_bare` in the refusal.
  - `test_the_refusal_keeps_to_the_benchmarks`: a pytester tree with the conftest under `bench/` and a bare test in `unit/test_unit.py`; `pytest --memray bench/... unit/test_unit.py` with a ceiling on every benchmark passes.
  - `test_memray_on_by_ini_refuses_too`: with `memray = true` in a written `pytest.ini`, a bare benchmark is refused without `--memray`.
  - `test_a_benchmark_in_a_class_is_read`: `benchmark_functions` on a written tree holding `class TestX: def test_y(self)` and `async def test_z()` reports both, without the fixture.
  - `test_pull_requests_are_measured_of_every_type` (§2 decision 2): `pull_request` carries no `types` key.
  - `test_vtk_runs_on_one_thread` (§2 decision 7): a pytester benchmark asserts `vtkSMPTools.GetEstimatedNumberOfThreads() == 1`, and passes.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_benchmarks.py`. Expected: FAIL for the new and changed tests, on the names, the unit test, the ini key and the class.
- [ ] **Step 3: Write `bare`** and call it from `pytest_collection_modifyitems` with `Path(__file__).parent`, switching on `value_or_ini(config, "memray")`; then `benchmark_functions`, used by `test_every_benchmark_uses_the_fixture`; then add `types` to the filters the trigger test refuses.
- [ ] **Step 4: Correct §4.2's example** to `limit_memory("22 MB")`, `test_line(benchmark, line)` and `benchmark(geodesic.line, *line)`.
- [ ] **Step 5: Run** the tests and `pixi run --frozen -e test benchmarks-memory`. Expected: PASS.
- [ ] **Step 6: Commit** as `tests: name a benchmark by its node id, and close bench spec §8 item 1`.

### Task 2: The Bridge Benchmarks

**Files:**
- Modify: `benchmarks/conftest.py`
- Create: `benchmarks/test_bridge.py`

**Interfaces:**
- Consumes: `GRID_STEP` and the seeded data of `grid_mesh` (row 1).
- Produces: session fixtures `grid_bounds() -> tuple[np.ndarray, np.ndarray]`, the 361 longitudes and 181 latitudes; `grid_bounds_2d() -> tuple[np.ndarray, np.ndarray]`, their `np.meshgrid`; `grid_data() -> np.ndarray`, the 64,800 seeded cell values, which `grid_mesh` now uses too; `grid_nodes() -> tuple[np.ndarray, np.ndarray, np.ndarray]`, the node longitudes, latitudes and `regular_faces` of a mesh built from them; `cloud() -> tuple[np.ndarray, np.ndarray]`, 100,000 longitudes from `rng.uniform(-180, 180)` and latitudes from `np.degrees(np.arcsin(rng.uniform(-1, 1)))`, uniform on the sphere.

- [ ] **Step 1: Write the benchmarks**, each with a placeholder `limit_memory("1 GB")`:
  - `test_from_1d(benchmark, grid_bounds, grid_data)`: `Transform.from_1d(*grid_bounds, data=grid_data)`, asserting 64,800 cells.
  - `test_from_2d(benchmark, grid_bounds_2d, grid_data)`: `Transform.from_2d`, asserting 64,800 cells.
  - `test_from_unstructured(benchmark, grid_nodes, grid_data)`: `Transform.from_unstructured(xs, ys, connectivity=faces, data=grid_data)`, asserting 64,800 cells.
  - `test_from_points(benchmark, cloud)`: `Transform.from_points(*cloud)`, asserting 100,000 points.
- [ ] **Step 2: Run** `pixi run --frozen -e test benchmarks`. Expected: 8 passed. Then `pixi run --frozen -e test pytest tests/test_benchmarks.py`. Expected: PASS.
- [ ] **Step 3: Measure** with `pixi run --frozen -e test benchmarks-memory`, set each ceiling, and run it again. Expected: 8 passed.
- [ ] **Step 4: Commit** as `tests: benchmark the bridge (bench spec row 2)`, the peaks and ceilings in the message.

### Task 3: The Transform Benchmarks

**Files:**
- Create: `benchmarks/test_transform.py`

**Interfaces:**
- Consumes: `grid_mesh` (row 1), `cloud` (Task 2), `geovista.crs.WGS84`.

- [ ] **Step 1: Write the benchmarks**, over `PROJECTIONS = ["+proj=robin", "+proj=moll", "+proj=eqc"]` with ids `robinson`, `mollweide` and `plate-carree`, each with a placeholder ceiling:
  - `test_transform_mesh(benchmark, grid_mesh, projection)`: `transform_mesh(grid_mesh, projection)`, asserting at least 64,800 cells.
  - `test_transform_points(benchmark, cloud, projection)`: `transform_points(WGS84, projection, *cloud)`, asserting shape `(100_000, 3)` and every value finite.
- [ ] **Step 2: Run** `pixi run --frozen -e test benchmarks`, then measure and set the ceilings as in Task 2. Expected: 14 passed under each task.
- [ ] **Step 3: Commit** as `tests: benchmark the transforms (bench spec row 2)`, with the peaks and ceilings.

### Task 4: Landing

- [ ] **Step 1: Push**, confirm with `git ls-remote`, and read the `codspeed benchmarks` job: its duration, and each benchmark in CodSpeed's comment. Past 10 minutes, apply call 3 and push again.
- [ ] **Step 2: Mark §8 item 1** `🏁 Resolved (2026-11-10, {pull}`2927` · 🔎 2026-11-10, {pull}`2925` · 🎫 {issue}`2926`)`, saying what settled each gap, and row 2 `✅ landed`, dated the day it merges.
- [ ] **Step 3: Write the fragment**, then run `pixi run -e test check-spec-status 2927`, the strict incremental docs build, and the full suite after it, `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e test tests-unit`. Expected: PASS.
- [ ] **Step 4: Commit** as `docs: land row 2 of bench spec §9`, push, and ask {user}`bjlittle` to mark the pull request ready.

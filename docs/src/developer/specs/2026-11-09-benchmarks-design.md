# Benchmarks Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how `geovista` measures its own speed and memory, where the
> measurements run, and what a contributor sees when a change makes either worse. Read it
> as current; the roadmap states what has actually landed.

- **Date:** 2026-11-09 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `bench spec §…`
- **Scope:** benchmarks of the computation in `geovista`'s public API, the CI workflow that
  runs them on every pull request and on `main`, the memory ceilings each one carries, and
  the developer guide's account of them. Rendering is out of scope (§4.6)
- **Lineage:** **bench spec**
- **Children:** none
- **Published:** in the specifications index

(bench-spec-1)=
## 1. Purpose

`geovista` has no benchmarks, so nothing in CI measures how fast it runs or how much memory
it takes. {issue}`2913` shows what that costs. {pull}`2912` made `geodesic.npoints_by_idx`
read each end of a segment through a NumPy masked array, and `geodesic.line`, which calls
it once a pair of vertices, went from 0.16 s to 0.36 s for 2,000 vertices. A final review
caught it by timing it by hand. A slowdown that nobody happens to time lands unnoticed.

A slowdown can also arrive without any change to `geovista`'s code. Its dependencies are
locked in `pixi.lock`, and that file changed in 30 commits over the three months to
2026-11-09: the weekly pull request of `ci-locks.yml`, dependabot raising a ceiling, and
pull requests of our own that add or change a dependency. A release of pyproj, VTK or NumPy
that is slower on the paths `geovista` takes into it is as real a regression as one in our
own code.

This specification gives `geovista` benchmarks of speed and memory that run on every pull
request, report a regression on the pull request that causes it, and follow the set-up
`pyvista` already runs, as workflow rule 1.5 asks.

(bench-spec-2)=
## 2. Decisions

1. **🤝 Agreed** (2026-11-09, {user}`bjlittle`, {pull}`2923`) — **Speed is measured by
   CodSpeed, in simulation mode.** Simulation counts the CPU instructions a benchmark runs
   under Valgrind, so its result does not move with the load on a shared runner, and can be
   compared with a stored result for the base commit. `pyvista` has run it this way since
   pyvista/pyvista#9111 (§3.2). The free plan is unlimited for open-source projects, and
   simulation runs on our own GitHub runner. Chosen by {user}`bjlittle` on 2026-11-09, over
   pytest-benchmark comparing the base and the head in one job, which needs no external
   service but gives noisy timings and no history, and over asv, whose environments know
   nothing of pixi (§5).
2. **🤝 Agreed** (2026-11-09, {user}`bjlittle`, {pull}`2923`) — **The benchmarks run on
   every pull request, on every push to `main`, and by hand.** That is when `pyvista` runs
   them. Each push to `main` stores the result that a pull request based on it is compared
   with. Every pull request is measured, so the weekly lock pull request and every
   dependabot one are too, with no path filter and no label to remember. Chosen by
   {user}`bjlittle` on 2026-11-09, over running on pushes to `main`, on pull requests that
   change `pixi.lock` and on a `benchmark` label.
3. **🤝 Agreed** (2026-11-09, {user}`bjlittle`, {pull}`2923`) — **The benchmarks run in the
   unsuffixed `test` environment.** `pytest-codspeed` and `pytest-memray` join the `test`
   feature, as `pyvista` keeps `pytest-codspeed` in its `test` group. The unsuffixed
   environments follow the newest Python, so the benchmarks move with it and
   `tests/test_python_support.py` has nothing new to track. `pytest-codspeed` acts only
   under `--codspeed`, and `pytest-memray` under `--memray` or on a test carrying one of its
   markers, so the CodSpeed run passes `-p no:memray`. Chosen by {user}`bjlittle` on
   2026-11-09, over a `bench` environment of its own.
4. **🤝 Agreed** (2026-11-09, {user}`bjlittle`, {pull}`2923`) — **A regression is reported,
   never required to pass.** CodSpeed's gate, the "CodSpeed Performance Analysis" check,
   and its comment on the pull request show a regression, and the memory job fails on a
   breached ceiling, but neither joins the required checks of `main`, which is how
   `pyvista` has it. The maintainer decides each case. {pull}`2912` is the case for it: it
   fixed how a missing position is read, knowingly made `geodesic.line` slower, and was
   right to merge with {issue}`2913` raised. Chosen by {user}`bjlittle` on 2026-11-09, over
   making the gate a required check.
5. **🤝 Agreed** (2026-11-09, {user}`bjlittle`, {pull}`2923`) — **Each benchmark carries a
   memory ceiling: its measured peak plus 20%, rounded up to a whole MiB.**
   `pytest-memray`'s `limit_memory` marker fails a test whose peak memory passes its limit.
   It hooks `malloc`, so it sees what VTK allocates in C++, which `tracemalloc` cannot. For
   one lock, a benchmark's peak barely moves from run to run, so 20% is room enough to
   catch a real regression without false alarms. A change that rightly raises a peak raises
   its ceiling in the same pull request, where the review sees it. CodSpeed's free plan has
   no memory instrument, so this is the one part not taken from `pyvista`. Chosen by
   {user}`bjlittle` on 2026-11-09, over limits of about twice the peak, which catch only a
   gross blow-up, and over no ceilings until a comparison with the base is built
   (row 4 of §9).
6. **🤝 Agreed** (2026-11-09, {user}`bjlittle`, {pull}`2923`) — **The benchmarks live in
   `benchmarks/`, written with the `benchmark` fixture.** That is `pyvista`'s layout, and
   the fixture is one that `pytest-benchmark` provides too, so the same files run under
   either tool. The unit suite never collects them, since `testpaths` already names `tests`
   alone, as `pyvista`'s does.
7. **🤝 Agreed** (2026-11-09, {user}`bjlittle`, {pull}`2923`) — **A benchmark measures
   computation, on data it builds itself.** Its input is made outside the measured call,
   from a seeded generator, and nothing is downloaded, so the job needs neither the network
   nor the pooch cache. VTK runs on one thread, so an instruction count never depends on how
   work was split, as `pyvista`'s `benchmarks/conftest.py` does, and so does OpenMP, since
   pykdtree queries on OpenMP threads, whose synchronisation the simulation cannot measure
   consistently, as {pull}`2924` found. Nothing is rendered (§4.6).
8. **🤝 Agreed** (2026-11-09, {user}`bjlittle`, {pull}`2923`) — **A change of dependency is
   measured by the pull request that makes it.** Every job installs its environment with
   `--frozen`, from the `pixi.lock` of the commit it measures. A pull request that changes
   only `pixi.lock` has the same code on both sides of its comparison, so whatever it
   reports was caused by the dependencies alone.

(bench-spec-3)=
## 3. What Exists Today

(bench-spec-3-1)=
### 3.1 In `geovista`

There are no benchmarks, and none of `asv`, `pytest-benchmark`, `pytest-codspeed`, CodSpeed
or memray appears in `pyproject.toml`, `requirements/` or `.github/`. The unit suite is run
by `pytest` from the repository root, and `pyproject.toml` sets `testpaths = "tests"`, so a
module under a new `benchmarks/` directory is collected only when it is named.

`pytest`'s configuration turns every warning into an error (`filterwarnings = "error"`) and
refuses an unknown marker (`--strict-markers`). Both apply to the benchmarks, which share it.

(bench-spec-3-2)=
### 3.2 In `pyvista`

`pyvista` added CodSpeed in pyvista/pyvista#9111, merged on 2026-09-07. As read on
2026-11-09:

- `.github/workflows/benchmarks.yml` runs on each push to `main`, each pull request and by
  hand, with one job, "CodSpeed (simulation)". It installs `pyvista` with `uv`, pinning
  `numpy` and `vtk` exactly, because "an upstream release shifts every baseline at once",
  then runs `CodSpeedHQ/action` with `mode: simulation` and
  `python -m pytest benchmarks --codspeed`. Its only permission is `contents: read`.
- `benchmarks/` holds 13 modules, each calling the `benchmark` fixture, such as
  `benchmark(_touch_attributes, sphere)` in `test_vtk_interop.py`.
- `benchmarks/conftest.py` builds every input outside the measured region, from
  `np.random.default_rng(0)`, scopes a fixture to the function when a benchmark mutates its
  object, and calls `vtkSMPTools.Initialize(1)` so that "instruction counts do not depend
  on work splitting".
- `pyproject.toml` caps `pytest-codspeed` below 5.1 and sets `testpaths = 'tests'`.
- Each pull request shows two checks, the job and "CodSpeed Performance Analysis", whose
  gate reported "Performance Gate Passed" on seven of the eight most recently closed, the
  eighth's job having failed before the gate ran. No branch
  protection or ruleset of `main` that this account can read requires either.

`geovista`'s `pixi.lock` already pins every dependency exactly, which is what `pyvista`'s two
pins do for its two largest, so it needs no pins of its own (§2 decision 8).

(bench-spec-3-3)=
### 3.3 The CodSpeed Wizard's Pull Request

{user}`bjlittle` installed the CodSpeed GitHub App on 2026-11-09, and its set-up wizard
opened {pull}`2924`. It adds 21 benchmarks in `benchmarks/test_bench.py`, on a synthetic
2° global grid, and a `ci-benchmarks.yml` that installs `.[test]` and `pytest-codspeed` with
`pip` on Python 3.14 and runs `pytest benchmarks --codspeed` in simulation mode. Its first
run passed, gate and all, so simulation runs on our own runner, authenticated by OIDC.

Four of its choices are taken into this design: `OMP_NUM_THREADS=1` (§2 decision 7), the
`id-token: write` permission CodSpeed's OIDC needs, pruning `benchmarks` from the sdist so
`check-manifest` passes, and the README's CodSpeed badge (§4.4). So are its benchmarks of
`from_cartesian`, `slice_cells`, `combine`, `npoints` and the gridlines, and its three
projections (§4.3).

Three are not. `pip` resolves the newest release of every dependency on each run, so an
upstream release would shift the result of whichever pull request ran next, and be blamed
on it (§2 decision 8). It has no memory ceilings (§2 decision 5). Its `geodesic.line`
benchmark runs through five vertices, too few to show the cost {issue}`2913` found in each
pair.

(bench-spec-4)=
## 4. Design

(bench-spec-4-1)=
### 4.1 The Dependencies

`pytest-codspeed` and `pytest-memray` join `[tool.pixi.feature.test.dependencies]`, and
`requirements/pypi-optional-test.txt` with the same ceilings, which
`tests/test_dependency_ceilings.py` holds in step. Both are on conda-forge, at 5.0.4 and
1.9.0 when this was written. `pytest-benchmark` is not added: it and `pytest-codspeed` both
provide the `benchmark` fixture.

(bench-spec-4-2)=
### 4.2 The Benchmarks

The benchmarks are modules named `test_<module>.py` under `benchmarks/`, one for each
`geovista` module they measure, with a `conftest.py` that builds the inputs and pins VTK to
one thread (§2 decision 7). It also makes the process's first matrix product, so that the
buffers OpenBLAS sets up on it, 128 MiB under every kernel older than `SkylakeX`, are
charged to no benchmark ({issue}`2933`). Each benchmark is a test that hands the call it measures to the
fixture, as `benchmark(geodesic.line, *line)`, and carries its ceiling:

```python
@pytest.mark.limit_memory("22 MB")
def test_line(benchmark, line):
    """Build a geodesic line through 2,000 vertices (bench spec §2 decision 7)."""
    benchmark(geodesic.line, *line)
```

The conftest refuses, under `--memray`, a
benchmark that carries no `limit_memory` mark, naming it, so a benchmark cannot be added
without its ceiling.

The inputs are made by the conftest, never downloaded:

| Input | Shape | Used By |
|---|---|---|
| a global grid | 1° cell bounds, 360 by 180 cells, as 1-D and as 2-D curvilinear coordinates, and as a mesh | the bridge, `transform_mesh`, `from_cartesian`, `slice_mesh`, `slice_cells`, `resize`, `find_nearest_cell`, `BBox.enclosed` |
| four copies of the grid's mesh | made for each benchmark | `combine` |
| a mesh of quads | the global grid's cells given by their corners, as `from_unstructured` takes them | the bridge |
| a point cloud | 100,000 seeded positions on the sphere, as positions and as a mesh of points | `from_points`, `transform_points`, `KDTree` |
| a kd-tree | over the cloud's mesh | `KDTree.query` |
| a geodesic box | 30° west to 30° east, 20° south to 40° north | `BBox.enclosed` |
| a line | 2,000 vertices, as in {issue}`2913` | `geodesic.line` |

A fixture whose object a benchmark changes is scoped to the function. The rest are built
once a session.

(bench-spec-4-3)=
### 4.3 What Is Measured

| Module | Benchmarks |
|---|---|
| `geodesic` | `line` through the line's 2,000 vertices; `npoints` for 10,000 points; `BBox.enclosed` on the global grid; `wedge` from 0° to 90° of longitude |
| `bridge` | `Transform.from_1d`, `from_2d` and `from_unstructured` on the global grid; `from_points` on the point cloud |
| `transform` | `transform_mesh` from the global grid, and `transform_points` on the point cloud, each to Robinson, Mollweide and Plate Carrée |
| `common` | `from_cartesian` of the global grid's mesh |
| `core` | `slice_mesh` of the global grid at the antimeridian; `slice_cells` at 45.5° east; `combine` of four copies of the global grid's mesh; `resize` of the global grid |
| `search` | building a `KDTree` from the point cloud; querying it with 10,000 of its points; `find_nearest_cell` |
| `gridlines` | `create_meridians` and `create_parallels` with their defaults |

Each name is the benchmark's test, as `test_from_1d`, so CodSpeed's report reads as the API
it measures. These paths take `geovista` into pyproj's `Transformer`, VTK's filters, NumPy
and pykdtree, which is where a dependency's regression would show (§2 decision 8).

(bench-spec-4-4)=
### 4.4 The Workflow

`.github/workflows/ci-benchmarks.yml` runs on `push` to `main`, on `pull_request` and on
`workflow_dispatch`. A run of a pull request is cancelled by a newer one, and a run of `main`
never is, so every commit of `main` stores the result that later pull requests are compared
with, as `pyvista`'s workflow does. Each action is pinned to a commit, as `zizmor` requires,
and `OMP_NUM_THREADS` is `1` throughout (§2 decision 7). It has two jobs, each installing
the `test` environment with `prefix-dev/setup-pixi` and `--frozen`:

- **`codspeed`** runs `CodSpeedHQ/action` with `mode: simulation`, and the command
  `pixi run --frozen -e test benchmarks`. It has `contents: read` and `id-token: write`,
  which CodSpeed's OIDC authentication needs, and no other permission.
- **`memory`** runs `pixi run --frozen -e test benchmarks-memory`, outside Valgrind, since
  memray and Valgrind both intercept `malloc`. Its only permission is `contents: read`.

Neither job's check joins the required checks of `main` (§2 decision 4). `MANIFEST.in`
prunes `benchmarks`, so `check-manifest` passes, and the README's Health row gains
CodSpeed's badge, beside Codecov's.

(bench-spec-4-5)=
### 4.5 The Tasks and the Guide

Two tasks join the `test` feature:

| Task | Runs |
|---|---|
| `benchmarks` | `pytest benchmarks --codspeed -p no:memray` |
| `benchmarks-memory` | `pytest benchmarks --memray --trace-python-allocators --most-allocations=0` |

Run locally, without Valgrind, `--codspeed` measures wall time, which is enough to compare
two branches on one machine. Both run OpenMP on one thread. Neither forces OpenBLAS's
kernel, which could crash an older CPU ({issue}`2935`): with the conftest's warm-up, a
benchmark's peak is the same under every kernel. Each task gets its row on the `packaging` and `testing` pages,
as `tests/test_pixi_tasks.py` requires. A "Benchmarks" section of the developer guide's
testing page says how to run them, how to add a benchmark, how to read CodSpeed's comment,
and how to set a ceiling: run `benchmarks-memory`, read the benchmark's peak from memray's
report, add 20%, and round up to a whole MiB.

(bench-spec-4-6)=
### 4.6 What This Design Leaves Alone

- **Rendering.** A scene under llvmpipe takes time that depends on the rasterizer, and
  constructing a plotter under Valgrind measures VTK's start-up more than `geovista`. The
  image tests already check what is drawn.
- **Wall time on a shared runner.** Simulation never sees it, so a slowdown that lives only
  in I/O, threads or cache misses is not caught. `geovista`'s computation is mostly
  CPU-bound NumPy and VTK, where an instruction count follows the time well.
- **Comparing memory with the base.** A ceiling sees a breach and nothing under it. A
  comparison of each benchmark's peak with the base commit's is row 4 of §9.

(bench-spec-5)=
## 5. Alternatives Considered

- **pytest-benchmark, comparing the base and the head in one job.** Both commits are
  checked out and installed, the benchmarks run on each, and
  `--benchmark-compare-fail=mean:25%` fails a regression. It needs no external service, but
  a shared runner's timings vary from run to run, which forces a coarse threshold, and it
  keeps no history. The benchmark files would be the same as these.
- **asv.** It keeps a history with graphs, and `asv find` bisects a regression. `iris` runs
  it each night and on a `benchmark_this` label, and on a change to its lock files. But asv
  builds its own environments, which know nothing of pixi, and `iris` needed a delegated
  environment layer (`asv_delegated.py`, `bm_runner.py`) to use its own. `geovista` would
  need the same.
- **Running on a label, or only on a change to `pixi.lock`.** Fewer runs, but every other
  pull request would need someone to remember the label, and it departs from `pyvista` with
  no saving: simulation is free (§2 decision 2).
- **Memory by `tracemalloc`.** It needs no plugin, but it sees only allocations made through
  Python's allocator, which leaves out what VTK allocates in C++.
- **CodSpeed's memory instrument.** It would put memory in the same report as speed, but it
  is not on the free plan.

(bench-spec-6)=
## 6. Testing

- The workflow is its own test: row 1 of §9 lands only once a run of it on its pull request
  has reported a result for every benchmark, and the memory job has passed.
- A test reads `pyproject.toml` and holds `testpaths` to `tests`, so the unit suite cannot
  start collecting `benchmarks/`.
- The conftest's refusal of a benchmark without a ceiling is tested with `pytester`: a
  benchmark without `limit_memory` fails under `--memray` and names itself, and one with it
  passes.
- `tests/test_pixi_tasks.py` holds each new task to its rows, and
  `tests/test_dependency_ceilings.py` holds the two plugins' ceilings in step.

(bench-spec-7)=
## 7. Scope

In scope are the two plugins, `benchmarks/` and its conftest, the benchmarks of §4.3 with
their ceilings, the two tasks, `ci-benchmarks.yml`, the `MANIFEST.in` entry, the README's
badge, the developer guide's section, and their tests. Out of scope are rendering, wall time on a shared runner, and making either
check required (§4.6, §2 decision 4). So is fixing a regression the benchmarks find, as
{pull}`2922` fixed {issue}`2913`, landing row 7 of positions spec §9.

(bench-spec-8)=
## 8. Open Items

Each carries the grammar of items spec §3.2.

1. **🏁 Resolved** (2026-11-10, {pull}`2927` · 🔎 2026-11-10, {pull}`2925` ·
   🎫 {issue}`2926`) — **The conftest and its tests have small gaps.** The final
   review of row 1 found five, and row 2 settled them. The refusal of §4.2 names a
   benchmark by its node id and keeps to `benchmarks/`. It reads memray's switch as
   pytest-memray does, which never reads its own `memray` ini key, as `--memray`
   defaults to false, so the ini setting needed nothing more. The test of
   §2 decision 6 reads methods and coroutines, the test of §2 decision 2 refuses a
   `types:` filter, VTK's single thread is tested under the threaded backend, as
   conda-forge's VTK defaults to its sequential one, and the example of §4.2 is
   current.

2. **🏁 Resolved** (2026-11-10, {pull}`2936` · 🔎 2026-11-10, {pull}`2927` ·
   🎫 {issue}`2928`) — **The tests and fixtures have small gaps.** The final review
   of row 2 found three, and row 3 settled them. VTK's threaded backend caps its
   thread count at the CPU's, so on a single core no run can show the pin; a test
   reads the conftest for `vtkSMPTools.Initialize(1)` at import instead. The reader
   of the fixture test reads every module at any depth and keyword-only
   parameters, and names a method by its class. The benchmarks read their sizes
   from the fixtures, each projection named with `pytest.param`.

(bench-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The plugins (§4.1), `benchmarks/` and its conftest with the `geodesic` benchmarks (§4.2, §4.3), the workflow (§4.4), and the tasks and the guide (§4.5) | ✅ landed (2026-11-10, {pull}`2925`) |
| 2 | The `bridge` and `transform` benchmarks (§4.3) | ✅ landed (2026-11-10, {pull}`2927`) |
| 3 | The `common`, `core`, `search` and `gridlines` benchmarks (§4.3) | ✅ landed (2026-11-10, {pull}`2936`) |
| 4 | Each benchmark's peak memory compared with the base commit's (§4.6) | 💡 candidate |

Statuses follow docs spec §3.6. Each row lands in a pull request of its own. Rows 2 and 3
need row 1, and not each other. Row 1 starts with `geodesic`, whose `line` benchmark covers
the path {issue}`2913` slowed and {pull}`2922` restored, so a return of that cost is caught.

Row 4 is wanted when a regression in memory is found that stayed under its ceiling. That
cannot be observed mechanically, so the row is **revisited by hand**, when such a
regression is found. It would record each benchmark's peak on both sides of a pull request
and compare them, which `pytest-memray` does not do itself.

(bench-spec-10)=
## 10. References

- {issue}`2913`, the slowdown that prompted this specification, and {issue}`2920`, which
  tracks it.
- {pull}`2924`, opened by CodSpeed's set-up wizard (§3.3).
- workflow rule 1.5, which points benchmarking at `pyvista`'s set-up.
- pyvista/pyvista#9111, which added CodSpeed to `pyvista`:
  <https://github.com/pyvista/pyvista/pull/9111>
- CodSpeed's pricing, which lists the free plan's limits: <https://codspeed.io/pricing>
- `pytest-memray`'s `limit_memory` and `limit_leaks` markers:
  <https://pytest-memray.readthedocs.io/en/latest/usage.html>
- `iris`'s asv workflow, `benchmarks_run.yml`:
  <https://github.com/SciTools/iris/blob/main/.github/workflows/benchmarks_run.yml>

(bench-spec-11)=
## 11. Verification

Each row follows ledger spec §3.4.

| Decision | Status | Evidence |
|---|---|---|
| §2 decision 1 | ✅ verified (2026-11-10, {pull}`2925`) | `tests/test_benchmarks.py` |
| §2 decision 2 | ✅ verified (2026-11-10, {pull}`2925`) | `tests/test_benchmarks.py` |
| §2 decision 3 | ✅ verified (2026-11-10, {pull}`2925`) | `tests/test_benchmarks.py` |
| §2 decision 4 | ✍️ signed off (2026-11-10, {user}`bjlittle`, {pull}`2925`) | Checked in review that neither `codspeed benchmarks` nor `memory ceilings`, nor CodSpeed's `CodSpeed Performance Analysis`, is among the required checks of `main`. |
| §2 decision 5 | ✍️ signed off (2026-11-10, {user}`bjlittle`, {pull}`2936`) | Each benchmark's measured peak, with Python's allocators traced, and its ceiling are tabled in {pull}`2925`, {pull}`2927` and {pull}`2936`. `tests/test_benchmarks.py` refuses a benchmark that carries no ceiling, but no test can show that a ceiling is its peak plus 20%. |
| §2 decision 6 | ✅ verified (2026-11-10, {pull}`2925`) | `tests/test_benchmarks.py` |
| §2 decision 7 | ✅ verified (2026-11-10, {pull}`2936`) | `tests/test_benchmarks.py` |
| §2 decision 8 | ✅ verified (2026-11-10, {pull}`2925`) | `tests/test_benchmarks.py` |

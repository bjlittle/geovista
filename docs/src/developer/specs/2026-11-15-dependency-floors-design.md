# Dependency Floors Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how `geovista` holds the minimum version of each dependency to what
> it declares: where the floors are written, the environments that resolve them, and the
> jobs that exercise them on a pull request, each week and at a release. Read it as
> current; the roadmap states what has actually landed.

- **Date:** 2026-11-15 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `floors spec §…`
- **Scope:** the floor each dependency declares, for `pixi` and for `pip`; the environments
  that resolve the `pixi` floors; the jobs that exercise both on every pull request, each
  week and before a release reaches PyPI; the check that holds the two sides' floors equal;
  and the developer guide's account of them. Ceilings are out of scope (§4.6)
- **Lineage:** **floors spec**
- **Children:** none
- **Prior art:** the dependency floors design of `bjlittle/tephpy` (§3.4); `pixi`'s
  `solve-strategy`; `uv`'s `--resolution lowest-direct`
- **Published:** in the specifications index

(floors-spec-1)=
## 1. Purpose

`geovista` declares a minimum version for its dependencies in two places, and nothing it
runs resolves either. Every `pixi` job installs with `--frozen` from `pixi.lock`, which
`ci-locks.yml` moves to the newest releases each week, and `ci-tests-pypi.yml` resolves the
newest releases from PyPI. A floor set too low therefore fails for one user, whose solve
happens to land on it, in an environment this repository never sees.

The `pixi` side declares a floor in 75 of its 77 versioned declarations, the other two
being the `python` pin of each version feature. The `pip` side, whose requirements are
what `pip install geovista` publishes, declares one on 13 of its 71 lines. Most were
dropped by {pull}`2226`, five days after dependabot's grouped bump in {pull}`2219` had
raised several to the newest release while widening their ceilings: `numpy >=1.25.0`
became `>=2.4.4`, and `pyproj >=3.3.0` became `>=3.7.2`. A line without a floor admits
every release on PyPI, and a user whose environment already holds an old one keeps it.
Resolved at its lowest by `uv`, `requirements/pypi-core.txt` picks netCDF4 0.6.1, whose
`setup.py` fails with a Python 2 syntax error before anything builds (measured
2026-11-15).

A throwaway run at the `pixi` floors on 2026-11-15 resolved the core, `test` and `docs`
floors as declared, on Python 3.13.0, and passed 5,140 tests at the core and `test` floors
(§3.3). It found the `devs` floors unsolvable, and two defects that no locked environment
reaches: {issue}`2967` and {issue}`2968`.

`bjlittle/tephpy` runs a weekly job for the same gap. It writes an exact pin for each
floor into a copy of its manifest, attributes a failure to one package by relaxing each
pin in turn, scans upward for the lowest version that passes, and files an issue (§3.4).
`pixi` has offered since 0.59 (2025-10-29) a solve strategy that resolves each direct
dependency to the lowest release it admits, which makes the pins unnecessary. This
specification holds `geovista`'s floors to what it declares with that strategy, on both
sides and at a release.

(floors-spec-2)=
## 2. Decisions

1. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **`pixi` resolves the
   floors itself, with `solve-strategy = "lowest-direct"`.** An environment so marked
   resolves each direct dependency to the lowest release its specifier admits, among the
   builds for its platform and Python, and each transitive one to the highest. That is the
   corner a floor claims, with no pin written and no manifest rewritten. Where the release
   a floor names cannot be used, it takes the lowest that can, as `>=1.7.2` resolved
   netcdf4 1.7.4 (§3.3), an answer tephpy's generator gets by querying the channel. Chosen
   by {user}`bjlittle` on 2026-11-15, over porting tephpy's pin generator, attribution,
   upward scan and issue filing (§5).
2. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **The `floors` environment
   is locked, and runs on every pull request.** It joins `pixi.lock` like any other, and a
   job of `ci-tests.yml` runs it with `--frozen`. Its result changes only when a commit
   changes something: code calling an API newer than a floor, a floor moved, or the weekly
   pull request of `ci-locks.yml` moving a transitive dependency. Each reaches the pull
   request that made it, so nothing needs attributing. Chosen by {user}`bjlittle` on
   2026-11-15, over a fresh solve each week, which needs no lock entry but goes red for
   reasons no pull request caused, and over both.
3. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **`floors` carries `devs`
   and `test`, as the test environments do.** The suite runs as it does there, with no
   test learning to skip, and every `devs` floor is installed, rasterio, pandas, pyarrow
   and h3 among them. The
   linters are installed and never run: at its floor, `ruff` reports its own rule set
   rather than anything about `geovista`'s floors. Chosen by {user}`bjlittle` on
   2026-11-15, over `test` alone, which would double as an environment without extras but
   cost six tests their coverage ({issue}`2967` covers that case), and over splitting an
   `exam` feature out of `devs` to mirror the `pip` extra.
4. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **The documentation is
   built at its floors each week, from a locked `floors-docs` environment.** `floors-docs`
   carries `devs` and `docs`, and builds `html-noplot` from `main` with the documentation
   build's own strictness. A failure opens an issue. Being locked, it goes red only after
   a merge, never on a hiccup of the channel. Chosen by {user}`bjlittle` on 2026-11-15,
   over a build on every pull request, a second Sphinx build each time whose cost is
   unmeasured, and over leaving the `docs` floors unexercised.
5. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **Every `pip` requirement
   carries a floor, equal to its `pixi` floor.** A check holds the two equal (§4.4), so a
   dependabot pull request that raises a `pip` floor, as {pull}`2219` did, fails on that
   pull request, as one whose `pip` ceiling outruns the `pixi` one fails the Dependency
   Ceilings check. Chosen by {user}`bjlittle` on 2026-11-15, over floors on
   `requirements/pypi-core.txt` alone, and over keeping the `pip` side without floors, as
   {pull}`2226` left it.
6. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **A person reads a
   failure.** Nothing attributes it to a package, scans for a version that passes, or
   opens a pull request to raise a floor. The author of a pull request reads its red check,
   and the maintainer reads a weekly or release failure from its run. Attribution would be
   added only if failures prove hard to read. Chosen by {user}`bjlittle` on 2026-11-15,
   with §2 decision 1.
7. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **A release reaches PyPI
   only once its wheel installs and passes at its floors.** On a tag, a job of
   `ci-wheels.yml` installs the built wheel with its `test` and `exam` extras under
   `--resolution lowest-direct` and runs the suite, and `publish-artifacts-pypi` needs it.
   The floors a user is promised are the wheel's `Requires-Dist` lines, and nothing
   resolves them before a release today (§3.2). Chosen by {user}`bjlittle` on 2026-11-15,
   over a step of a release checklist, and over no gate.
8. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **The `pip` floors are
   exercised each week too.** A job installs `.[test,exam]` under `uv`'s
   `--resolution lowest-direct` on Python 3.13 and runs the suite, beside the build of
   §2 decision 4. The `pip` side cannot be locked as the `pixi` side is, so the schedule
   gives the early warning and §2 decision 7 the guarantee.
9. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **A floors environment
   carries the oldest supported Python, and solves alone.** Floors resolved against the
   newest Python would not be the corner of what `geovista` supports. Each carries the
   oldest version feature and no solve-group, since a group shared with environments
   resolved at their highest would solve them together. Its name carries no version, as
   `floors` and `floors-docs`, so a SPEC 0 bump changes the feature it carries and not the
   jobs that name it.
10. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **The image tests are
    left out at the floors.** Their baselines are rendered under the `pyvista` and VTK
    that the lock pins, so a difference at a floor `pyvista` would measure the lock's
    distance from the floor rather than a defect in it. Each job at the floors runs what
    the `tests not image` legs of `ci-tests.yml` run.
11. **🤝 Agreed** (2026-11-15, {user}`bjlittle`, {pull}`2969`) — **The `tests floors`
    check is required on `main`.** A red floor cannot merge, so the pull request that
    breaks a floor is the one that raises it, which §2 decision 2 relies on. On a
    dependabot pull request the floor is raised on its own branch, as a ceiling already is.
    On the weekly lock pull request, whose branch `ci-locks.yml` rewrites each week, it is
    raised in a pull request merged ahead of it. The maintainer adds the check to the
    branch protection of `main` once row 1 of §9 lands. Chosen by {user}`bjlittle` on
    2026-11-15, over reporting it only, as bench spec §2 decision 4 does for the
    benchmarks, which would let a red floor merge and every later pull request inherit it.

(floors-spec-3)=
## 3. What Exists Today

(floors-spec-3-1)=
### 3.1 The Two Declaration Sites

Each dependency is declared twice, once for `pixi` and once for `pip`, and a floor can be
written on either side:

| Tier | `pixi` | `pip` |
|---|---|---|
| core | `[tool.pixi.dependencies]` | `requirements/pypi-core.txt` |
| `test` | `[tool.pixi.feature.test.dependencies]` and `.pypi-dependencies` | `requirements/pypi-optional-test.txt` |
| `docs` | `[tool.pixi.feature.docs.dependencies]` and `.pypi-dependencies` | `requirements/pypi-optional-docs.txt` |
| `devs` | `[tool.pixi.feature.devs.dependencies]` and `.pypi-dependencies` | `requirements/pypi-optional-devs.txt` and `requirements/pypi-optional-exam.txt` |

The two sides are not a mirror of each other. The `pip` extra `exam` (h3, pandas, pyarrow
and rasterio) has no `pixi` feature, its packages being declared under `devs`. One package
goes by two names: `h3` is `h3-py` on conda-forge, which `tests/test_dependency_ceilings.py`
maps in `RENAMED`. Other names differ only in case or separator, which canonical names
equate, as `netCDF4` and `netcdf4`. Some `pixi` declarations have no `pip` counterpart:
`python` and `pip` in each version feature, `setuptools` and `setuptools-scm` in the core
(for `pip`, the `[build-system]` table names them), and `make` in `docs`. The `devs`
feature's `geovista`, an editable path, is a source rather than a floor.

On the `pip` side, 13 of 71 lines carry a floor, six of them in `pypi-core.txt`
(measured 2026-11-15).

(floors-spec-3-2)=
### 3.2 What Runs Today

- Every `pixi` job installs with `--frozen` from `pixi.lock`. Each week `ci-locks.yml` runs
  `pixi update` and opens a pull request that moves every environment to the newest
  releases its specifiers admit, which tests the ceiling end of each declaration.
- `ci-tests.yml` runs on pull requests, on pushes to `main` and on `v*` tags, with legs
  `tests image` and `tests not image` for Python 3.13 and 3.14.
- `ci-tests-pypi.yml` runs on pull requests and each night, installing `.[test,exam]` with
  `pip` at the newest releases on Python 3.13 and 3.14. A failing scheduled run opens an
  issue.
- `ci-wheels.yml` builds the sdist and the wheel. Its `test-artifacts` job installs the
  wheel with `--no-deps` into a locked environment and imports it, and
  `publish-artifacts-pypi` needs only that job, on a `v*` tag. Nothing resolves the
  wheel's requirements before it is published, and a red `ci-tests.yml` on the same tag
  does not stop it.
- dependabot raises the `pip` ceilings daily, with the versioning strategy
  `increase-if-necessary`. Its grouped bump in {pull}`2219` raised floors as well (§1).
- `tests/test_dependency_ceilings.py` holds each `pixi` ceiling at or above its `pip`
  ceiling, documented as the Dependency Ceilings check.
- `tests/test_python_support.py` holds each environment named for a version in the
  solve-group of that version, every version to the same environments, and every
  environment not named for a version in the primary solve-group. A floors environment
  breaks all three as they are written (§4.1).

(floors-spec-3-3)=
### 3.3 What a Run at the Floors Found

On 2026-11-15, the core floors were solved with each of the `test`, `docs` and `devs`
features on Python 3.13, with `solve-strategy = "lowest-direct"`, from `main` at 8103fed4.
A scratch copy of `main` was then given an environment of the core and `test` features,
and the suite was run in it without the image, browser and example tests:

- The core, `test` and `docs` floors resolved, each direct dependency at its declared
  floor or the nearest release above it that the solve could use: lazy-loader 0.4,
  netcdf4 1.7.4, make 4.4.1. Python resolved to 3.13.0.
- The `devs` floors did not resolve. `pyarrow >=13.0.0`, a `pypi-dependencies` entry, has
  no wheel for Python 3.13, whose first is pyarrow 18.0.0, and its sdist fails to build.
- 5,140 tests passed and 14 failed. Three were {issue}`2967`, five were {issue}`2968`, and
  six came from the shape of the environment: five tests needed packages of `devs` or
  `exam`, and one holds every environment to a solve-group. None was a broken floor.
- From PyPI, `uv pip compile --resolution lowest-direct` over `requirements/pypi-core.txt`
  chose netCDF4 0.6.1 for the line `netCDF4 <1.8`, and failed to build it.

(floors-spec-3-4)=
### 3.4 tephpy's Floors Job

`bjlittle/tephpy` runs `ci-floors.yml` each week, specified by its
[dependency floors design](https://github.com/bjlittle/tephpy/blob/main/docs/src/developer/specs/2026-08-13-dependency-floors-design.md).
For each tier it rewrites every floor in a copy of the manifest to `==` the lowest release
that the channel carries for its Python and platform, then solves fresh. A failure is
attributed by relaxing each pin in turn, the package found is scanned upward for the
lowest release that passes, and an issue is filed for each tier and package. A second
half installs from PyPI with `uv pip install --resolution lowest-direct`. With its tests,
the job is about 4,900 lines.

The broken floors it was built for were found by hand while it was being designed, in
tephpy's issues 109 and 135 to 138 (read on 2026-11-15). Of the eight
issues the job has filed, two reported floors already filed by hand (145 and 146), three
came from tests reading the manifest its generator had rewritten (155, 158 and 163), and
one, 347, is open with nothing attributed. Its specification does not consider `pixi`'s
`solve-strategy`.

This design takes from it the corner of the oldest Python, a half for each declaration
site, the linters installed but not run, and the image tests left out. It leaves the
pins, the rewritten manifest, attribution, the upward scan, the filing of issues per
package, and the schedule as the only trigger (§5).

(floors-spec-4)=
## 4. Design

(floors-spec-4-1)=
### 4.1 The Floors Environments

Two environments join `[tool.pixi.environments]`, each carrying the oldest version
feature, which is `py313` when this was written:

```toml
floors = { features = ["devs", "py313", "test"], solve-strategy = "lowest-direct" }
floors-docs = { features = ["devs", "docs", "py313"], solve-strategy = "lowest-direct" }
```

Both are locked in `pixi.lock`. A floor raised above the version locked invalidates the
lock, so `pixi lock` re-solves it. A floor lowered does not, since the version locked still
satisfies it, so lowering one is followed by `pixi update --environment floors <package>`,
as {pull}`2974` found. The weekly `pixi update` of `ci-locks.yml` moves their transitive
dependencies while the direct ones stay at their floors.

When two floors cannot be resolved together, `lowest-direct` lifts one above its floor
rather than failing, as `uv` does. A pair broken that way still passes, and the lock shows
the lifted version (§4.6).

`tests/test_python_support.py` learns a third kind of environment. A floors environment is
named `floors` or `floors-<tier>`, carries the oldest version feature, declares
`solve-strategy = "lowest-direct"` and declares no solve-group. The three rules of §3.2
pass it over by that name, and new tests hold each of its properties, so a SPEC 0 bump
that leaves a floors environment on the old version fails there.

(floors-spec-4-2)=
### 4.2 Raising a Floor That Fails

Each row of §9 that adds a job raises the floors its job disproves, in its own pull
request, so a row is done when its job passes. Each floor goes to the lowest release under
which the job passes, found by hand, and the pull request names each one it raised.
Row 1 raises the `pixi` floors before its job runs on pull requests: `pyarrow` to the
lowest release with a wheel for the oldest Python, and any other the suite shows broken.
{issue}`2968` is fixed first, since a flaky test in a job that runs on every pull request
would read as a broken floor. Rows 3 and 4 are the first to install the `pip` floors, and
row 5 the first to build the documentation at the `docs` floors, so each may raise more.

From row 2 of §9 on, a floor is raised on both sides in one commit, which the check of
§4.4 enforces, followed by `pixi lock`. A row that lands before row 2 raises the `pixi`
floor alone, and row 2 copies it.

(floors-spec-4-3)=
### 4.3 The Jobs

- **`ci-tests.yml`** gains a `floors` job on each of its triggers. It runs what the
  `tests not image` legs run, in the `floors` environment, with `--frozen`. It is a job of
  its own rather than a leg of the `tests` matrix, which the coverage upload `needs`, so a
  red floor never stops the coverage report. Its check is named `tests floors`, with no
  version, so a SPEC 0 bump leaves the branch protection that requires it unchanged
  (§2 decision 11).
- **`ci-floors.yml`** is new, run each week and by hand, with `permissions: {}` and each
  job granted what it needs. Its `docs` job installs `floors-docs` with `--frozen` and
  runs `pixi run --frozen -e floors-docs make`, which builds `html-noplot` with
  `--fail-on-warning`. Its `pypi` job runs the composite action below against the
  checkout. A failing scheduled job opens an issue titled for that job, or comments on the
  open one carrying its title, so a floor that stays broken is one issue rather than one a
  week.
- **A composite action**, `.github/workflows/composite/floors-pypi/action.yml`, takes what
  to install: the checkout, or a wheel. It creates a Python 3.13 environment with `uv`,
  installs the target with its `test` and `exam` extras under
  `--resolution lowest-direct`, retrying the install once, and writes `uv pip freeze` to
  the step summary. `uv` takes a wheel's own requirements as transitive and would resolve
  them at their highest, so for a wheel the action reads its `Requires-Dist` lines, those
  of its core and of the two extras, and passes them to `uv` as direct requirements beside
  it. It restores the data through the `cartopy-cache` and `geovista-cache` composite
  actions, which run their commands from its `uv` environment rather than through `pixi`,
  then runs the suite without the image tests under `xvfb-run`, setting
  `PYVISTA_OFF_SCREEN` and `GEOVISTA_POOCH_MUTE` itself so that a caller need set neither.
  Its two callers share one copy of these steps.
- **`ci-wheels.yml`** gains a `test-floors` job, needing `build-artifacts`, which runs the
  composite action against the built wheel. It runs on `v*` tags, and on
  `workflow_dispatch`, a trigger the workflow gains so that the gate can be run before a
  release. `publish-artifacts-pypi` needs both `test-artifacts` and `test-floors`.

The install's single retry is for a fault of the index. A failing test is never retried.

(floors-spec-4-4)=
### 4.4 The `pip` Floors and the Dependency Floors Check

Each `pip` requirement becomes `>=F,<C`, where `F` is the floor of its `pixi` declaration.
`tests/test_dependency_floors.py` holds four things, reading both sides as
`tests/test_dependency_ceilings.py` does:

- every `pip` requirement declares a floor;
- every package declared on both sides has the same floor in each `pip` file and each
  `pixi` table that declares it, compared as versions, so that `0.4` and `0.4.0` agree;
- a specifier whose floor cannot be read, such as `>`, `==`, `~=` or a wildcard, is
  reported rather than skipped;
- a `pixi` declaration with no `pip` counterpart (§3.1) needs no `pip` floor.

The check gets a section of the Repository Checks page, "Dependency Floors", beside
"Dependency Ceilings". Its remedy is to put a floor back where a dependabot pull request
moved it, or to raise a floor on both sides together and run `pixi lock`.

(floors-spec-4-5)=
### 4.5 The Developer Guide

Each row updates the pages that describe what it changes, in the same pull request:

| Page | Section | Change | Row of §9 |
|---|---|---|---|
| `packaging.rst` | Pixi Solve-Groups | the floors environments: solved alone, at their lowest, on the oldest Python, and how `pixi lock` and `pixi update` treat them | 1, 5 |
| `testing.rst` | Continuous Integration | the `tests floors` check of `ci-tests.yml`, how to run the suite at the floors locally, and where to raise a floor when the check goes red on a bot's pull request | 1 |
| `packaging.rst` | Python Package Index | a floor on every `pip` requirement, equal to its `pixi` floor, and how to raise one | 2 |
| `checks.rst` | Dependency Floors | the new check, its rule, why it exists and its remedy, with its row in the table of checks | 2 |
| `codecraft.rst` | Dependabot | a dependabot pull request that moves a `pip` floor fails the Dependency Floors check, and how to restore it | 2 |
| `testing.rst` | Continuous Integration | a row for `ci-floors.yml`, and what its issue means | 3 |
| `packaging.rst` | Continuous Integration | the `ci-wheels.yml` row: no release reaches PyPI until its wheel passes at its floors | 4 |
| `documentation.rst` | Continuous Integration | the weekly build at the `docs` floors | 5 |

Row 2 also adds to the root `AGENTS.md`, under Build and Test, that a floor moves on both
sides in one commit and is followed by `pixi lock`.

(floors-spec-4-6)=
### 4.6 What This Design Leaves Alone

- **Ceilings.** `ci-locks.yml` moves the resolved point upward, and the Dependency
  Ceilings check holds the two sides' ceilings in step.
- **Other Pythons and platforms.** A floor claims one corner of what `geovista` supports:
  the oldest Python, on `linux-64`, the only platform it locks.
- **Raising a floor automatically** (§2 decision 6).
- **A floor higher than it needs to be.** It costs a user nothing they can observe, and
  finding one means scanning downward through releases `geovista` does not claim.
- **An environment without extras.** {issue}`2967` is the case for one, and its fix
  covers it.
- **A floor lifted by the solve** (§4.1). A report of each floor beside the version its
  environment locks would show one. Row 6 of §9 is that report.
- **The browser tests at the `docs` floors.** They check the chrome of
  `pydata-sphinx-theme` and `sphinx-book-theme`, which a floor of either could render
  differently, but they need a browser and a full build. Row 7 of §9 is that run.
- **The conda-forge feedstock.** Its `run:` requirements are a third declaration of the
  floors, still at the 0.5.3 release's (`numpy >=1.24`, `pyvista >=0.43.1,<0.45`). They
  are edited at a release, in `conda-forge/geovista-feedstock`, outside this repository's
  CI.

(floors-spec-5)=
## 5. Alternatives Considered

- **Porting tephpy's job.** Its generator, attribution, upward scan and issue filing
  answer a fresh weekly solve that writes exact pins. With `lowest-direct` there are no
  pins to write, and with a locked environment the pull request that breaks a floor is
  the one that reports it (§3.4).
- **A fresh solve each week, or a fresh solve as well as the locked one.** Either needs no
  lock entry and would catch a transitive dependency that drifts between pull requests.
  The weekly pull request of `ci-locks.yml` already re-solves the floors environments, and
  the `tests floors` check runs on it.
- **`floors` with `test` alone, or with an `exam` feature split out of `devs`.** The first
  would double as an environment without extras, at the cost of six tests' coverage. The
  second would pair the `pixi` features with the `pip` extras, a change to the manifest
  this design does not otherwise need.
- **The `docs` floors on every pull request, or not at all.** The first costs a second
  Sphinx build per pull request, and the second leaves a published extra's floors
  unexercised.
- **Floors on `requirements/pypi-core.txt` alone, or none.** The extras would make
  promises nothing could test, since `uv`'s lowest resolution of a line without a floor
  picks its oldest release.
- **Parking dependabot's `pip` updates**, as tephpy did. That would stop the ceiling bumps
  the Dependency Ceilings check relies on, and §2 decision 5 catches a raised floor
  without it.
- **A release checklist, or no gate.** A checklist is a step that is easy to skip, and
  reads the requirements as committed rather than the wheel.

(floors-spec-6)=
## 6. Testing

- Each job is its own test. Row 1 of §9 lands once the `tests floors` check has passed on
  its pull request, and rows 3, 4 and 5 once their job has passed on theirs.
  `workflow_dispatch` starts only a workflow whose copy on `main` has that trigger, so a
  throwaway commit runs the job on its pull request, and is reverted before the row lands.
  For rows 3 and 5 it adds a `pull_request` trigger to `ci-floors.yml`, and for row 4 it
  lets `test-floors` run on the `pull_request` trigger that `ci-wheels.yml` already has.
  Once the pull request merges, the workflow is run by hand, and for row 4 that run passes
  `test-floors` and publishes nothing.
- Each job is also seen to fail once, as workflow rule 2.6 asks. On its pull request, a
  throwaway commit breaks one floor, and the job is watched going red before the commit is
  reverted.
- `tests/test_python_support.py` holds each property of a floors environment (§4.1), and
  each is broken in turn to watch its test fail.
- `tests/test_dependency_floors.py` is shown failing on a demonstration of each clause of
  §4.4: a `pip` requirement without a floor, two floors that differ, two `pip` files that
  disagree, and a specifier it cannot read.
- No test reads a rewritten manifest, since nothing rewrites one.

(floors-spec-7)=
## 7. Scope

In scope are the two floors environments and the Python support test's account of them,
the floors that each job disproves on its first run (§4.2), a floor on every `pip`
requirement, the Dependency Floors check, the `floors` job of `ci-tests.yml`,
`ci-floors.yml`, the composite action, the `test-floors` job of `ci-wheels.yml`, and the
pages of §4.5. Out of scope are
ceilings, other Pythons and platforms, raising floors automatically, an environment
without extras, and the feedstock (§4.6).

(floors-spec-8)=
## 8. Open Items

Each carries the grammar of items spec §3.2.

1. **❓ Open** (🔎 2026-11-16, {pull}`2974` · 🎯 row 6 of §9 · 🎫 {issue}`2975`) —
   **A lowered floor is not re-solved by `pixi lock`.** The version locked still
   satisfies a lowered floor, so the `floors` environment stays where it was until
   `pixi update --environment floors <package>` runs, and `tests floors` stays green
   above the new floor meanwhile. §4.1 documents the step, but nothing checks that it
   was taken. The report of row 6 would show it, as a direct dependency locked above
   its floor that the solve did not lift.
2. **🏁 Resolved** (2026-11-22, {pull}`3007` · 🔎 2026-11-19, {pull}`2996` · 🎫 {issue}`3000`) —
   **The composite action relies on its caller's `env`.** `ci-floors.yml` sets
   `PYVISTA_OFF_SCREEN` and `GEOVISTA_POOCH_MUTE` for the whole workflow, and the
   `floors-pypi` action sets neither, so the suite has them only because its caller does.
   `ci-wheels.yml` has no workflow `env`, so the `test-floors` job of row 4 would run the
   suite without them, unless the job sets them or the action takes them over. The action
   now sets both on the step that runs the suite.

(floors-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The `floors` environment and the Python support test's account of it (§4.1), its job in `ci-tests.yml` (§4.3), each floor it disproves raised (§4.2), and its pages (§4.5) | ✅ landed (2026-11-16, {pull}`2974`) |
| 2 | A floor on every `pip` requirement and the Dependency Floors check (§4.4), and their pages (§4.5) · 🔗 after row 1 | ✅ landed (2026-11-17, {pull}`2985`) |
| 3 | The composite action and the `pypi` job of `ci-floors.yml` (§4.3), each floor it disproves raised (§4.2), and its page (§4.5) · 🔗 after row 2 | ✅ landed (2026-11-22, {pull}`2996`) |
| 4 | The `test-floors` job of `ci-wheels.yml` (§4.3), each floor it disproves raised (§4.2), and its page (§4.5) · 🔗 after row 3 | ✅ landed (2026-11-23, {pull}`3007`) |
| 5 | The `floors-docs` environment (§4.1) and the `docs` job of `ci-floors.yml` (§4.3), each floor it disproves raised (§4.2), and their pages (§4.5) · 🔗 after row 1 | 📋 not started |
| 6 | A report of each floor beside the version its environment locks (§4.6) | 💡 candidate |
| 7 | The browser tests at the `docs` floors (§4.6) | 💡 candidate |

Statuses follow docs spec §3.6. Each row lands in a pull request of its own. Row 1 waits on
{issue}`2968`. The floors row 2 copies to `pip` are those row 1 has shown to hold. `uv`'s
lowest resolution, which row 3 runs, means nothing until every line has a floor, and row 4
calls the composite action of row 3. Whichever of rows 3 and 5 lands first creates
`ci-floors.yml`.

Row 6 is wanted once a floor is found to have been lifted by the solve, and row 7 once a
floor of the theme or of an extension is found to break the chrome. Neither can be
observed mechanically, so both are **revisited by hand**, when such a case is found.

(floors-spec-10)=
## 10. References

- {pull}`2219`, dependabot's grouped bump that raised `pip` floors, and {pull}`2226`, which
  dropped them.
- {issue}`2967` and {issue}`2968`, found by the run of §3.3.
- tephpy's dependency floors design (§3.4):
  <https://github.com/bjlittle/tephpy/blob/main/docs/src/developer/specs/2026-08-13-dependency-floors-design.md>
- `pixi`'s `solve-strategy`, added in prefix-dev/pixi#4789 and released in 0.59.0:
  <https://pixi.sh/latest/reference/pixi_manifest/#solve-strategy-optional>
- `uv`'s resolution strategies:
  <https://docs.astral.sh/uv/concepts/resolution/#resolution-strategy>
- SPEC 0, which sets the oldest supported Python: <https://scientific-python.org/specs/spec-0000/>

(floors-spec-11)=
## 11. Verification

Each row follows ledger spec §3.4.

| Decision | Row | Status | Evidence |
|---|---|---|---|
| §2 decision 1 | row 1 of §9 | ✅ verified (2026-11-16, {pull}`2974`) | `tests/test_python_support.py` |
| §2 decision 2 | row 1 of §9 | ✅ verified (2026-11-16, {pull}`2974`) | `tests/test_floors.py` |
| §2 decision 3 | row 1 of §9 | ✅ verified (2026-11-16, {pull}`2974`) | `tests/test_python_support.py` |
| §2 decision 4 | row 5 of §9 | ⏳ pending | |
| §2 decision 5 | row 2 of §9 | ✅ verified (2026-11-17, {pull}`2985`) | `tests/test_dependency_floors.py` |
| §2 decision 6 | row 5 of §9 | ⏳ pending | |
| §2 decision 7 | row 4 of §9 | ✅ verified (2026-11-23, {pull}`3007`) | `tests/test_ci_floors.py` |
| §2 decision 8 | row 3 of §9 | ✅ verified (2026-11-22, {pull}`2996`) | `tests/test_ci_floors.py` |
| §2 decision 9 | row 1 of §9 | ✅ verified (2026-11-16, {pull}`2974`) | `tests/test_python_support.py` |
| §2 decision 10 | row 4 of §9 | ✅ verified (2026-11-23, {pull}`3007`) | `tests/test_ci_floors.py`, `tests/test_floors.py` |
| §2 decision 11 | row 2 of §9 | ✍️ signed off (2026-11-17, {user}`bjlittle`, {pull}`2985`) | Checked in review that `tests floors` is a required status check of the branch protection of `main`, added once row 1 landed. |

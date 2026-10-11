---
orphan: true
---

# type coverage change 6a — the untyped imports

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** clear the library's untyped imports with typeshed stubs where conda-forge carries
them and targeted overrides where nothing does, and take the five modules that leaves
clean, or nearly so, out of the typing ratchet: `geovista.cache`, `geovista.config`,
`geovista.qt`, `geovista.geometry` and `geovista.cli`.

**Architecture:** row 6 of the roadmap is split into three pull requests
({user}`bjlittle`, 2026-10-11): this one, the untyped imports; 6b, the mesh modules
`core`, `search`, `filters`, `gridlines` and `crs`; and 6c, the rest, which lands row 6.
Three distributions have conda-forge stubs, `types-shapely`, `pandas-stubs` and
`types-click-default-group`, which join `types-rasterio` in the `devs` feature. Three ship
no annotations at all, `pooch`, `geopy` and `fastparquet`, and get one override tracked by
{issue}`2629`. The optional site configuration is meant to be absent, and `pyvistaqt`,
though typed, is in no locked environment ({issue}`2630`); those three names get a second.

**Tech Stack:** `mypy` 2.x in strict mode, `pixi` (conda-forge) and its lock exports,
`pytest` with `pytest-mock` and `click.testing`.

**Spec:** `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, cited throughout
as `typing spec §…`. This plan implements the first part of change 6 of typing spec §4,
and the untyped imports §7 assigns to it.

**Branch:** `debt/typing-imports`. The plan is committed first and the pull request held in
draft until the implementation lands on it. `{PR}` below is that pull request's number.

## Global Constraints

- **Copyright header** and `from __future__ import annotations` on every Python file
  (root `AGENTS.md`, ruff-enforced). **Line length 88.**
- **The strictness settings stay as they are** (typing spec §7). An override names its
  modules exactly, never a pattern wider than the distribution (`geopy.*` covers
  `geopy.point`), and its comment cites the spec and the issue that retires it.
- **A dependency is declared everywhere `pixi` cannot see** (root `AGENTS.md`): the
  `devs` feature in `pyproject.toml`, `requirements/pypi-optional-devs.txt`, and the
  exports `ci-locks.yml` produces (`requirements/geovista.yml`,
  `requirements/locks/*_conda_spec.txt` and, through `lock2yaml.py`, `*_conda_spec.yml`).
  Run `pixi lock` after editing the feature, and check the lock adds only the stubs.
- **No `type: ignore`, and no new `noqa`.** An upstream defect is met with a typed local,
  plus a typing spec §8 item.
- **The ratchet only shrinks, in step:** `pyproject.toml` and `RATCHET_BASELINE` in the
  same commit as the fixes that make the module pass. Every commit passes the `mypy` hook.
- **Run the full non-image suite before each commit**, not only the tests of the task:
  `tests/test_spec_conventions.py` counts citations outside the specifications across the
  repository (37 of a ceiling of 70 on `main`; this change adds three).
- **A probe of a scratch tree never runs `python -I`**, which ignores `PYTHONPATH`.
- **Changelog.** One fragment, `{PR}.dependency.rst`, signed ``:user:`claude` ``; the
  `agentic` label on the pull request.
- **Every deferred item gets an `agentic` issue**, linked from the Follow-ups below and
  from the pull request's description.
- **Prose for other readers is humanized:** the spec's new text, the `pyproject.toml`
  comments, commit messages, the fragment and the pull request body. This plan is not.

## Five corrections this plan makes to the spec

Measured on 2026-10-11 against `main` at `248cf8bf`, and replayed in task order on a fresh
tree with its own environment.

1. **Row 6's count does not reproduce.** With every library entry lifted at `8b2f0ab3`,
   where the census was taken, these seventeen modules report 71 lines: 46 of code and 25
   imports, 14 of them `lazy_loader`. No division of those gives the roadmap's 51. On
   `main` they report 53. Ten of the modules load `numpy` or `pyvista` lazily without
   importing it under `TYPE_CHECKING` (typing spec §3.3), and with those imports added the
   count is 69: `core.py` goes from 16 lines to 23, `gridlines.py` from 0 to 5, `crs.py`
   from 0 to 1, and `pantry/data.py` and `report.py` gain one each. Row 6 is that 69,
   split three ways.
2. **Three of §7's untyped imports have stubs, and they reveal two errors.** With
   `types-shapely`, `pandas-stubs` and `types-click-default-group` installed, the imports
   of `shapely`, `pandas` and `click_default_group` clear. `shapely`'s stubs then show that
   `geometry.py`'s `unpack` was annotated for a `list[GeometrySequence]` it never receives;
   it is given `cartopy`'s geometries and a list of `LineString`s. The lock adds the three
   and `types-pytz`, which `pandas-stubs` requires, and nothing else.
3. **Three have neither stubs nor annotations.** The latest wheels of `pooch` (1.9.0),
   `geopy` (2.5.0) and `fastparquet` (2026.9.0) carry no `py.typed` and no `.pyi`, and none
   of the 27 functions in the `geopy` modules `geovista` imports has a return annotation.
   One override covers the three, and a new §8 item 9 waits on {issue}`2629`, which records
   `pooch`'s open upstream issue, fatiando/pooch#330.
4. **`pyvistaqt` is typed, and simply not installed.** 0.13.1 ships `py.typed` and is on
   conda-forge, but no locked environment carries it, so `mypy` cannot find it. It shares
   an override with `geovistaconfig` and `geovista.siteconfig`, which are meant to be
   absent. Adding it to the environment would let `mypy` check `geovista.qt` for real, and
   likely report {issue}`2622`, at the cost of a Qt binding; {issue}`2630` holds that
   decision.
5. **`cli.py` meets item 2's defect.** `p.add_axes()` is a `_Wrapped` call, the
   `call-arg` error typing spec §3.4 counts in the library. It goes through a typed local,
   like the two of change 5, and §8 item 8 grows to three.

## Review Focus

1. **The lock moves only the stubs.** `pixi.lock`'s diff adds `pandas-stubs`,
   `types-click-default-group`, `types-pytz` and `types-shapely` and changes no other
   package. → task 1 step 3.
2. **The overrides name exactly what they cover.** `geopy.*` is the narrowest form for a
   package imported as `geopy.point`; nothing of `geovista` sits under either block. →
   task 2 step 2's `mypy` run, which would show a hidden `geovista` error as a missing one.
3. **`geovista plot --axes` still adds the axes, and only then.** The typed local replaces
   a method call. → task 4, `test_axes`.
4. **The coastlines are unchanged.** `unpack`'s annotation changes; the existing
   `tests/geometry` cover `geometry.py` in full (measured) and pin its output.
5. **The documentation still builds with `-W`.** `unpack` is nested and unpublished, but
   the build is the check. → task 5 step 4.

---

### Task 1: add the three stub packages to the `devs` feature

**Files:**
- Modify: `pyproject.toml` (`[tool.pixi.feature.devs.dependencies]`), `pixi.lock`
- Modify: `requirements/pypi-optional-devs.txt`, `requirements/geovista.yml`,
  `requirements/locks/geovista_linux-64_conda_spec.txt`,
  `requirements/locks/geovista_linux-64_conda_spec.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: `shapely`, `pandas` and `click_default_group` typed for `mypy`.

- [ ] **Step 1: Declare them**

In `[tool.pixi.feature.devs.dependencies]`, keeping the list alphabetical, add
`pandas-stubs = ">=3.0.5,<4"` after `pandas`, and `types-click-default-group = ">=1.2.0,<2"`
and `types-shapely = ">=2.1.0,<3"` either side of `types-rasterio`. In
`requirements/pypi-optional-devs.txt`, keeping it sorted, add `pandas-stubs <3.1`,
`types-click-default-group <1.3` and `types-shapely <2.2`, the style of
`types-rasterio <1.6`.

- [ ] **Step 2: Lock**

Run: `pixi lock`

Expected: `pandas-stubs` 3.0.5.260914, `types-click-default-group` 1.2.0.20260518,
`types-pytz` 2026.5.0.20261006 and `types-shapely` 2.1.0.20260402 added.

- [ ] **Step 3: Check the lock moved nothing else**

Run: `git diff pixi.lock | grep -E "^[-+].*(conda|pypi): " | sed -E 's#.*/##' | sort -u`

Expected: the four `.conda` files above on `+` lines, and no `-` line.

- [ ] **Step 4: Regenerate the exports, as `ci-locks.yml` does**

```bash
pixi workspace export conda-explicit-spec --environment geovista --frozen --ignore-pypi-errors requirements/locks
pixi workspace export conda-environment --environment geovista requirements/geovista.yml
(cd requirements/locks && pixi run --frozen -e geovista python lock2yaml.py)
git diff --stat -- requirements
```

Expected: `geovista.yml` gains 3 lines, each `*_conda_spec.*` 4, and
`pypi-optional-devs.txt` 3.

- [ ] **Step 5: Verify, and commit**

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`; the stubs reveal nothing outside
the ratchet.

Run: `pixi run --frozen -e geovista pytest -m "not image" --numprocesses auto --dist worksteal`

Expected: exit 0, `main`'s count (2845 on 2026-10-11 with a docs build).

Message, humanized: `deps: add typeshed's stubs for shapely, pandas and
click-default-group to the devs environment`.

---

### Task 2: override what has no annotations, and retire three modules

**Files:**
- Modify: `pyproject.toml` (`[[tool.mypy.overrides]]`, the ratchet),
  `tests/test_typing_ratchet.py`

**Interfaces:**
- Consumes: task 1's stubs.
- Produces: two overrides; `geovista.cache`, `geovista.config` and `geovista.qt` out of
  the ratchet.

- [ ] **Step 1: Watch the three modules fail**

Delete `  "geovista.cache",`, `  "geovista.config",` and `  "geovista.qt",` from the
ratchet's `module` list in `pyproject.toml`, and the same three names from
`RATCHET_BASELINE`.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 4 errors in 3 files`: `pooch` in `cache/__init__.py`, the two
site configurations in `config.py`, `pyvistaqt` in `qt.py`, all `import-untyped` or
`import-not-found`.

- [ ] **Step 2: Add the two overrides**

After the `lazy_loader` override, add, humanized:

```text
[[tool.mypy.overrides]]
# typing spec §8 item 9 -- three distributions ship no annotations and have
# no stubs (#2629). Withdraw each name when its distribution, typeshed or
# conda-forge provides them.
ignore_missing_imports = true
module = ["fastparquet", "geopy.*", "pooch"]


[[tool.mypy.overrides]]
# typing spec §7 -- meant to be absent: the optional site configuration, and
# "pyvistaqt", which ships "py.typed" but is in no locked environment (#2630).
ignore_missing_imports = true
module = ["geovista.siteconfig", "geovistaconfig", "pyvistaqt"]
```

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

- [ ] **Step 3: Verify, and commit**

Run: `pixi run --frozen -e geovista pytest -m "not image" --numprocesses auto --dist worksteal`

Expected: exit 0, three fewer than task 1: `test_ratchet_entry_resolves` loses one case
per entry.

Run: `pixi run --frozen -e geovista pre-commit run --files pyproject.toml tests/test_typing_ratchet.py`

Expected: every hook passes.

Message, humanized: `fix: take cache, config and qt out of the typing ratchet`.

---

### Task 3: retire `geovista.geometry`

**Files:**
- Modify: `pyproject.toml`, `tests/test_typing_ratchet.py`, `src/geovista/geometry.py`

- [ ] **Step 1: Watch it fail**

Delete `geovista.geometry` from the ratchet and `RATCHET_BASELINE`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 2 errors in 1 file`: `type-arg` on `GeometrySequence` and `union-attr`
on `.coords`, both in `unpack`.

- [ ] **Step 2: Annotate `unpack` with what it receives**

In the `TYPE_CHECKING` block, replace `    from collections.abc import Generator` with
`    from collections.abc import Iterable`, and delete
`    from shapely.geometry.base import GeometrySequence`. Replace the parameter:

```text
        geometries: Generator[LineString | MultiLineString] | list[GeometrySequence],
```

with:

```text
        geometries: Iterable[LineString | MultiLineString],
```

and its docstring line `geometries : Generator of LineString or MultiLineString` with
`geometries : iterable of LineString or MultiLineString`. `unpack` is given `cartopy`'s
`reader.geometries()` and the `LineString`s of `multi_lines`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

- [ ] **Step 3: Verify, and commit**

Run: `pixi run --frozen -e geovista pytest tests/geometry`, then the full non-image suite.

Expected: PASS; the full suite one fewer than task 2.

Message, humanized: `fix: take geometry.py out of the typing ratchet`.

---

### Task 4: retire `geovista.cli`

**Files:**
- Modify: `pyproject.toml`, `tests/test_typing_ratchet.py`, `src/geovista/cli.py`
- Create: `tests/cli/test_plot.py`

- [ ] **Step 1: Pin `geovista plot`'s axes**

Create `tests/cli/test_plot.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the ``geovista plot`` command."""

from __future__ import annotations

from click.testing import CliRunner
import pytest
import pyvista as pv

from geovista.cli import main
from geovista.crs import WGS84, to_wkt
from geovista.geoplotter import GeoPlotter


@pytest.mark.parametrize("axes", [False, True])
def test_axes(mocker, tmp_path, axes):
    """The axes are added only when asked for, through pyvista's add_axes."""
    fname = tmp_path / "sphere.vtk"
    sphere = pv.Sphere()
    to_wkt(sphere, WGS84)
    sphere.save(fname)
    _ = mocker.patch.object(GeoPlotter, "show")
    spy = mocker.spy(GeoPlotter, "add_axes")
    args = ["plot", str(fname), *(["--axes"] if axes else [])]

    result = CliRunner().invoke(main, args)

    assert result.exit_code == 0, result.output
    assert spy.call_count == int(axes)
```

`show` is patched, so nothing renders; the mesh carries a CRS, or `add_mesh`'s warning
fails the test under `filterwarnings = error`.

Run: `pixi run --frozen -e geovista pytest tests/cli/test_plot.py -v`

Expected: PASS, 2 tests. They pin what step 4 must not change.

- [ ] **Step 2: Watch it fail**

Delete `geovista.cli` from the ratchet and `RATCHET_BASELINE`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 1 error in 1 file`: `call-arg`, `_Wrapped`, on `p.add_axes()`.

- [ ] **Step 3: Import `pyvista` for `mypy`**

`cli.py` loads `pyvista` lazily with no `TYPE_CHECKING` import. Replace:

```text
if TYPE_CHECKING:
    from collections.abc import Iterable
```

with:

```text
if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    import pyvista as pv
```

Run: `pixi run --frozen -e geovista mypy`

Expected: still `Found 1 error in 1 file`, the same.

- [ ] **Step 4: The typed local**

Replace:

```text
    if axes:
        p.add_axes()
```

with:

```text
    if axes:
        # typing spec §8 item 8 -- pyvista 0.49's _Wrapped drops the descriptor protocol
        add_axes: Callable[..., object] = p.add_axes
        add_axes()
```

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

Run: `pixi run --frozen -e geovista pytest tests/cli -v`

Expected: PASS.

- [ ] **Step 5: Verify, and commit**

Run: the full non-image suite.

Expected: exit 0, one more than task 3: two new tests, one ratchet case fewer.

Run: `pixi run --frozen -e geovista pre-commit run --files src/geovista/cli.py src/geovista/geometry.py tests/cli/test_plot.py pyproject.toml tests/test_typing_ratchet.py`

Expected: every hook passes.

Message, humanized: `fix: take cli.py out of the typing ratchet`.

---

### Task 5: the spec and the changelog

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §4, §7, §8
- Create: `changelog/{PR}.dependency.rst`

- [ ] **Step 1: §7, the untyped imports**

Replace the bullet's last sentence, "The rest is part of change 6.", with, humanized:

```text
Change 6 took the three stub packages into the `devs` feature, which revealed two errors
in `geometry.py`. `pooch`, `geopy` and `fastparquet` ship no annotations and have no
stubs, so one override covers them until they do ({ref}`§8 <typing-spec-8>` item 9).
The two site configurations share a second with `pyvistaqt`, which ships `py.typed` but
is in no locked environment ({issue}`2630`).
```

- [ ] **Step 2: §8, items 8 and 9**

In item 8, replace "Two typed locals in `geoplotter.py` wait" with "Three typed locals
wait", and after the sentence on `_warn_opacity` and `view_poi` add, humanized: "Change 6
added the third, for `p.add_axes()` in `cli.py`'s `plot`." Append item 9, humanized:

```text
9. **Open** ({issue}`2629`) — **Three dependencies ship no annotations.** `pooch` 1.9.0,
   `geopy` 2.5.0 and `fastparquet` 2026.9.0 carry no `py.typed` and no stubs, on
   conda-forge or typeshed, so one `ignore_missing_imports` override makes each import
   `Any`. Each name comes out when its distribution or a stub package types it; `pooch`
   has an open upstream issue asking for annotations.
```

- [ ] **Step 3: §4, row 6 in progress**

Change row 6's Status from `not started` to `` in progress ({pull}`PR`) ``. Rows 6b and
6c add their pull requests to it, and 6c lands it.

- [ ] **Step 4: The changelog, and verify**

Create `changelog/{PR}.dependency.rst`, humanized:

```rst
Added typeshed's ``types-shapely``, ``pandas-stubs`` and
``types-click-default-group`` stubs to the ``devs`` environment, so ``mypy`` checks
``shapely``, ``pandas`` and ``click-default-group`` code against their real
interfaces. ``geovista.cache``, ``geovista.cli``, ``geovista.config``,
``geovista.geometry`` and ``geovista.qt`` also leave the typing ratchet.
(:user:`claude`)
```

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py {PR} "changelog/{PR}.dependency.rst"`,
`pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/test_status_references.py`,
and `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status {PR}`. Then,
from `docs/`:

```bash
pixi run --frozen -e docs sphinx-build -b html -W --keep-going \
  -D plot_docstring=False -D plot_gallery=False \
  -D plot_inline=False -D plot_tutorial=False \
  -d _build/doctrees src _build/html
```

Expected: all pass, and `build succeeded` without warnings.

Message, humanized: `docs: correct the typing spec against change 6a's measurements`.

---

## Done when

- `pixi run --frozen -e geovista mypy` exits 0 with `geovista.cache`, `geovista.cli`,
  `geovista.config`, `geovista.geometry` and `geovista.qt` absent from both the ratchet and
  `RATCHET_BASELINE`.
- The lock adds the four stub packages and nothing else, and every export agrees.
- The suite passes, the documentation builds with `-W`, and CI is green, image tests
  included.
- Typing spec §4, §7 and §8 agree with the measurements, and row 6 reads in progress.
- Every deferred item has an `agentic` issue, linked below and from the pull request.

## Follow-ups

- {issue}`2629`: the override for `pooch`, `geopy` and `fastparquet`, until they ship
  annotations.
- {issue}`2630`: whether to add `pyvistaqt`, which is typed, to the environment so that
  `mypy` checks `geovista.qt` for real.
- {issue}`2622`: `GeoMultiPlotter`'s `pyvistaqt` base is not a plotter; `qt.py` leaves the
  ratchet here only because `pyvistaqt` is `Any`.

Changes 6b (`core`, `search`, `filters`, `gridlines`, `crs`) and 6c (`pantry`, `raster`,
`report`, `themes`, and row 6 landed) follow, each with its own plan.

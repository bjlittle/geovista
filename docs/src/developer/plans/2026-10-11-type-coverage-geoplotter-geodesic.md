---
orphan: true
---

# type coverage change 5 — `geoplotter.py` and `geodesic.py`

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** take `geovista.geodesic` and `geovista.geoplotter` out of the typing ratchet so
that `mypy` checks both in full, fix the four defects that checking them brings to light,
and retire the gallery's `attr-defined` suppression that change 5 owns.

**Architecture:** `geodesic.py` is typed already; its 15 lines are optional parameters
passed on unchecked, two of which are bugs, a list treated as an array, and `distance`'s
union return. `geoplotter.py` loads `numpy` and `pyproj` lazily without importing them
under `TYPE_CHECKING`, so it is 16 lines rather than 15, and `GeoPlotterBase` is a mixin
that declared the `pyvista` methods it borrows, every declaration clashing with
`pyvista`'s own. The mixin gets `pv.BasePlotter` as its base for `mypy` alone, which
removes the declarations and three `type: ignore` comments, and leaves `add_mesh` and
`add_points` as deliberate departures from `pyvista`'s signatures, marked with two
precise `type: ignore[override]` comments ({user}`bjlittle`, 2026-10-11).

**Tech Stack:** `mypy` 2.x in strict mode, `numpy` 2.5, `pyproj`, `pyvista` 0.49, `pytest`
with `pytest-xdist` and `pytest-mock`, `pixi` (conda-forge).

**Spec:** `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, cited throughout
as `typing spec §…`. This plan implements change 5 of typing spec §4, and the parts of
§3.4 and §8 item 3 that name change 5.

**Branch:** `debt/typing-geoplotter-geodesic`. The plan is committed first and the pull
request held in draft until the implementation lands on it. `{PR}` below is that pull
request's number.

## Global Constraints

- **Copyright header** and `from __future__ import annotations` on every Python file
  (root `AGENTS.md`, ruff-enforced). **Line length 88.**
- **Docstrings.** NumPy style, validated by `numpydoc-validation` on `src/`; an
  `@overload` stub carries `# numpydoc ignore=GL08` on its `def` line.
- **The strictness settings stay as they are** (typing spec §7).
- **A published `ArrayLike` parameter is converted at the boundary, never narrowed**
  (typing spec §3.3, §5). A private helper past a converting boundary is annotated with
  what it receives. Behaviour only widens, save the four defects fixed.
- **No `type: ignore`, and no new `noqa`, except the two `type: ignore[override]`
  comments of task 4 step 7**, which cite typing spec §3.5. An upstream defect is met
  with a typed local or a `typing.cast`, plus a typing spec §8 item.
- **The ratchet only shrinks, in step:** `pyproject.toml` and `RATCHET_BASELINE` in the
  same commit as the fixes that make the module pass. Every commit passes the `mypy` hook.
- **Tests:** one file per function under `tests/geodesic/` and `tests/geoplotter/`, as
  `tests/AGENTS.md` lays out; a citation in a docstring or comment carries its prefix
  (`typing spec §3.3`), or `tests/test_spec_conventions.py` fails, and a cited section
  must exist in the same commit. Run the full suite in `geovista`, and the new tests in
  `test-py314` too.
- **A probe of a scratch tree never runs `python -I`**: isolated mode ignores
  `PYTHONPATH`, so it imports the main checkout and compares `main` with itself.
- **Local suite runs** never pass `-p no:cacheprovider`; read results from failures and
  the exit code.
- **Changelog.** One fragment, `{PR}.bugfix.rst`, signed ``:user:`claude` ``; the
  `agentic` label on the pull request.
- **Every deferred item gets an `agentic` issue**, linked from the Follow-ups at the end
  of this plan and from the pull request's description (root `AGENTS.md`).
- **Prose for other readers is humanized:** the spec's new text, the `pyproject.toml`
  comment, commit messages, the fragment, the pull request body and any issue. This plan
  is not.
- **Names.** Repository text names the reviewer as {user}`bjlittle`.

## Six corrections this plan makes to the spec

Measured on 2026-10-11 against `main` at `997ee680`, and dry-run end to end in scratch
worktrees: every count below was replayed in task order on a fresh tree.

1. **Row 5's count reproduces, and moved for reasons outside both modules.** With both
   entries lifted at `8b2f0ab3`, where the census was taken, `mypy` reports 63 errors on
   38 lines (19 and 19), the roadmap's 38. On `main` it reports 43 on 30 (15 and 15),
   though neither file has changed since: change 2's `lazy_loader` override cleared one
   import in each, the annotations of `crs.py` and `common.py` cleared
   `geodesic.py` 269, 270 and 996 and `geoplotter.py` 755, 756, 763 and 1570, and
   added `geoplotter.py` 766.
2. **`geoplotter.py` hides its own count.** It loads `numpy` and `pyproj` with
   `lazy.load` and never imports them under `TYPE_CHECKING`, the case typing spec §3.3
   describes, so both are `Any` to `mypy`. Imported properly it is 16 lines, two cleared
   and three revealed.
3. **Four defects, all on `main`:** `BBox(..., crs=None)` raises `CRSError` though `crs`
   defaults to WGS84; `npoints` and `npoints_by_idx` raise `TypeError` for `npts=None`
   though it defaults to `GEODESIC_NPTS`; and `_add_graticule_labels` fails on a
   `GraticuleGrid` whose `lonlat` is a list (`TypeError`) or whose `mask` is a list, which
   `mask * REMESH_SEAM` repeats rather than scales (`ValueError` on the array length).
   `GraticuleGrid` is public and annotates both `ArrayLike`.
4. **`GeoPlotterBase` needs a base, and then two deliberate departures.** The mixin
   declared `theme`, `add_text`, `add_point_labels`, `reset_camera` and `camera` to borrow
   them from the plotter it is combined with; the first four clash with `pyvista`'s
   definitions (`geoplotter.py` 1596) and the last is not a type at all (typing spec §3.4,
   §8 item 3, {issue}`2569`). Under `TYPE_CHECKING` the mixin now extends `pv.BasePlotter`,
   which `pyvistaqt`'s plotters share; at runtime it extends `object`, as now. That removes
   all five declarations and three `type: ignore` comments (`attr-defined`, `arg-type`,
   `misc`). What remains is real: `add_mesh` and `add_points` take the mesh positionally
   and every other argument by keyword, and `add_mesh` returns `None` for an empty mesh.
   {user}`bjlittle` ruled on 2026-10-11 to keep the API, annotate the truth
   (`pv.Actor | None` on `add_mesh`, `add_points`, `add_base_layer` and `add_coastlines`,
   whose docstrings say so), and mark the two `def` lines `# type: ignore[override]`,
   recorded in a new typing spec §3.5. The library's `type: ignore` count goes from ten to
   nine.
5. **Two upstream defects reach library code.** `pyvista` 0.49 leaves `GPUInfo.__init__`
   unannotated (`no-untyped-call`), and its `_Wrapped` decorator, item 2's cause, breaks
   `self.reset_camera(render=False)` (`call-arg`) once the mixin knows its base. `pyvista`
   `main` fixes both. Each call goes through a local annotated `Callable`, the pattern root
   `AGENTS.md` gives for thin types, and a new §8 item 8 waits on {issue}`2568` for both.
6. **Change 5 moves change 7's count.** The gallery override swaps `attr-defined` for
   `no-untyped-call`, since correcting `camera` turns 45 `attr-defined` into 44
   `no-untyped-call` on `Camera.zoom`, unannotated in 0.49 (#2569's own measurement,
   reproduced). The honest `pv.Actor | None` adds seven `arg-type` errors in
   `examples/spatial_index/uber_h3.py`, whose `H3Asset` holds actors in fields typed
   `str | PolyData`. On `main` they never showed, because `Actor` derives from untyped VTK
   classes and so is compatible with anything; `None` is not. The gallery, measured with
   its ratchet entry lifted, goes from 28 errors to 35, all seven in that file. They stay
   under the ratchet until change 7.

Also deferred, by {user}`bjlittle`'s ruling: `add_mesh` documents an array `zlevel` but
raises on one when the mesh needs no transform, because `core.resize` takes only an `int`
({issue}`2618`). Task 4 keeps today's exceptions exactly, passing
`int(np.asarray(zlevel))`.

## Review Focus

1. **`BBox` builds the same mesh, no slower.** `npoints_by_idx` now converts its points,
   and `BBox` called it about 500 times with a list that grows to tens of thousands of
   points: converting there made `BBox` ten times slower in the dry run (0.058 s against
   0.579 s). `bbox_update` therefore calls `npoints` directly. → task 3 step 6.
2. **The mixin's `mypy`-only base never reaches runtime**, where `geovista.qt` combines it
   with `pyvistaqt`'s plotters. → task 4, `test_runtime_base_is_object` and
   `test_geoplotter_mro`.
3. **An empty mesh still returns `None` and adds nothing.** → task 4,
   `test_empty_mesh_returns_none`.
4. **The edited branches the non-image suite never reached still work:** re-centring a
   CRS with a central meridian (`assert centred is not None`), and `view_poi` on the
   sphere (`reset_camera` through its local). → task 4, `test_central_meridian_recentred`
   and `test_spherical_camera`; CI's image tests render both.
5. **An array `zlevel` without a transform raises exactly what it raised**, a
   `ValueError` for several values and a `TypeError` for one ({issue}`2618`). → the
   probe in task 4 step 9.

---

### Task 1: honour the documented `None` defaults in `geodesic.py`

**Files:**
- Modify: `src/geovista/geodesic.py`, `BBox.__init__` and `npoints`
- Modify: `tests/geodesic/test_BBox.py`
- Create: `tests/geodesic/test_npoints.py`, `tests/geodesic/test_npoints_by_idx.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `BBox(..., crs=None)` equal to `BBox(...)`; `npoints(..., npts=None)` and
  `npoints_by_idx(..., npts=None)` using `GEODESIC_NPTS`. Clears two of task 3's lines.

- [ ] **Step 1: Write the failing tests**

Append to `tests/geodesic/test_BBox.py`:

```python
def test_crs_none_is_wgs84():
    """A crs of None is the WGS84 default its docstring promises."""
    xs, ys = [-10, 10, 10, -10], [-10, -10, 10, 10]

    assert BBox(xs, ys, crs=None) == BBox(xs, ys)
```

Create `tests/geodesic/test_npoints.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.geodesic.npoints`."""

from __future__ import annotations

import numpy as np

from geovista.geodesic import npoints

#: The start and end points of a geodesic line.
START_LON, START_LAT, END_LON, END_LAT = -10.0, 20.0, 10.0, 30.0


def test_npts_none_is_the_default():
    """An npts of None is the GEODESIC_NPTS default its docstring promises."""
    expected = npoints(START_LON, START_LAT, END_LON, END_LAT)

    result = npoints(START_LON, START_LAT, END_LON, END_LAT, npts=None)

    np.testing.assert_array_equal(result, expected)


def test_radians_none_is_degrees():
    """A radians of None reads the points as degrees, as False does."""
    expected = npoints(START_LON, START_LAT, END_LON, END_LAT, npts=5)

    result = npoints(START_LON, START_LAT, END_LON, END_LAT, npts=5, radians=None)

    np.testing.assert_array_equal(result, expected)
```

Create `tests/geodesic/test_npoints_by_idx.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.geodesic.npoints_by_idx`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.geodesic import npoints_by_idx

#: Three points along a geodesic, as longitudes and latitudes.
LONS, LATS = [-10.0, 0.0, 10.0], [20.0, 25.0, 30.0]


def test_npts_none_is_the_default():
    """An npts of None is the GEODESIC_NPTS default its docstring promises."""
    expected = npoints_by_idx(LONS, LATS, start_idx=0, end_idx=1)

    result = npoints_by_idx(LONS, LATS, start_idx=0, end_idx=1, npts=None)

    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize("convert", [tuple, np.array], ids=["tuple", "array"])
def test_lists(convert):
    """Lists are the points given in any other array_like (typing spec §3.3)."""
    expected = npoints_by_idx(
        convert(LONS), convert(LATS), start_idx=0, end_idx=2, npts=5
    )

    result = npoints_by_idx(LONS, LATS, start_idx=0, end_idx=2, npts=5)

    np.testing.assert_array_equal(result, expected)
```

- [ ] **Step 2: Run them, and watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/geodesic/test_BBox.py tests/geodesic/test_npoints.py tests/geodesic/test_npoints_by_idx.py -k "crs_none or npts_none or radians_none or test_lists" -v`

Expected: 3 failed, 3 passed. `test_crs_none_is_wgs84` fails with `CRSError`, and both
`test_npts_none_is_the_default` with `TypeError: an integer is required`.
`test_radians_none_is_degrees` and the two `test_lists` cases pass already: they pin.

- [ ] **Step 3: Apply the defaults**

In `BBox.__init__`, replace `        self.crs = crs` with:

```text
        self.crs = WGS84 if crs is None else crs
```

In `npoints`, make the default the first statement after the docstring:

```text
    """
    if npts is None:
        npts = GEODESIC_NPTS

    if geod is None:
        geod = pyproj.Geod(ellps=ELLIPSE)
```

`npoints_by_idx` passes `npts` straight to `npoints`, so it needs nothing of its own.

- [ ] **Step 4: Run them again**

Run: the command of step 2.

Expected: PASS, 6 tests.

- [ ] **Step 5: Commit**

Message, humanized: `fix: honour the documented defaults of BBox's crs and npoints' npts`.

---

### Task 2: accept lists in `GraticuleGrid` labels

**Files:**
- Modify: `src/geovista/geoplotter.py`, `GeoPlotterBase._add_graticule_labels`
- Create: `tests/geoplotter/test__add_graticule_labels.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `lonlat` and `mask` converted where they are used. Clears three of task 4's
  lines.

- [ ] **Step 1: Write the failing tests**

Create `tests/geoplotter/test__add_graticule_labels.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.geoplotter.GeoPlotter._add_graticule_labels`."""

from __future__ import annotations

import numpy as np
import pyvista as pv

from geovista.geodesic import BBox
from geovista.geoplotter import GeoPlotter
from geovista.gridlines import GraticuleGrid

#: The longitude/latitude points of two labels.
LONLAT = [[0.0, 0.0], [90.0, 0.0]]

#: The two labels.
LABELS = ["0°", "90°E"]


def _labelled(
    mocker, lonlat, *, mask=None, manifold=None
) -> tuple[np.ndarray, list[str]]:
    """Return the points and labels passed on to add_point_labels."""
    p = GeoPlotter(manifold=manifold)
    spy = mocker.spy(p, "add_point_labels")
    graticule = GraticuleGrid(
        blocks=pv.MultiBlock(), lonlat=lonlat, labels=LABELS, mask=mask
    )

    p._add_graticule_labels(graticule)

    points, labels = spy.call_args.args
    return points, labels


def test_lonlat_list(mocker):
    """A list of points is the points given as an array (typing spec §3.3)."""
    expected, _ = _labelled(mocker, np.array(LONLAT))

    result, _ = _labelled(mocker, LONLAT)

    np.testing.assert_array_equal(result, expected)


def test_mask_list(mocker):
    """A list mask is the mask given as an array (typing spec §3.3)."""
    expected, _ = _labelled(mocker, np.array(LONLAT), mask=np.array([True, False]))

    result, _ = _labelled(mocker, np.array(LONLAT), mask=[True, False])

    np.testing.assert_array_equal(result, expected)


def test_manifold_keeps_the_labels_inside(mocker):
    """A manifold keeps only the labels whose points it encloses."""
    manifold = BBox([-10, 10, 10, -10], [-10, -10, 10, 10])

    _, labels = _labelled(mocker, np.array(LONLAT), manifold=manifold)

    assert list(labels) == ["0°"]
```

- [ ] **Step 2: Run them, and watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/geoplotter/test__add_graticule_labels.py -v`

Expected: 2 failed, 1 passed. `test_lonlat_list` fails with `TypeError: list indices
must be integers or slices, not tuple`, and `test_mask_list` with `ValueError: Invalid
array shape. Array 'gvRemeshPointIds' has length (0) but a length of (2) was expected.`
`test_manifold_keeps_the_labels_inside` pins the manifold branch, which no non-image test
reached.

- [ ] **Step 3: Convert where they are used**

In `_add_graticule_labels`, replace `        lonlat = graticule.lonlat` with
`        lonlat = np.asanyarray(graticule.lonlat)`, and
`            mask = graticule.mask * REMESH_SEAM` with
`            mask = np.asanyarray(graticule.mask) * REMESH_SEAM`.

- [ ] **Step 4: Run them again**

Run: the command of step 2.

Expected: PASS, 3 tests.

- [ ] **Step 5: Commit**

Message, humanized: `fix: accept lists for the points and mask of graticule labels`, naming
the list repetition.

---

### Task 3: retire `geovista.geodesic` from the ratchet

Counts below were measured on 2026-10-11 with tasks 1 and 2 applied.

**Files:**
- Modify: `pyproject.toml`, `tests/test_typing_ratchet.py`
- Modify: `src/geovista/geodesic.py`, `src/geovista/common.py`
- Modify: `tests/geodesic/test_line.py`

**Interfaces:**
- Consumes: task 1's defaults.
- Produces: `distance` overloads, which also clear one line of task 4; `npoints_by_idx`
  converting its points; `bbox_extend` taking `Sequence[float] | np.ndarray`.

- [ ] **Step 1: Pin `close=None`**

Append to `tests/geodesic/test_line.py`:

```python
def test_close_none_is_open():
    """A close of None leaves the line open, as False does."""
    expected = line([0, 10, 20], [0, 10, 0])

    result = line([0, 10, 20], [0, 10, 0], close=None)

    np.testing.assert_array_equal(result.lines, expected.lines)
```

Run: `pixi run --frozen -e geovista pytest tests/geodesic/test_line.py -k close_none -v`

Expected: PASS.

- [ ] **Step 2: Take the module out of the ratchet, and watch the check fail**

Delete `  "geovista.geodesic",` from the `ignore_errors` list in `pyproject.toml`, and
`        "geovista.geodesic",` from `RATCHET_BASELINE` in `tests/test_typing_ratchet.py`.

Run: `pixi run --frozen -e geovista pytest tests/test_typing_ratchet.py`

Expected: PASS.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 15 errors in 1 file (checked 86 source files)`, all in
`src/geovista/geodesic.py`, on 13 lines. If the count differs, stop.

- [ ] **Step 3: Overload `distance` on `mean`**

`distance` returns a `float` when `mean` is true and an array otherwise, but is annotated
`float | np.ndarray`, so every caller that wants the mean radius has a union: three lines
here, one in `geoplotter.py`. In `src/geovista/common.py`, extend the `typing` import:

```text
from typing import TYPE_CHECKING, Literal, overload
```

and insert above `def distance(`:

```text
@overload
def distance(  # numpydoc ignore=GL08
    mesh: pv.PolyData,
    /,
    *,
    origin: ArrayLike | None = ...,
    mean: Literal[True] = ...,
) -> float: ...


@overload
def distance(  # numpydoc ignore=GL08
    mesh: pv.PolyData,
    /,
    *,
    origin: ArrayLike | None = ...,
    mean: Literal[False] | None,
) -> np.ndarray: ...


@overload
def distance(  # numpydoc ignore=GL08
    mesh: pv.PolyData,
    /,
    *,
    origin: ArrayLike | None = ...,
    mean: bool | None = ...,
) -> float | np.ndarray: ...


```

`mean=None` falls through `if mean:` to the per-point branch, hence its overload.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 11 errors in 1 file`, on 10 lines.

- [ ] **Step 4: Lists and arrays of points**

In `npoints_by_idx`, convert at the boundary, the first line after the `geod` default:

```text
    lons, lats = np.asanyarray(lons), np.asanyarray(lats)
    start_lonlat = lons[start_idx], lats[start_idx]
```

`BBox._generate_bbox_face`'s `bbox_update` called `npoints_by_idx` about 500 times with
the lists the face is built in, and converting them on every call made `BBox` ten times
slower. Replace its call:

```text
            glons, glats = npoints_by_idx(
                self._bbox_lons,
                self._bbox_lats,
                start_idx=idx1,
                end_idx=idx2,
                npts=self._npts,
                geod=self._geod,
            )
```

with:

```text
            # index the growing lists directly, as npoints_by_idx would convert them
            glons, glats = npoints(
                self._bbox_lons[idx1],
                self._bbox_lats[idx1],
                self._bbox_lons[idx2],
                self._bbox_lats[idx2],
                npts=self._npts,
                geod=self._geod,
            )
```

The defaults of `include_start`, `include_end` and `radians` are the same in both.

`bbox_extend` receives arrays as well as sequences; annotate it so:

```text
        def bbox_extend(
            lons: Sequence[float] | np.ndarray, lats: Sequence[float] | np.ndarray
        ) -> None:
```

`_bbox_lons` and `_bbox_lats` are lists while the face is built, then were reassigned as
arrays for `boundary`'s fancy indexing. Delete the reassignment from
`_generate_bbox_mesh`:

```text
            # convert bbox lons/lats to ndarray (internal convenience i.e., boundary)
            self._bbox_lons = np.asanyarray(self._bbox_lons)
            self._bbox_lats = np.asanyarray(self._bbox_lats)

```

and convert in `boundary` instead:

```text
        edge_lons = np.asanyarray(self._bbox_lons)[edge_idxs]
        edge_lats = np.asanyarray(self._bbox_lats)[edge_idxs]
```

`to_cartesian`, between the two, takes the lists as they are.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 3 errors in 1 file`, on 3 lines.

- [ ] **Step 5: The last optionals**

In the `mesh` property, narrow what `_generate_bbox_mesh` sets, as the module already does
for `_surface_radius` (ruff's S101 is off here):

```text
        if self._mesh is None:
            self._generate_bbox_mesh()
        assert self._mesh is not None
        return self._mesh
```

In `line`, replace `pv.lines_from_points(xyz, close=close)` with
`pv.lines_from_points(xyz, close=bool(close))`; in `npoints`, pass
`radians=bool(radians)` to `geod.npts`. `None` was already falsy in both.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

- [ ] **Step 6: Check that `BBox` neither moves nor slows**

From the repository root:

```bash
git worktree add --detach /tmp/geovista-main main
cat > /tmp/bbox_probe.py <<'EOF'
import hashlib, sys, time, warnings
import numpy as np
warnings.simplefilter("ignore")
import geovista.geodesic
from geovista.geodesic import BBox
times = []
for _ in range(3):
    t = time.perf_counter(); bbox = BBox([-15, 20, 25, -15], [-25, -20, 15, 10]); m = bbox.mesh; times.append(time.perf_counter() - t)
h = hashlib.sha256(np.ascontiguousarray(m.points).tobytes() + np.ascontiguousarray(m.faces).tobytes()).hexdigest()[:16]
b = hashlib.sha256(np.ascontiguousarray(bbox.boundary().points).tobytes()).hexdigest()[:16]
print(geovista.geodesic.__file__, "min %.3fs" % min(times), "mesh", h, "boundary", b)
EOF
(cd /tmp && PYTHONPATH=/tmp/geovista-main/src pixi run --manifest-path "$OLDPWD" --frozen -e geovista python /tmp/bbox_probe.py)
(cd /tmp && PYTHONPATH="$OLDPWD/src" pixi run --manifest-path "$OLDPWD" --frozen -e geovista python /tmp/bbox_probe.py)
git worktree remove --force /tmp/geovista-main
```

Expected: each line names its own tree's `geodesic.py`; the `mesh` and `boundary`
digests match (`deb140f1a1d3e183`, `e9e0e7f47824d330` in the dry run); the branch's time
is within a few milliseconds of `main`'s (0.058 s against 0.052 s in the dry run).

- [ ] **Step 7: Verify, and commit**

Run: `pixi run --frozen -e geovista pytest tests/geodesic tests/common tests/test_typing_ratchet.py`

Expected: PASS.

Run: `pixi run --frozen -e geovista pre-commit run --files src/geovista/geodesic.py src/geovista/common.py tests/geodesic/*.py tests/test_typing_ratchet.py pyproject.toml`

Expected: every hook passes.

Message, humanized: `fix: take geodesic.py out of the typing ratchet`, naming the
`distance` overloads and why `BBox` calls `npoints` itself.

---

### Task 4: retire `geovista.geoplotter` from the ratchet

Counts below were measured on 2026-10-11 with tasks 1 to 3 applied.

**Files:**
- Modify: `pyproject.toml`, `tests/test_typing_ratchet.py`
- Modify: `src/geovista/geoplotter.py`, `src/geovista/crs.py`
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md` (§3.5, here,
  because the code cites it)
- Create: `tests/geoplotter/test_GeoPlotterBase.py`
- Modify: `tests/geoplotter/test_add_mesh.py`, `tests/geoplotter/test_view_poi.py`

**Interfaces:**
- Consumes: task 2's conversions and task 3's `distance` overloads.
- Produces: `GeoPlotterBase` extending `pv.BasePlotter` for `mypy` only; `add_mesh`,
  `add_points`, `add_base_layer`, `add_coastlines` returning `pv.Actor | None`;
  `from_wkt`, `has_wkt` and `to_wkt` taking `pv.DataObject`; typing spec §3.5.

- [ ] **Step 1: Pin the mixin and the branches nothing reached**

Create `tests/geoplotter/test_GeoPlotterBase.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.geoplotter.GeoPlotterBase`."""

from __future__ import annotations

import pyvista as pv

from geovista.geoplotter import GeoPlotter, GeoPlotterBase


def test_runtime_base_is_object():
    """The plotter base mypy sees never reaches runtime (typing spec §3.5)."""
    assert GeoPlotterBase.__bases__ == (object,)


def test_geoplotter_mro():
    """GeoPlotter still finds its own methods before pyvista's."""
    mro = GeoPlotter.__mro__

    assert mro.index(GeoPlotterBase) < mro.index(pv.Plotter)
```

In `tests/geoplotter/test_add_mesh.py`, add `import pyvista as pv` after `import pytest`
and `from geovista.crs import from_wkt` after `import geovista as gv`, then append:

```python
def test_empty_mesh_returns_none():
    """An empty mesh is not added, and nothing is returned for it."""
    p = GeoPlotter()

    assert p.add_mesh(pv.PolyData()) is None
    assert not p.actors


def test_central_meridian_recentred(lfric):
    """A mesh is sliced and transformed for a CRS with a central meridian."""
    p = GeoPlotter(crs="+proj=robin +lon_0=180")

    actor = p.add_mesh(lfric)

    assert actor is not None
    assert from_wkt(actor.mapper.dataset) == p.crs
```

Append to `tests/geoplotter/test_view_poi.py`:

```python
def test_spherical_camera(lfric):
    """On a sphere, the camera looks at the POI from straight above it."""
    p = GeoPlotter()
    p.add_mesh(lfric)

    p.view_poi(x=30, y=10)

    position = np.array(p.camera.position)
    expected = gv.common.to_cartesian(30, 10)[0]
    np.testing.assert_allclose(position / np.linalg.norm(position), expected, atol=1e-6)
    np.testing.assert_allclose(p.camera.focal_point, (0, 0, 0))
```

Run: `pixi run --frozen -e geovista pytest tests/geoplotter/test_GeoPlotterBase.py tests/geoplotter/test_add_mesh.py tests/geoplotter/test_view_poi.py -k "runtime_base or mro or empty_mesh or central_meridian or spherical" -v`

Expected: PASS, 5 tests. They pin what the steps below must not change.

- [ ] **Step 2: Take the module out of the ratchet, and watch the check fail**

Delete `  "geovista.geoplotter",` from `pyproject.toml`'s `ignore_errors` list and
`        "geovista.geoplotter",` from `RATCHET_BASELINE`.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 15 errors in 1 file`, all in `src/geovista/geoplotter.py`, on
11 lines.

- [ ] **Step 3: Let `mypy` see `numpy` and `pyproj`**

Correction 2. In the `TYPE_CHECKING` block, replace:

```text
    from numpy.typing import ArrayLike
    import pyvista as pv
```

with:

```text
    import numpy as np
    from numpy.typing import ArrayLike
    import pyproj
    import pyvista as pv
```

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 16 errors in 1 file`, on 13 lines.

- [ ] **Step 4: Give the mixin its base**

Correction 4. Replace `class GeoPlotterBase:  # numpydoc ignore=PR01` with:

```text
if TYPE_CHECKING:
    # the mixin is only ever combined with a plotter, which mypy needs to know
    _PlotterBase = pv.BasePlotter
else:
    _PlotterBase = object


class GeoPlotterBase(_PlotterBase):  # numpydoc ignore=PR01
```

Then delete what the base now provides:

- the class-level block `    if TYPE_CHECKING:` / `        theme: Theme` and the blank
  line after it;
- `            self.add_point_labels: Callable[..., None]` in `_add_graticule_labels`;
- `                self.add_text: Callable[..., None]` in `_warn_opacity`;
- `        self.camera: pv.Plotter.camera` in `view_poi` (keep `camera = self.camera`);
- `            self.reset_camera: Callable[..., None]` in `view_poi`;
- the three now unused comments: `  # type: ignore[attr-defined]` after
  `self.background_color,`, `  # type: ignore[arg-type]` after
  `scalar_bar_args.update(kwargs["scalar_bar_args"])`, and `  # type: ignore[misc]` after
  `super().add_mesh(mesh, **kwargs)`.

`super().__init__` and `super().add_mesh` are now checked against `pyvista`'s
signatures, so annotate what is passed through as `Any`, not `Any | None`: in
`GeoPlotterBase.__init__`, `*args: Any` and `**kwargs: Any`; in `add_mesh`,
`**kwargs: Any`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 14 errors in 1 file`, on 14 lines. The count rises by one line:
`add_mesh` and `add_points` are now checked as overrides, and `reset_camera` meets the
`_Wrapped` defect.

- [ ] **Step 5: The two upstream defects**

Correction 5. In `_warn_opacity`, replace `            info = pv.GPUInfo()` with:

```text
            # typing spec §8 -- pyvista 0.49 leaves GPUInfo.__init__ unannotated
            gpu_info: Callable[[], pv.GPUInfo] = pv.GPUInfo
            info = gpu_info()
```

In `view_poi`, replace `            self.reset_camera(render=False)` with:

```text
            # typing spec §8 -- pyvista 0.49's _Wrapped drops the descriptor protocol
            reset_camera: Callable[..., None] = self.reset_camera
            reset_camera(render=False)
```

`pv.GPUInfo` is read when the line runs, so the tests that patch `pyvista.GPUInfo` still
reach their mock.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 12 errors in 1 file`, on 12 lines.

- [ ] **Step 6: Values whose types were looser than their use**

In `_add_graticule_labels`, the manifold branch replaced a `list[str]` with an array;
keep it a list: `            labels = np.array(labels)[idxs].tolist()`.

In `add_mesh`, `src_crs and src_crs != tgt_crs` is a `CRS | None | bool`, and `planar`
cannot take the `None` the condition already excludes. Replace:

```text
            transform_required = src_crs and src_crs != tgt_crs
```

with:

```text
            transform_required = src_crs is not None and src_crs != tgt_crs
            src_planar = src_crs is not None and planar(src_crs)
```

and `            if transform_required and not cloud and not planar(src_crs):` with
`            if transform_required and not cloud and not src_planar:`. A `CRS` is always
truthy, so the condition is unchanged.

`set_central_meridian` returns `None` only where `get_central_meridian` finds no
meridian, so it cannot here. Replace
`                    tgt_crs = set_central_meridian(tgt_crs, 0)` with:

```text
                    centred = set_central_meridian(tgt_crs, 0)
                    # get_central_meridian found one, so it can be reset
                    assert centred is not None
                    tgt_crs = centred
```

`add_points` hands `from_wkt`, `has_wkt` and `to_wkt` whatever `pv.wrap` returns, a
`DataSet`, `MultiBlock` or `PartitionedDataSet`; the three only touch `field_data`, which
every `pv.DataObject` has. In `src/geovista/crs.py`, still ratcheted, widen
`mesh: pv.PolyData` to `mesh: pv.DataObject` in all three signatures, and the docstrings'
`mesh : :class:`~pyvista.PolyData`` to `mesh : :class:`~pyvista.DataObject``.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 4 errors in 1 file`, on 4 lines: the two overrides, `add_mesh`'s
`None`, and `resize`'s `zlevel`.

- [ ] **Step 7: Say where `geovista` departs from `pyvista`**

Correction 4, as {user}`bjlittle` ruled. Annotate `add_mesh`, `add_points`,
`add_base_layer` and `add_coastlines` `-> pv.Actor | None`, and in each docstring replace:

```text
        Returns
        -------
        Actor
            The rendered actor added to the plotter scene.
```

with:

```text
        Returns
        -------
        Actor or None
            The rendered actor added to the plotter scene, or ``None`` when the
            mesh is empty and nothing is added.
```

Mark the two `def` lines:

```text
    def add_mesh(  # type: ignore[override]  # typing spec §3.5
    def add_points(  # type: ignore[override]  # typing spec §3.5
```

Insert typing spec §3.5 after §3.4's last paragraph (ending "on account of `geopy` being
untyped."), humanized:

```text
(typing-spec-3-5)=
### 3.5 Where geovista departs from pyvista

`GeoPlotterBase` is a mixin. `GeoPlotter` combines it with `pyvista`'s `Plotter`, and
`geovista.qt` with the `pyvistaqt` plotters, but `mypy` could not know that, so the mixin
declared what it borrowed: `Callable[..., None]` for `add_text`, `add_point_labels` and
`reset_camera`, `Theme` for `theme`, and for `camera` an annotation that is not a type
(§3.4). Each clashed with `pyvista`'s definition. Change 5 gives the mixin
`pv.BasePlotter` as its base under `TYPE_CHECKING` and `object` at runtime, so the
declarations go, along with the three `type: ignore` comments they needed.

What remains is deliberate. `add_mesh` and `add_points` take the mesh or points
positionally and everything else by keyword, where `pyvista` takes a long run of
positional arguments, and `add_mesh` adds nothing for an empty mesh and returns `None`.
Matching `pyvista` would change `geovista`'s public API. So both `def` lines carry
`# type: ignore[override]`, citing this section, and `add_mesh`, `add_points`,
`add_base_layer` and `add_coastlines`, which return what `add_mesh` returns, are
annotated `pv.Actor | None`. Change 5 removes three `type: ignore` comments from the
library and adds these two, which leaves nine.
```

Use the spec's own cross-reference form for the two section references
(`` {ref}`§3.4 <typing-spec-3-4>` ``), as the surrounding sections do.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 1 error in 1 file`: `resize`'s `zlevel`.

- [ ] **Step 8: Keep the array `zlevel`'s exceptions**

The deferred defect, {issue}`2618`. Replace
`                mesh = resize(mesh, radius=radius, zlevel=zlevel, zscale=zscale)` with:

```text
                mesh = resize(
                    mesh, radius=radius, zlevel=int(np.asarray(zlevel)), zscale=zscale
                )
```

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

- [ ] **Step 9: Probe what did not change**

From the repository root:

```bash
git worktree add --detach /tmp/geovista-main main
cat > /tmp/zlevel_probe.py <<'EOF'
import warnings
import numpy as np, pyvista as pv
warnings.simplefilter("ignore")
pv.OFF_SCREEN = True
import geovista as gv
from geovista.bridge import Transform
print(gv.__file__)
for label, mesh, zlevel in (
    ("several", Transform.from_points([0, 10, 20], [0, 10, 20]), np.array([1, 2, 3])),
    ("one", Transform.from_points([0], [0]), np.array([2])),
    ("scalar", gv.Transform.from_1d([0, 10, 20], [0, 10, 20]), 2),
):
    try:
        print(label, type(gv.GeoPlotter(off_screen=True).add_mesh(mesh, zlevel=zlevel)).__name__)
    except Exception as e:
        print(label, type(e).__name__, str(e)[:60])
EOF
(cd /tmp && PYTHONPATH=/tmp/geovista-main/src pixi run --manifest-path "$OLDPWD" --frozen -e geovista python /tmp/zlevel_probe.py)
(cd /tmp && PYTHONPATH="$OLDPWD/src" pixi run --manifest-path "$OLDPWD" --frozen -e geovista python /tmp/zlevel_probe.py)
git worktree remove --force /tmp/geovista-main
```

Expected: each tree prints its own `geovista/__init__.py` first, then both print `several ValueError The truth value of an array with more
than one element`, `one TypeError only 0-dimensional arrays can be converted`, and
`scalar Actor`.

- [ ] **Step 10: Retire `attr-defined` from the gallery override**

Correction 6. In `pyproject.toml`, replace the `geovista.examples.*` override's comment
and codes with, humanized:

```text
[[tool.mypy.overrides]]
# typing spec §3.4 -- two "pyvista" 0.49 defects, both fixed on its "main":
# "_Wrapped" loses the descriptor protocol, and "Camera.zoom" carries no
# annotations. Confined to the gallery, whose scripts are published as
# example code, so a "type: ignore" comment in one is a directive a reader
# is invited to copy. Withdraw when the "pyvista" floor carries both fixes.
disable_error_code = ["call-arg", "no-untyped-call"]
module = ["geovista.examples.*"]
```

Measure the gallery with its ratchet entry lifted, then restore it:

```bash
cp pyproject.toml /tmp/pyproject.toml.bak
sed -i '/^  "geovista.examples.\*",$/d' pyproject.toml
pixi run --frozen -e geovista mypy | tail -1
cp /tmp/pyproject.toml.bak pyproject.toml
```

Expected: `Found 35 errors in 10 files`, against 28 on `main`; the seven more are
`arg-type` in `examples/spatial_index/uber_h3.py`, and none is `attr-defined`.

- [ ] **Step 11: Verify the whole**

Run: `pixi run --frozen -e geovista pytest tests/geoplotter tests/geodesic tests/crs tests/test_typing_ratchet.py tests/test_spec_conventions.py`

Expected: PASS.

Run: `pixi run --frozen -e test-py314 pytest tests/geoplotter tests/geodesic`

Expected: PASS.

Run: `pixi run --frozen -e geovista pytest -m "not image" --numprocesses auto --dist worksteal`

Expected: exit 0, `main`'s count plus 15 new tests less the two ratchet cases that go with
the entries (2804 + 13 = 2817 on 2026-10-11, with a docs build in `docs/_build`).

Run: `pixi run --frozen -e geovista pre-commit run --files src/geovista/geoplotter.py src/geovista/crs.py tests/geoplotter/*.py tests/test_typing_ratchet.py pyproject.toml docs/src/developer/specs/2026-10-06-type-coverage-design.md`

Expected: every hook passes.

- [ ] **Step 12: Commit**

Message, humanized: `fix: take geoplotter.py out of the typing ratchet`, naming the
mixin's base, the two deliberate departures and the gallery override.

---

### Task 5: the spec and the changelog

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §3.3, §3.4,
  §4, §8
- Create: `changelog/{PR}.bugfix.rst`

- [ ] **Step 1: Say what change 5 found**

In typing spec §3.3, after change 4's paragraphs (ending "where it meant `TypeError`."),
insert, humanized:

```text
Change 5 met the idiom where `mypy` could not see it. `geoplotter.py` loaded `numpy` and
`pyproj` with `lazy.load` and imported neither under `TYPE_CHECKING`, so both were `Any`
and the module reported 15 lines where it had 16. `_add_graticule_labels` indexed
`GraticuleGrid.lonlat` as an array and multiplied its `mask` by an integer, which repeats
a list rather than scaling it; both now convert where they are used. `npoints_by_idx`
converts its points too, but `BBox` called it about five hundred times with lists that
grow to tens of thousands of points, and converting them on every call made `BBox` ten
times slower. `BBox` now indexes its own lists and calls `npoints` directly: a private
caller on a hot path can step past a converting boundary instead of paying for it.
```

- [ ] **Step 2: Correct §3.4**

In the second bullet, replace from "Corrected to `pv.Camera` on a copy of the tree" to the
end of the bullet with, humanized:

```text
Change 5 removed the declaration ({ref}`§3.5 <typing-spec-3-5>`). All 45 cleared,
and 44 `no-untyped-call` took their place, because `Camera.zoom` has no annotations in
0.49.0. That residue is upstream, and `pyvista` `main` already annotates it. Tracked by
{issue}`2569`.
```

Replace the quoted `toml` block with task 4 step 10's override, verbatim. Replace the
paragraph from "The comment is quoted as it stands" to "nothing left to hold." with,
humanized:

```text
The comment is quoted as it stands in `pyproject.toml`, because a specification that
quotes the code has to quote what the code says. Both codes now name upstream defects
fixed on `pyvista` `main`, so the override goes when the floor reaches the release that
carries them ({issue}`2568`). Change 5 also adds seven errors in `uber_h3.py`, which
keeps the plotter's actors in fields typed `str | PolyData`. They appeared once
`add_mesh` admitted it can return `None`, and change 7 corrects them with the rest of the
gallery.
```

The paragraph after it opens "Neither code appears in the library, where `attr-defined` is
zero and `call-arg` is one". Measured on 2026-10-11 with the whole ratchet lifted, the
library has no `attr-defined`, one `call-arg` (`cli.py`) and four `no-untyped-call`
(`raster.py` twice, `themes.py` twice), all in modules change 6 retires. Replace that
sentence with, humanized:

```text
In the library, measured on 2026-10-11 with the whole ratchet lifted, `attr-defined` is
zero, `call-arg` is one, in `cli.py`, and `no-untyped-call` is four, in `raster.py` and
`themes.py`, all in modules change 6 retires, so the suppression stays confined to where
the plotting calls are.
```

- [ ] **Step 3: §8 item 3, and a new item 8**

Change item 3's status from `**Open** ({issue}`2569`, owned by change 5 of …)` to
`` **Resolved** (TODAY, {pull}`PR`) ``, and append to its text, humanized:

```text
Change 5 removed the annotation and swapped `attr-defined` for `no-untyped-call` in the
override, whose comment now names its real causes.
```

Append item 8, humanized:

```text
8. **Open** ({issue}`2568`) — **Two typed locals in `geoplotter.py` wait on the same
   `pyvista` release.** `pyvista` 0.49 leaves `GPUInfo.__init__` unannotated, and its
   `_Wrapped` decorator, item 2's cause, breaks `self.reset_camera(render=False)`. So
   `_warn_opacity` and `view_poi` call each through a local annotated `Callable`.
   `pyvista` `main` fixes both, and the locals come out with the floor that carries
   them, the trigger items 2 and 6 already wait on.
```

- [ ] **Step 4: Mark row 5 in progress**

In the §4 table, change row 5's Status from `not started` to
`` in progress ({pull}`PR`) ``.

- [ ] **Step 5: Write the changelog fragment**

Create `changelog/{PR}.bugfix.rst`, humanized:

```rst
``geovista.geodesic.BBox`` treats ``crs=None`` as WGS84, as documented, where it
raised ``CRSError``, and ``npoints`` and ``npoints_by_idx`` treat ``npts=None`` as
``GEODESIC_NPTS``, where they raised ``TypeError``. Graticule labels accept a
``GraticuleGrid`` whose points or mask are lists; a list mask was repeated rather
than scaled. ``GeoPlotter.add_mesh``, ``add_points``, ``add_base_layer`` and
``add_coastlines`` are annotated to return ``None`` for an empty mesh, which they
already did. ``geovista.geodesic`` and ``geovista.geoplotter`` also leave the
typing ratchet, so ``mypy`` checks them in full. (:user:`claude`)
```

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py {PR} "changelog/{PR}.bugfix.rst"`

Expected: `🆗 Your changelog contribution looks good to me.`

- [ ] **Step 6: Verify, commit and push**

Run: `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/test_status_references.py tests/docs/test_readingtime_coverage.py`

Expected: PASS.

Run: `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status {PR}`

Expected: every reference holds.

Run, from `docs/`:

```bash
pixi run --frozen -e docs sphinx-build -b html -W --keep-going \
  -D plot_docstring=False -D plot_gallery=False \
  -D plot_inline=False -D plot_tutorial=False \
  -d _build/doctrees src _build/html
```

Expected: `build succeeded`, with no warnings.

Message, humanized: `docs: correct the typing spec against change 5's measurements`.
The pull request body says it closes {issue}`2569`.

---

### Task 6: land row 5

The pull request's last commit, made once the implementation, the final review and any
Codex round are done.

- [ ] **Step 1:** In the typing spec §4 table, replace row 5's `` in progress
  ({pull}`PR`) `` with `` ✅ landed (DATE, {pull}`PR`) ``, `DATE` being `date -u +%F`
  on the day it is committed; a landed date is held to within a day of the UTC merge.
- [ ] **Step 2:** Run `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/test_status_references.py`
  and `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status {PR}`
  (expected PASS and all hold), commit `docs: mark row 5 of the typing roadmap landed`,
  push. If the merge slips past the next UTC day, redate it first.

---

## Done when

- `pixi run --frozen -e geovista mypy` exits 0 with `geovista.geodesic` and
  `geovista.geoplotter` absent from both the ratchet and `RATCHET_BASELINE`.
- The five failing tests of tasks 1 and 2 were seen failing, then passing.
- The suite passes in `geovista`, the new tests in `test-py314`, `BBox` matches `main`
  in shape and speed, and CI is green, image tests included.
- The library holds nine `type: ignore` comments, two of them task 4's, and the gallery
  override names `call-arg` and `no-untyped-call`.
- Typing spec §3.3, §3.4, §3.5, §4 and §8 agree with the measurements, and row 5 reads
  landed as the pull request's last commit.
- Every deferred item has an `agentic` issue, linked from the Follow-ups below and from the
  pull request's description.

## Follow-ups

- {issue}`2618`: `add_mesh` raises on an array `zlevel` when the mesh needs no
  transform, because `core.resize` takes only an `int`. Deferred by {user}`bjlittle`'s
  ruling; task 4 keeps the exceptions it raised.

The final review's minors, and any defect it sets aside, each get an `agentic` issue
listed here before the pull request leaves draft.

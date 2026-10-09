---
orphan: true
---

# type coverage change 4 — `common.py`

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** take `geovista.common` out of the typing ratchet so that `mypy` checks it in
full, and fix the two defects checking it brings to light: `vectors_to_cartesian`
refusing lists, and `cast_UnstructuredGrid_to_PolyData` raising the wrong exception.

**Architecture:** `common.py` already imports `numpy` under `TYPE_CHECKING`, so its 19
lines are real. Eight trace to two public functions that never convert their
`ArrayLike` input, `vectors_to_cartesian` and `nan_mask`, and converting at their
boundaries clears them. One is a runtime type guard on an annotated parameter, which
`mypy` calls unreachable and which raised `AttributeError` where it meant `TypeError`.
The other ten are variables reassigned to another type and return values typed looser
than their annotations, each corrected without a behaviour change except
`triangulated`, which now returns the `bool` it promises.

**Tech Stack:** `mypy` 2.x in strict mode, `numpy` 2.5, `pyvista` 0.49, `pytest` with
`pytest-xdist`, `pixi` (conda-forge).

**Spec:** `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, cited throughout
as `typing spec §…`. This plan implements change 4 of typing spec §4.

**Branch:** `debt/typing-common`, whose prefix earns `type: tech-debt` automatically. The
plan is committed first and the pull request held in draft until the implementation lands
on it. `{PR}` below is that pull request's number.

## Global Constraints

- **Copyright header** and `from __future__ import annotations` on every Python file
  (root `AGENTS.md`, ruff-enforced). **Line length 88.**
- **Docstrings.** NumPy style, validated by `numpydoc-validation` on `src/`.
  `--doctest-modules` is on, so `wrap`'s `>>>` examples run.
- **The strictness settings stay as they are** (typing spec §7).
- **A published `ArrayLike` parameter is converted at the boundary, never narrowed**
  (typing spec §3.3, §5). A private helper past a converting boundary is annotated with
  what it receives. Behaviour only widens.
- **No `type: ignore`, and no new `noqa`** to make a typing change pass.
- **The ratchet only shrinks, in step:** `pyproject.toml` and `RATCHET_BASELINE` in the
  same commit as the fixes that make the module pass. Every commit passes the `mypy` hook.
- **Tests:** one file per function under `tests/common/`, as `tests/AGENTS.md` lays out;
  a citation in a docstring carries its prefix (`typing spec §3.3`, never a bare `§3.3`),
  or `tests/test_spec_conventions.py` fails. Run the full suite in `geovista`, and the
  new tests in `test-py314`, which CI's test jobs use and which can lock other versions.
- **Local suite runs** never pass `-p no:cacheprovider`; read results from failures and
  the exit code.
- **Changelog.** One fragment, `{PR}.bugfix.rst`, signed ``:user:`claude` ``; the
  `agentic` label on the pull request.
- **Every deferred item gets an `agentic` issue**, linked from the Follow-ups at the end
  of this plan and from the pull request's description (root `AGENTS.md`).
- **Prose for other readers is humanized:** the spec's new text, commit messages, the
  fragment, the pull request body and any issue. This plan is not.
- **Names.** Repository text names the reviewer as {user}`bjlittle`.

## Four corrections this plan makes to the spec

Measured on 2026-10-09 against `main` at `69879c08`, and dry-run end to end in a scratch
worktree.

1. **Row 4's count reproduces.** With the entry lifted at `8b2f0ab3`, where the census
   was taken, `mypy` reports 68 errors on 20 lines, the roadmap's 20. On `main` it reports
   67 on 19: change 2's `lazy_loader` override cleared the import.
2. **The idiom is eight lines in two functions, not the census's six, and both are
   defects.** `vectors_to_cartesian` reads `.shape` from `lons`, `lats` and the vector
   components without converting any of them, so a list raises `AttributeError: 'list'
   object has no attribute 'shape'` (four lines), and its arithmetic on the unconverted
   components is three more. `nan_mask` returns its input unchanged when it is not masked,
   so a list comes back as a list where it promises an array (one line). Both convert at
   the boundary. The other five public `ArrayLike` functions, `distance`, `to_cartesian`,
   `to_lonlat`, `to_lonlats` and `wrap`, already accept lists, measured.
3. **A runtime type guard raised the wrong exception, and needs a rule.**
   `cast_UnstructuredGrid_to_PolyData` is annotated `mesh: pv.UnstructuredGrid` and checks
   `isinstance(mesh, pv.UnstructuredGrid)`, so `mypy` reports the check's body unreachable.
   That body was broken besides: `type(mesh).split(" ")` calls `split` on a class, so any
   other dataset raised `AttributeError: type object 'PolyData' has no attribute 'split'`
   where it meant a `TypeError`. `mesh` is annotated with the type the function accepts
   before it validates, `pv.DataSet`, which keeps the check reachable without a
   `type: ignore`. The pattern can recur in the modules still ratcheted, so typing spec
   §3.3 gains the rule.
4. **`vtk` stays lazy and untyped.** Its four calls in `common.py` toggle VTK warnings.
   `import vtk` has no `py.typed`, and the stubs live in `vtkmodules`, but aliasing
   `vtkmodules.vtkCommonCore` as `vtk` trips ruff's N813, and a `noqa` to type four
   toggles is not worth it. This is a decision, not deferred work.

## Review Focus

1. **A scalar longitude still comes back from `wrap` as a 1D array, and a 0D array stays
   0D**, since `[lons]` becomes `np.atleast_1d(lons)`. → task 3, `test_scalar_is_1d` and
   `test_0d_array_stays_0d`.
2. **`vectors_to_cartesian` still refuses a component of another shape**, now for lists
   too. → task 1, `test_vectors_must_match_the_points`.
3. **Masked data through `nan_mask` still comes back filled with NaN**, since
   `np.asanyarray` keeps a masked array masked. → the existing `test_masked_to_nans`.
4. **`distance(..., mean=False)` still returns a distance per point**, under the wider
   annotation of its result. → task 3, `test_origin_list`.
5. **The gallery's meshes do not move**, though `to_cartesian` under them is edited. →
   task 3's fingerprint step; all 21 pantry meshes matched `main` in the dry run.

---

### Task 1: honour `ArrayLike` in `vectors_to_cartesian` and `nan_mask`

**Files:**
- Modify: `src/geovista/common.py`, `vectors_to_cartesian` and `nan_mask`
- Create: `tests/common/test_vectors_to_cartesian.py`
- Modify: `tests/common/test_nan_mask.py`

**Interfaces:**
- Consumes: nothing.
- Produces: both functions converting at their first statements, which clears eight of
  task 3's lines.

- [ ] **Step 1: Write the failing tests**

Create `tests/common/test_vectors_to_cartesian.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.vectors_to_cartesian`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.common import vectors_to_cartesian

#: Two points, as longitudes and latitudes.
LONS, LATS = [0.0, 90.0], [0.0, 45.0]

#: The eastward, northward and upward components of a vector at each point.
VECTORS = ([1.0, 2.0], [3.0, 4.0], [5.0, 6.0])


def _arrays(*values: list[float]) -> tuple[np.ndarray, ...]:
    """Return each of the values as an array."""
    return tuple(np.array(value) for value in values)


@pytest.mark.parametrize(
    ("component", "expected"),
    [(0, [0.0, 1.0, 0.0]), (1, [0.0, 0.0, 1.0]), (2, [1.0, 0.0, 0.0])],
    ids=["eastward", "northward", "upward"],
)
def test_unit_vectors_at_the_origin(component, expected):
    """Each unit component at (0, 0) points along its own cartesian axis."""
    vectors = [np.zeros(1), np.zeros(1), np.zeros(1)]
    vectors[component] = np.ones(1)

    result = vectors_to_cartesian(np.zeros(1), np.zeros(1), tuple(vectors), radius=1.0)

    np.testing.assert_allclose(np.ravel(result), expected, atol=1e-15)


@pytest.mark.parametrize("given", ["points", "vectors", "both"])
def test_lists(given):
    """Lists are accepted wherever arrays are (typing spec §3.3)."""
    expected = vectors_to_cartesian(*_arrays(LONS, LATS), _arrays(*VECTORS))
    lons, lats = (LONS, LATS) if given != "vectors" else _arrays(LONS, LATS)
    vectors = VECTORS if given != "points" else _arrays(*VECTORS)

    result = vectors_to_cartesian(lons, lats, vectors)

    np.testing.assert_array_equal(result, expected)


def test_vectors_must_match_the_points():
    """A component of another shape than the points is refused."""
    with pytest.raises(ValueError, match="some 'vectors' do not have same shape"):
        _ = vectors_to_cartesian(LONS, LATS, ([1.0], [3.0, 4.0], [5.0, 6.0]))
```

Append to `tests/common/test_nan_mask.py`:

```python
def test_list():
    """A list comes back as the array its annotation promises (typing spec §3.3)."""
    result = nan_mask([1.0, 2.0])

    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, [1.0, 2.0])
```

- [ ] **Step 2: Run them, and watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/common/test_vectors_to_cartesian.py tests/common/test_nan_mask.py -v`

Expected: 5 failed, 10 passed. The three `test_lists` cases and
`test_vectors_must_match_the_points` fail with `AttributeError: 'list' object has no
attribute 'shape'`, and `nan_mask`'s `test_list` on its `isinstance` check. The three
`test_unit_vectors_at_the_origin` cases pass already: they pin the arithmetic.

- [ ] **Step 3: Convert at both boundaries**

In `vectors_to_cartesian`, replace:

```text
    radius += radius * zlevel_array * zscale

    if lons.shape != lats.shape:
        msg = f"'lons' and 'lats' do not have same shape: {lons.shape} != {lats.shape}."
        raise ValueError(msg)

    if any(x.shape != lons.shape for x in vectors):
        msg = (
            "some 'vectors' do not have same shape as 'lons' : "
            f"{[x.shape for x in vectors]} != {lons.shape}."
        )
        raise ValueError(msg)

    lons, lats = (np.deg2rad(arr) for arr in (lons, lats))
    u, v, w = vectors
```

with:

```text
    radius += radius * zlevel_array * zscale

    lons, lats = np.asanyarray(lons), np.asanyarray(lats)
    u, v, w = (np.asanyarray(component) for component in vectors)

    if lons.shape != lats.shape:
        msg = f"'lons' and 'lats' do not have same shape: {lons.shape} != {lats.shape}."
        raise ValueError(msg)

    if any(x.shape != lons.shape for x in (u, v, w)):
        msg = (
            "some 'vectors' do not have same shape as 'lons' : "
            f"{[x.shape for x in (u, v, w)]} != {lons.shape}."
        )
        raise ValueError(msg)

    lons, lats = (np.deg2rad(arr) for arr in (lons, lats))
```

In `nan_mask`, make the conversion the first statement after the docstring:

```text
    """
    data = np.asanyarray(data)

    if np.ma.isMaskedArray(data):
```

`np.asanyarray` returns an array, masked or not, unchanged, so only lists and other
non-arrays see a difference.

- [ ] **Step 4: Run them again**

Run: `pixi run --frozen -e geovista pytest tests/common/test_vectors_to_cartesian.py tests/common/test_nan_mask.py -v`

Expected: PASS, 15 tests.

- [ ] **Step 5: Commit**

Message, humanized: `fix: accept lists in vectors_to_cartesian and nan_mask`, with a
body naming the `AttributeError`, the list `nan_mask` returned, and the tests that failed
first. `geovista.common` is still ratcheted, so the `mypy` hook passes.

---

### Task 2: raise the `TypeError` the cast's guard means

**Files:**
- Modify: `src/geovista/common.py`, `cast_UnstructuredGrid_to_PolyData`
- Create: `tests/common/test_cast_UnstructuredGrid_to_PolyData.py`

**Interfaces:**
- Consumes: nothing.
- Produces: a guard that raises `TypeError`, whose annotation task 3 widens.

- [ ] **Step 1: Write the failing test**

Create `tests/common/test_cast_UnstructuredGrid_to_PolyData.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.cast_UnstructuredGrid_to_PolyData`."""

from __future__ import annotations

import pytest
import pyvista as pv

from geovista.common import cast_UnstructuredGrid_to_PolyData


def test_converts():
    """An unstructured grid becomes the surface it describes."""
    sphere = pv.Sphere()

    result = cast_UnstructuredGrid_to_PolyData(sphere.cast_to_unstructured_grid())

    assert isinstance(result, pv.PolyData)
    assert (result.n_points, result.n_cells) == (sphere.n_points, sphere.n_cells)


def test_not_an_unstructured_grid():
    """Anything else is refused with a TypeError naming what was given."""
    with pytest.raises(
        TypeError, match=r"Expected a 'pyvista\.UnstructuredGrid', got 'PolyData'"
    ):
        _ = cast_UnstructuredGrid_to_PolyData(pv.Sphere())
```

- [ ] **Step 2: Run it, and watch it fail**

Run: `pixi run --frozen -e geovista pytest tests/common/test_cast_UnstructuredGrid_to_PolyData.py -v`

Expected: 1 failed, 1 passed. `test_not_an_unstructured_grid` fails with
`AttributeError: type object 'PolyData' has no attribute 'split'`.

- [ ] **Step 3: Name the type that was given**

Replace:

```text
        dtype = type(mesh).split(" ")[1][:-1]
        emsg = f"Expected a 'pyvista.UnstructuredGrid', got {dtype}."
```

with:

```text
        emsg = f"Expected a 'pyvista.UnstructuredGrid', got '{type(mesh).__name__}'."
```

- [ ] **Step 4: Run it again**

Run: `pixi run --frozen -e geovista pytest tests/common/test_cast_UnstructuredGrid_to_PolyData.py -v`

Expected: PASS, 2 tests.

- [ ] **Step 5: Commit**

Message, humanized: `fix: raise the TypeError cast_UnstructuredGrid_to_PolyData means`.

---

### Task 3: retire `geovista.common` from the ratchet

Counts below were measured on 2026-10-09 with tasks 1 and 2 applied.

**Files:**
- Modify: `pyproject.toml`, `tests/test_typing_ratchet.py`
- Modify: `src/geovista/common.py`
- Modify: `tests/common/test_distance.py`, `test_to_lonlat.py`, `test_to_lonlats.py`,
  `test_wrap.py`, `test_triangulated.py`

**Interfaces:**
- Consumes: tasks 1 and 2's code.
- Produces: `common.py` checked in full; `cast_UnstructuredGrid_to_PolyData(mesh:
  pv.DataSet)`; `triangulated` returning `bool`.

- [ ] **Step 1: Pin the contract**

These pass already. Append to `tests/common/test_distance.py`:

```python
def test_origin_list(lfric):
    """An origin given as a list is the origin given as an array (typing spec §3.3)."""
    expected = distance(lfric, origin=np.array([1.0, 2.0, 3.0]), mean=False)

    result = distance(lfric, origin=[1.0, 2.0, 3.0], mean=False)

    assert result.shape == (lfric.n_points,)
    np.testing.assert_array_equal(result, expected)
```

to `tests/common/test_to_lonlat.py`:

```python
def test_list(degrees):
    """A point given as a list is the point given as an array (typing spec §3.3)."""
    point = np.asarray(degrees.xyz, dtype=float)

    np.testing.assert_array_equal(to_lonlat(point.tolist()), to_lonlat(point))
```

to `tests/common/test_to_lonlats.py`:

```python
def test_nested_lists(manydegrees):
    """Nested lists are the points given as an array (typing spec §3.3)."""
    points = np.asarray(manydegrees.xyz, dtype=float)

    np.testing.assert_array_equal(to_lonlats(points.tolist()), to_lonlats(points))
```

and to `tests/common/test_wrap.py`:

```python
def test_scalar_is_1d():
    """A scalar longitude comes back as a 1D array of one."""
    result = wrap(180)

    assert result.shape == (1,)
    np.testing.assert_array_equal(result, [-180.0])


def test_0d_array_stays_0d():
    """A 0D array is iterable, so it keeps its dimension."""
    result = wrap(np.array(180.0))

    assert result.shape == ()
    np.testing.assert_array_equal(result, -180.0)
```

Run: `pixi run --frozen -e geovista pytest tests/common/test_distance.py tests/common/test_to_lonlat.py tests/common/test_to_lonlats.py tests/common/test_wrap.py -k "origin_list or test_list or nested_lists or scalar_is_1d or 0d_array" -v`

Expected: PASS.

- [ ] **Step 2: Take the module out of the ratchet, and watch the check fail**

Delete `  "geovista.common",` from the `ignore_errors` list in `pyproject.toml`, and
`        "geovista.common",` from `RATCHET_BASELINE` in `tests/test_typing_ratchet.py`
(its other mentions are `_drift` sample data, and stay).

Run: `pixi run --frozen -e geovista pytest tests/test_typing_ratchet.py`

Expected: PASS.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 11 errors in 1 file (checked 86 source files)`, every one in
`src/geovista/common.py`, on 11 lines. If the count differs, stop.

- [ ] **Step 3: The cast, annotated with what it accepts**

Correction 3. In `cast_UnstructuredGrid_to_PolyData`, replace `    mesh:
pv.UnstructuredGrid,` with `    mesh: pv.DataSet,`; in its docstring replace:

```text
    mesh :  :class:`~pyvista.UnstructuredGrid`
        The unstructured grid to be converted.
```

with:

```text
    mesh : :class:`~pyvista.DataSet`
        The unstructured grid to be converted. Any other kind of dataset raises
        :class:`TypeError`.
```

and replace `    result = pv.core.filters._get_output(alg)  # noqa: SLF001` with
`    result: pv.PolyData = pv.core.filters._get_output(alg)  # noqa: SLF001`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 9 errors in 1 file`.

- [ ] **Step 4: Variables that change type**

In `distance`, replace `    result = np.sqrt(np.sum(pts * pts, axis=1))` with
`    result: float | np.ndarray = np.sqrt(np.sum(pts * pts, axis=1))`.

In `from_cartesian`, the lines branch reuses `cell_pids`, an array earlier in the
function, for a list; rename it `poi_cell_pids` in its three uses:

```text
                poi_cell_pids = [
                    mesh.get_cell(cid).point_ids for cid in poi_cells[VTK_CELL_IDS]
                ]
                mask_positive = lons[poi_cell_pids] > 0
```

and `                    select_pids = np.asanyarray(poi_cell_pids)[select_mask]`. The
branch runs under `test_lines_closed_interval` in `tests/common/test_from_cartesian.py`,
measured with coverage; `tests/gridlines` never reaches it.

In both `to_cartesian` and `vectors_to_cartesian`, replace
`    radius += radius * zlevel_array * zscale` with
`    radii = radius + radius * zlevel_array * zscale`; in `to_cartesian` use `radii` in
place of `radius` in the three `np.ravel(radius * ...)` lines, and in
`vectors_to_cartesian` return `(radii * wx, radii * wy, radii * wz)`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 4 errors in 1 file`.

- [ ] **Step 5: Return values, and `triangulated`'s bool**

Append to `tests/common/test_triangulated.py`:

```python
def test_returns_bool(lam_uk):
    """The result is the bool its annotation promises, not a numpy bool."""
    assert type(triangulated(lam_uk)) is bool
```

Run: `pixi run --frozen -e geovista pytest tests/common/test_triangulated.py -v`

Expected: `test_returns_bool` FAILS, `<class 'numpy.bool'> is bool`.

In `to_lonlat`, declare the unpacked result:

```text
    result: np.ndarray
    (result,) = to_lonlats(point, radians=radians, radius=radius, rtol=rtol, atol=atol)
```

In `triangulated`, replace the two lines `result: bool = np.all(...)` and
`return result` with `    return bool(np.all(np.diff(_face_offsets(surface)) == 3))`
(ruff's RET504 refuses an assignment followed by its own return).

In `wrap`, replace `        lons = [lons]` with `        lons = np.atleast_1d(lons)`, and
`        dtype = np.float64` with `        dtype = np.dtype(np.float64)`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

Run: `pixi run --frozen -e geovista pytest tests/common/test_triangulated.py -v`

Expected: PASS, 3 tests.

- [ ] **Step 6: Verify the whole**

Run: `pixi run --frozen -e geovista pytest tests/common tests/test_typing_ratchet.py`

Expected: PASS, 482 tests, 38 more than on `main`: 39 new cases, less
`test_ratchet_entry_resolves[geovista.common]`, which goes with the entry.

Run: `pixi run --frozen -e test-py314 pytest tests/common`

Expected: PASS.

Run: `pixi run --frozen -e geovista pytest -m "not image" --numprocesses auto --dist worksteal`

Expected: exit 0, `2757 passed` with a docs build in `docs/_build` (`main`'s 2719 and 38).

Run: `pixi run --frozen -e geovista pre-commit run --files src/geovista/common.py tests/common/*.py tests/test_typing_ratchet.py pyproject.toml`

Expected: every hook passes.

- [ ] **Step 7: Check that the gallery's meshes do not move**

The pantry's meshes reach `to_cartesian` through the bridge. Fingerprint all of them on
`main` and on the branch, from the repository root:

```bash
git worktree add --detach /tmp/geovista-main main
cat > /tmp/fingerprint.py <<'EOF'
import hashlib, inspect, json, sys, warnings
import numpy as np
from geovista.pantry import meshes

warnings.simplefilter("ignore")
found = {}
for name, fn in sorted(inspect.getmembers(meshes, inspect.isfunction)):
    if fn.__module__ != meshes.__name__ or name.startswith("_"):
        continue
    mesh, digest = fn(), hashlib.sha256()
    digest.update(np.ascontiguousarray(mesh.points).tobytes())
    digest.update(np.ascontiguousarray(getattr(mesh, "faces", [])).tobytes())
    for key in sorted(mesh.array_names):
        array = np.asarray(mesh[key])
        text = "".join(array.ravel()) if array.dtype.kind == "U" else None
        digest.update(key.encode())
        digest.update(text.encode() if text is not None else array.tobytes())
    found[name] = digest.hexdigest()
json.dump(found, open(sys.argv[1], "w"), indent=1)
EOF
(cd /tmp && PYTHONPATH=/tmp/geovista-main/src pixi run --manifest-path "$OLDPWD" --frozen -e geovista python /tmp/fingerprint.py /tmp/main.json)
(cd /tmp && PYTHONPATH="$OLDPWD/src" pixi run --manifest-path "$OLDPWD" --frozen -e geovista python /tmp/fingerprint.py /tmp/branch.json)
python3 -c "import json; a, b = (json.load(open(f'/tmp/{n}.json')) for n in ('main', 'branch')); print(len(a), [k for k in a if a[k] != b[k]])"
git worktree remove --force /tmp/geovista-main
```

Expected: `21 []`, every pantry mesh identical, points, faces and arrays.

- [ ] **Step 8: Commit**

Message, humanized: `fix: take common.py out of the typing ratchet`, naming correction 3
and the `triangulated` bool.

---

### Task 4: the spec and the changelog

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §3.3, §4
- Create: `changelog/{PR}.bugfix.rst`

- [ ] **Step 1: Say what change 4 found, and the rule for runtime guards**

In typing spec §3.3, after the paragraph change 3 added (ending "The API reference
publishes no private members."), insert, humanized and wrapped at the spec's width:

```text
Change 4 found the idiom on eight of `common.py`'s lines, where the census counted six,
all in two public functions and both genuine:
`vectors_to_cartesian` read `.shape` from points and vector components it never
converted, so lists raised `AttributeError`, and `nan_mask` handed a list back where it
promises an array. Both now convert at the boundary. It also met the other pattern
this rule leaves open, a runtime type check on an annotated parameter, whose body `mypy`
reports unreachable because the annotation says it cannot run. The parameter is
annotated with the type the function accepts before it validates, `pv.DataSet` for
`cast_UnstructuredGrid_to_PolyData`, which keeps the check reachable without a
`type: ignore`.
```

- [ ] **Step 2: Mark row 4 in progress**

In the typing spec §4 table, change row 4's Status from `not started` to
`` in progress ({pull}`PR`) ``.

- [ ] **Step 3: Write the changelog fragment**

Create `changelog/{PR}.bugfix.rst`, humanized:

```rst
``vectors_to_cartesian`` now accepts lists for its longitudes, latitudes and
vector components, as its ``ArrayLike`` annotation promises; it raised
``AttributeError``. ``cast_UnstructuredGrid_to_PolyData`` raises the
``TypeError`` it means to for anything but an unstructured grid, where it raised
``AttributeError``. ``nan_mask`` returns an array for a list, and
``triangulated`` returns a ``bool``. ``geovista.common`` also leaves the typing
ratchet, so ``mypy`` checks it in full. (:user:`claude`)
```

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py {PR} "changelog/{PR}.bugfix.rst"`

Expected: `🆗 Your changelog contribution looks good to me.`

- [ ] **Step 4: Verify, commit and push**

Run: `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py`

Expected: PASS.

Run, from `docs/`:

```bash
pixi run --frozen -e docs sphinx-build -b html -W --keep-going \
  -D plot_docstring=False -D plot_gallery=False \
  -D plot_inline=False -D plot_tutorial=False \
  -d _build/doctrees src _build/html
```

Expected: `build succeeded`, with no warnings.

Message, humanized: `docs: correct the typing spec against change 4's measurements`.

---

### Task 5: land row 4

The pull request's last commit, made once the implementation, the final review and any
Codex round are done, dated the day it is committed.

- [ ] **Step 1:** In the typing spec §4 table, replace row 4's `` in progress
  ({pull}`PR`) `` with `` ✅ landed (TODAY, {pull}`PR`) ``.
- [ ] **Step 2:** Run `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py`
  (expected PASS), commit `docs: mark row 4 of the typing roadmap landed`, push.

---

## Done when

- `pixi run --frozen -e geovista mypy` exits 0 with `geovista.common` absent from both the
  ratchet and `RATCHET_BASELINE`.
- The five task 1 failures, task 2's guard and `test_returns_bool` were seen failing, then
  passing.
- The suite passes in `geovista`, `tests/common` in `test-py314`, the pantry fingerprints
  match `main`, and CI is green, image tests included.
- Typing spec §3.3 and §4 agree with the measurements, and row 4 reads landed as the pull
  request's last commit.
- Every deferred item has an `agentic` issue, linked from the Follow-ups below and from the
  pull request's description.

## Follow-ups

None yet. The final review's minors, and any defect it sets aside, each get an `agentic`
issue listed here before the pull request leaves draft.

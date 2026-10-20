---
orphan: true
---

# type coverage change 6b — the mesh modules

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** take the five mesh modules, `geovista.crs`, `geovista.filters`,
`geovista.gridlines`, `geovista.search` and `geovista.core`, out of the typing ratchet,
fixing the two bugs and the one pyvista defect their 38 lines hide.

**Architecture:** row 6b of typing spec §4, the second of the three pull requests row 6
was split into ({pull}`2659`). Each module gains the `numpy` import under `TYPE_CHECKING`
that typing spec §3.3 asks of a module loading it lazily, and leaves the ratchet in the
commit that makes it pass, smallest first, so that `core`, which imports the other four,
goes last. Two genuine bugs get a failing test first. pyvista 0.49 types integer and
boolean arrays in a way no numpy array satisfies; four typed locals meet it, and a new
§8 item waits on the release that fixes it.

**Tech Stack:** `mypy` 2.x in strict mode, `pytest`, `pyvista` 0.49.1, `numpy` 2.5.

**Spec:** `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, cited throughout
as `typing spec §…`. This plan implements row 6b of §4.

**Branch:** `debt/typing-mesh`. The plan is committed first and the pull request held in
draft until the implementation lands on it. `{PR}` below is that pull request's number.

## Global Constraints

- **Copyright header** and `from __future__ import annotations` on every Python file
  (root `AGENTS.md`, ruff-enforced). **Line length 88.**
- **The strictness settings stay as they are** (typing spec §7).
- **No `type: ignore`, no `typing.cast`, and no new `noqa`.** An upstream defect is met with
  a typed local, a comment naming the defect beside it, and a typing spec §8 item.
- **A runtime type check on an annotated parameter** widens the parameter to the type the
  function accepts before it validates (typing spec §3.3, change 4's rule).
- **`distance` returns `float | np.ndarray`.** A caller that wants the mean radius converts
  with `float(...)`, as change 5's callers do; it is not given overloads (change 5 dropped
  them because autoapi garbles them).
- **The ratchet only shrinks, in step:** `pyproject.toml` and `RATCHET_BASELINE` in the
  same commit as the fixes that make the module pass. Every commit passes the `mypy` hook.
- **Run the full non-image suite before each commit**, not only the tests of the task:
  `tests/test_spec_conventions.py` counts citations outside the specifications (37 of a
  ceiling of 70 on `main`; this change adds none).
- **Run the image tests locally before pushing.** This host renders now:
  `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e geovista pytest -n auto -m image tests`.
  `core.py` and `gridlines.py` feed nearly every scene.
- **A probe of a scratch tree never runs `python -I`**, which ignores `PYTHONPATH`.
- **Changelog.** One fragment, `{PR}.bugfix.rst`, signed ``:user:`claude` ``; the
  `agentic` label on the pull request.
- **Every deferred item gets an `agentic` issue**, linked from the Follow-ups below and
  from the pull request's description.
- **Prose for other readers is humanized:** the spec's new text, the code comments, commit
  messages, the fragment and the pull request body. This plan is not.

## What the dry run measured

Measured on 2026-10-20 against `main` at `3141c971`, with the five entries lifted, the
`numpy` imports added, and every fix below applied to a scratch tree, which `mypy` then
passed in full (85 source files) with the non-image suite and all 92 image tests green.

1. **Row 6b's count reproduces.** The five modules report 45 errors on 38 lines: `core`
   28 errors on 23 lines, `search` 6 on 4, `filters` 5, `gridlines` 5, `crs` 1. {pull}`2668`
   changed one of `core`'s `resize` errors for another and left the count alone.
2. **Six of the 38 lines are pyvista's.** Checked against a clone of `pyvista` `main`
   (`f51e933`) with its new `pyvista-validation` 0.5.4 dependency beside it, these vanish:
   `filters.py` 188 and 191, `core.py` 426, 706 (two errors), 824 (one of two) and 1071.
   pyvista 0.49 annotates arrays as `NDArray[int]`, `NDArray[bool]` and `NDArray[float]`,
   with Python's scalar types as the dtype. `numpy.float64` subclasses `float`, so a float
   array passes into pyvista, but `numpy.bool` and `numpy.intp` subclass neither `bool` nor
   `int`, so `extract_cells` refuses every real mask and index array. And numpy's own
   methods refuse what pyvista hands back: `+=` on a mesh's `faces`, `min` on a cell's
   `points`. pyvista pull requests 9344 and 9351 (both merged 2026-09-29) replace the
   aliases. The locked 0.49.1 (2026-10-11) was released from the 0.49 branch, cut on
   2026-09-07, and carries neither. The sixth line, 1071, is
   `ids[n_ids:] = ...`, the `__setitem__` key of §8 item 6 again.
3. **Two bugs.** `combine` returns a single mesh before checking its type, so
   `combine(pv.ImageData(...))` returns an `ImageData` from a function annotated to return
   `PolyData`. `find_nearest_cell` documents `z` as optional, defaulting to zero, and
   accepts `None`, which VTK refuses with `TypeError` on a projected mesh.
4. **Change 4's rule applies twice.** `combine` and `slice_cells` check for the
   `pv.PolyData` they are annotated to receive, so `mypy` reports both `raise`s
   unreachable; both parameters widen to `pv.DataSet`. `tests/core/test_slice_cells.py`
   already passes an `ImageData`.
5. **`set_active_scalars` wants a literal.** Four sites in `core.py` pass
   `association.name.lower()`, a `str`; pyvista takes `"point"` or `"cell"`. pyvista
   reports `POINT` for a mesh with no active scalars, so the association is only ever
   `POINT` or `CELL` there, and one private helper maps it.
6. **The rest are rebinding.** A name bound to a list and then to an array, or to a
   `pyvista_ndarray` and then to an `ndarray`: `gridlines.py` 375, 581 to 594,
   `search.py` 360, and `core.py`'s `slice_lines` and `_carry_line_data`.

## Review Focus

1. **A single mesh that is not a `PolyData`.** `combine` now raises `TypeError` for it, as
   it does for any other mesh it cannot combine; a single `PolyData` is still returned as
   it is. → task 4, `test_single_mesh_fail` and `test_single_mesh_pass_thru`.
2. **A slice keeps cell scalars as cell scalars** when point data shares their name.
   `slice_cells` drops such a point array during the remesh ({issue}`2675`), so only
   `MeridianSlice`, which restores the input mesh's own scalars, can tell `"cell"` from
   `"point"`. → task 4, `test_active_scalars_kept`, which fails if `_preference` always
   answers `"point"` (measured).
3. **`find_nearest_cell` with `z=None` on a projected mesh** finds the same cell as `z=0`.
   → task 3, `test_planar_z`.
4. **`projected` returns a Python `bool`,** as annotated, for a mesh with no CRS too. A
   `numpy.bool` fails `is True` and `isinstance(..., bool)` for a caller who checks either.
   → task 1, `test_bool__no_crs`.
5. **The graticule is unchanged.** `create_parallels` with `poles_label` builds its pole
   points through a renamed list; `tests/gridlines/test_create_parallels.py::test_core`
   pins them, and the image tests draw them.

---

### Task 1: retire `geovista.crs` and `geovista.filters`

**Files:**
- Modify: `src/geovista/crs.py` (`TYPE_CHECKING` block, `projected`),
  `src/geovista/filters.py` (`TYPE_CHECKING` block, `remesh`)
- Modify: `pyproject.toml` (the ratchet), `tests/test_typing_ratchet.py`
- Test: `tests/crs/test_projected.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `projected(mesh: pv.DataObject) -> bool` returning a Python `bool`.

- [ ] **Step 1: Write the failing test**

Append to `tests/crs/test_projected.py`:

```python
@pytest.mark.parametrize("mesh", [pv.Plane(), pv.Sphere()], ids=["planar", "sphere"])
def test_bool__no_crs(mesh):
    """Test that the result is a Python bool, not a NumPy one."""
    assert type(projected(mesh)) is bool
```

Run: `pixi run --frozen -e geovista pytest tests/crs/test_projected.py -k bool`

Expected: both FAIL, `numpy.bool` is not `bool`.

- [ ] **Step 2: Lift the two modules, and watch them fail**

Delete `  "geovista.crs",` and `  "geovista.filters",` from the ratchet's `module` list in
`pyproject.toml`, and both names from `RATCHET_BASELINE`. Add `import numpy as np` as the
first line of the `if TYPE_CHECKING:` block of `crs.py` and of `filters.py`, and
`from numpy.typing import NDArray` after it in `filters.py`.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 6 errors in 2 files`: `crs.py` 1, `filters.py` 5 (`Plane`'s
`center`, `i_size`, `j_size`, and two `extract_cells`).

- [ ] **Step 3: Fix `crs.py`**

In `projected`, wrap the `np.isclose(...) or ...` expression assigned to `result` in
`bool(...)`.

- [ ] **Step 4: Fix `filters.py`**

In `remesh`, `radius = float(distance(mesh))`. Annotate the two masks as any array, with
the comment, humanized:

```python
        # pyvista 0.49 annotates "extract_cells" to refuse a numpy boolean mask,
        # which it accepts at runtime, so the masks are typed as any array
        west_mask: NDArray[Any] = lower_mask | upper_mask
        east_mask: NDArray[Any] = ~west_mask
```

and import `Any` from `typing`.

- [ ] **Step 5: Verify, and commit**

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 85 source files`.

Run: `pixi run --frozen -e geovista pytest -m "not image" --numprocesses auto --dist worksteal`

Expected: exit 0; 2910 passed with a docs build present, as on `main` (two new tests, two
fewer `test_ratchet_entry_resolves` cases).

Run: `pixi run --frozen -e geovista pre-commit run --files src/geovista/crs.py src/geovista/filters.py tests/crs/test_projected.py pyproject.toml tests/test_typing_ratchet.py`

Expected: every hook passes.

Message, humanized: `fix: type check crs.py and filters.py in full`.

---

### Task 2: retire `geovista.gridlines`

**Files:**
- Modify: `src/geovista/gridlines.py` (`TYPE_CHECKING` block, `create_meridians`,
  `create_parallels`)
- Modify: `pyproject.toml`, `tests/test_typing_ratchet.py`

**Interfaces:**
- Consumes: nothing.
- Produces: no signature changes.

- [ ] **Step 1: Lift the module, and watch it fail**

Delete `  "geovista.gridlines",` from the ratchet and `RATCHET_BASELINE`; add
`import numpy as np` as the first line of the `if TYPE_CHECKING:` block.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 5 errors in 1 file`, all `gridlines.py`: 375, 581, 583, 585,
594.

- [ ] **Step 2: Stop rebinding the lists**

In both functions, drop `grid_points = np.vstack(grid_points)` and pass
`lonlat=np.vstack(grid_points)` to `GraticuleGrid` instead. In `create_parallels`, the pole
list becomes `poles: list[list[float]] = []`, appended to as `lonlat` was, and
`lonlat = np.array(poles, dtype=float)` inside `if poles:`; the rest of that block is
unchanged.

- [ ] **Step 3: Verify, and commit**

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 85 source files`.

Run the full non-image suite. Expected: exit 0, 2909 passed.

Run pre-commit on the three files. Expected: every hook passes.

Message, humanized: `fix: type check gridlines.py in full`.

---

### Task 3: retire `geovista.search`, and let `z=None` mean zero

**Files:**
- Modify: `src/geovista/search.py` (`find_cell_neighbours`, `find_nearest_cell`)
- Modify: `pyproject.toml`, `tests/test_typing_ratchet.py`
- Test: `tests/search/test_find_nearest_cell.py`

**Interfaces:**
- Consumes: nothing.
- Produces: no signature changes; `find_nearest_cell(..., z=None)` behaves as `z=0`.

- [ ] **Step 1: Write the failing test**

Append to `tests/search/test_find_nearest_cell.py`, importing `Transform` from
`geovista.bridge` and `transform_mesh` from `geovista.transform`:

```python
@pytest.mark.parametrize("z", [0, None])
def test_planar_z(z):
    """Test a POI with no z-coordinate on a projected mesh defaults to zero."""
    mesh = transform_mesh(Transform.from_1d([0, 10, 20], [0, 10, 20]), "+proj=eqc")
    x, y, _ = mesh.cell_centers().points[3]
    assert find_nearest_cell(mesh, x, y, z=z) == [3]
```

Run: `pixi run --frozen -e geovista pytest tests/search/test_find_nearest_cell.py -k planar_z`

Expected: `[0]` passes, `[None]` FAILS with `TypeError: FindClosestPoint argument 1`.

- [ ] **Step 2: Lift the module, and watch it fail**

Delete `  "geovista.search",` from the ratchet and `RATCHET_BASELINE`.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 6 errors in 1 file`: 360, 416, three on 419, 421.

- [ ] **Step 3: Fix `find_cell_neighbours`**

Drop the `pids = np.unique(list(pids))` rebinding; pass `np.unique(pids)` straight to
`extract_points`, keeping the comment on the cell ids above it.

- [ ] **Step 4: Fix `find_nearest_cell`**

Build the planar POI as an array, with `None` as zero:

```python
    poi = (
        to_cartesian(x, y)[0]
        if crs in [WGS84, None]
        else np.array([x, y, 0 if z is None else z], dtype=float)
    )
```

and narrow the closest cell after `find_closest_cell`, humanized:

```python
    # a single point has a single closest cell
    assert isinstance(cid, int)
```

pyvista returns a Python `int` for one point (measured); `S101` is ignored for this
idiom, as change 5 found.

- [ ] **Step 5: Verify, and commit**

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 85 source files`.

Run the full non-image suite. Expected: exit 0, 2910 passed.

Run pre-commit on the four files. Expected: every hook passes.

Message, humanized: `fix: type check search.py in full, and let find_nearest_cell take
z=None`.

---

### Task 4: retire `geovista.core`

**Files:**
- Modify: `src/geovista/core.py`
- Modify: `pyproject.toml`, `tests/test_typing_ratchet.py`
- Create: `tests/core/test_combine.py`, `tests/core/test_MeridianSlice.py`

**Interfaces:**
- Consumes: tasks 1 to 3, whose modules `core.py` imports.
- Produces: `combine(*meshes: pv.DataSet, data=..., clean=...) -> pv.PolyData`,
  `slice_cells(mesh: pv.DataSet, /, ...) -> pv.PolyData`,
  `MeridianSlice._intersection(self, bias, n_points: int | None = None)`, and the private
  `_preference(association: pv.FieldAssociation) -> Literal["cell", "point"]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_combine.py`, with the module docstring
`"""Unit-tests for :func:`geovista.core.combine`."""`:

```python
def test_single_mesh_fail():
    """Test trap of a single mesh that is not a :class:`~pyvista.PolyData`."""
    emsg = "Can only combine 'pyvista.PolyData' meshes, input mesh #1 has type"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(pv.ImageData(dimensions=(2, 2, 2)))


def test_mesh_fail():
    """Test trap of a mesh that is not a :class:`~pyvista.PolyData`."""
    emsg = "Can only combine 'pyvista.PolyData' meshes, input mesh #2 has type"
    with pytest.raises(TypeError, match=emsg):
        _ = combine(pv.Sphere(), pv.ImageData(dimensions=(2, 2, 2)))


def test_single_mesh_pass_thru():
    """Test a single :class:`~pyvista.PolyData` is returned as it is."""
    mesh = pv.Sphere()
    assert combine(mesh) is mesh
```

Create `tests/core/test_MeridianSlice.py`, with the module docstring
`"""Unit-tests for :class:`geovista.core.MeridianSlice`."""`:

```python
@pytest.mark.parametrize("preference", ["cell", "point"])
def test_active_scalars_kept(preference):
    """Test the active scalars keep their association when both share a name."""
    mesh = Transform.from_1d([-10, 0, 10, 20], [-10, 0, 10])
    mesh.point_data["data"] = range(mesh.n_points)
    mesh.cell_data["data"] = range(mesh.n_cells)
    mesh.set_active_scalars("data", preference=preference)
    expected = mesh.active_scalars_info
    _ = MeridianSlice(mesh, 5)
    assert mesh.active_scalars_info == expected
    assert expected.association == pv.FieldAssociation[preference.upper()]
```

Run: `pixi run --frozen -e geovista pytest tests/core/test_combine.py tests/core/test_MeridianSlice.py`

Expected: `test_single_mesh_fail` FAILS (DID NOT RAISE); the other four pass, pinning
behaviour the change must keep.

- [ ] **Step 2: Lift the module, and watch it fail**

Delete `  "geovista.core",` from the ratchet and `RATCHET_BASELINE`. In `core.py`, make
the `typing` import `TYPE_CHECKING, Any, Literal`, and the `TYPE_CHECKING` block
`import numpy as np`, `from numpy.typing import ArrayLike, NDArray`, `import pyvista as pv`.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 28 errors in 1 file`, all `core.py`.

- [ ] **Step 3: The active scalars**

Add `_preference(association: pv.FieldAssociation) -> Literal["cell", "point"]` above
`class MeridianSlice`, returning `"cell"` for `pv.FieldAssociation.CELL` and `"point"`
otherwise, with a numpydoc docstring (Parameters, Returns; no Notes, as for the module's
other private helpers) saying that `"point"` is also what pyvista reports for a mesh with no
active scalars. Pass `preference=_preference(...)` at the four sites that pass
`association.name.lower()`: two in `MeridianSlice`, `association = _preference(...)` in
`combine`, and the last line before `slice_cells` returns.

- [ ] **Step 4: The runtime checks, and `combine`'s single mesh**

`combine(*meshes: pv.DataSet, ...)` and `slice_cells(mesh: pv.DataSet, /, ...)`. In
`combine`, return early only for a `PolyData`:
`if len(meshes) == 1 and isinstance(meshes[0], pv.PolyData):`, and drop the
`pv.PolyData` annotation from `first = meshes[0]`. The docstrings keep naming `PolyData`,
the type each function requires.

- [ ] **Step 5: The radii, and `n_points`**

`self.radius = float(distance(mesh))` in `MeridianSlice.__init__`, and
`radius = float(distance(mesh))` in `slice_lines`. `_intersection`'s `n_points` becomes
`int | None`, and its docstring `n_points : int, optional`. In `resize`, the surface's
`new_radius = radius + radius * float(level) * zscale`; `level` is 0-d there.

- [ ] **Step 6: The cell ids**

In `slice_cells`, pass `remeshed[GV_CELL_IDS].tolist()` to `find_cell_neighbours`, whose
documented `cid` is a list. In `slice_lines`, after `poi_cids = mesh.find_closest_cell(...)`,
narrow it, humanized:

```python
    # several points have an array of closest cells
    assert isinstance(poi_cids, np.ndarray)
```

(an `(N, 3)` input returns an array even for `N == 1`, measured), iterate
`poi_cids.tolist()` in the `cid_pids` comprehension, zip over `pois.tolist()` and
`poi_cids.tolist()`, and append `int(intersection_pid[0])` to `detach_pids`.

- [ ] **Step 7: The rebound arrays**

Annotate `points: NDArray[Any] = mesh.points.copy()` in `slice_lines`, and
`values: NDArray[Any] = np.atleast_1d(mesh.point_data[name])` at its first binding in
`_carry_line_data`.

- [ ] **Step 8: The pyvista defects**

Three typed locals, each with its comment, humanized:

- `combine`: `faces: NDArray[Any] = mesh.faces.copy()`, because pyvista 0.49 types the
  faces with a Python `int` dtype, which refuses numpy's in-place arithmetic.
- `slice_cells`: `cxpts: NDArray[Any] = neighbours.get_cell(cid).points[:, 0]`, because it
  types the points with a Python `float` dtype, which refuses numpy's reductions.
- `_keep_roles`: split `ids, n_ids = ...` into `ids: NDArray[Any] = target[name]` and
  `n_ids = array.GetNumberOfTuples()`, because it refuses a slice as the key of an
  assignment, which it accepts at runtime (§8 item 6). Keep the comment that pyvista hands
  back a view.

- [ ] **Step 9: Verify, and commit**

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 85 source files`.

Run: `pixi run --frozen -e geovista pytest tests/core/test_combine.py tests/core/test_MeridianSlice.py`

Expected: all pass.

Run the full non-image suite. Expected: exit 0, 2914 passed.

Run the image suite under `xvfb-run` (Global Constraints). Expected: 92 passed.

Run pre-commit on the five files. Expected: every hook passes.

Message, humanized: `fix: type check core.py in full, and have combine check a single
mesh`.

---

### Task 5: the spec and the changelog

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §3.3, §8, §9
- Create: `changelog/{PR}.bugfix.rst`

- [ ] **Step 1: §3.3, what change 6b found**

After change 5's paragraph, add, humanized:

```text
Change 6b met change 4's runtime check twice more, in `core.py`. `combine` and
`slice_cells` check for the `pv.PolyData` they were annotated to receive, so both now take
a `pv.DataSet`. `combine` handed a single mesh back before its check, so
`combine(pv.ImageData(...))` returned an `ImageData` from a function annotated to return
`PolyData`; it now raises `TypeError`, as it does for any other mesh it cannot combine.
`find_nearest_cell` documents `z` as optional and zero by default, and accepted `None`,
which VTK refused with `TypeError` on a projected mesh; `None` now means zero.
```

- [ ] **Step 2: §8, items 6 and 10**

Item 6's title becomes "The cast in `transform_mesh`, and a typed local in `core.py`, wait
on the same `pyvista` release." After the sentence on change 2, add, humanized: "Change 6b
types the ids `_keep_roles` assigns through a slice as any array, for the same reason."
Append item 10, humanized:

```text
10. **Open** ({issue}`2568`) — **Four typed locals wait on the same `pyvista` release.**
    `pyvista` 0.49 types its arrays with Python's `int`, `bool` and `float` as the dtype.
    `numpy.float64` subclasses `float`, so a float array passes into `pyvista`, but
    `numpy.intp` and `numpy.bool` subclass neither `int` nor `bool`, so `extract_cells`
    refuses every real mask or index array. Numpy's own methods refuse what `pyvista`
    hands back in the same way, `+=` on a mesh's faces and `min` on a cell's points.
    Change 6b types the two masks in `filters.remesh`, the faces in `core.combine` and
    the points in `core.slice_cells` as any array. `pyvista` pull requests 9344 and 9351
    replace the annotations. Both merged on 2026-09-29, after the 0.49 release branch was
    cut on 2026-09-07, so 0.49.1 does not carry them, and the locals come out with the
    floor that does, the trigger items 2, 6 and 8 wait on.
```

- [ ] **Step 3: §9, the two pull requests**

After the entry for pull request 9262, add, humanized:

```text
- `pyvista` pull requests 9344 and 9351, which replace the array aliases item 10 of
  {ref}`§8 <typing-spec-8>` waits on:
  <https://github.com/pyvista/pyvista/pull/9344> and
  <https://github.com/pyvista/pyvista/pull/9351>
```

- [ ] **Step 4: The changelog, and verify**

Create `changelog/{PR}.bugfix.rst`, humanized:

```rst
:func:`geovista.core.combine` raises ``TypeError`` for a single mesh that is not
a :class:`~pyvista.PolyData`, where it returned the mesh unchecked, and
:func:`geovista.search.find_nearest_cell` treats ``z=None`` as zero, as
documented, where it raised ``TypeError`` on a projected mesh.
:func:`geovista.crs.projected` returns a Python ``bool``. ``geovista.core``,
``geovista.crs``, ``geovista.filters``, ``geovista.gridlines`` and
``geovista.search`` also leave the typing ratchet, so ``mypy`` checks them in
full. (:user:`claude`)
```

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py {PR} "changelog/{PR}.bugfix.rst"`,
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

Message, humanized: `docs: record what typing change 6b found`.

---

### Task 6: land row 6b

After the final review, its fixes, CI and any Codex round, as the pull request's last
commit: change row 6b's Status to `` ✅ landed (YYYY-MM-DD, {pull}`{PR}`) `` with
`date -u +%F`, and run `check-spec-status {PR}` again. If the merge slips a day, correct the
date first.

Message, humanized: `docs: land typing roadmap row 6b`.

---

## Done when

- `pixi run --frozen -e geovista mypy` exits 0 with `geovista.core`, `geovista.crs`,
  `geovista.filters`, `geovista.gridlines` and `geovista.search` absent from both the
  ratchet and `RATCHET_BASELINE`.
- The suite passes, image tests included, locally and in CI, and the documentation builds
  with `-W`.
- Typing spec §3.3, §8 and §9 record what the change found, and row 6b reads landed.
- Every deferred item has an `agentic` issue, linked below and from the pull request.

## Follow-ups

- {issue}`2675`: `slice_cells` drops a point array that shares a cell array's name, and
  leaks VTK's id arrays through `slice_mesh`, both found while writing task 4's test.
- {issue}`2568`: gains §8 item 10's four typed locals and item 6's second, to withdraw with
  the `pyvista` floor. Comment on it when the pull request opens.
